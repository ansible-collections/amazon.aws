# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import random
import re
import string
import time

try:
    # ansible-core >= 2.21
    from ansible._internal._powershell import _script

    HAS_MODERN_PWSH = True
except ImportError:
    # ansible-core < 2.21 fallback
    HAS_MODERN_PWSH = False
    import base64

    _script = None  # For type checking

from ansible.module_utils._text import to_bytes
from ansible.module_utils._text import to_text


class TerminalManager:
    def __init__(self, connection):
        """
        Initialise the TerminalManager.

        :param connection: The AWS SSM connection object
        """
        self.connection = connection

    def generate_marker(self) -> str:
        return "".join(  # nosec B311 - markers for output parsing, not security
            [random.choice(string.ascii_letters) for i in range(self.connection.MARK_LENGTH)]
        )

    def prestage_windows_command_executor(self) -> None:
        """Pre-stage a PowerShell function to execute commands from stdin.

        This avoids PTY echo issues by reading the command itself from stdin
        rather than sending it through the terminal. The function also supports
        reading additional stdin data for the command if needed.

        Uses extremely compressed syntax to minimize PTY echo delays.
        Does NOT wait for confirmation - the prestage command will be echoed
        slowly by the PTY, but we proceed immediately. If the function fails
        to load, the first actual command will fail.
        """
        # Compressed function that:
        # 1. Reads command from stdin (until EOF delimiter \0\0\0\0)
        # 2. Optionally reads stdin data for command (until second EOF delimiter)
        # 3. Executes command, piping stdin if provided
        # 4. Returns output wrapped in markers
        # Variable names: $b=BeginMark, $e=EndMark, $h=HasStdin, $c=cmd, $l=line, $t=cmdText, $d=stdinData
        command = (
            "function i($b,$e,$h){"
            "$c=@();"
            'while(($l=[Console]::In.ReadLine())-and($l-ne"`0`0`0`0")){$c+=$l};'
            '$t=$c-join"`n";'
            "echo $b;"
            "if($h){"
            "$d=@();"
            'while(($l=[Console]::In.ReadLine())-and($l-ne"`0`0`0`0")){$d+=$l};'
            "$d|iex $t"
            "}else{"
            "iex $t"
            "};"
            "echo '';"
            "echo $LASTEXITCODE;"
            "echo $e"
            "}\n"
        )

        prestage_cmd = to_bytes(command, errors="surrogate_or_strict")
        self.connection.verbosity_display(3, "PRESTAGE CMD EXEC: Sending compressed stdin helper function 'i'")
        self.connection.verbosity_display(4, f"PRESTAGE CMD EXEC: Command length: {len(prestage_cmd)} bytes")
        self.connection.verbosity_display(5, f"PRESTAGE CMD EXEC: Command:\n{to_text(prestage_cmd)}")
        self.connection.verbosity_display(
            3,
            "PRESTAGE CMD EXEC: Not waiting for confirmation (PTY echo too slow) - will fail on first command if load failed",
        )

        # Send command without waiting for completion
        # The PTY will echo this slowly, but PowerShell will eventually execute it
        # If it fails to load, the first actual command will error
        self.connection.session_manager.stdin_write(prestage_cmd)

        # Give PowerShell a moment to process the function definition
        # This is a compromise - we can't wait for confirmation due to PTY echo,
        # but we also can't proceed instantly or the function won't be ready
        time.sleep(2)
        self.connection.verbosity_display(3, "PRESTAGE CMD EXEC: Proceeding without confirmation")

    def prepare_windows(self) -> None:
        self.disable_windows_echo_command()
        self.disable_windows_prompt_command()
        self.prestage_windows_command_executor()
        self.connection.verbosity_display(3, "PRE (windows) Terminal configured")

    def prepare_default(self) -> None:
        # Ensure SSM Session has started
        self.ensure_ssm_session_has_started()
        # Disable echo command
        self.disable_echo_command()
        # Disable prompt command
        self.disable_prompt_command()
        self.connection.verbosity_display(3, "PRE (default) Terminal configured")

    def prepare_terminal(self) -> None:
        """perform any one-time terminal settings"""
        if self.connection.is_windows:
            self.prepare_windows()
        else:
            self.prepare_default()

    def _encode_powershell_command(self, script: str, disable_input: bool = False) -> str:
        """Encode a PowerShell script using the appropriate method for the Ansible version.

        :param script: The PowerShell script to encode.
        :param disable_input: Whether to disable stdin (only supported in modern versions).
        :returns: The encoded PowerShell command line.
        """
        self.connection.verbosity_display(
            6, f"ENCODE_PWSH: Script length: {len(script)} chars, disable_input={disable_input}"
        )
        if HAS_MODERN_PWSH:
            # Use modern API (ansible-core >= 2.21)
            self.connection.verbosity_display(5, "ENCODE_PWSH: Using modern _script.get_pwsh_encoded_cmdline() API")
            self.connection.verbosity_display(6, f"ENCODE_PWSH: Input script:\n{script}")
            cmd_parts = _script.get_pwsh_encoded_cmdline(
                script,
                override_execution_policy=True,
                disable_input=disable_input,
            )
            result = " ".join(cmd_parts)
            self.connection.verbosity_display(5, f"ENCODE_PWSH: Result length: {len(result)} chars")
            self.connection.verbosity_display(6, f"ENCODE_PWSH: Result command:\n{result}")
            return result
        else:
            # Fallback for ansible-core < 2.21
            self.connection.verbosity_display(5, "ENCODE_PWSH: Using legacy base64 encoding (ansible-core < 2.21)")
            self.connection.verbosity_display(6, f"ENCODE_PWSH: Input script:\n{script}")
            # Encode script to base64 UTF-16LE
            script_bytes = to_bytes(script, encoding="utf-16-le")
            encoded_script = base64.b64encode(script_bytes).decode("ascii")
            self.connection.verbosity_display(6, f"ENCODE_PWSH: Base64 length: {len(encoded_script)} chars")

            # Build command line (mimics _common_args from powershell.py)
            # Note: Legacy method doesn't support disable_input parameter
            if disable_input:
                self.connection.verbosity_display(
                    5, "ENCODE_PWSH: WARNING - disable_input not supported in legacy mode, ignoring"
                )
            result = (
                f"powershell -NoProfile -NonInteractive -ExecutionPolicy Unrestricted -EncodedCommand {encoded_script}"
            )
            self.connection.verbosity_display(5, f"ENCODE_PWSH: Result length: {len(result)} chars")
            self.connection.verbosity_display(6, f"ENCODE_PWSH: Result command:\n{result}")
            return result

    def wrap_command(self, cmd: str, mark_begin: str, mark_end: str, has_stdin: bool = False) -> tuple[str, str]:
        """Wrap command so stdout and status can be extracted.

        For Windows: Returns a trigger command that invokes the pre-staged executor.
                     The actual command is returned separately to be sent via stdin.
        For Linux: Returns the wrapped command inline (original behavior).

        :param cmd: The command to wrap.
        :param mark_begin: The begin marker.
        :param mark_end: The end marker.
        :param has_stdin: Whether stdin data will be sent to this command.
        :returns: Tuple of (trigger_command, actual_command_for_stdin).
                  For Linux, actual_command_for_stdin will be empty string.
        """

        if self.connection.is_windows:
            # Windows: Use pre-staged helper function 'i'
            # The trigger is just the function call - command is sent via stdin
            has_stdin_str = "$true" if has_stdin else "$false"
            trigger_cmd = f"i '{mark_begin}' '{mark_end}' {has_stdin_str}\n"

            self.connection.verbosity_display(4, f"WRAP_COMMAND: Windows mode (has_stdin={has_stdin})")
            self.connection.verbosity_display(5, f"WRAP_COMMAND: Trigger command: {trigger_cmd.strip()}")
            self.connection.verbosity_display(5, f"WRAP_COMMAND: Command to send via stdin ({len(cmd)} bytes)")
            self.connection.verbosity_display(6, f"WRAP_COMMAND: Full command for stdin:\n{to_text(cmd)}")

            return (trigger_cmd, cmd)
        else:
            # Linux/Unix: use existing inline approach
            self.connection.verbosity_display(4, "WRAP_COMMAND: Linux/Unix mode - wrapping command")
            self.connection.verbosity_display(5, f"WRAP_COMMAND: Original command: {to_text(cmd)[:200]}...")
            self.connection.verbosity_display(5, f"WRAP_COMMAND: Original command length: {len(cmd)} bytes")
            self.connection.verbosity_display(6, f"WRAP_COMMAND: Full original command:\n{to_text(cmd)}")
            wrapped_cmd = (
                f"printf '%s\\n' '{mark_begin}' ;\n"
                f"echo | {cmd} ;\n"
                f"printf '\\n%s\\n%s\\n' \"$?\" '{mark_end}' ;\n"
            )  # fmt: skip
            self.connection.verbosity_display(5, f"WRAP_COMMAND: Wrapped command length: {len(wrapped_cmd)} bytes")
            self.connection.verbosity_display(5, f"WRAP_COMMAND: Begin marker: {mark_begin}")
            self.connection.verbosity_display(5, f"WRAP_COMMAND: End marker: {mark_end}")
            self.connection.verbosity_display(6, f"WRAP_COMMAND: Full wrapped command:\n{to_text(wrapped_cmd)}")

            return (wrapped_cmd, "")

    def disable_echo_command(self) -> None:
        """Disable terminal echo on Linux/Unix using stty.

        This prevents commands from being echoed back, which improves output
        parsing and prevents sensitive data from appearing in logs.
        """
        disable_echo_cmd = to_bytes("stty -echo\n", errors="surrogate_or_strict")

        # Send command
        self.connection.verbosity_display(3, "DISABLE ECHO: Disabling terminal echo using stty")
        self.connection.verbosity_display(4, f"DISABLE ECHO Command: {to_text(disable_echo_cmd).strip()}")
        self.connection.verbosity_display(5, f"DISABLE ECHO Command bytes: {len(disable_echo_cmd)} bytes")
        self.connection.session_manager.stdin_write(disable_echo_cmd)

        self.connection.session_manager.wait_for_match(
            label="DISABLE ECHO", cmd=disable_echo_cmd, match="stty -echo", is_windows=self.connection.is_windows
        )
        self.connection.verbosity_display(3, "DISABLE ECHO: Terminal echo disabled")

    def disable_windows_echo_command(self) -> None:
        """Disable command echo in PowerShell.

        Disables both PSReadLine (syntax highlighting) and Windows Console echo.
        PSReadLine provides interactive features including command echo with syntax
        highlighting. The Windows Console also echoes input via ENABLE_ECHO_INPUT flag.
        """
        end_mark = self.generate_marker()
        # Remove PSReadLine and disable console echo via Windows API
        # This is equivalent to 'stty -echo' on Linux
        command = (
            "Remove-Module PSReadLine -ErrorAction SilentlyContinue ; "
            # Define P/Invoke for kernel32 console functions
            "Add-Type -TypeDefinition @'\n"
            "using System;\n"
            "using System.Runtime.InteropServices;\n"
            "public class ConsoleHelper {\n"
            '    [DllImport("kernel32.dll", SetLastError = true)]\n'
            "    public static extern IntPtr GetStdHandle(int nStdHandle);\n"
            '    [DllImport("kernel32.dll", SetLastError = true)]\n'
            "    public static extern bool GetConsoleMode(IntPtr hConsoleHandle, out uint lpMode);\n"
            '    [DllImport("kernel32.dll", SetLastError = true)]\n'
            "    public static extern bool SetConsoleMode(IntPtr hConsoleHandle, uint dwMode);\n"
            "    public const int STD_INPUT_HANDLE = -10;\n"
            "    public const uint ENABLE_ECHO_INPUT = 0x0004;\n"
            "}\n"
            "'@ -ErrorAction SilentlyContinue ; "
            # Disable echo on stdin
            "$h = [ConsoleHelper]::GetStdHandle([ConsoleHelper]::STD_INPUT_HANDLE) ; "
            "$mode = [uint32]0 ; "
            "[void][ConsoleHelper]::GetConsoleMode($h, [ref]$mode) ; "
            "$mode = $mode -band (-bnot [ConsoleHelper]::ENABLE_ECHO_INPUT) ; "
            "[void][ConsoleHelper]::SetConsoleMode($h, $mode) ; "
            f"echo {end_mark}\n"
        )
        disable_echo_cmd = to_bytes(command, errors="surrogate_or_strict")
        end_marker_rex = f"^{re.escape(end_mark)}$"
        self.connection.verbosity_display(3, "DISABLE WIN ECHO: Disabling PSReadLine and Windows Console echo")
        self.connection.verbosity_display(4, f"DISABLE WIN ECHO End marker text: {end_mark}")
        self.connection.verbosity_display(4, f"DISABLE WIN ECHO End marker RegEx: \n{end_marker_rex}")
        disable_echo_reply = re.compile(end_marker_rex, re.MULTILINE)

        # Send command
        self.connection.verbosity_display(4, f"DISABLE WIN ECHO Command text: \n{to_text(disable_echo_cmd)}")
        self.connection.verbosity_display(4, f"DISABLE WIN ECHO Sending {len(disable_echo_cmd)} bytes")
        self.connection.session_manager.stdin_write(disable_echo_cmd)

        self.connection.session_manager.wait_for_match(
            label="DISABLE WIN ECHO", cmd=disable_echo_cmd, match=disable_echo_reply.search, is_windows=True
        )
        self.connection.verbosity_display(3, "DISABLE WIN ECHO: PSReadLine removed and Console echo disabled")

    def disable_windows_prompt_command(self) -> None:
        """Disable prompt in PowerShell by setting it to empty string.

        This mirrors the Linux behavior where PS1='' sets an empty prompt.
        """
        end_mark = self.generate_marker()
        command = f'function prompt {{ "" }} ; echo {end_mark}\n'
        disable_prompt_cmd = to_bytes(command, errors="surrogate_or_strict")
        end_marker_rex = f"^{re.escape(end_mark)}$"
        self.connection.verbosity_display(4, f"DISABLE WIN PROMPT End marker text: {end_mark}")
        self.connection.verbosity_display(4, f"DISABLE WIN PROMPT End marker RegEx: \n{end_marker_rex}")
        disable_prompt_reply = re.compile(end_marker_rex, re.MULTILINE)

        # Send command
        self.connection.verbosity_display(4, f"DISABLE WIN PROMPT Command text: \n{to_text(disable_prompt_cmd)}")
        self.connection.verbosity_display(4, f"DISABLE WIN PROMPT Sending {len(disable_prompt_cmd)} bytes")
        self.connection.session_manager.stdin_write(disable_prompt_cmd)

        self.connection.session_manager.wait_for_match(
            label="DISABLE WIN PROMPT", cmd=disable_prompt_cmd, match=disable_prompt_reply.search, is_windows=True
        )

    def disable_prompt_command(self) -> None:
        """Disable prompt on Linux/Unix by setting PS1 to empty string.

        This mirrors the Windows behavior of setting an empty prompt function.
        Also disables bracketed paste mode which can interfere with output parsing.
        """
        end_mark = self.generate_marker()
        command = (
            "PS1='' ; "
            "bind 'set enable-bracketed-paste off'; "
            f"printf '\\n%s\\n' '{end_mark}'\n"
        )  # fmt: skip
        disable_prompt_cmd = to_bytes(command, errors="surrogate_or_strict")
        disable_prompt_reply = re.compile(r"\r\r\n" + re.escape(end_mark) + r"\r\r\n", re.MULTILINE)

        # Send command
        self.connection.verbosity_display(
            3, "DISABLE PROMPT: Setting empty prompt (PS1='') and disabling bracketed paste"
        )
        self.connection.verbosity_display(4, f"DISABLE PROMPT End marker: {end_mark}")
        self.connection.verbosity_display(5, f"DISABLE PROMPT Command: {to_text(disable_prompt_cmd).strip()}")
        self.connection.session_manager.stdin_write(disable_prompt_cmd)

        self.connection.session_manager.wait_for_match(
            label="DISABLE PROMPT", cmd=disable_prompt_cmd, match=disable_prompt_reply.search, is_windows=False
        )
        self.connection.verbosity_display(3, "DISABLE PROMPT: Prompt disabled")

    def ensure_ssm_session_has_started(self) -> None:
        """Ensure the SSM session has started on the host.

        Polls stdout until we match 'Starting session with SessionId' which
        indicates the session-manager-plugin has successfully connected.
        """
        self.connection.verbosity_display(3, "START SSM SESSION: Waiting for session to start")
        self.connection.verbosity_display(4, "START SSM SESSION: Looking for 'Starting session with SessionId' message")
        self.connection.session_manager.wait_for_match(
            label="START SSM SESSION",
            cmd="start_session",
            match="Starting session with SessionId",
            is_windows=self.connection.is_windows,
        )
        self.connection.verbosity_display(3, "START SSM SESSION: Session started successfully")
