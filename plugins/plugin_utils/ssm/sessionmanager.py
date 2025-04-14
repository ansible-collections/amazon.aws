# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import os
import select
import time
from pty import openpty
from subprocess import PIPE
from subprocess import Popen
from typing import Any
from typing import Callable
from typing import Dict
from typing import NoReturn
from typing import Optional
from typing import Union

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_text

verbosity_display_type = Callable[[int, str], None]


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
        self._session = session
        self._stdout = stdout
        self.verbosity_display = verbosity_display
        self._timeout = timeout
        self._poller = None
        self.instance_id = instance_id
        self._session_id = None
        self._poller = _create_polling_obj(self._stdout)
        self._has_timeout = False

    def stdin_write(self, command: Union[bytes, str]) -> None:
        self._session.stdin.write(command)

    def stdout_read_text(self, size: int = 1024) -> str:
        return to_text(self._stdout.read(size))

    def stdout_readline(self) -> str:
        return self._stdout.readline()

    def flush_stderr(self) -> str:
        """read and return stderr with minimal blocking"""

        poller = _create_polling_obj(self._session.stderr)
        stderr = ""
        while self._session.poll() is None:
            if not poller.poll(1):
                break
            line = self._session.stderr.readline()
            self.verbosity_display(4, f"stderr line: {to_text(line)}")
            stderr = stderr + line
        return stderr

    def poll_stdout(self, length: int = 1000) -> bool:
        return bool(self._poller.poll(length))

    def poll(self, label: str, cmd: str) -> NoReturn:
        """Poll session to retrieve content from stdout.

        :param label: A label for the display (EXEC, PRE...)
        :param cmd: The command being executed
        """
        start = round(time.time())
        yield self.poll_stdout()
        while self._session.poll() is None:
            remaining = start + self._timeout - round(time.time())
            self.verbosity_display(4, f"{label} remaining: {remaining} second(s)")
            if remaining < 0:
                self._has_timeout = True
                raise SSMProcessManagerTimeOutFailure(f"{label} command '{cmd}' timeout on host: {self.instance_id}")
            yield self.poll_stdout()

    def wait_for_match(self, label: str, cmd: Union[str, bytes], match: Union[str, Callable[[str], bool]]) -> None:
        stdout = ""
        self.verbosity_display(4, f"{label} WAIT FOR: {match} - Command = {to_text(cmd)}")
        for result in self.poll(label=label, cmd=to_text(cmd)):
            if result:
                text = self.stdout_read_text()
                self.verbosity_display(4, f"{label} stdout line: \n{text}")
                stdout += text
                if isinstance(match, str):
                    if stdout.find(match) != -1:
                        break
                elif match(stdout):
                    break

    def terminate(self) -> None:
        if self._has_timeout:
            self._session.terminate()
        else:
            cmd = b"\nexit\n"
            self._session.communicate(cmd)


class SSMSessionManager:
    MARK_LENGTH = 26

    def __init__(
        self, ssm_client: Any, instance_id: str, ssm_timeout: int, verbosity_display: verbosity_display_type
    ) -> None:
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

        self.verbosity_display(3, f"ESTABLISH SSM CONNECTION TO: {self.instance_id}")
        if parameters is None:
            parameters = {}
        start_session_args = dict(Target=self.instance_id, Parameters=parameters)
        if document_name is not None:
            start_session_args["DocumentName"] = document_name
        response = self._client.start_session(**start_session_args)
        self._session_id = response["SessionId"]
        self.verbosity_display(4, f"SSM CONNECTION ID: {self._session_id}")

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
            self._client.terminate_session(SessionId=self._session_id)
            self._session_id = None
