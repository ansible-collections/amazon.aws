# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import time
import typing
from functools import wraps

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Callable

from ansible_collections.amazon.aws.plugins.module_utils.cloud import BackoffIterator


class AWSConnectionRetry:
    """
    Decorator class for retrying connection plugin operations with exponential backoff.

    Designed for use with AWS connection plugins that need to restart connections
    on failure (e.g., SSM, which needs to close and reopen sessions).

    The decorated method must be an instance method on an object with:
    - reconnection_retries (int): Number of retry attempts
    - verbosity_display (callable): Function for logging verbosity messages
    - close() (optional): Method to close/restart the connection

    Example usage:
        @AWSConnectionRetry.exponential_backoff()
        def exec_command(self, cmd):
            # command execution code
            pass
    """

    @staticmethod
    def _get_max_retries(instance: Any, retries_param: int | None) -> int:
        """Get the maximum retry count from parameter or instance attribute."""
        if retries_param is not None:
            return retries_param
        return int(getattr(instance, "reconnection_retries", 0))

    @staticmethod
    def _get_cmd_summary(args: tuple) -> str:
        """Extract command summary from arguments for logging."""
        if args:
            return f"{args[0]}..."
        return "command"

    @staticmethod
    def _get_display_func(instance: Any) -> Callable:
        """Get verbosity display function or return no-op."""
        return getattr(instance, "verbosity_display", lambda level, msg: None)

    @staticmethod
    def _restart_connection(instance: Any) -> None:
        """Close and restart connection if close method exists."""
        if hasattr(instance, "close"):
            instance.close()

    @staticmethod
    def _format_retry_message(
        attempt: int, max_retries: int, exception: Exception, cmd_summary: str, pause: float
    ) -> str:
        """Format the retry log message."""
        return (
            f"AWSConnectionRetry: attempt {attempt}/{max_retries + 1}, "
            f"caught exception ({type(exception).__name__}: {exception}) "
            f"from cmd ({cmd_summary}), pausing for {pause} seconds"
        )

    @classmethod
    def exponential_backoff(
        cls,
        retries: int | None = None,
        initial_delay: int = 1,
        backoff_multiplier: int = 2,
        max_delay: int = 30,
        jitter: bool = False,
    ) -> Callable:
        """
        Wrap a connection plugin method with retry behavior and connection restart.

        Args:
            retries: Number of retry attempts. If None, reads from self.reconnection_retries
            initial_delay: Initial delay in seconds (default: 1)
            backoff_multiplier: Multiplier for exponential backoff (default: 2)
            max_delay: Maximum delay between retries in seconds (default: 30)
            jitter: If True, add randomness to delay values (default: False)

        Returns:
            Callable: Decorated function with retry behavior
        """

        def retry_decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapped(self, *args: Any, **kwargs: Any) -> Any:
                max_retries = cls._get_max_retries(self, retries)
                display = cls._get_display_func(self)
                cmd_summary = cls._get_cmd_summary(args)

                # Create backoff iterator for delay calculations
                backoff_iterator = BackoffIterator(
                    delay=initial_delay, backoff=backoff_multiplier, max_delay=max_delay, jitter=jitter
                )

                attempt = 0
                for pause in backoff_iterator:
                    try:
                        return_tuple = func(self, *args, **kwargs)
                        # Success - return immediately to avoid catching display() exceptions
                        return return_tuple
                    except Exception as e:
                        attempt += 1
                        if attempt > max_retries:
                            raise

                        msg = cls._format_retry_message(attempt, max_retries, e, cmd_summary, pause)
                        display(2, msg)
                        time.sleep(pause)
                        cls._restart_connection(self)

            return wrapped

        return retry_decorator
