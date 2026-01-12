from __future__ import annotations

# ============================================================
# INTEGRAÇÃO
# ============================================================

DOMAIN = "easy_smart_monitor"
NAME = "Easy Smart Monitor"
VERSION = "1.0.0"

# ============================================================
# TEST MODE
# ============================================================

TEST_MODE = True


# ============================================================
# PLATAFORMAS
# ============================================================

PLATFORMS: list[str] = [
    "sensor",
    "binary_sensor",
    "siren",
    "button",
]


# ============================================================
# CONFIG FLOW / CONFIG ENTRY
# ============================================================

CONF_API_HOST = "api_host"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

CONF_EQUIPMENTS = "equipments"
CONF_SENSORS = "sensors"

CONF_SEND_INTERVAL = "send_interval"
CONF_PAUSED = "paused"

CONF_COLLECT_INTERVAL = "collect_interval"
CONF_ENABLED = "enabled"


# ============================================================
# STORAGE (FILA LOCAL)
# ============================================================

STORAGE_VERSION = 1
STORAGE_KEY_QUEUE = "easy_smart_monitor.queue"


# ============================================================
# DEFAULTS
# ============================================================

DEFAULT_SEND_INTERVAL = 60          # segundos
DEFAULT_COLLECT_INTERVAL = 30       # segundos
DEFAULT_DOOR_OPEN_SECONDS = 120     # segundos


# ============================================================
# SENSOR TYPES (CONTRATO)
# ============================================================

SENSOR_TYPE_TEMPERATURE = "temperature"
SENSOR_TYPE_HUMIDITY = "humidity"
SENSOR_TYPE_ENERGY = "energy"
SENSOR_TYPE_DOOR = "door"

SUPPORTED_SENSOR_TYPES: list[str] = [
    SENSOR_TYPE_TEMPERATURE,
    SENSOR_TYPE_HUMIDITY,
    SENSOR_TYPE_ENERGY,
    SENSOR_TYPE_DOOR,
]


# ============================================================
# STATUS DA INTEGRAÇÃO
# ============================================================

INTEGRATION_STATUS_ONLINE = "online"
INTEGRATION_STATUS_OFFLINE = "offline"
INTEGRATION_STATUS_PAUSED = "paused"
INTEGRATION_STATUS_API_ERROR = "api_error"
INTEGRATION_STATUS_AUTH_ERROR = "auth_error"


# ============================================================
# STATUS DO EQUIPAMENTO
# ============================================================

EQUIPMENT_STATUS_OK = "ok"
EQUIPMENT_STATUS_DOOR_OPEN = "porta_aberta"
EQUIPMENT_STATUS_NO_POWER = "sem_energia"
EQUIPMENT_STATUS_SENSOR_ERROR = "erro_sensor"


# ============================================================
# BINARY STATE KEYS (USADOS PELO COORDINATOR)
# ============================================================

BINARY_STATE_ENERGY_ON = "energy_on"
BINARY_STATE_DOOR_OPEN = "door_open"


# ============================================================
# NUMERIC STATE KEYS (USADOS PELO COORDINATOR)
# ============================================================

NUMERIC_STATE_TEMPERATURE = "temperature"
NUMERIC_STATE_HUMIDITY = "humidity"


# ============================================================
# SIREN
# ============================================================

SIREN_TRIGGER_REASON_DOOR = "door_open"