from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL_VIRTUAL,
)
from .storage import EasySmartMonitorStorage
from .coordinator import EasySmartMonitorCoordinator


# ============================================================
# SETUP DA PLATAFORMA
# ============================================================

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: EasySmartMonitorCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]
    storage: EasySmartMonitorStorage = coordinator.storage

    entities: list[NumberEntity] = []

    for equipment_id, equipment in storage.get_equipments().items():
        device_info = DeviceInfo(
            identifiers={(DOMAIN, equipment_id)},
            name=equipment["name"],
            manufacturer=MANUFACTURER,
            model=MODEL_VIRTUAL,
            suggested_area=equipment.get("location"),
        )

        entities.extend(
            [
                EasySmartMonitorCollectIntervalNumber(
                    coordinator,
                    storage,
                    equipment_id,
                    device_info,
                ),
                EasySmartMonitorDoorTimeoutNumber(
                    coordinator,
                    storage,
                    equipment_id,
                    device_info,
                ),
            ]
        )

    async_add_entities(entities)


# ============================================================
# NUMBER — INTERVALO DE COLETA
# ============================================================

class EasySmartMonitorCollectIntervalNumber(
    CoordinatorEntity, NumberEntity
):
    """Intervalo de coleta do equipamento (segundos)."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:timer-outline"
    _attr_native_min_value = 10
    _attr_native_max_value = 3600
    _attr_native_step = 10
    _attr_native_unit_of_measurement = "s"

    def __init__(
        self,
        coordinator: EasySmartMonitorCoordinator,
        storage: EasySmartMonitorStorage,
        equipment_id: str,
        device_info: DeviceInfo,
    ):
        super().__init__(coordinator)
        self.storage = storage
        self.equipment_id = equipment_id

        self._attr_name = "Intervalo de Coleta"
        self._attr_unique_id = f"{equipment_id}_collect_interval"
        self._attr_device_info = device_info

    @property
    def native_value(self):
        equipment = self.storage.get_equipment(self.equipment_id)
        return equipment.get("collect_interval", 30)

    async def async_set_native_value(self, value: float):
        await self.storage.set_collect_interval(
            self.equipment_id, int(value)
        )
        self.coordinator.async_set_updated_data({})


# ============================================================
# NUMBER — TEMPO DE PORTA ABERTA
# ============================================================

class EasySmartMonitorDoorTimeoutNumber(
    CoordinatorEntity, NumberEntity
):
    """Tempo máximo de porta aberta (segundos)."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:door-open"
    _attr_native_min_value = 10
    _attr_native_max_value = 900
    _attr_native_step = 10
    _attr_native_unit_of_measurement = "s"

    def __init__(
        self,
        coordinator: EasySmartMonitorCoordinator,
        storage: EasySmartMonitorStorage,
        equipment_id: str,
        device_info: DeviceInfo,
    ):
        super().__init__(coordinator)
        self.storage = storage
        self.equipment_id = equipment_id

        self._attr_name = "Tempo Porta Aberta"
        self._attr_unique_id = f"{equipment_id}_door_timeout"
        self._attr_device_info = device_info

    @property
    def native_value(self):
        equipment = self.storage.get_equipment(self.equipment_id)
        return equipment.get("door", {}).get("open_timeout", 120)

    async def async_set_native_value(self, value: float):
        await self.storage.set_door_config(
            self.equipment_id,
            open_timeout=int(value),
        )
        self.coordinator.async_set_updated_data({})