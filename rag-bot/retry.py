"""
Retry decorator with exponential backoff
Handles transient failures for Azure services
"""
import time
import logging
from functools import wraps
from typing import Callable
import random

logger = logging.getLogger(__name__)

# Exceptions that should trigger a retry
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    Exception,  # We'll check error messages for known transient errors
)

def is_retryable_error(exception: Exception) -> bool:
    """Determine if an error should trigger a retry"""
    # Check exception type
    if isinstance(exception, (ConnectionError, TimeoutError)):
        return True

    # Check error messages for known transient errors
    error_msg = str(exception).lower()
    retryable_patterns = [
        'rate limit',
        'too many requests',
        'timeout',
        'connection',
        'temporarily unavailable',
        'service unavailable',
        'throttled',
        '429',
        '503',
        '504',
    ]

    return any(pattern in error_msg for pattern in retryable_patterns)

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 32.0,
    exponential_base: float = 2.0,
    jitter: bool = True
):
    """
    Decorator for retrying functions with exponential backoff

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay in seconds between retries
        exponential_base: Base for exponential backoff calculation
        jitter: Add random jitter to prevent thundering herd

    Usage:
        @retry_with_backoff(max_retries=3, initial_delay=1.0)
        def my_function():
            # Function that might fail transiently
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            delay = initial_delay

            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    # Check if error is retryable
                    if not is_retryable_error(e):
                        logger.error(f"{func.__name__} failed with non-retryable error: {e}")
                        raise

                    retries += 1

                    if retries > max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    current_delay = min(delay * (exponential_base ** (retries - 1)), max_delay)

                    # Add jitter to prevent thundering herd
                    if jitter:
                        current_delay = current_delay * (0.5 + random.random() * 0.5)

                    logger.warning(
                        f"{func.__name__} failed (attempt {retries}/{max_retries}): {e}. "
                        f"Retrying in {current_delay:.2f}s..."
                    )

                    time.sleep(current_delay)

            # Should never reach here
            raise RuntimeError(f"{func.__name__} exhausted all retries")

        return wrapper
    return decorator

# Convenience decorators for common scenarios
retry_api_call = retry_with_backoff(max_retries=3, initial_delay=1.0, max_delay=16.0)
retry_db_operation = retry_with_backoff(max_retries=3, initial_delay=0.5, max_delay=8.0)
retry_whatsapp = retry_with_backoff(max_retries=2, initial_delay=2.0, max_delay=10.0)
