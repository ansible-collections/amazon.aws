# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import base64
from unittest.mock import MagicMock
from unittest.mock import call

import pytest

from ansible_collections.amazon.aws.plugins.plugin_utils.ssm.windows_executor import WindowsCommandExecutor


@pytest.fixture(name="mock_dependencies")
def fixture_mock_dependencies():
    """Create mock dependencies for WindowsCommandExecutor."""
    return {
        "s3_client": MagicMock(name="s3_client"),
        "s3_manager": MagicMock(name="s3_manager"),
        "session_manager": MagicMock(name="session_manager"),
        "exec_communicate": MagicMock(name="exec_communicate", return_value=(0, "output", "")),
        "instance_id": "i-1234567890abcdef0",
        "bucket_name": "test-bucket",
        "verbosity_display": MagicMock(name="verbosity_display"),
    }


@pytest.fixture(name="executor")
def fixture_executor(mock_dependencies):
    """Create a WindowsCommandExecutor instance with mocked dependencies."""
    return WindowsCommandExecutor(**mock_dependencies)


class TestWindowsCommandExecutor:
    def test_init(self, mock_dependencies):
        """Test WindowsCommandExecutor initialisation."""
        executor = WindowsCommandExecutor(**mock_dependencies)
        assert executor._s3_client == mock_dependencies["s3_client"]
        assert executor._s3_manager == mock_dependencies["s3_manager"]
        assert executor._session_manager == mock_dependencies["session_manager"]
        assert executor._exec_communicate == mock_dependencies["exec_communicate"]
        assert executor._instance_id == mock_dependencies["instance_id"]
        assert executor._bucket_name == mock_dependencies["bucket_name"]
        assert executor._verbosity_display == mock_dependencies["verbosity_display"]

    def test_decode_powershell_command_no_encoding(self, executor):
        """Test _decode_powershell_command with plain PowerShell script."""
        cmd = "Write-Host 'Hello World'"
        result = executor._decode_powershell_command(cmd)
        assert result == cmd

    def test_decode_powershell_command_with_encoding(self, executor):
        """Test _decode_powershell_command with -EncodedCommand."""
        # Create a base64-encoded UTF-16LE PowerShell command
        script = "Write-Host 'Test'"
        encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        cmd = f"powershell -EncodedCommand {encoded}"

        result = executor._decode_powershell_command(cmd)
        assert result == script

    def test_decode_powershell_command_with_encoding_quoted(self, executor):
        """Test _decode_powershell_command with quoted -EncodedCommand."""
        script = "Get-Process"
        encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        cmd = f"powershell -EncodedCommand '{encoded}'"

        result = executor._decode_powershell_command(cmd)
        assert result == script

    def test_decode_powershell_command_invalid_encoding(self, executor):
        """Test _decode_powershell_command with invalid base64."""
        cmd = "powershell -EncodedCommand INVALID!!!"
        result = executor._decode_powershell_command(cmd)
        # Should fall back to original command
        assert result == cmd

    def test_upload_script_to_s3(self, executor, mock_dependencies):
        """Test _upload_script_to_s3 uploads script and returns presigned URL."""
        script = "Write-Host 'Test Script'"
        s3_key = "i-1234567890abcdef0/commands/test-uuid.ps1"
        expected_url = "https://test-bucket.s3.amazonaws.com/presigned-url"

        mock_dependencies["s3_manager"].get_url.return_value = expected_url

        result = executor._upload_script_to_s3(s3_key, script)

        # Verify S3 upload
        mock_dependencies["s3_client"].put_object.assert_called_once()
        call_kwargs = mock_dependencies["s3_client"].put_object.call_args[1]
        assert call_kwargs["Bucket"] == "test-bucket"
        assert call_kwargs["Key"] == s3_key
        assert call_kwargs["ContentType"] == "text/plain; charset=utf-8"

        # Verify presigned URL generation
        mock_dependencies["s3_manager"].get_url.assert_called_once_with("get_object", "test-bucket", s3_key, "GET")
        assert result == expected_url

    def test_upload_stdin_to_s3(self, executor, mock_dependencies):
        """Test _upload_stdin_to_s3 uploads stdin data and returns presigned URL."""
        stdin_data = b"test input data"
        stdin_key = "i-1234567890abcdef0/commands/test-uuid-stdin.txt"
        expected_url = "https://test-bucket.s3.amazonaws.com/presigned-stdin-url"

        mock_dependencies["s3_manager"].get_url.return_value = expected_url

        result = executor._upload_stdin_to_s3(stdin_key, stdin_data)

        # Verify S3 upload
        mock_dependencies["s3_client"].put_object.assert_called_once()
        call_kwargs = mock_dependencies["s3_client"].put_object.call_args[1]
        assert call_kwargs["Bucket"] == "test-bucket"
        assert call_kwargs["Key"] == stdin_key
        assert call_kwargs["Body"] == stdin_data
        assert call_kwargs["ContentType"] == "text/plain; charset=utf-8"

        # Verify presigned URL generation
        mock_dependencies["s3_manager"].get_url.assert_called_once_with("get_object", "test-bucket", stdin_key, "GET")
        assert result == expected_url

    def test_generate_wrapper_without_stdin(self, executor):
        """Test _generate_wrapper_without_stdin generates correct PowerShell wrapper."""
        presigned_url = "https://s3.example.com/script.ps1"
        mark_begin = "BEGIN_MARKER"
        mark_end = "END_MARKER"

        result = executor._generate_wrapper_without_stdin(presigned_url, mark_begin, mark_end)

        # Verify wrapper structure
        assert "$wc=[System.Net.WebClient]::new()" in result
        assert "$wc.Encoding=[System.Text.Encoding]::UTF8" in result
        assert f"$s=$wc.DownloadString('{presigned_url}')" in result
        assert "$wc.Dispose()" in result
        assert "$t=[System.IO.Path]::GetTempFileName()" in result
        assert "[System.IO.File]::WriteAllText($t,$s,[System.Text.Encoding]::UTF8)" in result
        assert f"echo '{mark_begin}'" in result
        assert "powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $t" in result
        assert "$e=$LASTEXITCODE" in result
        assert f"echo '{mark_end}'" in result
        assert "try {" in result
        assert "} catch {" in result

    def test_generate_wrapper_with_stdin(self, executor):
        """Test _generate_wrapper_with_stdin generates correct PowerShell wrapper."""
        presigned_url = "https://s3.example.com/script.ps1"
        stdin_url = "https://s3.example.com/stdin.txt"
        mark_begin = "BEGIN_MARKER"
        mark_end = "END_MARKER"

        result = executor._generate_wrapper_with_stdin(presigned_url, stdin_url, mark_begin, mark_end)

        # Verify wrapper structure includes both URLs
        assert "$wc=[System.Net.WebClient]::new()" in result
        assert "$wc.Encoding=[System.Text.Encoding]::UTF8" in result
        assert f"$s=$wc.DownloadString('{presigned_url}')" in result
        assert f"$i=$wc.DownloadString('{stdin_url}')" in result
        assert "$wc.Dispose()" in result
        assert "[System.IO.File]::WriteAllText($t,$s,[System.Text.Encoding]::UTF8)" in result
        assert f"echo '{mark_begin}'" in result
        # Verify stdin is piped to PowerShell
        assert '($i -split "`r?`n") | powershell' in result
        assert "$e=$LASTEXITCODE" in result
        assert f"echo '{mark_end}'" in result

    def test_execute_wrapper(self, executor, mock_dependencies):
        """Test _execute_wrapper sends wrapper to session and calls exec_communicate."""
        wrapper = "powershell -Command Write-Host 'Test'"
        mark_begin = "BEGIN"
        mark_end = "END"
        expected_result = (0, "test output", "")

        mock_dependencies["exec_communicate"].return_value = expected_result

        result = executor._execute_wrapper(wrapper, mark_begin, mark_end)

        # Verify wrapper was written to session stdin
        mock_dependencies["session_manager"].stdin_write.assert_called_once()
        written_data = mock_dependencies["session_manager"].stdin_write.call_args[0][0]
        assert wrapper in written_data.decode("utf-8")

        # Verify exec_communicate was called with wrapper and None for stdin (wrapper handles it)
        mock_dependencies["exec_communicate"].assert_called_once_with(wrapper, None, mark_begin, mark_end)

        assert result == expected_result

    def test_cleanup_s3_objects_script_only(self, executor, mock_dependencies):
        """Test _cleanup_s3_objects removes script object."""
        s3_key = "i-1234567890abcdef0/commands/test.ps1"
        stdin_key = None

        executor._cleanup_s3_objects(s3_key, stdin_key)

        # Verify script was deleted
        mock_dependencies["s3_client"].delete_object.assert_called_once_with(Bucket="test-bucket", Key=s3_key)

    def test_cleanup_s3_objects_with_stdin(self, executor, mock_dependencies):
        """Test _cleanup_s3_objects removes both script and stdin objects."""
        s3_key = "i-1234567890abcdef0/commands/test.ps1"
        stdin_key = "i-1234567890abcdef0/commands/test-stdin.txt"

        executor._cleanup_s3_objects(s3_key, stdin_key)

        # Verify both objects were deleted
        assert mock_dependencies["s3_client"].delete_object.call_count == 2
        mock_dependencies["s3_client"].delete_object.assert_has_calls(
            [call(Bucket="test-bucket", Key=s3_key), call(Bucket="test-bucket", Key=stdin_key)], any_order=True
        )

    def test_cleanup_s3_objects_handles_exceptions(self, executor, mock_dependencies):
        """Test _cleanup_s3_objects handles S3 deletion errors gracefully."""
        s3_key = "i-1234567890abcdef0/commands/test.ps1"
        stdin_key = None

        # Make delete_object raise an exception
        mock_dependencies["s3_client"].delete_object.side_effect = Exception("S3 error")

        # Should not raise exception
        executor._cleanup_s3_objects(s3_key, stdin_key)

        # Verify error was logged
        mock_dependencies["verbosity_display"].assert_any_call(
            3, "EXEC_VIA_S3: Failed to clean up S3 objects: S3 error"
        )

    def test_execute_integration_no_stdin(self, executor, mock_dependencies):
        """Test execute() full flow without stdin."""
        cmd = "Write-Host 'Hello'"
        mark_begin = "BEGIN_TEST"
        mark_end = "END_TEST"
        expected_output = (0, "Hello\n", "")

        # Mock S3 manager to return presigned URL
        mock_dependencies["s3_manager"].get_url.return_value = "https://s3.example.com/script.ps1"
        mock_dependencies["exec_communicate"].return_value = expected_output

        result = executor.execute(cmd, None, mark_begin, mark_end)

        # Verify script was uploaded to S3
        assert mock_dependencies["s3_client"].put_object.call_count == 1

        # Verify exec_communicate was called
        mock_dependencies["exec_communicate"].assert_called_once()

        # Verify cleanup happened
        assert mock_dependencies["s3_client"].delete_object.call_count == 1

        assert result == expected_output

    def test_execute_integration_with_stdin(self, executor, mock_dependencies):
        """Test execute() full flow with stdin data."""
        cmd = "Write-Host 'Process input'"
        in_data = b"input line 1\ninput line 2"
        mark_begin = "BEGIN_TEST"
        mark_end = "END_TEST"
        expected_output = (0, "Processed\n", "")

        # Mock S3 manager to return presigned URLs
        mock_dependencies["s3_manager"].get_url.side_effect = [
            "https://s3.example.com/script.ps1",
            "https://s3.example.com/stdin.txt",
        ]
        mock_dependencies["exec_communicate"].return_value = expected_output

        result = executor.execute(cmd, in_data, mark_begin, mark_end)

        # Verify script and stdin were uploaded to S3
        assert mock_dependencies["s3_client"].put_object.call_count == 2

        # Verify two presigned URLs were generated
        assert mock_dependencies["s3_manager"].get_url.call_count == 2

        # Verify cleanup happened for both objects
        assert mock_dependencies["s3_client"].delete_object.call_count == 2

        assert result == expected_output

    def test_execute_with_encoded_command(self, executor, mock_dependencies):
        """Test execute() decodes -EncodedCommand before uploading."""
        script = "Get-Date"
        encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        cmd = f"powershell -EncodedCommand {encoded}"
        mark_begin = "BEGIN"
        mark_end = "END"

        mock_dependencies["s3_manager"].get_url.return_value = "https://s3.example.com/script.ps1"
        mock_dependencies["exec_communicate"].return_value = (0, "2026-03-19", "")

        executor.execute(cmd, None, mark_begin, mark_end)

        # Verify the uploaded script is the decoded version
        uploaded_body = mock_dependencies["s3_client"].put_object.call_args[1]["Body"]
        # Should be the decoded script "Get-Date", not the encoded command line
        assert b"Get-Date" in uploaded_body
        assert b"EncodedCommand" not in uploaded_body
