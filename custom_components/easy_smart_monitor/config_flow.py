from __future__ import annotations

import logging
import uuid
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import aiohttp_client, selector
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import (
    DOMAIN,
    CONF_API_HOST,
    CONF_USERNAME,
    CONF_PASSWORD,
    DEFAULT_DOOR_OPEN_SECONDS,
    TEST_MODE,
)
from .client import EasySmartMonitorApiClient

_LOGGER = logging.getLogger(__name__)


# ============================================================
# CONFIG FLOW — CRIAÇÃO DA INTEGRAÇÃO
# ============================================================

class EasySmartMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config Flow do Easy Smart Monitor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ):
        errors: dict[str, str] = {}

        if user_input is not None:
            api_host = user_input[CONF_API_HOST]
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            # --------------------------------------------------
            # TEST MODE (SEM API REAL)
            # --------------------------------------------------
            if TEST_MODE:
                _LOGGER.warning(
                    "Easy Smart Monitor iniciado em TEST_MODE "
                    "(API não será validada)"
                )
                return self.async_create_entry(
                    title="Easy Smart Monitor (TEST MODE)",
                    data={
                        CONF_API_HOST: api_host,
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                    },
                    options={
                        "equipments": [],
                        "send_interval": 60,
                        "paused": False,
                    },
                )

            # --------------------------------------------------
            # PRODUÇÃO — VALIDA API
            # --------------------------------------------------
            try:
                session = aiohttp_client.async_get_clientsession(self.hass)
                client = EasySmartMonitorApiClient(
                    base_url=api_host,
                    username=username,
                    password=password,
                    session=session,
                )
                await client.async_login()
            except Exception as err:  # noqa: BLE001
                _LOGGER.error("Erro ao autenticar na API: %s", err)
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title="Easy Smart Monitor",
                    data={
                        CONF_API_HOST: api_host,
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                    },
                    options={
                        "equipments": [],
                        "send_interval": 60,
                        "paused": False,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_API_HOST): str,
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return EasySmartMonitorOptionsFlow(config_entry)


# ============================================================
# OPTIONS FLOW — CONFIGURAÇÃO CONTÍNUA
# ============================================================

class EasySmartMonitorOptionsFlow(config_entries.OptionsFlow):
    """Options Flow do Easy Smart Monitor."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry

        # Estrutura garantida
        self.options = dict(entry.options)
        self.options.setdefault("equipments", [])
        self.options.setdefault("send_interval", 60)
        self.options.setdefault("paused", False)

        self._selected_equipment_id: int | None = None

    # =========================================================
    # MENU PRINCIPAL
    # =========================================================

    async def async_step_init(self, user_input=None):
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "integration_settings",
                "equipment_menu",
                "sensor_menu",
            ],
        )

    # =========================================================
    # MENU 1 — CONFIGURAÇÃO DA INTEGRAÇÃO
    # =========================================================

    async def async_step_integration_settings(self, user_input=None):
        if user_input is not None:
            self.options["send_interval"] = user_input["send_interval"]
            self.options["paused"] = user_input["paused"]
            return self.async_create_entry(title="", data=self.options)

        return self.async_show_form(
            step_id="integration_settings",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "send_interval",
                        default=self.options["send_interval"],
                    ): vol.All(int, vol.Range(min=10)),
                    vol.Required(
                        "paused",
                        default=self.options["paused"],
                    ): bool,
                }
            ),
        )

    # =========================================================
    # MENU 2 — CONFIGURAÇÃO DE EQUIPAMENTOS
    # =========================================================

    async def async_step_equipment_menu(self, user_input=None):
        return self.async_show_menu(
            step_id="equipment_menu",
            menu_options=[
                "add_equipment",
                "select_equipment",
            ],
        )

    async def async_step_select_equipment(self, user_input=None):
        if not self.options["equipments"]:
            return await self.async_step_add_equipment()

        if user_input is not None:
            self._selected_equipment_id = user_input["equipment_id"]
            return await self.async_step_edit_equipment()

        equipment_map = {
            f"{e['name']} ({e['location']})": e["id"]
            for e in self.options["equipments"]
        }

        return self.async_show_form(
            step_id="select_equipment",
            data_schema=vol.Schema(
                {
                    vol.Required("equipment_id"): vol.In(equipment_map),
                }
            ),
        )

    async def async_step_add_equipment(self, user_input=None):
        if user_input is not None:
            equipment_id = (
                max([e["id"] for e in self.options["equipments"]], default=0)
                + 1
            )

            self.options["equipments"].append(
                {
                    "id": equipment_id,
                    "uuid": uuid.uuid4().hex,
                    "name": user_input["name"],
                    "location": user_input["location"],
                    "collect_interval": user_input["collect_interval"],
                    "enabled": True,
                    "door": {
                        "enable_siren": True,
                        "open_timeout": DEFAULT_DOOR_OPEN_SECONDS,
                    },
                    "sensors": [],
                }
            )

            return self.async_create_entry(title="", data=self.options)

        return self.async_show_form(
            step_id="add_equipment",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): str,
                    vol.Required("location"): str,
                    vol.Required(
                        "collect_interval", default=30
                    ): vol.All(int, vol.Range(min=10)),
                }
            ),
        )

    async def async_step_edit_equipment(self, user_input=None):
        equipment = next(
            e for e in self.options["equipments"]
            if e["id"] == self._selected_equipment_id
        )

        door_cfg = equipment.get("door", {})

        if user_input is not None:
            equipment.update(
                {
                    "name": user_input["name"],
                    "location": user_input["location"],
                    "collect_interval": user_input["collect_interval"],
                    "enabled": user_input["enabled"],
                    "door": {
                        "enable_siren": user_input["enable_siren"],
                        "open_timeout": user_input["open_timeout"],
                    },
                }
            )
            return self.async_create_entry(title="", data=self.options)

        return self.async_show_form(
            step_id="edit_equipment",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default=equipment["name"]): str,
                    vol.Required(
                        "location", default=equipment["location"]
                    ): str,
                    vol.Required(
                        "collect_interval",
                        default=equipment["collect_interval"],
                    ): vol.All(int, vol.Range(min=10)),
                    vol.Required(
                        "enabled", default=equipment["enabled"]
                    ): bool,
                    vol.Required(
                        "enable_siren",
                        default=door_cfg.get("enable_siren", True),
                    ): bool,
                    vol.Required(
                        "open_timeout",
                        default=door_cfg.get(
                            "open_timeout",
                            DEFAULT_DOOR_OPEN_SECONDS,
                        ),
                    ): vol.All(int, vol.Range(min=10)),
                }
            ),
        )

    # =========================================================
    # MENU 3 — CONFIGURAÇÃO DE SENSORES
    # =========================================================

    async def async_step_sensor_menu(self, user_input=None):
        return self.async_show_menu(
            step_id="sensor_menu",
            menu_options=[
                "add_sensor",
            ],
        )

    async def async_step_add_sensor(self, user_input=None):
        if self._selected_equipment_id is None:
            return await self.async_step_select_equipment()

        equipment = next(
            e for e in self.options["equipments"]
            if e["id"] == self._selected_equipment_id
        )

        if user_input is not None:
            sensor_id = (
                max([s["id"] for s in equipment["sensors"]], default=0)
                + 1
            )

            equipment["sensors"].append(
                {
                    "id": sensor_id,
                    "uuid": uuid.uuid4().hex,
                    "entity_id": user_input["entity_id"],
                    "type": user_input["sensor_type"],
                    "enabled": True,
                }
            )

            return self.async_create_entry(title="", data=self.options)

        entity_reg = async_get_entity_registry(self.hass)
        entities = [
            e.entity_id
            for e in entity_reg.entities.values()
            if not e.disabled
        ]

        return self.async_show_form(
            step_id="add_sensor",
            data_schema=vol.Schema(
                {
                    vol.Required("entity_id"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=entities,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required("sensor_type"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                "temperature",
                                "humidity",
                                "energy",
                                "door",
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )