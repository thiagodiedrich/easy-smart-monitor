from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
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
    Cria dinamicamente botões de RESET de sirene para cada EQUIPAMENTO.
    """
    coordinator: EasySmartMonitorCoordinator = hass.data[DOMAIN][entry.entry_id]

    equipments: dict[str, Any] = entry.options.get("equipments", {})
    entities: list[ButtonEntity] = []

    for equipment in equipments.values():
        entities.append(
            EasySmartResetSirenButton(
                coordinator=coordinator,
                equipment=equipment,
            )
        )

    if entities:
        async_add_entities(entities)


# ============================================================
# RESET SIREN BUTTON
# ============================================================

class EasySmartResetSirenButton(CoordinatorEntity, ButtonEntity):
    """
    Botão para resetar/desligar a sirene de um EQUIPAMENTO.
    """

    _attr_icon = "mdi:alarm-off"

    def __init__(
        self,
        coordinator: EasySmartMonitorCoordinator,
        equipment: dict,
    ) -> None:
        super().__init__(coordinator)
        self._equipment = equipment

        self._attr_name = f"{equipment['name']} Reset Sirene"
        self._attr_unique_id = f"{equipment['uuid']}_reset_siren"

    async def async_press(self) -> None:
        """
        Ao pressionar o botão:
        - desliga a sirene
        - reseta estado lógico (usado depois pela automação de 120s)
        """
        _LOGGER.debug(
            "Reset de sirene acionado para equipamento %s",
            self._equipment["name"],
        )

        # 🔔 Desliga a sirene associada a este equipamento
        siren_entity_id = f"switch.{self._equipment['name'].lower().replace(' ', '_')}_sirene"

        if self.hass.states.get(siren_entity_id):
            await self.hass.services.async_call(
                "switch",
                "turn_off",
                {"entity_id": siren_entity_id},
                blocking=False,
            )

        # 🔁 Marca no coordinator que o reset foi acionado
        if hasattr(self.coordinator, "reset_siren"):
            self.coordinator.reset_siren(self._equipment["id"])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "equipment_id": self._equipment["id"],
            "equipment_name": self._equipment["name"],
            "equipment_location": self._equipment["location"],
            "type": "reset_button",
        }