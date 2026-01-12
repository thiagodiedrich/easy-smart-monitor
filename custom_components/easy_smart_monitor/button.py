from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL_VIRTUAL,
)
from .coordinator import EasySmartMonitorCoordinator


# ============================================================
# SETUP DA PLATAFORMA
# ============================================================

async def async_setup_entry(hass, entry, async_add_entities):
    """Configura botões do Easy Smart Monitor."""
    coordinator: EasySmartMonitorCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]

    entities: list[ButtonEntity] = []

    # ----------------------------
    # BOTÕES POR EQUIPAMENTO
    # ----------------------------
    for equipment in entry.options.get("equipments", []):
        device_info = DeviceInfo(
            identifiers={(DOMAIN, equipment["uuid"])},
            name=equipment["name"],
            manufacturer=MANUFACTURER,
            model=MODEL_VIRTUAL,
            suggested_area=equipment.get("location"),
        )

        entities.append(
            EasySmartMonitorSilenceAlarmButton(
                coordinator=coordinator,
                equipment=equipment,
                device_info=device_info,
            )
        )

    async_add_entities(entities)


# ============================================================
# ENTIDADE — BOTÃO
# ============================================================

class EasySmartMonitorSilenceAlarmButton(
    CoordinatorEntity, ButtonEntity
):
    """Botão para silenciar o alarme do equipamento."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:bell-off"

    def __init__(
        self,
        coordinator: EasySmartMonitorCoordinator,
        equipment: dict,
        device_info: DeviceInfo,
    ):
        super().__init__(coordinator)
        self.equipment = equipment
        self._attr_name = "Silenciar Alarme"
        self._attr_unique_id = (
            f"{equipment['uuid']}_silence_alarm"
        )
        self._attr_device_info = device_info

    async def async_press(self) -> None:
        """Executa o silenciamento da sirene."""
        await self.coordinator.async_silence_siren(
            self.equipment["id"]
        )