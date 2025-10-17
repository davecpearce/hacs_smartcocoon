"""Test component setup and initialization."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pysmartcocoon.errors import UnauthorizedError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed

from custom_components.smartcocoon import SmartCocoonController, async_setup_entry, async_unload_entry
from custom_components.smartcocoon.const import (
    CONF_ENABLE_PRESET_MODES,
    DEFAULT_ENABLE_PRESET_MODES,
    DOMAIN,
)
from custom_components.smartcocoon.fan import async_setup_entry as fan_async_setup_entry

from .const import MOCK_USER_INPUT


@pytest.fixture
def mock_config_entry() -> ConfigEntry:
    """Create a mock config entry."""
    return ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="test@example.com",
        data=MOCK_USER_INPUT,
        source="user",
        options={CONF_ENABLE_PRESET_MODES: True},
    )


async def test_async_setup(hass: HomeAssistant) -> None:
    """Test the component gets setup."""
    from custom_components.smartcocoon.const import DOMAIN
    from homeassistant.setup import async_setup_component

    assert await async_setup_component(hass, DOMAIN, {}) is True


async def test_smartcocoon_controller_init(hass: HomeAssistant) -> None:
    """Test SmartCocoonController initialization."""
    controller = SmartCocoonController(
        username="test@example.com",
        password="password",
        enable_preset_modes=True,
        hass=hass,
    )
    
    assert controller._username == "test@example.com"
    assert controller._password == "password"
    assert controller._enable_preset_modes is True
    assert controller._hass == hass
    assert controller._scmanager is None
    assert controller._session is None


async def test_smartcocoon_controller_properties(hass: HomeAssistant) -> None:
    """Test SmartCocoonController properties."""
    controller = SmartCocoonController(
        username="test@example.com",
        password="password",
        enable_preset_modes=False,
        hass=hass,
    )
    
    assert controller.enable_preset_modes is False
    assert controller.scmanager is None


async def test_smartcocoon_controller_async_start_success(hass: HomeAssistant) -> None:
    """Test successful async_start."""
    controller = SmartCocoonController(
        username="test@example.com",
        password="password",
        enable_preset_modes=True,
        hass=hass,
    )
    
    mock_scmanager = MagicMock()
    mock_scmanager.async_start_services = AsyncMock(return_value=True)
    mock_scmanager.locations = {"loc1": "Location 1"}
    mock_scmanager.thermostats = {"thermo1": "Thermostat 1"}
    mock_scmanager.rooms = {"room1": "Room 1"}
    mock_scmanager.fans = {"fan1": "Fan 1"}
    
    with patch("custom_components.smartcocoon.SmartCocoonManager", return_value=mock_scmanager):
        result = await controller.async_start()
        
        assert result is True
        assert controller._scmanager == mock_scmanager
        assert controller._session is not None


async def test_smartcocoon_controller_async_start_unauthorized(hass: HomeAssistant) -> None:
    """Test async_start with unauthorized error."""
    controller = SmartCocoonController(
        username="test@example.com",
        password="password",
        enable_preset_modes=True,
        hass=hass,
    )
    
    mock_scmanager = MagicMock()
    mock_scmanager.async_start_services = AsyncMock(side_effect=UnauthorizedError("Invalid credentials"))
    
    with patch("custom_components.smartcocoon.SmartCocoonManager", return_value=mock_scmanager):
        with pytest.raises(ConfigEntryAuthFailed):
            await controller.async_start()


async def test_async_setup_entry_success(hass: HomeAssistant, mock_config_entry: ConfigEntry) -> None:
    """Test successful async_setup_entry."""
    with patch("custom_components.smartcocoon.SmartCocoonController") as mock_controller_class, \
         patch("custom_components.smartcocoon.fan.async_setup_entry") as mock_fan_setup:
        
        mock_controller = MagicMock()
        mock_controller.async_start = AsyncMock(return_value=True)
        mock_controller_class.return_value = mock_controller
        
        result = await async_setup_entry(hass, mock_config_entry)
        
        assert result is True
        assert DOMAIN in hass.data
        assert mock_config_entry.entry_id in hass.data[DOMAIN]
        mock_fan_setup.assert_called_once()


async def test_async_setup_entry_with_default_options(hass: HomeAssistant) -> None:
    """Test async_setup_entry with default options."""
    config_entry = ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="test@example.com",
        data=MOCK_USER_INPUT,
        source="user",
        options={},  # Empty options should use defaults
    )
    
    with patch("custom_components.smartcocoon.SmartCocoonController") as mock_controller_class, \
         patch("custom_components.smartcocoon.fan.async_setup_entry") as mock_fan_setup:
        
        mock_controller = MagicMock()
        mock_controller.async_start = AsyncMock(return_value=True)
        mock_controller_class.return_value = mock_controller
        
        result = await async_setup_entry(hass, config_entry)
        
        assert result is True
        # Verify controller was created with default enable_preset_modes
        mock_controller_class.assert_called_once_with(
            "test@example.com",
            "password",
            DEFAULT_ENABLE_PRESET_MODES,
            hass,
        )


async def test_async_unload_entry_success(hass: HomeAssistant, mock_config_entry: ConfigEntry) -> None:
    """Test successful async_unload_entry."""
    # Setup the entry first
    hass.data[DOMAIN] = {mock_config_entry.entry_id: MagicMock()}
    
    with patch("custom_components.smartcocoon.async_unload_platforms", return_value=True) as mock_unload:
        result = await async_unload_entry(hass, mock_config_entry)
        
        assert result is True
        mock_unload.assert_called_once_with(mock_config_entry, ["fan"])
        assert mock_config_entry.entry_id not in hass.data[DOMAIN]


async def test_async_unload_entry_failure(hass: HomeAssistant, mock_config_entry: ConfigEntry) -> None:
    """Test failed async_unload_entry."""
    # Setup the entry first
    hass.data[DOMAIN] = {mock_config_entry.entry_id: MagicMock()}
    
    with patch("custom_components.smartcocoon.async_unload_platforms", return_value=False) as mock_unload:
        result = await async_unload_entry(hass, mock_config_entry)
        
        assert result is False
        # Data should still be present if unload failed
        assert mock_config_entry.entry_id in hass.data[DOMAIN]


async def test_async_update_options(hass: HomeAssistant, mock_config_entry: ConfigEntry) -> None:
    """Test async_update_options."""
    from custom_components.smartcocoon import async_update_options
    
    with patch.object(hass.config_entries, "async_reload") as mock_reload:
        await async_update_options(hass, mock_config_entry)
        mock_reload.assert_called_once_with(mock_config_entry.entry_id)