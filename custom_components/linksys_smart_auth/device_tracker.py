"""Linksys Smart Wifi device tracking"""

import logging

from homeassistant.components.device_tracker import ScannerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event as HomeAssistant
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .linksys import Linksys, LinksysConfig, Device
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
        device: Device,
        connections: list,
    ) -> None:
        self.hass = hass
        self._device = device
        self._mac_address = device.get("mac_address", None)

        self._id = device.get("id")
        self._name = device.get('name', self._id)
        self._connections = device.get('connections')

    def is_connected(self) -> bool:
        return self._device.is_online()
        