"""Climate platform for OttoWilde G32 dial controls."""
from __future__ import annotations

from typing import Any

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from homeassistant.components.climate.const import HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN, MANUFACTURER, MODEL

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OttoWilde climate dial entities."""

    climates = []

    # Zone climate entities (0-600°C, step 10)
    for i in range(1, 5):
        climates.append(
            OttoWildeClimate(
                entry=entry,
                num=i,
                entity_type="zone",
                sensor_entity=f"sensor.ottowilde_g32_zone_{i}",
                number_entity=f"number.ottowilde_g32_grill_zone_{i}_target",
                min_temp=0,
                max_temp=600,
                temp_step=10,
            )
        )

    # Probe climate entities (0-120°C, step 1)
    for i in range(1, 5):
        climates.append(
            OttoWildeClimate(
                entry=entry,
                num=i,
                entity_type="probe",
                sensor_entity=f"sensor.ottowilde_g32_probe_{i}",
                number_entity=f"number.ottowilde_g32_grill_probe_{i}_target",
                min_temp=0,
                max_temp=120,
                temp_step=1,
            )
        )

    async_add_entities(climates)
    _LOGGER.info(f"Created {len(climates)} climate dial entities")


class OttoWildeClimate(ClimateEntity):
    """Climate entity for temperature dial control."""

    _attr_has_entity_name = True
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_modes = [HVACMode.HEAT]
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        entry: ConfigEntry,
        num: int,
        entity_type: str,
        sensor_entity: str,
        number_entity: str,
        min_temp: float,
        max_temp: float,
        temp_step: float,
    ) -> None:
        """Initialize climate dial entity."""
        self._entry = entry
        self._num = num
        self._type = entity_type
        self._sensor_entity = sensor_entity
        self._number_entity = number_entity

        # Temperature range configuration
        self._attr_min_temp = min_temp
        self._attr_max_temp = max_temp
        self._attr_target_temperature_step = temp_step

        # Entity configuration
        self._attr_unique_id = f"{entry.entry_id}_{entity_type}_{num}_dial"
        self._attr_name = f"{entity_type.capitalize()} {num} Dial"
        self._attr_icon = "mdi:fire" if entity_type == "zone" else "mdi:thermometer"

        # Device linkage
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="OttoWilde G32 Grill",
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

        # Internal state
        self._attr_current_temperature = None
        self._attr_target_temperature = None
        self._attr_hvac_mode = HVACMode.HEAT

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        # Track sensor entity for current temperature
        @callback
        def sensor_state_listener(event):
            """Handle sensor state changes."""
            new_state = event.data.get("new_state")
            if new_state is None or new_state.state in ["unknown", "unavailable"]:
                self._attr_current_temperature = None
            else:
                try:
                    self._attr_current_temperature = float(new_state.state)
                except (ValueError, TypeError):
                    self._attr_current_temperature = None
            self.async_write_ha_state()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._sensor_entity], sensor_state_listener
            )
        )

        # Track number entity for target temperature
        @callback
        def number_state_listener(event):
            """Handle number entity state changes."""
            new_state = event.data.get("new_state")
            if new_state is None or new_state.state in ["unknown", "unavailable"]:
                self._attr_target_temperature = None
            else:
                try:
                    self._attr_target_temperature = float(new_state.state)
                except (ValueError, TypeError):
                    self._attr_target_temperature = None
            self.async_write_ha_state()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._number_entity], number_state_listener
            )
        )

        # Initialize current values
        sensor_state = self.hass.states.get(self._sensor_entity)
        if sensor_state and sensor_state.state not in ["unknown", "unavailable"]:
            try:
                self._attr_current_temperature = float(sensor_state.state)
            except (ValueError, TypeError):
                pass

        number_state = self.hass.states.get(self._number_entity)
        if number_state and number_state.state not in ["unknown", "unavailable"]:
            try:
                self._attr_target_temperature = float(number_state.state)
            except (ValueError, TypeError):
                pass

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if ATTR_TEMPERATURE not in kwargs:
            return

        temperature = kwargs[ATTR_TEMPERATURE]

        # Update the number entity
        await self.hass.services.async_call(
            "number",
            "set_value",
            {
                "entity_id": self._number_entity,
                "value": temperature,
            },
            blocking=True,
        )

        _LOGGER.debug(
            f"Set {self._type} {self._num} target temperature to {temperature}°C"
        )

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode (always heat for grill)."""
        # Grill is always in heat mode, no action needed
        pass
