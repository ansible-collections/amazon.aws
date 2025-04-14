# -*- coding: utf-8 -*-

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# While it may seem appropriate to import our custom fixtures here, the pytest_ansible pytest plugin
# isn't as agressive as the ansible_test._util.target.pytest.plugins.ansible_pytest_collections plugin
# when it comes to rewriting the import paths and as such we can't import fixtures via their
# absolute import path or across collections.


import re
from unittest.mock import ANY
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3

from ansible_collections.community.aws.plugins.connection.aws_ssm import TerminalManager

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_poll.py requires the python modules 'boto3' and 'botocore'")


def test_ensure_ssm_session_has_started(connection_aws_ssm):
    if not hasattr(connection_aws_ssm, "terminal_manager"):
        connection_aws_ssm.terminal_manager = TerminalManager(connection_aws_ssm)

    connection_aws_ssm.terminal_manager.ensure_ssm_session_has_started()
    connection_aws_ssm.session_manager.wait_for_match.assert_called_once_with(
        label="START SSM SESSION", cmd="start_session", match="Starting session with SessionId"
    )


@patch("ansible_collections.community.aws.plugins.plugin_utils.ssm.terminalmanager.to_bytes")
@patch("ansible_collections.community.aws.plugins.plugin_utils.ssm.terminalmanager.to_text")
def test_disable_echo_command(m_to_text, m_to_bytes, connection_aws_ssm):
    m_to_text.side_effect = str
    m_to_bytes.side_effect = lambda x, **kw: str(x)

    if not hasattr(connection_aws_ssm, "terminal_manager"):
        connection_aws_ssm.terminal_manager = TerminalManager(connection_aws_ssm)

    connection_aws_ssm.terminal_manager.disable_echo_command()
    connection_aws_ssm.session_manager.stdin_write.assert_called_once_with("stty -echo\n")
    connection_aws_ssm.session_manager.wait_for_match.assert_called_once_with(
        label="DISABLE ECHO", cmd="stty -echo\n", match="stty -echo"
    )


@patch("ansible_collections.community.aws.plugins.plugin_utils.ssm.terminalmanager.random")
@patch("ansible_collections.community.aws.plugins.plugin_utils.ssm.terminalmanager.to_bytes")
@patch("ansible_collections.community.aws.plugins.plugin_utils.ssm.terminalmanager.to_text")
def test_disable_prompt_command(m_to_text, m_to_bytes, m_random, connection_aws_ssm):
    m_to_text.side_effect = str
    m_to_bytes.side_effect = lambda x, **kw: str(x)

    if not hasattr(connection_aws_ssm, "terminal_manager"):
        connection_aws_ssm.terminal_manager = TerminalManager(connection_aws_ssm)

    m_random.choice = MagicMock()
    m_random.choice.side_effect = lambda x: "a"

    end_mark = "".join(["a" for i in range(connection_aws_ssm.MARK_LENGTH)])

    prompt_cmd = f"PS1='' ; bind 'set enable-bracketed-paste off'; printf '\\n%s\\n' '{end_mark}'\n"

    connection_aws_ssm.terminal_manager.disable_prompt_command()

    connection_aws_ssm.session_manager.stdin_write.assert_called_once_with(prompt_cmd)
    disable_prompt_reply = re.compile(r"\r\r\n" + re.escape(end_mark) + r"\r\r\n", re.MULTILINE)
    connection_aws_ssm.session_manager.wait_for_match.assert_called_once_with(
        label="DISABLE PROMPT", cmd=ANY, match=disable_prompt_reply.search
    )
