# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import random
import re
import string

from ansible.module_utils._text import to_bytes
from ansible.module_utils._text import to_text
from ansible.plugins.shell.powershell import _common_args


class TerminalManager:
    def __init__(self, connection):
        self.connection = connection

    def prepare_terminal(self) -> None:
        """perform any one-time terminal settings"""
        # No Windows setup for now
        if self.connection.is_windows:
            return

        # Ensure SSM Session has started
        self.ensure_ssm_session_has_started()

        # Disable echo command
        self.disable_echo_command()  # pylint: disable=unreachable

        # Disable prompt command
        self.disable_prompt_command()  # pylint: disable=unreachable

        self.connection.verbosity_display(4, "PRE Terminal configured")  # pylint: disable=unreachable

    def wrap_command(self, cmd: str, mark_start: str, mark_end: str) -> str:
        """Wrap command so stdout and status can be extracted"""

        if self.connection.is_windows:
            if not cmd.startswith(" ".join(_common_args) + " -EncodedCommand"):
                cmd = self.connection._shell._encode_script(cmd, preserve_rc=True)
            cmd = f"{cmd}; echo {mark_start}\necho {mark_end}\n"
        else:
            cmd = (
                f"printf '%s\\n' '{mark_start}';\n"
                f"echo | {cmd};\n"
                f"printf '\\n%s\\n%s\\n' \"$?\" '{mark_end}';\n"
            )  # fmt: skip

        self.connection.verbosity_display(4, f"wrap_command: \n'{to_text(cmd)}'")
        return cmd

    def disable_echo_command(self) -> None:
        """Disable echo command from the host"""
        disable_echo_cmd = to_bytes("stty -echo\n", errors="surrogate_or_strict")

        # Send command
        self.connection.verbosity_display(4, f"DISABLE ECHO Disabling Prompt: \n{disable_echo_cmd}")
        self.connection.session_manager.stdin_write(disable_echo_cmd)

        self.connection.session_manager.wait_for_match(label="DISABLE ECHO", cmd=disable_echo_cmd, match="stty -echo")

    def disable_prompt_command(self) -> None:
        """Disable prompt command from the host"""
        end_mark = "".join([random.choice(string.ascii_letters) for i in range(self.connection.MARK_LENGTH)])
        disable_prompt_cmd = to_bytes(
            "PS1='' ; bind 'set enable-bracketed-paste off'; printf '\\n%s\\n' '" + end_mark + "'\n",
            errors="surrogate_or_strict",
        )
        disable_prompt_reply = re.compile(r"\r\r\n" + re.escape(end_mark) + r"\r\r\n", re.MULTILINE)

        # Send command
        self.connection.verbosity_display(4, f"DISABLE PROMPT Disabling Prompt: \n{disable_prompt_cmd}")
        self.connection.session_manager.stdin_write(disable_prompt_cmd)

        self.connection.session_manager.wait_for_match(
            label="DISABLE PROMPT", cmd=disable_prompt_cmd, match=disable_prompt_reply.search
        )

    def ensure_ssm_session_has_started(self) -> None:
        """Ensure the SSM session has started on the host. We poll stdout
        until we match the following string 'Starting session with SessionId'
        """
        self.connection.session_manager.wait_for_match(
            label="START SSM SESSION", cmd="start_session", match="Starting session with SessionId"
        )
