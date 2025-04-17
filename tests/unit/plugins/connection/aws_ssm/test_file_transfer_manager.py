# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from io import BytesIO
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible.errors import AnsibleError

from ansible_collections.community.aws.plugins.plugin_utils.ssm.filetransfermanager import CommandResult
from ansible_collections.community.aws.plugins.plugin_utils.ssm.filetransfermanager import FileTransferManager


class TestFileTransferManager:
    @pytest.fixture
    def file_transfer_manager(self, connection_aws_ssm):
        """Creates an instance of FileTransferManager"""

        connection_aws_ssm._s3_manager = MagicMock()
        connection_aws_ssm._s3_manager.client = MagicMock()
        connection_aws_ssm.reconnection_retries = 5

        return FileTransferManager(
            bucket_name="test_bucket",
            instance_id=connection_aws_ssm._instance_id,
            s3_client=connection_aws_ssm._s3_manager.client,
            reconnection_retries=connection_aws_ssm.reconnection_retries,
            verbosity_display=MagicMock(),
            close=MagicMock(),
            exec_command=MagicMock(),
        )

    @pytest.mark.parametrize(
        "ssm_action, handler_method, expected_output, in_path, out_path",
        [
            ("get", "_handle_get", "Success", "local_in.txt", "remote_out.txt"),
            ("put", "_handle_put", "Uploaded", "local_in2.txt", "remote_out2.txt"),
            ("get", "_handle_get", "Success", "input_3.txt", "output_3.txt"),
            ("put", "_handle_put", "Uploaded", "input_4.txt", "output_4.txt"),
        ],
    )
    def test_file_transport_command(
        self,
        file_transfer_manager,
        connection_aws_ssm,
        ssm_action: str,
        handler_method: str,
        expected_output: str,
        in_path: str,
        out_path: str,
    ):
        connection_aws_ssm._s3_manager.client.delete_object = MagicMock()
        handler_mock = MagicMock(return_value=CommandResult(returncode=0, stdout=expected_output, stderr=""))
        setattr(file_transfer_manager, handler_method, handler_mock)

        result = file_transfer_manager._file_transport_command(
            in_path,
            out_path,
            ssm_action,
            "test-cmd",
            put_args={},
            s3_path="test_s3_path",
        )

        handler_mock.assert_called_once()
        connection_aws_ssm._s3_manager.client.delete_object.assert_called_once_with(
            Bucket="test_bucket", Key="test_s3_path"
        )
        assert result["returncode"] == 0
        assert result["stdout"] == expected_output
        assert result["stderr"] == ""

    @pytest.mark.parametrize(
        "command_input, expected_returncode, expected_stdout",
        [
            ("echo test", 0, "Command executed"),
            ("failing command", 1, "Error message"),
        ],
    )
    def test_exec_transport_commands(
        self,
        file_transfer_manager,
        connection_aws_ssm,
        command_input: str,
        expected_returncode: int,
        expected_stdout: str,
    ):
        # Mocking exec_command for the given command input
        file_transfer_manager.exec_command.return_value = (
            expected_returncode,
            expected_stdout,
            "" if expected_returncode == 0 else "Error message",
        )

        commands = [{"command": command_input}]

        if expected_returncode == 0:
            result = file_transfer_manager._exec_transport_commands("input.txt", "output.txt", commands)
            assert result["returncode"] == expected_returncode
            assert result["stdout"] == expected_stdout
        else:
            with pytest.raises(AnsibleError, match=r"failed to transfer file to input.txt output.txt:\s*Error message"):
                file_transfer_manager._exec_transport_commands("input.txt", "output.txt", commands)

    def test_handle_get(self, file_transfer_manager, connection_aws_ssm):
        connection_aws_ssm._s3_manager.client.download_fileobj = MagicMock()
        file_transfer_manager.exec_command.return_value = (0, "test", "")
        result = file_transfer_manager._handle_get(
            "in_path", "out_path", [{"command": "test-cmd", "method": "put"}], "s3_path"
        )
        assert result["returncode"] == 0
        connection_aws_ssm._s3_manager.client.download_fileobj.assert_called_once()

    def test_handle_put(self, file_transfer_manager, connection_aws_ssm):
        connection_aws_ssm._s3_manager.client.upload_fileobj = MagicMock()
        file_transfer_manager.exec_command.return_value = (0, "test", "")

        mock_file_content = b"dummy content"
        mock_file = BytesIO(mock_file_content)
        with patch("builtins.open", return_value=mock_file) as mocked_open:
            result = file_transfer_manager._handle_put(
                "in_path", "out_path", [{"command": "test-cmd", "method": "get"}], "s3_path", {}
            )

        assert result["returncode"] == 0
        connection_aws_ssm._s3_manager.client.upload_fileobj.assert_called_once()
