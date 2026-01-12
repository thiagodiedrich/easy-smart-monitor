"""
Easy Smart Monitor - Entity Tests

Testes unitários das entidades do Easy Smart Monitor.

Cobertura:
- Sensores globais
- Sensores por equipamento
- Binary sensors
- Sirene
- Botão de silenciar
- Estados novos da v1.1.0 (temperature_alert)
- TEST_MODE
"""

import pytest

from homeassistant.helpers.entity import DeviceInfo

from custom_components.easy_smart_monitor.sensor import (
    EasySmartMonitorIntegrationStatusSensor,
    EasySmartMonitorEquipmentStatusSensor,
    EasySmartMonitorTemperatureSensor,
    EasySmartMonitorHumiditySensor,
)
from custom_components.easy_smart_monitor.binary_sensor import (
    EasySmartMonitorEnergyBinarySensor,
    EasySmartMonitorDoorBinarySensor,
)
from custom_components.easy_smart_monitor.siren import (
    EasySmartMonitorSiren,
)
from custom_components.easy_smart_monitor.button import (
    EasySmartMonitorSilenceAlarmButton,
)
from custom_components.easy_smart_monitor.const import (
    DOMAIN,
    EQUIPMENT_STATUS_OK,
    EQUIPMENT_STATUS_DOOR_OPEN,
    EQUIPMENT_STATUS_TEMPERATURE_ALERT,
    TEST_MODE,
)


# ============================================================
# SANITY CHECK
# ============================================================

def test_test_mode_is_enabled():
    """Garante que TEST_MODE está ativo durante os testes."""
    assert TEST_MODE is True


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def device_info():
    """DeviceInfo padrão de equipamento."""
    return DeviceInfo(
        identifiers={(DOMAIN, "equip-uuid")},
        name="Freezer Teste",
        manufacturer="Easy Smart Monitor",
        model="Virtual",
    )


@pytest.fixture
def coordinator_mock():
    """
    Mock do coordinator contendo todos os atributos
    esperados pelas entidades.
    """
    class Coordinator:
        integration_status = "test_mode"
        last_successful_sync = None
        queue_size = 2

        equipment_status = {1: EQUIPMENT_STATUS_OK}
        equipment_status_details = {1: {}}

        numeric_states = {
            1: {
                "temperature": -18.0,
                "humidity": 65.0,
            }
        }

        binary_states = {
            1: {
                "energy_on": True,
                "door_open": False,
            }
        }

        binary_attributes = {
            1: {
                "energy": {
                    "power_w": 120,
                    "voltage_v": 220,
                },
                "door": {},
            }
        }

        siren_state = {1: False}
        siren_attributes = {1: {}}

        async def async_trigger_siren(self, equipment_id: int):
            self.siren_state[equipment_id] = True
            self.equipment_status[equipment_id] = EQUIPMENT_STATUS_DOOR_OPEN

        async def async_silence_siren(self, equipment_id: int):
            self.siren_state[equipment_id] = False
            self.equipment_status[equipment_id] = EQUIPMENT_STATUS_OK
            self.equipment_status_details[equipment_id] = {}

    return Coordinator()


@pytest.fixture
def equipment():
    """Mock de equipamento."""
    return {
        "id": 1,
        "uuid": "equip-uuid",
        "name": "Freezer Teste",
    }


# ============================================================
# SENSOR TESTS
# ============================================================

def test_integration_status_sensor(coordinator_mock, device_info):
    sensor = EasySmartMonitorIntegrationStatusSensor(
        coordinator=coordinator_mock,
        name="Status Integração",
        unique_id="integration_status",
        device_info=device_info,
    )

    assert sensor.native_value == "test_mode"
    assert sensor.extra_state_attributes["queue_size"] == 2


def test_equipment_status_sensor_ok(coordinator_mock, device_info, equipment):
    sensor = EasySmartMonitorEquipmentStatusSensor(
        coordinator=coordinator_mock,
        equipment=equipment,
        device_info=device_info,
    )

    assert sensor.native_value == EQUIPMENT_STATUS_OK
    assert sensor.extra_state_attributes == {}


def test_equipment_status_sensor_temperature_alert(
    coordinator_mock, device_info, equipment
):
    coordinator_mock.equipment_status[1] = EQUIPMENT_STATUS_TEMPERATURE_ALERT
    coordinator_mock.equipment_status_details[1] = {
        "reason": "above_max",
        "value": -10.0,
        "max": -16.0,
    }

    sensor = EasySmartMonitorEquipmentStatusSensor(
        coordinator=coordinator_mock,
        equipment=equipment,
        device_info=device_info,
    )

    assert sensor.native_value == EQUIPMENT_STATUS_TEMPERATURE_ALERT
    assert sensor.extra_state_attributes["reason"] == "above_max"
    assert sensor.extra_state_attributes["value"] == -10.0


def test_temperature_sensor(coordinator_mock, device_info, equipment):
    sensor = EasySmartMonitorTemperatureSensor(
        coordinator=coordinator_mock,
        equipment=equipment,
        device_info=device_info,
    )

    assert sensor.native_value == -18.0


def test_humidity_sensor(coordinator_mock, device_info, equipment):
    sensor = EasySmartMonitorHumiditySensor(
        coordinator=coordinator_mock,
        equipment=equipment,
        device_info=device_info,
    )

    assert sensor.native_value == 65.0


# ============================================================
# BINARY SENSOR TESTS
# ============================================================

def test_energy_binary_sensor(coordinator_mock, device_info, equipment):
    sensor = EasySmartMonitorEnergyBinarySensor(
        coordinator=coordinator_mock,
        equipment=equipment,
        device_info=device_info,
    )

    assert sensor.is_on is True
    assert sensor.extra_state_attributes["power_w"] == 120


def test_door_binary_sensor(coordinator_mock, device_info, equipment):
    sensor = EasySmartMonitorDoorBinarySensor(
        coordinator=coordinator_mock,
        equipment=equipment,
        device_info=device_info,
    )

    assert sensor.is_on is False


# ============================================================
# SIREN TESTS
# ============================================================

@pytest.mark.asyncio
async def test_siren_turn_on(coordinator_mock, device_info, equipment):
    siren = EasySmartMonitorSiren(
        coordinator=coordinator_mock,
        equipment=equipment,
        device_info=device_info,
    )

    assert siren.is_on is False

    await siren.async_turn_on()

    assert coordinator_mock.siren_state[1] is True
    assert coordinator_mock.equipment_status[1] == EQUIPMENT_STATUS_DOOR_OPEN


@pytest.mark.asyncio
async def test_siren_turn_off(coordinator_mock, device_info, equipment):
    siren = EasySmartMonitorSiren(
        coordinator=coordinator_mock,
        equipment=equipment,
        device_info=device_info,
    )

    coordinator_mock.siren_state[1] = True

    await siren.async_turn_off()

    assert coordinator_mock.siren_state[1] is False
    assert coordinator_mock.equipment_status[1] == EQUIPMENT_STATUS_OK


# ============================================================
# BUTTON TESTS
# ============================================================

@pytest.mark.asyncio
async def test_silence_alarm_button(coordinator_mock, device_info, equipment):
    button = EasySmartMonitorSilenceAlarmButton(
        coordinator=coordinator_mock,
        equipment=equipment,
        device_info=device_info,
    )

    coordinator_mock.siren_state[1] = True
    coordinator_mock.equipment_status[1] = EQUIPMENT_STATUS_DOOR_OPEN

    await button.async_press()

    assert coordinator_mock.siren_state[1] is False
    assert coordinator_mock.equipment_status[1] == EQUIPMENT_STATUS_OK