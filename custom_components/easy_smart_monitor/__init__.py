from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .const import DOMAIN, PLATFORMS
from .client import EasySmartMonitorApiClient
from .coordinator import EasySmartMonitorCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """
    Setup inicial da integração.
    Não utiliza YAML, apenas retorna True para compatibilidade.
    """
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Configura a integração a partir de uma ConfigEntry.
    Cria client, coordinator e registra as plataformas.
    """
    hass.data.setdefault(DOMAIN, {})

    session = aiohttp_client.async_get_clientsession(hass)

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

    await coordinator.async_initialize()

    hass.data[DOMAIN][entry.entry_id] = {
        "client": api_client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    _LOGGER.info("Easy Smart Monitor inicializado com sucesso")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Remove a integração e descarrega todas as plataformas.
    Garante cancelamento de tasks e persistência correta.
    """
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        coordinator: EasySmartMonitorCoordinator = data["coordinator"]

        await coordinator.async_shutdown()

        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)

        _LOGGER.info("Easy Smart Monitor descarregado com sucesso")

    return unload_ok