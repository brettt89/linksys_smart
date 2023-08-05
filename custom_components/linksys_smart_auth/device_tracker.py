"""Support for Linksys Smart Wifi routers using auth."""

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

async def async_setup(hass: HomeAssistant, config: ConfigEntry):
    """Add the entities."""
    test = "test"
    # device_trackers: List[LinksysVelopMeshDeviceTracker] = [
    #     LinksysVelopMeshDeviceTracker(
    #         config_entry=config,
    #         device_id=tracker,
    #         hass=hass,
    #     )
    #     for tracker in config.options.get(CONF_DEVICE_TRACKERS, [])
    # ]

    # async_add_entities(device_trackers)

# from __future__ import annotations

# from http import HTTPStatus
# import logging
# import base64

# import requests
# import voluptuous as vol

# from homeassistant.components.device_tracker import (
#     DOMAIN,
#     PLATFORM_SCHEMA as PARENT_PLATFORM_SCHEMA,
#     DeviceScanner,
# )
# from homeassistant.const import ( CONF_HOST, CONF_USERNAME, CONF_PASSWORD, )
# from homeassistant.core import HomeAssistant
# import homeassistant.helpers.config_validation as cv
# from homeassistant.helpers.typing import ConfigType

# DEFAULT_TIMEOUT = 10

# _LOGGER = logging.getLogger(__name__)

# PLATFORM_SCHEMA = PARENT_PLATFORM_SCHEMA.extend({
#     vol.Required(CONF_HOST): cv.string,
#     vol.Required(CONF_USERNAME): cv.string,
#     vol.Required(CONF_PASSWORD): cv.string,
# })


# def get_scanner(
#     hass: HomeAssistant, config: ConfigType
# ) -> LinksysSmartWifiDeviceScanner | None:
#     """Validate the configuration and return a Linksys AP scanner."""
#     try:
#         return LinksysSmartWifiDeviceScanner(config[DOMAIN])
#     except ConnectionError:
#         return None


# class LinksysSmartWifiDeviceScanner(DeviceScanner):
#     """Class which queries a Linksys Access Point."""

#     def __init__(self, config):
#         """Initialize the scanner."""
#         self.host = config[CONF_HOST]
#         self.username = config.get(CONF_USERNAME)
#         self.password = config.get(CONF_PASSWORD)
#         self.last_results = {}

#         # Check if the access point is accessible
#         response = self._get_router()
#         if response.status_code != HTTPStatus.OK:
#             raise ConnectionError("Cannot connect to Linksys Access Point")

#     def scan_devices(self):
#         """Scan for new devices and return a list with device IDs (MACs)."""
#         self._update_info()

#         return self.last_results.keys()

#     def get_device_name(self, device):
#         """Return the name (if known) of the device."""
#         return self.last_results.get(device)

#     def _update_info(self):
#         """Check for connected devices."""
#         _LOGGER.info("Checking Linksys Smart Wifi")

#         self.last_results = {}
#         online = {}
#         response = self._get_network_connections()
#         if response.status_code != HTTPStatus.OK:
#             _LOGGER.error(
#                 "Got HTTP status code %d when getting device list", response.status_code
#             )
#             return False
#         try:
#             data = response.json()
#             result = data["responses"][0]
#             for connection in result["output"]["connections"]:
#                 online[connection["macAddress"]] = connection
#         except (KeyError, IndexError):
#             _LOGGER.exception("Router returned unexpected response")
#             return False

#         response = self._get_devices()
#         if response.status_code != HTTPStatus.OK:
#             _LOGGER.error(
#                 "Got HTTP status code %d when getting device list", response.status_code
#             )
#             return False
#         try:
#             data = response.json()
#             result = data["responses"][0]
#             for data in result["output"]["devices"]:
#                 device = Device(data)
#                 if not (device.mac_address in online):
#                     device.set_online(False)
#                     _LOGGER.debug("Device %s is not connected", device.mac_address)
#                     continue

#                 device.set_connection(online[device.mac_address])
#                 _LOGGER.debug("Device %s is connected", device.mac_address)
                
#                 self.last_results[device.mac_address] = device.name
#         except (KeyError, IndexError):
#             _LOGGER.exception("Router returned unexpected response")
#             return False
#         return True

#     def _get_auth(self):
#         # create the login hash
#         credentials = f"{self.username}:{self.password}"
#         encoded_credentials = base64.b64encode(credentials.encode()).decode()
#         return f"Basic {encoded_credentials}"

#     def _get_network_connections(self):
#         data = [
#             {
#                 "request": {},
#                 "action": "http://linksys.com/jnap/networkconnections/GetNetworkConnections",
#             }
#         ]
#         headers = {
#             "X-JNAP-Action": "http://linksys.com/jnap/core/Transaction",
#             "X-JNAP-Authorization": self._get_auth()
#         }
#         return requests.post(
#             f"http://{self.host}/JNAP/",
#             timeout=DEFAULT_TIMEOUT,
#             headers=headers,
#             json=data,
#         )

#     def _get_devices(self):
#         data = [
#             {
#                 "request": {"sinceRevision": 0},
#                 "action": "http://linksys.com/jnap/devicelist/GetDevices3",
#             }
#         ]
#         headers = {
#             "X-JNAP-Action": "http://linksys.com/jnap/core/Transaction",
#             "X-JNAP-Authorization": self._get_auth()
#         }
#         return requests.post(
#             f"http://{self.host}/JNAP/",
#             timeout=DEFAULT_TIMEOUT,
#             headers=headers,
#             json=data,
#         )

#     def _get_router(self):
#         data = [
#             {
#                 "request": {},
#                 "action": "http://linksys.com/jnap/core/GetDeviceInfo",
#             }
#         ]
#         headers = {
#             "X-JNAP-Action": "http://linksys.com/jnap/core/Transaction",
#             "X-JNAP-Authorization": self._get_auth()
#         }
#         return requests.post(
#             f"http://{self.host}/JNAP/",
#             timeout=DEFAULT_TIMEOUT,
#             headers=headers,
#             json=data,
#         )

# class Device:

#     def __init__(self, info):
#         self.raw_info = info
#         self._process()

#     def _process(self):
#         self.device_id = self.raw_info["deviceID"]

#         # Default to friendlyName or deviceID if not found
#         self.name = self.raw_info.get("friendlyName", self.device_id)
#         # Check properties for name value and override if found
#         for prop in self.raw_info["properties"]:
#             if prop["name"] == "userDeviceName":
#                 self.name = prop["value"]
        
#         interfaces = self.raw_info['knownInterfaces']
#         connections = self.raw_info['connections']

#         # Loop over interfaces to get MAC address data
#         self.mac_address = "Unknown"
#         for interface in interfaces:
#             if not (mac := interface["macAddress"]):
#                 _LOGGER.warning("Skipping interface without known MAC address")
#                 continue

#             self.mac_address = mac
        
#         # Loop over connections to find IP address data
#         self.ip_address = "Unknown"
#         for connection in connections:
#             if not (ip := connection["ipAddress"]):
#                 _LOGGER.warning("Skipping interface without known ip address")
#                 continue

#             self.ip_address = ip

#     def set_connection(self, connection):
#         self.connection = Connection(connection)
    
#     def set_online(self, flag):
#         self.online = flag

# class Connection:

#     def __init__(self, connection):
#         self.mac_address = connection['macAddress']
#         self.negotiated_mbps = connection['negotiatedMbps']

#         if "wireless" in connection:
#             self.wireless = connection["wireless"]

#     def is_wireless(self):
#         return self.hasattr("wireless")
        