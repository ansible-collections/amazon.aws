# -*- coding: utf-8 -*-

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock

import pytest

from ansible_collections.community.aws.plugins.connection.aws_ssm import Connection
from ansible_collections.community.aws.plugins.connection.aws_ssm import ConnectionBase


@pytest.fixture(name="connection_aws_ssm")
def fixture_connection_aws_ssm():
    play_context = MagicMock()
    play_context.shell = True

    def connection_init(*args, **kwargs):
        pass

    Connection.__init__ = connection_init
    ConnectionBase.exec_command = MagicMock()
    connection = Connection()

    connection._instance_id = "i-0a1b2c3d4e5f"
    connection._polling_obj = None
    connection._has_timeout = False
    connection.is_windows = False

    connection.poll_stdout = MagicMock()
    connection._session = MagicMock()
    connection._session.poll = MagicMock()
    connection._session.poll.side_effect = lambda: None
    connection._session.stdin = MagicMock()
    connection._session.stdin.write = MagicMock()
    connection._stdout = MagicMock()
    connection._flush_stderr = MagicMock()

    def display_msg(msg):
        print("--- AWS SSM CONNECTION --- ", msg)

    connection._v = MagicMock()
    connection._v.side_effect = display_msg

    connection._vv = MagicMock()
    connection._vv.side_effect = display_msg

    connection._vvv = MagicMock()
    connection._vvv.side_effect = display_msg

    connection._vvvv = MagicMock()
    connection._vvvv.side_effect = display_msg

    connection.get_option = MagicMock()
    return connection
