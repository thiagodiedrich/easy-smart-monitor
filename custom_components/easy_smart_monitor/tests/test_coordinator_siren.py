import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.easy_smart_monitor.coordinator import (
    EasySmartMonitorCoordinator
)


@pytest.mark.asyncio
async def test_door_timer_triggers_siren():
    hass = MagicMock()
    hass.services.async_call = AsyncMock()

    entry = MagicMock()
    entry.options = {
        "equipments": {
            "1": {
                "id": 1,
                "name": "Freezer",
                "sensors": {
                    "1": {
                        "type": "door",
                        "entity_id": "binary_sensor.porta",
                    }
                },
            }
        }
    }

    client = MagicMock()
    coordinator = EasySmartMonitorCoordinator(hass, entry, client)

    with patch("asyncio.sleep", new=AsyncMock()):
        coordinator._is_door_open = MagicMock(return_value=True)
        await coordinator._door_timer_task(1)

    hass.services.async_call.assert_called()