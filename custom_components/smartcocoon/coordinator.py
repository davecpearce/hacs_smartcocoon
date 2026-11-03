"""Polling coordinator for SmartCocoon fans."""

from __future__ import annotations

from datetime import timedelta
import logging

from pysmartcocoon.errors import UnauthorizedError
from pysmartcocoon.manager import SmartCocoonManager

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class SmartCocoonCoordinator(DataUpdateCoordinator[None]):  # type: ignore[misc]
    """Refresh every fan from the cloud on a fixed interval.

    Until this existed, fan state reached Home Assistant only when Home
    Assistant itself sent a command. The entity said "updates come from MQTT",
    but MQTT support was removed in 2024 and the update callback it registered
    is never called. So a speed changed in the app, a fan dropping offline, or
    eco mode adjusting the speed on its own never showed up -- which is
    ha-smartcocoon#421.

    MQTT cannot replace this: each fan's MQTT credentials are the fan's own
    broker identity, and connecting with them knocks the real fan offline.

    The fans themselves stay on the manager, which is what the entities read;
    the coordinator only decides when to refresh them and whether it worked.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        scmanager: SmartCocoonManager,
        config_entry: ConfigEntry | None = None,
    ) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self._scmanager = scmanager

    async def _async_update_data(self) -> None:
        """Fetch every fan in one request."""
        try:
            refreshed = await self._scmanager.async_refresh_fans()
        except UnauthorizedError as err:
            # The library has already tried a fresh login. Raising this, not
            # UpdateFailed, is what makes Home Assistant ask for a new
            # password; otherwise polling would fail quietly every minute.
            raise ConfigEntryAuthFailed(
                "SmartCocoon rejected the stored credentials"
            ) from err
        if not refreshed:
            # The fans keep their previous values; marking the update failed
            # makes the entities unavailable rather than quietly stale.
            raise UpdateFailed("Could not refresh SmartCocoon fans")
