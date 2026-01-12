from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)
from homeassistant.util import dt as dt_util

from .const import DOMAIN, TEST_MODE
from .client import EasySmartMonitorApiClient
from .storage import EasySmartMonitorStorage

_LOGGER = logging.getLogger(__name__)


class EasySmartMonitorCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """
    Coordinator central do Easy Smart Monitor.

    Responsabilidades:
    - Orquestrar leitura de sensores do HA
    - Respeitar configuração do storage
    - Enfileirar eventos
    - Enviar eventos para API
    - Controlar sirene e lógica de porta
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api_client: EasySmartMonitorApiClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,
        )

        self.hass = hass
        self.entry = entry
        self.api = api_client

        self.storage = EasySmartMonitorStorage(hass)

        self._queue: list[dict[str, Any]] = []
        self._last_door_open: dict[str, datetime] = {}
        self._last_successful_sync: datetime | None = None

        self._lock = asyncio.Lock()

    # =========================================================
    # LIFECYCLE
    # =========================================================

    async def async_initialize(self) -> None:
        """Inicialização assíncrona do coordinator."""
        await self.storage.async_load()

        # Garante que existe pelo menos um equipamento em TEST_MODE
        if TEST_MODE and not self.storage.get_equipments():
            await self.storage.add_equipment(
                equipment_id="test_equipment",
                name="Equipamento Teste",
                location="TEST MODE",
            )

        _LOGGER.info(
            "Easy Smart Monitor iniciado com %s equipamentos",
            len(self.storage.get_equipments()),
        )

    # =========================================================
    # UPDATE CORE
    # =========================================================

    async def _async_update_data(self) -> dict[str, Any]:
        """Não usado — updates são manuais."""
        return {}

    # =========================================================
    # LOOP PRINCIPAL
    # =========================================================

    async def async_process(self) -> None:
        """
        Loop principal:
        - Lê sensores configurados
        - Gera eventos
        - Avalia sirene
        - Envia fila
        """
        async with self._lock:
            await self._process_equipments()
            await self._flush_queue()

    async def _process_equipments(self) -> None:
        """Processa todos os equipamentos ativos."""
        now = dt_util.utcnow()

        for equipment_id, equipment in self.storage.get_equipments().items():
            if not equipment.get("enabled", True):
                continue

            await self._process_equipment(
                equipment_id,
                equipment,
                now,
            )

    async def _process_equipment(
        self,
        equipment_id: str,
        equipment: dict[str, Any],
        now: datetime,
    ) -> None:
        """Processa um único equipamento."""
        sensors = equipment.get("sensors", {})
        door_cfg = equipment.get("door", {})

        # -----------------------------------------------------
        # TEMPERATURA / UMIDADE / ENERGIA
        # -----------------------------------------------------

        for sensor_type in ("temperature", "humidity", "energy"):
            entity_id = sensors.get(sensor_type)
            if not entity_id:
                continue

            state = self.hass.states.get(entity_id)
            if not state or state.state in ("unknown", "unavailable"):
                continue

            try:
                value = float(state.state)
            except ValueError:
                continue

            self._queue.append(
                {
                    "equipment_id": equipment_id,
                    "type": sensor_type,
                    "value": value,
                    "timestamp": now.isoformat(),
                }
            )

        # -----------------------------------------------------
        # PORTA + SIRENE
        # -----------------------------------------------------

        door_entity = sensors.get("door")
        if door_entity:
            state = self.hass.states.get(door_entity)
            if state:
                is_open = state.state == "on"

                last_open = self._last_door_open.get(equipment_id)

                if is_open and not last_open:
                    self._last_door_open[equipment_id] = now

                if not is_open:
                    self._last_door_open.pop(equipment_id, None)

                if (
                    is_open
                    and door_cfg.get("enable_siren", True)
                    and last_open
                ):
                    elapsed = (now - last_open).total_seconds()
                    if elapsed >= door_cfg.get("open_timeout", 120):
                        await self._trigger_siren(
                            equipment_id, elapsed
                        )

    # =========================================================
    # SIRENE
    # =========================================================

    async def _trigger_siren(
        self, equipment_id: str, elapsed: float
    ) -> None:
        """Dispara evento de sirene."""
        self._queue.append(
            {
                "equipment_id": equipment_id,
                "type": "door_alarm",
                "value": elapsed,
                "timestamp": dt_util.utcnow().isoformat(),
            }
        )

    async def async_trigger_siren(self, equipment_id: str) -> None:
        """Disparo manual da sirene."""
        self._queue.append(
            {
                "equipment_id": equipment_id,
                "type": "manual_alarm",
                "timestamp": dt_util.utcnow().isoformat(),
            }
        )

    async def async_silence_siren(self, equipment_id: str) -> None:
        """Silencia sirene (apenas limpa estado interno)."""
        self._last_door_open.pop(equipment_id, None)

    # =========================================================
    # FILA / ENVIO
    # =========================================================

    async def _flush_queue(self) -> None:
        """Envia eventos acumulados para a API."""
        if not self._queue:
            return

        events = list(self._queue)
        self._queue.clear()

        if TEST_MODE:
            _LOGGER.info(
                "TEST_MODE ativo — %s eventos simulados",
                len(events),
            )
            self._last_successful_sync = dt_util.utcnow()
            return

        try:
            await self.api.send_events(events)
            self._last_successful_sync = dt_util.utcnow()
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Erro ao enviar eventos: %s", err)
            self._queue.extend(events)

    # =========================================================
    # INFO PARA ENTIDADES
    # =========================================================

    @property
    def last_successful_sync(self) -> datetime | None:
        return self._last_successful_sync

    @property
    def queue_size(self) -> int:
        return len(self._queue)