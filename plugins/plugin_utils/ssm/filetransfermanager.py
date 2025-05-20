# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from typing import Any
from typing import Callable
from typing import Dict
from typing import Optional

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes

from ansible_collections.amazon.aws.plugins.plugin_utils.ssm.common import CommandResult
from ansible_collections.amazon.aws.plugins.plugin_utils.ssm.common import ssm_retry


class FileTransferManager:
    """Manages file transfers using S3 as an intermediary."""

    def __init__(
        self,
        bucket_name: str,
        instance_id: str,
        s3_client,
        reconnection_retries: int,
        verbosity_display: Callable[[int, str], None],
        close: Callable[[], None],
        exec_command: Callable[[str, Optional[bool], Optional[bool]], CommandResult],
    ):
        """
        Initializes the FileTransferManager with a given connection.

        :param connection: The connection object used for S3 and remote execution.
        """
        self.bucket_name = bucket_name
        self.instance_id = instance_id
        self.s3_client = s3_client
        self.reconnection_retries = reconnection_retries
        self.verbosity_display = verbosity_display
        self.close = close
        self.exec_command = exec_command

    @ssm_retry
    def _file_transport_command(
        self,
        in_path: str,
        out_path: str,
        ssm_action: str,
        command: str,
        put_args: Dict[str, Any],
        s3_path: str,
    ) -> CommandResult:
        """
        Transfers files to or from a remote host using S3.

        :param in_path: The local path of the file to be transferred.
        :param out_path: The remote path where the file should be placed.
        :param ssm_action: The action to perform, either 'get' (download) or 'put' (upload).
        :param command: A shell command string
        :param put_args: Additional arguments for S3 upload.
        :param s3_path: The S3 path where the file is stored.
        :return: A CommandResult dictionary containing execution results.
        """
        try:
            if ssm_action == "get":
                return self._handle_get(in_path, out_path, command, s3_path)
            return self._handle_put(in_path, out_path, command, s3_path, put_args)
        finally:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_path)

    def _handle_get(self, in_path: str, out_path: str, command: str, s3_path: str) -> CommandResult:
        """
        Handles downloading a file from the remote host via S3.

        :param in_path: The local destination path for the file.
        :param out_path: The remote source path of the file.
        :param commands: The transport commands to execute.
        :param s3_path: The S3 path where the file is stored.
        :return: A CommandResult dictionary containing execution results.
        """

        result = self._exec_transport_commands(in_path, out_path, command)
        with open(to_bytes(out_path, errors="surrogate_or_strict"), "wb") as data:
            self.s3_client.download_fileobj(self.bucket_name, s3_path, data)

        return result

    def _handle_put(
        self, in_path: str, out_path: str, command: str, s3_path: str, put_args: Dict[str, Any]
    ) -> CommandResult:
        """
        Handles uploading a file to the remote host via S3.

        :param in_path: The local source path of the file.
        :param out_path: The remote destination path for the file.
        :param commands: The transport commands to execute.
        :param s3_path: The S3 path where the file will be stored.
        :param put_args: Additional arguments for S3 upload.
        :return: A CommandResult dictionary containing execution results.
        """

        with open(to_bytes(in_path, errors="surrogate_or_strict"), "rb") as data:
            self.s3_client.upload_fileobj(data, self.bucket_name, s3_path, ExtraArgs=put_args)

        result = self._exec_transport_commands(in_path, out_path, command)

        return result

    def _exec_transport_commands(self, in_path: str, out_path: str, command: str) -> CommandResult:
        """
        Executes the provided transport commands.

        :param in_path: The input path.
        :param out_path: The output path.
        :param commands: A list of command dictionaries containing the command string and metadata.
        :return: A CommandResult dictionary containing execution results.
        """
        returncode, stdout, stderr = self.exec_command(command, in_data=None, sudoable=False)

        # Check the return code
        if returncode != 0:
            raise AnsibleError(f"failed to transfer file to {in_path} {out_path}:\n{stdout}\n{stderr}")

        return {"returncode": returncode, "stdout": stdout, "stderr": stderr}
