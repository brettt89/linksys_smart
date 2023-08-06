"""Linksys Smart Wifi device tracking"""

import logging

from homeassistant.components.device_tracker import ScannerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event as HomeAssistant
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .linksys import Linksys, LinksysConfig
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class LinksysTrackerEntityDescription(EntityDescription):
    """Class describing Linksys device tracker entity."""

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up device tracker for UniFi Network integration."""
    config_data = hass.data[DOMAIN][config_entry.entry_id]

    _LOGGER.debug(
        "Config Data: %s %s %s",
        config_data.get("host"),
        config_data.get("username"),
        config_data.get("password"),
    )

    config = LinksysConfig(hass, config_data)
    await  config.async_initialize()

    linksys = Linksys(hass, config)
    await linksys.async_initialize()

    device_trackers: list[LinksysScannerEntity] = [
        LinksysScannerEntity(
            hass=hass,
            device=device,
            connections=linksys.connections
        )
        for device in linksys.devices
    ]

    async_add_entities(device_trackers)

class LinksysScannerEntity(ScannerEntity):
    """Representation of a linksys scanner."""

    entity_description: LinksysTrackerEntityDescription

    def __init__(
        self,
        hass: HomeAssistant,
        device: dict,
        connections: list,
    ) -> None:
        self.hass = hass
        self._device = device
        self._mac_address = device.get("mac", None)

        self._id = device.get("device_id")
        self._name = device.get('friendlyName', self._id)

        self._get_device_adapter_info()

    def _get_device_adapter_info(self) -> None:
        self._interfaces: list[dict] = [a for a in self._device.get("knownInterfaces")]
        if self._interfaces:
            self._mac = self._interfaces[0].get("macAddress", "")

        self._connections: list[dict] = [a for a in self._device.get("connections")]
        if self._connections:
            self._ip = self._connections[0].get("ip", "")

    def is_connected(self) -> bool:
        if self._mac_address in self._connections:
            return True
        return False
        