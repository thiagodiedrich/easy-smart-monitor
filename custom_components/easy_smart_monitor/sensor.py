from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EasySmartMonitorCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """
    Cria dinamicamente sensores reais do Home Assistant
    a partir dos equipamentos e sensores configurados no Options Flow.
    """
    coordinator: EasySmartMonitorCoordinator = hass.data[DOMAIN][entry.entry_id]

    equipments: dict[str, Any] = entry.options.get("equipments", {})
    entities: list[SensorEntity] = []

    for equipment in equipments.values():
        equipment_name = equipment["name"]

        for sensor in equipment.get("sensors", {}).values():
            if not sensor.get("enabled", True):
                continue

            sensor_type = sensor.get("type")

            if sensor_type == "temperature":
                entities.append(
                    EasySmartTemperatureSensor(
                        coordinator=coordinator,
                        equipment=equipment,
                        sensor=sensor,
                    )
                )

            elif sensor_type == "energy":
                entities.append(
                    EasySmartEnergySensor(
                        coordinator=coordinator,
                        equipment=equipment,
                        sensor=sensor,
                    )
                )

    if entities:
        async_add_entities(entities)


# ============================================================
# BASE SENSOR
# ============================================================

class EasySmartBaseSensor(CoordinatorEntity, SensorEntity):
    """
    Classe base para sensores que espelham sensores já existentes no HA.
    """

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

    def _get_source_state(self):
        return self.hass.states.get(self._source_entity_id)


# ============================================================
# TEMPERATURE SENSOR
# ============================================================

class EasySmartTemperatureSensor(EasySmartBaseSensor):
    _attr_device_class = "temperature"
    _attr_native_unit_of_measurement = "°C"

    def __init__(
        self,
        coordinator: EasySmartMonitorCoordinator,
        equipment: dict,
        sensor: dict,
    ) -> None:
        super().__init__(coordinator, equipment, sensor)
        self._attr_name = f"{equipment['name']} Temperatura"
        self._attr_unique_id = sensor["uuid"]

    @property
    def native_value(self) -> float | None:
        state = self._get_source_state()
        if not state:
            return None

        try:
            return float(state.state)
        except (ValueError, TypeError):
            _LOGGER.debug(
                "Estado inválido para temperatura (%s): %s",
                self._source_entity_id,
                state.state,
            )
            return None


# ============================================================
# ENERGY SENSOR (Potência / Consumo genérico)
# ============================================================

class EasySmartEnergySensor(EasySmartBaseSensor):
    _attr_device_class = "energy"
    _attr_native_unit_of_measurement = "kWh"

    def __init__(
        self,
        coordinator: EasySmartMonitorCoordinator,
        equipment: dict,
        sensor: dict,
    ) -> None:
        super().__init__(coordinator, equipment, sensor)
        self._attr_name = f"{equipment['name']} Energia"
        self._attr_unique_id = sensor["uuid"]

    @property
    def native_value(self) -> float | None:
        state = self._get_source_state()
        if not state:
            return None

        try:
            return float(state.state)
        except (ValueError, TypeError):
            _LOGGER.debug(
                "Estado inválido para energia (%s): %s",
                self._source_entity_id,
                state.state,
            )
            return None