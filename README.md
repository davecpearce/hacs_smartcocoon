# SmartCocoon Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![pre-commit][pre-commit-shield]][pre-commit]
[![Black][black-shield]][black]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

![logo](logo.png)

**Disclaimer**
This is not an official integration from or supported by the SmartCocoon

**Introduction**
This a _custom component_ for [Home Assistant](https://www.home-assistant.io/). It enables control of SmartCocoon Smart Vent / Register Booster Fans [SmartCocoon](https://mysmartcocoon.com/).

This integration will create one device and one fan entity for each of your fans.

**Notes:**

You have the option to include the 'auto' and 'eco' preset modes for your fan. The settings for the 'auto' mode will need to be made through the official SmartCocoon app. Preset modes work well in Home Assistant but render poorly in Apple Home fan entities. These modes are disabled by default, you may prefer to manage automations within Home Assistant and/or Node Red.

At this time, if you control your fan from the SmartCocoon app, Home Assistant will not receive these updates.

## Installation

This Integration can be installed in two ways:

**HACS Installation**

Add the following to the Custom Repository under `Settings` in HACS:

`davecpearce/hacs_smartcocoon` and choose `Integration` as the Category

**Manual Installation**

1. Use Git to clone the repo to a local directory by entering <br/>`git clone https://github.com/davecpearce/hacs_smartcocoon.git`
1. If you do not already have a `custom_components` directory in your Home Assistant config directory, create it.
1. Copy or move the `smartcocoon` folder from `hacs_smartcocoon/custom_components` you cloned from step 1 to the `custom_components` folder in your Home Assistant `config` folder.

## Track Updates

If installed via HACS, updates are flagged automatically. Otherwise, you will have to manually update as described in the manual installation steps above.

## Configuration

There is a config flow for this integration. After installing the custom component:

1. Go to **Configuration**->**Integrations**
2. Click **+ ADD INTEGRATION** to setup a new integration
3. Search for **SmartCocoon** and click on it
4. You will be guided through the rest of the setup process via the config flow
   - You will have to provide the same 'username' and 'password' you use when logging into the official SmartCocoon iOS or Android application.
5. You have the option to select the Area of each detected fan.
6. After the installation completes, you will see a "Configure" button for the SmartCocoon integration where you have the option to "Enable Preset Modes"

<!---->

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## Credits

This project was generated from [@oncleben31](https://github.com/oncleben31)'s [Home Assistant Custom Component Cookiecutter](https://github.com/oncleben31/cookiecutter-homeassistant-custom-component) template.

Code template was mainly taken from [@Ludeeus](https://github.com/ludeeus)'s [integration_blueprint][integration_blueprint] template

---

[black]: https://github.com/psf/black
[black-shield]: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
[buymecoffee]: https://www.buymeacoffee.com/davepearce
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/davecpearce/hacs_smartcocoon.svg?style=for-the-badge
[commits]: https://github.com/davecpearce/hacs_smartcocoon/commits/main
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/davecpearce/hacs_smartcocoon.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40davecpearce-blue.svg?style=for-the-badge
[pre-commit]: https://github.com/pre-commit/pre-commit
[pre-commit-shield]: https://img.shields.io/badge/pre--commit-enabled-brightgreen?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/davecpearce/hacs_smartcocoon.svg?style=for-the-badge
[releases]: https://github.com/davecpearce/hacs_smartcocoon/releases
[user_profile]: https://github.com/davecpearce
