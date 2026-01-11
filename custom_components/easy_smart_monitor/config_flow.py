from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, TEST_MODE
from .client import EasySmartMonitorClient

import uuid
from homeassistant.helpers.selector import EntitySelector

class EasySmartMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        return EasySmartMonitorOptionsFlow()

    async def async_step_user(self, user_input=None):
        errors = {}
        if TEST_MODE:
            return self.async_create_entry(
                title="Easy Smart Monitor (TEST MODE)",
                data={
                    "api_url": "http://localhost",
                    "username": "test",
                    "password": "test",
                },
            )
        if user_input:
            client = EasySmartMonitorClient(
                self.hass,
                user_input["api_url"],
                user_input["username"],
                user_input["password"],
            )
            try:
                await client.async_login()
                return self.async_create_entry(
                    title="Easy Smart Monitor",
                    data=user_input,
                )
            except Exception:
                errors["base"] = "auth_failed"

        schema = vol.Schema({
            vol.Required("api_url"): str,
            vol.Required("username"): str,
            vol.Required("password"): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

class EasySmartMonitorOptionsFlow(config_entries.OptionsFlow):

    def __init__(self):
        self._options = {}
        self._equipment_id = None

    async def async_step_init(self, user_input=None):
        if not self._options:
            self._options = dict(self.config_entry.options)

        equipments = self._options.get("equipments", {})

        if user_input:
            action = user_input["action"]

            if action == "add":
                return await self.async_step_add_equipment()

            if action == "save":
                return self.async_create_entry(title="", data=self._options)

            self._equipment_id = action
            return await self.async_step_equipment_menu()

        actions = {
            "add": "➕ Adicionar equipamento",
            "save": "💾 Salvar e sair",
        }

        for eq_id, eq in equipments.items():
            actions[eq_id] = f"{eq['name']} ({eq['location']})"

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("action"): vol.In(actions)
            }),
        )

    async def async_step_add_equipment(self, user_input=None):
        if user_input:
            equipments = self._options.setdefault("equipments", {})
            next_id = str(len(equipments) + 1)

            equipments[next_id] = {
                "id": int(next_id),
                "uuid": str(uuid.uuid4()),
                "name": user_input["name"],
                "location": user_input["location"],
                "sensors": {},
            }

            return await self.async_step_init()

        return self.async_show_form(
            step_id="add_equipment",
            data_schema=vol.Schema({
                vol.Required("name"): str,
                vol.Required("location"): str,
            }),
        )

    async def async_step_equipment_menu(self, user_input=None):
        eq = self._options["equipments"][self._equipment_id]
        sensors = eq.get("sensors", {})

        if user_input:
            action = user_input["action"]

            if action == "add_sensor":
                return await self.async_step_add_sensor()

            if action == "remove_equipment":
                del self._options["equipments"][self._equipment_id]
                return await self.async_step_init()

            if action == "back":
                return await self.async_step_init()

            if action.startswith("sensor_"):
                sensor_id = action.replace("sensor_", "")
                del sensors[sensor_id]
                return await self.async_step_equipment_menu()

        actions = {
            "add_sensor": "➕ Adicionar sensor",
            "remove_equipment": "❌ Remover equipamento",
            "back": "↩️ Voltar",
        }

        for sensor_id, sensor in sensors.items():
            actions[f"sensor_{sensor_id}"] = (
                f"🧩 {sensor['type']} → {sensor['entity_id']}"
            )

        return self.async_show_form(
            step_id="equipment_menu",
            data_schema=vol.Schema({
                vol.Required("action"): vol.In(actions)
            }),
        )

    async def async_step_add_sensor(self, user_input=None):
        sensors = self._options["equipments"][self._equipment_id]["sensors"]

        if user_input:
            next_id = str(len(sensors) + 1)
            sensors[next_id] = {
                "id": int(next_id),
                "uuid": str(uuid.uuid4()),
                "entity_id": user_input["entity_id"],
                "type": user_input["type"],
                "enabled": user_input["enabled"],
            }

            return await self.async_step_equipment_menu()

        return self.async_show_form(
            step_id="add_sensor",
            data_schema=vol.Schema({
                vol.Required("entity_id"): EntitySelector(),
                vol.Required("type"): vol.In(
                    ["temperature", "energy", "door", "siren", "button"]
                ),
                vol.Optional("enabled", default=True): bool,
            }),
        )