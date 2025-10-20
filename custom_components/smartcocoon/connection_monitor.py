"""Connection monitoring and recovery for SmartCocoon devices."""

from datetime import datetime
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_call_later

from .error_handler import SmartCocoonErrorHandler

_LOGGER = logging.getLogger(__name__)


class ConnectionMonitorConfig:
    """Configuration for ConnectionMonitor."""

    def __init__(self, **kwargs: int) -> None:
        """Initialize config with keyword arguments."""
        self.max_offline_duration = kwargs.get("max_offline_duration", 3600)  # 1 hour
        self.recovery_attempt_interval = kwargs.get(
            "recovery_attempt_interval", 300
        )  # 5 minutes
        self.max_recovery_attempts_per_hour = kwargs.get(
            "max_recovery_attempts_per_hour", 5
        )  # 5 attempts
        self.recovery_reset_interval = kwargs.get(
            "recovery_reset_interval", 3600
        )  # 60 minutes
        self.connection_check_interval = kwargs.get(
            "connection_check_interval", 3600
        )  # 1 hour


class ConnectionMonitor:
    """Monitors device connections and handles recovery."""

    def __init__(
        self,
        hass: HomeAssistant,
        scmanager: Any,
        error_handler: SmartCocoonErrorHandler,
        config: ConnectionMonitorConfig,
    ) -> None:
        """Initialize the connection monitor."""
        self._hass = hass
        self._scmanager = scmanager
        self._error_handler = error_handler
        self._max_offline_duration = config.max_offline_duration
        self._recovery_attempt_interval = config.recovery_attempt_interval
        self._max_recovery_attempts_per_hour = config.max_recovery_attempts_per_hour
        self._recovery_reset_interval = config.recovery_reset_interval
        self._connection_check_interval = config.connection_check_interval

        # Track device states
        self._device_states: dict[str, dict[str, Any]] = {}
        self._last_check: datetime | None = None
        self._unsubscribe_timer: Any = None
        self._startup_time: datetime = datetime.now()
        self._grace_period_callback: Any = None
        self._recovery_callbacks: dict[str, Any] = {}
        self._periodic_check_callback: Any = None

    async def start_monitoring(self) -> None:
        """Start monitoring device connections."""
        _LOGGER.info("Starting SmartCocoon connection monitoring")

        # Initial check to establish baseline
        await self._check_connections()

        # Schedule a check after the grace period to handle fans that were down
        # at startup
        self._grace_period_callback = async_call_later(
            self._hass, 35, self._post_grace_period_check
        )

        # Schedule periodic connection checks to detect disconnections
        self._schedule_periodic_check()

    async def stop_monitoring(self) -> None:
        """Stop monitoring device connections."""
        # Cancel grace period callback if it exists
        if self._grace_period_callback:
            self._grace_period_callback()
            self._grace_period_callback = None

        # Cancel periodic check callback if it exists
        if self._periodic_check_callback:
            self._periodic_check_callback()
            self._periodic_check_callback = None

        # Cancel all recovery callbacks
        for callback in self._recovery_callbacks.values():
            if callback:
                callback()
        self._recovery_callbacks.clear()

        _LOGGER.info("Stopped SmartCocoon connection monitoring")

    async def _post_grace_period_check(self, now: datetime) -> None:
        """Check connections after the startup grace period has expired."""
        _LOGGER.debug(
            "Post-grace period check - evaluating disconnected fans for recovery"
        )
        await self._check_connections(now)

    def _schedule_periodic_check(self) -> None:
        """Schedule the next periodic connection check."""
        if self._periodic_check_callback:
            self._periodic_check_callback()
            self._periodic_check_callback = None

        self._periodic_check_callback = async_call_later(
            self._hass, self._connection_check_interval, self._periodic_connection_check
        )
        _LOGGER.debug(
            "Scheduled next connection check in %d hours",
            self._connection_check_interval // 3600,
        )

    async def _periodic_connection_check(self, now: datetime) -> None:
        """Periodic connection check to detect disconnections."""
        _LOGGER.debug("Performing periodic connection check")
        await self._check_connections(now)
        # Schedule the next check
        self._schedule_periodic_check()

    async def _check_connections(self, now: datetime | None = None) -> None:
        """Check all device connections and attempt recovery."""
        if not self._scmanager or not self._scmanager.fans:
            _LOGGER.debug(
                "No SmartCocoon manager or fans available for connection check"
            )
            return

        _LOGGER.debug(
            "Checking SmartCocoon device connections for %d fans",
            len(self._scmanager.fans),
        )
        self._last_check = now or datetime.now()

        # High-level visibility of which fans will be evaluated
        _LOGGER.debug(
            "Evaluating connection status for fans: %s",
            ", ".join(str(fid) for fid in self._scmanager.fans.keys()),
        )

        for fan_id, fan in self._scmanager.fans.items():
            _LOGGER.debug("Checking connection for fan %s", fan_id)
            await self._check_device_connection(fan_id, fan)

    async def _check_device_connection(self, fan_id: str, fan: Any) -> None:
        """Check and potentially recover a specific device connection."""
        current_time = datetime.now()
        is_connected = getattr(fan, "connected", False)

        _LOGGER.debug(
            "Fan %s connection status: %s",
            fan_id,
            "connected" if is_connected else "disconnected",
        )

        # Initialize device state if not exists
        if fan_id not in self._device_states:
            self._device_states[fan_id] = {
                "last_connected": current_time if is_connected else None,
                "last_disconnected": current_time if not is_connected else None,
                "recovery_attempts": 0,
                "last_recovery_attempt": None,
                "first_recovery_attempt": None,
            }
            _LOGGER.debug(
                "Initialized device state for fan %s (connected: %s)",
                fan_id,
                is_connected,
            )

        device_state = self._device_states[fan_id]

        if is_connected:
            # Device is connected - update state
            if not device_state["last_connected"] or device_state["last_disconnected"]:
                friendly_name = self._get_fan_friendly_name(fan_id)
                _LOGGER.info("%s is now connected", friendly_name)
                device_state["last_connected"] = current_time
                device_state["last_disconnected"] = None
                device_state["recovery_attempts"] = 0
                # Notify fan entity of connection status change
                await self._notify_fan_entity(fan_id)
        else:
            # Device is disconnected - check if we should attempt recovery
            if not device_state["last_disconnected"]:
                device_state["last_disconnected"] = current_time
                friendly_name = self._get_fan_friendly_name(fan_id)
                _LOGGER.warning("%s is now disconnected", friendly_name)
                # Notify fan entity of disconnection immediately
                await self._notify_fan_entity(fan_id)

            # Add startup grace period to avoid immediate recovery attempts on startup
            startup_grace_period = 30  # 30 seconds
            time_since_startup = (current_time - self._startup_time).total_seconds()

            if time_since_startup < startup_grace_period:
                friendly_name = self._get_fan_friendly_name(fan_id)
                _LOGGER.info(
                    (
                        "%s is disconnected but within startup grace period (%ds) "
                        "- skipping recovery"
                    ),
                    friendly_name,
                    int(time_since_startup),
                )
                return

            # Check if we should attempt recovery
            await self._attempt_device_recovery(fan_id, fan, device_state)

    def _get_fan_friendly_name(self, fan_id: str) -> str:
        """Get the friendly name for a fan from the entity registry."""
        try:
            entity_registry = er.async_get(self._hass)

            # Find the fan entity
            for entity_id, entity_entry in entity_registry.entities.items():
                if (
                    entity_entry.platform == "smartcocoon"
                    and entity_entry.domain == "fan"
                    and fan_id in entity_entry.unique_id
                ):
                    # Return the friendly name if available, otherwise the entity name
                    return str(
                        entity_entry.name
                        or entity_id.split(".")[-1].replace("_", " ").title()
                    )
        except (AttributeError, KeyError, TypeError):
            pass

        # Fallback to just the fan ID
        return f"Fan {fan_id}"

    def _is_matching_fan_entity(self, entity_entry: Any, fan_id: str) -> bool:
        """Check if entity entry matches the fan_id."""
        if not (
            entity_entry.platform == "smartcocoon" and entity_entry.domain == "fan"
        ):
            return False

        # Extract fan_id from unique_id (format: smartcocoon_fan_<fan_id>)
        unique_id_parts = str(entity_entry.unique_id).rsplit("_", maxsplit=1)
        return (
            len(unique_id_parts) == 2
            and unique_id_parts[-1].lower() == str(fan_id).lower()
        )

    async def _update_fan_entity_callback(self, fan_id: str) -> bool:
        """Update fan entity callback if found. Returns True if matched."""
        fan_component = self._hass.data.get("fan")
        if not fan_component or not hasattr(fan_component, "entities"):
            return False

        for fan_entity in fan_component.entities:
            if (
                hasattr(fan_entity, "_fan_id")
                and getattr(fan_entity, "_fan_id", None) == fan_id
            ):
                _LOGGER.debug(
                    "Calling async_update_fan_callback for fan %s",
                    fan_id,
                )
                # Use the callback to ensure full refresh
                if hasattr(fan_entity, "async_update_fan_callback"):
                    await fan_entity.async_update_fan_callback()
                elif hasattr(fan_entity, "async_write_ha_state"):
                    fan_entity.async_write_ha_state()
                return True
        return False

    async def _notify_fan_entity(self, fan_id: str) -> None:
        """Notify the fan entity to update its state."""
        try:
            # Find and notify the fan entity directly
            entity_registry = er.async_get(self._hass)

            # Find the fan entity by exact fan_id match
            for entity_id, entity_entry in entity_registry.entities.items():
                if not self._is_matching_fan_entity(entity_entry, fan_id):
                    continue

                _LOGGER.debug(
                    "Notifying fan entity %s of connection status change", entity_id
                )

                # Get the entity from the state machine
                entity = self._hass.states.get(entity_id)
                if entity and await self._update_fan_entity_callback(fan_id):
                    return

                _LOGGER.debug(
                    (
                        "No in-memory fan entity object matched _fan_id=%s for "
                        "entity %s"
                    ),
                    fan_id,
                    entity_id,
                )

            _LOGGER.debug(
                (
                    "No entity_registry entry matched fan_id=%s; availability may not "
                    "refresh"
                ),
                fan_id,
            )
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            _LOGGER.debug("Could not notify fan entity for %s: %s", fan_id, exc)

    async def _attempt_device_recovery(
        self, fan_id: str, fan: Any, device_state: dict[str, Any]
    ) -> None:
        """Attempt to recover a disconnected device."""
        current_time = datetime.now()

        # Don't attempt recovery too frequently
        if device_state["last_recovery_attempt"]:
            time_since_last_attempt = (
                current_time - device_state["last_recovery_attempt"]
            )
            if (
                time_since_last_attempt.total_seconds()
                < self._recovery_attempt_interval
            ):
                _LOGGER.debug(
                    "%s: Skipping recovery; last attempt %ds ago < interval %ds",
                    self._get_fan_friendly_name(fan_id),
                    int(time_since_last_attempt.total_seconds()),
                    int(self._recovery_attempt_interval),
                )
                return

        # Don't attempt recovery if device has been offline too long
        # (convert hours to seconds)
        if device_state["last_disconnected"]:
            offline_duration = current_time - device_state["last_disconnected"]
            if offline_duration.total_seconds() > self._max_offline_duration:
                friendly_name = self._get_fan_friendly_name(fan_id)
                _LOGGER.warning(
                    "%s has been offline for %s - stopping recovery attempts",
                    friendly_name,
                    offline_duration,
                )
                return

        # Reset recovery attempts after 1 hour to allow continued trying
        if device_state["first_recovery_attempt"]:
            time_since_first_attempt = (
                current_time - device_state["first_recovery_attempt"]
            )
            if time_since_first_attempt.total_seconds() > self._recovery_reset_interval:
                friendly_name = self._get_fan_friendly_name(fan_id)
                _LOGGER.info(
                    "Resetting recovery attempts for %s after %d minutes",
                    friendly_name,
                    self._recovery_reset_interval // 60,
                )
                device_state["recovery_attempts"] = 0
                device_state["first_recovery_attempt"] = None

        # Limit recovery attempts per hour (not total)
        if device_state["recovery_attempts"] >= self._max_recovery_attempts_per_hour:
            friendly_name = self._get_fan_friendly_name(fan_id)
            _LOGGER.debug(
                "%s has reached %d recovery attempts this period - waiting for reset",
                friendly_name,
                self._max_recovery_attempts_per_hour,
            )
            return

        friendly_name = self._get_fan_friendly_name(fan_id)
        _LOGGER.info(
            "Attempting to recover %s (attempt %d)",
            friendly_name,
            device_state["recovery_attempts"] + 1,
        )

        device_state["recovery_attempts"] += 1
        device_state["last_recovery_attempt"] = current_time

        # Track first recovery attempt for reset timing
        if device_state["first_recovery_attempt"] is None:
            device_state["first_recovery_attempt"] = current_time

        try:
            # Attempt to refresh the device data
            async def update_fan() -> Any:
                # Call the fan's internal update without direct static access
                method = getattr(
                    fan,
                    "_async_update_fan",
                    None,
                )
                if callable(method):
                    return await method()
                return None

            await self._error_handler.async_retry_operation(
                operation=update_fan,
                operation_name=f"recover fan {fan_id}",
                context={
                    "fan_id": fan_id,
                    "attempt": device_state["recovery_attempts"],
                },
            )

            # Check if recovery was successful
            if getattr(fan, "connected", False):
                _LOGGER.info("Fan %s recovery successful!", fan_id)
                device_state["recovery_attempts"] = 0
                device_state["last_connected"] = current_time
                device_state["last_disconnected"] = None
                # Notify so HA updates availability/attributes immediately
                await self._notify_fan_entity(fan_id)
            else:
                _LOGGER.debug(
                    "Fan %s recovery attempt %d did not restore connection",
                    fan_id,
                    device_state["recovery_attempts"],
                )
                # Schedule next recovery attempt
                await self._schedule_next_recovery(fan_id, fan, device_state)

        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            _LOGGER.warning(
                "Fan %s recovery attempt %d failed: %s",
                fan_id,
                device_state["recovery_attempts"],
                exc,
            )
            # Schedule next recovery attempt even if this one failed
            await self._schedule_next_recovery(fan_id, fan, device_state)

    async def _schedule_next_recovery(
        self, fan_id: str, fan: Any, device_state: dict[str, Any]
    ) -> None:
        """Schedule the next recovery attempt for a fan."""
        # Cancel any existing callback for this fan
        if self._recovery_callbacks.get(fan_id):
            self._recovery_callbacks[fan_id]()
            self._recovery_callbacks[fan_id] = None

        # Check if we should schedule another attempt
        if device_state["recovery_attempts"] >= self._max_recovery_attempts_per_hour:
            friendly_name = self._get_fan_friendly_name(fan_id)
            _LOGGER.debug(
                "%s has reached max recovery attempts (%d) - waiting for reset",
                friendly_name,
                self._max_recovery_attempts_per_hour,
            )
            return

        # Schedule next attempt after the configured interval
        friendly_name = self._get_fan_friendly_name(fan_id)
        interval_seconds = self._recovery_attempt_interval
        _LOGGER.debug(
            "Scheduling next recovery attempt for %s in %d seconds",
            friendly_name,
            interval_seconds,
        )

        async def next_recovery_attempt(_now: datetime) -> None:
            """Execute the next recovery attempt."""
            _LOGGER.debug("Executing scheduled recovery attempt for %s", friendly_name)
            await self._attempt_device_recovery(fan_id, fan, device_state)

        self._recovery_callbacks[fan_id] = async_call_later(
            self._hass, interval_seconds, next_recovery_attempt
        )

    def get_device_status(self, fan_id: str) -> dict[str, Any] | None:
        """Get the current status of a specific device."""
        return self._device_states.get(fan_id)

    def get_all_device_status(self) -> dict[str, dict[str, Any]]:
        """Get the status of all devices."""
        return self._device_states.copy()

    async def force_recovery_check(self, fan_id: str | None = None) -> None:
        """Force an immediate recovery check.

        If fan_id is provided, only that device will be evaluated; otherwise all.
        """
        if fan_id is None:
            _LOGGER.info("Forcing immediate connection recovery check for all devices")
            await self._check_connections()
            return

        if not self._scmanager or not self._scmanager.fans:
            _LOGGER.debug("No SmartCocoon manager or fans available for forced check")
            return

        fan = self._scmanager.fans.get(fan_id)
        if not fan:
            _LOGGER.debug("Force recovery requested for unknown fan_id=%s", fan_id)
            return

        _LOGGER.info("Forcing immediate connection recovery check for fan %s", fan_id)
        await self._check_device_connection(fan_id, fan)

    async def check_fan_unavailable(self, fan_id: str) -> None:
        """Check and attempt recovery for a fan that has become unavailable."""
        if not self._scmanager or fan_id not in self._scmanager.fans:
            _LOGGER.warning("Fan %s not found for unavailable check", fan_id)
            return

        fan = self._scmanager.fans[fan_id]
        friendly_name = self._get_fan_friendly_name(fan_id)
        _LOGGER.info("%s has become unavailable - checking connection", friendly_name)

        # Force a fresh check of this specific fan
        await self._check_device_connection(fan_id, fan)
