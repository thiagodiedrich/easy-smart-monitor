"""
Testes do EasySmartMonitorCoordinator.

Foco:
- TEST_MODE ativo
- Pipeline interno
- Lógica de porta aberta -> sirene
- Estados esperados pelas entidades
"""

import asyncio
from datetime import timedelta

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.util.dt import utcnow

from custom_components.easy_smart_monitor.coordinator import (
    EasySmartMonitorCoordinator,
)
from custom_components.easy_smart_monitor.const import (
    DEFAULT_DOOR_OPEN_SECONDS,
    EQUIPMENT_STATUS_OK,
    EQUIPMENT_STATUS_DOOR_OPEN,
    TEST_MODE,
)


# ============================================================
# SANITY CHECK
# ============================================================

def test_test_mode_is_enabled():
    """Garante que TEST_MODE está ativo."""
    assert TEST_MODE is True


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def mock_entry():
    """Mock de ConfigEntry com um equipamento e sensor de porta."""
    class Entry:
        entry_id = "test_entry"
        data = {
            "api_host": "http://fake-api",
            "username": "test",
            "password": "test",
        }
        options = {
            "equipments": [
                {
                    "id": 1,
                    "uuid": "equip-uuid",
                    "name": "Freezer Teste",
                    "location": "Cozinha",
                    "collect_interval": 30,
                    "enabled": True,
                    "sensors": [
                        {
                            "id": 1,
                            "uuid": "sensor-uuid",
                            "entity_id": "binary_sensor.door_test",
                            "type": "door",
                            "enabled": True,
                        }
                    ],
                }
            ]
        }

    return Entry()


@pytest.fixture
def mock_api_client():
    """Mock simples do API client (não usado em TEST_MODE)."""
    class Client:
        async def send_events(self, events):
            return None

    return Client()


# ============================================================
# TESTES
# ============================================================

@pytest.mark.asyncio
async def test_coordinator_initialize(hass: HomeAssistant, mock_entry, mock_api_client):
    """Coordinator inicializa estados corretamente."""
    coordinator = EasySmartMonitorCoordinator(
        hass=hass,
        api_client=mock_api_client,
        entry=mock_entry,
    )

    await coordinator.async_initialize()

    assert coordinator.integration_status in ("online", "test_mode")
    assert coordinator.queue_size == 0
    assert coordinator.equipment_status[1] == EQUIPMENT_STATUS_OK
    assert coordinator.siren_state[1] is False


@pytest.mark.asyncio
async def test_door_open_triggers_siren_after_timeout(
    hass: HomeAssistant,
    mock_entry,
    mock_api_client,
    monkeypatch,
):
    """
    Porta aberta deve disparar sirene após DEFAULT_DOOR_OPEN_SECONDS.
    """
    coordinator = EasySmartMonitorCoordinator(
        hass=hass,
        api_client=mock_api_client,
        entry=mock_entry,
    )

    await coordinator.async_initialize()

    # Reduz timeout para teste rápido
    monkeypatch.setattr(
        "custom_components.easy_smart_monitor.coordinator.DEFAULT_DOOR_OPEN_SECONDS",
        0.1,
    )

    # Simula evento de porta aberta
    await coordinator._process_sensor_update(
        equipment=mock_entry.options["equipments"][0],
        sensor=mock_entry.options["equipments"][0]["sensors"][0],
        state="on",
        attributes={},
        timestamp=utcnow(),
    )

    # Aguarda timer
    await asyncio.sleep(0.15)

    assert coordinator.siren_state[1] is True
    assert coordinator.equipment_status[1] == EQUIPMENT_STATUS_DOOR_OPEN
    assert "triggered_at" in coordinator.siren_attributes[1]


@pytest.mark.asyncio
async def test_door_close_cancels_timer(
    hass: HomeAssistant,
    mock_entry,
    mock_api_client,
    monkeypatch,
):
    """
    Porta fechada antes do timeout não deve disparar sirene.
    """
    coordinator = EasySmartMonitorCoordinator(
        hass=hass,
        api_client=mock_api_client,
        entry=mock_entry,
    )

    await coordinator.async_initialize()

    monkeypatch.setattr(
        "custom_components.easy_smart_monitor.coordinator.DEFAULT_DOOR_OPEN_SECONDS",
        0.2,
    )

    # Porta aberta
    await coordinator._process_sensor_update(
        equipment=mock_entry.options["equipments"][0],
        sensor=mock_entry.options["equipments"][0]["sensors"][0],
        state="on",
        attributes={},
        timestamp=utcnow(),
    )

    # Porta fechada rapidamente
    await coordinator._process_sensor_update(
        equipment=mock_entry.options["equipments"][0],
        sensor=mock_entry.options["equipments"][0]["sensors"][0],
        state="off",
        attributes={},
        timestamp=utcnow() + timedelta(seconds=0.05),
    )

    await asyncio.sleep(0.25)

    assert coordinator.siren_state[1] is False
    assert coordinator.equipment_status[1] == EQUIPMENT_STATUS_OK


@pytest.mark.asyncio
async def test_silence_siren_resets_state(
    hass: HomeAssistant,
    mock_entry,
    mock_api_client,
):
    """Botão de silenciar deve desligar sirene e resetar status."""
    coordinator = EasySmartMonitorCoordinator(
        hass=hass,
        api_client=mock_api_client,
        entry=mock_entry,
    )

    await coordinator.async_initialize()

    # Força sirene ligada
    await coordinator.async_trigger_siren(1)

    assert coordinator.siren_state[1] is True

    await coordinator.async_silence_siren(1)

    assert coordinator.siren_state[1] is False
    assert coordinator.equipment_status[1] == EQUIPMENT_STATUS_OK
    assert coordinator.siren_attributes[1] == {}


@pytest.mark.asyncio
async def test_queue_is_filled_on_sensor_update(
    hass: HomeAssistant,
    mock_entry,
    mock_api_client,
):
    """Qualquer update de sensor deve gerar evento na fila."""
    coordinator = EasySmartMonitorCoordinator(
        hass=hass,
        api_client=mock_api_client,
        entry=mock_entry,
    )

    await coordinator.async_initialize()

    await coordinator._process_sensor_update(
        equipment=mock_entry.options["equipments"][0],
        sensor=mock_entry.options["equipments"][0]["sensors"][0],
        state="on",
        attributes={},
        timestamp=utcnow(),
    )

    assert coordinator.queue_size == 1