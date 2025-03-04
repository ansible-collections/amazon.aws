# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from io import StringIO
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible.playbook.play_context import PlayContext
from ansible.plugins.loader import connection_loader

from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3

from ansible_collections.community.aws.plugins.connection.aws_ssm import Connection

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_data_pipeline.py requires the python modules 'boto3' and 'botocore'")


class TestConnectionBaseClass:
    def test_init_clients(self):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get("community.aws.aws_ssm", pc, new_stdin)

        # Mock get_option to return expected region and profile
        def mock_get_option(key):
            options = {
                "profile": "test-profile",
                "region": "us-east-1",
            }
            return options.get(key, None)

        conn.get_option = MagicMock(side_effect=mock_get_option)

        # Mock the _initialize_ssm_client and _initialize_s3_client methods
        conn._initialize_ssm_client = MagicMock()
        conn._initialize_s3_client = MagicMock()

        conn._init_clients()

        conn._initialize_ssm_client.assert_called_once_with("us-east-1", "test-profile")
        conn._initialize_s3_client.assert_called_once_with("test-profile")

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

    @patch("boto3.client")
    def test_initialize_s3_client(self, mock_boto3_client):
        """
        Test for the _initialize_s3_client method to ensure the S3 client is initialized correctly.
        """

        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get("community.aws.aws_ssm", pc, new_stdin)

        test_profile_name = "test-profile"

        # Mock the _get_bucket_endpoint method to return dummy values
        conn._get_bucket_endpoint = MagicMock(return_value=("http://example.com", "us-west-2"))

        conn._get_boto_client = MagicMock(return_value=mock_boto3_client)

        conn._initialize_s3_client(test_profile_name)

        conn._get_bucket_endpoint.assert_called_once()

        conn._get_boto_client.assert_called_once_with(
            "s3",
            region_name="us-west-2",
            endpoint_url="http://example.com",
            profile_name=test_profile_name,
        )

        assert conn._s3_client is mock_boto3_client

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
        """Testing command generation on Windows systems"""
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get("community.aws.aws_ssm", pc, new_stdin)
        conn.get_option = MagicMock()

        conn.is_windows = is_windows

        mock_s3_client = MagicMock()
        mock_s3_client.generate_presigned_url.return_value = "https://test-url"
        conn._s3_client = mock_s3_client

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
            assert "curl --request PUT -H" in test_command_generation[0][2]["command"]
            assert test_command_generation[0][2]["method"] == "put"
            # Three command dictionaries are generated on non-Windows systems
            assert len(test_command_generation[0]) == 3

        # Ensure data types of command object are as expected
        assert isinstance(test_command_generation, tuple)
        assert isinstance(test_command_generation[0], list)
        assert isinstance(test_command_generation[0][0], dict)
