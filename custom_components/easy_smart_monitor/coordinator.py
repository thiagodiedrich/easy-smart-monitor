from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    TEST_MODE,
    DEFAULT_DOOR_OPEN_SECONDS,
    EQUIPMENT_STATUS_OK,
    EQUIPMENT_STATUS_DOOR_OPEN,
    EQUIPMENT_STATUS_TEMPERATURE_ALERT,
    INTEGRATION_STATUS_ONLINE,
    INTEGRATION_STATUS_API_ERROR,
    INTEGRATION_STATUS_TEST_MODE,
)

_LOGGER = logging.getLogger(__name__)


class EasySmartMonitorCoordinator(DataUpdateCoordinator):
    """
    Coordinator principal do Easy Smart Monitor.

    Responsável por:
    - Processar eventos de sensores
    - Aplicar regras por equipamento
    - Controlar sirene
    - Gerenciar fila local
    - Atualizar estados das entidades
    """

    def __init__(
        self,
        hass: HomeAssistant,
        api_client,
        entry,
    ) -> None:
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=None,
        )

        self.hass = hass
        self.api_client = api_client
        self.entry = entry

        # -----------------------------------------------------
        # STATUS GLOBAL DA INTEGRAÇÃO
        # -----------------------------------------------------
        self.integration_status: str = (
            INTEGRATION_STATUS_TEST_MODE
            if TEST_MODE
            else INTEGRATION_STATUS_ONLINE
        )

        self.last_successful_sync: datetime | None = None

        # -----------------------------------------------------
        # FILA LOCAL DE EVENTOS
        # -----------------------------------------------------
        self._queue: list[dict[str, Any]] = []

        # -----------------------------------------------------
        # ESTADOS POR EQUIPAMENTO
        # -----------------------------------------------------
        self.equipment_status: dict[int, str] = {}
        self.equipment_status_details: dict[int, dict] = {}

        self.numeric_states: dict[int, dict[str, float | None]] = {}
        self.binary_states: dict[int, dict[str, bool]] = {}
        self.binary_attributes: dict[int, dict[str, dict]] = {}

        self.siren_state: dict[int, bool] = {}
        self.siren_attributes: dict[int, dict] = {}

        # -----------------------------------------------------
        # TASKS INTERNAS
        # -----------------------------------------------------
        self._open_door_tasks: dict[int, asyncio.Task] = {}

    # =========================================================
    # PROPRIEDADES
    # =========================================================

    @property
    def queue_size(self) -> int:
        """Quantidade de eventos pendentes na fila."""
        return len(self._queue)

    # =========================================================
    # CICLO DE VIDA
    # =========================================================

    async def async_initialize(self) -> None:
        """Inicializa estruturas internas para todos os equipamentos."""
        for equipment in self.entry.options.get("equipments", []):
            equipment_id = equipment["id"]

            self.equipment_status[equipment_id] = EQUIPMENT_STATUS_OK
            self.equipment_status_details[equipment_id] = {}

            self.numeric_states[equipment_id] = {
                "temperature": None,
                "humidity": None,
            }

            self.binary_states[equipment_id] = {
                "energy_on": False,
                "door_open": False,
            }

            self.binary_attributes[equipment_id] = {
                "energy": {},
                "door": {},
            }

            self.siren_state[equipment_id] = False
            self.siren_attributes[equipment_id] = {}

        await self.async_set_updated_data({})

        _LOGGER.info("Easy Smart Monitor Coordinator inicializado")

    async def async_shutdown(self) -> None:
        """Cancela tasks internas e limpa recursos."""
        for task in self._open_door_tasks.values():
            task.cancel()

        self._open_door_tasks.clear()

        _LOGGER.info("Easy Smart Monitor Coordinator finalizado")

    # =========================================================
    # CONFIGURAÇÕES AUXILIARES
    # =========================================================

    def _get_door_config(self, equipment: dict) -> tuple[bool, int]:
        """
        Retorna configuração de porta com fallback seguro.

        Returns:
            (enable_siren, open_timeout)
        """
        door_cfg = equipment.get("door", {})

        enable_siren = door_cfg.get("enable_siren", True)
        open_timeout = door_cfg.get(
            "open_timeout",
            DEFAULT_DOOR_OPEN_SECONDS,
        )

        return enable_siren, open_timeout

    # =========================================================
    # ALERTA DE TEMPERATURA (FEATURE 2)
    # =========================================================

    def _evaluate_temperature_alert(
        self,
        equipment: dict,
        equipment_id: int,
    ) -> None:
        """Avalia se a temperatura está fora da faixa configurada."""
        temp_cfg = equipment.get("temperature")

        if not temp_cfg or not temp_cfg.get("enabled", False):
            return

        temp = self.numeric_states[equipment_id].get("temperature")
        if temp is None:
            return

        temp_min = temp_cfg.get("min")
        temp_max = temp_cfg.get("max")

        if temp_min is not None and temp < temp_min:
            self.equipment_status[equipment_id] = (
                EQUIPMENT_STATUS_TEMPERATURE_ALERT
            )
            self.equipment_status_details[equipment_id] = {
                "reason": "below_min",
                "value": temp,
                "min": temp_min,
            }
        elif temp_max is not None and temp > temp_max:
            self.equipment_status[equipment_id] = (
                EQUIPMENT_STATUS_TEMPERATURE_ALERT
            )
            self.equipment_status_details[equipment_id] = {
                "reason": "above_max",
                "value": temp,
                "max": temp_max,
            }
        else:
            # Volta para OK apenas se não houver sirene ativa
            if not self.siren_state.get(equipment_id):
                self.equipment_status[equipment_id] = EQUIPMENT_STATUS_OK
                self.equipment_status_details[equipment_id] = {}

    # =========================================================
    # PROCESSAMENTO DE SENSORES
    # =========================================================

    async def _process_sensor_update(
        self,
        *,
        equipment: dict,
        sensor: dict,
        state: Any,
        attributes: dict,
        timestamp: datetime,
    ) -> None:
        """Processa atualização de sensor."""
        equipment_id = equipment["id"]
        sensor_type = sensor["type"]

        # -----------------------------
        # PORTA
        # -----------------------------
        if sensor_type == "door":
            is_open = state == "on"
            self.binary_states[equipment_id]["door_open"] = is_open

            if is_open:
                self.binary_attributes[equipment_id]["door"] = {
                    "open_since": timestamp.isoformat()
                }
                await self._start_door_timer(equipment)
            else:
                await self._cancel_door_timer(equipment_id)
                if not self.siren_state[equipment_id]:
                    self.equipment_status[equipment_id] = EQUIPMENT_STATUS_OK

        # -----------------------------
        # ENERGIA
        # -----------------------------
        elif sensor_type == "energy":
            self.binary_states[equipment_id]["energy_on"] = state == "on"
            self.binary_attributes[equipment_id]["energy"] = attributes

        # -----------------------------
        # TEMPERATURA
        # -----------------------------
        elif sensor_type == "temperature":
            self.numeric_states[equipment_id]["temperature"] = float(state)
            self._evaluate_temperature_alert(equipment, equipment_id)

        # -----------------------------
        # UMIDADE
        # -----------------------------
        elif sensor_type == "humidity":
            self.numeric_states[equipment_id]["humidity"] = float(state)

        # -----------------------------
        # FILA DE EVENTOS
        # -----------------------------
        self._queue.append(
            {
                "equipment_id": equipment_id,
                "sensor_type": sensor_type,
                "state": state,
                "attributes": attributes,
                "timestamp": timestamp.isoformat(),
            }
        )

        await self.async_set_updated_data({})

    # =========================================================
    # LÓGICA DE PORTA / SIRENE (FEATURE 1)
    # =========================================================

    async def _start_door_timer(self, equipment: dict) -> None:
        equipment_id = equipment["id"]

        enable_siren, open_timeout = self._get_door_config(equipment)

        if not enable_siren:
            _LOGGER.debug(
                "Sirene desabilitada para equipamento %s",
                equipment_id,
            )
            return

        if equipment_id in self._open_door_tasks:
            return

        self._open_door_tasks[equipment_id] = asyncio.create_task(
            self._door_timer_task(equipment_id, open_timeout)
        )

    async def _door_timer_task(
        self,
        equipment_id: int,
        timeout: int,
    ) -> None:
        try:
            await asyncio.sleep(timeout)
            await self.async_trigger_siren(equipment_id)
        except asyncio.CancelledError:
            pass

    async def _cancel_door_timer(self, equipment_id: int) -> None:
        task = self._open_door_tasks.pop(equipment_id, None)
        if task:
            task.cancel()

    async def async_trigger_siren(self, equipment_id: int) -> None:
        """Dispara a sirene do equipamento."""
        self.siren_state[equipment_id] = True
        self.equipment_status[equipment_id] = EQUIPMENT_STATUS_DOOR_OPEN
        self.siren_attributes[equipment_id] = {
            "triggered_at": datetime.utcnow().isoformat()
        }

        await self.async_set_updated_data({})

    async def async_silence_siren(self, equipment_id: int) -> None:
        """Silencia a sirene do equipamento."""
        await self._cancel_door_timer(equipment_id)

        self.siren_state[equipment_id] = False
        self.equipment_status[equipment_id] = EQUIPMENT_STATUS_OK
        self.siren_attributes[equipment_id] = {}

        await self.async_set_updated_data({})

    # =========================================================
    # ENVIO DE EVENTOS PARA API
    # =========================================================

    async def async_flush_queue(self) -> None:
        """Envia eventos acumulados para a API."""
        if not self._queue:
            return

        if TEST_MODE:
            _LOGGER.info(
                "TEST_MODE ativo: %s eventos descartados",
                len(self._queue),
            )
            self._queue.clear()
            self.last_successful_sync = datetime.utcnow()
            await self.async_set_updated_data({})
            return

        try:
            await self.api_client.send_events(self._queue)
            self._queue.clear()
            self.last_successful_sync = datetime.utcnow()
            self.integration_status = INTEGRATION_STATUS_ONLINE
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Erro ao enviar eventos: %s", err)
            self.integration_status = INTEGRATION_STATUS_API_ERROR

        await self.async_set_updated_data({})