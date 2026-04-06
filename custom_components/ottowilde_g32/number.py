"""Number platform for OttoWilde G32 threshold configuration."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODEL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OttoWilde threshold number entities."""

    numbers = []

    # Zone thresholds (0-600°C, step 10)
    for i in range(1, 5):
        numbers.append(
            OttoWildeThresholdNumber(
                entry=entry,
                num=i,
                entity_type="zone",
                min_val=0,
                max_val=600,
                step=10,
                initial=300,
            )
        )

    # Probe thresholds (0-120°C, step 1)
    for i in range(1, 5):
        numbers.append(
            OttoWildeThresholdNumber(
                entry=entry,
                num=i,
                entity_type="probe",
                min_val=0,
                max_val=120,
                step=1,
                initial=60,
            )
        )

    async_add_entities(numbers)
    _LOGGER.info(f"Created {len(numbers)} threshold number entities")


class OttoWildeThresholdNumber(NumberEntity):
    """Number entity for temperature threshold configuration."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "°C"
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        entry: ConfigEntry,
        num: int,
        entity_type: str,
        min_val: float,
        max_val: float,
        step: float,
        initial: float,
    ) -> None:
        """Initialize threshold number entity."""
        self._entry = entry
        self._num = num
        self._type = entity_type
        self._attr_native_min_value = min_val
        self._attr_native_max_value = max_val
        self._attr_native_step = step
        self._attr_native_value = initial

        # Entity configuration
        self._attr_unique_id = f"{entry.entry_id}_{entity_type}_{num}_threshold"
        self._attr_name = f"{entity_type.capitalize()} {num} Target"
        self._attr_icon = "mdi:fire" if entity_type == "zone" else "mdi:thermometer"

        # Device linkage
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="OttoWilde G32 Grill",
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set new threshold value."""
        self._attr_native_value = value
        self.async_write_ha_state()
        _LOGGER.debug(
            f"Set {self._type} {self._num} threshold to {value}°C"
        )
