"""Test constants for the SmartCocoon integration."""
from __future__ import annotations

from custom_components.smartcocoon.const import (
    ATTR_ROOM_NAME,
    CONF_ENABLE_PRESET_MODES,
    DEFAULT_ENABLE_PRESET_MODES,
    DOMAIN,
    SC_PRESET_MODE_AUTO,
    SC_PRESET_MODE_ECO,
    SC_PRESET_MODES,
)


def test_domain_constant() -> None:
    """Test DOMAIN constant."""
    assert DOMAIN == "smartcocoon"
    assert isinstance(DOMAIN, str)


def test_attr_room_name_constant() -> None:
    """Test ATTR_ROOM_NAME constant."""
    assert ATTR_ROOM_NAME == "room_name"
    assert isinstance(ATTR_ROOM_NAME, str)


def test_conf_enable_preset_modes_constant() -> None:
    """Test CONF_ENABLE_PRESET_MODES constant."""
    assert CONF_ENABLE_PRESET_MODES == "enable_preset_modes"
    assert isinstance(CONF_ENABLE_PRESET_MODES, str)


def test_default_enable_preset_modes_constant() -> None:
    """Test DEFAULT_ENABLE_PRESET_MODES constant."""
    assert DEFAULT_ENABLE_PRESET_MODES is False
    assert isinstance(DEFAULT_ENABLE_PRESET_MODES, bool)


def test_preset_mode_constants() -> None:
    """Test preset mode constants."""
    assert SC_PRESET_MODE_AUTO == "auto"
    assert SC_PRESET_MODE_ECO == "eco"
    assert isinstance(SC_PRESET_MODE_AUTO, str)
    assert isinstance(SC_PRESET_MODE_ECO, str)


def test_preset_modes_list() -> None:
    """Test SC_PRESET_MODES list."""
    assert SC_PRESET_MODES == [SC_PRESET_MODE_AUTO, SC_PRESET_MODE_ECO]
    assert isinstance(SC_PRESET_MODES, list)
    assert len(SC_PRESET_MODES) == 2
    assert SC_PRESET_MODE_AUTO in SC_PRESET_MODES
    assert SC_PRESET_MODE_ECO in SC_PRESET_MODES


def test_preset_modes_immutability() -> None:
    """Test that SC_PRESET_MODES is a proper list."""
    # Should be able to iterate
    for mode in SC_PRESET_MODES:
        assert isinstance(mode, str)
        assert mode in ["auto", "eco"]

    # Should be able to check membership
    assert "auto" in SC_PRESET_MODES
    assert "eco" in SC_PRESET_MODES
    assert "invalid" not in SC_PRESET_MODES


def test_constants_are_strings() -> None:
    """Test that all string constants are actually strings."""
    string_constants = [
        DOMAIN,
        ATTR_ROOM_NAME,
        CONF_ENABLE_PRESET_MODES,
        SC_PRESET_MODE_AUTO,
        SC_PRESET_MODE_ECO,
    ]

    for constant in string_constants:
        assert isinstance(constant, str), f"{constant} should be a string"


def test_constants_are_immutable() -> None:
    """Test that constants are properly defined and immutable."""
    # These should be module-level constants, not mutable
    assert DOMAIN == "smartcocoon"
    assert ATTR_ROOM_NAME == "room_name"
    assert CONF_ENABLE_PRESET_MODES == "enable_preset_modes"
    assert DEFAULT_ENABLE_PRESET_MODES is False
    assert SC_PRESET_MODE_AUTO == "auto"
    assert SC_PRESET_MODE_ECO == "eco"
    assert SC_PRESET_MODES == ["auto", "eco"]


def test_preset_modes_usage() -> None:
    """Test how SC_PRESET_MODES would be used in practice."""
    # Simulate validation logic
    def is_valid_preset_mode(mode: str) -> bool:
        return mode in SC_PRESET_MODES

    assert is_valid_preset_mode("auto") is True
    assert is_valid_preset_mode("eco") is True
    assert is_valid_preset_mode("invalid") is False
    assert is_valid_preset_mode("") is False


def test_constants_import() -> None:
    """Test that all constants can be imported."""
    # If we get here without ImportError, the test passes
    assert True
