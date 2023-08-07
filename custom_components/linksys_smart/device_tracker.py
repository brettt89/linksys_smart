"""Linksys Smart Wifi device tracking"""

import logging

from homeassistant.components.device_tracker import ScannerEntity, SourceType
from homeassistant.components.device_tracker import DOMAIN as ENTITY_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event as HomeAssistant
from homeassistant.helpers import device_registry as dr
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

    config = LinksysConfig(hass, config_data)
    await  config.async_initialize()

    linksys = Linksys(hass, config)
    await linksys.async_initialize()

    # Register Linksys device
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, linksys.mac)},
        identifiers={(DOMAIN, linksys.serial_number)},
        manufacturer=linksys.manufacturer,
        suggested_area="Lounge",
        name=linksys.description,
        model=linksys.model_number,
        sw_version=linksys.fw_version,
        hw_version=linksys.hw_version,
    )

    device_trackers: list[LinksysScannerEntity] = [
        LinksysScannerEntity(
            config_entry=config_entry,
            device=device,
            connections=linksys.connections
        )
        for device in linksys.devices.values()
    ]

    async_add_entities(device_trackers)

class LinksysScannerEntity(ScannerEntity):
    """Representation of a linksys scanner."""

    entity_description: LinksysTrackerEntityDescription

    def __init__(
        self,
        config_entry: ConfigEntry,
        device: Device,
        connections: list,
    ) -> None:
        self._config: ConfigEntry = config_entry
        self._device = device
        self._mac = device.mac_address
        self._ip = device.ip_address

        _LOGGER.debug("Mac Address: %s", self._mac)

        self._attr_has_entity_name = True
        self._attr_name = device.name
        self._connections = device.connections

    @property
    def is_connected(self) -> bool:
        return self._device.is_online()

    @property
    def ip_address(self) -> str | None:
        """Get the IP address."""
        return self._ip

    @property
    def mac_address(self) -> str | None:
        """Get the MAC address."""
        return self._mac

    @property
    def source_type(self) -> str:
        """Get the source of the device tracker."""
        return SourceType.ROUTER

    @property
    def unique_id(self) -> str | None:
        """Get the unique_id."""
        if self._device is not None:
            return (
                f"{self._config.entry_id}::"
                f"{ENTITY_DOMAIN.lower()}::"
                f"{self._device.unique_id}"
            )
        
        return None
        