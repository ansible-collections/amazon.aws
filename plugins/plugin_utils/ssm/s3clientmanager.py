# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Dict
    from typing import Optional
    from typing import Tuple

from ansible_collections.amazon.aws.plugins.plugin_utils.s3 import generate_encryption_settings


class S3ClientManager:
    def __init__(self, client: Any) -> None:
        """
        Initialise the S3ClientManager.

        :param client: The boto3 S3 client
        """
        self._s3_client = client

    @property
    def client(self) -> Any:
        return self._s3_client

    def get_url(
        self,
        client_method: str,
        bucket_name: str,
        out_path: str,
        http_method: str,
        extra_args: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate URL for get_object / put_object"""

        params = {"Bucket": bucket_name, "Key": out_path}
        if extra_args is not None:
            params.update(extra_args)
        return self._s3_client.generate_presigned_url(
            client_method, Params=params, ExpiresIn=3600, HttpMethod=http_method
        )

    def generate_host_commands(
        self,
        bucket_name: str,
        bucket_sse_mode: Optional[str],
        bucket_sse_kms_key_id: Optional[str],
        s3_path: str,
        in_path: str,
        out_path: str,
        is_windows: bool,
        method: str,
    ) -> Tuple[str, Optional[Dict[str, str]]]:
        """
        Generate commands for the specified bucket and configurations, S3 path, input path, and output path.
        The function generates a curl/Invoke-WebRequest command to be executed on the managed node.
        The method 'get' means the controller node wants to retrieve content from the managed node, the corresponding
        on the managed node is a 'put' command to updload content to the S3 bucket.
        The method 'put' means the controller node wants to upload content to the managed node, the corresponding
        on the managed node is a 'get' command to download content to the S3 bucket.

        :param bucket_name: The name of the S3 bucket used for file transfers.
        :param s3_path: The S3 path to the file to be sent.
        :param in_path: Input path
        :param out_path: Output path
        :param method: The request method to use for the command (can be "get" or "put").

        :returns: A tuple containing a shell command string and optional extra arguments for the PUT request.
        """

        command = None
        url = None
        put_args = None
        if method == "get":
            put_args, put_headers = generate_encryption_settings(bucket_sse_mode, bucket_sse_kms_key_id)
            url = self.get_url("put_object", bucket_name, s3_path, "PUT", extra_args=put_args)
            if is_windows:
                put_command_headers = "; ".join([f"'{h}' = '{v}'" for h, v in put_headers.items()])
                # Use -Body with ReadAllBytes instead of -InFile to properly handle unicode paths
                # PowerShell's -InFile parameter can have issues with unicode file paths
                # Using .NET ReadAllBytes ensures proper unicode path handling
                escaped_in_path = in_path.replace("'", "''")
                command = (
                    "$ErrorActionPreference = 'Stop' ; "
                    f"$fileContent = [System.IO.File]::ReadAllBytes('{escaped_in_path}') ; "
                    "Invoke-WebRequest -Method PUT "
                    # @{'key' = 'value'; 'key2' = 'value2'}
                    f"-Headers @{{{put_command_headers}}} "
                    "-Body $fileContent "
                    f"-Uri '{url}' "
                    f"-UseBasicParsing"
                )  # fmt: skip
            else:
                # Due to https://github.com/curl/curl/issues/183 earlier
                # versions of curl did not create the output file, when the
                # response was empty. Although this issue was fixed in 2015,
                # some actively maintained operating systems still use older
                # versions of it (e.g. CentOS 7)
                put_command_headers = " ".join([f"-H '{h}: {v}'" for h, v in put_headers.items()])
                command = (
                    "curl --request PUT "
                    f"{put_command_headers} "
                    f"--upload-file '{in_path}' "
                    f"'{url}'"
                )  # fmt: skip
        elif method == "put":
            url = self.get_url("get_object", bucket_name, s3_path, "GET")
            if is_windows:
                # Use .NET File.WriteAllBytes instead of -OutFile to properly handle unicode paths
                # PowerShell's -OutFile parameter can have issues with unicode file paths
                # Using .NET WriteAllBytes ensures proper unicode path handling
                escaped_out_path = out_path.replace("'", "''")
                command = (
                    "$ErrorActionPreference = 'Stop' ; "
                    f"$response = Invoke-WebRequest -Uri '{url}' -UseBasicParsing ; "
                    f"[System.IO.File]::WriteAllBytes('{escaped_out_path}', $response.Content)"
                )  # fmt: skip
            else:
                command = (
                    "curl "
                    f"-o '{out_path}' "
                    f"'{url}'"
                    ";"
                    "touch "
                    f"'{out_path}'"
                )  # fmt: skip

        return command, put_args
