# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import time
from functools import wraps
from typing import Any
from typing import TypedDict

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_text


def ssm_retry(func: Any) -> Any:
    """
    Decorator to retry in the case of a connection failure
    Will retry if:
    * an exception is caught
    Will not retry if
    * remaining_tries is <2
    * retries limit reached
    """

    @wraps(func)
    def wrapped(self, *args: Any, **kwargs: Any) -> Any:
        reconnection_retries = getattr(self, "reconnection_retries")
        remaining_tries = int(reconnection_retries) + 1
        verbosity_d = getattr(self, "verbosity_display", None)
        cmd_summary = f"{args[0]}..."
        for attempt in range(remaining_tries):
            try:
                return_tuple = func(self, *args, **kwargs)
                verbosity_d(4, f"ssm_retry: (success) {to_text(return_tuple)}")
                return return_tuple
            except (AnsibleConnectionFailure, Exception) as e:
                if attempt == remaining_tries - 1:
                    raise
                pause = 2**attempt - 1
                pause = min(pause, 30)

                if isinstance(e, AnsibleConnectionFailure):
                    msg = f"ssm_retry: attempt: {attempt}, cmd ({cmd_summary}), pausing for {pause} seconds"
                else:
                    msg = (
                        f"ssm_retry: attempt: {attempt}, caught exception({e})"
                        f"from cmd ({cmd_summary}),pausing for {pause} seconds"
                    )

                verbosity_d(2, msg)

                time.sleep(pause)

                # Do not attempt to reuse the existing session on retries
                # This will cause the SSM session to be completely restarted,
                # as well as reinitializing the boto3 clients
                if hasattr(self, "close"):
                    self.close()

                continue

    return wrapped


class CommandResult(TypedDict):
    """
    A dictionary that contains the executed command results.
    """

    returncode: int
    stdout: str
    stderr: str
