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
                # Get retry count from decorator parameter or instance attribute
                if retries is not None:
                    max_retries = retries
                else:
                    max_retries = int(getattr(self, "reconnection_retries"))

                # Use verbosity_display if available, otherwise no-op
                display = getattr(self, "verbosity_display", lambda level, msg: None)
                cmd_summary = f"{args[0]}..." if args else "command"

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

                        msg = (
                            f"AWSConnectionRetry: attempt {attempt}/{max_retries + 1}, "
                            f"caught exception ({type(e).__name__}: {e}) "
                            f"from cmd ({cmd_summary}), pausing for {pause} seconds"
                        )
                        display(2, msg)

                        time.sleep(pause)

                        # Restart the connection before retrying
                        # This ensures we don't reuse a broken connection
                        if hasattr(self, "close"):
                            self.close()

            return wrapped

        return retry_decorator
