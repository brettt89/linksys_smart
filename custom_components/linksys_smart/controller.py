"""Linksys Smart Wifi Network abstraction."""
from __future__ import annotations

import base64
import logging

from aiohttp import ClientSession, ClientError
from asyncio import TimeoutError
from types import MappingProxyType
from typing import Any

_LOGGER = logging.getLogger(__name__)

LINKSYS_JNAP_ENDPOINT: str = "/JNAP/"
LINKSYS_JNAP_ACTION_URL: str = "http://linksys.com/jnap"
LINKSYS_JNAP_ACTION_HEADER = "X-JNAP-Action"
LINKSYS_JNAP_AUTHORIZATION_HEADER = "X-JNAP-Authorization"
LINKSYS_JNAP_ACTION_TRANSACTION = "http://linksys.com/jnap/core/Transaction"

class LinksysError(Exception):
    """Exception if api error occurs."""

class AuthError(LinksysError):
    """Exception if auth error occurs."""

class UnkownActionError(LinksysError):
    """Exception if unknown action error occurs."""

class LinksysController:
    """Manages a single Linksys Smart Wifi Network instance."""

    def __init__(
        self, session: ClientSession, config: MappingProxyType[str, Any],
    ) -> None:
        """Initialize the system."""
        self._session = session
        self._config = config
        self.url: str = ""
        self.headers: dict[str, Any] = {}


    async def async_initialize(self):
        """Load Linksys Smart Wifi parameters."""
        host = self._config.get("host")
        self.url = f"http://{host}{LINKSYS_JNAP_ENDPOINT}"

        username = self._config.get("username")
        password = self._config.get("password")
        credentials_string = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials_string.encode()).decode()
        auth_string =  f"Basic {encoded_credentials}"

        self.headers[LINKSYS_JNAP_ACTION_HEADER] = LINKSYS_JNAP_ACTION_TRANSACTION
        self.headers[LINKSYS_JNAP_AUTHORIZATION_HEADER] = auth_string

    async def async_check_admin_password(self) -> bool:
        """Load Linksys Smart Wifi devices"""

        responses = await self.request("core/CheckAdminPassword")
        result = responses[0]['result']

        return result == "OK"


    async def async_get_device_info(self) -> list[dict]:
        """Load Linksys Smart Wifi devices"""

        responses = await self.request("core/GetDeviceInfo")
        output = responses[0]['output']

        return output

    async def async_get_devices(self) -> list[dict]:
        """Load Linksys Smart Wifi devices"""

        payload = {
            "sinceRevision": 0
        }
        responses = await self.request("devicelist/GetDevices3", payload)
        output = responses[0]['output']

        devices = output['devices']
        return devices

    async def async_get_network_connections(self) -> list[dict]:
        """Load Linksys Smart Wifi network connections"""

        responses = await self.request("networkconnections/GetNetworkConnections")
        output = responses[0]['output']

        connections = output['connections']
        return connections

    async def async_get_wan_status(self) -> dict:
        """Load Linksys Smart Wifi network connections"""

        responses = await self.request("router/GetWANStatus")
        output = responses[0]['output']

        return output
    
    async def request(
        self,
        action: str,
        payload: dict[str, Any] = {},
    ):
        """Make a request to the API."""
        json = [
            {
                "request": payload,
                "action": f"{LINKSYS_JNAP_ACTION_URL}/{action}",
            }
        ]

        try:
            _LOGGER.debug(
                "sending (to %s) %s %s %s",
                self.url,
                "post",
                self.headers,
                json,
            )
            async with self._session.request("post", self.url, headers=self.headers, json=json, timeout=10) as res:
                _LOGGER.debug(
                    "received (from %s) %s %s %s",
                    self.url,
                    res.status,
                    res.content_type,
                    res,
                )

                res.raise_for_status()

                response = await res.json()
                _LOGGER.debug("data (from %s) %s", self.url, response)
                _raise_on_error(response)
                
                return response["responses"]
        except TimeoutError:
            raise ClientError("Timeout occurred when attempting to connect to router.")
        

def _raise_on_error(data: dict[str, Any] | None) -> None:
    """Check response for error message."""
    if not isinstance(data, dict):
        return None

    if not "result" in data or not "responses" in data:
        raise LinksysError("Unexpected reponse from router.")

    if data["result"] != "OK":
        # Error
        if data["result"] == "_ErrorUnknownAction":
            raise UnkownActionError()
        response = data["responses"][0]
        if response["result"] == "_ErrorUnauthorized":
            raise AuthError()
        if "error" in response:
            raise LinksysError(response["error"])
            