from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN


# ============================================================
# BASE SENSOR
# ============================================================

class EasySmartMonitorBaseSensor(CoordinatorEntity, SensorEntity):
    """Classe base para sensores do Easy Smart Monitor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        *,
        name: str,
        unique_id: str,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_device_info = device_info


# ============================================================
# SENSOR GLOBAL — STATUS DA INTEGRAÇÃO
# ============================================================

class EasySmartMonitorIntegrationStatusSensor(EasySmartMonitorBaseSensor):
    """Sensor que expõe o status global da integração."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_icon = "mdi:cloud-check"

    @property
    def native_value(self) -> str:
        return self.coordinator.integration_status

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "queue_size": self.coordinator.queue_size,
            "last_successful_sync": self.coordinator.last_successful_sync.isoformat()
            if self.coordinator.last_successful_sync
            else None,
        }


# ============================================================
# SENSOR GLOBAL — FILA LOCAL
# ============================================================

class EasySmartMonitorQueueSizeSensor(EasySmartMonitorBaseSensor):
    """Sensor que expõe o tamanho da fila local."""

    _attr_icon = "mdi:database"

    @property
    def native_value(self) -> int:
        return self.coordinator.queue_size


# ============================================================
# SENSOR — STATUS DO EQUIPAMENTO
# ============================================================

class EasySmartMonitorEquipmentStatusSensor(EasySmartMonitorBaseSensor):
    """Sensor de status geral do equipamento."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_icon = "mdi:fridge-outline"

    def __init__(
        self,
        coordinator,
        *,
        equipment: dict[str, Any],
        device_info: DeviceInfo,
    ) -> None:
        self._equipment_id = equipment["id"]

        super().__init__(
            coordinator,
            name="Status",
            unique_id=f"{equipment['uuid']}_status",
            device_info=device_info,
        )

    @property
    def native_value(self) -> str:
        return self.coordinator.equipment_status.get(self._equipment_id, "ok")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.coordinator.equipment_status_details.get(self._equipment_id, {})


# ============================================================
# SENSOR — TEMPERATURA
# ============================================================

class EasySmartMonitorTemperatureSensor(EasySmartMonitorBaseSensor):
    """Sensor de temperatura do equipamento."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = "°C"
    _attr_icon = "mdi:thermometer"

    def __init__(
        self,
        coordinator,
        *,
        equipment: dict[str, Any],
        device_info: DeviceInfo,
    ) -> None:
        self._equipment_id = equipment["id"]

        super().__init__(
            coordinator,
            name="Temperatura",
            unique_id=f"{equipment['uuid']}_temperature",
            device_info=device_info,
        )

    @property
    def native_value(self) -> float | None:
        return (
            self.coordinator.numeric_states
            .get(self._equipment_id, {})
            .get("temperature")
        )


# ============================================================
# SENSOR — UMIDADE
# ============================================================

class EasySmartMonitorHumiditySensor(EasySmartMonitorBaseSensor):
    """Sensor de umidade do equipamento."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:water-percent"

    def __init__(
        self,
        coordinator,
        *,
        equipment: dict[str, Any],
        device_info: DeviceInfo,
    ) -> None:
        self._equipment_id = equipment["id"]

        super().__init__(
            coordinator,
            name="Umidade",
            unique_id=f"{equipment['uuid']}_humidity",
            device_info=device_info,
        )

    @property
    def native_value(self) -> float | None:
        return (
            self.coordinator.numeric_states
            .get(self._equipment_id, {})
            .get("humidity")
        )