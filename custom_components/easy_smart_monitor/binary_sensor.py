from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN
from .coordinator import EasySmartMonitorCoordinator

_LOGGER = logging.getLogger(__name__)


# ============================================================
# SETUP DA PLATAFORMA (OBRIGATÓRIO)
# ============================================================

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """
    Cria dinamicamente binary_sensors (porta)
    a partir dos equipamentos configurados no Options Flow.
    """
    coordinator: EasySmartMonitorCoordinator = hass.data[DOMAIN][entry.entry_id]

    equipments: dict[str, Any] = entry.options.get("equipments", {})
    entities: list[BinarySensorEntity] = []

    for equipment in equipments.values():
        for sensor in equipment.get("sensors", {}).values():
            if not sensor.get("enabled", True):
                continue

            if sensor.get("type") == "door":
                entities.append(
                    EasySmartDoorBinarySensor(
                        coordinator=coordinator,
                        equipment=equipment,
                        sensor=sensor,
                    )
                )

    if entities:
        async_add_entities(entities)


# ============================================================
# BASE BINARY SENSOR
# ============================================================

class EasySmartBaseBinarySensor(CoordinatorEntity, BinarySensorEntity):

    def __init__(
        self,
        coordinator: EasySmartMonitorCoordinator,
        equipment: dict,
        sensor: dict,
    ) -> None:
        super().__init__(coordinator)
        self._equipment = equipment
        self._sensor = sensor
        self._source_entity_id: str = sensor["entity_id"]
        self._unsub_listener = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        self._unsub_listener = async_track_state_change_event(
            self.hass,
            [self._source_entity_id],
            self._state_listener,
        )

        state = self.hass.states.get(self._source_entity_id)
        if state:
            self.coordinator.handle_door_state_change(
                self._equipment["id"],
                state.state == "on",
            )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_listener:
            self._unsub_listener()
            self._unsub_listener = None
        await super().async_will_remove_from_hass()

    @callback
    def _state_listener(self, event) -> None:
        new_state = event.data.get("new_state")
        if not new_state:
            return

        is_open = new_state.state == "on"

        self.coordinator.handle_door_state_change(
            self._equipment["id"],
            is_open,
        )

    def _get_source_state(self):
        return self.hass.states.get(self._source_entity_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "equipment_id": self._equipment["id"],
            "equipment_name": self._equipment["name"],
            "equipment_location": self._equipment["location"],
            "sensor_id": self._sensor["id"],
            "sensor_type": self._sensor["type"],
            "source_entity_id": self._source_entity_id,
        }


# ============================================================
# DOOR SENSOR
# ============================================================

class EasySmartDoorBinarySensor(EasySmartBaseBinarySensor):

    _attr_device_class = BinarySensorDeviceClass.DOOR

    def __init__(
        self,
        coordinator: EasySmartMonitorCoordinator,
        equipment: dict,
        sensor: dict,
    ) -> None:
        super().__init__(coordinator, equipment, sensor)
        self._attr_name = f"{equipment['name']} Porta"
        self._attr_unique_id = sensor["uuid"]

    @property
    def is_on(self) -> bool:
        state = self._get_source_state()
        return bool(state and state.state == "on")