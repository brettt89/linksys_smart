"""The linksys_smart_auth component."""

import logging

_LOGGER = logging.getLogger(__name__)

class Device:

    def __init__(self, info):
        self.raw_info = info
        self._process()

    def _process(self):
        self.device_id = self.raw_info["deviceID"]

        # Default to friendlyName or deviceID if not found
        self.name = self.raw_info.get("friendlyName", self.device_id)
        # Check properties for name value and override if found
        for prop in self.raw_info["properties"]:
            if prop["name"] == "userDeviceName":
                self.name = prop["value"]
        
        interfaces = self.raw_info['knownInterfaces']
        connections = self.raw_info['connections']

        # Loop over interfaces to get MAC address data
        self.mac_address = "Unknown"
        for interface in interfaces:
            if not (mac := interface["macAddress"]):
                _LOGGER.warning("Skipping interface without known MAC address")
                continue

            self.mac_address = mac
        
        # Loop over connections to find IP address data
        self.ip_address = "Unknown"
        for connection in connections:
            if not (ip := connection["ipAddress"]):
                _LOGGER.warning("Skipping interface without known ip address")
                continue

            self.ip_address = ip

    def set_connection(self, connection):
        self.connection = Connection(connection)
    
    def set_online(self, flag):
        self.online = flag

class Connection:

    def __init__(self, connection):
        self.mac_address = connection['macAddress']
        self.negotiated_mbps = connection['negotiatedMbps']

        if "wireless" in connection:
            self.wireless = connection["wireless"]

    def is_wireless(self):
        return self.hasattr("wireless")
        