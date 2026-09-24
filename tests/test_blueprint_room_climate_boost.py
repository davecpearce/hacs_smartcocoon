"""Characterization tests for the Room Climate Boost blueprint.

These lock in the blueprint's behavior as an executable spec. Each scenario
instantiates the real blueprint as an automation (HA core's blueprint test
pattern), drives entity states, and asserts the ``fan.set_percentage`` the
automation commands (or that it stays silent).

Almost every case is the same shape -- set the world, fire a trigger, assert the
commanded speed -- so they are expressed as one data-driven, parametrized test
over ``_SCENARIOS`` rather than ~30 near-identical functions.

The blueprint is YAML, so it does not move the ``custom_components`` coverage
number -- these tests gate correctness, not coverage.
"""

from __future__ import annotations

import pathlib
import shutil
from typing import Any

from freezegun.api import FrozenDateTimeFactory
import pytest

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.setup import async_setup_component

BLUEPRINT_SRC = (
    pathlib.Path(__file__).parents[1]
    / "blueprints/automation/smartcocoon/room_climate_boost.yaml"
)
BLUEPRINT_REL = "smartcocoon/room_climate_boost.yaml"

THERMOSTAT = "climate.t"
ROOM = "sensor.room"
FAN = "fan.test"

DEFAULT_INPUTS = {
    "thermostat": THERMOSTAT,
    "room_sensor": ROOM,
    "booster_fan": FAN,
}

# A future date (real "today" is 2026-08-xx) so freezing never moves the HA
# scheduler backwards. Day hour = 12 (outside 22:00-08:00), night hour = 23.
_DAY = "2026-09-15 12:00:00"
_NIGHT = "2026-09-15 23:00:00"


def _install_blueprint(hass: HomeAssistant) -> None:
    dest = pathlib.Path(
        hass.config.path("blueprints/automation/smartcocoon/room_climate_boost.yaml")
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(BLUEPRINT_SRC, dest)


async def _setup(hass: HomeAssistant, inputs: dict[str, Any] | None = None) -> None:
    """Install the blueprint and instantiate it as a single automation."""
    merged = {**DEFAULT_INPUTS, **(inputs or {})}
    # Pin the clock's timezone so frozen UTC times map predictably to the
    # blueprint's day/night window (the test harness defaults to US/Pacific).
    await hass.config.async_set_time_zone("UTC")
    _install_blueprint(hass)
    assert await async_setup_component(
        hass,
        "automation",
        {"automation": {"use_blueprint": {"path": BLUEPRINT_REL, "input": merged}}},
    )
    await hass.async_block_till_done()


async def _trigger(
    hass: HomeAssistant,
    calls: list[ServiceCall],
    freezer: FrozenDateTimeFactory,
    *,
    hvac_action: str,
    room: float,
    mode: str = "cool",
    when: str = _DAY,
    temperature: float | None = None,
    target_temp_high: float | None = None,
    target_temp_low: float | None = None,
    current_temperature: float | None = None,
    fan_state: str = "on",
    fan_pct: int = 50,
    helpers: dict[str, str] | None = None,
) -> None:
    """Set the world, then change the room sensor to fire the automation."""
    freezer.move_to(when)
    for entity, state in (helpers or {}).items():
        hass.states.async_set(entity, state)

    attrs: dict[str, Any] = {"hvac_action": hvac_action}
    for key, value in (
        ("temperature", temperature),
        ("target_temp_high", target_temp_high),
        ("target_temp_low", target_temp_low),
        ("current_temperature", current_temperature),
    ):
        if value is not None:
            attrs[key] = value
    hass.states.async_set(THERMOSTAT, mode, attrs)
    hass.states.async_set(
        FAN, fan_state, {} if fan_state == "off" else {"percentage": fan_pct}
    )
    hass.states.async_set(ROOM, "-999")  # prime
    await hass.async_block_till_done()
    calls.clear()

    hass.states.async_set(ROOM, str(room))  # the asserted trigger
    await hass.async_block_till_done()


def _last_pct(calls: list[ServiceCall]) -> int:
    assert calls, "expected a fan.set_percentage call, got none"
    return int(calls[-1].data["percentage"])


async def _run_scenario(
    hass: HomeAssistant,
    calls: list[ServiceCall],
    freezer: FrozenDateTimeFactory,
    case: dict[str, Any],
) -> None:
    """Set up (with any per-case inputs), trigger, and assert the outcome.

    ``expected`` is the commanded percentage, or None to assert no command.
    """
    await _setup(hass, case.get("inputs"))
    await _trigger(hass, calls, freezer, **case["trigger"])
    expected = case["expected"]
    if expected is None:
        assert len(calls) == 0, f"expected no command, got {calls}"
    else:
        assert _last_pct(calls) == expected


# --------------------------------------------------------------------------- #
# Smoke: the blueprint is a valid, loadable blueprint.
# --------------------------------------------------------------------------- #
async def test_blueprint_instantiates(hass: HomeAssistant) -> None:
    """The blueprint loads and produces an automation entity."""
    await _setup(hass)
    automations = hass.states.async_entity_ids("automation")
    assert automations, "blueprint did not instantiate an automation"
    state = hass.states.get(automations[0])
    assert state is not None
    assert state.state != "unavailable"


# --------------------------------------------------------------------------- #
# Behavior matrix. Each case: optional setup `inputs`, the `trigger` state, and
# the `expected` commanded percentage (None = no command). Defaults: boost=100,
# circulate=60, assist=17, baseline=8, boost_threshold=1.0, release=0.3.
# --------------------------------------------------------------------------- #
_SCENARIOS = [
    # --- cooling tier ladder ---
    pytest.param(
        {
            "trigger": {
                "hvac_action": "cooling",
                "target_temp_high": 22.0,
                "room": 24.0,
            },
            "expected": 100,
        },
        id="cooling-boost",
    ),
    pytest.param(
        {
            "trigger": {
                "hvac_action": "cooling",
                "target_temp_high": 22.0,
                "room": 22.5,
            },
            "expected": 17,
        },
        id="cooling-assist-daytime",
    ),
    pytest.param(
        {
            "trigger": {"hvac_action": "fan", "target_temp_high": 22.0, "room": 24.0},
            "expected": 60,
        },
        id="fan-only-circulate-cooling",
    ),
    pytest.param(
        {
            "trigger": {"hvac_action": "idle", "target_temp_high": 22.0, "room": 20.0},
            "expected": 8,
        },
        id="baseline-when-idle",
    ),
    # --- heating tier ladder (symmetric) ---
    pytest.param(
        {
            "trigger": {
                "mode": "heat",
                "hvac_action": "heating",
                "target_temp_low": 21.0,
                "room": 19.0,
            },
            "expected": 100,
        },
        id="heating-boost",
    ),
    pytest.param(
        {
            "trigger": {
                "mode": "heat",
                "hvac_action": "heating",
                "target_temp_low": 21.0,
                "room": 20.5,
            },
            "expected": 17,
        },
        id="heating-assist-daytime",
    ),
    pytest.param(
        {
            "trigger": {
                "mode": "heat",
                "hvac_action": "fan",
                "target_temp_low": 21.0,
                "room": 19.0,
            },
            "expected": 60,
        },
        id="fan-only-circulate-heating",
    ),
    # --- HVAC-off equalizer, bidirectional (tiers on |room - house|) ---
    pytest.param(
        {
            "trigger": {
                "mode": "fan_only",
                "hvac_action": "fan",
                "current_temperature": 22.0,
                "room": 24.1,
            },
            "expected": 100,
        },
        id="equalizer-warm-2.1",
    ),
    pytest.param(
        {
            "trigger": {
                "mode": "fan_only",
                "hvac_action": "fan",
                "current_temperature": 22.0,
                "room": 23.2,
            },
            "expected": 60,
        },
        id="equalizer-warm-1.2",
    ),
    pytest.param(
        {
            "trigger": {
                "mode": "fan_only",
                "hvac_action": "fan",
                "current_temperature": 22.0,
                "room": 22.6,
            },
            "expected": 33,
        },
        id="equalizer-warm-0.6",
    ),
    pytest.param(
        {
            "trigger": {
                "mode": "fan_only",
                "hvac_action": "fan",
                "current_temperature": 22.0,
                "room": 22.2,
            },
            "expected": 8,
        },
        id="equalizer-warm-0.2",
    ),
    pytest.param(
        {
            "trigger": {
                "mode": "fan_only",
                "hvac_action": "fan",
                "current_temperature": 22.0,
                "room": 19.9,
            },
            "expected": 100,
        },
        id="equalizer-cold-2.1",
    ),
    pytest.param(
        {
            "trigger": {
                "mode": "fan_only",
                "hvac_action": "fan",
                "current_temperature": 22.0,
                "room": 20.8,
            },
            "expected": 60,
        },
        id="equalizer-cold-1.2",
    ),
    pytest.param(
        {
            "trigger": {
                "mode": "fan_only",
                "hvac_action": "fan",
                "current_temperature": 22.0,
                "room": 21.4,
            },
            "expected": 33,
        },
        id="equalizer-cold-0.6",
    ),
    pytest.param(
        {
            "trigger": {
                "mode": "fan_only",
                "hvac_action": "fan",
                "current_temperature": 22.0,
                "room": 21.8,
            },
            "expected": 8,
        },
        id="equalizer-cold-0.2",
    ),
    # --- night suppression ---
    pytest.param(
        {
            "trigger": {
                "when": _NIGHT,
                "hvac_action": "cooling",
                "target_temp_high": 22.0,
                "room": 22.5,
            },
            "expected": 8,
        },
        id="night-suppresses-cooling-assist",
    ),
    pytest.param(
        {
            "trigger": {
                "when": _NIGHT,
                "hvac_action": "fan",
                "target_temp_high": 22.0,
                "room": 24.0,
            },
            "expected": 8,
        },
        id="night-suppresses-fan-circulate",
    ),
    pytest.param(
        {
            "trigger": {
                "when": _NIGHT,
                "hvac_action": "cooling",
                "target_temp_high": 22.0,
                "room": 24.0,
            },
            "expected": 100,
        },
        id="night-still-allows-cooling-boost",
    ),
    pytest.param(
        {
            "trigger": {
                "when": _NIGHT,
                "mode": "heat",
                "hvac_action": "heating",
                "target_temp_low": 21.0,
                "room": 19.0,
            },
            "expected": 100,
        },
        id="night-still-allows-heating-boost",
    ),
    pytest.param(
        {
            "trigger": {
                "when": _NIGHT,
                "mode": "heat",
                "hvac_action": "heating",
                "target_temp_low": 21.0,
                "room": 20.5,
            },
            "expected": 8,
        },
        id="night-suppresses-heating-assist",
    ),
    # --- caps and floor ---
    pytest.param(
        {
            "inputs": {"night_max_speed": 8},
            "trigger": {
                "when": _NIGHT,
                "hvac_action": "cooling",
                "target_temp_high": 22.0,
                "room": 24.0,
            },
            "expected": 8,
        },
        id="night-max-cap",
    ),
    pytest.param(
        {
            "inputs": {"max_speed": 60},
            "trigger": {
                "hvac_action": "cooling",
                "target_temp_high": 22.0,
                "room": 24.0,
            },
            "expected": 60,
        },
        id="max-speed-cap",
    ),
    pytest.param(
        {
            "inputs": {"speed_floor_entity": "input_number.floor"},
            "trigger": {
                "hvac_action": "idle",
                "target_temp_high": 22.0,
                "room": 20.0,
                "helpers": {"input_number.floor": "40"},
            },
            "expected": 40,
        },
        id="speed-floor",
    ),
    # --- force-max override and manual-off handling ---
    pytest.param(
        {
            "inputs": {"force_max_boolean": "input_boolean.max"},
            "trigger": {
                "hvac_action": "idle",
                "target_temp_high": 22.0,
                "room": 20.0,
                "helpers": {"input_boolean.max": "on"},
            },
            "expected": 100,
        },
        id="force-max-overrides-everything",
    ),
    pytest.param(
        {
            "trigger": {
                "hvac_action": "cooling",
                "target_temp_high": 22.0,
                "room": 24.0,
                "fan_state": "off",
            },
            "expected": None,
        },
        id="manual-off-respected",
    ),
    pytest.param(
        {
            "inputs": {"force_manage": True},
            "trigger": {
                "hvac_action": "idle",
                "target_temp_high": 22.0,
                "room": 20.0,
                "fan_state": "off",
            },
            "expected": 8,
        },
        id="force-manage-ignores-manual-off",
    ),
    # --- sticky release hysteresis ---
    pytest.param(
        {
            "trigger": {
                "hvac_action": "cooling",
                "target_temp_high": 22.0,
                "room": 22.5,
                "fan_pct": 50,
            },
            "expected": 17,
        },
        id="no-premature-boost-below-threshold",
    ),
    pytest.param(
        {
            "trigger": {
                "hvac_action": "cooling",
                "target_temp_high": 22.0,
                "room": 22.5,
                "fan_pct": 98,
            },
            "expected": None,
        },
        id="sticky-holds-high-within-band",
    ),
    pytest.param(
        {
            "trigger": {
                "hvac_action": "cooling",
                "target_temp_high": 22.0,
                "room": 22.2,
                "fan_pct": 98,
            },
            "expected": 17,
        },
        id="release-steps-down-below-release-threshold",
    ),
    # --- enable toggles gate each direction ---
    pytest.param(
        {
            "inputs": {"enable_cooling": False},
            "trigger": {
                "hvac_action": "cooling",
                "target_temp_high": 22.0,
                "room": 24.0,
            },
            "expected": 8,
        },
        id="enable-cooling-false-leaves-baseline",
    ),
    pytest.param(
        {
            "inputs": {"enable_heating": False},
            "trigger": {
                "mode": "heat",
                "hvac_action": "heating",
                "target_temp_low": 21.0,
                "room": 19.0,
            },
            "expected": 8,
        },
        id="enable-heating-false-leaves-baseline",
    ),
    # --- re-command threshold ---
    pytest.param(
        {
            "trigger": {
                "hvac_action": "cooling",
                "target_temp_high": 22.0,
                "room": 24.0,
                "fan_pct": 97,
            },
            "expected": None,
        },
        id="no-recommand-within-threshold",
    ),
]


@pytest.mark.parametrize("case", _SCENARIOS)  # type: ignore[untyped-decorator]
async def test_speed_scenario(
    hass: HomeAssistant,
    calls: list[ServiceCall],
    freezer: FrozenDateTimeFactory,
    case: dict[str, Any],
) -> None:
    """Drive the blueprint through one scenario and assert the commanded speed."""
    await _run_scenario(hass, calls, freezer, case)


# --------------------------------------------------------------------------- #
# Instant whole-house MAX hook: dedicated template triggers on the force_max
# helper fire on the toggle itself (not a room-sensor change), so these are
# separate from the scenario matrix. They also prove the unset-safe property:
# with no force_max_boolean the blueprint must still load and never fire.
# --------------------------------------------------------------------------- #
_MAX_HELPER = "input_boolean.max"


def _prime_idle(hass: HomeAssistant, fan_pct: int) -> None:
    """Idle + room below setpoint -> desired baseline (8)."""
    hass.states.async_set(
        THERMOSTAT, "cool", {"hvac_action": "idle", "target_temp_high": 22.0}
    )
    hass.states.async_set(FAN, "on", {"percentage": fan_pct})
    hass.states.async_set(ROOM, "20.0")


async def test_instant_max_on_edge(
    hass: HomeAssistant, calls: list[ServiceCall]
) -> None:
    """Turning the MAX helper ON commands 100 immediately (no room change)."""
    await _setup(hass, {"force_max_boolean": _MAX_HELPER})
    hass.states.async_set(_MAX_HELPER, "off")
    _prime_idle(hass, fan_pct=8)
    await hass.async_block_till_done()
    calls.clear()

    hass.states.async_set(_MAX_HELPER, "on")  # only change
    await hass.async_block_till_done()
    assert _last_pct(calls) == 100


async def test_instant_max_off_edge(
    hass: HomeAssistant, calls: list[ServiceCall]
) -> None:
    """Turning MAX OFF immediately reclaims the real speed (not stuck at 100)."""
    await _setup(hass, {"force_max_boolean": _MAX_HELPER})
    hass.states.async_set(_MAX_HELPER, "on")
    _prime_idle(hass, fan_pct=100)
    await hass.async_block_till_done()
    calls.clear()

    hass.states.async_set(_MAX_HELPER, "off")  # only change
    await hass.async_block_till_done()
    assert _last_pct(calls) == 8


async def test_max_hook_unset_loads_and_is_quiet(
    hass: HomeAssistant, calls: list[ServiceCall]
) -> None:
    """With force_max_boolean unset, the blueprint loads and never spuriously fires."""
    await _setup(hass)  # no force_max_boolean
    automations = hass.states.async_entity_ids("automation")
    assert automations, "blueprint failed to load when force_max_boolean is unset"
    state = hass.states.get(automations[0])
    assert state is not None
    assert state.state == "on"

    _prime_idle(hass, fan_pct=8)
    await hass.async_block_till_done()
    calls.clear()
    hass.states.async_set("input_boolean.unrelated", "on")
    await hass.async_block_till_done()
    assert len(calls) == 0
