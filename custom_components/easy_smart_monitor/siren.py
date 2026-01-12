from __future__ import annotations

from typing import Any

from homeassistant.components.siren import SirenEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN


class EasySmartMonitorSiren(CoordinatorEntity, SirenEntity):
    """Entidade de sirene do Easy Smart Monitor."""

    _attr_has_entity_name = True
    _attr_supported_features = 0
    _attr_icon = "mdi:alarm-bell"

    def __init__(
        self,
        coordinator,
        *,
        equipment: dict[str, Any],
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)

        self._equipment_id = equipment["id"]

        self._attr_name = "Alarme"
        self._attr_unique_id = f"{equipment['uuid']}_siren"
        self._attr_device_info = device_info

    # ------------------------------------------------------------
    # STATE
    # ------------------------------------------------------------

    @property
    def is_on(self) -> bool:
        """Indica se a sirene está ligada."""
        return bool(
            self.coordinator.siren_state.get(self._equipment_id, False)
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Atributos extras da sirene."""
        return (
            self.coordinator.siren_attributes
            .get(self._equipment_id, {})
        )

    # ------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Liga a sirene manualmente."""
        await self.coordinator.async_trigger_siren(self._equipment_id)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Desliga a sirene manualmente."""
        await self.coordinator.async_silence_siren(self._equipment_id)