"""Network client device class."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.util import slugify
import homeassistant.util.dt as dt_util

from .const import ATTR_DEVICE_TRACKER


class Device:
    """Represents a network device."""


    def __init__(self, mac: str, params: dict[str, Any]):
        """Initialize the network device."""
        self._mac = mac
        self._params = params
        self._last_seen: datetime | None = None
        self._attrs: dict[str, Any] = {}

    @property
    def name(self) -> str | None:
        """Return device name."""
        # Check properties for name value and return if found
        for prop in self._params.get("properties", []):
            if prop["name"] == "userDeviceName":
                return prop["value"]
        
        # If device has a friendly name, return that
        if self._params.get("friendlyName"):
            return self._params.get("friendlyName")

        # default to device_id if nothing else can be found
        return self._params.get("deviceID")

    @property
    def ip_address(self) -> str | None:
        """Return device ip address."""
        if len(connections := self._params.get("connections", [])) == 1:
            return connections[0].get("ipAddress")

    @property
    def mac(self) -> str | None:
        """Return device mac."""
        return self._mac

    @property
    def last_seen(self) -> datetime | None:
        """Return device last seen."""
        return self._last_seen

    @property
    def attrs(self) -> dict[str, Any]:
        """Return device attributes."""
        for attr in ATTR_DEVICE_TRACKER:
            if attr in self._params:
                self._attrs[slugify(attr)] = self._params[attr]
        return self._attrs

    def update(
        self,
        params: dict[str, Any] | None = None,
        active: bool = False,
    ) -> None:
        """Update Device params."""
        if params:
            self._params = params
        if active:
            self._last_seen = dt_util.utcnow()