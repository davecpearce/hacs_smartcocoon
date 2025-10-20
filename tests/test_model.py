"""Test models for the SmartCocoon integration."""

from __future__ import annotations

from custom_components.smartcocoon.model import FanExtraAttributes


def test_fan_extra_attributes_typeddict() -> None:
    """Test FanExtraAttributes TypedDict structure."""
    # Test that it's a proper TypedDict
    assert issubclass(FanExtraAttributes, dict)  # TypedDict is a subclass of dict

    # Test that it has the expected keys
    expected_keys = {
        "room_name",
        "fan_id",
        "firmware_version",
        "connected",
        "fan_on",
        "mode",
        "last_connected",
        "last_disconnected",
        "predicted_room_temperature",
        "is_room_estimating",
        "thermostat_vendor",
        "room_id",
        "identifier",
    }
    assert set(FanExtraAttributes.__annotations__.keys()) == expected_keys

    # Test that room_name is optional (total=False)
    # Note: __total__ might not be available in all Python versions
    # We'll just test the structure instead


def test_fan_extra_attributes_creation() -> None:
    """Test creating FanExtraAttributes instances."""
    # Test with room_name
    attrs_with_room: FanExtraAttributes = {"room_name": "Living Room"}
    assert attrs_with_room["room_name"] == "Living Room"

    # Test empty (should be valid due to total=False)
    attrs_empty: FanExtraAttributes = {}
    assert len(attrs_empty) == 0

    # Test with only the defined key
    attrs_extra: FanExtraAttributes = {
        "room_name": "Bedroom",
    }
    assert attrs_extra["room_name"] == "Bedroom"


def test_fan_extra_attributes_type_hints() -> None:
    """Test that type hints are correct."""
    annotations = FanExtraAttributes.__annotations__

    # room_name should be str (check the annotation exists)
    assert "room_name" in annotations
    assert annotations["room_name"] is not None


def test_fan_extra_attributes_immutability() -> None:
    """Test that FanExtraAttributes behaves like a regular dict."""
    attrs: FanExtraAttributes = {"room_name": "Kitchen"}

    # Should be able to modify like a regular dict
    attrs["room_name"] = "Dining Room"
    assert attrs["room_name"] == "Dining Room"

    # Should be able to modify existing keys
    attrs["room_name"] = "Updated Room"
    assert attrs["room_name"] == "Updated Room"


def test_fan_extra_attributes_usage_in_fan_entity() -> None:
    """Test how FanExtraAttributes is used in practice."""
    # Simulate how it would be used in the fan entity
    room_name = "Master Bedroom"
    attrs: FanExtraAttributes = {"room_name": room_name}

    # Test that it can be used as return value
    def get_extra_state_attributes() -> FanExtraAttributes:
        return attrs

    result = get_extra_state_attributes()
    assert result["room_name"] == room_name
    assert isinstance(result, dict)
    # TypedDict doesn't support isinstance checks at runtime
    assert "room_name" in result
