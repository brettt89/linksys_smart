"""UI for configuring the integration."""

import logging

from aiohttp import ClientError
from asyncio import TimeoutError
import voluptuous as vol
from types import MappingProxyType
from typing import Any

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant import config_entries

from .const import DOMAIN
from .controller import LinksysController, LinksysError

_LOGGER = logging.getLogger(__name__)

class LinksysWifiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Store connection configuration"""
    def __init__(self):
        self.config: dict[str, Any] = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            try:
                # Validate user input
                controller = LinksysController(async_get_clientsession(self.hass), MappingProxyType(user_input))
                await controller.async_initialize()
                await controller.check_admin_password()

            except (ClientError, LinksysError) as err:
                errors["base"] = str(err)

            else:
                # Store the data
                return self.async_create_entry(
                    title="Linksys Smart Wifi",
                    data=user_input,
                )

            
        # Specify items in the order they are to be displayed in the UI
        data_schema = {
            vol.Required("host", default="192.168.1.1"): str,
            vol.Required("username", default="admin"): str,
            vol.Required("password"): str,
        }

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=errors
        )
