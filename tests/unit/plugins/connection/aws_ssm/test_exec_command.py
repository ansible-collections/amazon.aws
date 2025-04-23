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
            ["L_START_1", "SOME_CONTENT", "L_END_1"],
            "SOME_CONTENT",
        ),
        (
            "L_START_2",
            "L_END_2",
            ["L_START_2", "FIRST", "+", "SECOND", "L_END_2"],
            "FIRST+SECOND",
        ),
    ],
)
@patch("ansible_collections.community.aws.plugins.connection.aws_ssm.filter_ansi")
def test_connection_aws_ssm_exec_communicate(
    m_filter_ansi, connection_aws_ssm, mark_start, mark_end, stdout_lines, expected_stdout
):
    m_filter_ansi.side_effect = lambda line, is_windows: line
    connection_aws_ssm.poll = MagicMock()

    def _poll(trc, cmd):
        while True:
            yield True

    connection_aws_ssm.session_manager.poll.side_effect = _poll
    connection_aws_ssm.session_manager.stdout_readline.side_effect = stdout_lines
    connection_aws_ssm._post_process = MagicMock()
    returncode = MagicMock()
    connection_aws_ssm._post_process.side_effect = lambda line, marker: (returncode, line)

    stderr = MagicMock()
    connection_aws_ssm.session_manager.flush_stderr.return_value = stderr

    result_returncode, result_stdout, result_stderr = connection_aws_ssm.exec_communicate(
        "ansible-test units", mark_start, mark_start, mark_end
    )

    assert result_returncode == returncode
    assert result_stdout == expected_stdout
    assert stderr == result_stderr


def test_connection_aws_ssm_exec_communicate_with_exception(connection_aws_ssm):
    exception_msg = "Connection timeout??!!"
    connection_aws_ssm.exec_communicate = MagicMock()
    connection_aws_ssm.exec_communicate.side_effect = AnsibleConnectionFailure(exception_msg)

    with pytest.raises(AnsibleConnectionFailure) as exc_info:
        connection_aws_ssm.exec_communicate("ansible-test units", MagicMock(), MagicMock(), MagicMock())

    assert str(exc_info.value) == exception_msg


@pytest.mark.parametrize("is_windows", [True, False])
@patch("ansible_collections.community.aws.plugins.connection.aws_ssm.chunks")
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
