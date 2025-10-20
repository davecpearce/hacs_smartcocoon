"""Models for the SmartCocoon integration."""

from __future__ import annotations

from typing import TypedDict


class FanExtraAttributes(TypedDict, total=False):
    """TypedDict for climates extra attributes."""

    room_name: str
    fan_id: str
    firmware_version: str
    connected: bool
    fan_on: bool
    mode: str
    last_connected: str
    last_disconnected: str
    predicted_room_temperature: float
    is_room_estimating: bool
    thermostat_vendor: str
    power: int | bool
    room_id: str
    identifier: str
