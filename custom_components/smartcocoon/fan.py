"""Support for SmartCocoon fans."""

from __future__ import annotations

from collections.abc import Callable
import logging
from typing import Any

from pysmartcocoon.manager import SmartCocoonManager

from homeassistant.components.fan import ENTITY_ID_FORMAT, FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import async_generate_entity_id

from . import SmartCocoonController
from .connection_monitor import ConnectionMonitor
from .const import DOMAIN, SC_PRESET_MODE_AUTO, SC_PRESET_MODE_ECO, SC_PRESET_MODES
from .model import FanExtraAttributes

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: Callable[[list[SmartCocoonFan]], None],
) -> None:
    """Initialize sensor platform from config entry."""

    _LOGGER.debug("Starting async_setup_entry")

    smartcocoon: SmartCocoonController = hass.data[DOMAIN][config_entry.entry_id]
    scmanager: SmartCocoonManager = smartcocoon.scmanager

    fans = []

    for fan_id in scmanager.fans:
        _LOGGER.debug("Adding Entity for fan_id: %s", fan_id)
        fans.append(SmartCocoonFan(hass, smartcocoon, fan_id))

    async_add_entities(fans)

    _LOGGER.debug("Completed async_setup_entry")


class SmartCocoonFan(FanEntity):  # type: ignore[misc]
    """A SmartCocoon fan entity."""

    def __init__(
        self,
        hass: HomeAssistant,
        smartcocoon: SmartCocoonController,
        fan_id: str,
    ) -> None:
        """Initialize the SmartCocoon entity."""

        self._fan_id = fan_id
        self._smartcocoon = smartcocoon
        self._scmanager = smartcocoon.scmanager
        self._enable_preset_modes = smartcocoon.enable_preset_modes

        if self._scmanager is None:
            raise ValueError("SmartCocoonManager is not initialized")

        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT,
            f"{self._scmanager.fans[self._fan_id].room_name}_{self._fan_id}",
            hass=hass,
        )

        # The fan can be updated directly by the SmartCocoon app.
        # Register callback without static private access.
        setattr(
            self._scmanager.fans[self._fan_id],
            "_async_update_fan_callback",
            self.async_update_fan_callback,
        )

        _LOGGER.debug("Initialized fan_id: %s", self._fan_id)
        # Initialize attribute cache
        self._attr_extra_state_attributes: FanExtraAttributes = {
            "room_name": self._get_fan_data().room_name
        }
        # Initialize availability tracking
        self._last_available: bool | None = None

    async def async_added_to_hass(self) -> None:
        """Run when entity is about to be added to Home Assistant."""
        # Build and set attributes immediately when added
        self._attr_extra_state_attributes = self._build_extra_attrs()
        _LOGGER.debug(
            "Fan %s: async_added_to_hass - initial attrs: %s",
            self._fan_id,
            self._attr_extra_state_attributes,
        )
        self.async_write_ha_state()

    def _get_fan_data(self) -> Any:
        """Get fan data from scmanager, ensuring it's not None."""
        if self._scmanager is None:
            raise ValueError("SmartCocoonManager is not initialized")
        return self._scmanager.fans[self._fan_id]

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._get_fan_data().connected  # type: ignore[no-any-return]

    @property
    def device_info(self) -> DeviceInfo:
        """Return info for device registry."""
        fan_data = self._get_fan_data()

        _LOGGER.debug(
            "device_info: fan_id: %s, sw_version: %s",
            self._fan_id,
            fan_data.firmware_version,
        )

        return {
            "identifiers": {(DOMAIN, f"smartcocoon_fan_{self._fan_id}")},
            "name": f"{fan_data.room_name}:{self._fan_id}",
            "model": "Smart Vent",
            "sw_version": fan_data.firmware_version,
            "manufacturer": "SmartCocoon",
        }

    @property
    def extra_state_attributes(self) -> FanExtraAttributes:
        """Return the device specific state attributes."""
        # Always refresh cached attributes before returning
        self._attr_extra_state_attributes = self._build_extra_attrs()
        _LOGGER.debug(
            "Fan %s: extra_state_attributes built: %s",
            self._fan_id,
            self._attr_extra_state_attributes,
        )
        return self._attr_extra_state_attributes

    def _build_extra_attrs(self) -> FanExtraAttributes:
        """Build extra attributes dict from current data sources.

        Branching is minimized here; detailed extraction happens in
        _extract_pysmartcocoon_attrs.
        """
        fan_data = self._get_fan_data()
        attrs: FanExtraAttributes = {"room_name": fan_data.room_name}

        try:
            attrs["fan_id"] = self._fan_id
            extracted = self._extract_pysmartcocoon_attrs(fan_data)
            if "firmware_version" in extracted:
                attrs["firmware_version"] = extracted["firmware_version"]
            if "connected" in extracted:
                attrs["connected"] = extracted["connected"]
            if "fan_on" in extracted:
                attrs["fan_on"] = extracted["fan_on"]
            if "mode" in extracted:
                attrs["mode"] = extracted["mode"]
            if "predicted_room_temperature" in extracted:
                attrs["predicted_room_temperature"] = extracted[
                    "predicted_room_temperature"
                ]
            if "is_room_estimating" in extracted:
                attrs["is_room_estimating"] = extracted["is_room_estimating"]
            if "thermostat_vendor" in extracted:
                attrs["thermostat_vendor"] = extracted["thermostat_vendor"]
            if "room_id" in extracted:
                attrs["room_id"] = extracted["room_id"]
            if "identifier" in extracted:
                attrs["identifier"] = extracted["identifier"]

            cm_attrs = self._extract_connection_monitor_attrs()
            if "last_connected" in cm_attrs:
                attrs["last_connected"] = cm_attrs["last_connected"]
            if "last_disconnected" in cm_attrs:
                attrs["last_disconnected"] = cm_attrs["last_disconnected"]
        except (AttributeError, KeyError, TypeError):
            pass

        return attrs

    def _extract_pysmartcocoon_attrs(self, fan_data: Any) -> dict[str, Any]:
        """Extract attributes exposed by pysmartcocoon.

        This keeps branching out of _build_extra_attrs to satisfy lint limits.
        """
        extracted: dict[str, Any] = {}

        value = getattr(fan_data, "firmware_version", None)
        if isinstance(value, str):
            extracted["firmware_version"] = value

        value = getattr(fan_data, "connected", None)
        if isinstance(value, bool):
            extracted["connected"] = value

        value = getattr(fan_data, "fan_on", None)
        if isinstance(value, bool):
            extracted["fan_on"] = value

        # Skip duplicating speed percentage (provided via FanEntity.percentage)
        _ = getattr(fan_data, "speed_pct", None)

        value = getattr(fan_data, "mode", None)
        if isinstance(value, str):
            extracted["mode"] = value

        value = getattr(fan_data, "predicted_room_temperature", None)
        if isinstance(value, (int, float)):
            extracted["predicted_room_temperature"] = float(value)

        value = getattr(fan_data, "is_room_estimating", None)
        if isinstance(value, bool):
            extracted["is_room_estimating"] = value

        value = getattr(fan_data, "thermostat_vendor", None)
        if isinstance(value, str):
            extracted["thermostat_vendor"] = value

        value = getattr(fan_data, "room_id", None)
        if isinstance(value, str):
            extracted["room_id"] = value

        value = getattr(fan_data, "identifier", None)
        if isinstance(value, str):
            extracted["identifier"] = value

        return extracted

    def _extract_connection_monitor_attrs(self) -> dict[str, str]:
        """Extract attributes from ConnectionMonitor if present."""
        result: dict[str, str] = {}
        connection_monitor: ConnectionMonitor | None = (
            self._smartcocoon.connection_monitor
            if hasattr(self._smartcocoon, "connection_monitor")
            else None
        )
        if not connection_monitor:
            return result
        state = connection_monitor.get_device_status(self._fan_id)
        if not state:
            return result
        lc = state.get("last_connected")
        ld = state.get("last_disconnected")
        if lc is not None:
            result["last_connected"] = (
                lc.isoformat() if hasattr(lc, "isoformat") else str(lc)
            )
        if ld is not None:
            result["last_disconnected"] = (
                ld.isoformat() if hasattr(ld, "isoformat") else str(ld)
            )
        return result

    @property
    def is_connected(self) -> bool:
        """Return whether the mock bridge is connected."""
        return self._get_fan_data().connected  # type: ignore[no-any-return]

    @property
    def is_on(self) -> bool:
        """Return true if the fan is on."""
        return self._get_fan_data().fan_on  # type: ignore[no-any-return]

    @property
    def fan_id(self) -> str:
        """Return the physical ID of the fan."""
        return self._fan_id

    @property
    def name(self) -> str:
        """Get entity name."""
        fan_data = self._get_fan_data()
        return f"SmartCocoon Fan - {fan_data.room_name}:{self._fan_id}"

    @property
    def percentage(self) -> int | None:
        """Return the current speed as a percentage (0-100)."""
        fan_data = self._get_fan_data()
        speed_pct = fan_data.speed_pct
        _LOGGER.debug(
            "Fan %s: Speed percentage from pysmartcocoon: %s (type: %s)",
            self._fan_id,
            speed_pct,
            type(speed_pct),
        )
        percentage = int(speed_pct)
        _LOGGER.debug("Fan %s: Converted to percentage: %s", self._fan_id, percentage)
        return percentage

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode, e.g., auto, smart, interval, favorite."""
        fan_data = self._get_fan_data()
        return fan_data.mode  # type: ignore[no-any-return]

    @property
    def preset_modes(self) -> list[str] | None:
        """List of available preset modes."""

        if self._enable_preset_modes:
            return SC_PRESET_MODES

        return None

    @property
    def should_poll(self) -> bool:
        """No polling needed, updates come from MQTT."""
        return False

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return 100

    @property
    def supported_features(self) -> FanEntityFeature:
        """Flag supported features."""
        flags = FanEntityFeature(0)
        flags |= FanEntityFeature.SET_SPEED
        flags |= FanEntityFeature.TURN_OFF
        flags |= FanEntityFeature.TURN_ON
        if self._enable_preset_modes:
            flags |= FanEntityFeature.PRESET_MODE
        return flags

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this fan."""
        return f"{DOMAIN}_fan_{self._fan_id}".lower()

    async def async_update_fan_callback(self) -> None:
        """Update state from callback."""
        _LOGGER.debug("Fan ID: %s - Received update callback", self.fan_id)
        # Refresh attributes before writing state
        self._attr_extra_state_attributes = self._build_extra_attrs()
        self.async_write_ha_state()

    def async_write_ha_state(self) -> None:
        """Ensure attributes are refreshed and log on each state write."""
        try:
            # Check if availability changed
            was_available = getattr(self, '_last_available', None)
            is_available = self.available

            # If availability changed from True to False, trigger recovery
            if was_available is True and is_available is False:
                _LOGGER.info(
                    "Fan %s became unavailable - triggering recovery check",
                    self._fan_id,
                )
                # Trigger recovery check asynchronously
                if (
                    hasattr(self._smartcocoon, 'connection_monitor')
                    and self._smartcocoon.connection_monitor
                ):
                    self.hass.async_create_task(
                        self._smartcocoon.connection_monitor.check_fan_unavailable(
                            self._fan_id
                        )
                    )

            # Store current availability for next check
            self._last_available = is_available

            self._attr_extra_state_attributes = self._build_extra_attrs()
            _LOGGER.debug(
                "Fan %s: write_ha_state attrs: %s",
                self._fan_id,
                self._attr_extra_state_attributes,
            )
        except (AttributeError, KeyError, TypeError):
            pass
        super().async_write_ha_state()

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed of the fan, as a percentage."""
        _LOGGER.debug(
            "Fan %s: Setting percentage to %s (type: %s)",
            self._fan_id,
            percentage,
            type(percentage),
        )
        assert self._scmanager is not None  # Checked in constructor
        scmanager = self._scmanager  # Store reference to avoid mypy issues
        await self._smartcocoon.error_handler.async_retry_operation(
            operation=lambda: scmanager.async_set_fan_speed(self._fan_id, percentage),
            operation_name=f"set fan speed to {percentage}%",
            context={"fan_id": self._fan_id, "percentage": percentage},
        )
        _LOGGER.debug(
            "Fan %s: Successfully set percentage to %s", self._fan_id, percentage
        )
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        _LOGGER.debug("Fan %s: Setting preset mode to %s", self._fan_id, preset_mode)
        if preset_mode not in SC_PRESET_MODES:
            raise ValueError(
                f"{preset_mode} is not a valid preset_mode: {SC_PRESET_MODES}"
            )

        assert self._scmanager is not None  # Checked in constructor
        scmanager = self._scmanager  # Store reference to avoid mypy issues
        if preset_mode == SC_PRESET_MODE_AUTO:
            await self._smartcocoon.error_handler.async_retry_operation(
                operation=lambda: scmanager.async_set_fan_auto(self._fan_id),
                operation_name="set fan to auto mode",
                context={"fan_id": self._fan_id, "preset_mode": preset_mode},
            )
            _LOGGER.debug("Fan %s: Successfully set to auto mode", self._fan_id)
        elif preset_mode == SC_PRESET_MODE_ECO:
            await self._smartcocoon.error_handler.async_retry_operation(
                operation=lambda: scmanager.async_set_fan_eco(self._fan_id),
                operation_name="set fan to eco mode",
                context={"fan_id": self._fan_id, "preset_mode": preset_mode},
            )
            _LOGGER.debug("Fan %s: Successfully set to eco mode", self._fan_id)
        else:
            raise ValueError(f"Unsupported preset mode {preset_mode}")

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the entity."""
        _LOGGER.debug("Fan %s: Turning off", self._fan_id)
        assert self._scmanager is not None  # Checked in constructor
        scmanager = self._scmanager  # Store reference to avoid mypy issues
        await self._smartcocoon.error_handler.async_retry_operation(
            operation=lambda: scmanager.async_fan_turn_off(self._fan_id),
            operation_name="turn off fan",
            context={"fan_id": self._fan_id},
        )
        _LOGGER.debug("Fan %s: Successfully turned off", self._fan_id)
        self.async_write_ha_state()

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the entity."""
        _LOGGER.debug(
            "Fan %s: Turning on (percentage=%s, preset_mode=%s)",
            self._fan_id,
            percentage,
            preset_mode,
        )
        if preset_mode:
            await self.async_set_preset_mode(preset_mode)
            return

        if percentage is not None:
            await self.async_set_percentage(percentage)

        assert self._scmanager is not None  # Checked in constructor
        scmanager = self._scmanager  # Store reference to avoid mypy issues
        await self._smartcocoon.error_handler.async_retry_operation(
            operation=lambda: scmanager.async_fan_turn_on(self._fan_id),
            operation_name="turn on fan",
            context={"fan_id": self._fan_id},
        )
        _LOGGER.debug("Fan %s: Successfully turned on", self._fan_id)
        self.async_write_ha_state()
