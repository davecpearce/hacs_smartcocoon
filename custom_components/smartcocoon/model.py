"""Models for the AVM FRITZ!SmartHome integration."""
from __future__ import annotations

from typing import TypedDict


class FanExtraAttributes(TypedDict, total=False):
    """TypedDict for climates extra attributes."""

    room_name: str
