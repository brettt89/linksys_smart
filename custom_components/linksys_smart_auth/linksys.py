""" Linksys Smart Wifi Support """

import logging

from homeassistant.core import Event as HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .controller import LinksysController
from .const import DOMAIN

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

class Linksys:

    def __init__(self, hass: HomeAssistant, config: LinksysConfig) -> None:
        self.hass = hass
        self.config = config
        self.devices = {}
        self.connections = {}

    async def async_initialize(self):
        session = async_get_clientsession(self.hass)
        self._controller = LinksysController(session, self.config)
        await self._controller.async_initialize()

        devices = await self._controller.async_get_devices()
        for data in devices:
            device = Device(data)
            if device.mac_address:
                self.devices[device.mac_address] = device

        connections = await self._controller.async_get_network_connections()
        for connection in connections:
            mac = connection["macAddress"]
            self.connections[mac] = connection

            if mac in self.devices:
                device: Device = self.devices[mac]
                device.seen()

        
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