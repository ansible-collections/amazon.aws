# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Windows command execution via S3 for AWS SSM connections.

This module provides S3-based command execution to avoid PTY echo timeouts on Windows.
The PTY echoes ALL stdin data to stdout before PowerShell can read it, causing timeouts
on large commands. This approach keeps the session command tiny by uploading the actual
command to S3 and executing a small wrapper that downloads and runs it.
"""

from __future__ import annotations

import base64
import re
import typing
import uuid

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Callable
    from typing import Optional

from ansible.module_utils._text import to_bytes
from ansible.module_utils._text import to_text


class WindowsCommandExecutor:
    """Executes Windows PowerShell commands via S3 upload/download to avoid PTY echo issues."""

    def __init__(
        self,
        s3_client: Any,
        s3_manager: Any,
        session_manager: Any,
        exec_communicate: Callable,
        instance_id: str,
        bucket_name: str,
        verbosity_display: Callable[[int, str], None],
    ) -> None:
        """
        Initialise the WindowsCommandExecutor.

        :param s3_client: Boto3 S3 client for uploading/deleting objects
        :param s3_manager: S3ClientManager for generating presigned URLs
        :param session_manager: SSMSessionManager for writing to session stdin
        :param exec_communicate: Connection's exec_communicate method for executing commands
        :param instance_id: EC2 instance ID (used for S3 key prefixes)
        :param bucket_name: S3 bucket name for temporary command storage
        :param verbosity_display: Function for logging at different verbosity levels
        """
        self._s3_client = s3_client
        self._s3_manager = s3_manager
        self._session_manager = session_manager
        self._exec_communicate = exec_communicate
        self._instance_id = instance_id
        self._bucket_name = bucket_name
        self._verbosity_display = verbosity_display

    def execute(self, cmd: str, in_data: Optional[bytes], mark_begin: str, mark_end: str) -> tuple[int, str, str]:
        """
        Execute a Windows command by uploading to S3 and downloading via tiny wrapper command.

        This avoids PTY echo timeouts by keeping the session command tiny (~100 bytes)
        while the actual command (which may be kilobytes) is retrieved from S3.

        :param cmd: The PowerShell command to execute (may be encoded command line).
        :param in_data: Optional stdin data for the command.
        :param mark_begin: The begin marker for output parsing.
        :param mark_end: The end marker for output parsing.
        :returns: A tuple of (exit_code, stdout, stderr).
        """
        # Generate unique S3 key for this command
        command_id = str(uuid.uuid4())
        s3_key = f"{self._instance_id}/commands/{command_id}.ps1"
        stdin_key = None  # Initialize for cleanup scope

        self._verbosity_display(3, f"EXEC_VIA_S3: Uploading command to s3://{self._bucket_name}/{s3_key}")
        self._verbosity_display(4, f"EXEC_VIA_S3: Command length: {len(cmd)} bytes")

        # DEBUG: Show command encoding details (level 6 for long-term debugging of encoding issues)
        cmd_str = to_text(cmd)
        self._verbosity_display(6, f"EXEC_VIA_S3: Command (str): {repr(cmd_str[:200])}")
        if isinstance(cmd, bytes):
            self._verbosity_display(6, f"EXEC_VIA_S3: Command (bytes): {cmd[:200]}")
        self._verbosity_display(6, f"EXEC_VIA_S3: Command content:\n{cmd_str}")

        # Extract PowerShell script from -EncodedCommand if present
        script_to_upload = self._decode_powershell_command(cmd_str)

        try:
            # Upload script to S3
            presigned_url = self._upload_script_to_s3(s3_key, script_to_upload)

            # Handle stdin data if present
            if in_data:
                stdin_key = f"{self._instance_id}/commands/{command_id}-stdin.txt"
                stdin_url = self._upload_stdin_to_s3(stdin_key, in_data)
                wrapper = self._generate_wrapper_with_stdin(presigned_url, stdin_url, mark_begin, mark_end)
            else:
                wrapper = self._generate_wrapper_without_stdin(presigned_url, mark_begin, mark_end)

            # Execute wrapper command
            result = self._execute_wrapper(wrapper, mark_begin, mark_end)

            self._verbosity_display(3, f"EXEC_VIA_S3: Command execution complete, returncode={result[0]}")
            self._verbosity_display(6, f"EXEC_VIA_S3: Stdout (str): {repr(result[1][:200])}")
            self._verbosity_display(6, f"EXEC_VIA_S3: Stderr (str): {repr(result[2][:200])}")
            self._verbosity_display(6, f"EXEC_VIA_S3: Stdout type: {type(result[1])}, length: {len(result[1])}")
            self._verbosity_display(6, f"EXEC_VIA_S3: Stderr type: {type(result[2])}, length: {len(result[2])}")
            return result

        finally:
            # Clean up S3 objects
            self._cleanup_s3_objects(s3_key, stdin_key)

    def _decode_powershell_command(self, cmd_str: str) -> str:
        """
        Extract PowerShell script from -EncodedCommand if present.

        The wrapper expects PowerShell script code, not a command line with -EncodedCommand.
        If the command is a PowerShell command line with -EncodedCommand, decode it to get
        the actual script.

        :param cmd_str: The command string to check for -EncodedCommand
        :returns: Either the decoded PowerShell script or the original command
        """
        script_to_upload = cmd_str
        encoded_match = re.search(r'-EncodedCommand\s+["\']?([A-Za-z0-9+/=]+)["\']?', cmd_str)

        if encoded_match:
            self._verbosity_display(4, "EXEC_VIA_S3: Detected -EncodedCommand, decoding to extract PowerShell script")
            try:
                # Extract and decode the base64-encoded UTF-16LE PowerShell script
                encoded_script = encoded_match.group(1)
                self._verbosity_display(5, f"EXEC_VIA_S3: Base64 length: {len(encoded_script)} chars")
                script_bytes = base64.b64decode(encoded_script)
                script_to_upload = script_bytes.decode("utf-16-le")
                self._verbosity_display(4, f"EXEC_VIA_S3: Decoded script length: {len(script_to_upload)} chars")
                self._verbosity_display(6, f"EXEC_VIA_S3: Decoded script:\n{script_to_upload}")
            except Exception as e:
                self._verbosity_display(
                    3, f"EXEC_VIA_S3: WARNING - Failed to decode -EncodedCommand, uploading as-is: {e}"
                )
                # Fall back to uploading the command line as-is
                script_to_upload = cmd_str

        return script_to_upload

    def _upload_script_to_s3(self, s3_key: str, script: str) -> str:
        """
        Upload PowerShell script to S3 and return presigned URL.

        :param s3_key: S3 key for the script object
        :param script: PowerShell script content to upload
        :returns: Presigned URL for downloading the script
        """
        script_bytes = to_bytes(script, errors="surrogate_or_strict")
        self._verbosity_display(6, f"EXEC_VIA_S3: Script to upload (str): {repr(to_text(script)[:200])}")
        self._verbosity_display(6, f"EXEC_VIA_S3: Script to upload (bytes): {script_bytes[:200]}")

        # Upload with UTF-8 content type so PowerShell recognizes it as text
        self._s3_client.put_object(
            Bucket=self._bucket_name,
            Key=s3_key,
            Body=script_bytes,
            ContentType="text/plain; charset=utf-8",
        )
        self._verbosity_display(4, f"EXEC_VIA_S3: Uploaded {len(script_bytes)} bytes to S3")

        # Generate presigned URL (1 hour expiry)
        presigned_url = self._s3_manager.get_url("get_object", self._bucket_name, s3_key, "GET")

        self._verbosity_display(4, f"EXEC_VIA_S3: Generated presigned URL (length: {len(presigned_url)})")
        self._verbosity_display(6, f"EXEC_VIA_S3: Presigned URL: {presigned_url}")

        return presigned_url

    def _upload_stdin_to_s3(self, stdin_key: str, in_data: bytes) -> str:
        """
        Upload stdin data to S3 and return presigned URL.

        :param stdin_key: S3 key for the stdin object
        :param in_data: Stdin data to upload
        :returns: Presigned URL for downloading the stdin data
        """
        self._verbosity_display(3, f"EXEC_VIA_S3: Uploading stdin data to s3://{self._bucket_name}/{stdin_key}")
        self._verbosity_display(4, f"EXEC_VIA_S3: Stdin data length: {len(in_data)} bytes")
        self._verbosity_display(6, f"EXEC_VIA_S3: Stdin data (bytes): {in_data[:200]}")
        self._verbosity_display(
            6,
            f"EXEC_VIA_S3: Stdin data (decoded): {repr(to_text(in_data, errors='surrogate_or_strict')[:200])}",
        )

        self._s3_client.put_object(
            Bucket=self._bucket_name,
            Key=stdin_key,
            Body=in_data,
            ContentType="text/plain; charset=utf-8",
        )

        stdin_url = self._s3_manager.get_url("get_object", self._bucket_name, stdin_key, "GET")
        self._verbosity_display(4, f"EXEC_VIA_S3: Generated stdin presigned URL (length: {len(stdin_url)})")
        self._verbosity_display(6, f"EXEC_VIA_S3: Stdin presigned URL: {stdin_url}")

        return stdin_url

    def _generate_wrapper_with_stdin(self, presigned_url: str, stdin_url: str, mark_begin: str, mark_end: str) -> str:
        """
        Generate PowerShell wrapper that downloads script and stdin from S3, then executes.

        The wrapper:
        1. Downloads script and stdin using WebClient (with UTF-8 encoding)
        2. Saves script to temp file
        3. Pipes stdin lines to PowerShell executing the script file
        4. Captures and outputs the exit code

        :param presigned_url: Presigned URL for the script
        :param stdin_url: Presigned URL for stdin data
        :param mark_begin: Begin marker for output parsing
        :param mark_end: End marker for output parsing
        :returns: PowerShell wrapper command as string
        """
        # PowerShell: download script and stdin using WebClient (more reliable than Invoke-WebRequest)
        # See https://github.com/ansible-collections/amazon.aws/pull/2820
        # Set WebClient encoding to UTF-8 to correctly decode S3 content
        # Save script to temp file and execute as separate process to handle exit codes correctly
        # Scriptblocks don't set $LASTEXITCODE properly when they contain exit statements
        wrapper = (
            f"try {{ "
            f"$wc=[System.Net.WebClient]::new() ; "
            f"$wc.Encoding=[System.Text.Encoding]::UTF8 ; "
            f"$s=$wc.DownloadString('{presigned_url}') ; "
            f"$i=$wc.DownloadString('{stdin_url}') ; "
            f"$wc.Dispose() ; "
            f"$t=[System.IO.Path]::GetTempFileName() ; "
            f"$t=[System.IO.Path]::ChangeExtension($t,'.ps1') ; "
            f"[System.IO.File]::WriteAllText($t,$s,[System.Text.Encoding]::UTF8) ; "
            f"echo '{mark_begin}' ; "
            f'($i -split "`r?`n") | powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $t ; '
            f"$e=$LASTEXITCODE ; "
            f"Remove-Item -LiteralPath $t -Force -ErrorAction SilentlyContinue ; "
            f"echo '' ; echo $e ; echo '{mark_end}' "
            f"}} catch {{ "
            f"echo '{mark_begin}' ; echo \"S3_DOWNLOAD_ERROR: $_\" ; echo '' ; echo 99 ; echo '{mark_end}' "
            f"}}"
        )
        return wrapper

    def _generate_wrapper_without_stdin(self, presigned_url: str, mark_begin: str, mark_end: str) -> str:
        """
        Generate PowerShell wrapper that downloads script from S3 and executes (no stdin).

        The wrapper:
        1. Downloads script using WebClient (with UTF-8 encoding)
        2. Saves script to temp file
        3. Executes the script file in a new PowerShell process
        4. Captures and outputs the exit code

        :param presigned_url: Presigned URL for the script
        :param mark_begin: Begin marker for output parsing
        :param mark_end: End marker for output parsing
        :returns: PowerShell wrapper command as string
        """
        # No stdin: download script using WebClient and execute
        # See https://github.com/ansible-collections/amazon.aws/pull/2820
        # Set WebClient encoding to UTF-8 to correctly decode S3 content
        # Save script to temp file and execute as separate process to handle exit codes correctly
        # Scriptblocks don't set $LASTEXITCODE properly when they contain exit statements
        wrapper = (
            f"try {{ "
            f"$wc=[System.Net.WebClient]::new() ; "
            f"$wc.Encoding=[System.Text.Encoding]::UTF8 ; "
            f"$s=$wc.DownloadString('{presigned_url}') ; "
            f"$wc.Dispose() ; "
            f"$t=[System.IO.Path]::GetTempFileName() ; "
            f"$t=[System.IO.Path]::ChangeExtension($t,'.ps1') ; "
            f"[System.IO.File]::WriteAllText($t,$s,[System.Text.Encoding]::UTF8) ; "
            f"echo '{mark_begin}' ; "
            f"powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $t ; "
            f"$e=$LASTEXITCODE ; "
            f"Remove-Item -LiteralPath $t -Force -ErrorAction SilentlyContinue ; "
            f"echo '' ; echo $e ; echo '{mark_end}' "
            f"}} catch {{ "
            f"echo '{mark_begin}' ; echo \"S3_DOWNLOAD_ERROR: $_\" ; echo '' ; echo 99 ; echo '{mark_end}' "
            f"}}"
        )
        return wrapper

    def _execute_wrapper(self, wrapper: str, mark_begin: str, mark_end: str) -> tuple[int, str, str]:
        """
        Send wrapper command to session and execute via normal communicate flow.

        :param wrapper: PowerShell wrapper command to execute
        :param mark_begin: Begin marker for output parsing
        :param mark_end: End marker for output parsing
        :returns: Tuple of (exit_code, stdout, stderr)
        """
        self._verbosity_display(3, f"EXEC_VIA_S3: Wrapper command length: {len(wrapper)} bytes")
        self._verbosity_display(5, f"EXEC_VIA_S3: Wrapper command:\n{wrapper}")

        # Send wrapper command via session (tiny, won't timeout from echo)
        wrapper_bytes = to_bytes(wrapper + "\n", errors="surrogate_or_strict")
        self._verbosity_display(3, f"EXEC_VIA_S3: Sending wrapper command to session ({len(wrapper_bytes)} bytes)")
        self._session_manager.stdin_write(wrapper_bytes)

        # Execute via normal communicate flow (no stdin data since wrapper handles it)
        return self._exec_communicate(wrapper, None, mark_begin, mark_end)

    def _cleanup_s3_objects(self, s3_key: str, stdin_key: Optional[str]) -> None:
        """
        Clean up temporary S3 objects created for command execution.

        :param s3_key: S3 key for the script object
        :param stdin_key: Optional S3 key for stdin data object
        """
        try:
            self._verbosity_display(4, f"EXEC_VIA_S3: Cleaning up S3 object: {s3_key}")
            self._s3_client.delete_object(Bucket=self._bucket_name, Key=s3_key)
            if stdin_key is not None:
                self._verbosity_display(4, f"EXEC_VIA_S3: Cleaning up S3 stdin object: {stdin_key}")
                self._s3_client.delete_object(Bucket=self._bucket_name, Key=stdin_key)
        except Exception as e:
            self._verbosity_display(3, f"EXEC_VIA_S3: Failed to clean up S3 objects: {e}")
