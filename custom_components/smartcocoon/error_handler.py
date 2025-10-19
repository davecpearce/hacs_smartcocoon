"""Error handling module for SmartCocoon integration."""

import asyncio
from collections.abc import Coroutine
from dataclasses import dataclass
import logging
import random
from typing import Any, Callable, TypeVar

from pysmartcocoon.errors import RequestError, SmartCocoonError, UnauthorizedError

from homeassistant.exceptions import ConfigEntryAuthFailed

_LOGGER = logging.getLogger(__name__)

R = TypeVar("R")  # Return type of the operation


@dataclass
class RetryConfig:
    """Configuration for retry logic."""

    max_attempts: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 30.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True
    # Retry generic exceptions (use with caution)
    retry_generic_exceptions: bool = False


class SmartCocoonErrorHandler:
    """Handles errors and implements retry logic for SmartCocoon API calls."""

    def __init__(self, retry_config: RetryConfig | None = None) -> None:
        """Initialize the error handler."""
        self._retry_config = retry_config if retry_config else RetryConfig()

    async def async_retry_operation(
        self,
        operation: Callable[..., Coroutine[Any, Any, R]],
        operation_name: str = "API operation",
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> R:
        """Retry an asynchronous operation with exponential backoff and jitter."""
        context = context if context is not None else {}
        for attempt in range(self._retry_config.max_attempts):
            try:
                return await operation(**kwargs)
            except UnauthorizedError as exc:
                _LOGGER.error(
                    "Authentication failed for %s (attempt %d/%d). Context: %s",
                    operation_name,
                    attempt + 1,
                    self._retry_config.max_attempts,
                    context,
                )
                # Convert UnauthorizedError to ConfigEntryAuthFailed for HA integration
                raise ConfigEntryAuthFailed("Authentication failed") from exc
            except (RequestError, SmartCocoonError, asyncio.TimeoutError) as exc:
                if attempt == self._retry_config.max_attempts - 1:
                    _LOGGER.error(
                        "Failed to complete %s after %d attempts. Context: %s. Error: %s",
                        operation_name,
                        self._retry_config.max_attempts,
                        context,
                        exc,
                    )
                    raise exc

                delay = self._calculate_delay(attempt)
                _LOGGER.warning(
                    "Attempt %d/%d for %s failed. Retrying in %.2f seconds. Context: %s. Error: %s",
                    attempt + 1,
                    self._retry_config.max_attempts,
                    operation_name,
                    delay,
                    context,
                    exc,
                )
                await asyncio.sleep(delay)
            except Exception as exc:
                if self._retry_config.retry_generic_exceptions:
                    if attempt == self._retry_config.max_attempts - 1:
                        _LOGGER.error(
                            "Failed to complete %s after %d attempts. Context: %s. Error: %s",
                            operation_name,
                            self._retry_config.max_attempts,
                            context,
                            exc,
                        )
                        raise exc
                    
                    delay = self._calculate_delay(attempt)
                    _LOGGER.warning(
                        "Attempt %d/%d for %s failed with unexpected error. Retrying in %.2f seconds. Context: %s. Error: %s",
                        attempt + 1,
                        self._retry_config.max_attempts,
                        operation_name,
                        delay,
                        context,
                        exc,
                    )
                    await asyncio.sleep(delay)
                else:
                    _LOGGER.exception(
                        "An unexpected error occurred during %s (attempt %d/%d). Context: %s",
                        operation_name,
                        attempt + 1,
                        self._retry_config.max_attempts,
                        context,
                    )
                    raise exc
        raise RuntimeError(
            "Should not reach here: retry logic exhausted without raising an exception."
        )

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate the delay for the next retry attempt."""
        delay = self._retry_config.base_delay * (
            self._retry_config.exponential_base**attempt
        )
        if self._retry_config.jitter:
            delay = random.uniform(0, delay)
        return min(delay, self._retry_config.max_delay)
