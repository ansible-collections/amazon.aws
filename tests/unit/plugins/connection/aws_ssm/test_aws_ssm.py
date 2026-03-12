# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from io import StringIO
from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

import pytest

from ansible.errors import AnsibleError
from ansible.errors import AnsibleFileNotFound
from ansible.playbook.play_context import PlayContext
from ansible.plugins.loader import connection_loader

from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3
from ansible_collections.amazon.aws.plugins.plugin_utils.ssm.s3clientmanager import S3ClientManager
from ansible_collections.amazon.aws.plugins.plugin_utils.ssm.s3clientmanager import generate_encryption_settings

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_data_pipeline.py requires the python modules 'boto3' and 'botocore'")


@pytest.fixture(name="loaded_aws_ssm")
def fixture_loaded_aws_ssm():
    conn = connection_loader.get("amazon.aws.aws_ssm", PlayContext(), StringIO())
    # conn.verbosity_display = MagicMock()
    conn._connect = MagicMock()
    conn.test_options = {
        "bucket_sse_mode": MagicMock(),
        "bucket_sse_kms_key_id": MagicMock(),
        "reconnection_retries": 3,
    }
    conn.get_option = MagicMock(side_effect=conn.test_options.get)
    conn.file_transfer_manager = MagicMock()

    return conn


class TestConnectionBaseClass:
    @patch("ansible_collections.amazon.aws.plugins.connection.aws_ssm.get_bucket_region", return_value="fake-region")
    def test_init_clients(self, mock_get_bucket_region, loaded_aws_ssm):
        boto_clients = {"ssm": MagicMock(), "s3": MagicMock()}

        print(dir(self))

        def mock_client(service, *args, **kwargs):
            client = boto_clients.get(service)
            # Mock the meta attributes for S3 clients
            if service == "s3":
                client.meta.endpoint_url = "https://s3.fake-region.amazonaws.com"
                client.meta.region_name = "fake-region"
            return client

        loaded_aws_ssm.client = MagicMock(side_effect=mock_client)

        options = {
            "s3_addressing_style": MagicMock(),
            "bucket_endpoint_url": None,  # No explicit endpoint URL
            "bucket_name": "test-bucket",
            "access_key": MagicMock(),
            "secret_key": MagicMock(),
            "session_token": MagicMock(),
            "region": "us-east-1",
            "profile": MagicMock(),
        }

        def mock_get_option(name, **kwargs):
            return options.get(name)

        loaded_aws_ssm.get_option = MagicMock(side_effect=mock_get_option)

        loaded_aws_ssm._init_clients()

        # Validate that get_bucket_region was called
        mock_get_bucket_region.assert_called_once()

        # Validate that the S3 client was created with the correct endpoint and region
        config = {"signature_version": "s3v4", "s3": {"addressing_style": options.get("s3_addressing_style")}}
        loaded_aws_ssm.client.assert_has_calls(
            [
                call("s3", region="us-east-1"),  # Initial temporary call to determine bucket region
                call("s3", region="fake-region"),  # Second temporary call for the bucket's actual region
                call(
                    "s3", endpoint="https://s3.fake-region.amazonaws.com", region="fake-region", aws_config=config
                ),  # Final S3 client
                call("ssm", aws_config=config),
            ]
        )
        assert loaded_aws_ssm.s3_manager.client == boto_clients["s3"]
        assert loaded_aws_ssm._client == boto_clients["ssm"]

    @pytest.mark.parametrize("path_exists", [True, False])
    @patch("ansible_collections.amazon.aws.plugins.connection.aws_ssm.to_bytes")
    @patch("os.path.exists")
    def test_plugins_connection_aws_ssm_put_file(self, mock_os_path_exists, mock_to_bytes, loaded_aws_ssm, path_exists):
        mock_os_path_exists.return_value = path_exists

        in_path = MagicMock()
        out_path = MagicMock()
        file_transport_result = MagicMock()
        loaded_aws_ssm.generate_commands = MagicMock(return_value=("", [], {}))
        loaded_aws_ssm.file_transfer_manager._file_transport_command = MagicMock(return_value=file_transport_result)
        to_bytes_results = MagicMock()
        mock_to_bytes.return_value = to_bytes_results
        if path_exists:
            assert loaded_aws_ssm.put_file(in_path, out_path) == file_transport_result
            loaded_aws_ssm.file_transfer_manager._file_transport_command.assert_called_once_with(
                in_path, out_path, "put", [], {}, ""
            )
        else:
            with pytest.raises(AnsibleFileNotFound) as exc_info:
                loaded_aws_ssm.put_file(in_path, out_path)
            assert str(exc_info.value).startswith("file or module does not exist: ")
            loaded_aws_ssm.file_transfer_manager._file_transport_command.assert_not_called()

        mock_os_path_exists.assert_called_once_with(to_bytes_results)
        mock_to_bytes.assert_called_once_with(in_path, errors="surrogate_or_strict")

    def test_plugins_connection_aws_ssm_fetch_file(self, loaded_aws_ssm):
        in_path = MagicMock()
        out_path = MagicMock()
        file_transport_result = MagicMock()
        loaded_aws_ssm.generate_commands = MagicMock(return_value=("", [], {}))
        loaded_aws_ssm.file_transfer_manager._file_transport_command = MagicMock(return_value=file_transport_result)

        assert loaded_aws_ssm.fetch_file(in_path, out_path) == file_transport_result
        loaded_aws_ssm.file_transfer_manager._file_transport_command.assert_called_once_with(
            in_path, out_path, "get", [], {}, ""
        )

    @pytest.mark.parametrize("session_manager_initialized", [True, False])
    def test_plugins_connection_aws_ssm_close(self, loaded_aws_ssm, session_manager_initialized):
        session_manager = MagicMock()
        if session_manager_initialized:
            loaded_aws_ssm.session_manager = session_manager
        loaded_aws_ssm.close()

        if session_manager_initialized:
            session_manager.terminate.assert_called_once()
        else:
            session_manager.terminate.assert_not_called()
        assert loaded_aws_ssm.session_manager is None

    def test_plugins_connection_aws_ssm_del_handles_exceptions(self, loaded_aws_ssm):
        """Test that __del__ handles exceptions gracefully during shutdown"""
        loaded_aws_ssm.close = MagicMock(side_effect=ReferenceError("weakly-referenced object no longer exists"))
        loaded_aws_ssm.__del__()
        loaded_aws_ssm.close.assert_called_once()

    @pytest.mark.parametrize("level", ["invalid value", 5, -1])
    @patch("ansible_collections.amazon.aws.plugins.connection.aws_ssm.display")
    def test_verbosity_diplay_invalid_level(self, mock_display, loaded_aws_ssm, level):
        """Testing verbosity levels"""
        # Test exception is raised when verbosity level is not an accepted value
        with pytest.raises(AnsibleError) as exc_info:
            loaded_aws_ssm.verbosity_display(level, "unit testing connection aws_ssm plugin")
        assert str(exc_info.value) == (f"Invalid verbosity level: {level}")
        for method in ("v", "vv", "vvv", "vvvv"):
            getattr(mock_display, method).assert_not_called()

    @pytest.mark.parametrize("host", [None, "test-host"])
    @pytest.mark.parametrize(
        "level,method",
        [
            (1, "v"),
            (2, "vv"),
            (3, "vvv"),
            (4, "vvvv"),
        ],
    )
    @patch("ansible_collections.amazon.aws.plugins.connection.aws_ssm.display")
    def test_verbosity_diplay(self, mock_display, loaded_aws_ssm, host, level, method):
        """Testing verbosity levels"""
        loaded_aws_ssm.host = host
        message = "unit testing connection aws_ssm plugin"
        loaded_aws_ssm.verbosity_display(level, message)
        # Verify the correct display method was called with expected args
        args = {}
        if host:
            args["host"] = host
        getattr(mock_display, method).assert_called_once_with(message, **args)


class TestS3ClientManager:
    """
    Tests for the S3ClientManager class
    """

    def create_object(self):
        self.client = MagicMock()
        return S3ClientManager(self.client)

    @pytest.mark.parametrize("method", ["get", "put", "fake"])
    @pytest.mark.parametrize("is_windows", [False, True])
    @patch("ansible_collections.amazon.aws.plugins.plugin_utils.ssm.s3clientmanager.generate_encryption_settings")
    def test_generate_host_commands(self, m_generate_encryption_settings, method, is_windows):
        """Testing command generation on both Windows and non-Windows systems"""
        s3_client_manager = self.create_object()

        s3_client_manager.get_url = MagicMock()
        s3_client_manager.get_url.return_value = "https://test-url"
        encryption_headers = {"ServerSideEncryption": "aws:kms"}
        encryption_args = MagicMock()
        m_generate_encryption_settings.return_value = (encryption_args, encryption_headers)

        bucket_sse_mode = MagicMock()
        bucket_sse_kms_key_id = MagicMock()
        s3_path = MagicMock()
        bucket_name = MagicMock()

        test_command_generation, put_args = s3_client_manager.generate_host_commands(
            bucket_name=bucket_name,
            bucket_sse_mode=bucket_sse_mode,
            bucket_sse_kms_key_id=bucket_sse_kms_key_id,
            s3_path=s3_path,
            in_path="test/in/path",
            out_path="test/out/path",
            is_windows=is_windows,
            method=method,
        )

        if method not in ("get", "put"):
            assert put_args is None
            assert test_command_generation is None
        else:
            assert isinstance(test_command_generation, str)
            print(m_generate_encryption_settings.mock_calls)
            if method == "get":
                m_generate_encryption_settings.assert_called_once_with(bucket_sse_mode, bucket_sse_kms_key_id)
                if is_windows:
                    assert test_command_generation.startswith("Invoke-WebRequest -Method PUT -Headers @")
                    assert test_command_generation.endswith(
                        "-InFile 'test/in/path' -Uri 'https://test-url' -UseBasicParsing"
                    )
                else:
                    assert test_command_generation.startswith("curl --request PUT ")
                    assert test_command_generation.endswith("--upload-file 'test/in/path' 'https://test-url'")
                assert put_args == encryption_args
                s3_client_manager.get_url.assert_called_once_with(
                    "put_object", bucket_name, s3_path, "PUT", extra_args=encryption_args
                )
            elif method == "put":
                m_generate_encryption_settings.assert_not_called()
                if is_windows:
                    assert "Invoke-WebRequest 'https://test-url' -OutFile 'test/out/path'" == test_command_generation
                else:
                    assert "curl -o 'test/out/path' 'https://test-url';touch 'test/out/path'" == test_command_generation
                assert put_args is None
                s3_client_manager.get_url.assert_called_once_with("get_object", bucket_name, s3_path, "GET")

    def test_get_url_no_extra_args(self):
        """
        Test get_url() without extra_args
        """
        s3_client_manager = self.create_object()
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/generate_presigned_url.html
        self.client.generate_presigned_url.return_value = "http://test-url-extra"

        result = s3_client_manager.get_url(
            client_method="put_object",
            bucket_name="test_bucket",
            out_path="test/path",
            http_method="PUT",
        )

        expected_params = {"Bucket": "test_bucket", "Key": "test/path"}

        self.client.generate_presigned_url.assert_called_once_with(
            "put_object", Params=expected_params, ExpiresIn=3600, HttpMethod="PUT"
        )
        assert result == "http://test-url-extra"

    def test_get_url_extra_args(self):
        """
        Test get_url() with extra_args
        """
        s3_client_manager = self.create_object()
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/generate_presigned_url.html
        self.client.generate_presigned_url.return_value = "http://test-url-extra"
        extra_args = {"ACL": "public-read", "ContentType": "text/plain"}

        result = s3_client_manager.get_url(
            client_method="put_object",
            bucket_name="test_bucket",
            out_path="test/path",
            http_method="PUT",
            extra_args=extra_args,
        )

        expected_params = {"Bucket": "test_bucket", "Key": "test/path"}
        expected_params.update(extra_args)

        self.client.generate_presigned_url.assert_called_once_with(
            "put_object", Params=expected_params, ExpiresIn=3600, HttpMethod="PUT"
        )
        assert result == "http://test-url-extra"


@pytest.mark.parametrize(
    "bucket_sse_mode,bucket_sse_kms_key_id,args,headers",
    [
        (None, "We do not care about this", {}, {}),
        (
            "sse_no_kms",
            "sse_key_id",
            {"ServerSideEncryption": "sse_no_kms"},
            {"x-amz-server-side-encryption": "sse_no_kms"},
        ),
        ("aws:kms", "", {"ServerSideEncryption": "aws:kms"}, {"x-amz-server-side-encryption": "aws:kms"}),
        ("aws:kms", None, {"ServerSideEncryption": "aws:kms"}, {"x-amz-server-side-encryption": "aws:kms"}),
        (
            "aws:kms",
            "test_kms_id",
            {"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": "test_kms_id"},
            {"x-amz-server-side-encryption": "aws:kms", "x-amz-server-side-encryption-aws-kms-key-id": "test_kms_id"},
        ),
    ],
)
def test_generate_encryption_settings(bucket_sse_mode, bucket_sse_kms_key_id, args, headers):
    """
    Test generate_encryption_settings()
    """

    r_args, r_headers = generate_encryption_settings(bucket_sse_mode, bucket_sse_kms_key_id)
    assert r_args == args
    assert r_headers == headers
