# SmartCocoon Automations & Blueprints

This integration gives you a `fan.*` entity per SmartCocoon booster fan. That's the
raw building block — this guide turns it into useful control, from one-line recipes to
a full self-regulating room-climate blueprint.

Everything here uses only standard Home Assistant entities (a `climate` thermostat and a
temperature `sensor`), so it should work with **any** climate integration. It was
developed and tested against **Ecobee** — see
[Compatibility](#compatibility--read-this-first) for the one hard requirement.

It progresses from simplest to most capable:

1. [How the fan behaves in Home Assistant](#how-the-fan-behaves-in-home-assistant)
2. [Building blocks](#building-blocks) — a speed sensor and a fan group
3. [Simple recipes](#simple-recipes) — no blueprint required
4. [Advanced: the Room Climate Boost blueprint](#advanced-the-room-climate-boost-blueprint)
5. [Caveats](#caveats)

---

## How the fan behaves in Home Assistant

A few properties of the fan entity drive everything below:

- **`fan.set_percentage` is the reliable lever.** Speed is a percentage. The entity
  reports `speed_count: 100`, so Home Assistant treats it as **continuous 0–100** and
  the hardware rounds to its nearest physical step. There are no fixed "canonical"
  speeds to hit — pick whatever percentages read well for your rooms; they're just
  tunable defaults.
- **Preset modes (`auto` / `eco`) are optional** and configured in the SmartCocoon app.
  They're disabled by default and render poorly in Apple Home. For Home-Assistant-driven
  automation, prefer percentage control and leave presets off (see the README notes).
- **The integration does not see app-side changes.** If you also drive a fan from the
  SmartCocoon app, Home Assistant won't know. The cleanest automations treat Home
  Assistant as the **sole writer** of a fan's speed — otherwise HA and the app fight.

The current speed is exposed as the `percentage` attribute of the fan entity.

### Speed & noise — why automate at all

SmartCocoon booster fans trade airflow for noise, and that trade-off is the whole
reason to automate rather than pick one fixed speed. A rough, anecdotal guide (trust
your own ears / a dB meter over these numbers):

- **8–16%** — a low, near-silent baseline. Prefer this to fully **OFF**: a powered-but-idle
  booster fan sitting in a vent can restrict airflow more than the bare register, so a
  quiet baseline that keeps air moving is usually better than off.
- **~60%** — clearly audible but tolerable; many people accept it running, some even
  overnight.
- **100%** — **LOUD.** Excellent for fast recovery when a room is far off target, but not
  something you want running continuously or while you sleep.

Automating lets you live in the quiet baseline almost always, step up to ~60% when a
room drifts, and only hit 100% for short, justified boosts — with **night caps** so a
boost can't blast a bedroom awake.

### You need a room temperature sensor

Everything here is driven by **room** temperature vs. the thermostat setpoint, so an
accurate per-room sensor is what makes it effective — without one the automations have
nothing meaningful to act on. Good sources:

- **Thermostat remote sensors** — Ecobee room sensors, Nest temperature sensors, etc.,
  exposed as `sensor.*` in Home Assistant.
- **Standalone sensors** — any Zigbee / Z-Wave / Wi-Fi temperature sensor
  (`device_class: temperature`).

**Can you use the SmartCocoon fan's own reading?** Not directly. This integration
registers **only a `fan` entity — there is no dedicated SmartCocoon temperature
`sensor`.** The fan does carry a `predicted_room_temperature` _attribute_, but (a) it's a
SmartCocoon _estimate_ (see the `is_room_estimating` attribute), not a direct
measurement, (b) it isn't always present, and (c) being an attribute rather than a
`sensor` entity, you can't pick it in the blueprint's sensor selector. If you have
nothing better, you _can_ wrap it in a template sensor — but a real sensor is strongly
preferred:

```yaml
# configuration.yaml — last-resort room sensor from the fan's estimate
template:
  - sensor:
      - name: "Bedroom Room Temp (SmartCocoon estimate)"
        unit_of_measurement: "°C"
        device_class: temperature
        state: "{{ state_attr('fan.bedroom', 'predicted_room_temperature') | float(0) }}"
        availability: "{{ state_attr('fan.bedroom', 'predicted_room_temperature') is not none }}"
```

---

## Building blocks

### A numeric speed sensor (for graphing / conditions)

The speed lives on the fan as an _attribute_, which you can't graph directly. Expose it
as a numeric sensor with a template:

```yaml
# configuration.yaml
template:
  - sensor:
      - name: "Bedroom Fan Speed"
        unit_of_measurement: "%"
        state: "{{ state_attr('fan.bedroom', 'percentage') | int(0) }}"
```

### A fan group (control all vents at once)

Group your booster fans into one entity so recipes can act on every vent together:

```yaml
# configuration.yaml
fan:
  - platform: group
    name: All Vents
    entities:
      - fan.bedroom
      - fan.office
      - fan.living_room
```

You now have `fan.all_vents` for whole-house on/off.

---

## Simple recipes

These are standalone automations — no blueprint needed. They assume a `climate` entity
(e.g. `climate.thermostat`) and a room temperature `sensor.*`.

### Boost a room when it's hot vs. the setpoint

Turn the fan up when the room runs warmer than the cool setpoint, and back to a quiet
baseline when it recovers. This is an on/off _pair_ so it re-commands in both directions:

```yaml
automation:
  - alias: "Bedroom fan – boost when hot"
    trigger:
      - platform: state
        entity_id: sensor.bedroom_temperature
    condition:
      - condition: template
        value_template: >-
          {{ (states('sensor.bedroom_temperature') | float(0))
             - (state_attr('climate.thermostat', 'temperature') | float(99)) >= 1.0 }}
    action:
      - service: fan.set_percentage
        target:
          entity_id: fan.bedroom
        data:
          percentage: 100

  - alias: "Bedroom fan – back to quiet when recovered"
    trigger:
      - platform: state
        entity_id: sensor.bedroom_temperature
    condition:
      - condition: template
        value_template: >-
          {{ (states('sensor.bedroom_temperature') | float(0))
             - (state_attr('climate.thermostat', 'temperature') | float(99)) < 0.3 }}
    action:
      - service: fan.set_percentage
        target:
          entity_id: fan.bedroom
        data:
          percentage: 8
```

### Quiet overnight

Cap a bedroom fan to a whisper during sleeping hours:

```yaml
automation:
  - alias: "Bedroom fan – quiet at night"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: fan.set_percentage
        target:
          entity_id: fan.bedroom
        data:
          percentage: 8
```

### All vents off when away, on when home

```yaml
automation:
  - alias: "Vents off when away"
    trigger:
      - platform: state
        entity_id: input_boolean.away
        to: "on"
    action:
      - service: fan.turn_off
        target:
          entity_id: fan.all_vents

  - alias: "Vents on when home"
    trigger:
      - platform: state
        entity_id: input_boolean.away
        to: "off"
    action:
      - service: fan.set_percentage
        target:
          entity_id: fan.all_vents
        data:
          percentage: 8
```

---

## Advanced: the Room Climate Boost blueprint

For a room that should **self-regulate**, this repo ships a blueprint at
[`blueprints/automation/smartcocoon/room_climate_boost.yaml`](../blueprints/automation/smartcocoon/room_climate_boost.yaml).
Instantiate it once per room; each instance is the sole writer for that room's fan.

### Compatibility — read this first

The blueprint is generic to the `climate` domain. It uses only standard attributes:
`hvac_action`, `temperature`, `target_temp_high` / `target_temp_low`, and (for the
equalizer) `current_temperature`. It handles both single-setpoint (`cool` / `heat`) and
dual-setpoint (`heat_cool` / `auto`) thermostats.

**The one hard requirement: your thermostat must report `hvac_action`.** Some climate
integrations only report the _mode_ (`cool`/`heat`/`off`) and never the live _action_
(`cooling`/`heating`/`fan`/`idle`). Without `hvac_action` the blueprint can't tell "AC
is actively cooling" from "AC is on but idle," and the tier logic won't work. It was
developed and tested against Ecobee.

### What it does — the speed tiers

The blueprint works **symmetrically for cooling and heating** — a register booster pulls
warm supply air into a cold room in winter just as it pulls cool air into a hot room in
summer. "Demand" is how far the room is on the wrong side of the active setpoint:
`room − cool_setpoint` while cooling, `heat_setpoint − room` while heating (positive =
escalate). Each direction has its own on/off toggle (**Manage during cooling** /
**Manage during heating**, both on by default).

Every trigger, the blueprint computes a target speed and only re-commands the fan when
the current speed is more than one step (>4%) off. From highest priority down:

| Situation                                                    | Speed                                                  |
| ------------------------------------------------------------ | ------------------------------------------------------ |
| **Force-MAX** helper ON                                      | `100` (overrides everything, incl. a manually-off fan) |
| Actively **heating/cooling** and demand ≥ boost threshold    | `boost_speed` (default 100)                            |
| **Fan-only** (blower on, no active demand) and demand ≥ thr. | `circulate_speed` (default 60)                         |
| Actively **heating/cooling**, within threshold, daytime      | `assist_speed` (default 17)                            |
| **HVAC-off equalizer** (see below)                           | 100 / 60 / 33 by \|room − house\| delta                |
| Otherwise (idle / within range / night-suppressed)           | `baseline_speed` (default 8)                           |

### The HVAC-off equalizer

When the central blower is circulating with **no active heating/cooling demand** and
you're home, there's no setpoint to chase — so instead the fan equalizes the room toward
the _house's_ current temperature (the thermostat's `current_temperature`, or a reference
sensor you choose), **in either direction**. Tiers on `|room − house|`:

- `≥ 2.0 °C` → `100%`
- `≥ 1.0 °C` → `60%`
- `≥ 0.5 °C` → `33%`
- else → baseline

It can only move house-temperature air (it can't push a room _past_ the house temp — no
cooling below it in summer, no warming above it in winter), and it respects the away flag
and night suppression. Turn it off per room with **Enable HVAC-off equalizer**.

### Importing the blueprint

[![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fdavecpearce%2Fhacs_smartcocoon%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fsmartcocoon%2Froom_climate_boost.yaml)

Or manually: **Settings → Automations & Scenes → Blueprints → Import Blueprint**, and
paste:

```
https://github.com/davecpearce/hacs_smartcocoon/blob/main/blueprints/automation/smartcocoon/room_climate_boost.yaml
```

> Blueprints bundled inside an integration repo are **not** auto-distributed by HACS —
> import via the badge/URL above.

### Per-room setup — examples

Create one automation per room from the blueprint. Only `thermostat`, `room_sensor`, and
`booster_fan` are required; everything else has a sensible default. Both directions are
managed by default — set `enable_cooling` / `enable_heating` to `false` to opt a room out
of one.

**Bedroom — both directions, night caps on (default):**

```yaml
use_blueprint:
  path: smartcocoon/room_climate_boost.yaml
  input:
    thermostat: climate.thermostat
    room_sensor: sensor.bedroom_temperature
    booster_fan: fan.bedroom
    night_max_speed: 8 # never louder than a whisper overnight
    enable_night_suppression: true
```

**Office — runs full tiers 24/7, but quieter ceiling:**

```yaml
use_blueprint:
  path: smartcocoon/room_climate_boost.yaml
  input:
    thermostat: climate.thermostat
    room_sensor: sensor.office_temperature
    booster_fan: fan.office
    enable_night_suppression: false # you work/game late — keep assist/circulate active
    max_speed: 60 # full speed is too loud in here
```

**Cold back bedroom — heating only:**

```yaml
use_blueprint:
  path: smartcocoon/room_climate_boost.yaml
  input:
    thermostat: climate.thermostat
    room_sensor: sensor.back_bedroom_temperature
    booster_fan: fan.back_bedroom
    enable_cooling: false # this room only ever runs cold — boost on heating
    enable_heating: true
```

### Companion helpers (optional)

- **Whole-house MAX switch** — create an `input_boolean` (e.g.
  `input_boolean.vent_fans_max`) and point every room's **Force-MAX boolean** input at
  it. Flip it on to blast every fan to 100%. The blueprint responds **instantly on both
  edges** (dedicated template triggers), so a dashboard toggle, voice intent, or scene
  blasts immediately and reclaims control the moment it's turned off.
- **Speed floor / pre-cool ramp** — create an `input_number` (0–100) and set it as each
  room's **External speed floor**. An external automation (e.g. a sunrise pre-cool) can
  raise the floor without fighting the blueprint — the blueprint stays the sole writer and
  can still go higher. Sketch:

  ```yaml
  automation:
    - alias: "Sunrise pre-cool ramp"
      trigger:
        - platform: sun
          event: sunrise
      action:
        - service: input_number.set_value
          target:
            entity_id: input_number.vent_speed_floor
          data:
            value: 40
    - alias: "Clear pre-cool ramp mid-morning"
      trigger:
        - platform: time
          at: "09:00:00"
      action:
        - service: input_number.set_value
          target:
            entity_id: input_number.vent_speed_floor
          data:
            value: 0
  ```

- **Standalone instant-MAX (no blueprint needed)** — if you _aren't_ using the blueprint
  but still want a "blast all vents" switch, a small automation on a [fan group](#a-fan-group-control-all-vents-at-once)
  does it:

  ```yaml
  automation:
    - alias: "Vent fans — instant MAX"
      trigger:
        - platform: state
          entity_id: input_boolean.vent_fans_max
          to: "on"
      action:
        - service: fan.set_percentage
          target:
            entity_id: fan.all_vents
          data:
            percentage: 100
  ```

  With the blueprint, you don't need this — its Force-MAX input already gives instant MAX
  on both edges. Standalone, note the OFF edge: this recipe only sets 100 on the ON edge,
  so add a matching `to: "off"` trigger that restores your normal speed if you want the
  fans to drop back automatically.

---

## Caveats

- **Be the sole writer.** The integration doesn't see app-side changes, so let one
  automation own each fan's speed. Mixing the app and HA causes them to fight.
- **The external speed floor isn't a trigger.** An optional input can't be a state-trigger
  entity_id (an unset one would make the blueprint fail to load), so a change to the speed
  floor is picked up on the next re-evaluation — a room/thermostat state change or the
  periodic tick — **within ~10 minutes**. (The Force-MAX boolean is exempt: it gets
  dedicated template triggers, so it responds instantly.) If you need an instant floor
  change, drive the fan directly for that one action.
- **Night caps.** With night suppression on, the assist/circulate/equalize tiers collapse
  to baseline overnight; only an active heating/cooling boost may exceed baseline. Set
  `night_max_speed` low to prevent a nighttime boost from waking a bedroom.
