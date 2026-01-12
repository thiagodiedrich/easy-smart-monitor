from __future__ import annotations

from homeassistant.components.siren import SirenEntity
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
    """Configura sirenes do Easy Smart Monitor."""
    coordinator: EasySmartMonitorCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]

    entities: list[SirenEntity] = []

    for equipment in _get_equipments(entry):
        device_info = DeviceInfo(
            identifiers={(DOMAIN, equipment["uuid"])},
            name=equipment["name"],
            manufacturer=MANUFACTURER,
            model=MODEL_VIRTUAL,
            suggested_area=equipment.get("location"),
        )

        entities.append(
            EasySmartMonitorSiren(
                coordinator, equipment, device_info
            )
        )

    async_add_entities(entities)


# ============================================================
# ENTIDADE — SIRENE
# ============================================================

class EasySmartMonitorSiren(
    CoordinatorEntity, SirenEntity
):
    """Sirene do equipamento monitorado."""

    _attr_has_entity_name = True
    _attr_supported_features = 0

    def __init__(
        self,
        coordinator: EasySmartMonitorCoordinator,
        equipment: dict,
        device_info: DeviceInfo,
    ):
        super().__init__(coordinator)
        self.equipment = equipment
        self._attr_name = "Alarme"
        self._attr_unique_id = f"{equipment['uuid']}_siren"
        self._attr_device_info = device_info

    @property
    def is_on(self):
        return self.coordinator.siren_state.get(
            self.equipment["id"], False
        )

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_trigger_siren(
            self.equipment["id"]
        )

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_silence_siren(
            self.equipment["id"]
        )

    @property
    def extra_state_attributes(self):
        return self.coordinator.siren_attributes.get(
            self.equipment["id"], {}
        )