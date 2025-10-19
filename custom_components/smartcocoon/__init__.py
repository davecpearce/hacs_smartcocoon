"""The SmartCocoon integration."""

from __future__ import annotations

import logging

from aiohttp import ClientSession
from pysmartcocoon.errors import UnauthorizedError
from pysmartcocoon.manager import SmartCocoonManager

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_ENABLE_PRESET_MODES, DEFAULT_ENABLE_PRESET_MODES, DOMAIN
from .error_handler import RetryConfig, SmartCocoonErrorHandler

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["fan"]


class SmartCocoonController:
    """SmartCocoon main class."""

    def __init__(
        self,
        username: str,
        password: str,
        enable_preset_modes: bool,
        hass: HomeAssistant,
    ) -> None:
        """Initialize."""
        self._username = username
        self._password = password
        self._scmanager: SmartCocoonManager | None = None
        self._hass: HomeAssistant = hass
        self._session: ClientSession | None = None

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

        return True

    @property
    def error_handler(self) -> SmartCocoonErrorHandler:
        """Return the error handler instance."""
        return self._error_handler


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up SmartCocoon from a config entry."""

    config_data = config_entry.data
    username = config_data[CONF_USERNAME]
    password = config_data[CONF_PASSWORD]
    config_options = config_entry.options
    enable_preset_modes = config_options.get(
        CONF_ENABLE_PRESET_MODES, DEFAULT_ENABLE_PRESET_MODES
    )

    smartcocoon = SmartCocoonController(
        username,
        password,
        enable_preset_modes,
        hass,
    )

    await smartcocoon.async_start()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = smartcocoon

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    config_entry.async_on_unload(config_entry.add_update_listener(async_update_options))

    return True


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
