"""Pytest configuration and fixtures for SmartCocoon integration tests."""

import pytest

from homeassistant.core import HomeAssistant


@pytest.fixture  # type: ignore[misc]
def _hass(hass: HomeAssistant) -> HomeAssistant:
    """Alias for hass fixture to avoid unused argument warnings."""
    return hass
