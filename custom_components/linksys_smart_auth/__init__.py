"""The linksys_smart_auth component."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .linksys import Linksys, LinksysConfig

from .const import (
    DOMAIN
)

PLATFORMS = [Platform.DEVICE_TRACKER]

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Create a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = config_entry.data

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True
