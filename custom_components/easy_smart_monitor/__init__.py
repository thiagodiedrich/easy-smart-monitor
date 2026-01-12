from __future__ import annotations

import logging

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import EasySmartMonitorCoordinator
from .client import EasySmartMonitorApiClient

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Setup inicial da integração."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Configura Easy Smart Monitor a partir de uma ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})

    # 🔹 Sessão HTTP compartilhada
    session = aiohttp.ClientSession()

    api_client = EasySmartMonitorApiClient(
        base_url=entry.data["api_host"],
        username=entry.data["username"],
        password=entry.data["password"],
        session=session,
    )

    coordinator = EasySmartMonitorCoordinator(
        hass=hass,
        api_client=api_client,
        entry=entry,
    )

    # ⚠️ CRÍTICO: armazenar o coordinator diretamente
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await coordinator.async_initialize()

    await hass.config_entries.async_forward_entry_setups(
        entry, PLATFORMS
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Remove a integração."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )

    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)

        # Fecha a sessão HTTP
        await coordinator.api_client._session.close()

        await coordinator.async_shutdown()

    return unload_ok