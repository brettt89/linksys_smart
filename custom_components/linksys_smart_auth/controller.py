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

        self.host = config.host
        self.username = config.username
        self.password = config.password

        self.url = f"http://{self.host}/{LINKSYS_JNAP_ENDPOINT}"
        self.headers: dict[str, Any] = {}

        self.details: dict[str, Any] = {}
        self.services: list[str] = []


    async def async_initialize(self) -> None:
        """Load Linksys Smart Wifi parameters."""

        credentials_string = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials_string.encode()).decode()
        auth_string =  f"Basic {encoded_credentials}"

        self.headers[LOCAL_JNAP_ACTION_HEADER] = LOCAL_JNAP_ACTION_TRANSACTION
        self.headers[LOCAL_JNAP_AUTHORIZATION_HEADER] = auth_string

        responses = await self.async_get_device_info()

        self.device_info = responses[0]
        self.services = responses[0].get("services", [])


    async def async_get_device_info(self) -> list[dict]:
        """Load Linksys Smart Wifi devices"""

        return await self.request("core/GetDeviceInfo")

    async def async_get_devices(self) -> list[dict]:
        """Load Linksys Smart Wifi devices"""

        return await self.request("devicelist/GetDevices3")

    
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
            