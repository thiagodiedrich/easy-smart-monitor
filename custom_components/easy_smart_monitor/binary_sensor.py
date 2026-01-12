from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
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

    entities: list[BinarySensorEntity] = []

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

        entities.append(
            EasySmartMonitorDoorBinarySensor(
                coordinator, equipment_id, device_info
            )
        )

    async_add_entities(entities)


# ============================================================
# SENSOR BINÁRIO — PORTA
# ============================================================

class EasySmartMonitorDoorBinarySensor(
    CoordinatorEntity, BinarySensorEntity
):
    """Estado da porta do equipamento."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.DOOR

    def __init__(
        self,
        coordinator: EasySmartMonitorCoordinator,
        equipment_id: str,
        device_info: DeviceInfo,
    ):
        super().__init__(coordinator)
        self.equipment_id = equipment_id
        self._attr_name = "Porta"
        self._attr_unique_id = f"{equipment_id}_door"
        self._attr_device_info = device_info

    @property
    def is_on(self) -> bool | None:
        source = self.coordinator.storage.get_sensor_source(
            self.equipment_id, "door"
        )
        if not source:
            return None

        state = self.coordinator.hass.states.get(source)
        if not state:
            return None

        return state.state == "on"