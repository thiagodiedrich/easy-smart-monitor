from __future__ import annotations

from homeassistant.components.siren import SirenEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo


class EasySmartMonitorSiren(CoordinatorEntity, SirenEntity):
    """Sirene do equipamento."""

    _attr_has_entity_name = True
    _attr_supported_features = 0

    def __init__(self, coordinator, equipment: dict, device_info: DeviceInfo):
        super().__init__(coordinator)
        self.equipment = equipment
        self._attr_unique_id = f"{equipment['uuid']}_siren"
        self._attr_name = "Alarme"
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