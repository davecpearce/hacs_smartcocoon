# SmartCocoon Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![pre-commit][pre-commit-shield]][pre-commit]
[![Ruff][ruff-shield]][ruff]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

![logo](logo.png)

**Disclaimer**
This is not an official integration from, or supported by, SmartCocoon.

**Introduction**
This a _custom component_ for [Home Assistant](https://www.home-assistant.io/). It enables control of SmartCocoon Smart Vent / Register Booster Fans [SmartCocoon](https://mysmartcocoon.com/).

This integration will create one device and one fan entity for each of your fans.

**Notes:**

- **Home Assistant checks every fan once a minute**, so changes made in the SmartCocoon
  app or by the fan itself show up within about 60 seconds. All fans are refreshed in
  a single request.
- **In eco and auto modes the speed shown is the speed the fan is actually running at**,
  matching the SmartCocoon app. The cloud adjusts it in steps of 1/12 (about 8%), so
  you'll see values like 17%, 25% and 33%. In always-on mode it is the speed you set.
- You have the option to include the 'auto' and 'eco' preset modes for your fan. The
  settings for the 'auto' mode will need to be made through the official SmartCocoon
  app. Preset modes work well in Home Assistant but render poorly in Apple Home fan
  entities. These modes are disabled by default, you may prefer to manage automations
  within Home Assistant and/or Node Red.
- A fan that loses its connection to the SmartCocoon cloud shows as **unavailable**.

## Installation

This Integration can be installed in two ways:

**HACS Installation**

In HACS, open the **⋮** menu (top right) → **Custom repositories**, then add:

- Repository: `davecpearce/ha-smartcocoon`
- Type: `Integration`

Then search for **SmartCocoon** in HACS and download it.

**Manual Installation**

1. Use Git to clone the repo to a local directory by entering <br/>`git clone https://github.com/davecpearce/ha-smartcocoon.git`
1. If you do not already have a `custom_components` directory in your Home Assistant config directory, create it.
1. Copy or move the `smartcocoon` folder from `ha-smartcocoon/custom_components` you cloned from step 1 to the `custom_components` folder in your Home Assistant `config` folder.

## Release notes

See the [releases page](https://github.com/davecpearce/ha-smartcocoon/releases) for
what changed in each version.

## Track Updates

If installed via HACS, updates are flagged automatically. Otherwise, you will have to manually update as described in the manual installation steps above.

## Configuration

There is a config flow for this integration. After installing the custom component:

1. Go to **Settings** → **Devices & services**
2. Click **+ ADD INTEGRATION** to set up a new integration
3. Search for **SmartCocoon** and click on it
4. You will be guided through the rest of the setup process via the config flow
   - You will have to provide the same 'username' and 'password' you use when logging into the official SmartCocoon iOS or Android application.
5. You have the option to select the Area of each detected fan.
6. After the installation completes, you will see a "Configure" button for the SmartCocoon integration where you have the option to "Enable Preset Modes" and connection monitoring options.

### Changing your password

If SmartCocoon stops accepting the saved password, for example after you change it in
the app, Home Assistant shows a **Reconfigure** prompt for SmartCocoon under
**Settings** → **Devices & services**. Enter the new password there. The integration
reloads with it; there's no need to remove and re-add it, and your entities, areas and
automations are kept.

Expired sessions are renewed automatically and never need you.

### Fan attributes

Each fan entity carries these attributes alongside its state and `percentage`:

| Attribute                                                                               | Meaning                                                  |
| --------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| `mode`                                                                                  | `auto`, `eco`, `always_on` or `always_off`               |
| `speed_level`                                                                           | The speed step the fan is running at, 1–12               |
| `connected`                                                                             | Whether the fan is connected to the SmartCocoon cloud    |
| `predicted_room_temperature`, `is_room_estimating`                                      | SmartCocoon's room temperature estimate                  |
| `room_name`, `room_id`, `fan_id`, `identifier`, `firmware_version`, `thermostat_vendor` | Descriptive details                                      |
| `last_connected`, `last_disconnected`                                                   | When the connection monitor last saw the fan come and go |

### Options

These options make recovery behavior more predictable and user friendly:

- **Enable Preset Modes**: Expose SmartCocoon preset modes (auto/eco). Default: off.
- **Max Offline Duration (hours)**: How long to keep attempting recovery. Default: 24.
- **Recovery Attempt Interval (minutes)**: Minimum delay between attempts per fan. Default: 5.
- **Max Recovery Attempts Per Hour**: Rate limit for recovery attempts per fan. Default: 5.
- **Recovery Reset Interval (minutes)**: When to reset the attempt counter. Default: 60.
- **Connection Check Interval (hours)**: How often to check cloud status for disconnected fans. Default: 1.

Notes:

- The integration adds a 30-second startup grace period before attempting any recovery to avoid noisy logs and unnecessary calls immediately after HA restarts.
- Periodic connection checks detect when fans become unavailable and trigger recovery automatically.
- Recovery attempts continue automatically until successful or max attempts are reached.
- Logs include the fan's friendly name for clarity.

### Services

Two services are provided. Both work globally or on a single fan using `entity_id`.

- `smartcocoon.force_recovery`
  - Force an immediate connection check and recovery attempt.
  - Data (optional): `{ "entity_id": "fan.bedroom" }`

- `smartcocoon.get_device_status`
  - Dump the current recovery state tracked by the integration.
  - Data (optional): `{ "entity_id": "fan.office" }`

If `entity_id` is omitted, the service operates on all fans.

### Troubleshooting

- To collect debug logs, open **Settings** → **Devices & services** → **SmartCocoon**
  → **⋮** → **Enable debug logging**, reproduce the problem, then choose **Disable
  debug logging** to download the log. Passwords, tokens and your address are masked,
  but read the log before attaching it to an issue. See the
  [library's debug guide](https://github.com/davecpearce/pysmartcocoon/blob/main/docs/DEBUG_GUIDE.md)
  for more.
- If a fan is unplugged and later plugged back in, the integration will attempt recovery automatically according to the options above.
- To accelerate testing, temporarily lower the intervals in Options (e.g., 1 minute for checks/attempts) and restart Home Assistant.
- Use the `smartcocoon.force_recovery` service to trigger an immediate recovery cycle.

<!---->

## Automations & Blueprints

Out of the box the integration gives you a `fan.*` entity per fan. The
[**Automations & Blueprints cookbook**](docs/AUTOMATIONS.md) turns that into useful
control — from one-line recipes (boost a hot or cold room, quiet overnight, all vents off
when away) up to a full self-regulating **Room Climate Boost** blueprint that drives a
room's booster fan off your thermostat's `hvac_action` and a room temperature sensor,
symmetrically for **cooling and heating**.

Import the blueprint (works with any `climate` entity that reports `hvac_action`;
developed and tested against Ecobee):

[![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint pre-filled.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fdavecpearce%2Fha-smartcocoon%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fsmartcocoon%2Froom_climate_boost.yaml)

See [`docs/AUTOMATIONS.md`](docs/AUTOMATIONS.md) for the full walkthrough.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## Credits

This project was generated from [@oncleben31](https://github.com/oncleben31)'s [Home Assistant Custom Component Cookiecutter](https://github.com/oncleben31/cookiecutter-homeassistant-custom-component) template.

Code template was mainly taken from [@Ludeeus](https://github.com/ludeeus)'s [integration_blueprint][integration_blueprint] template

---

[buymecoffee]: https://www.buymeacoffee.com/davepearce
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/davecpearce/ha-smartcocoon.svg?style=for-the-badge
[commits]: https://github.com/davecpearce/ha-smartcocoon/commits/main
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/davecpearce/ha-smartcocoon.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40davecpearce-blue.svg?style=for-the-badge
[pre-commit]: https://github.com/pre-commit/pre-commit
[pre-commit-shield]: https://img.shields.io/badge/pre--commit-enabled-brightgreen?style=for-the-badge
[releases-shield]: https://img.shields.io/github/v/release/davecpearce/ha-smartcocoon.svg?style=for-the-badge
[releases]: https://github.com/davecpearce/ha-smartcocoon/releases
[ruff]: https://github.com/astral-sh/ruff
[ruff-shield]: https://img.shields.io/badge/code%20style-ruff-261230.svg?style=for-the-badge
[user_profile]: https://github.com/davecpearce
