# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from io import StringIO
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible.errors import AnsibleError
from ansible.playbook.play_context import PlayContext
from ansible.plugins.loader import connection_loader

from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3

from ansible_collections.community.aws.plugins.connection.aws_ssm import Connection
from ansible_collections.community.aws.plugins.plugin_utils.s3clientmanager import S3ClientManager

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_data_pipeline.py requires the python modules 'boto3' and 'botocore'")


class TestConnectionBaseClass:
    @patch(
        "ansible_collections.community.aws.plugins.plugin_utils.s3clientmanager.S3ClientManager.get_bucket_endpoint",
        return_value=("fake-s3-endpoint", "fake-region"),
    )
    @patch(
        "ansible_collections.community.aws.plugins.plugin_utils.s3clientmanager.S3ClientManager.get_s3_client",
        return_value=MagicMock(),
    )
    def test_init_clients(self, mock_get_s3_client, mock_get_bucket_endpoint):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get("community.aws.aws_ssm", pc, new_stdin)

        def mock_get_option(key):
            options = {
                "profile": "test-profile",
                "region": "us-east-1",
            }
            return options.get(key, None)

        conn.get_option = MagicMock(side_effect=mock_get_option)

        # Mock the _initialize_ssm_client and _initialize_s3_client methods
        conn._initialize_ssm_client = MagicMock()

        conn._init_clients()

        # Assert that _initialize_ssm_client was called once
        conn._initialize_ssm_client.assert_called_once_with("us-east-1", "test-profile")

        # Assert that get_bucket_endpoint was called once
        mock_get_bucket_endpoint.assert_called_once()

        # Assert that get_s3_client was called with appropriate arguments
        mock_get_s3_client.assert_called_once()

        # Assert that self._s3_client is not None
        assert conn._s3_client is not None
        assert conn._s3_client is conn.s3_manager._s3_client

    @patch("boto3.client")
    def test_initialize_ssm_client(self, mock_boto3_client):
        """
        Test for the _initialize_ssm_client method to ensure the SSM client is initialized correctly.
        """
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get("community.aws.aws_ssm", pc, new_stdin)

        test_region_name = "us-west-2"
        test_profile_name = "test-profile"

        # Mock the _get_boto_client method to return a mock client
        conn._get_boto_client = MagicMock(return_value=mock_boto3_client)

        conn._initialize_ssm_client(test_region_name, test_profile_name)

        conn._get_boto_client.assert_called_once_with(
            "ssm",
            region_name=test_region_name,
            profile_name=test_profile_name,
        )

        assert conn._client is mock_boto3_client

    @patch("os.path.exists")
    @patch("subprocess.Popen")
    @patch("select.poll")
    @patch("boto3.client")
    def test_plugins_connection_aws_ssm_start_session(self, boto_client, s_poll, s_popen, mock_ospe):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get("community.aws.aws_ssm", pc, new_stdin)
        conn.get_option = MagicMock()
        conn.get_option.side_effect = ["i1234", "executable", "abcd", "i1234"]
        conn.host = "abc"
        mock_ospe.return_value = True
        boto3 = MagicMock()
        boto3.client("ssm").return_value = MagicMock()
        conn.start_session = MagicMock()
        conn._session_id = MagicMock()
        conn._session_id.return_value = "s1"
        s_popen.return_value.stdin.write = MagicMock()
        s_poll.return_value = MagicMock()
        s_poll.return_value.register = MagicMock()
        s_popen.return_value.poll = MagicMock()
        s_popen.return_value.poll.return_value = None
        conn._stdin_readline = MagicMock()
        conn._stdin_readline.return_value = "abc123"
        conn.SESSION_START = "abc"
        conn.start_session()

    @patch("random.choice")
    def test_plugins_connection_aws_ssm_exec_command(self, r_choice):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get("community.aws.aws_ssm", pc, new_stdin)
        r_choice.side_effect = ["a", "a", "a", "a", "a", "b", "b", "b", "b", "b"]
        conn.MARK_LENGTH = 5
        conn._session = MagicMock()
        conn._session.stdin.write = MagicMock()
        conn._wrap_command = MagicMock()
        conn._wrap_command.return_value = "cmd1"
        conn._flush_stderr = MagicMock()
        conn._windows = MagicMock()
        conn._windows.return_value = True
        conn._session.poll = MagicMock()
        conn._session.poll.return_value = None
        conn._timeout = MagicMock()
        conn._poll_stdout = MagicMock()
        conn._poll_stdout.poll = MagicMock()
        conn._poll_stdout.poll.return_value = True
        conn._session.stdout = MagicMock()
        conn._session.stdout.readline = MagicMock()
        conn._post_process = MagicMock()
        conn._post_process.return_value = "test"
        conn._session.stdout.readline.side_effect = iter(["aaaaa\n", "Hi\n", "0\n", "bbbbb\n"])
        conn.get_option = MagicMock()
        conn.get_option.return_value = 1
        returncode = "a"
        stdout = "b"
        return (returncode, stdout, conn._flush_stderr)

    def test_plugins_connection_aws_ssm_prepare_terminal(self):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get("community.aws.aws_ssm", pc, new_stdin)
        conn.is_windows = MagicMock()
        conn.is_windows.return_value = True

    def test_plugins_connection_aws_ssm_wrap_command(self):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get("community.aws.aws_ssm", pc, new_stdin)
        conn.is_windows = MagicMock()
        conn.is_windows.return_value = True
        return "windows1"

    def test_plugins_connection_aws_ssm_post_process(self):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get("community.aws.aws_ssm", pc, new_stdin)
        conn.is_windows = MagicMock()
        conn.is_windows.return_value = True
        conn.stdout = MagicMock()
        returncode = 0
        return returncode, conn.stdout

    @patch("subprocess.Popen")
    def test_plugins_connection_aws_ssm_flush_stderr(self, s_popen):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get("community.aws.aws_ssm", pc, new_stdin)
        conn.poll_stderr = MagicMock()
        conn.poll_stderr.register = MagicMock()
        conn.stderr = None
        s_popen.poll().return_value = 123
        return conn.stderr

    # XXX This isn't doing anything
    # def test_plugins_connection_aws_ssm_get_url(self):
    #     pc = PlayContext()
    #     new_stdin = StringIO()
    #     connection_loader.get('community.aws.aws_ssm', pc, new_stdin)
    #     boto3 = MagicMock()
    #     boto3.client('s3').return_value = MagicMock()
    #     boto3.generate_presigned_url.return_value = MagicMock()
    #     return (boto3.generate_presigned_url.return_value)

    @patch("os.path.exists")
    def test_plugins_connection_aws_ssm_put_file(self, mock_ospe):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get("community.aws.aws_ssm", pc, new_stdin)
        conn._connect = MagicMock()
        conn._file_transport_command = MagicMock()
        conn._file_transport_command.return_value = (0, "stdout", "stderr")
        conn.put_file("/in/file", "/out/file")

    def test_plugins_connection_aws_ssm_fetch_file(self):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get("community.aws.aws_ssm", pc, new_stdin)
        conn._connect = MagicMock()
        conn._file_transport_command = MagicMock()
        conn._file_transport_command.return_value = (0, "stdout", "stderr")
        conn.fetch_file("/in/file", "/out/file")

    @patch("subprocess.check_output")
    @patch("boto3.client")
    def test_plugins_connection_file_transport_command(self, boto_client, s_check_output):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get("community.aws.aws_ssm", pc, new_stdin)
        conn.get_option = MagicMock()
        conn.get_option.side_effect = ["1", "2", "3", "4", "5"]
        conn._get_url = MagicMock()
        conn._get_url.side_effect = ["url1", "url2"]
        boto3 = MagicMock()
        boto3.client("s3").return_value = MagicMock()
        conn.get_option.return_value = 1
        get_command = MagicMock()
        put_command = MagicMock()
        conn.exec_command = MagicMock()
        conn.exec_command.return_value = (put_command, None, False)
        conn.download_fileobj = MagicMock()
        conn.exec_command(put_command, in_data=None, sudoable=False)
        conn.exec_command(get_command, in_data=None, sudoable=False)

    @patch("subprocess.check_output")
    def test_plugins_connection_aws_ssm_close(self, s_check_output):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get("community.aws.aws_ssm", pc, new_stdin)
        conn.instance_id = "i-12345"
        conn._session_id = True
        conn.get_option = MagicMock()
        conn.get_option.side_effect = ["/abc", "pqr"]
        conn._session = MagicMock()
        conn._session.terminate = MagicMock()
        conn._session.communicate = MagicMock()
        conn._terminate_session = MagicMock()
        conn._terminate_session.return_value = ""
        conn._session_id = MagicMock()
        conn._session_id.return_value = "a"
        conn._client = MagicMock()
        conn.close()

    def test_generate_mark(self):
        """Testing string generation"""
        test_a = Connection.generate_mark()
        test_b = Connection.generate_mark()

        assert test_a != test_b
        assert len(test_a) == Connection.MARK_LENGTH
        assert len(test_b) == Connection.MARK_LENGTH

    @pytest.mark.parametrize("is_windows", [False, True])
    def test_generate_commands(self, is_windows):
        """Testing command generation on both Windows and non-Windows systems"""
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get("community.aws.aws_ssm", pc, new_stdin)
        conn.get_option = MagicMock()

        conn.is_windows = is_windows

        mock_s3_manager = MagicMock(spec=S3ClientManager)

        mock_s3_manager.get_url.return_value = "https://test-url"
        mock_s3_manager.generate_encryption_settings.return_value = (
            {"ServerSideEncryption": "aws:kms"},
            {"x-amz-server-side-encryption": "aws:kms"},
        )
        conn.s3_manager = mock_s3_manager

        test_command_generation = conn._generate_commands(
            "test_bucket",
            "test/s3/path",
            "test/in/path",
            "test/out/path",
        )

        # Check contents of generated command dictionaries
        assert "command" in test_command_generation[0][0]
        assert "method" in test_command_generation[0][0]
        assert "headers" in test_command_generation[0][0]

        if is_windows:
            assert "Invoke-WebRequest" in test_command_generation[0][1]["command"]
            assert test_command_generation[0][1]["method"] == "put"
            # Two command dictionaries are generated for Windows
            assert len(test_command_generation[0]) == 2
        else:
            put_cmd = test_command_generation[0][2]["command"]
            assert "curl --request PUT" in put_cmd
            assert "-H 'x-amz-server-side-encryption: aws:kms'" in put_cmd
            assert "--upload-file 'test/in/path'" in put_cmd
            assert "'https://test-url'" in put_cmd
            assert test_command_generation[0][2]["method"] == "put"
            # Three command dictionaries are generated on non-Windows systems
            assert len(test_command_generation[0]) == 3

        # Ensure data types of command object are as expected
        assert isinstance(test_command_generation, tuple)
        assert isinstance(test_command_generation[0], list)
        assert isinstance(test_command_generation[0][0], dict)

    @pytest.mark.parametrize(
        "message,level,method",
        [
            ("test message 1", 1, "v"),
            ("test message 2", 2, "vv"),
            ("test message 3", 3, "vvv"),
            ("test message 4", 4, "vvvv"),
        ],
    )
    def test_verbosity_diplay(self, message, level, method):
        """Testing verbosity levels"""
        play_context = MagicMock()
        play_context.shell = "sh"
        conn = Connection(play_context)
        conn.host = "test-host"  # Test with host set

        with patch("ansible_collections.community.aws.plugins.connection.aws_ssm.display") as mock_display:
            conn.verbosity_display(level, message)
            # Verify the correct display method was called with expected args
            mock_method = getattr(mock_display, method)
            mock_method.assert_called_once_with(message, host="test-host")

            # Test without host set
            conn.host = None
            conn.verbosity_display(1, "no host message")
            mock_display.v.assert_called_with("no host message")

            # Test exception is raised when verbosity level is not an accepted value
            with pytest.raises(AnsibleError):
                conn.verbosity_display("invalid value", "test message")

    def test_poll_verbosity(self):
        """Test poll method verbosity display"""
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get("community.aws.aws_ssm", pc, new_stdin)

        conn._session = MagicMock()
        conn._session.poll.return_value = None
        conn.get_option = MagicMock(return_value=10)  # ssm_timeout
        conn.poll_stdout = MagicMock()
        conn.instance_id = "i-1234567890"
        conn.host = conn.instance_id

        with patch("time.time", return_value=100), patch.object(conn, "verbosity_display") as mock_display:
            poll_gen = conn.poll("TEST", "test command")
            # Advance generator twice to trigger the verbosity message
            next(poll_gen)
            next(poll_gen)

            # Verify verbosity message contains remaining time
            mock_display.assert_called_with(4, "TEST remaining: 10 second(s)")


class TestS3ClientManager:
    """
    Tests for the S3ClientManager class
    """

    @patch(
        "ansible_collections.community.aws.plugins.connection.aws_ssm.S3ClientManager.get_s3_client",
        return_value="mocked_s3_client",
    )
    def test_initialize_client(self, mock_get_s3_client):
        """
        Test initialize_client()
        """
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get("community.aws.aws_ssm", pc, new_stdin)

        s3_client_manager = S3ClientManager(connection=conn)

        s3_client_manager.initialize_client(
            region_name="us-east-2", endpoint_url="https://mock-endpoint", profile_name="test-profile"
        )

        assert mock_get_s3_client.call_count == 1

        mock_get_s3_client.assert_called_once_with(
            region_name="us-east-2",
            endpoint_url="https://mock-endpoint",
            profile_name="test-profile",
        )

        assert s3_client_manager._s3_client is not None
        assert s3_client_manager._s3_client == "mocked_s3_client"

    def test_get_bucket_endpoint(self):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get("community.aws.aws_ssm", pc, new_stdin)

        # Mock get_option to return expected values
        def mock_get_option(key):
            options = {
                "region": "us-east-2",
                "profile": "test-profile",
                "bucket_name": "my-bucket",
                "bucket_endpoint_url": None,
            }
            return options.get(key)

        conn.get_option = MagicMock(side_effect=mock_get_option)

        s3_manager = S3ClientManager(connection=conn)

        mock_tmp_client = MagicMock()
        mock_tmp_client.head_bucket.return_value = {
            "ResponseMetadata": {"HTTPHeaders": {"x-amz-bucket-region": "us-east-2"}}
        }

        mock_region_client = MagicMock()
        mock_region_client.meta.endpoint_url = "https://s3.us-east-2.amazonaws.com"
        mock_region_client.meta.region_name = "us-east-2"

        s3_manager.get_s3_client = MagicMock(side_effect=[mock_tmp_client, mock_region_client])

        endpoint, region = s3_manager.get_bucket_endpoint()

        assert endpoint == "https://s3.us-east-2.amazonaws.com"
        assert region == "us-east-2"

    @patch("boto3.session.Session")
    def test_get_s3_client(self, mock_session_cls):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get("community.aws.aws_ssm", pc, new_stdin)

        # Mock get_option to return expected values
        def mock_get_option(key):
            options = {
                "access_key_id": "dummy_key",
                "secret_access_key": "dummy_secret",
                "session_token": "dummy_token",
                "s3_addressing_style": "path",
            }
            return options.get(key, None)

        conn.get_option = MagicMock(side_effect=mock_get_option)

        s3_manager = S3ClientManager(connection=conn)

        mock_session = MagicMock()
        mock_client = "mock_client"
        mock_session.client.return_value = mock_client
        mock_session_cls.return_value = mock_session

        client = s3_manager.get_s3_client(
            region_name="us-east-2", profile_name="test-profile", endpoint_url="http://example.com"
        )

        assert client == mock_client

    def test_get_url_no_extra_args(self):
        """
        Test get_url() without extra_args
        """
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get("community.aws.aws_ssm", pc, new_stdin)

        s3_manager = S3ClientManager(connection=conn)
        mock_s3_client = MagicMock()
        s3_manager._s3_client = mock_s3_client
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/generate_presigned_url.html
        mock_s3_client.generate_presigned_url.return_value = "http://test-url-extra"

        result = s3_manager.get_url(
            client_method="put_object",
            bucket_name="test_bucket",
            out_path="test/path",
            http_method="PUT",
        )

        expected_params = {"Bucket": "test_bucket", "Key": "test/path"}

        mock_s3_client.generate_presigned_url.assert_called_once_with(
            "put_object", Params=expected_params, ExpiresIn=3600, HttpMethod="PUT"
        )
        assert result == "http://test-url-extra"

    def test_get_url_extra_args(self):
        """
        Test get_url() with extra_args
        """
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get("community.aws.aws_ssm", pc, new_stdin)

        s3_manager = S3ClientManager(connection=conn)
        mock_s3_client = MagicMock()
        s3_manager._s3_client = mock_s3_client
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/generate_presigned_url.html
        mock_s3_client.generate_presigned_url.return_value = "http://test-url-extra"
        extra_args = {"ACL": "public-read", "ContentType": "text/plain"}

        result = s3_manager.get_url(
            client_method="put_object",
            bucket_name="test_bucket",
            out_path="test/path",
            http_method="PUT",
            extra_args=extra_args,
        )

        expected_params = {"Bucket": "test_bucket", "Key": "test/path"}
        expected_params.update(extra_args)

        mock_s3_client.generate_presigned_url.assert_called_once_with(
            "put_object", Params=expected_params, ExpiresIn=3600, HttpMethod="PUT"
        )
        assert result == "http://test-url-extra"

    def test_generate_encryption_settings(self):
        """
        Test generate_encryption_settings()
        """
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get("community.aws.aws_ssm", pc, new_stdin)

        # Mock get_option to return expected values
        def mock_get_option(key):
            options = {
                "profile": "test-profile",
                "region": "us-east-1",
                "bucket_sse_mode": "aws:kms",
                "bucket_sse_kms_key_id": "my-kms-key-id",
            }
            return options.get(key, None)

        conn.get_option = MagicMock(side_effect=mock_get_option)

        s3_manager = S3ClientManager(connection=conn)
        put_args, put_headers = s3_manager.generate_encryption_settings()

        expected_put_args = {"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": "my-kms-key-id"}
        expected_put_headers = {
            "x-amz-server-side-encryption": "aws:kms",
            "x-amz-server-side-encryption-aws-kms-key-id": "my-kms-key-id",
        }

        assert put_args == expected_put_args
        assert put_headers == expected_put_headers
        conn.get_option.assert_any_call("bucket_sse_mode")
        conn.get_option.assert_any_call("bucket_sse_kms_key_id")
