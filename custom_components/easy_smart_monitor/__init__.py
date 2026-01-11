from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN
from .client import EasySmartMonitorClient
from .coordinator import EasySmartMonitorCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """
    Setup inicial da integração (YAML).
    Não utilizado — configuração é somente via UI.
    """
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Setup da integração a partir de um Config Entry.
    """
    _LOGGER.info("Inicializando Easy Smart Monitor")

    hass.data.setdefault(DOMAIN, {})

    # ======================================================
    # CLIENT HTTP
    # ======================================================

    client = EasySmartMonitorClient(
        base_url=entry.data["api_url"],
        username=entry.data["username"],
        password=entry.data["password"],
    )

    # ======================================================
    # COORDINATOR
    # ======================================================

    coordinator = EasySmartMonitorCoordinator(
        hass=hass,
        entry=entry,
        client=client,
    )

    # Inicialização explícita (fila + loop)
    await coordinator.async_initialize()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # ======================================================
    # SETUP DAS PLATAFORMAS
    # ======================================================

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Descarrega a integração (reload / remoção).
    """
    _LOGGER.info("Finalizando Easy Smart Monitor")

    coordinator: EasySmartMonitorCoordinator = hass.data[DOMAIN].get(
        entry.entry_id
    )

    if coordinator:
        await coordinator.async_shutdown()

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok