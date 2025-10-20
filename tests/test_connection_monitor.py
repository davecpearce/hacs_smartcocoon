"""Test connection monitor functionality."""
# ruff: noqa: SLF001

# pylint: disable=protected-access,unused-argument

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.smartcocoon.connection_monitor import (
    ConnectionMonitor,
    ConnectionMonitorConfig,
)
from custom_components.smartcocoon.error_handler import (
    RetryConfig,
    SmartCocoonErrorHandler,
)


class TestConnectionMonitor:
    """Test the ConnectionMonitor class."""

    @pytest.fixture
    def mock_hass(self):
        """Create a mock Home Assistant instance."""
        hass = MagicMock()
        hass.async_track_time_interval = MagicMock(return_value=MagicMock())
        return hass

    @pytest.fixture
    def mock_scmanager(self):
        """Create a mock SmartCocoonManager."""
        scmanager = MagicMock()

        # Create mock fan objects
        fan1 = MagicMock()
        fan1.connected = False
        fan1._async_update_fan = AsyncMock()

        fan2 = MagicMock()
        fan2.connected = True
        fan2._async_update_fan = AsyncMock()

        scmanager.fans = {
            "fan1": fan1,
            "fan2": fan2,
        }

        return scmanager

    @pytest.fixture
    def error_handler(self):
        """Create an error handler."""
        return SmartCocoonErrorHandler(RetryConfig(max_attempts=2))

    @pytest.fixture
    def connection_monitor(self, mock_hass, mock_scmanager, error_handler):
        """Create a ConnectionMonitor instance."""
        config = ConnectionMonitorConfig(
            max_offline_duration=3600,  # 1 hour for testing
            recovery_attempt_interval=300,  # 5 minutes for testing
            max_recovery_attempts_per_hour=5,  # 5 attempts for testing
            recovery_reset_interval=3600,  # 60 minutes for testing
            connection_check_interval=3600,  # 1 hour for testing
        )

        return ConnectionMonitor(
            hass=mock_hass,
            scmanager=mock_scmanager,
            error_handler=error_handler,
            config=config,
        )

    @pytest.mark.asyncio
    async def test_start_monitoring(self, connection_monitor, mock_hass):
        """Test starting the connection monitor."""
        # Ensure scmanager has fans so timer gets set up
        connection_monitor._scmanager.fans = {"fan1": MagicMock()}

        with patch(
            "custom_components.smartcocoon.connection_monitor.async_call_later"
        ) as mock_call_later:
            mock_call_later.return_value = MagicMock()

            await connection_monitor.start_monitoring()

            # Verify that async_call_later was called twice
            # (grace period + periodic check)
            assert mock_call_later.call_count == 2

            # Verify the callbacks are stored
            assert connection_monitor._grace_period_callback is not None
            assert connection_monitor._periodic_check_callback is not None

    @pytest.mark.asyncio
    async def test_stop_monitoring(self, connection_monitor, mock_hass):
        """Test stopping the connection monitor."""
        # Ensure scmanager has fans so timer gets set up
        connection_monitor._scmanager.fans = {"fan1": MagicMock()}

        with patch(
            "custom_components.smartcocoon.connection_monitor.async_call_later"
        ) as mock_call_later:
            mock_timer = MagicMock()
            mock_call_later.return_value = mock_timer

            # Start monitoring first
            await connection_monitor.start_monitoring()

            # Stop monitoring
            await connection_monitor.stop_monitoring()

            # Verify the timer was called (multiple times due to multiple callbacks)
            assert mock_timer.call_count >= 2
            # Verify the callbacks are cleared
            assert connection_monitor._grace_period_callback is None
            assert connection_monitor._periodic_check_callback is None

    @pytest.mark.asyncio
    async def test_check_connections(self, connection_monitor, mock_scmanager):
        """Test checking device connections."""
        # Mock the recovery attempt to prevent it from running
        with patch.object(
            connection_monitor, "_attempt_device_recovery", new_callable=AsyncMock
        ):
            await connection_monitor._check_connections()

            # Verify that device states are initialized
            assert "fan1" in connection_monitor._device_states
            assert "fan2" in connection_monitor._device_states

            # Verify fan1 is marked as disconnected
            fan1_state = connection_monitor._device_states["fan1"]
            assert fan1_state["last_disconnected"] is not None
            assert fan1_state["recovery_attempts"] == 0

            # Verify fan2 is marked as connected
            fan2_state = connection_monitor._device_states["fan2"]
            assert fan2_state["last_connected"] is not None
            assert fan2_state["last_disconnected"] is None

    @pytest.mark.asyncio
    async def test_device_recovery_attempt(self, connection_monitor, mock_scmanager):
        """Test attempting device recovery."""
        fan1 = mock_scmanager.fans["fan1"]
        fan1.connected = False

        # Initialize device state
        connection_monitor._device_states["fan1"] = {
            "last_connected": None,
            "last_disconnected": datetime.now() - timedelta(seconds=120),
            "recovery_attempts": 0,
            "first_recovery_attempt": None,
            "last_recovery_attempt": None,
        }

        # Attempt recovery
        await connection_monitor._attempt_device_recovery(
            "fan1", fan1, connection_monitor._device_states["fan1"]
        )

        # Verify recovery attempt was made
        fan1._async_update_fan.assert_called_once()
        assert connection_monitor._device_states["fan1"]["recovery_attempts"] == 1
        assert (
            connection_monitor._device_states["fan1"]["last_recovery_attempt"]
            is not None
        )

    @pytest.mark.asyncio
    async def test_recovery_success(self, connection_monitor, mock_scmanager):
        """Test successful device recovery."""
        fan1 = mock_scmanager.fans["fan1"]
        fan1.connected = False

        # Initialize device state
        connection_monitor._device_states["fan1"] = {
            "last_connected": None,
            "last_disconnected": datetime.now() - timedelta(seconds=120),
            "recovery_attempts": 0,
            "first_recovery_attempt": None,
            "last_recovery_attempt": None,
        }

        # Mock successful recovery
        with patch.object(fan1, "connected", True):
            await connection_monitor._attempt_device_recovery(
                "fan1", fan1, connection_monitor._device_states["fan1"]
            )

        # Verify recovery was successful
        fan1_state = connection_monitor._device_states["fan1"]
        assert fan1_state["recovery_attempts"] == 0  # Reset on success
        assert fan1_state["last_connected"] is not None
        assert fan1_state["last_disconnected"] is None

    @pytest.mark.asyncio
    async def test_recovery_rate_limiting(self, connection_monitor, mock_scmanager):
        """Test that recovery attempts are rate limited."""
        fan1 = mock_scmanager.fans["fan1"]
        fan1.connected = False

        # Initialize device state with recent recovery attempt
        connection_monitor._device_states["fan1"] = {
            "last_connected": None,
            "last_disconnected": datetime.now() - timedelta(seconds=120),
            "recovery_attempts": 1,
            "first_recovery_attempt": None,
            "last_recovery_attempt": datetime.now()
            - timedelta(seconds=30),  # Recent attempt
        }

        # Attempt recovery (should be rate limited)
        await connection_monitor._attempt_device_recovery(
            "fan1", fan1, connection_monitor._device_states["fan1"]
        )

        # Verify no additional recovery attempt was made
        assert connection_monitor._device_states["fan1"]["recovery_attempts"] == 1

    @pytest.mark.asyncio
    async def test_max_recovery_attempts(self, connection_monitor, mock_scmanager):
        """Test that recovery stops after max attempts."""
        fan1 = mock_scmanager.fans["fan1"]
        fan1.connected = False

        # Initialize device state with max attempts reached
        connection_monitor._device_states["fan1"] = {
            "last_connected": None,
            "last_disconnected": datetime.now() - timedelta(seconds=120),
            "recovery_attempts": 5,  # Max attempts
            "first_recovery_attempt": None,
            "last_recovery_attempt": datetime.now()
            - timedelta(seconds=600),  # Old attempt
        }

        # Attempt recovery (should be blocked by max attempts)
        await connection_monitor._attempt_device_recovery(
            "fan1", fan1, connection_monitor._device_states["fan1"]
        )

        # Verify no additional recovery attempt was made
        assert connection_monitor._device_states["fan1"]["recovery_attempts"] == 5

    @pytest.mark.asyncio
    async def test_max_offline_duration(self, connection_monitor, mock_scmanager):
        """Test that recovery stops after max offline duration."""
        fan1 = mock_scmanager.fans["fan1"]
        fan1.connected = False

        # Initialize device state with long offline duration
        connection_monitor._device_states["fan1"] = {
            "last_connected": None,
            "last_disconnected": datetime.now()
            - timedelta(hours=25),  # 25 hours offline
            "recovery_attempts": 1,
            "first_recovery_attempt": None,
            "last_recovery_attempt": datetime.now() - timedelta(hours=25),
        }

        # Attempt recovery (should be blocked by max offline duration)
        await connection_monitor._attempt_device_recovery(
            "fan1", fan1, connection_monitor._device_states["fan1"]
        )

        # Verify no additional recovery attempt was made
        assert connection_monitor._device_states["fan1"]["recovery_attempts"] == 1

    def test_get_device_status(self, connection_monitor):
        """Test getting device status."""
        # Initialize some device states
        connection_monitor._device_states = {
            "fan1": {
                "last_connected": datetime.now(),
                "last_disconnected": None,
                "recovery_attempts": 0,
                "first_recovery_attempt": None,
                "last_recovery_attempt": None,
            }
        }

        # Get status
        status = connection_monitor.get_device_status("fan1")
        assert status is not None
        assert status["recovery_attempts"] == 0

        # Get non-existent device
        status = connection_monitor.get_device_status("nonexistent")
        assert status is None

    def test_get_all_device_status(self, connection_monitor):
        """Test getting all device status."""
        # Initialize some device states
        connection_monitor._device_states = {
            "fan1": {"test": "data1"},
            "fan2": {"test": "data2"},
        }

        # Get all status
        all_status = connection_monitor.get_all_device_status()
        assert len(all_status) == 2
        assert "fan1" in all_status
        assert "fan2" in all_status

    @pytest.mark.asyncio
    async def test_force_recovery_check(self, connection_monitor, mock_scmanager):
        """Test forcing a recovery check."""
        with patch.object(
            connection_monitor, "_check_connections", new_callable=AsyncMock
        ) as mock_check:
            await connection_monitor.force_recovery_check()
            mock_check.assert_called_once()
