"""Number platform for the Adaptive Lighting integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import slugify

from .const import (
    CONF_NAME,
    DEFAULT_OVERRIDE_BRIGHTNESS,
    DEFAULT_OVERRIDE_COLOR_TEMP,
    DOMAIN,
    ICON_BRIGHTNESS,
    ICON_COLOR_TEMP,
    OVERRIDE_BRIGHTNESS_NUMBER,
    OVERRIDE_COLOR_TEMP_NUMBER,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)


class SimpleNumber(NumberEntity, RestoreEntity):
    """Representation of an Adaptive Lighting number entity."""

    def __init__(
        self,
        which: str,
        initial_value: float,
        min_value: float,
        max_value: float,
        step: float,
        unit: str,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        icon: str,
    ) -> None:
        """Initialize the Adaptive Lighting number entity."""
        self.hass = hass
        self._icon = icon
        self._value: float | None = None
        self._which = which
        self._config_name = config_entry.data.get(CONF_NAME) or config_entry.options.get(CONF_NAME)
        self._unique_id = f"{self._config_name}_{slugify(self._which)}"
        self._name = f"Adaptive Lighting {which}: {self._config_name}"
        self._initial_value = initial_value
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit
        self._attr_mode = NumberMode.SLIDER

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID of entity."""
        return self._unique_id

    @property
    def icon(self) -> str:
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        return self._value

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                (DOMAIN, self._config_name),
            },
            name=f"Adaptive Lighting: {self._config_name}",
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_added_to_hass(self) -> None:
        """Call when entity about to be added to hass."""
        last_state = await self.async_get_last_state()
        _LOGGER.debug("%s: last state is %s", self._name, last_state)
        if last_state is not None and last_state.state not in (None, "unknown", "unavailable"):
            try:
                self._value = float(last_state.state)
            except (ValueError, TypeError):
                self._value = self._initial_value
        else:
            self._value = self._initial_value

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        _LOGGER.debug("%s: Setting value to %s", self._name, value)
        self._value = value
        self.async_write_ha_state()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Adaptive Lighting number entities."""
    data = hass.data[DOMAIN]

    override_brightness_number = SimpleNumber(
        which="Override Brightness",
        initial_value=DEFAULT_OVERRIDE_BRIGHTNESS,
        min_value=1,
        max_value=100,
        step=1,
        unit="%",
        hass=hass,
        config_entry=config_entry,
        icon=ICON_BRIGHTNESS,
    )
    override_color_temp_number = SimpleNumber(
        which="Override Color Temperature",
        initial_value=DEFAULT_OVERRIDE_COLOR_TEMP,
        min_value=2000,
        max_value=6500,
        step=100,
        unit="K",
        hass=hass,
        config_entry=config_entry,
        icon=ICON_COLOR_TEMP,
    )

    # Store in hass.data for switch.py to access
    data[config_entry.entry_id][OVERRIDE_BRIGHTNESS_NUMBER] = override_brightness_number
    data[config_entry.entry_id][OVERRIDE_COLOR_TEMP_NUMBER] = override_color_temp_number

    async_add_entities(
        [override_brightness_number, override_color_temp_number],
        update_before_add=True,
    )
