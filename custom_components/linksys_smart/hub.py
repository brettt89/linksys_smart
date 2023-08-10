"""The Linksys router class."""

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_DETECTION_TIME,
    DEFAULT_DETECTION_TIME,
    DOMAIN
)
from .controller import LinksysController
from .device import Device

_LOGGER = logging.getLogger(__name__)

class LinksysData:
    """Handle all communication with the Linksys API."""

    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigEntry, api: LinksysController
    ) -> None:
        """Initialize the Linksys Client."""
        self.hass = hass
        self.config_entry = config_entry
        self.api = api
        self.all_devices: dict[str, dict[str, Any]] = {}
        self.devices: dict[str, Device] = {}
        self.manufacturer: str = ""
        self.hostname: str = ""
        self.model: str = ""
        self.firmware: str = ""
        self.serial_number: str = ""

    @staticmethod
    def load_mac(devices: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Load dictionary using MAC address as key."""
        mac_devices = {}
        for device in devices:
            if mac := device.get("macAddress"):
                mac_devices[mac] = device
                continue
            if len(connections := device.get("knownInterfaces", [])) == 1:
                if "macAddress" in connections[0]:
                    mac = connections[0]["macAddress"]
                    mac_devices[mac] = device
        return mac_devices

    async def async_get_linksys_details(self) -> None:
        """Get Linksys Router info."""
        if result := await self.api.async_get_device_info():
            self.hostname = result.get("description")
            self.manufacturer = result.get("manufacturer")
            self.model = result.get("modelNumber")
            self.firmware = result.get("firmwareVersion")
            self.serial_number = result.get("serialNumber")

    async def async_update_devices(self) -> None:
        """Get list of devices with latest status."""
        if devices := await self.api.async_get_devices():
            self.all_devices = self.load_mac(devices)

        if not self.all_devices:
            return

        if conns := await self.api.async_get_network_connections():
            connections = self.load_mac(conns)

        for mac, params in self.all_devices.items():
            if mac not in self.devices:
                self.devices[mac] = Device(mac, params)
            else:
                self.devices[mac].update(params=params)

            active = True

            if not mac in connections:
                active = False
            
            self.devices[mac].update(active=active)

class LinksysDataUpdateCoordinator(DataUpdateCoordinator[None]):
    """Linksys Router Object."""

    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigEntry, api: LinksysController
    ) -> None:
        """Initialize the Linksys Client."""
        self.hass = hass
        self.config_entry: ConfigEntry = config_entry
        self._linksys_data = LinksysData(self.hass, self.config_entry, api)
        super().__init__(
            self.hass,
            _LOGGER,
            name=f"{DOMAIN} - {self.host}",
            update_interval=timedelta(seconds=10),
        )

    @property
    def host(self) -> str:
        """Return the host of this hub."""
        return str(self.config_entry.data[CONF_HOST])

    @property
    def hostname(self) -> str:
        """Return the hostname of the hub."""
        return self._linksys_data.hostname

    @property
    def manufacturer(self) -> str:
        """Return the manufacturer of the hub."""
        return self._linksys_data.manufacturer

    @property
    def serial_num(self) -> str:
        """Return the serial number of the hub."""
        return self._linksys_data.serial_number

    @property
    def model(self) -> str:
        """Return the model of the hub."""
        return self._linksys_data.model

    @property
    def firmware(self) -> str:
        """Return the firmware of the hub."""
        return self._linksys_data.firmware

    @property
    def serial_num(self) -> str:
        """Return the serial number of the hub."""
        return self._linksys_data.serial_number

    @property
    def api(self) -> LinksysData:
        """Represent Linksys data object."""
        return self._linksys_data

    @property
    def option_detection_time(self) -> timedelta:
        """Config entry option defining number of seconds from last seen to away."""
        return timedelta(
            seconds=self.config_entry.options.get(
                CONF_DETECTION_TIME, DEFAULT_DETECTION_TIME
            )
        )

    async def _async_update_data(self) -> None:
        """Update Linksys devices information."""
        await self._linksys_data.async_update_devices()
