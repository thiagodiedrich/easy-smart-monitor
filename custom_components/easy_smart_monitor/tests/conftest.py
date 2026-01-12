"""
Configuração global de testes para Easy Smart Monitor.

Responsabilidades:
- Forçar TEST_MODE
- Garantir ambiente limpo
- Disponibilizar fixture hass (Home Assistant)
"""

import os
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component


# ============================================================
# TEST MODE GLOBAL
# ============================================================

@pytest.fixture(autouse=True)
def enable_test_mode(monkeypatch):
    """
    Força TEST_MODE=True para TODOS os testes.

    Isso garante:
    - Nenhuma chamada HTTP real
    - Login simulado
    - Envio de eventos simulado
    """
    monkeypatch.setenv("EASY_SMART_MONITOR_TEST_MODE", "true")
    yield
    monkeypatch.delenv("EASY_SMART_MONITOR_TEST_MODE", raising=False)


# ============================================================
# FIXTURE HOME ASSISTANT
# ============================================================

@pytest.fixture
async def hass(hass: HomeAssistant) -> HomeAssistant:
    """
    Fixture do Home Assistant pronta para uso.

    - Garante que o core está carregado
    - Permite uso de config_entries, states, services
    """
    await async_setup_component(hass, "homeassistant", {})
    return hass


# ============================================================
# FIXTURE UTILITÁRIA — EVENT LOOP
# ============================================================

@pytest.fixture(scope="session")
def event_loop():
    """
    Event loop dedicado para pytest-asyncio.

    Evita warnings e comportamentos inconsistentes.
    """
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()