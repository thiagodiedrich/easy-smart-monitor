"""
Constantes globais do Easy Smart Monitor.

Este arquivo centraliza:
- Domínio da integração
- Flags globais (TEST_MODE)
- Defaults de configuração
- Status da integração
- Status dos equipamentos

Versão alvo: v1.1.0
"""

from __future__ import annotations

import os

# ============================================================
# INTEGRAÇÃO
# ============================================================

DOMAIN = "easy_smart_monitor"

MANUFACTURER = "Easy Smart Monitor"
MODEL_VIRTUAL = "Virtual"


# ============================================================
# CONFIG FLOW (CREDENCIAIS)
# ============================================================

CONF_API_HOST = "api_host"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"


# ============================================================
# TEST MODE
# ============================================================

"""
TEST_MODE permite rodar a integração sem:
- API externa
- Credenciais reais
- Conectividade de rede

Usado para:
- Desenvolvimento local
- Testes automatizados
- CI / GitHub Actions
"""

TEST_MODE = True


# ============================================================
# DEFAULTS (CONFIGURAÇÃO)
# ============================================================

# Intervalo padrão de envio para API (segundos)
DEFAULT_SEND_INTERVAL = 60

# Tempo padrão de porta aberta para disparar sirene (segundos)
DEFAULT_DOOR_OPEN_SECONDS = 120


# ============================================================
# STATUS DA INTEGRAÇÃO
# ============================================================

INTEGRATION_STATUS_ONLINE = "online"
INTEGRATION_STATUS_PAUSED = "paused"
INTEGRATION_STATUS_API_ERROR = "api_error"
INTEGRATION_STATUS_TEST_MODE = "test_mode"


# ============================================================
# STATUS DO EQUIPAMENTO
# ============================================================

EQUIPMENT_STATUS_OK = "ok"
EQUIPMENT_STATUS_DOOR_OPEN = "door_open"
EQUIPMENT_STATUS_TEMPERATURE_ALERT = "temperature_alert"


# ============================================================
# TIPOS DE SENSOR
# ============================================================

SENSOR_TYPE_TEMPERATURE = "temperature"
SENSOR_TYPE_HUMIDITY = "humidity"
SENSOR_TYPE_ENERGY = "energy"
SENSOR_TYPE_DOOR = "door"


# ============================================================
# ATRIBUTOS PADRÃO
# ============================================================

ATTR_OPEN_SINCE = "open_since"
ATTR_TRIGGERED_AT = "triggered_at"
ATTR_REASON = "reason"
ATTR_VALUE = "value"
ATTR_MIN = "min"
ATTR_MAX = "max"