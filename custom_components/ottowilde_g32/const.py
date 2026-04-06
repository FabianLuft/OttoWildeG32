"""Constants for the OttoWilde G32 integration."""

DOMAIN = "ottowilde_g32"

# Configuration
CONF_GRILL_IP = "grill_ip"

# Cloud connection
CLOUD_HOST = "3.120.177.98"
CLOUD_PORT = 4501
LOCAL_PORT = 4501

# mDNS discovery
MDNS_NAME = "g32connected"
MDNS_TYPE = "_ottowilde._tcp.local."

# Update intervals
SCAN_INTERVAL = 4  # Grill sends data every ~4 seconds

# Device info
MANUFACTURER = "OttoWilde"
MODEL = "G32 Connected"
