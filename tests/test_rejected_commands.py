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


def _fan_entity(accepted: bool) -> SmartCocoonFan:
    """Build a fan entity whose commands return `accepted`."""
    entity = SmartCocoonFan.__new__(SmartCocoonFan)

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

    # The real error handler awaits the operation and returns its result. A
    # non-async lambda here would hand back an un-awaited coroutine, which is
    # truthy and would make every one of these tests pass vacuously.
    async def _run(operation: object, **_: object) -> object:
        return await operation()  # type: ignore[operator]

    controller.error_handler.async_retry_operation = AsyncMock(side_effect=_run)

    # Built via __new__ to avoid the full Home Assistant entity setup, so the
    # collaborators have to be injected directly.
    entity._fan_id = FAN_ID  # noqa: SLF001
    entity._scmanager = scmanager  # noqa: SLF001
    entity._smartcocoon = controller  # noqa: SLF001
    entity.async_write_ha_state = MagicMock()  # type: ignore[method-assign]
    return entity


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

    assert entity.async_write_ha_state.call_count > 0  # type: ignore[attr-defined]


async def test_rejected_command_does_not_write_state() -> None:
    """State must not be written for a change that was not applied.

    This is the point of the fix: writing state on a rejected command is
    what left the UI disagreeing with the hardware.
    """
    entity = _fan_entity(accepted=False)

    with pytest.raises(HomeAssistantError):
        await entity.async_set_percentage(50)

    assert entity.async_write_ha_state.call_count == 0  # type: ignore[attr-defined]


async def test_error_message_identifies_the_fan_and_action() -> None:
    """The raised error should say which fan and what was attempted."""
    entity = _fan_entity(accepted=False)

    with pytest.raises(HomeAssistantError) as excinfo:
        await entity.async_set_percentage(75)

    message = str(excinfo.value)
    assert FAN_ID in message
    assert "75" in message
