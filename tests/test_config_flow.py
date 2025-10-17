"""Test config flow for SmartCocoon integration."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from pysmartcocoon.errors import UnauthorizedError
import voluptuous as vol

from homeassistant import config_entries
from custom_components.smartcocoon import config_flow
from custom_components.smartcocoon.const import (
    CONF_ENABLE_PRESET_MODES,
    DEFAULT_ENABLE_PRESET_MODES,
    DOMAIN,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .const import MOCK_USER_INPUT


async def test_flow_user_form(hass: HomeAssistant) -> None:
    """Test that the user step works."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expected = {
        "data_schema": vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        ),
        "errors": {},
        "flow_id": result["flow_id"],
        "handler": DOMAIN,
        "last_step": None,
        "step_id": "user",
        "type": FlowResultType.FORM,
    }

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert "data_schema" in result


async def test_flow_user_success(hass: HomeAssistant) -> None:
    """Test successful user flow."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.smartcocoon.config_flow.validate_input",
        return_value={"title": "test@example.com"},
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_INPUT
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "test@example.com"
    assert result["data"] == MOCK_USER_INPUT


async def test_flow_invalid_auth(hass: HomeAssistant) -> None:
    """Test flow with invalid authentication."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.smartcocoon.config_flow.validate_input",
        side_effect=config_flow.InvalidAuth,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_INPUT
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_auth"


async def test_flow_cannot_connect(hass: HomeAssistant) -> None:
    """Test flow with connection error."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.smartcocoon.config_flow.validate_input",
        side_effect=config_flow.CannotConnect,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_INPUT
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"


async def test_flow_unknown_error(hass: HomeAssistant) -> None:
    """Test flow with unknown error."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.smartcocoon.config_flow.validate_input",
        side_effect=Exception,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_INPUT
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "unknown"


async def test_flow_duplicate_entry(hass: HomeAssistant) -> None:
    """Test flow with duplicate entry."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.smartcocoon.config_flow.validate_input",
        return_value={"title": "test@example.com"},
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_INPUT
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY

    # Try to create another entry with same username
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.smartcocoon.config_flow.validate_input",
        return_value={"title": "test@example.com"},
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_INPUT
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_validate_input_success(hass: HomeAssistant) -> None:
    """Test validate_input success."""
    with patch(
        "homeassistant.components.smartcocoon.config_flow.SmartCocoonManager"
    ) as mock_manager:
        mock_manager.return_value.async_start_services = AsyncMock(return_value=True)
        
        result = await config_flow.validate_input(hass, MOCK_USER_INPUT)
        
        assert result == {"title": "test@example.com"}


async def test_validate_input_failure(hass: HomeAssistant) -> None:
    """Test validate_input failure."""
    with patch(
        "homeassistant.components.smartcocoon.config_flow.SmartCocoonManager"
    ) as mock_manager:
        mock_manager.return_value.async_start_services = AsyncMock(return_value=False)
        
        with pytest.raises(config_flow.InvalidAuth):
            await config_flow.validate_input(hass, MOCK_USER_INPUT)


async def test_options_flow_init(hass: HomeAssistant) -> None:
    """Test options flow initialization."""
    config_entry = config_entries.ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="test@example.com",
        data=MOCK_USER_INPUT,
        source=config_entries.SOURCE_USER,
        options={},
    )
    
    options_flow = config_flow.OptionsFlowHandler(config_entry)
    result = await options_flow.async_step_init()
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"
    assert "data_schema" in result


async def test_options_flow_submit(hass: HomeAssistant) -> None:
    """Test options flow submission."""
    config_entry = config_entries.ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="test@example.com",
        data=MOCK_USER_INPUT,
        source=config_entries.SOURCE_USER,
        options={},
    )
    
    options_flow = config_flow.OptionsFlowHandler(config_entry)
    user_input = {CONF_ENABLE_PRESET_MODES: True}
    result = await options_flow.async_step_init(user_input=user_input)
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == user_input
