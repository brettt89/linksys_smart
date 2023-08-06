""" Linksys Smart Wifi Support """

import logging

from homeassistant.core import Event as HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .controller import LinksysController
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class LinksysConfig(Store):
    """Config for manual setup of Google."""

    _STORAGE_VERSION = 1
    _STORAGE_KEY = DOMAIN

    def __init__(self, hass, config):
        """Initialize the config."""
        self.hass = hass
        self._store = Store(hass, self._STORAGE_VERSION, self._STORAGE_KEY)
        self._data = None
        self._config = config

    async def async_initialize(self):
        """Perform async initialization of config."""
        should_save_data = False
        if (data := await self._store.async_load()) is None:
            data = {
                "host": self._config.get("host", None),
                "username": self._config.get("username", "admin"),
                "password": self._config.get("password", None),
            }
            should_save_data = True

        if should_save_data:
            await self._store.async_save(data)

        self._data = data

    @property
    def enabled(self):
        """Return if Entity is enabled."""
        return True

    @property
    def host(self):
        return self._data.get("host")

    @property
    def username(self):
        return self._data.get("username")

    @property
    def password(self):
        return self._data.get("password")

class Linksys:

    def __init__(self, hass: HomeAssistant, config: LinksysConfig) -> None:
        self.hass = hass
        self.config = config

    async def async_initialize(self):
        session = async_get_clientsession(self.hass)
        controller = LinksysController(session, self.config)
        await controller.async_initialize()

        self._controller = controller

    async def async_get_devices(self):
        return await self._controller.async_get_devices()

# import base64
# import logging
# from typing import Any

# import asyncio
# from aiohttp import ClientError, ClientResponseError
# from collections.abc import Callable, Coroutine
# from http import HTTPStatus

# from homeassistant.core import HomeAssistant
# from homeassistant.helpers.aiohttp_client import async_get_clientsession
# from homeassistant.util.decorator import Registry

# from .const import (
#     ERR_ACTION_ERROR,
#     ERR_UNKNOWN_ERROR,
#     LINKSYS_JNAP_ENDPOINT,
#     LINKSYS_JNAP_ACTION_URL
# )

# from .helpers import RequestData

# LOCAL_JNAP_ACTION_HEADER = "X-JNAP-Action"
# LOCAL_JNAP_AUTHORIZATION_HEADER = "X-JNAP-Authorization"
# LOCAL_JNAP_ACTION_TRANSACTION = "http://linksys.com/jnap/core/Transaction"

# HANDLERS: Registry[
#     str,
#     Callable[
#         [HomeAssistant, dict[str, Any]],
#         Coroutine[Any, Any, dict[str, Any] | None],
#     ],
# ] = Registry()
# _LOGGER = logging.getLogger(__name__)

# async def async_handle_message(hass, config, action, request):
#     """Handle incoming API messages."""
#     data = RequestData(
#         config
#     )

#     response = await _process(hass, data, action, request)

#     if response and response["result"] == "Error":
#         _LOGGER.error("Error handling action %s: %s", action, response["responses"])

#     return response

# async def _process(hass, data, action, request):
#     """Process a message."""

#     if (handler := HANDLERS.get(action)) is None:
#         return {
#             "result": "Error",
#             "responses": [
#                 {
#                     "result": ERR_ACTION_ERROR,
#                     "error": f"Unknown action method for \"{action}\""
#                 }
#             ],
#         }

#     try:
#         return await handler(hass, data, request)
#     except Exception:  # pylint: disable=broad-except
#         _LOGGER.exception("Unexpected error")
#         return {
#             "result": "Error",
#             "responses": [
#                 {
#                     "result": ERR_UNKNOWN_ERROR,
#                     "error": f"Unknown error for \"{action}\""
#                 }
#             ],
#         }


# @HANDLERS.register("GetDeviceInfo")
# async def async_get_device_info(
#     hass: HomeAssistant, data: RequestData, payload: dict = {}
# ) -> dict[str, Any]:
#     """Handle core/GetDeviceInfo request."""

#     action = f"{LINKSYS_JNAP_ACTION_URL}/core/GetDeviceInfo"
#     return await async_make_request(hass, data, action, payload)

# async def async_make_request(
#     hass: HomeAssistant, data: RequestData, action: str, payload: dict = {}
# ) -> dict:
#     """Make API Request to Linksys Router"""
#     json = [{
#         "request": payload,
#         "action": action
#     }]

#     def _get_headers(config):
#         credentials_string = f"{config.username}:{config.password}"
#         encoded_credentials = base64.b64encode(credentials_string.encode()).decode()
#         auth_string = f"Basic {encoded_credentials}"

#         headers = {
#             LOCAL_JNAP_ACTION_HEADER: LOCAL_JNAP_ACTION_TRANSACTION,
#             LOCAL_JNAP_AUTHORIZATION_HEADER: auth_string
#         }

#         return headers

#     headers = _get_headers(data.config)
#     url = f"http://{data.config.host}{LINKSYS_JNAP_ENDPOINT}"

#     session = async_get_clientsession(hass)
#     async with session.post(url, headers=headers, json=json) as res:
#         res.raise_for_status()
#         return await res.json()

# # import base64

# # from http import HTTPStatus
# # import logging

# # from aiohttp import ClientError, ClientResponseError

# # _LOGGER = logging.getLogger(__name__)

# # class Linksys:

# #     def __init__(self, host, password, request_timeout, session):
# #         """ Set defaults """
# #         self.session = session

# #         self.url = f"http://{self.host}/JNAP/"
# #         self.headers = self._get_headers(password)
# #         self.default_data = [
# #             {
# #                 "request": {},
# #                 "action": "http://linksys.com/jnap/core/GetDeviceInfo",
# #             }
# #         ]

# #         self.timeout = request_timeout

# #     def _get_headers(password):
# #         username = "admin"
# #         credentials_string = f"{username}:{password}"
# #         encoded_credentials = base64.b64encode(credentials_string.encode()).decode()
# #         auth_string = f"Basic {encoded_credentials}"

# #         headers = {
# #             "X-JNAP-Action": "http://linksys.com/jnap/core/Transaction",
# #             "X-JNAP-Authorization": auth_string
# #         }

# #         return headers

# #     async def authenticate(self):

# #         async def _call():
            
# #             json_data = [
# #                 {
# #                     "request": {},
# #                     "action": "http://linksys.com/jnap/core/GetDeviceInfo",
# #                 }
# #             ]
# #             async with self.session.post(self.url, headers=self.headers, json=json_data) as res:
# #                 res.raise_for_status()
# #                 return res.status

# #         return await _call()



# #     def make_request(self):
         
        
# #         # check connection
# #         data = [
# #             {
# #                 "request": {},
# #                 "action": "http://linksys.com/jnap/core/GetDeviceInfo",
# #             }
# #         ]
# #         headers = {
# #             "X-JNAP-Action": "http://linksys.com/jnap/core/Transaction",
# #             "X-JNAP-Authorization": auth_string
# #         }
# #         try:
# #             session = async_get_clientsession(self.hass)
# #             response = await session.post(
# #                 f"http://{host}/JNAP/",
# #                 timeout=10,
# #                 headers=headers,
# #                 json=data,
# #             )
# #         except aiohttp.ServerTimeoutError:
# #             self.errors["base"] = "timeout"
# #             return False
# #         except aiohttp.ClientConnectionError:
# #             self.errors["base"] = "connection_error"
# #             return False
# #         except aiohttp.ClientResponseError:
# #             self.errors["base"] = "http_error"
# #             return False
# #         except aiohttp.ClientError:
# #             self.errors["base"] = "unexpected"
# #             return False

# #         try:
# #             data = await response.json()
# #             result = data["result"]
# #             responses = data["responses"]

# #             if result != "OK":
# #                 self.errors["base"] = "api_error"
# #                 error_type = responses[0]['result']
# #                 if error_type == "_ErrorUnauthorized":
# #                     self.errors["base"] = "unauthorized"
# #                 return False
            
# #             return True

# #         except (KeyError, IndexError):
# #             self.errors["base"] = "invalid_response"
# #             return False

# #         return True

# # class api:
# #     """ Linksys Smart Wifi API connection"""
# #     def __init__(self, auth):
# #         self.status = "OK"

# #     def