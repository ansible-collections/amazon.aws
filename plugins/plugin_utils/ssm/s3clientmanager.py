# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

try:
    import boto3
except ImportError:
    pass
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple


def generate_encryption_settings(
    bucket_sse_mode: Optional[str], bucket_sse_kms_key_id: Optional[str]
) -> Tuple[Dict, Dict]:
    """Generate Encryption Settings"""
    args = {}
    headers = {}
    if not bucket_sse_mode:
        return args, headers

    args["ServerSideEncryption"] = bucket_sse_mode
    headers["x-amz-server-side-encryption"] = bucket_sse_mode
    if bucket_sse_mode == "aws:kms" and bucket_sse_kms_key_id:
        args["SSEKMSKeyId"] = bucket_sse_kms_key_id
        headers["x-amz-server-side-encryption-aws-kms-key-id"] = bucket_sse_kms_key_id
    return args, headers


class S3ClientManager:
    def __init__(self, client: Any) -> None:
        self._s3_client = client

    @property
    def client(self) -> Any:
        return self._s3_client

    @staticmethod
    def _get_s3_client(
        access_key_id: Optional[str],
        secret_key_id: Optional[str],
        session_token: Optional[str],
        region_name: str,
        profile_name: Optional[str],
    ) -> Any:
        if not region_name:
            region_name = "us-east-1"
        session_args = dict(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_key_id,
            aws_session_token=session_token,
            region_name=region_name,
        )
        if profile_name:
            session_args["profile_name"] = profile_name
        session = boto3.session.Session(**session_args)
        return session.client("s3")

    @staticmethod
    def get_bucket_endpoint(
        bucket_name: str,
        bucket_endpoint_url: Optional[str],
        access_key_id: Optional[str],
        secret_key_id: Optional[str],
        session_token: Optional[str],
        region_name: Optional[str],
        profile_name: Optional[str],
    ) -> Tuple[str, str]:
        """
        Fetches the correct S3 endpoint and region for use with our bucket.
        If we don't explicitly set the endpoint then some commands will use the global
        endpoint and fail
        (new AWS regions and new buckets in a region other than the one we're running in)
        """
        if not region_name:
            region_name = "us-east-1"
        tmp_s3_client = S3ClientManager._get_s3_client(
            access_key_id, secret_key_id, session_token, region_name, profile_name
        )

        # Fetch the location of the bucket so we can open a client against the 'right' endpoint
        # This /should/ always work
        head_bucket = tmp_s3_client.head_bucket(Bucket=(bucket_name))
        bucket_region = head_bucket.get("ResponseMetadata", {}).get("HTTPHeaders", {}).get("x-amz-bucket-region", None)
        if bucket_region is None:
            bucket_region = "us-east-1"

        if bucket_endpoint_url:
            return bucket_endpoint_url, bucket_region

        # Create another client for the region the bucket lives in, so we can nab the endpoint URL
        if bucket_region != region_name:
            tmp_s3_client = S3ClientManager._get_s3_client(
                access_key_id, secret_key_id, session_token, bucket_region, profile_name
            )

        return tmp_s3_client.meta.endpoint_url, tmp_s3_client.meta.region_name

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
                command = (
                    "Invoke-WebRequest -Method PUT "
                    # @{'key' = 'value'; 'key2' = 'value2'}
                    f"-Headers @{{{put_command_headers}}} "
                    f"-InFile '{in_path}' "
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
                command = (
                    "Invoke-WebRequest "
                    f"'{url}' "
                    f"-OutFile '{out_path}'"
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
