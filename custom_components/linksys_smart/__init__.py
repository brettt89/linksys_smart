"""The linksys_smart component."""

from types import MappingProxyType

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import config_validation as cv, device_registry as dr

from .const import DOMAIN
from .controller import LinksysController
from .hub import LinksysDataUpdateCoordinator

CONFIG_SCHEMA = cv.removed(DOMAIN, raise_if_present=False)

PLATFORMS = [Platform.DEVICE_TRACKER]

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up the Linksys component."""
    session = async_get_clientsession(hass)
    config = MappingProxyType(config_entry)
    api = LinksysController(session, config)
    api.async_initialize()
    coordinator = LinksysDataUpdateCoordinator(hass, config_entry, api)

    await coordinator.api.async_get_linksys_details()
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(DOMAIN, coordinator.serial_num)},
        manufacturer=coordinator.manufacturer,
        model=coordinator.model,
        name=coordinator.hostname,
        sw_version=coordinator.firmware,
    )

    return True

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    ):
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok