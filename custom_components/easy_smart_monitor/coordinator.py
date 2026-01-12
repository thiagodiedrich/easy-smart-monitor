from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.util.dt import utcnow

from .const import (
    DOMAIN,
    STORAGE_VERSION,
    STORAGE_KEY_QUEUE,
    DEFAULT_DOOR_OPEN_SECONDS,
)

_LOGGER = logging.getLogger(__name__)


class EasySmartMonitorCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator central do Easy Smart Monitor."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client,
        entry,
    ) -> None:
        self.hass = hass
        self.entry = entry
        self.api_client = api_client

        # Persistência
        self._store: Store[list[dict[str, Any]]] = Store(
            hass, STORAGE_VERSION, STORAGE_KEY_QUEUE
        )
        self._queue: list[dict[str, Any]] = []

        # Estados globais
        self.integration_status: str = "offline"
        self.last_successful_sync: datetime | None = None
        self._paused: bool = False

        # Estados por equipamento
        self.equipment_status: dict[int, str] = {}
        self.equipment_status_details: dict[int, dict] = {}

        self.numeric_states: dict[int, dict[str, float]] = {}
        self.binary_states: dict[int, dict[str, bool]] = {}
        self.binary_attributes: dict[int, dict[str, dict]] = {}

        self.siren_state: dict[int, bool] = {}
        self.siren_attributes: dict[int, dict] = {}

        # Timers
        self._open_door_tasks: dict[int, asyncio.Task] = {}

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,
        )

    # ---------------------------------------------------------
    # SETUP / SHUTDOWN
    # ---------------------------------------------------------

    async def async_initialize(self) -> None:
        """Inicializa o coordinator."""
        self._queue = await self._store.async_load() or []

        for equipment in self.entry.options.get("equipments", []):
            eid = equipment["id"]

            self.equipment_status[eid] = "ok"
            self.equipment_status_details[eid] = {}
            self.numeric_states[eid] = {}
            self.binary_states[eid] = {}
            self.binary_attributes[eid] = {}
            self.siren_state[eid] = False
            self.siren_attributes[eid] = {}

        self._register_state_listeners()

        self.integration_status = "online"
        self.async_set_updated_data({})

        _LOGGER.info(
            "Easy Smart Monitor inicializado (%s eventos na fila)",
            len(self._queue),
        )

    async def async_shutdown(self) -> None:
        """Finaliza coordinator."""
        for task in self._open_door_tasks.values():
            task.cancel()

        await self._store.async_save(self._queue)

    # ---------------------------------------------------------
    # LISTENERS
    # ---------------------------------------------------------

    def _register_state_listeners(self) -> None:
        """Registra listeners para sensores configurados."""
        for equipment in self.entry.options.get("equipments", []):
            for sensor in equipment.get("sensors", []):
                if not sensor.get("enabled", True):
                    continue

                async_track_state_change_event(
                    self.hass,
                    sensor["entity_id"],
                    self._handle_state_change,
                )

    @callback
    async def _handle_state_change(self, event) -> None:
        new_state = event.data.get("new_state")
        if not new_state:
            return

        entity_id = new_state.entity_id
        timestamp = utcnow()

        for equipment in self.entry.options.get("equipments", []):
            for sensor in equipment.get("sensors", []):
                if sensor["entity_id"] != entity_id:
                    continue

                await self._process_sensor_update(
                    equipment,
                    sensor,
                    new_state.state,
                    new_state.attributes,
                    timestamp,
                )

    # ---------------------------------------------------------
    # PIPELINE CENTRAL
    # ---------------------------------------------------------

    async def _process_sensor_update(
        self,
        equipment: dict,
        sensor: dict,
        state: Any,
        attributes: dict,
        timestamp: datetime,
    ) -> None:
        equipment_id = equipment["id"]
        sensor_type = sensor["type"]

        # ---- Persistência na fila
        self._queue.append(
            {
                "equipment_id": equipment_id,
                "equipment_name": equipment["name"],
                "equipment_uuid": equipment["uuid"],
                "sensor_id": sensor["id"],
                "sensor_uuid": sensor["uuid"],
                "sensor_type": sensor_type,
                "sensor_status": state,
                "timestamp": timestamp.isoformat(),
            }
        )
        await self._store.async_save(self._queue)

        # ---- Atualização de estados
        if sensor_type == "temperature":
            self.numeric_states[equipment_id]["temperature"] = float(state)

        elif sensor_type == "humidity":
            self.numeric_states[equipment_id]["humidity"] = float(state)

        elif sensor_type == "energy":
            self.binary_states[equipment_id]["energy_on"] = state == "on"
            self.binary_attributes[equipment_id]["energy"] = {
                "power_w": attributes.get("power"),
                "voltage_v": attributes.get("voltage"),
                "current_a": attributes.get("current"),
                "energy_kwh": attributes.get("energy"),
            }

        elif sensor_type == "door":
            is_open = state == "on"
            self.binary_states[equipment_id]["door_open"] = is_open

            if is_open:
                self.binary_attributes[equipment_id]["door"] = {
                    "open_since": timestamp.isoformat()
                }
                await self._start_door_timer(equipment)
            else:
                await self._cancel_door_timer(equipment_id)

        self.async_set_updated_data({})

    # ---------------------------------------------------------
    # DOOR / SIREN LOGIC
    # ---------------------------------------------------------

    async def _start_door_timer(self, equipment: dict) -> None:
        equipment_id = equipment["id"]

        if equipment_id in self._open_door_tasks:
            return

        self._open_door_tasks[equipment_id] = asyncio.create_task(
            self._door_timer_task(equipment)
        )

    async def _door_timer_task(self, equipment: dict) -> None:
        equipment_id = equipment["id"]

        try:
            await asyncio.sleep(DEFAULT_DOOR_OPEN_SECONDS)
            await self.async_trigger_siren(equipment_id)
        except asyncio.CancelledError:
            pass

    async def _cancel_door_timer(self, equipment_id: int) -> None:
        task = self._open_door_tasks.pop(equipment_id, None)
        if task:
            task.cancel()

    # ---------------------------------------------------------
    # SIREN / BUTTON
    # ---------------------------------------------------------

    async def async_trigger_siren(self, equipment_id: int) -> None:
        self.siren_state[equipment_id] = True
        self.siren_attributes[equipment_id] = {
            "trigger_reason": "door_open",
            "triggered_at": utcnow().isoformat(),
        }
        self.equipment_status[equipment_id] = "porta_aberta"
        self.async_set_updated_data({})

    async def async_silence_siren(self, equipment_id: int) -> None:
        await self._cancel_door_timer(equipment_id)
        self.siren_state[equipment_id] = False
        self.siren_attributes[equipment_id] = {}
        self.equipment_status[equipment_id] = "ok"
        self.async_set_updated_data({})

    # ---------------------------------------------------------
    # API SENDER
    # ---------------------------------------------------------

    async def async_send_queue(self) -> None:
        if self._paused or not self._queue:
            return

        try:
            await self.api_client.send_events(self._queue)
            self._queue.clear()
            await self._store.async_save(self._queue)

            self.last_successful_sync = utcnow()
            self.integration_status = "online"
        except Exception as err:  # noqa: BLE001
            self.integration_status = "api_error"
            _LOGGER.error("Erro ao enviar dados para API: %s", err)

        self.async_set_updated_data({})

    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------

    @property
    def queue_size(self) -> int:
        return len(self._queue)

    def pause(self) -> None:
        self._paused = True
        self.integration_status = "paused"

    def resume(self) -> None:
        self._paused = False
        self.integration_status = "online"