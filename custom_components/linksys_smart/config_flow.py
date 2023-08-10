"""Config flow for Mikrotik."""
from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

import voluptuous as vol

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
)
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DEFAULT_NAME,
    DOMAIN,
)
from .controller import LinksysController, LinksysError, AuthError
from .hub import get_api


class MikrotikFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Mikrotik config flow."""

    VERSION = 1
    _reauth_entry: config_entries.ConfigEntry | None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST]})

            try:
                controller = LinksysController(async_get_clientsession(self.hass), MappingProxyType(user_input))
                await controller.async_initialize()
                await controller.async_check_admin_password()
            except LinksysError:
                errors["base"] = "cannot_connect"
            except AuthError:
                errors[CONF_USERNAME] = "invalid_auth"
                errors[CONF_PASSWORD] = "invalid_auth"

            if not errors:
                return self.async_create_entry(
                    title=f"{DEFAULT_NAME} ({user_input[CONF_HOST]})", data=user_input
                )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_USERNAME, default="admin"): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, data: Mapping[str, Any]) -> FlowResult:
        """Perform reauth upon an API authentication error."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Confirm reauth dialog."""
        errors = {}
        assert self._reauth_entry
        if user_input is not None:
            user_input = {**self._reauth_entry.data, **user_input}
            try:
                controller = LinksysController(async_get_clientsession(self.hass), MappingProxyType(user_input))
                await controller.async_initialize()
                await controller.async_check_admin_password()
            except LinksysError:
                errors["base"] = "cannot_connect"
            except AuthError:
                errors[CONF_USERNAME] = "invalid_auth"
                errors[CONF_PASSWORD] = "invalid_auth"

            if not errors:
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry,
                    data=user_input,
                )
                await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            description_placeholders={
                CONF_USERNAME: self._reauth_entry.data[CONF_USERNAME]
            },
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )
