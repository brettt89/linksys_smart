
"""Constants used in the Linksys components."""
from typing import Final

DOMAIN: Final = "linksys_smart"
DEFAULT_NAME: Final = "Linksys"

CONF_DETECTION_TIME: Final = "detection_time"
DEFAULT_DETECTION_TIME: Final = 300

ATTR_DEVICE_TRACKER: Final = [
    "deviceID",
    "lastChangeRevision",
    "model",
    "unit",
    "isAuthority",
    "properties",
    "knownInterfaces",
    "connections",
]