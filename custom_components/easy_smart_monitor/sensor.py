from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL_VIRTUAL
from .coordinator import EasySmartMonitorCoordinator


# ============================================================
# SETUP DA PLATAFORMA
# ============================================================

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: EasySmartMonitorCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]

    entities: list[SensorEntity] = []

    # ----------------------------
    # SENSOR GLOBAL — STATUS
    # ----------------------------
    entities.append(
        EasySmartMonitorIntegrationStatusSensor(coordinator)
    )

    # ----------------------------
    # SENSORES POR EQUIPAMENTO
    # ----------------------------
    for equipment_id, equipment in (
        coordinator.storage.get_equipments().items()
    ):
        device_info = DeviceInfo(
            identifiers={(DOMAIN, equipment_id)},
            name=equipment["name"],
            manufacturer=MANUFACTURER,
            model=MODEL_VIRTUAL,
            suggested_area=equipment.get("location"),
        )

        entities.extend(
            [
                EasySmartMonitorTemperatureSensor(
                    coordinator, equipment_id, device_info
                ),
                EasySmartMonitorHumiditySensor(
                    coordinator, equipment_id, device_info
                ),
                EasySmartMonitorEnergySensor(
                    coordinator, equipment_id, device_info
                ),
            ]
        )

    async_add_entities(entities)


# ============================================================
# SENSOR GLOBAL — STATUS DA INTEGRAÇÃO
# ============================================================

class EasySmartMonitorIntegrationStatusSensor(
    CoordinatorEntity, SensorEntity
):
    """Status geral da integração."""

    _attr_has_entity_name = True
    _attr_name = "Status"
    _attr_icon = "mdi:lan-connect"

    def __init__(self, coordinator: EasySmartMonitorCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_integration_status"

    @property
    def native_value(self):
        if self.coordinator.last_successful_sync:
            return "online"
        return "idle"

    @property
    def extra_state_attributes(self):
        return {
            "queue_size": self.coordinator.queue_size,
            "last_successful_sync": self.coordinator.last_successful_sync,
        }


# ============================================================
# SENSOR — TEMPERATURA
# ============================================================

class EasySmartMonitorTemperatureSensor(
    CoordinatorEntity, SensorEntity
):
    """Temperatura do equipamento."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = "°C"

    def __init__(
        self,
        coordinator: EasySmartMonitorCoordinator,
        equipment_id: str,
        device_info: DeviceInfo,
    ):
        super().__init__(coordinator)
        self.equipment_id = equipment_id
        self._attr_name = "Temperatura"
        self._attr_unique_id = f"{equipment_id}_temperature"
        self._attr_device_info = device_info

    @property
    def native_value(self):
        source = self.coordinator.storage.get_sensor_source(
            self.equipment_id, "temperature"
        )
        if not source:
            return None

        state = self.coordinator.hass.states.get(source)
        if not state or state.state in ("unknown", "unavailable"):
            return None

        try:
            return float(state.state)
        except ValueError:
            return None


# ============================================================
# SENSOR — UMIDADE
# ============================================================

class EasySmartMonitorHumiditySensor(
    CoordinatorEntity, SensorEntity
):
    """Umidade do equipamento."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = "%"

    def __init__(
        self,
        coordinator: EasySmartMonitorCoordinator,
        equipment_id: str,
        device_info: DeviceInfo,
    ):
        super().__init__(coordinator)
        self.equipment_id = equipment_id
        self._attr_name = "Umidade"
        self._attr_unique_id = f"{equipment_id}_humidity"
        self._attr_device_info = device_info

    @property
    def native_value(self):
        source = self.coordinator.storage.get_sensor_source(
            self.equipment_id, "humidity"
        )
        if not source:
            return None

        state = self.coordinator.hass.states.get(source)
        if not state or state.state in ("unknown", "unavailable"):
            return None

        try:
            return float(state.state)
        except ValueError:
            return None


# ============================================================
# SENSOR — ENERGIA
# ============================================================

class EasySmartMonitorEnergySensor(
    CoordinatorEntity, SensorEntity
):
    """Energia do equipamento."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.ENERGY

    def __init__(
        self,
        coordinator: EasySmartMonitorCoordinator,
        equipment_id: str,
        device_info: DeviceInfo,
    ):
        super().__init__(coordinator)
        self.equipment_id = equipment_id
        self._attr_name = "Energia"
        self._attr_unique_id = f"{equipment_id}_energy"
        self._attr_device_info = device_info

    @property
    def native_value(self):
        source = self.coordinator.storage.get_sensor_source(
            self.equipment_id, "energy"
        )
        if not source:
            return None

        state = self.coordinator.hass.states.get(source)
        if not state or state.state in ("unknown", "unavailable"):
            return None

        try:
            return float(state.state)
        except ValueError:
            return None