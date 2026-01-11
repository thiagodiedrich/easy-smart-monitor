import pytest
from unittest.mock import AsyncMock, MagicMock

from custom_components.easy_smart_monitor.coordinator import (
    EasySmartMonitorCoordinator
)


@pytest.mark.asyncio
async def test_enqueue_and_persist_queue():
    hass = MagicMock()
    entry = MagicMock()
    entry.options = {}

    client = MagicMock()
    coordinator = EasySmartMonitorCoordinator(hass, entry, client)

    coordinator._store.async_save = AsyncMock()

    await coordinator._enqueue_event({"event": "test"})

    assert len(coordinator._queue) == 1
    coordinator._store.async_save.assert_called_once()