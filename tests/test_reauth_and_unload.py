"""Reauth and clean unload, from review of hacs/default#12776.

Two gaps. SmartCocoon rejecting the stored password raised
ConfigEntryAuthFailed, but there was no reauth step to answer it, and from
commands, the recovery timer and polling nothing started one -- so the only
way to enter a new password was to delete the integration. And unloading the
entry never stopped the connection monitor, whose timers reschedule
themselves, so every options save (which reloads) left another one polling.
"""

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

from freezegun.api import FrozenDateTimeFactory
from pysmartcocoon.errors import RequestError, UnauthorizedError
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.smartcocoon import SmartCocoonController
from custom_components.smartcocoon.config_flow import (
    CannotConnect,
    InvalidAuth,
    validate_input,
)
from custom_components.smartcocoon.connection_monitor import (
    ConnectionMonitor,
    ConnectionMonitorConfig,
)
from custom_components.smartcocoon.const import DOMAIN
from custom_components.smartcocoon.coordinator import SmartCocoonCoordinator
from custom_components.smartcocoon.fan import SmartCocoonFan
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

USERNAME = "dave@example.com"
START_SERVICES = (
    "custom_components.smartcocoon.config_flow.SmartCocoonManager.async_start_services"
)


@pytest.fixture(autouse=True)  # type: ignore[untyped-decorator]
def _custom_integrations(enable_custom_integrations: None) -> None:
    """Let Home Assistant load this integration's config flow."""


def _entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=USERNAME,
        unique_id=USERNAME,
        data={CONF_USERNAME: USERNAME, CONF_PASSWORD: "old-password"},
    )
    entry.add_to_hass(hass)
    return entry


# --- validate_input ---------------------------------------------------------


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("error", "expected"),
    [(UnauthorizedError("401"), InvalidAuth), (RequestError("down"), CannotConnect)],
)
async def test_validate_input_maps_library_errors(
    hass: HomeAssistant, error: Exception, expected: type[Exception]
) -> None:
    """A rejected login is invalid_auth, not "Unexpected error"."""
    with (
        patch(START_SERVICES, AsyncMock(side_effect=error)),
        pytest.raises(expected),
    ):
        await validate_input(hass, {CONF_USERNAME: USERNAME, CONF_PASSWORD: "x"})


# --- reauth flow ------------------------------------------------------------


async def test_reauth_saves_the_new_password(hass: HomeAssistant) -> None:
    """The user enters a new password, it is checked, saved, and reloaded."""
    entry = _entry(hass)
    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    with (
        patch(START_SERVICES, AsyncMock(return_value=True)),
        patch.object(hass.config_entries, "async_schedule_reload") as reload,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PASSWORD: "new-password"}
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_PASSWORD] == "new-password"
    assert entry.data[CONF_USERNAME] == USERNAME
    # The entry reloads so the new password takes effect without a restart.
    reload.assert_called_once_with(entry.entry_id)


async def test_reauth_rejects_a_wrong_password(hass: HomeAssistant) -> None:
    """A wrong password is reported and nothing is saved."""
    entry = _entry(hass)
    result = await entry.start_reauth_flow(hass)

    with patch(START_SERVICES, AsyncMock(side_effect=UnauthorizedError("401"))):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PASSWORD: "still-wrong"}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}
    assert entry.data[CONF_PASSWORD] == "old-password"


# --- starting reauth outside setup ------------------------------------------


class _StubFan(SmartCocoonFan):
    """A fan entity whose command handler rejects the credentials."""

    def __init__(self) -> None:  # pylint: disable=super-init-not-called
        controller = MagicMock()
        controller.error_handler.async_retry_operation = AsyncMock(
            side_effect=ConfigEntryAuthFailed("rejected")
        )
        self._fan_id = "4125f4"
        self._scmanager = MagicMock()
        self._smartcocoon = controller
        self.controller = controller  # typed as a mock, for assertions


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("method", "args"),
    [("async_set_percentage", (50,)), ("async_turn_on", ()), ("async_turn_off", ())],
)
async def test_command_starts_reauth(method: str, args: tuple[object, ...]) -> None:
    """A command that hits rejected credentials asks for a new password."""
    entity = _StubFan()
    with pytest.raises(ConfigEntryAuthFailed):
        await getattr(entity, method)(*args)
    entity.controller.start_reauth.assert_called_once()


async def test_recovery_starts_reauth_instead_of_escaping(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """The recovery timer asks for a new password and stops retrying."""
    fan = SimpleNamespace(connected=False, _async_update_fan=AsyncMock())
    error_handler = MagicMock()
    error_handler.async_retry_operation = AsyncMock(
        side_effect=ConfigEntryAuthFailed("rejected")
    )
    on_auth_failed = MagicMock()
    monitor = ConnectionMonitor(
        hass=hass,
        scmanager=MagicMock(fans={"4125f4": fan}),
        error_handler=error_handler,
        config=ConnectionMonitorConfig(),
        on_auth_failed=on_auth_failed,
    )
    freezer.tick(timedelta(seconds=60))  # past the startup grace period

    with patch(
        "custom_components.smartcocoon.connection_monitor.async_call_later"
    ) as call_later:
        await monitor.force_recovery_check("4125f4")  # must not raise

    error_handler.async_retry_operation.assert_awaited_once()
    on_auth_failed.assert_called_once()
    call_later.assert_not_called()  # no futile retry scheduled


async def test_polling_starts_reauth(hass: HomeAssistant) -> None:
    """Rejected credentials during a poll ask for a new password."""
    entry = _entry(hass)
    manager = MagicMock(
        async_refresh_fans=AsyncMock(side_effect=UnauthorizedError("401"))
    )
    coordinator = SmartCocoonCoordinator(hass, manager, entry)

    with patch.object(entry, "async_start_reauth") as start_reauth:
        await coordinator.async_refresh()

    assert coordinator.last_update_success is False
    assert isinstance(coordinator.last_exception, ConfigEntryAuthFailed)
    start_reauth.assert_called_once()


def test_controller_start_reauth(hass: HomeAssistant) -> None:
    """The controller hands reauth to its config entry."""
    entry = MagicMock()
    controller = SmartCocoonController(
        username=USERNAME,
        password="x",
        enable_preset_modes=False,
        hass=hass,
        config_entry=entry,
    )
    controller.start_reauth()
    entry.async_start_reauth.assert_called_once_with(hass)


# --- unload -----------------------------------------------------------------


def _setup_patches(first_refresh: AsyncMock, stop: AsyncMock) -> list[object]:
    return [
        patch.object(
            SmartCocoonController, "async_start", AsyncMock(return_value=True)
        ),
        patch.object(SmartCocoonController, "async_stop", stop),
        patch.object(
            SmartCocoonController,
            "scmanager",
            new_callable=PropertyMock,
            return_value=MagicMock(fans={}),
        ),
        patch.object(
            SmartCocoonCoordinator, "async_config_entry_first_refresh", first_refresh
        ),
    ]


async def test_unload_stops_the_controller(hass: HomeAssistant) -> None:
    """Unloading -- which every options save does -- stops the monitor."""
    entry = _entry(hass)
    stop = AsyncMock()
    patches = _setup_patches(AsyncMock(), stop)
    for p in patches:
        p.start()  # type: ignore[attr-defined]
    try:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        stop.assert_not_awaited()

        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
    finally:
        for p in patches:
            p.stop()  # type: ignore[attr-defined]

    stop.assert_awaited_once()


async def test_failed_setup_stops_the_controller(hass: HomeAssistant) -> None:
    """A setup that fails after the monitor started must not leave it running.

    A failed first refresh means "retry later", so without this each retry
    started one more monitor.
    """
    entry = _entry(hass)
    stop = AsyncMock()
    patches = _setup_patches(AsyncMock(side_effect=ConfigEntryNotReady("down")), stop)
    for p in patches:
        p.start()  # type: ignore[attr-defined]
    try:
        assert not await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    finally:
        for p in patches:
            p.stop()  # type: ignore[attr-defined]

    stop.assert_awaited_once()
