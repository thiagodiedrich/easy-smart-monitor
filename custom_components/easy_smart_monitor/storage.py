from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_config"


class EasySmartMonitorStorage:
    """
    Camada de persistência do Easy Smart Monitor.

    Responsabilidades:
    - Armazenar equipamentos
    - Armazenar configuração por equipamento
    - Persistir associações de sensores
    - Fornecer API simples para o coordinator e entidades
    """

    def __init__(self, hass: HomeAssistant) -> None:
        self._store = Store[dict[str, Any]](
            hass,
            STORAGE_VERSION,
            STORAGE_KEY,
        )
        self._data: dict[str, Any] = {}

    # =========================================================
    # LOAD / SAVE
    # =========================================================

    async def async_load(self) -> None:
        """Carrega dados persistidos."""
        data = await self._store.async_load()
        self._data = data or {"equipments": {}}

        _LOGGER.debug(
            "Easy Smart Monitor storage carregado: %s", self._data
        )

    async def async_save(self) -> None:
        """Persiste dados no disco."""
        await self._store.async_save(self._data)
        _LOGGER.debug("Easy Smart Monitor storage salvo")

    # =========================================================
    # EQUIPAMENTOS
    # =========================================================

    def get_equipments(self) -> dict[str, dict[str, Any]]:
        """Retorna todos os equipamentos."""
        return self._data.setdefault("equipments", {})

    def get_equipment(self, equipment_id: str) -> dict[str, Any] | None:
        """Retorna um equipamento específico."""
        return self.get_equipments().get(equipment_id)

    async def add_equipment(
        self,
        *,
        equipment_id: str,
        name: str,
        location: str,
    ) -> None:
        """Adiciona um novo equipamento."""
        self.get_equipments()[equipment_id] = {
            "id": equipment_id,
            "name": name,
            "location": location,
            "enabled": True,

            # Configurações
            "collect_interval": 30,
            "door": {
                "enable_siren": True,
                "open_timeout": 120,
            },

            # Associação de sensores HA
            "sensors": {
                "temperature": None,
                "humidity": None,
                "energy": None,
                "door": None,
            },
        }

        await self.async_save()

    async def remove_equipment(self, equipment_id: str) -> None:
        """Remove um equipamento."""
        self.get_equipments().pop(equipment_id, None)
        await self.async_save()

    # =========================================================
    # CONFIGURAÇÃO DO EQUIPAMENTO
    # =========================================================

    async def set_equipment_enabled(
        self, equipment_id: str, enabled: bool
    ) -> None:
        equipment = self.get_equipment(equipment_id)
        if equipment is None:
            return

        equipment["enabled"] = enabled
        await self.async_save()

    async def set_collect_interval(
        self, equipment_id: str, interval: int
    ) -> None:
        equipment = self.get_equipment(equipment_id)
        if equipment is None:
            return

        equipment["collect_interval"] = interval
        await self.async_save()

    async def set_door_config(
        self,
        equipment_id: str,
        *,
        enable_siren: bool | None = None,
        open_timeout: int | None = None,
    ) -> None:
        equipment = self.get_equipment(equipment_id)
        if equipment is None:
            return

        door_cfg = equipment.setdefault("door", {})
        if enable_siren is not None:
            door_cfg["enable_siren"] = enable_siren
        if open_timeout is not None:
            door_cfg["open_timeout"] = open_timeout

        await self.async_save()

    # =========================================================
    # ASSOCIAÇÃO DE SENSORES
    # =========================================================

    async def set_sensor_source(
        self,
        equipment_id: str,
        sensor_type: str,
        entity_id: str | None,
    ) -> None:
        """
        Associa uma entidade do Home Assistant a um tipo de sensor.
        """
        equipment = self.get_equipment(equipment_id)
        if equipment is None:
            return

        sensors = equipment.setdefault("sensors", {})
        sensors[sensor_type] = entity_id

        await self.async_save()

    def get_sensor_source(
        self, equipment_id: str, sensor_type: str
    ) -> str | None:
        equipment = self.get_equipment(equipment_id)
        if equipment is None:
            return None

        return equipment.get("sensors", {}).get(sensor_type)