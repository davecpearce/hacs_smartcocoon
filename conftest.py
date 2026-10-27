"""Pytest configuration and fixtures for SmartCocoon integration tests."""

from typing import cast

import pytest
from pytest_homeassistant_custom_component.common import async_mock_service

from homeassistant.core import HomeAssistant, ServiceCall


@pytest.fixture  # type: ignore[untyped-decorator]
def _hass(hass: HomeAssistant) -> HomeAssistant:
    """Alias for hass fixture to avoid unused argument warnings."""
    return hass


@pytest.fixture  # type: ignore[untyped-decorator]
def calls(hass: HomeAssistant) -> list[ServiceCall]:
    """Capture fan.set_percentage service calls (used by blueprint tests)."""
    return cast("list[ServiceCall]", async_mock_service(hass, "fan", "set_percentage"))
