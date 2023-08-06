"""Linksys Smart Wifi device tracking"""

from homeassistant.components.device_tracker import ScannerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event as HomeAssistant
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .linksys import Linksys, LinksysConfig
from .const import DOMAIN

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
    devices = await linksys.async_get_devices()

    device_trackers: list[LinksysScannerEntity] = [
        LinksysScannerEntity(
            hass=hass,
            device=device,
        )
        for device in devices
    ]

    async_add_entities(device_trackers)

class LinksysScannerEntity(ScannerEntity):
    """Representation of a linksys scanner."""

    entity_description: LinksysTrackerEntityDescription

    def __init__(
        self,
        hass: HomeAssistant,
        device: dict,
    ) -> None:
        self.hass = hass
        self._device = device

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
        