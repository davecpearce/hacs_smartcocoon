"""Tests that a rejected fan command surfaces as an error in Home Assistant.

The library reports whether the cloud API actually applied a change. Before
this, the integration wrote the new state and logged success either way, so a
rejected command left Home Assistant displaying a speed or mode the vent had
never adopted, with nothing for the user to act on.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.smartcocoon.fan import SmartCocoonFan
from homeassistant.exceptions import HomeAssistantError

FAN_ID = "abc123"


class _StubFan(SmartCocoonFan):
    """A fan entity wired to stubs, keeping the real command methods.

    Subclassing rather than patching a constructed entity avoids the full
    Home Assistant entity setup while leaving the code under test untouched.
    """

    # The parent __init__ needs a config entry, hass and a live manager, none
    # of which these tests want.
    def __init__(self, accepted: bool) -> None:  # pylint: disable=super-init-not-called
        scmanager = MagicMock()
        for name in (
            "async_set_fan_speed",
            "async_fan_turn_on",
            "async_fan_turn_off",
            "async_set_fan_auto",
            "async_set_fan_eco",
        ):
            setattr(scmanager, name, AsyncMock(return_value=accepted))

        controller = MagicMock()

        # The real error handler awaits the operation and returns its result.
        # A non-async lambda here would hand back an un-awaited coroutine,
        # which is truthy -- every one of these tests would pass vacuously.
        async def _run(operation: object, **_: object) -> object:
            return await operation()  # type: ignore[operator]

        controller.error_handler.async_retry_operation = AsyncMock(side_effect=_run)

        self._fan_id = FAN_ID
        self._scmanager = scmanager
        self._smartcocoon = controller
        self.state_writes = 0

    def async_write_ha_state(self) -> None:
        """Record state writes instead of touching Home Assistant."""
        self.state_writes += 1


def _fan_entity(accepted: bool) -> _StubFan:
    """Build a fan entity whose commands return `accepted`."""
    return _StubFan(accepted)


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("method", "args"),
    [
        ("async_set_percentage", (50,)),
        ("async_turn_on", ()),
        ("async_turn_off", ()),
    ],
)
async def test_rejected_command_raises(method: str, args: tuple[object, ...]) -> None:
    """A command the fan did not accept must raise, not report success."""
    entity = _fan_entity(accepted=False)

    with pytest.raises(HomeAssistantError):
        await getattr(entity, method)(*args)


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("method", "args"),
    [
        ("async_set_percentage", (50,)),
        ("async_turn_on", ()),
        ("async_turn_off", ()),
    ],
)
async def test_accepted_command_succeeds(method: str, args: tuple[object, ...]) -> None:
    """An accepted command still completes and writes state."""
    entity = _fan_entity(accepted=True)

    await getattr(entity, method)(*args)

    assert entity.state_writes > 0


async def test_rejected_command_does_not_write_state() -> None:
    """State must not be written for a change that was not applied.

    This is the point of the fix: writing state on a rejected command is
    what left the UI disagreeing with the hardware.
    """
    entity = _fan_entity(accepted=False)

    with pytest.raises(HomeAssistantError):
        await entity.async_set_percentage(50)

    assert entity.state_writes == 0


async def test_error_message_identifies_the_fan_and_action() -> None:
    """The raised error should say which fan and what was attempted."""
    entity = _fan_entity(accepted=False)

    with pytest.raises(HomeAssistantError) as excinfo:
        await entity.async_set_percentage(75)

    message = str(excinfo.value)
    assert FAN_ID in message
    assert "75" in message
