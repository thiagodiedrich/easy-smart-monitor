from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL_VIRTUAL,
)


# ============================================================
# SENSOR GLOBAL — STATUS DA INTEGRAÇÃO
# ============================================================

class EasySmartMonitorIntegrationStatusSensor(
    CoordinatorEntity, SensorEntity
):
    """Sensor de status global da integração."""

    _attr_has_entity_name = True
    _attr_name = "Status"
    _attr_icon = "mdi:lan-connect"

    def __init__(self, coordinator, name, unique_id, device_info: DeviceInfo):
        super().__init__(coordinator)
        self._attr_unique_id = unique_id
        self._attr_device_info = device_info
        self._attr_name = name

    @property
    def native_value(self):
        return self.coordinator.integration_status

    @property
    def extra_state_attributes(self):
        return {
            "queue_size": self.coordinator.queue_size,
            "last_successful_sync": self.coordinator.last_successful_sync,
        }


# ============================================================
# SENSOR POR EQUIPAMENTO — STATUS
# ============================================================

class EasySmartMonitorEquipmentStatusSensor(
    CoordinatorEntity, SensorEntity
):
    """Sensor de status do equipamento."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:alert-circle-outline"

    def __init__(self, coordinator, equipment: dict, device_info: DeviceInfo):
        super().__init__(coordinator)
        self.equipment = equipment
        self._attr_unique_id = f"{equipment['uuid']}_status"
        self._attr_name = "Status"
        self._attr_device_info = device_info

    @property
    def native_value(self):
        return self.coordinator.equipment_status.get(
            self.equipment["id"]
        )

    @property
    def extra_state_attributes(self):
        return self.coordinator.equipment_status_details.get(
            self.equipment["id"], {}
        )


# ============================================================
# SENSOR POR EQUIPAMENTO — TEMPERATURA
# ============================================================

class EasySmartMonitorTemperatureSensor(
    CoordinatorEntity, SensorEntity
):
    """Sensor de temperatura do equipamento."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "°C"
    _attr_device_class = "temperature"

    def __init__(self, coordinator, equipment: dict, device_info: DeviceInfo):
        super().__init__(coordinator)
        self.equipment = equipment
        self._attr_unique_id = f"{equipment['uuid']}_temperature"
        self._attr_name = "Temperatura"
        self._attr_device_info = device_info

    @property
    def native_value(self):
        return self.coordinator.numeric_states[
            self.equipment["id"]
        ].get("temperature")


# ============================================================
# SENSOR POR EQUIPAMENTO — UMIDADE
# ============================================================

class EasySmartMonitorHumiditySensor(
    CoordinatorEntity, SensorEntity
):
    """Sensor de umidade do equipamento."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "%"
    _attr_device_class = "humidity"

    def __init__(self, coordinator, equipment: dict, device_info: DeviceInfo):
        super().__init__(coordinator)
        self.equipment = equipment
        self._attr_unique_id = f"{equipment['uuid']}_humidity"
        self._attr_name = "Umidade"
        self._attr_device_info = device_info

    @property
    def native_value(self):
        return self.coordinator.numeric_states[
            self.equipment["id"]
        ].get("humidity")