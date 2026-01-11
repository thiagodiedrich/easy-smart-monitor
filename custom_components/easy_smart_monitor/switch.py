from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EasySmartMonitorCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """
    Cria dinamicamente switches de SIRENE para cada EQUIPAMENTO.
    """
    coordinator: EasySmartMonitorCoordinator = hass.data[DOMAIN][entry.entry_id]

    equipments: dict[str, Any] = entry.options.get("equipments", {})
    entities: list[SwitchEntity] = []

    for equipment in equipments.values():
        entities.append(
            EasySmartSirenSwitch(
                coordinator=coordinator,
                equipment=equipment,
            )
        )

    if entities:
        async_add_entities(entities)


# ============================================================
# SIRENE SWITCH
# ============================================================

class EasySmartSirenSwitch(CoordinatorEntity, SwitchEntity):
    """
    Switch virtual de sirene por EQUIPAMENTO.
    """

    _attr_icon = "mdi:alarm-bell"

    def __init__(
        self,
        coordinator: EasySmartMonitorCoordinator,
        equipment: dict,
    ) -> None:
        super().__init__(coordinator)
        self._equipment = equipment
        self._is_on: bool = False

        self._attr_name = f"{equipment['name']} Sirene"
        self._attr_unique_id = f"{equipment['uuid']}_siren"

    @property
    def is_on(self) -> bool:
        return self._is_on

    async def async_turn_on(self, **kwargs) -> None:
        """
        Liga a sirene (virtual).
        """
        _LOGGER.debug(
            "Sirene ligada manualmente para equipamento %s",
            self._equipment["name"],
        )
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """
        Desliga a sirene (virtual).
        """
        _LOGGER.debug(
            "Sirene desligada manualmente para equipamento %s",
            self._equipment["name"],
        )
        self._is_on = False
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "equipment_id": self._equipment["id"],
            "equipment_name": self._equipment["name"],
            "equipment_location": self._equipment["location"],
            "type": "siren",
        }