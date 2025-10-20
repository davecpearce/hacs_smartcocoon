"""Config flow for SmartCocoon integration."""

from __future__ import annotations

import logging
from typing import Any

from pysmartcocoon.manager import SmartCocoonManager
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_CONNECTION_CHECK_INTERVAL,
    CONF_ENABLE_PRESET_MODES,
    CONF_MAX_OFFLINE_DURATION,
    CONF_MAX_RECOVERY_ATTEMPTS_PER_HOUR,
    CONF_RECOVERY_ATTEMPT_INTERVAL,
    CONF_RECOVERY_RESET_INTERVAL,
    DEFAULT_CONNECTION_CHECK_INTERVAL,
    DEFAULT_ENABLE_PRESET_MODES,
    DEFAULT_MAX_OFFLINE_DURATION,
    DEFAULT_MAX_RECOVERY_ATTEMPTS_PER_HOUR,
    DEFAULT_RECOVERY_ATTEMPT_INTERVAL,
    DEFAULT_RECOVERY_RESET_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {vol.Required(CONF_USERNAME): cv.string, vol.Required(CONF_PASSWORD): cv.string}
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    session = async_get_clientsession(hass)

    scmanager = SmartCocoonManager(session)

    if not await scmanager.async_start_services(
        data[CONF_USERNAME], data[CONF_PASSWORD]
    ):
        raise InvalidAuth

    return {"title": data[CONF_USERNAME]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[misc,call-arg]
    """Handle a config flow for SmartCocoon."""

    VERSION = 1

    @staticmethod
    @callback  # type: ignore[misc]
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return OptionsFlowHandler()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> Any:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
        self._abort_if_unique_id_configured()

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class OptionsFlowHandler(config_entries.OptionsFlow):  # type: ignore[misc]
    """Handle a option flow for SmartCocoon."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> Any:
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        enable_preset_modes = options.get(
            CONF_ENABLE_PRESET_MODES, DEFAULT_ENABLE_PRESET_MODES
        )
        max_offline_duration = options.get(
            CONF_MAX_OFFLINE_DURATION, DEFAULT_MAX_OFFLINE_DURATION
        )
        recovery_attempt_interval = options.get(
            CONF_RECOVERY_ATTEMPT_INTERVAL, DEFAULT_RECOVERY_ATTEMPT_INTERVAL
        )
        max_recovery_attempts_per_hour = options.get(
            CONF_MAX_RECOVERY_ATTEMPTS_PER_HOUR, DEFAULT_MAX_RECOVERY_ATTEMPTS_PER_HOUR
        )
        recovery_reset_interval = options.get(
            CONF_RECOVERY_RESET_INTERVAL, DEFAULT_RECOVERY_RESET_INTERVAL
        )
        connection_check_interval = options.get(
            CONF_CONNECTION_CHECK_INTERVAL, DEFAULT_CONNECTION_CHECK_INTERVAL
        )

        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_ENABLE_PRESET_MODES, default=enable_preset_modes
                ): bool,
                vol.Optional(
                    CONF_MAX_OFFLINE_DURATION,
                    default=max_offline_duration,
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=168,
                        step=1,
                        unit_of_measurement="hours",
                        mode="box",
                    )
                ),
                vol.Optional(
                    CONF_RECOVERY_ATTEMPT_INTERVAL,
                    default=recovery_attempt_interval,
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=60,
                        step=1,
                        unit_of_measurement="minutes",
                        mode="box",
                    )
                ),
                vol.Optional(
                    CONF_MAX_RECOVERY_ATTEMPTS_PER_HOUR,
                    default=max_recovery_attempts_per_hour,
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=20,
                        step=1,
                        unit_of_measurement="attempts",
                        mode="box",
                    )
                ),
                vol.Optional(
                    CONF_RECOVERY_RESET_INTERVAL,
                    default=recovery_reset_interval,
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=15,
                        max=240,
                        step=15,
                        unit_of_measurement="minutes",
                        mode="box",
                    )
                ),
                vol.Optional(
                    CONF_CONNECTION_CHECK_INTERVAL,
                    default=connection_check_interval,
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=24,
                        step=1,
                        unit_of_measurement="hours",
                        mode="box",
                    )
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)


class CannotConnect(HomeAssistantError):  # type: ignore[misc]
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):  # type: ignore[misc]
    """Error to indicate there is invalid auth."""
