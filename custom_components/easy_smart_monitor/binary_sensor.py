from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
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
    """Retorna equipamentos de options ou data."""
    return (
        entry.options.get("equipments")
        or entry.data.get("equipments")
        or []
    )


# ============================================================
# SETUP DA PLATAFORMA
# ============================================================

async def async_setup_entry(hass, entry, async_add_entities):
    """Configura binary sensors do Easy Smart Monitor."""
    coordinator: EasySmartMonitorCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]

    entities: list[BinarySensorEntity] = []

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
                EasySmartMonitorEnergyBinarySensor(
                    coordinator, equipment, device_info
                ),
                EasySmartMonitorDoorBinarySensor(
                    coordinator, equipment, device_info
                ),
            ]
        )

    async_add_entities(entities)


# ============================================================
# SENSOR BINÁRIO — ENERGIA
# ============================================================

class EasySmartMonitorEnergyBinarySensor(
    CoordinatorEntity, BinarySensorEntity
):
    """Sensor binário de energia do equipamento."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.POWER

    def __init__(
        self,
        coordinator: EasySmartMonitorCoordinator,
        equipment: dict,
        device_info: DeviceInfo,
    ):
        super().__init__(coordinator)
        self.equipment = equipment
        self._attr_name = "Energia"
        self._attr_unique_id = f"{equipment['uuid']}_energy"
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
    """Sensor binário de porta do equipamento."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.DOOR

    def __init__(
        self,
        coordinator: EasySmartMonitorCoordinator,
        equipment: dict,
        device_info: DeviceInfo,
    ):
        super().__init__(coordinator)
        self.equipment = equipment
        self._attr_name = "Porta"
        self._attr_unique_id = f"{equipment['uuid']}_door"
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