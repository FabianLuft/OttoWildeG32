"""Config flow for OttoWilde G32 integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import zeroconf
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import CONF_GRILL_IP, DOMAIN, MDNS_NAME, MDNS_TYPE

_LOGGER = logging.getLogger(__name__)


async def validate_grill_ip(hass: HomeAssistant, grill_ip: str) -> dict[str, Any]:
    """Validate that the grill IP is reachable."""
    # Simple reachability check - try to open a connection
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(grill_ip, 4501),
            timeout=5.0
        )
        writer.close()
        await writer.wait_closed()
        return {"title": f"OttoWilde G32 ({grill_ip})"}
    except (asyncio.TimeoutError, OSError) as err:
        _LOGGER.warning(f"Could not connect to grill at {grill_ip}: {err}")
        # Still allow setup even if grill is currently offline
        return {"title": f"OttoWilde G32 ({grill_ip})"}


class OttoWildeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OttoWilde G32."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.discovered_ip: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            grill_ip = user_input[CONF_GRILL_IP]

            # Check if already configured
            await self.async_set_unique_id(grill_ip)
            self._abort_if_unique_id_configured()

            try:
                info = await validate_grill_ip(self.hass, grill_ip)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=info["title"],
                    data={CONF_GRILL_IP: grill_ip},
                )

        # Try mDNS discovery
        if self.discovered_ip is None:
            try:
                self.discovered_ip = await self._discover_grill()
            except Exception as err:
                _LOGGER.debug(f"mDNS discovery failed: {err}")

        # Show form with discovered IP or empty
        data_schema = vol.Schema({
            vol.Required(
                CONF_GRILL_IP,
                default=self.discovered_ip or ""
            ): cv.string,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "dns_setup": "Make sure DNS redirect is configured in UniFi router:\n"
                            "ssh admin@router_ip\n"
                            "echo 'address=/socket.ottowildeapp.com/<HOMEASSISTANT_IP>' "
                            ">> /etc/dnsmasq.d/ottowilde.conf\n"
                            "killall -HUP dnsmasq"
            },
        )

    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle zeroconf discovery."""
        _LOGGER.info(f"Discovered OttoWilde G32 via mDNS: {discovery_info}")

        # Get IP address from discovery
        self.discovered_ip = discovery_info.host

        # Check if already configured
        await self.async_set_unique_id(self.discovered_ip)
        self._abort_if_unique_id_configured()

        return await self.async_step_user()

    async def _discover_grill(self) -> str | None:
        """Try to discover grill via mDNS."""
        try:
            # Use HomeAssistant's zeroconf instance to look for the grill
            from homeassistant.components.zeroconf import async_get_instance

            zc = await async_get_instance(self.hass)

            # Look for the g32connected.localdomain service
            # This is a simplified approach - full mDNS browsing would be more complex
            _LOGGER.debug("Attempting mDNS discovery for OttoWilde G32")

            # For now, return None and rely on manual entry
            # Full mDNS browsing implementation would require additional async listeners
            return None

        except Exception as err:
            _LOGGER.debug(f"mDNS discovery error: {err}")
            return None
