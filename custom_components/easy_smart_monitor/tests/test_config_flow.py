"""
Testes do Config Flow do Easy Smart Monitor.

Foco:
- TEST_MODE ativo
- Criação da integração sem API online
- OptionsFlow básico
"""

import pytest

from homeassistant import data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.easy_smart_monitor.const import DOMAIN, TEST_MODE


# ============================================================
# SANITY CHECK
# ============================================================

def test_test_mode_is_enabled():
    """
    Garante que os testes estão rodando em TEST_MODE.
    """
    assert TEST_MODE is True


# ============================================================
# CONFIG FLOW — USER STEP
# ============================================================

@pytest.mark.asyncio
async def test_config_flow_user_step_in_test_mode(hass: HomeAssistant):
    """
    Deve permitir criar a integração em TEST_MODE
    sem validar API externa.
    """
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
    )

    # Primeira tela: formulário
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    # Envia credenciais fake
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "api_host": "http://fake-api",
            "username": "test_user",
            "password": "test_pass",
        },
    )

    # Integração criada com sucesso
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert "Easy Smart Monitor" in result["title"]

    entry = result["result"]

    assert entry.domain == DOMAIN
    assert entry.data["api_host"] == "http://fake-api"
    assert entry.data["username"] == "test_user"
    assert entry.options["equipments"] == []
    assert entry.options["send_interval"] == 60
    assert entry.options["paused"] is False


# ============================================================
# OPTIONS FLOW — INIT
# ============================================================

@pytest.mark.asyncio
async def test_options_flow_init_menu(hass: HomeAssistant):
    """
    OptionsFlow deve abrir menu principal corretamente.
    """
    # Cria entry em TEST_MODE
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "api_host": "http://fake-api",
            "username": "test_user",
            "password": "test_pass",
        },
    )
    entry = result["result"]

    # Inicia OptionsFlow
    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == data_entry_flow.FlowResultType.MENU
    assert result["step_id"] == "init"
    assert "integration_settings" in result["menu_options"]
    assert "select_equipment" in result["menu_options"]


# ============================================================
# OPTIONS FLOW — INTEGRATION SETTINGS
# ============================================================

@pytest.mark.asyncio
async def test_options_flow_integration_settings(hass: HomeAssistant):
    """
    Deve permitir alterar send_interval e paused.
    """
    # Cria entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "api_host": "http://fake-api",
            "username": "test_user",
            "password": "test_pass",
        },
    )
    entry = result["result"]

    # Inicia OptionsFlow
    result = await hass.config_entries.options.async_init(entry.entry_id)
    flow_id = result["flow_id"]

    # Entra em integration_settings
    result = await hass.config_entries.options.async_configure(
        flow_id,
        {"next_step_id": "integration_settings"},
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM

    # Salva novas configurações
    result = await hass.config_entries.options.async_configure(
        flow_id,
        {
            "send_interval": 120,
            "paused": True,
        },
    )

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY

    updated_entry = hass.config_entries.async_get_entry(entry.entry_id)

    assert updated_entry.options["send_interval"] == 120
    assert updated_entry.options["paused"] is True


# ============================================================
# OPTIONS FLOW — ADD EQUIPMENT
# ============================================================

@pytest.mark.asyncio
async def test_options_flow_add_equipment(hass: HomeAssistant):
    """
    Deve permitir adicionar equipamento via OptionsFlow.
    """
    # Cria entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "api_host": "http://fake-api",
            "username": "test_user",
            "password": "test_pass",
        },
    )
    entry = result["result"]

    # Inicia OptionsFlow
    result = await hass.config_entries.options.async_init(entry.entry_id)
    flow_id = result["flow_id"]

    # Seleciona add_equipment pelo menu
    result = await hass.config_entries.options.async_configure(
        flow_id,
        {"next_step_id": "add_equipment"},
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM

    # Envia dados do equipamento
    result = await hass.config_entries.options.async_configure(
        flow_id,
        {
            "name": "Freezer Teste",
            "location": "Cozinha",
            "collect_interval": 30,
        },
    )

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY

    updated_entry = hass.config_entries.async_get_entry(entry.entry_id)
    equipments = updated_entry.options["equipments"]

    assert len(equipments) == 1
    assert equipments[0]["name"] == "Freezer Teste"
    assert equipments[0]["location"] == "Cozinha"
    assert equipments[0]["enabled"] is True
    assert equipments[0]["sensors"] == []