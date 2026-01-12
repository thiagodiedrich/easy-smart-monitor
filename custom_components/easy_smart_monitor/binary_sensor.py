from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo


# ============================================================
# SENSOR BINÁRIO — ENERGIA
# ============================================================

class EasySmartMonitorEnergyBinarySensor(
    CoordinatorEntity, BinarySensorEntity
):
    """Sensor binário de energia."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.POWER

    def __init__(self, coordinator, equipment: dict, device_info: DeviceInfo):
        super().__init__(coordinator)
        self.equipment = equipment
        self._attr_unique_id = f"{equipment['uuid']}_energy"
        self._attr_name = "Energia"
        self._attr_device_info = device_info

    @property
    def is_on(self):
        return self.coordinator.binary_states[
            self.equipment["id"]
        ].get("energy_on")

    @property
    def extra_state_attributes(self):
        return self.coordinator.binary_attributes[
            self.equipment["id"]
        ].get("energy", {})


# ============================================================
# SENSOR BINÁRIO — PORTA
# ============================================================

class EasySmartMonitorDoorBinarySensor(
    CoordinatorEntity, BinarySensorEntity
):
    """Sensor binário de porta."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.DOOR

    def __init__(self, coordinator, equipment: dict, device_info: DeviceInfo):
        super().__init__(coordinator)
        self.equipment = equipment
        self._attr_unique_id = f"{equipment['uuid']}_door"
        self._attr_name = "Porta"
        self._attr_device_info = device_info

    @property
    def is_on(self):
        return self.coordinator.binary_states[
            self.equipment["id"]
        ].get("door_open")

    @property
    def extra_state_attributes(self):
        return self.coordinator.binary_attributes[
            self.equipment["id"]
        ].get("door", {})