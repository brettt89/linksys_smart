"""Linksys Smart Wifi Network abstraction."""

import base64
import logging

from aiohttp import ClientSession
from types import MappingProxyType
from typing import Any

from .const import (
    LINKSYS_JNAP_ACTION_URL,
    LINKSYS_JNAP_ENDPOINT
)

_LOGGER = logging.getLogger(__name__)

LOCAL_JNAP_ACTION_HEADER = "X-JNAP-Action"
LOCAL_JNAP_AUTHORIZATION_HEADER = "X-JNAP-Authorization"
LOCAL_JNAP_ACTION_TRANSACTION = "http://linksys.com/jnap/core/Transaction"

class LinksysController:
    """Manages a single Linksys Smart Wifi Network instance."""

    def __init__(
        self, session: ClientSession, config: MappingProxyType[str, Any],
    ) -> None:
        """Initialize the system."""
        self.session = session
        self.last_response = None

        self.host = config.get("host")
        self.username = config.get("username")
        self.password = config.get("password")

        self.url = f"http://{self.host}/{LINKSYS_JNAP_ENDPOINT}"
        self.headers: dict[str, Any] = {}


    async def async_initialize(self):
        """Load Linksys Smart Wifi parameters."""

        credentials_string = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials_string.encode()).decode()
        auth_string =  f"Basic {encoded_credentials}"

        self.headers[LOCAL_JNAP_ACTION_HEADER] = LOCAL_JNAP_ACTION_TRANSACTION
        self.headers[LOCAL_JNAP_AUTHORIZATION_HEADER] = auth_string

    async def check_admin_password(self) -> bool:
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
        self.last_response = None

        json = [
            {
                "request": payload,
                "action": f"{LINKSYS_JNAP_ACTION_URL}/{action}",
            }
        ]

        try:
            async with self.session.request("post", self.url, headers=self.headers, json=json) as res:
                _LOGGER.debug(
                    "received (from %s) %s %s %s",
                    self.url,
                    res.status,
                    res.content_type,
                    res,
                )

                res.raise_for_status()
                self.last_response = res

                response = await res.json()
                _LOGGER.debug("data (from %s) %s", self.url, response)
                _raise_on_error(response)
                
                return response["responses"]

        except Exception as e:
            _LOGGER.error("Request to Linksys router failed: %s", str(e))
            raise e
        

def _raise_on_error(data: dict[str, Any] | None) -> None:
    """Check response for error message."""
    if not isinstance(data, dict):
        return None

    if not "result" in data or not "responses" in data:
        raise Exception("Unexpected reponse from router.")
    
    if data["result"] != "OK":
        response = data["responses"][0]
        if "error" in response:
            raise Exception(response["error"])
            