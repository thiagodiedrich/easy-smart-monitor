from __future__ import annotations

import asyncio
import logging
from datetime import timedelta, datetime
from typing import Dict, Any, List

from aiohttp import ClientSession, ClientError
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.storage import Store

from .client import EasySmartMonitorClient

_LOGGER = logging.getLogger(__name__)


class EasySmartMonitorCoordinator(DataUpdateCoordinator):
    """
    Coordinator responsável por:
    - lógica da porta (120s)
    - controle da sirene
    - reset de sirene
    - fila local persistente
    - envio periódico de eventos para API
    """

    SEND_INTERVAL = 60  # segundos
    QUEUE_STORAGE_KEY = "easy_smart_monitor_queue"
    QUEUE_STORAGE_VERSION = 1

    def __init__(
        self,
        hass: HomeAssistant,
        entry,
        client: EasySmartMonitorClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Easy Smart Monitor",
            update_interval=timedelta(seconds=30),
        )

        self.hass: HomeAssistant = hass
        self.entry = entry
        self.client = client

        # ===== Timers de porta por equipamento =====
        self._door_tasks: Dict[int, asyncio.Task] = {}

        # ===== Fila local =====
        self._store = Store(
            hass,
            self.QUEUE_STORAGE_VERSION,
            self.QUEUE_STORAGE_KEY,
        )
        self._queue: List[Dict[str, Any]] = []

        # ===== Controle do loop de envio =====
        self._send_task: asyncio.Task | None = None
        self._queue_lock = asyncio.Lock()

    # ======================================================
    # CICLO DO COORDINATOR (OBRIGATÓRIO)
    # ======================================================

    async def _async_update_data(self) -> dict:
        """
        Método obrigatório do DataUpdateCoordinator.

        Não buscamos dados externos aqui.
        A lógica é baseada em eventos.
        """
        return {}

    async def async_initialize(self) -> None:
        """
        Inicialização explícita do coordinator:
        - carrega fila persistente
        - inicia loop de envio
        """
        data = await self._store.async_load()
        self._queue = data or []

        _LOGGER.info(
            "Fila local carregada com %d eventos pendentes",
            len(self._queue),
        )

        if not self._send_task:
            self._send_task = self.hass.async_create_task(
                self._send_loop()
            )

    async def async_shutdown(self) -> None:
        """
        Finalização limpa.
        """
        if self._send_task:
            self._send_task.cancel()
            self._send_task = None

        for task in self._door_tasks.values():
            if not task.done():
                task.cancel()

    # ======================================================
    # LÓGICA DA PORTA (120s)
    # ======================================================

    @callback
    def handle_door_state_change(self, equipment_id: int, is_open: bool) -> None:
        """
        Chamado pelo binary_sensor quando a porta muda de estado.
        """
        self.hass.async_create_task(
            self._enqueue_event(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "equipment_id": equipment_id,
                    "event": "door",
                    "open": is_open,
                }
            )
        )

        if is_open:
            _LOGGER.debug(
                "Porta aberta para equipamento %s, iniciando timer",
                equipment_id,
            )
            self._start_door_timer(equipment_id)
        else:
            _LOGGER.debug(
                "Porta fechada para equipamento %s, cancelando timer",
                equipment_id,
            )
            self._cancel_door_timer(equipment_id)

    def _start_door_timer(self, equipment_id: int) -> None:
        self._cancel_door_timer(equipment_id)

        self._door_tasks[equipment_id] = self.hass.async_create_task(
            self._door_timer_task(equipment_id)
        )

    def _cancel_door_timer(self, equipment_id: int) -> None:
        task = self._door_tasks.pop(equipment_id, None)
        if task and not task.done():
            task.cancel()

    async def _door_timer_task(self, equipment_id: int) -> None:
        try:
            await asyncio.sleep(120)

            if not self._is_door_open(equipment_id):
                _LOGGER.debug(
                    "Timer finalizado mas porta está fechada (%s)",
                    equipment_id,
                )
                return

            _LOGGER.warning(
                "Porta aberta por 120s, acionando sirene (%s)",
                equipment_id,
            )

            await self._turn_on_siren(equipment_id)

            await self._enqueue_event(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "equipment_id": equipment_id,
                    "event": "siren",
                    "state": "on",
                }
            )

        except asyncio.CancelledError:
            _LOGGER.debug(
                "Timer cancelado para equipamento %s",
                equipment_id,
            )

    # ======================================================
    # CONTROLE DA SIRENE
    # ======================================================

    async def _turn_on_siren(self, equipment_id: int) -> None:
        entity_id = self._get_siren_entity_id(equipment_id)
        if entity_id:
            await self.hass.services.async_call(
                "switch",
                "turn_on",
                {"entity_id": entity_id},
                blocking=False,
            )

    async def _turn_off_siren(self, equipment_id: int) -> None:
        entity_id = self._get_siren_entity_id(equipment_id)
        if entity_id:
            await self.hass.services.async_call(
                "switch",
                "turn_off",
                {"entity_id": entity_id},
                blocking=False,
            )

    def reset_siren(self, equipment_id: int) -> None:
        """
        Chamado pelo botão RESET.
        """
        _LOGGER.info(
            "Reset de sirene para equipamento %s",
            equipment_id,
        )

        self._cancel_door_timer(equipment_id)
        self.hass.async_create_task(self._turn_off_siren(equipment_id))

        self.hass.async_create_task(
            self._enqueue_event(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "equipment_id": equipment_id,
                    "event": "reset",
                }
            )
        )

        # Se a porta ainda estiver aberta, reinicia o timer
        if self._is_door_open(equipment_id):
            self._start_door_timer(equipment_id)

    # ======================================================
    # FILA LOCAL
    # ======================================================

    async def _enqueue_event(self, payload: Dict[str, Any]) -> None:
        async with self._queue_lock:
            self._queue.append(payload)
            await self._store.async_save(self._queue)

    async def _send_loop(self) -> None:
        """
        Loop assíncrono que envia a fila para a API periodicamente.
        """
        async with ClientSession() as session:
            while True:
                try:
                    await asyncio.sleep(self.SEND_INTERVAL)

                    if not self._queue:
                        continue

                    async with self._queue_lock:
                        batch = list(self._queue)

                    await self.client.async_send_events(session, batch)

                    async with self._queue_lock:
                        self._queue.clear()
                        await self._store.async_save(self._queue)

                    _LOGGER.info(
                        "Fila enviada com sucesso (%d eventos)",
                        len(batch),
                    )

                except ClientError as err:
                    _LOGGER.warning(
                        "Falha ao enviar fila, mantendo eventos: %s",
                        err,
                    )
                except asyncio.CancelledError:
                    _LOGGER.debug("Loop de envio cancelado")
                    return
                except Exception as err:
                    _LOGGER.exception(
                        "Erro inesperado no envio da fila: %s",
                        err,
                    )

    # ======================================================
    # UTILITÁRIOS
    # ======================================================

    def _is_door_open(self, equipment_id: int) -> bool:
        equipments: Dict[str, Any] = self.entry.options.get("equipments", {})
        for eq in equipments.values():
            if eq.get("id") == equipment_id:
                for sensor in eq.get("sensors", {}).values():
                    if sensor.get("type") == "door":
                        state = self.hass.states.get(sensor["entity_id"])
                        return bool(state and state.state == "on")
        return False

    def _get_siren_entity_id(self, equipment_id: int) -> str | None:
        equipments: Dict[str, Any] = self.entry.options.get("equipments", {})
        for eq in equipments.values():
            if eq.get("id") == equipment_id:
                slug = eq["name"].lower().replace(" ", "_")
                return f"switch.{slug}_sirene"
        return None