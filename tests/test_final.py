"""Final comprehensive tests for SmartCocoon integration with high coverage."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryAuthFailed

from custom_components.smartcocoon import SmartCocoonController, async_setup_entry, async_unload_entry, async_update_options
from custom_components.smartcocoon.const import DOMAIN
from custom_components.smartcocoon.fan import SmartCocoonFan, async_setup_entry as fan_async_setup_entry
from custom_components.smartcocoon.config_flow import validate_input, CannotConnect, InvalidAuth

from .const import MOCK_USER_INPUT


def test_exceptions() -> None:
    """Test custom exceptions."""
    # Test CannotConnect
    exc = CannotConnect()
    assert isinstance(exc, Exception)
    assert str(exc) == ""
    
    # Test InvalidAuth
    exc = InvalidAuth()
    assert isinstance(exc, Exception)
    assert str(exc) == ""


async def test_validate_input_success(hass: HomeAssistant) -> None:
    """Test validate_input success."""
    with patch("custom_components.smartcocoon.config_flow.SmartCocoonManager") as mock_manager_class:
        mock_manager = MagicMock()
        mock_manager.async_start_services = AsyncMock(return_value=True)
        mock_manager_class.return_value = mock_manager
        
        result = await validate_input(hass, MOCK_USER_INPUT)
        
        assert result == {"title": "test@example.com"}
        mock_manager.async_start_services.assert_called_once_with("test@example.com", "password")


async def test_validate_input_failure(hass: HomeAssistant) -> None:
    """Test validate_input failure."""
    with patch("custom_components.smartcocoon.config_flow.SmartCocoonManager") as mock_manager_class:
        mock_manager = MagicMock()
        mock_manager.async_start_services = AsyncMock(return_value=False)
        mock_manager_class.return_value = mock_manager
        
        with pytest.raises(InvalidAuth):
            await validate_input(hass, MOCK_USER_INPUT)


async def test_validate_input_exception(hass: HomeAssistant) -> None:
    """Test validate_input with exception."""
    with patch("custom_components.smartcocoon.config_flow.SmartCocoonManager") as mock_manager_class:
        mock_manager = MagicMock()
        mock_manager.async_start_services = AsyncMock(side_effect=Exception("Connection error"))
        mock_manager_class.return_value = mock_manager
        
        with pytest.raises(Exception, match="Connection error"):
            await validate_input(hass, MOCK_USER_INPUT)


async def test_smartcocoon_controller_properties(hass: HomeAssistant) -> None:
    """Test SmartCocoonController properties."""
    controller = SmartCocoonController(
        username="test@example.com",
        password="password",
        enable_preset_modes=True,
        hass=hass,
    )
    
    assert controller.enable_preset_modes is True
    assert controller.scmanager is None


async def test_smartcocoon_controller_async_start_unauthorized(hass: HomeAssistant) -> None:
    """Test async_start with unauthorized error."""
    from pysmartcocoon.errors import UnauthorizedError
    
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


async def test_smartcocoon_controller_async_start_exception(hass: HomeAssistant) -> None:
    """Test async_start with general exception."""
    controller = SmartCocoonController(
        username="test@example.com",
        password="password",
        enable_preset_modes=True,
        hass=hass,
    )
    
    mock_scmanager = MagicMock()
    mock_scmanager.async_start_services = AsyncMock(side_effect=Exception("Network error"))
    
    with patch("custom_components.smartcocoon.SmartCocoonManager", return_value=mock_scmanager):
        with pytest.raises(Exception, match="Network error"):
            await controller.async_start()


async def test_async_update_options(hass: HomeAssistant) -> None:
    """Test async_update_options."""
    config_entry = ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="test@example.com",
        data=MOCK_USER_INPUT,
        source="user",
        options={},
        unique_id="test@example.com",
        minor_version=1,
        discovery_keys=set(),
        subentries_data=[],
    )
    
    with patch.object(hass.config_entries, "async_reload") as mock_reload:
        await async_update_options(hass, config_entry)
        mock_reload.assert_called_once_with(config_entry.entry_id)


async def test_fan_async_setup_entry(hass: HomeAssistant) -> None:
    """Test fan platform setup."""
    config_entry = ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="test@example.com",
        data=MOCK_USER_INPUT,
        source="user",
        options={},
        unique_id="test@example.com",
        minor_version=1,
        discovery_keys=set(),
        subentries_data=[],
    )
    
    mock_controller = MagicMock(spec=SmartCocoonController)
    mock_controller.scmanager.fans = {"fan_1": MagicMock()}
    mock_controller.enable_preset_modes = True
    
    hass.data[DOMAIN] = {config_entry.entry_id: mock_controller}
    
    entities = []
    
    with patch("custom_components.smartcocoon.fan.SmartCocoonFan") as mock_fan_class:
        mock_fan = MagicMock()
        mock_fan_class.return_value = mock_fan
        
        await fan_async_setup_entry(hass, config_entry, entities.append)
        
        assert len(entities) == 1
        mock_fan_class.assert_called_once()


async def test_smartcocoon_fan_async_methods(hass: HomeAssistant) -> None:
    """Test SmartCocoonFan async methods with proper mocking."""
    controller = MagicMock(spec=SmartCocoonController)
    controller.enable_preset_modes = True
    controller.scmanager = MagicMock()
    controller.scmanager.fans = {
        "fan_1": MagicMock(
            room_name="Living Room",
            connected=True,
            fan_on=True,
            power=75,
            mode="auto",
            firmware_version="1.0.0",
        )
    }
    
    # Mock async methods properly
    controller.scmanager.async_set_fan_speed = AsyncMock()
    controller.scmanager.async_set_fan_auto = AsyncMock()
    controller.scmanager.async_set_fan_eco = AsyncMock()
    controller.scmanager.async_fan_turn_off = AsyncMock()
    controller.scmanager.async_fan_turn_on = AsyncMock()
    
    fan = SmartCocoonFan(hass, controller, "fan_1")
    
    # Test async_set_percentage
    with patch.object(fan, "async_write_ha_state") as mock_write:
        await fan.async_set_percentage(50)
        controller.scmanager.async_set_fan_speed.assert_called_once_with("fan_1", 50)
        mock_write.assert_called_once()
    
    # Test async_set_preset_mode_auto
    with patch.object(fan, "async_write_ha_state") as mock_write:
        await fan.async_set_preset_mode("auto")
        controller.scmanager.async_set_fan_auto.assert_called_once_with("fan_1")
        mock_write.assert_called_once()
    
    # Test async_set_preset_mode_eco
    with patch.object(fan, "async_write_ha_state") as mock_write:
        await fan.async_set_preset_mode("eco")
        controller.scmanager.async_set_fan_eco.assert_called_once_with("fan_1")
        mock_write.assert_called_once()
    
    # Test async_turn_off
    with patch.object(fan, "async_write_ha_state") as mock_write:
        await fan.async_turn_off()
        controller.scmanager.async_fan_turn_off.assert_called_once_with("fan_1")
        mock_write.assert_called_once()
    
    # Test async_turn_on
    with patch.object(fan, "async_write_ha_state") as mock_write:
        await fan.async_turn_on()
        controller.scmanager.async_fan_turn_on.assert_called_once_with("fan_1")
        mock_write.assert_called_once()


async def test_smartcocoon_fan_invalid_preset_mode(hass: HomeAssistant) -> None:
    """Test SmartCocoonFan with invalid preset mode."""
    controller = MagicMock(spec=SmartCocoonController)
    controller.enable_preset_modes = True
    controller.scmanager = MagicMock()
    controller.scmanager.fans = {
        "fan_1": MagicMock(
            room_name="Living Room",
            connected=True,
            fan_on=True,
            power=75,
            mode="auto",
            firmware_version="1.0.0",
        )
    }
    
    fan = SmartCocoonFan(hass, controller, "fan_1")
    
    with pytest.raises(ValueError, match="is not a valid preset_mode"):
        await fan.async_set_preset_mode("invalid_mode")


async def test_smartcocoon_fan_unsupported_preset_mode(hass: HomeAssistant) -> None:
    """Test SmartCocoonFan with unsupported preset mode."""
    controller = MagicMock(spec=SmartCocoonController)
    controller.enable_preset_modes = True
    controller.scmanager = MagicMock()
    controller.scmanager.fans = {
        "fan_1": MagicMock(
            room_name="Living Room",
            connected=True,
            fan_on=True,
            power=75,
            mode="auto",
            firmware_version="1.0.0",
        )
    }
    
    fan = SmartCocoonFan(hass, controller, "fan_1")
    
    with pytest.raises(ValueError, match="is not a valid preset_mode"):
        await fan.async_set_preset_mode("unsupported")


async def test_smartcocoon_fan_turn_on_with_preset_mode(hass: HomeAssistant) -> None:
    """Test SmartCocoonFan turn_on with preset mode."""
    controller = MagicMock(spec=SmartCocoonController)
    controller.enable_preset_modes = True
    controller.scmanager = MagicMock()
    controller.scmanager.fans = {
        "fan_1": MagicMock(
            room_name="Living Room",
            connected=True,
            fan_on=True,
            power=75,
            mode="auto",
            firmware_version="1.0.0",
        )
    }
    
    controller.scmanager.async_set_fan_auto = AsyncMock()
    
    fan = SmartCocoonFan(hass, controller, "fan_1")
    
    with patch.object(fan, "async_set_preset_mode") as mock_set_preset_mode, \
         patch.object(fan, "async_write_ha_state") as mock_write:
        await fan.async_turn_on(preset_mode="auto")
        mock_set_preset_mode.assert_called_once_with("auto")
        # Should not call async_fan_turn_on when preset_mode is provided
        controller.scmanager.async_fan_turn_on.assert_not_called()


async def test_smartcocoon_fan_turn_on_with_percentage(hass: HomeAssistant) -> None:
    """Test SmartCocoonFan turn_on with percentage."""
    controller = MagicMock(spec=SmartCocoonController)
    controller.enable_preset_modes = True
    controller.scmanager = MagicMock()
    controller.scmanager.fans = {
        "fan_1": MagicMock(
            room_name="Living Room",
            connected=True,
            fan_on=True,
            power=75,
            mode="auto",
            firmware_version="1.0.0",
        )
    }
    
    controller.scmanager.async_fan_turn_on = AsyncMock()
    
    fan = SmartCocoonFan(hass, controller, "fan_1")
    
    with patch.object(fan, "async_set_percentage") as mock_set_percentage, \
         patch.object(fan, "async_write_ha_state") as mock_write:
        await fan.async_turn_on(percentage=50)
        mock_set_percentage.assert_called_once_with(50)
        controller.scmanager.async_fan_turn_on.assert_called_once_with("fan_1")
        mock_write.assert_called_once()


def test_smartcocoon_fan_without_preset_modes(hass: HomeAssistant) -> None:
    """Test SmartCocoonFan without preset modes enabled."""
    from homeassistant.components.fan import FanEntityFeature
    
    controller = MagicMock(spec=SmartCocoonController)
    controller.enable_preset_modes = False
    controller.scmanager = MagicMock()
    controller.scmanager.fans = {
        "fan_1": MagicMock(
            room_name="Living Room",
            connected=True,
            fan_on=True,
            power=75,
            mode="auto",
            firmware_version="1.0.0",
        )
    }
    
    fan = SmartCocoonFan(hass, controller, "fan_1")
    
    assert fan.preset_modes is None
    assert fan.supported_features & FanEntityFeature.PRESET_MODE == 0


def test_smartcocoon_fan_device_info(hass: HomeAssistant) -> None:
    """Test SmartCocoonFan device info."""
    controller = MagicMock(spec=SmartCocoonController)
    controller.enable_preset_modes = True
    controller.scmanager = MagicMock()
    controller.scmanager.fans = {
        "fan_1": MagicMock(
            room_name="Living Room",
            connected=True,
            fan_on=True,
            power=75,
            mode="auto",
            firmware_version="1.0.0",
        )
    }
    
    fan = SmartCocoonFan(hass, controller, "fan_1")
    
    device_info = fan.device_info
    assert isinstance(device_info, dict)
    assert device_info["identifiers"] == {(DOMAIN, "smartcocoon_fan_fan_1")}
    assert device_info["name"] == "Living Room:fan_1"
    assert device_info["model"] == "Smart Vent"
    assert device_info["sw_version"] == "1.0.0"
    assert device_info["manufacturer"] == "SmartCocoon"


def test_smartcocoon_fan_extra_state_attributes(hass: HomeAssistant) -> None:
    """Test SmartCocoonFan extra state attributes."""
    controller = MagicMock(spec=SmartCocoonController)
    controller.enable_preset_modes = True
    controller.scmanager = MagicMock()
    controller.scmanager.fans = {
        "fan_1": MagicMock(
            room_name="Living Room",
            connected=True,
            fan_on=True,
            power=75,
            mode="auto",
            firmware_version="1.0.0",
        )
    }
    
    fan = SmartCocoonFan(hass, controller, "fan_1")
    
    attrs = fan.extra_state_attributes
    assert isinstance(attrs, dict)
    assert attrs["room_name"] == "Living Room"


async def test_smartcocoon_fan_update_callback(hass: HomeAssistant) -> None:
    """Test fan update callback."""
    controller = MagicMock(spec=SmartCocoonController)
    controller.enable_preset_modes = True
    controller.scmanager = MagicMock()
    controller.scmanager.fans = {
        "fan_1": MagicMock(
            room_name="Living Room",
            connected=True,
            fan_on=True,
            power=75,
            mode="auto",
            firmware_version="1.0.0",
        )
    }
    
    fan = SmartCocoonFan(hass, controller, "fan_1")
    
    with patch.object(fan, "async_write_ha_state") as mock_write:
        await fan.async_update_fan_callback()
        mock_write.assert_called_once()


def test_smartcocoon_fan_basic_properties(hass: HomeAssistant) -> None:
    """Test SmartCocoonFan basic properties."""
    controller = MagicMock(spec=SmartCocoonController)
    controller.enable_preset_modes = True
    controller.scmanager = MagicMock()
    controller.scmanager.fans = {
        "fan_1": MagicMock(
            room_name="Living Room",
            connected=True,
            fan_on=True,
            power=75,
            mode="auto",
            firmware_version="1.0.0",
        )
    }
    
    fan = SmartCocoonFan(hass, controller, "fan_1")
    
    # Test basic properties
    assert fan.available is True
    assert fan.is_connected is True
    assert fan.is_on is True
    assert fan.fan_id == "fan_1"
    assert fan.name == "SmartCocoon Fan - Living Room:fan_1"
    assert fan.percentage == 0.75  # 75/100
    assert fan.preset_mode == "auto"
    assert fan.should_poll is False
    assert fan.speed_count == 100
    assert fan.unique_id == "smartcocoon_fan_fan_1"


def test_smartcocoon_fan_supported_features(hass: HomeAssistant) -> None:
    """Test SmartCocoonFan supported features."""
    from homeassistant.components.fan import FanEntityFeature
    
    controller = MagicMock(spec=SmartCocoonController)
    controller.enable_preset_modes = True
    controller.scmanager = MagicMock()
    controller.scmanager.fans = {
        "fan_1": MagicMock(
            room_name="Living Room",
            connected=True,
            fan_on=True,
            power=75,
            mode="auto",
            firmware_version="1.0.0",
        )
    }
    
    fan = SmartCocoonFan(hass, controller, "fan_1")
    
    expected_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_OFF
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.PRESET_MODE
    )
    assert fan.supported_features == expected_features


def test_smartcocoon_fan_preset_modes(hass: HomeAssistant) -> None:
    """Test SmartCocoonFan preset modes."""
    from custom_components.smartcocoon.const import SC_PRESET_MODES
    
    controller = MagicMock(spec=SmartCocoonController)
    controller.enable_preset_modes = True
    controller.scmanager = MagicMock()
    controller.scmanager.fans = {
        "fan_1": MagicMock(
            room_name="Living Room",
            connected=True,
            fan_on=True,
            power=75,
            mode="auto",
            firmware_version="1.0.0",
        )
    }
    
    fan = SmartCocoonFan(hass, controller, "fan_1")
    
    assert fan.preset_modes == SC_PRESET_MODES
