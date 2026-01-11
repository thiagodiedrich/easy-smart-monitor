import pytest
from unittest.mock import AsyncMock, MagicMock

from custom_components.easy_smart_monitor.client import EasySmartMonitorClient


@pytest.mark.asyncio
async def test_client_login_success():
    client = EasySmartMonitorClient(
        "http://api.test",
        "user",
        "pass",
    )

    session = AsyncMock()
    response = AsyncMock()
    response.__aenter__.return_value = response
    response.json.return_value = {"token": "abc123"}
    response.raise_for_status.return_value = None

    session.post.return_value = response

    await client.async_login(session)

    assert client._token == "abc123"


@pytest.mark.asyncio
async def test_send_events_reauth_on_401():
    client = EasySmartMonitorClient(
        "http://api.test",
        "user",
        "pass",
    )

    session = AsyncMock()

    # Primeira chamada retorna 401
    error = Exception()
    error.status = 401

    client._token = "expired"
    client._post_events = AsyncMock(side_effect=[error, None])
    client.async_login = AsyncMock()

    await client.async_send_events(session, [{"event": "x"}])

    assert client.async_login.called