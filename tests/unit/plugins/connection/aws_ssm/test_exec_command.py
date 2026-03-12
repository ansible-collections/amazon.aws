# -*- coding: utf-8 -*-

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# While it may seem appropriate to import our custom fixtures here, the pytest_ansible pytest plugin
# isn't as agressive as the ansible_test._util.target.pytest.plugins.ansible_pytest_collections plugin
# when it comes to rewriting the import paths and as such we can't import fixtures via their
# absolute import path or across collections.


from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible.errors import AnsibleConnectionFailure


@pytest.mark.parametrize(
    "mark_start,mark_end,stdout_lines,expected_stdout",
    [
        (
            "L_START_1",
            "L_END_1",
            ["SOME_CONTENT", "L_END_1"],
            "SOME_CONTENT",
        ),
        (
            "L_START_2",
            "L_END_2",
            ["FIRST", "+", "SECOND", "L_END_2"],
            "FIRST+SECOND",
        ),
        # Test that end marker can appear anywhere in the line
        (
            "L_START_3",
            "L_END_3",
            ["OUTPUT", "prefix_L_END_3_suffix"],
            "OUTPUT",
        ),
        # Test that end marker can be part of other text
        (
            "L_START_4",
            "MARKER",
            ["CONTENT", "some text MARKER more text"],
            "CONTENT",
        ),
    ],
)
@patch("ansible_collections.amazon.aws.plugins.plugin_utils.ssm.text.filter_ansi")
def test_connection_aws_ssm_exec_communicate(
    m_filter_ansi, connection_aws_ssm, mark_start, mark_end, stdout_lines, expected_stdout
):
    m_filter_ansi.side_effect = lambda line, is_windows: line
    connection_aws_ssm.poll = MagicMock()

    def _poll(trc, cmd):
        while True:
            yield True

    connection_aws_ssm.session_manager.poll.side_effect = _poll
    # wait_for_match consumes the start marker, so readline only sees content after it
    connection_aws_ssm.session_manager.wait_for_match = MagicMock()
    connection_aws_ssm.session_manager.stdout_readline.side_effect = stdout_lines
    connection_aws_ssm._post_process = MagicMock()
    returncode = MagicMock()
    connection_aws_ssm._post_process.side_effect = lambda line, marker: (returncode, line)

    stderr = MagicMock()
    connection_aws_ssm.session_manager.flush_stderr.return_value = stderr

    result_returncode, result_stdout, result_stderr = connection_aws_ssm.exec_communicate(
        "ansible-test units", None, mark_start, mark_end
    )

    assert result_returncode == returncode
    assert result_stdout == expected_stdout
    assert stderr == result_stderr


def test_connection_aws_ssm_exec_communicate_with_exception(connection_aws_ssm):
    exception_msg = "Connection timeout??!!"
    connection_aws_ssm.exec_communicate = MagicMock()
    connection_aws_ssm.exec_communicate.side_effect = AnsibleConnectionFailure(exception_msg)

    with pytest.raises(AnsibleConnectionFailure) as exc_info:
        connection_aws_ssm.exec_communicate("ansible-test units", None, MagicMock(), MagicMock(), MagicMock())

    assert str(exc_info.value) == exception_msg


@pytest.mark.parametrize("is_windows", [True, False])
@patch("ansible_collections.amazon.aws.plugins.connection.aws_ssm.chunks")
def test_connection_aws_ssm_exec_command(m_chunks, connection_aws_ssm, is_windows):
    connection_aws_ssm.is_windows = is_windows
    connection_aws_ssm.exec_communicate = MagicMock()
    connection_aws_ssm.reconnection_retries = 5
    result = MagicMock()
    connection_aws_ssm.exec_communicate.return_value = result

    chunk = MagicMock()
    m_chunks.return_value = [chunk]

    cmd = MagicMock()
    in_data = MagicMock()
    sudoable = MagicMock()
    connection_aws_ssm.terminal_manager = MagicMock()

    assert result == connection_aws_ssm.exec_command(cmd, in_data, sudoable)
    # m_chunks.assert_called_once_with(chunk, 1024)
    connection_aws_ssm.session_manager.flush_stderr.assert_called_once_with()


@pytest.mark.parametrize(
    "stdout_input,expected_returncode,expected_stdout,is_windows",
    [
        # Linux: output format is: <output>\n\n<returncode>\n
        ("some output\nmore output\n\n0\n", 0, "some output\nmore output", False),
        ("single line\n\n42\n", 42, "single line", False),
        ("multi\nline\noutput\n\n1\n", 1, "multi\nline\noutput", False),
        # Windows: same format, but with JSON output test
        ('{"result": "data"}\n\n0\n', 0, '{"result": "data"}', True),
        ("plain text\n\n0\n", 0, "plain text", True),
        # Windows with CLIXML filtering
        ("output\n#< CLIXML <Objs></Objs>more\n\n0\n", 0, "output\nmore", True),
    ],
)
def test_connection_aws_ssm_post_process(connection_aws_ssm, stdout_input, expected_returncode, expected_stdout, is_windows):
    connection_aws_ssm.is_windows = is_windows
    mark_begin = "MARK_START"

    returncode, stdout = connection_aws_ssm._post_process(stdout_input, mark_begin)

    assert returncode == expected_returncode
    assert stdout == expected_stdout


def test_connection_aws_ssm_post_process_invalid_returncode(connection_aws_ssm):
    """Test that _post_process handles invalid return codes gracefully"""
    connection_aws_ssm.is_windows = False
    stdout_input = "output\n\nnot_a_number\n"

    returncode, stdout = connection_aws_ssm._post_process(stdout_input, "MARK")

    # Should return 32 when return code is not a valid integer
    assert returncode == 32
    assert stdout == "output"
