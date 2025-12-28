"""The SmartCocoon integration."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientSession
from pysmartcocoon.manager import SmartCocoonManager
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .connection_monitor import ConnectionMonitor, ConnectionMonitorConfig
from .const import (
    CONF_CONNECTION_CHECK_INTERVAL,
    CONF_ENABLE_PRESET_MODES,
    CONF_MAX_OFFLINE_DURATION,
    CONF_MAX_RECOVERY_ATTEMPTS_PER_HOUR,
    CONF_RECOVERY_ATTEMPT_INTERVAL,
    CONF_RECOVERY_RESET_INTERVAL,
    DEFAULT_CONNECTION_CHECK_INTERVAL,
    DEFAULT_ENABLE_PRESET_MODES,
    DEFAULT_MAX_OFFLINE_DURATION,
    DEFAULT_MAX_RECOVERY_ATTEMPTS_PER_HOUR,
    DEFAULT_RECOVERY_ATTEMPT_INTERVAL,
    DEFAULT_RECOVERY_RESET_INTERVAL,
    DOMAIN,
)
from .error_handler import RetryConfig, SmartCocoonErrorHandler

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["fan"]


class SmartCocoonController:
    """SmartCocoon main class."""

    def __init__(  # pylint: disable=too-many-positional-arguments
        self,
        username: str,
        password: str,
        enable_preset_modes: bool,
        hass: HomeAssistant,
        max_offline_duration: int = DEFAULT_MAX_OFFLINE_DURATION,
        recovery_attempt_interval: int = DEFAULT_RECOVERY_ATTEMPT_INTERVAL,
        max_recovery_attempts_per_hour: int = DEFAULT_MAX_RECOVERY_ATTEMPTS_PER_HOUR,
        recovery_reset_interval: int = DEFAULT_RECOVERY_RESET_INTERVAL,
        connection_check_interval: int = DEFAULT_CONNECTION_CHECK_INTERVAL,
    ) -> None:
        """Initialize."""
        self._username = username
        self._password = password
        self._scmanager: SmartCocoonManager | None = None
        self._hass: HomeAssistant = hass
        self._session: ClientSession | None = None
        self._connection_monitor: ConnectionMonitor | None = None
        self._max_offline_duration = max_offline_duration
        self._recovery_attempt_interval = recovery_attempt_interval
        self._max_recovery_attempts_per_hour = max_recovery_attempts_per_hour
        self._recovery_reset_interval = recovery_reset_interval
        self._connection_check_interval = connection_check_interval

        if enable_preset_modes:
            self._enable_preset_modes = True
        else:
            self._enable_preset_modes = False

        # Initialize error handler with retry configuration
        self._error_handler = SmartCocoonErrorHandler(
            RetryConfig(
                max_attempts=3,
                base_delay=1.0,
                max_delay=30.0,
                exponential_base=2.0,
                jitter=True,
            )
        )

    @property
    def enable_preset_modes(self) -> bool:
        """Return the Enable Preset Mode flag."""
        return self._enable_preset_modes

    @property
    def scmanager(self) -> SmartCocoonManager | None:
        """Return the SmartCocoonManager object."""
        return self._scmanager

    async def async_start(self) -> bool:
        """Start the SmartCocoon Manager."""

        _LOGGER.debug("Starting SmartCocoon services")

        self._session = async_get_clientsession(self._hass)
        self._scmanager = SmartCocoonManager(self._session)

        # Use error handler for retry logic
        assert self._scmanager is not None  # Checked in constructor
        scmanager = self._scmanager  # Store reference to avoid mypy issues
        await self._error_handler.async_retry_operation(
            operation=lambda: scmanager.async_start_services(
                username=self._username, password=self._password
            ),
            operation_name="SmartCocoon service startup",
            context={"username": self._username},
        )

        _LOGGER.debug("SmartCocoon services started successfully")

        _LOGGER.debug("scmanager.locations: %s", self._scmanager.locations)
        _LOGGER.debug("scmanager.thermostats: %s", self._scmanager.thermostats)
        _LOGGER.debug("scmanager.rooms: %s", self._scmanager.rooms)
        _LOGGER.debug("scmanager.fans: %s", self._scmanager.fans)

        # Start connection monitoring
        config = ConnectionMonitorConfig(
            max_offline_duration=self._max_offline_duration
            * 3600,  # Convert hours to seconds
            recovery_attempt_interval=self._recovery_attempt_interval
            * 60,  # Convert minutes to seconds
            max_recovery_attempts_per_hour=self._max_recovery_attempts_per_hour,
            recovery_reset_interval=self._recovery_reset_interval
            * 60,  # Convert minutes to seconds
            connection_check_interval=self._connection_check_interval
            * 3600,  # Convert hours to seconds
        )

        self._connection_monitor = ConnectionMonitor(
            hass=self._hass,
            scmanager=self._scmanager,
            error_handler=self._error_handler,
            config=config,
        )
        await self._connection_monitor.start_monitoring()

        return True

    @property
    def error_handler(self) -> SmartCocoonErrorHandler:
        """Return the error handler instance."""
        return self._error_handler

    @property
    def connection_monitor(self) -> ConnectionMonitor | None:
        """Return the connection monitor instance."""
        return self._connection_monitor

    async def async_stop(self) -> None:
        """Stop the SmartCocoon Manager and cleanup resources."""
        if self._connection_monitor:
            await self._connection_monitor.stop_monitoring()
            self._connection_monitor = None
        _LOGGER.debug("SmartCocoon services stopped")


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up SmartCocoon from a config entry."""

    config_data = config_entry.data
    username = config_data[CONF_USERNAME]
    password = config_data[CONF_PASSWORD]
    config_options = config_entry.options
    enable_preset_modes = config_options.get(
        CONF_ENABLE_PRESET_MODES, DEFAULT_ENABLE_PRESET_MODES
    )
    max_offline_duration = config_options.get(
        CONF_MAX_OFFLINE_DURATION, DEFAULT_MAX_OFFLINE_DURATION
    )
    recovery_attempt_interval = config_options.get(
        CONF_RECOVERY_ATTEMPT_INTERVAL, DEFAULT_RECOVERY_ATTEMPT_INTERVAL
    )
    max_recovery_attempts_per_hour = config_options.get(
        CONF_MAX_RECOVERY_ATTEMPTS_PER_HOUR, DEFAULT_MAX_RECOVERY_ATTEMPTS_PER_HOUR
    )
    recovery_reset_interval = config_options.get(
        CONF_RECOVERY_RESET_INTERVAL, DEFAULT_RECOVERY_RESET_INTERVAL
    )
    connection_check_interval = config_options.get(
        CONF_CONNECTION_CHECK_INTERVAL, DEFAULT_CONNECTION_CHECK_INTERVAL
    )

    smartcocoon = SmartCocoonController(
        username=username,
        password=password,
        enable_preset_modes=enable_preset_modes,
        hass=hass,
        max_offline_duration=max_offline_duration,
        recovery_attempt_interval=recovery_attempt_interval,
        max_recovery_attempts_per_hour=max_recovery_attempts_per_hour,
        recovery_reset_interval=recovery_reset_interval,
        connection_check_interval=connection_check_interval,
    )

    await smartcocoon.async_start()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = smartcocoon

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    # Register services
    await _async_register_services(hass, smartcocoon)

    config_entry.async_on_unload(config_entry.add_update_listener(async_update_options))

    return True


async def _async_register_services(
    hass: HomeAssistant, smartcocoon: SmartCocoonController
) -> None:
    """Register SmartCocoon services."""

    async def async_force_recovery(
        call: Any,  # pylint: disable=unused-argument
    ) -> None:
        """Force a recovery check for all devices or one entity if provided."""
        if smartcocoon.connection_monitor:
            entity_id: str | None = call.data.get("entity_id")
            fan_id: str | None = None

            if entity_id:
                # Map entity_id to fan_id via entity registry unique_id
                try:
                    entity_registry = er.async_get(hass)
                    entry = entity_registry.async_get(entity_id)
                    if entry and entry.platform == DOMAIN and entry.domain == "fan":
                        # unique_id contains the fan identifier
                        fan_id = str(entry.unique_id).rsplit("_", maxsplit=1)[-1]
                except (AttributeError, ValueError, TypeError):
                    fan_id = None

            await smartcocoon.connection_monitor.force_recovery_check(fan_id)
            _LOGGER.info(
                "Forced recovery check completed%s",
                f" for {entity_id}" if entity_id else "",
            )
        else:
            _LOGGER.warning("Connection monitor not available")

    async def async_get_device_status(
        call: Any,  # pylint: disable=unused-argument
    ) -> None:
        """Get device status for all devices or one entity if provided."""
        if smartcocoon.connection_monitor:
            entity_id: str | None = call.data.get("entity_id")
            if entity_id:
                try:
                    entity_registry = er.async_get(hass)
                    entry = entity_registry.async_get(entity_id)
                    if entry and entry.platform == DOMAIN and entry.domain == "fan":
                        fan_id = str(entry.unique_id).rsplit("_", maxsplit=1)[-1]
                        status = smartcocoon.connection_monitor.get_device_status(
                            fan_id
                        )
                        _LOGGER.info("Device status for %s: %s", entity_id, status)
                        return
                except (AttributeError, ValueError, TypeError):
                    pass

            status = smartcocoon.connection_monitor.get_all_device_status()
            _LOGGER.info("Device status: %s", status)
        else:
            _LOGGER.warning("Connection monitor not available")

    # Register services
    hass.services.async_register(
        DOMAIN,
        "force_recovery",
        async_force_recovery,
        schema=vol.Schema({vol.Optional("entity_id"): str}),
    )

    hass.services.async_register(
        DOMAIN,
        "get_device_status",
        async_get_device_status,
        schema=vol.Schema({vol.Optional("entity_id"): str}),
    )


async def async_update_options(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok: bool = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )

    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok
