"""Tests for ConnectionMonitorConfig units and time handling.

Three things are pinned here:

1. The config converts from the units the options flow collects (hours and
   minutes) to the seconds used internally, in one place.
2. Its defaults describe the shipped configuration. They previously read as
   raw seconds and made `max_offline_duration` equal `recovery_reset_interval`,
   a combination that cannot occur in production and in which the recovery
   reset is unreachable.
3. Timestamps are timezone-aware UTC, matching what Home Assistant hands to
   `async_call_later` callbacks. Mixing the two raises TypeError.
"""

# pylint: disable=protected-access
# ruff: noqa: SLF001

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

from custom_components.smartcocoon.connection_monitor import (
    ConnectionMonitor,
    ConnectionMonitorConfig,
)
from custom_components.smartcocoon.const import (
    DEFAULT_MAX_OFFLINE_DURATION,
    DEFAULT_RECOVERY_RESET_INTERVAL,
)
from custom_components.smartcocoon.error_handler import (
    RetryConfig,
    SmartCocoonErrorHandler,
)
from homeassistant.util import dt as dt_util


def test_units_are_converted_to_seconds() -> None:
    """Hours and minutes in, seconds out."""
    config = ConnectionMonitorConfig(
        max_offline_hours=2,
        recovery_attempt_minutes=3,
        recovery_reset_minutes=4,
        connection_check_hours=5,
    )

    assert config.max_offline_duration == 2 * 3600
    assert config.recovery_attempt_interval == 3 * 60
    assert config.recovery_reset_interval == 4 * 60
    assert config.connection_check_interval == 5 * 3600


def test_defaults_match_the_shipped_configuration() -> None:
    """Constructing bare must give what the integration actually runs."""
    config = ConnectionMonitorConfig()

    assert config.max_offline_duration == DEFAULT_MAX_OFFLINE_DURATION * 3600
    assert config.recovery_reset_interval == DEFAULT_RECOVERY_RESET_INTERVAL * 60


def test_reset_interval_is_shorter_than_max_offline() -> None:
    """The recovery reset must be reachable before recovery gives up.

    `_attempt_device_recovery` returns early once a fan has been offline
    longer than `max_offline_duration`, and the reset check sits after that
    return. If the two are equal -- as the old defaults made them -- the
    reset can never run, because `first_recovery_attempt` always postdates
    `last_disconnected`.
    """
    config = ConnectionMonitorConfig()

    assert config.recovery_reset_interval < config.max_offline_duration


def _monitor() -> ConnectionMonitor:
    scmanager = MagicMock()
    scmanager.fans = {}
    return ConnectionMonitor(
        hass=MagicMock(),
        scmanager=scmanager,
        error_handler=SmartCocoonErrorHandler(RetryConfig(max_attempts=1)),
        config=ConnectionMonitorConfig(),
    )


async def test_recovery_attempts_reset_after_the_interval() -> None:
    """The branch that was unreachable under the old defaults.

    A fan offline for two hours, whose first recovery attempt was 90 minutes
    ago, is past the 60 minute reset but well inside the 24 hour give-up
    window -- so the counter should be cleared and recovery continue.
    """
    monitor = _monitor()
    now = dt_util.utcnow()

    fan = MagicMock()
    fan.connected = False
    fan._async_update_fan = AsyncMock()

    state = {
        "last_connected": None,
        "last_disconnected": now - timedelta(hours=2),
        "recovery_attempts": 3,
        "first_recovery_attempt": now - timedelta(minutes=90),
        "last_recovery_attempt": now - timedelta(minutes=30),
    }

    await monitor._attempt_device_recovery("fan1", fan, state)

    # Counter was reset, then this attempt counted as the first of the period.
    assert state["recovery_attempts"] == 1
    fan._async_update_fan.assert_called_once()


async def test_recovery_stops_after_max_offline() -> None:
    """Past the give-up window, no further attempts are made."""
    monitor = _monitor()
    now = dt_util.utcnow()

    fan = MagicMock()
    fan.connected = False
    fan._async_update_fan = AsyncMock()

    state = {
        "last_connected": None,
        "last_disconnected": now - timedelta(hours=25),
        "recovery_attempts": 1,
        "first_recovery_attempt": now - timedelta(hours=25),
        "last_recovery_attempt": now - timedelta(hours=1),
    }

    await monitor._attempt_device_recovery("fan1", fan, state)

    fan._async_update_fan.assert_not_called()


def test_timestamps_are_timezone_aware() -> None:
    """Naive timestamps would raise when compared with a callback's `now`.

    Home Assistant passes an aware UTC datetime to `async_call_later`
    callbacks, so anything stored here has to be aware too.
    """
    monitor = _monitor()

    assert monitor._startup_time.tzinfo is not None
    # And subtracting a callback-style timestamp must not raise.
    assert (dt_util.utcnow() - monitor._startup_time).total_seconds() >= 0
