from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL_VIRTUAL,
)
from .storage import EasySmartMonitorStorage
from .coordinator import EasySmartMonitorCoordinator


# ============================================================
# HELPERS
# ============================================================

SENSOR_TYPES = {
    "temperature": {
        "name": "Sensor de Temperatura",
        "domain": "sensor",
    },
    "humidity": {
        "name": "Sensor de Umidade",
        "domain": "sensor",
    },
    "energy": {
        "name": "Sensor de Energia",
        "domain": "sensor",
    },
    "door": {
        "name": "Sensor de Porta",
        "domain": "binary_sensor",
    },
}


def _get_entity_options(hass, domain: str) -> list[str]:
    """Lista entidades disponíveis de um domínio."""
    registry = async_get_entity_registry(hass)
    entities = [
        e.entity_id
        for e in registry.entities.values()
        if e.entity_id.startswith(f"{domain}.") and not e.disabled
    ]
    entities.sort()
    return ["Nenhum"] + entities


# ============================================================
# SETUP DA PLATAFORMA
# ============================================================

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: EasySmartMonitorCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]
    storage: EasySmartMonitorStorage = coordinator.storage

    entities: list[SelectEntity] = []

    for equipment_id, equipment in storage.get_equipments().items():
        device_info = DeviceInfo(
            identifiers={(DOMAIN, equipment_id)},
            name=equipment["name"],
            manufacturer=MANUFACTURER,
            model=MODEL_VIRTUAL,
            suggested_area=equipment.get("location"),
        )

        for sensor_type, cfg in SENSOR_TYPES.items():
            entities.append(
                EasySmartMonitorSensorSourceSelect(
                    coordinator,
                    storage,
                    equipment_id,
                    sensor_type,
                    cfg["name"],
                    cfg["domain"],
                    device_info,
                )
            )

    async_add_entities(entities)


# ============================================================
# SELECT — ASSOCIAÇÃO DE SENSOR
# ============================================================

class EasySmartMonitorSensorSourceSelect(
    CoordinatorEntity, SelectEntity
):
    """Seleciona a entidade HA usada como fonte de sensor."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:tune"

    def __init__(
        self,
        coordinator: EasySmartMonitorCoordinator,
        storage: EasySmartMonitorStorage,
        equipment_id: str,
        sensor_type: str,
        name: str,
        domain: str,
        device_info: DeviceInfo,
    ):
        super().__init__(coordinator)
        self.storage = storage
        self.hass = coordinator.hass
        self.equipment_id = equipment_id
        self.sensor_type = sensor_type
        self.domain = domain

        self._attr_name = name
        self._attr_unique_id = (
            f"{equipment_id}_{sensor_type}_source"
        )
        self._attr_device_info = device_info

        self._options = _get_entity_options(
            coordinator.hass, domain
        )

    @property
    def options(self) -> list[str]:
        return self._options

    @property
    def current_option(self) -> str:
        entity_id = self.storage.get_sensor_source(
            self.equipment_id, self.sensor_type
        )
        return entity_id or "Nenhum"

    async def async_select_option(self, option: str) -> None:
        value = None if option == "Nenhum" else option
        await self.storage.set_sensor_source(
            self.equipment_id,
            self.sensor_type,
            value,
        )
        self.coordinator.async_set_updated_data({})