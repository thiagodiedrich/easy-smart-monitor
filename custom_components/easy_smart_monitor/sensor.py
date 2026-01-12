from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL_VIRTUAL,
)
from .coordinator import EasySmartMonitorCoordinator


# ============================================================
# HELPERS
# ============================================================

def _get_equipments(entry) -> list[dict]:
    """
    Retorna lista de equipamentos da ConfigEntry.

    Prioridade:
    1. entry.options (quando OptionsFlow existir)
    2. entry.data (configuração inicial)
    """
    return (
        entry.options.get("equipments")
        or entry.data.get("equipments")
        or []
    )


# ============================================================
# SETUP DA PLATAFORMA
# ============================================================

async def async_setup_entry(hass, entry, async_add_entities):
    """Configura sensores do Easy Smart Monitor."""
    coordinator: EasySmartMonitorCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]

    entities: list[SensorEntity] = []

    # --------------------------------------------------------
    # SENSOR GLOBAL DA INTEGRAÇÃO
    # --------------------------------------------------------
    integration_device = DeviceInfo(
        identifiers={(DOMAIN, "integration")},
        name="Easy Smart Monitor",
        manufacturer=MANUFACTURER,
        model=MODEL_VIRTUAL,
    )

    entities.append(
        EasySmartMonitorIntegrationStatusSensor(
            coordinator=coordinator,
            name="Status",
            unique_id=f"{entry.entry_id}_integration_status",
            device_info=integration_device,
        )
    )

    # --------------------------------------------------------
    # SENSORES POR EQUIPAMENTO
    # --------------------------------------------------------
    for equipment in _get_equipments(entry):
        device_info = DeviceInfo(
            identifiers={(DOMAIN, equipment["uuid"])},
            name=equipment["name"],
            manufacturer=MANUFACTURER,
            model=MODEL_VIRTUAL,
            suggested_area=equipment.get("location"),
        )

        entities.extend(
            [
                EasySmartMonitorEquipmentStatusSensor(
                    coordinator, equipment, device_info
                ),
                EasySmartMonitorTemperatureSensor(
                    coordinator, equipment, device_info
                ),
                EasySmartMonitorHumiditySensor(
                    coordinator, equipment, device_info
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
    """Sensor de status global da integração."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:lan-connect"

    def __init__(
        self,
        coordinator: EasySmartMonitorCoordinator,
        name: str,
        unique_id: str,
        device_info: DeviceInfo,
    ):
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_device_info = device_info

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

    def __init__(
        self,
        coordinator: EasySmartMonitorCoordinator,
        equipment: dict,
        device_info: DeviceInfo,
    ):
        super().__init__(coordinator)
        self.equipment = equipment
        self._attr_name = "Status"
        self._attr_unique_id = f"{equipment['uuid']}_status"
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
    _attr_device_class = "temperature"
    _attr_native_unit_of_measurement = "°C"

    def __init__(
        self,
        coordinator: EasySmartMonitorCoordinator,
        equipment: dict,
        device_info: DeviceInfo,
    ):
        super().__init__(coordinator)
        self.equipment = equipment
        self._attr_name = "Temperatura"
        self._attr_unique_id = f"{equipment['uuid']}_temperature"
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
    _attr_device_class = "humidity"
    _attr_native_unit_of_measurement = "%"

    def __init__(
        self,
        coordinator: EasySmartMonitorCoordinator,
        equipment: dict,
        device_info: DeviceInfo,
    ):
        super().__init__(coordinator)
        self.equipment = equipment
        self._attr_name = "Umidade"
        self._attr_unique_id = f"{equipment['uuid']}_humidity"
        self._attr_device_info = device_info

    @property
    def native_value(self):
        return self.coordinator.numeric_states[
            self.equipment["id"]
        ].get("humidity")