from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN


class EasySmartMonitorSilenceAlarmButton(CoordinatorEntity, ButtonEntity):
    """Botão para silenciar o alarme do equipamento."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:bell-off"

    def __init__(
        self,
        coordinator,
        *,
        equipment: dict,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)

        self._equipment_id = equipment["id"]

        self._attr_name = "Silenciar Alarme"
        self._attr_unique_id = f"{equipment['uuid']}_silence_alarm"
        self._attr_device_info = device_info

    async def async_press(self) -> None:
        """Executa a ação de silenciar o alarme."""
        await self.coordinator.async_silence_siren(self._equipment_id)