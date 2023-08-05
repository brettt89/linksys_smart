"""Support for Linksys Smart Wifi routers using auth."""
from __future__ import annotations

from http import HTTPStatus
import logging
import base64

from . import Device

import requests
import voluptuous as vol

from homeassistant.components.device_tracker import (
    DOMAIN,
    PLATFORM_SCHEMA as PARENT_PLATFORM_SCHEMA,
    DeviceScanner,
)
from homeassistant.const import ( CONF_HOST, CONF_USERNAME, CONF_PASSWORD, )
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

DEFAULT_TIMEOUT = 10

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PARENT_PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
})


def get_scanner(
    hass: HomeAssistant, config: ConfigType
) -> LinksysSmartWifiDeviceScanner | None:
    """Validate the configuration and return a Linksys AP scanner."""
    try:
        return LinksysSmartWifiDeviceScanner(config[DOMAIN])
    except ConnectionError:
        return None


class LinksysSmartWifiDeviceScanner(DeviceScanner):
    """Class which queries a Linksys Access Point."""

    def __init__(self, config):
        """Initialize the scanner."""
        self.host = config[CONF_HOST]
        self.username = config.get(CONF_USERNAME)
        self.password = config.get(CONF_PASSWORD)
        self.last_results = {}

        # Check if the access point is accessible
        response = self._make_request()
        if response.status_code != HTTPStatus.OK:
            raise ConnectionError("Cannot connect to Linksys Access Point")

    def scan_devices(self):
        """Scan for new devices and return a list with device IDs (MACs)."""
        self._update_info()

        return self.last_results.keys()

    def get_device_name(self, device):
        """Return the name (if known) of the device."""
        return self.last_results.get(device)

    def _update_info(self):
        """Check for connected devices."""
        _LOGGER.info("Checking Linksys Smart Wifi")

        self.last_results = {}
        online = []
        response = self._get_network_connections()
        if response.status_code != HTTPStatus.OK:
            _LOGGER.error(
                "Got HTTP status code %d when getting device list", response.status_code
            )
            return False
        try:
            data = response.json()
            result = data["responses"][0]
            for connection in result["output"]["connections"]:
                online[connection["macAddress"]] = connection
        except (KeyError, IndexError):
            _LOGGER.exception("Router returned unexpected response")
            return False

        response = self._get_devices()
        if response.status_code != HTTPStatus.OK:
            _LOGGER.error(
                "Got HTTP status code %d when getting device list", response.status_code
            )
            return False
        try:
            data = response.json()
            result = data["responses"][0]
            for data in result["output"]["devices"]:
                device = Device(data)
                if not (device.mac_address in online):
                    device.set_online(False)
                    _LOGGER.debug("Device %s is not connected", device.mac_address)
                    continue

                device.set_connection(online[device.mac_address])
                _LOGGER.debug("Device %s is connected", device.mac_address)
                
                self.last_results[device.mac_address] = device.name
        except (KeyError, IndexError):
            _LOGGER.exception("Router returned unexpected response")
            return False
        return True

    def _get_auth(self):
        # create the login hash
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded_credentials}"

    def _get_network_connections(self):
        data = [
            {
                "request": {},
                "action": "http://linksys.com/jnap/networkconnections/GetNetworkConnections",
            }
        ]
        headers = {
            "X-JNAP-Action": "http://linksys.com/jnap/core/Transaction",
            "X-JNAP-Authorization": self._get_auth()
        }
        return requests.post(
            f"http://{self.host}/JNAP/",
            timeout=DEFAULT_TIMEOUT,
            headers=headers,
            json=data,
        )

    def _get_devices(self):
        data = [
            {
                "request": {"sinceRevision": 0},
                "action": "http://linksys.com/jnap/devicelist/GetDevices3",
            }
        ]
        headers = {
            "X-JNAP-Action": "http://linksys.com/jnap/core/Transaction",
            "X-JNAP-Authorization": self._get_auth()
        }
        return requests.post(
            f"http://{self.host}/JNAP/",
            timeout=DEFAULT_TIMEOUT,
            headers=headers,
            json=data,
        )