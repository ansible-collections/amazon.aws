# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import json
import os
import select
import time
import typing
from pty import openpty
from subprocess import PIPE
from subprocess import Popen

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Callable
    from typing import Dict
    from typing import Iterator
    from typing import NoReturn
    from typing import Optional
    from typing import Union

    verbosity_display_type = Callable[[int, str], None]

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.common.text.converters import to_text

from ansible_collections.amazon.aws.plugins.plugin_utils.text import filter_ansi


class SSMProcessManagerTimeOutFailure(AnsibleConnectionFailure):
    pass


def _create_polling_obj(fd: Any) -> Any:
    """create polling object using select.poll, this is helpful for unit testing"""
    poller = select.poll()
    poller.register(fd, select.POLLIN)
    return poller


class ProcessManager:
    def __init__(
        self, instance_id: str, session: Any, stdout: Any, timeout: int, verbosity_display: verbosity_display_type
    ) -> None:
        """
        Initialise the ProcessManager.

        :param instance_id: The EC2 instance ID
        :param session: The subprocess session
        :param stdout: The stdout file descriptor
        :param timeout: Connection timeout in seconds
        :param verbosity_display: Function for logging verbosity messages
        """
        self._session = session
        self._stdout = stdout
        self.verbosity_display = verbosity_display
        self._timeout = timeout
        self._poller = None
        self.instance_id = instance_id
        self._session_id = None
        self._poller = _create_polling_obj(self._stdout)
        self._has_timeout = False
        self._stderr_accumulator = ""

    def stdin_write(self, command: Union[bytes, str]) -> None:
        if isinstance(command, str):
            command = command.encode("utf-8")
        self.verbosity_display(5, f"stdin_write: Writing {len(command)} bytes")
        self.verbosity_display(5, f"stdin_write: First 200 bytes: {repr(command[:200])}")
        self._session.stdin.write(command)
        self._session.stdin.flush()
        self.verbosity_display(5, "stdin_write: Flushed")

    def stdout_read_text(self, size: int = 1024) -> str:
        return to_text(self._stdout.read(size), encoding="utf-8", errors="surrogate_or_strict")

    def stdout_readline(self) -> str:
        self.verbosity_display(5, "stdout_readline: About to call readline()")
        result = self._stdout.readline()
        self.verbosity_display(5, f"stdout_readline: readline() returned {len(result)} bytes")
        # DEBUG: Level 6 for long-term debugging of encoding issues
        self.verbosity_display(6, f"stdout_readline: Raw bytes: {result[:200]}")
        # Decode as UTF-8 with surrogate escapes to handle any encoding issues
        decoded = to_text(result, encoding="utf-8", errors="surrogate_or_strict")
        self.verbosity_display(6, f"stdout_readline: Decoded string: {repr(decoded[:200])}")
        return decoded

    def flush_stderr(self) -> str:
        """Read available stderr, accumulate it, and return all accumulated stderr.

        This method reads any currently available stderr data without blocking,
        accumulates it internally, and returns the full accumulated stderr.
        The accumulator is then cleared so subsequent calls start fresh.

        :returns: All accumulated stderr since last flush
        """

        poller = _create_polling_obj(self._session.stderr)
        self.verbosity_display(5, "FLUSH_STDERR: Checking session.poll() status")
        poll_result = self._session.poll()
        self.verbosity_display(5, f"FLUSH_STDERR: session.poll() returned {poll_result}")
        while poll_result is None:
            self.verbosity_display(5, "FLUSH_STDERR: About to poll stderr with 1ms timeout")
            poll_res = poller.poll(1)
            self.verbosity_display(5, f"FLUSH_STDERR: stderr poll returned {poll_res}")
            if not poll_res:
                break
            self.verbosity_display(5, "FLUSH_STDERR: About to read stderr line")
            line = to_text(self._session.stderr.readline(), encoding="utf-8", errors="surrogate_or_strict")
            self.verbosity_display(5, f"FLUSH_STDERR: stderr readline returned {len(line)} chars")
            self.verbosity_display(4, f"stderr line: {repr(line)}")
            self._stderr_accumulator = self._stderr_accumulator + line
            self.verbosity_display(5, "FLUSH_STDERR: Checking session.poll() status")
            poll_result = self._session.poll()
            self.verbosity_display(5, f"FLUSH_STDERR: session.poll() returned {poll_result}")

        # Return accumulated stderr and clear the accumulator
        result = self._stderr_accumulator
        self._stderr_accumulator = ""
        return result

    def poll_stdout(self, length: int = 1000) -> bool:
        self.verbosity_display(5, f"poll_stdout: About to poll with {length}ms timeout")
        result = bool(self._poller.poll(length))
        self.verbosity_display(5, f"poll_stdout({length}ms) -> {result}")
        return result

    def poll(self, label: str, cmd: str) -> Iterator[bool]:
        """Poll session to retrieve content from stdout.

        :param label: A label for the display (EXEC, PRE...)
        :param cmd: The command being executed
        """
        start = round(time.time())
        yield self.poll_stdout()
        self.verbosity_display(5, f"{label} POLL: Checking session.poll() status")
        poll_result = self._session.poll()
        self.verbosity_display(5, f"{label} POLL: session.poll() returned {poll_result}")
        while poll_result is None:
            remaining = start + self._timeout - round(time.time())
            self.verbosity_display(4, f"{label} remaining: {remaining} second(s)")
            if remaining < 0:
                self._has_timeout = True
                raise SSMProcessManagerTimeOutFailure(f"{label} command '{cmd}' timeout on host: {self.instance_id}")
            yield self.poll_stdout()
            self.verbosity_display(5, f"{label} POLL: Checking session.poll() status")
            poll_result = self._session.poll()
            self.verbosity_display(5, f"{label} POLL: session.poll() returned {poll_result}")

    def wait_for_match(
        self, label: str, cmd: Union[str, bytes], match: Union[str, Callable[[str], bool]], is_windows: bool = False
    ) -> None:
        """Wait for stdout to match a pattern.

        For callable matches (e.g. regex), tries matching on both raw and ANSI-filtered
        stdout to handle cases where terminal control codes might interfere with matching.

        Uses readline() to avoid consuming additional output beyond the matched line,
        preventing race conditions where both start and end markers are read together.

        :param label: Label for logging purposes.
        :param cmd: The command being executed.
        :param match: Either a string to search for or a callable that returns True when matched.
        :param is_windows: Whether the output is from a Windows host (for ANSI filtering).
        """
        stdout = ""
        wait_start = time.time()
        last_progress_log = wait_start
        poll_count = 0
        line_count = 0

        self.verbosity_display(4, f"{label} WAIT_FOR_MATCH: Starting to wait for pattern")
        if isinstance(match, str):
            self.verbosity_display(4, f"{label} WAIT_FOR_MATCH: Looking for string: {repr(match)}")
        else:
            self.verbosity_display(4, f"{label} WAIT_FOR_MATCH: Looking for pattern match")
        self.verbosity_display(4, f"{label} WAIT_FOR_MATCH: Command = {to_text(cmd)}")

        # Check stderr before starting to wait
        stderr_output = self.flush_stderr()
        if stderr_output:
            self.verbosity_display(4, f"{label} WAIT_FOR_MATCH: stderr before wait: {repr(stderr_output)}")

        for result in self.poll(label=label, cmd=to_text(cmd)):
            poll_count += 1
            current_time = time.time()

            # Log progress every 5 seconds during long waits
            if current_time - last_progress_log >= 5.0:
                elapsed = current_time - wait_start
                self.verbosity_display(
                    3,
                    f"{label} WAIT_FOR_MATCH: Still waiting after {elapsed:.1f}s ({line_count} lines, {poll_count} polls, {len(stdout)} bytes collected)",
                )
                last_progress_log = current_time

            if result:
                line = to_text(self.stdout_readline())
                line_count += 1
                self.verbosity_display(4, f"{label} WAIT_FOR_MATCH: stdout line {line_count}: {repr(line)}")
                stdout += line

                if isinstance(match, str):
                    if stdout.find(match) != -1:
                        elapsed = time.time() - wait_start
                        self.verbosity_display(
                            4, f"{label} WAIT_FOR_MATCH: MATCHED! Found string in stdout after {elapsed:.2f}s"
                        )
                        break
                    # Log last 100 chars to help debug why match isn't found
                    self.verbosity_display(
                        5, f"{label} WAIT_FOR_MATCH: No match yet, last 100 chars: {repr(stdout[-100:])}"
                    )
                else:
                    # For callable matches, try both raw and filtered text
                    stdout_filtered = filter_ansi(stdout, is_windows)
                    if match(stdout) or match(stdout_filtered):
                        elapsed = time.time() - wait_start
                        self.verbosity_display(
                            4, f"{label} WAIT_FOR_MATCH: MATCHED! Pattern matched stdout after {elapsed:.2f}s"
                        )
                        break
                    # Log last 100 chars to help debug why pattern doesn't match
                    self.verbosity_display(5, f"{label} WAIT_FOR_MATCH: No pattern match yet")
                    self.verbosity_display(5, f"{label} WAIT_FOR_MATCH: Last 100 chars (raw): {repr(stdout[-100:])}")
                    self.verbosity_display(
                        5, f"{label} WAIT_FOR_MATCH: Last 100 chars (filtered): {repr(stdout_filtered[-100:])}"
                    )
            else:
                # No stdout data, check stderr
                stderr_output = self.flush_stderr()
                if stderr_output:
                    self.verbosity_display(4, f"{label} WAIT_FOR_MATCH: stderr while waiting: {repr(stderr_output)}")

        total_duration = time.time() - wait_start
        self.verbosity_display(
            4,
            f"{label} WAIT_FOR_MATCH: Complete after {total_duration:.2f}s - {line_count} lines, {poll_count} polls, {len(stdout)} bytes collected",
        )
        self.verbosity_display(5, f"{label} WAIT_FOR_MATCH: Full stdout collected: {repr(stdout)}")

        # Check if we saw command echo before the match (indicates PSReadLine wasn't removed on Windows)
        if is_windows and label == "EXEC_COMMUNICATE" and line_count > 5:
            # Look for signs of PowerShell command echo (base64 or PowerShell keywords)
            if "powershell" in stdout.lower() or any(
                char in stdout for char in ["A", "B", "C", "D"] if stdout.count(char) > 50
            ):
                self.verbosity_display(
                    2,
                    f"{label} WAIT_FOR_MATCH: WARNING - Detected possible command echo in {line_count} lines before marker. "
                    "PSReadLine may not have been removed properly.",
                )

    def terminate(self) -> None:
        if self._has_timeout:
            self._session.terminate()
        else:
            cmd = b"\nexit\n"
            self._session.communicate(cmd)


class SSMSessionManager:
    def __init__(
        self, ssm_client: Any, instance_id: str, ssm_timeout: int, verbosity_display: verbosity_display_type
    ) -> None:
        """
        Initialise the SSMSessionManager.

        :param ssm_client: The boto3 SSM client
        :param instance_id: The EC2 instance ID
        :param ssm_timeout: Connection timeout in seconds
        :param verbosity_display: Function for logging verbosity messages
        """
        self._session_id = None
        self._instance_id = instance_id
        self.verbosity_display = verbosity_display
        self._client = ssm_client
        self._process_mgr = None
        self._timeout = ssm_timeout
        self._session = None

    @property
    def instance_id(self) -> str:
        return self._instance_id

    @property
    def session(self) -> Any:
        return self._session

    @property
    def stdout(self) -> Any:
        return self._stdout

    def __getattr__(self, attr: str) -> Callable:
        if self._process_mgr and hasattr(self._process_mgr, attr):
            return getattr(self._process_mgr, attr)
        raise AttributeError(f"class SSMSessionManager has no attribute '{attr}'")

    def start_session(
        self,
        executable: str,
        document_name: Optional[str],
        region_name: Optional[str],
        profile_name: str,
        parameters: Dict[str, Any] = None,
    ) -> None:
        """Start SSM Session manager session and eventually prepare terminal"""

        self.verbosity_display(2, f"ESTABLISH SSM CONNECTION TO: {self.instance_id}")
        if parameters is None:
            parameters = {}
        start_session_args = dict(Target=self.instance_id, Parameters=parameters)
        if document_name is not None:
            start_session_args["DocumentName"] = document_name
        response = self._client.start_session(**start_session_args)
        self._session_id = response["SessionId"]
        self.verbosity_display(3, f"SSM CONNECTION ID: {self._session_id}")

        cmd = [
            executable,
            json.dumps(response),
            region_name,
            "StartSession",
            profile_name,
            json.dumps({"Target": self.instance_id}),
            self._client.meta.endpoint_url,
        ]

        self.verbosity_display(4, f"SSM COMMAND: {to_text(cmd)}")

        stdout_r, stdout_w = openpty()
        self._session = Popen(cmd, stdin=PIPE, stdout=stdout_w, stderr=PIPE, close_fds=True, bufsize=0)

        os.close(stdout_w)
        stdout = os.fdopen(stdout_r, "rb", 0)

        self._process_mgr = ProcessManager(
            instance_id=self.instance_id,
            session=self._session,
            stdout=stdout,
            timeout=self._timeout,
            verbosity_display=self.verbosity_display,
        )

    def terminate(self) -> None:
        if self._process_mgr:
            self._process_mgr.terminate()
        if self._session_id and self._client:
            try:
                self._client.terminate_session(SessionId=self._session_id)
            except ReferenceError:
                # Client may have been garbage collected during cleanup
                pass
            self._session_id = None
