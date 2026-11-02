"""Tests for polling: the coordinator, and what the fan entity shows from it.

Fan state used to reach Home Assistant only when Home Assistant sent a
command; nothing else ever refreshed it. These cover the replacement: a
coordinator that refreshes every fan on an interval, and an entity that
shows the speed the fan is actually running at.
"""

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.smartcocoon.coordinator import SmartCocoonCoordinator
from custom_components.smartcocoon.fan import SmartCocoonFan
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

FAN_ID = "4125f4"


def _fan_data(**overrides: Any) -> SimpleNamespace:
    """Fan state as the library exposes it after a refresh."""
    values: dict[str, Any] = {
        "room_name": "Office",
        "mode": "eco",
        "speed_level": 2,
        "speed_pct": 38,
        "connected": True,
        "fan_on": True,
        "firmware_version": "20409",
        "predicted_room_temperature": 21.0,
        "is_room_estimating": False,
        "thermostat_vendor": "ecobee",
        "room_id": 51328,
        "identifier": 129140,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class _StubFan(SmartCocoonFan):
    """A fan entity over stub data, keeping the real properties.

    Subclassing avoids the full entity setup while leaving the code under
    test untouched.
    """

    # The parent __init__ needs hass, a config entry and a live manager.
    def __init__(  # pylint: disable=super-init-not-called
        self, fan_data: SimpleNamespace, last_update_success: bool = True
    ) -> None:
        self._fan_id = FAN_ID
        self._scmanager = MagicMock(fans={FAN_ID: fan_data})
        self._smartcocoon = MagicMock(connection_monitor=None)
        self.coordinator = MagicMock(last_update_success=last_update_success)


# --- coordinator ------------------------------------------------------------


async def test_coordinator_succeeds_when_refresh_works(hass: HomeAssistant) -> None:
    """A good refresh leaves the entities available."""
    manager = MagicMock(async_refresh_fans=AsyncMock(return_value=True))
    coordinator = SmartCocoonCoordinator(hass, manager)

    await coordinator.async_refresh()

    manager.async_refresh_fans.assert_awaited_once()
    assert coordinator.last_update_success is True


async def test_coordinator_fails_when_refresh_fails(hass: HomeAssistant) -> None:
    """A failed refresh must be reported, not silently leave stale data."""
    manager = MagicMock(async_refresh_fans=AsyncMock(return_value=False))
    coordinator = SmartCocoonCoordinator(hass, manager)

    await coordinator.async_refresh()

    assert coordinator.last_update_success is False
    assert isinstance(coordinator.last_exception, UpdateFailed)


async def test_coordinator_polls_on_an_interval(hass: HomeAssistant) -> None:
    """It refreshes on its own, not only when a command is sent."""
    coordinator = SmartCocoonCoordinator(hass, MagicMock())
    assert coordinator.update_interval is not None
    assert coordinator.update_interval.total_seconds() == 60


# --- percentage -------------------------------------------------------------


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("mode", "speed_level", "speed_pct", "expected"),
    [
        # #421: the app showed 17% (level 2 of 12) while HA showed power's 38%.
        ("eco", 2, 38, 17),
        ("auto", 12, 33, 100),
        ("auto", 6, 33, 50),
        # Always-on: power is the speed that was set, so it stays.
        ("always_on", 1, 15, 15),
        ("always_off", 1, 15, 15),
        # No level reported: fall back to power rather than show nothing.
        ("eco", None, 38, 38),
    ],
)
def test_percentage(mode: str, speed_level: Any, speed_pct: int, expected: int) -> None:
    """Shows the speed the fan runs at in the modes where the cloud picks it."""
    entity = _StubFan(
        _fan_data(mode=mode, speed_level=speed_level, speed_pct=speed_pct)
    )
    assert entity.percentage == expected


# --- availability -----------------------------------------------------------


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("last_update_success", "connected", "expected"),
    [
        (True, True, True),
        # A failed poll means `connected` may be stale.
        (False, True, False),
        (True, False, False),
    ],
)
def test_available(last_update_success: bool, connected: bool, expected: bool) -> None:
    """Available only if the last poll worked and the fan is connected."""
    entity = _StubFan(_fan_data(connected=connected), last_update_success)
    assert entity.available is expected


# --- attributes -------------------------------------------------------------


def test_attributes_previously_dropped_are_present() -> None:
    """Values the library supplies as numbers used to vanish silently."""
    attrs = _StubFan(_fan_data()).extra_state_attributes
    assert attrs["predicted_room_temperature"] == 21.0
    assert attrs["room_id"] == "51328"
    assert attrs["identifier"] == "129140"
    assert attrs["speed_level"] == 2
