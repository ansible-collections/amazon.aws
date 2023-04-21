# (c) 2023 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import sentinel

from ansible.errors import AnsibleConnectionFailure

import ansible_collections.amazon.aws.plugins.plugin_utils.connection as utils_connection


# pylint: disable=abstract-class-instantiated
def test_fail(monkeypatch):
    monkeypatch.setattr(utils_connection.AWSConnectionBase, "__abstractmethods__", set())
    monkeypatch.setattr(utils_connection.ConnectionBase, "__init__", MagicMock(name="__init__"))

    connection_plugin = utils_connection.AWSConnectionBase()
    with pytest.raises(AnsibleConnectionFailure, match=str(sentinel.ERROR_MSG)):
        connection_plugin._do_fail(sentinel.ERROR_MSG)


# pylint: disable=abstract-class-instantiated
def test_init(monkeypatch):
    kwargs = {"example": sentinel.KWARG}
    require_aws_sdk = MagicMock(name="require_aws_sdk")
    require_aws_sdk.return_value = sentinel.RETURNED_SDK

    monkeypatch.setattr(utils_connection.AWSConnectionBase, "__abstractmethods__", set())
    monkeypatch.setattr(utils_connection.ConnectionBase, "__init__", MagicMock(name="__init__"))
    monkeypatch.setattr(utils_connection.AWSConnectionBase, "require_aws_sdk", require_aws_sdk)

    connection_plugin = utils_connection.AWSConnectionBase(sentinel.PARAM_TERMS, sentinel.PARAM_VARS, **kwargs)
    assert require_aws_sdk.call_args == call(botocore_version=None, boto3_version=None)

    connection_plugin = utils_connection.AWSConnectionBase(
        sentinel.PARAM_ONE,
        sentinel.PARAM_TWO,
        boto3_version=sentinel.PARAM_BOTO3,
        botocore_version=sentinel.PARAM_BOTOCORE,
        **kwargs,
    )
    assert require_aws_sdk.call_args == call(
        botocore_version=sentinel.PARAM_BOTOCORE, boto3_version=sentinel.PARAM_BOTO3
    )
