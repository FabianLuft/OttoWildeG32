"""Binary sensor platform for OttoWilde G32 grill."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODEL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OttoWilde G32 binary sensors."""
    proxy = hass.data[DOMAIN][entry.entry_id]

    sensors: list[BinarySensorEntity] = [
        OttoWildeHoodSensor(proxy, entry),
        OttoWildeAutoLightSensor(proxy, entry),
        OttoWildeWarningsEnabledSensor(proxy, entry),
    ]

    async_add_entities(sensors)


class OttoWildeBaseBinarySensor(BinarySensorEntity):
    """Base class for OttoWilde binary sensors."""

    _attr_has_entity_name = True

    def __init__(self, proxy, entry: ConfigEntry) -> None:
        """Initialize the binary sensor."""
        self.proxy = proxy
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="OttoWilde G32 Grill",
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        @callback
        def handle_update(event):
            """Handle proxy update events."""
            self._handle_coordinator_update(event.data)

        self.async_on_remove(
            self.hass.bus.async_listen(f"{DOMAIN}_update", handle_update)
        )

    def _handle_coordinator_update(self, data: dict[str, Any]) -> None:
        """Handle updated data from the proxy."""
        # Override in subclasses
        pass


class OttoWildeHoodSensor(OttoWildeBaseBinarySensor):
    """Representation of hood status sensor."""

    _attr_device_class = BinarySensorDeviceClass.OPENING
    _attr_name = "Hood"

    def __init__(self, proxy, entry: ConfigEntry) -> None:
        """Initialize the hood sensor."""
        super().__init__(proxy, entry)
        self._attr_unique_id = f"{entry.entry_id}_hood"
        self._attr_is_on = None

    def _handle_coordinator_update(self, data: dict[str, Any]) -> None:
        """Handle updated data from the proxy."""
        if 'hood_open' in data:
            self._attr_is_on = data['hood_open']
            self.async_write_ha_state()


class OttoWildeAutoLightSensor(OttoWildeBaseBinarySensor):
    """Binary sensor showing if auto-light should be triggered based on light sensor."""

    _attr_device_class = BinarySensorDeviceClass.LIGHT
    _attr_name = "Auto Light Triggered"
    _attr_icon = "mdi:lightbulb-auto"

    def __init__(self, proxy, entry: ConfigEntry) -> None:
        """Initialize the auto-light sensor."""
        super().__init__(proxy, entry)
        self._attr_unique_id = f"{entry.entry_id}_auto_light"
        self._attr_is_on = None

    def _handle_coordinator_update(self, data: dict[str, Any]) -> None:
        """Handle updated data from the proxy."""
        if 'auto_light_triggered' in data:
            self._attr_is_on = data['auto_light_triggered']
            self.async_write_ha_state()


class OttoWildeWarningsEnabledSensor(OttoWildeBaseBinarySensor):
    """Binary sensor showing grill warnings state."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_name = "Warnings Enabled"
    _attr_icon = "mdi:alert"

    def __init__(self, proxy, entry: ConfigEntry) -> None:
        """Initialize the warnings sensor."""
        super().__init__(proxy, entry)
        self._attr_unique_id = f"{entry.entry_id}_warnings_enabled"
        self._attr_is_on = None

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        @callback
        def handle_config_update(event):
            """Handle proxy config update events."""
            if 'warnings_enabled' in event.data:
                self._attr_is_on = event.data['warnings_enabled']
                self.async_write_ha_state()

        self.async_on_remove(
            self.hass.bus.async_listen(f"{DOMAIN}_config_update", handle_config_update)
        )
