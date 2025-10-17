"""Test fan platform for SmartCocoon integration."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.fan import FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

from custom_components.smartcocoon import SmartCocoonController
from custom_components.smartcocoon.const import (
    ATTR_ROOM_NAME,
    DOMAIN,
    SC_PRESET_MODE_AUTO,
    SC_PRESET_MODE_ECO,
    SC_PRESET_MODES,
)
from custom_components.smartcocoon.fan import SmartCocoonFan, async_setup_entry
from custom_components.smartcocoon.model import FanExtraAttributes

from .const import MOCK_FAN_DATA, MOCK_USER_INPUT


@pytest.fixture
def mock_smartcocoon_controller(hass: HomeAssistant) -> SmartCocoonController:
    """Create a mock SmartCocoonController."""
    controller = SmartCocoonController(
        username="test@example.com",
        password="password",
        enable_preset_modes=True,
        hass=hass,
    )
    
    # Mock the scmanager
    controller._scmanager = MagicMock()
    controller._scmanager.fans = {
        "fan_1": MagicMock(
            room_name="Living Room",
            connected=True,
            fan_on=True,
            power=75,
            mode=SC_PRESET_MODE_AUTO,
            firmware_version="1.0.0",
            _async_update_fan_callback=None,
        )
    }
    
    return controller


@pytest.fixture
def mock_config_entry() -> ConfigEntry:
    """Create a mock config entry."""
    return ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="test@example.com",
        data=MOCK_USER_INPUT,
        source="user",
        options={},
    )


async def test_async_setup_entry(hass: HomeAssistant, mock_config_entry: ConfigEntry) -> None:
    """Test fan platform setup."""
    mock_controller = MagicMock(spec=SmartCocoonController)
    mock_controller.scmanager.fans = {"fan_1": MagicMock()}
    mock_controller.enable_preset_modes = True
    
    hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_controller}
    
    entities = []
    
    with patch("custom_components.smartcocoon.fan.SmartCocoonFan") as mock_fan_class:
        mock_fan = MagicMock()
        mock_fan_class.return_value = mock_fan
        
        await async_setup_entry(hass, mock_config_entry, entities.append)
        
        assert len(entities) == 1
        mock_fan_class.assert_called_once()


async def test_smartcocoon_fan_properties(
    hass: HomeAssistant, mock_smartcocoon_controller: SmartCocoonController
) -> None:
    """Test SmartCocoonFan properties."""
    fan = SmartCocoonFan(hass, mock_smartcocoon_controller, "fan_1")
    
    # Test basic properties
    assert fan.available is True
    assert fan.is_connected is True
    assert fan.is_on is True
    assert fan.fan_id == "fan_1"
    assert fan.name == "SmartCocoon Fan - Living Room:fan_1"
    assert fan.percentage == 0.75  # 75/100
    assert fan.preset_mode == SC_PRESET_MODE_AUTO
    assert fan.preset_modes == SC_PRESET_MODES
    assert fan.should_poll is False
    assert fan.speed_count == 100
    assert fan.unique_id == "smartcocoon_fan_fan_1"
    
    # Test supported features
    expected_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_OFF
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.PRESET_MODE
    )
    assert fan.supported_features == expected_features


async def test_smartcocoon_fan_device_info(
    hass: HomeAssistant, mock_smartcocoon_controller: SmartCocoonController
) -> None:
    """Test SmartCocoonFan device info."""
    fan = SmartCocoonFan(hass, mock_smartcocoon_controller, "fan_1")
    
    device_info = fan.device_info
    assert isinstance(device_info, dict)
    assert device_info["identifiers"] == {(DOMAIN, "smartcocoon_fan_fan_1")}
    assert device_info["name"] == "Living Room:fan_1"
    assert device_info["model"] == "Smart Vent"
    assert device_info["sw_version"] == "1.0.0"
    assert device_info["manufacturer"] == "SmartCocoon"


async def test_smartcocoon_fan_extra_state_attributes(
    hass: HomeAssistant, mock_smartcocoon_controller: SmartCocoonController
) -> None:
    """Test SmartCocoonFan extra state attributes."""
    fan = SmartCocoonFan(hass, mock_smartcocoon_controller, "fan_1")
    
    attrs = fan.extra_state_attributes
    assert isinstance(attrs, FanExtraAttributes)
    assert attrs[ATTR_ROOM_NAME] == "Living Room"


async def test_smartcocoon_fan_without_preset_modes(
    hass: HomeAssistant, mock_smartcocoon_controller: SmartCocoonController
) -> None:
    """Test SmartCocoonFan without preset modes enabled."""
    mock_smartcocoon_controller._enable_preset_modes = False
    fan = SmartCocoonFan(hass, mock_smartcocoon_controller, "fan_1")
    
    assert fan.preset_modes is None
    assert fan.supported_features & FanEntityFeature.PRESET_MODE == 0


async def test_async_update_fan_callback(
    hass: HomeAssistant, mock_smartcocoon_controller: SmartCocoonController
) -> None:
    """Test fan update callback."""
    fan = SmartCocoonFan(hass, mock_smartcocoon_controller, "fan_1")
    
    with patch.object(fan, "async_write_ha_state") as mock_write:
        await fan.async_update_fan_callback()
        mock_write.assert_called_once()


async def test_async_set_percentage(
    hass: HomeAssistant, mock_smartcocoon_controller: SmartCocoonController
) -> None:
    """Test setting fan percentage."""
    fan = SmartCocoonFan(hass, mock_smartcocoon_controller, "fan_1")
    
    with patch.object(fan, "async_write_ha_state") as mock_write:
        await fan.async_set_percentage(50)
        mock_smartcocoon_controller.scmanager.async_set_fan_speed.assert_called_once_with("fan_1", 50)
        mock_write.assert_called_once()


async def test_async_set_preset_mode_auto(
    hass: HomeAssistant, mock_smartcocoon_controller: SmartCocoonController
) -> None:
    """Test setting preset mode to auto."""
    fan = SmartCocoonFan(hass, mock_smartcocoon_controller, "fan_1")
    
    with patch.object(fan, "async_write_ha_state") as mock_write:
        await fan.async_set_preset_mode(SC_PRESET_MODE_AUTO)
        mock_smartcocoon_controller.scmanager.async_set_fan_auto.assert_called_once_with("fan_1")
        mock_write.assert_called_once()


async def test_async_set_preset_mode_eco(
    hass: HomeAssistant, mock_smartcocoon_controller: SmartCocoonController
) -> None:
    """Test setting preset mode to eco."""
    fan = SmartCocoonFan(hass, mock_smartcocoon_controller, "fan_1")
    
    with patch.object(fan, "async_write_ha_state") as mock_write:
        await fan.async_set_preset_mode(SC_PRESET_MODE_ECO)
        mock_smartcocoon_controller.scmanager.async_set_fan_eco.assert_called_once_with("fan_1")
        mock_write.assert_called_once()


async def test_async_set_preset_mode_invalid(
    hass: HomeAssistant, mock_smartcocoon_controller: SmartCocoonController
) -> None:
    """Test setting invalid preset mode."""
    fan = SmartCocoonFan(hass, mock_smartcocoon_controller, "fan_1")
    
    with pytest.raises(ValueError, match="invalid_mode is not a valid preset_mode"):
        await fan.async_set_preset_mode("invalid_mode")


async def test_async_turn_off(
    hass: HomeAssistant, mock_smartcocoon_controller: SmartCocoonController
) -> None:
    """Test turning off fan."""
    fan = SmartCocoonFan(hass, mock_smartcocoon_controller, "fan_1")
    
    with patch.object(fan, "async_write_ha_state") as mock_write:
        await fan.async_turn_off()
        mock_smartcocoon_controller.scmanager.async_fan_turn_off.assert_called_once_with("fan_1")
        mock_write.assert_called_once()


async def test_async_turn_on_with_percentage(
    hass: HomeAssistant, mock_smartcocoon_controller: SmartCocoonController
) -> None:
    """Test turning on fan with percentage."""
    fan = SmartCocoonFan(hass, mock_smartcocoon_controller, "fan_1")
    
    with patch.object(fan, "async_set_percentage") as mock_set_percentage, \
         patch.object(fan, "async_write_ha_state") as mock_write:
        await fan.async_turn_on(percentage=50)
        mock_set_percentage.assert_called_once_with(50)
        mock_smartcocoon_controller.scmanager.async_fan_turn_on.assert_called_once_with("fan_1")
        mock_write.assert_called_once()


async def test_async_turn_on_with_preset_mode(
    hass: HomeAssistant, mock_smartcocoon_controller: SmartCocoonController
) -> None:
    """Test turning on fan with preset mode."""
    fan = SmartCocoonFan(hass, mock_smartcocoon_controller, "fan_1")
    
    with patch.object(fan, "async_set_preset_mode") as mock_set_preset_mode, \
         patch.object(fan, "async_write_ha_state") as mock_write:
        await fan.async_turn_on(preset_mode=SC_PRESET_MODE_AUTO)
        mock_set_preset_mode.assert_called_once_with(SC_PRESET_MODE_AUTO)
        # Should not call async_fan_turn_on when preset_mode is provided
        mock_smartcocoon_controller.scmanager.async_fan_turn_on.assert_not_called()


async def test_async_turn_on_default(
    hass: HomeAssistant, mock_smartcocoon_controller: SmartCocoonController
) -> None:
    """Test turning on fan with default settings."""
    fan = SmartCocoonFan(hass, mock_smartcocoon_controller, "fan_1")
    
    with patch.object(fan, "async_write_ha_state") as mock_write:
        await fan.async_turn_on()
        mock_smartcocoon_controller.scmanager.async_fan_turn_on.assert_called_once_with("fan_1")
        mock_write.assert_called_once()
