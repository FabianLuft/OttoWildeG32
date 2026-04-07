"""Sensor platform for OttoWilde G32 grill."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
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
    """Set up OttoWilde G32 sensors."""
    proxy = hass.data[DOMAIN][entry.entry_id]

    sensors: list[SensorEntity] = []

    # Add zone temperature sensors (4 zones)
    for i in range(1, 5):
        sensors.append(OttoWildeZoneSensor(proxy, entry, i))

    # Add probe temperature sensors (4 probes)
    for i in range(1, 5):
        sensors.append(OttoWildeProbeSensor(proxy, entry, i))

    # Add gas level sensor
    sensors.append(OttoWildeGasSensor(proxy, entry))

    # Add configuration sensor
    sensors.append(OttoWildeLightSensitivitySensor(proxy, entry))

    async_add_entities(sensors)


class OttoWildeBaseSensor(SensorEntity):
    """Base class for OttoWilde sensors."""

    _attr_has_entity_name = True

    def __init__(self, proxy, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
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


class OttoWildeZoneSensor(OttoWildeBaseSensor):
    """Representation of a grill zone temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, proxy, entry: ConfigEntry, zone_number: int) -> None:
        """Initialize the zone sensor."""
        super().__init__(proxy, entry)
        self._zone_number = zone_number
        self._zone_key = f"zone_{zone_number}"
        self._attr_name = f"Zone {zone_number}"
        self._attr_unique_id = f"{entry.entry_id}_zone_{zone_number}"
        self._attr_native_value = None

    def _handle_coordinator_update(self, data: dict[str, Any]) -> None:
        """Handle updated data from the proxy."""
        if 'zones' in data:
            if self._zone_key in data['zones']:
                self._attr_native_value = data['zones'][self._zone_key]
                self.async_write_ha_state()
            elif data['zones'].get(self._zone_key) is None:
                # Explicitly set to None when grill is off
                self._attr_native_value = None
                self.async_write_ha_state()


class OttoWildeProbeSensor(OttoWildeBaseSensor):
    """Representation of a meat probe temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, proxy, entry: ConfigEntry, probe_number: int) -> None:
        """Initialize the probe sensor."""
        super().__init__(proxy, entry)
        self._probe_number = probe_number
        self._probe_key = f"probe_{probe_number}"
        self._attr_name = f"Probe {probe_number}"
        self._attr_unique_id = f"{entry.entry_id}_probe_{probe_number}"
        self._attr_native_value = None

    def _handle_coordinator_update(self, data: dict[str, Any]) -> None:
        """Handle updated data from the proxy."""
        if 'probes' in data:
            if self._probe_key in data['probes']:
                # Update with value (could be None if probe disconnected, or a temperature)
                self._attr_native_value = data['probes'][self._probe_key]
                self.async_write_ha_state()


class OttoWildeGasSensor(OttoWildeBaseSensor):
    """Representation of gas tank level sensor."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_name = "Gas Level"

    def __init__(self, proxy, entry: ConfigEntry) -> None:
        """Initialize the gas sensor."""
        super().__init__(proxy, entry)
        self._attr_unique_id = f"{entry.entry_id}_gas_level"
        self._attr_native_value = None

    def _handle_coordinator_update(self, data: dict[str, Any]) -> None:
        """Handle updated data from the proxy."""
        if 'gas_level' in data and data['gas_level'] is not None:
            self._attr_native_value = data['gas_level']
            self.async_write_ha_state()


class OttoWildeConfigBaseSensor(SensorEntity):
    """Base class for configuration sensors."""

    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = True

    def __init__(self, proxy, entry: ConfigEntry) -> None:
        """Initialize the config sensor."""
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
        def handle_config_update(event):
            """Handle proxy config update events."""
            self._handle_config_update(event.data)

        self.async_on_remove(
            self.hass.bus.async_listen(f"{DOMAIN}_config_update", handle_config_update)
        )

    def _handle_config_update(self, data: dict[str, Any]) -> None:
        """Handle updated config from the proxy."""
        # Override in subclasses
        pass


class OttoWildeLightSensitivitySensor(OttoWildeConfigBaseSensor):
    """Sensor showing grill light sensitivity level (1-3)."""

    _attr_name = "Light Sensitivity"
    _attr_icon = "mdi:lightbulb-cfl"

    def __init__(self, proxy, entry: ConfigEntry) -> None:
        """Initialize the light sensitivity sensor."""
        super().__init__(proxy, entry)
        self._attr_unique_id = f"{entry.entry_id}_light_sensitivity"
        self._attr_native_value = None

    def _handle_config_update(self, data: dict[str, Any]) -> None:
        """Handle updated config from the proxy."""
        if 'light_sensitivity' in data:
            level = data['light_sensitivity']
            self._attr_native_value = level if level is not None else "Unknown"
            self.async_write_ha_state()
