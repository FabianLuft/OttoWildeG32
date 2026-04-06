"""The OttoWilde G32 integration."""
import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .proxy import OttoWildeProxy

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.NUMBER, Platform.CLIMATE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OttoWilde G32 from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    grill_ip = entry.data["grill_ip"]

    _LOGGER.info(f"Setting up OttoWilde G32 integration for grill at {grill_ip}")

    # Create and start the MITM proxy
    proxy = OttoWildeProxy(hass, grill_ip)

    try:
        await proxy.start()
    except Exception as err:
        _LOGGER.error(f"Failed to start proxy: {err}")
        return False

    # Store proxy instance
    hass.data[DOMAIN][entry.entry_id] = proxy

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading OttoWilde G32 integration")

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Stop and remove proxy
        proxy = hass.data[DOMAIN].pop(entry.entry_id)
        await proxy.stop()

    return unload_ok
