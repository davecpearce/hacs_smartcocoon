"""Test constants and mock data for SmartCocoon integration tests."""

from __future__ import annotations

# Mock user input for testing
MOCK_USER_INPUT = {
    "username": "test@example.com",
    "password": "password",
}

# Mock fan data for testing
MOCK_FAN_DATA = {
    "fan_1": {
        "room_name": "Living Room",
        "connected": True,
        "fan_on": True,
        "power": 75,
        "mode": "auto",
        "firmware_version": "1.0.0",
    },
    "fan_2": {
        "room_name": "Bedroom",
        "connected": False,
        "fan_on": False,
        "power": 0,
        "mode": "eco",
        "firmware_version": "1.1.0",
    },
}

# Mock SmartCocoon manager data
MOCK_SCMANAGER_DATA = {
    "locations": {"loc1": "Location 1", "loc2": "Location 2"},
    "thermostats": {"thermo1": "Thermostat 1"},
    "rooms": {"room1": "Room 1", "room2": "Room 2"},
    "fans": MOCK_FAN_DATA,
}

# Mock config entry options
MOCK_OPTIONS = {
    "enable_preset_modes": True,
}

# Mock config entry data with options
MOCK_CONFIG_ENTRY_DATA = {
    **MOCK_USER_INPUT,
    "options": MOCK_OPTIONS,
}
