"""The linksys_smart_auth component."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .linksys import Linksys, LinksysConfig

from .const import (
    DOMAIN
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Create a config entry."""
    config = LinksysConfig(config_entry)
    linksys = Linksys(hass, config)
    linksys.initialize()

    hass.data[DOMAIN][config_entry.entry_id] = linksys

