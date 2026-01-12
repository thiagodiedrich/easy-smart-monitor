"""
Easy Smart Monitor - Coordinator Tests (v1.1.0)

Este arquivo contém os testes unitários do EasySmartMonitorCoordinator,
incluindo as FEATURES da v1.1.0:

FEATURE 1:
- Timeout de porta configurável por equipamento
- enable_siren por equipamento

FEATURE 2:
- Alertas de temperatura (min / max)
- Mudança de status do equipamento quando fora da faixa

Objetivos gerais:
- Garantir funcionamento correto em TEST_MODE
- Validar inicialização do coordinator
- Testar processamento de sensores
- Validar lógica de porta aberta com timeout configurável
- Garantir que enable_siren=False bloqueia o alarme
- Validar cancelamento de timer ao fechar porta
- Testar disparo e silenciamento da sirene
- Validar alertas de temperatura
- Garantir funcionamento da fila local de eventos

Compatível com:
- Home Assistant 2024.12+
- pytest + pytest-asyncio
- Easy Smart Monitor v1.1.0
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
    """
    Garante que os testes estão sendo executados em TEST_MODE.
    """
    assert TEST_MODE is True


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def mock_entry():
    """
    Mock de ConfigEntry com:
    - Um equipamento
    - Sensor de porta
    - Sensor de temperatura
    - Configuração de porta (v1.1.0)
    - Configuração de temperatura (v1.1.0)
    """

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
                    "door": {
                        "enable_siren": True,
                        "open_timeout": DEFAULT_DOOR_OPEN_SECONDS,
                    },
                    "temperature": {
                        "enabled": True,
                        "min": -22.0,
                        "max": -16.0,
                    },
                    "sensors": [
                        {
                            "id": 1,
                            "uuid": "sensor-door-uuid",
                            "entity_id": "binary_sensor.door_test",
                            "type": "door",
                            "enabled": True,
                        },
                        {
                            "id": 2,
                            "uuid": "sensor-temp-uuid",
                            "entity_id": "sensor.temp_test",
                            "type": "temperature",
                            "enabled": True,
                        },
                    ],
                }
            ]
        }

    return Entry()


@pytest.fixture
def mock_api_client():
    """
    Mock simples do cliente de API.
    Em TEST_MODE, não há chamadas externas.
    """

    class Client:
        async def send_events(self, events):
            return None

    return Client()


# ============================================================
# TESTES — INICIALIZAÇÃO
# ============================================================

@pytest.mark.asyncio
async def test_coordinator_initialize(
    hass: HomeAssistant,
    mock_entry,
    mock_api_client,
):
    """
    Verifica se o coordinator inicializa corretamente os estados.
    """
    coordinator = EasySmartMonitorCoordinator(
        hass=hass,
        api_client=mock_api_client,
        entry=mock_entry,
    )

    await coordinator.async_initialize()

    assert coordinator.queue_size == 0
    assert coordinator.equipment_status[1] == EQUIPMENT_STATUS_OK
    assert coordinator.siren_state[1] is False
    assert coordinator.numeric_states[1]["temperature"] is None


# ============================================================
# TESTES — ALERTAS DE TEMPERATURA (FEATURE 2)
# ============================================================

@pytest.mark.asyncio
async def test_temperature_within_range_does_not_trigger_alert(
    hass: HomeAssistant,
    mock_entry,
    mock_api_client,
):
    """
    Temperatura dentro da faixa configurada não deve alterar status.
    """
    coordinator = EasySmartMonitorCoordinator(
        hass=hass,
        api_client=mock_api_client,
        entry=mock_entry,
    )

    await coordinator.async_initialize()

    await coordinator._process_sensor_update(
        equipment=mock_entry.options["equipments"][0],
        sensor=mock_entry.options["equipments"][0]["sensors"][1],
        state=-18.0,
        attributes={},
        timestamp=utcnow(),
    )

    assert coordinator.numeric_states[1]["temperature"] == -18.0
    assert coordinator.equipment_status[1] == EQUIPMENT_STATUS_OK


@pytest.mark.asyncio
async def test_temperature_above_max_triggers_alert_status(
    hass: HomeAssistant,
    mock_entry,
    mock_api_client,
):
    """
    Temperatura acima do limite máximo deve alterar o status do equipamento.
    """
    coordinator = EasySmartMonitorCoordinator(
        hass=hass,
        api_client=mock_api_client,
        entry=mock_entry,
    )

    await coordinator.async_initialize()

    await coordinator._process_sensor_update(
        equipment=mock_entry.options["equipments"][0],
        sensor=mock_entry.options["equipments"][0]["sensors"][1],
        state=-10.0,
        attributes={},
        timestamp=utcnow(),
    )

    assert coordinator.numeric_states[1]["temperature"] == -10.0
    assert coordinator.equipment_status[1] != EQUIPMENT_STATUS_OK


@pytest.mark.asyncio
async def test_temperature_below_min_triggers_alert_status(
    hass: HomeAssistant,
    mock_entry,
    mock_api_client,
):
    """
    Temperatura abaixo do limite mínimo deve alterar o status do equipamento.
    """
    coordinator = EasySmartMonitorCoordinator(
        hass=hass,
        api_client=mock_api_client,
        entry=mock_entry,
    )

    await coordinator.async_initialize()

    await coordinator._process_sensor_update(
        equipment=mock_entry.options["equipments"][0],
        sensor=mock_entry.options["equipments"][0]["sensors"][1],
        state=-30.0,
        attributes={},
        timestamp=utcnow(),
    )

    assert coordinator.numeric_states[1]["temperature"] == -30.0
    assert coordinator.equipment_status[1] != EQUIPMENT_STATUS_OK


# ============================================================
# TESTES — PORTA / SIRENE (FEATURE 1)
# ============================================================

@pytest.mark.asyncio
async def test_door_open_triggers_siren_after_timeout(
    hass: HomeAssistant,
    mock_entry,
    mock_api_client,
):
    """
    Porta aberta deve disparar sirene após o timeout configurado.
    """
    mock_entry.options["equipments"][0]["door"]["open_timeout"] = 0.1

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

    await asyncio.sleep(0.15)

    assert coordinator.siren_state[1] is True
    assert coordinator.equipment_status[1] == EQUIPMENT_STATUS_DOOR_OPEN


@pytest.mark.asyncio
async def test_siren_disabled_does_not_trigger(
    hass: HomeAssistant,
    mock_entry,
    mock_api_client,
):
    """
    enable_siren=False impede o disparo da sirene.
    """
    mock_entry.options["equipments"][0]["door"] = {
        "enable_siren": False,
        "open_timeout": 0.1,
    }

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

    await asyncio.sleep(0.2)

    assert coordinator.siren_state[1] is False
    assert coordinator.equipment_status[1] == EQUIPMENT_STATUS_OK


# ============================================================
# TESTES — FILA DE EVENTOS
# ============================================================

@pytest.mark.asyncio
async def test_queue_is_filled_on_sensor_update(
    hass: HomeAssistant,
    mock_entry,
    mock_api_client,
):
    """
    Atualizações de sensores devem gerar eventos na fila.
    """
    coordinator = EasySmartMonitorCoordinator(
        hass=hass,
        api_client=mock_api_client,
        entry=mock_entry,
    )

    await coordinator.async_initialize()

    await coordinator._process_sensor_update(
        equipment=mock_entry.options["equipments"][0],
        sensor=mock_entry.options["equipments"][0]["sensors"][1],
        state=-18.0,
        attributes={},
        timestamp=utcnow(),
    )

    assert coordinator.queue_size == 1
