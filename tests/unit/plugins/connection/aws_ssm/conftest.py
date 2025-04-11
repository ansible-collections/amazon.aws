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
    connection.is_windows = False

    connection.session_manager = MagicMock()

    def display_msg(msg):
        print("--- AWS SSM CONNECTION --- ", msg)

    connection.verbosity_display = MagicMock()
    connection.verbosity_display.side_effect = lambda level, msg: display_msg(msg)

    connection.get_option = MagicMock()
    return connection
