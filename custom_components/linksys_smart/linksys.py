""" Linksys Smart Wifi Support """

import logging
from types import MappingProxyType

from aiohttp import ClientError
from homeassistant.core import Event as HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .controller import LinksysController, LinksysError
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
        await self._store.async_remove()
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

    def get(self, name):
        return self._data.get(name)

class Linksys:

    def __init__(self, hass: HomeAssistant, config: LinksysConfig) -> None:
        self.hass = hass
        self.config = config
        self.devices = {}
        self.connections = {}

        self.services = []

    async def async_initialize(self):
        session = async_get_clientsession(self.hass)
        self._controller = LinksysController(session, self.config)
        await self._controller.async_initialize()

        try:
            device_info = await self._controller.async_get_device_info()
            wan_details = await self._controller.async_get_wan_status()
            connections = await self._controller.async_get_network_connections()
            devices = await self._controller.async_get_devices()
        except (ClientError, LinksysError) as err:
            _LOGGER.error("Linksys API error: %s", err)

        self.manufacturer = device_info.get("manufacturer", "Unknown")
        self.serial_number = device_info.get("serialNumber")
        self.model_number = device_info.get("modelNumber", "Unknown")
        self.hw_version = device_info.get("hardwareVersion")
        self.fw_version = device_info.get("firmwareVersion")
        self.fw_date = device_info.get("firmwareDate")
        self.description = device_info.get("description", "")
        self.services = device_info.get("services", [])

        
        self.mac = wan_details.get("macAddress")
        self.wan = {
            "type": wan_details.get("detectedWANType"),
            "status": wan_details.get("wanStatus"),
        }
        
        for connection in connections:
            mac = connection["macAddress"]
            self.connections[mac] = connection
        
        for data in devices:
            device = Device(data)
            if device.mac_address:
                self.devices[device.mac_address] = device

            # If device is matching router, then mark as seen
            if self.mac == device.mac_address:
                device.seen()
                continue

            # Check devices for mac address and mark as seen
            if device.mac_address in self.connections:
                device.seen()
                continue

            # If mac not found in devices, mark as unseen
            device.unseen()
        
class Device:
    def __init__(self, config):
        self.device_id = config.get("deviceID")
        self.friendly_name = config.get("friendlyName", None)
        self.interfaces = config.get("knownInterfaces", [])
        self.connections = config.get("connections", [])
        self.properties = config.get("properties", [])
        self.online = False
        self.mac_address = None
        self.ip_address = None

        if len(self.interfaces) == 1:
            if "macAddress" in self.interfaces[0]:
                self.mac_address = self.interfaces[0].get("macAddress")

        if len(self.connections) == 1:
            if "ipAddress" in self.connections[0]:
                self.ip_address = self.connections[0].get("ipAddress")
            if "ipv6Address" in self.connections[0]:
                self.ipv6_address = self.connections[0].get("ipv6Address")

    def is_online(self) -> bool:
        return self.online

    def seen(self) -> None:
        self.online = True

    def unseen(self) -> None:
        self.online = False

    @property
    def name(self) -> str | None:
        # Check properties for name value and return if found
        for prop in self.properties:
            if prop["name"] == "userDeviceName":
                return prop["value"]
        
        # If device has a friendly name, return that
        if self.friendly_name:
            return self.friendly_name

        # default to device_id if nothing else can be found
        return self.device_id

    @property
    def unique_id(self) -> str | None:
        if self.mac_address:
            return self.mac_address
        return self.id