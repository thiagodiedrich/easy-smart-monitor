"""
Testes unitários do EasySmartMonitorApiClient.

Foco:
- TEST_MODE ativo
- Nenhuma chamada HTTP real
- Comportamento previsível
"""

import pytest
import aiohttp

from custom_components.easy_smart_monitor.client import (
    EasySmartMonitorApiClient,
)
from custom_components.easy_smart_monitor.const import TEST_MODE


# ============================================================
# SANITY CHECK
# ============================================================

def test_test_mode_is_enabled():
    """
    Garante que os testes estão rodando em TEST_MODE.
    """
    assert TEST_MODE is True


# ============================================================
# LOGIN
# ============================================================

@pytest.mark.asyncio
async def test_async_login_in_test_mode():
    """
    Login deve ser simulado em TEST_MODE.
    """
    async with aiohttp.ClientSession() as session:
        client = EasySmartMonitorApiClient(
            base_url="http://fake-api",
            username="user",
            password="pass",
            session=session,
        )

        await client.async_login()

        assert client._access_token == "test-token"
        assert client.token_expires_at is None


# ============================================================
# SEND EVENTS
# ============================================================

@pytest.mark.asyncio
async def test_send_events_does_not_fail_in_test_mode():
    """
    Envio de eventos não deve tentar HTTP nem lançar erro.
    """
    async with aiohttp.ClientSession() as session:
        client = EasySmartMonitorApiClient(
            base_url="http://fake-api",
            username="user",
            password="pass",
            session=session,
        )

        events = [
            {"equipment_id": 1, "sensor": "door", "value": "open"},
            {"equipment_id": 1, "sensor": "temperature", "value": 5},
        ]

        # Não deve lançar exceção
        await client.send_events(events)


@pytest.mark.asyncio
async def test_send_events_with_empty_list():
    """
    Lista vazia deve ser ignorada silenciosamente.
    """
    async with aiohttp.ClientSession() as session:
        client = EasySmartMonitorApiClient(
            base_url="http://fake-api",
            username="user",
            password="pass",
            session=session,
        )

        await client.send_events([])


# ============================================================
# GET STATUS
# ============================================================

@pytest.mark.asyncio
async def test_get_status_in_test_mode():
    """
    get_status deve retornar payload simulado em TEST_MODE.
    """
    async with aiohttp.ClientSession() as session:
        client = EasySmartMonitorApiClient(
            base_url="http://fake-api",
            username="user",
            password="pass",
            session=session,
        )

        status = await client.get_status()

        assert isinstance(status, dict)
        assert status["status"] == "test_mode"
        assert "API simulada" in status["message"]


# ============================================================
# INTERNAL REQUEST (TEST MODE)
# ============================================================

@pytest.mark.asyncio
async def test_internal_request_is_mocked_in_test_mode():
    """
    _request não deve executar HTTP real em TEST_MODE.
    """
    async with aiohttp.ClientSession() as session:
        client = EasySmartMonitorApiClient(
            base_url="http://fake-api",
            username="user",
            password="pass",
            session=session,
        )

        response = await client._request(
            method="GET",
            endpoint="/fake-endpoint",
        )

        assert response == {}


# ============================================================
# TOKEN REFRESH
# ============================================================

@pytest.mark.asyncio
async def test_refresh_token_in_test_mode_does_nothing():
    """
    Refresh token não deve alterar estado em TEST_MODE.
    """
    async with aiohttp.ClientSession() as session:
        client = EasySmartMonitorApiClient(
            base_url="http://fake-api",
            username="user",
            password="pass",
            session=session,
        )

        await client.async_login()
        await client.async_refresh_token()

        assert client._access_token == "test-token"