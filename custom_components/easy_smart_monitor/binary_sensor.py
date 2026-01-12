from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN


# ============================================================
# BASE BINARY SENSOR
# ============================================================

class EasySmartMonitorBaseBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Classe base para binary_sensors do Easy Smart Monitor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        *,
        name: str,
        unique_id: str,
        device_info: DeviceInfo,
        equipment_id: int,
        state_key: str,
        attributes_key: str | None = None,
        device_class: BinarySensorDeviceClass | None = None,
        icon: str | None = None,
    ) -> None:
        super().__init__(coordinator)

        self._equipment_id = equipment_id
        self._state_key = state_key
        self._attributes_key = attributes_key

        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_device_info = device_info

        if device_class:
            self._attr_device_class = device_class
        if icon:
            self._attr_icon = icon

    @property
    def is_on(self) -> bool:
        """Retorna o estado binário a partir do coordinator."""
        return bool(
            self.coordinator.binary_states
            .get(self._equipment_id, {})
            .get(self._state_key, False)
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Atributos extras do binary sensor."""
        if not self._attributes_key:
            return {}

        return (
            self.coordinator.binary_attributes
            .get(self._equipment_id, {})
            .get(self._attributes_key, {})
        )


# ============================================================
# BINARY SENSOR — ENERGIA (LIGADO / DESLIGADO)
# ============================================================

class EasySmartMonitorEnergyBinarySensor(EasySmartMonitorBaseBinarySensor):
    """Binary sensor que indica se o equipamento está energizado."""

    def __init__(
        self,
        coordinator,
        *,
        equipment: dict[str, Any],
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(
            coordinator,
            name="Energia",
            unique_id=f"{equipment['uuid']}_energy",
            device_info=device_info,
            equipment_id=equipment["id"],
            state_key="energy_on",
            attributes_key="energy",
            device_class=BinarySensorDeviceClass.POWER,
            icon="mdi:power",
        )


# ============================================================
# BINARY SENSOR — PORTA (ABERTA / FECHADA)
# ============================================================

class EasySmartMonitorDoorBinarySensor(EasySmartMonitorBaseBinarySensor):
    """Binary sensor que indica se a porta está aberta."""

    def __init__(
        self,
        coordinator,
        *,
        equipment: dict[str, Any],
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(
            coordinator,
            name="Porta",
            unique_id=f"{equipment['uuid']}_door",
            device_info=device_info,
            equipment_id=equipment["id"],
            state_key="door_open",
            attributes_key="door",
            device_class=BinarySensorDeviceClass.DOOR,
            icon="mdi:door",
        )