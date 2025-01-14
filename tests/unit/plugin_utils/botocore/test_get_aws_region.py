# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import sentinel

import pytest

import ansible_collections.amazon.aws.plugins.plugin_utils.botocore as utils_botocore
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleBotocoreError


class FailException(Exception):
    pass


@pytest.fixture(name="aws_plugin")
def fixture_aws_plugin(monkeypatch):
    aws_plugin = MagicMock()
    aws_plugin.fail_aws.side_effect = FailException()
    aws_plugin.get_options.return_value = sentinel.PLUGIN_OPTIONS

    return aws_plugin


@pytest.fixture(name="botocore_utils")
def fixture_botocore_utils(monkeypatch):
    return utils_botocore


###############################################################
# module_utils.botocore.get_aws_region
###############################################################
def test_get_aws_region_simple_plugin(monkeypatch, aws_plugin, botocore_utils):
    region_method = MagicMock(name="_aws_region")
    monkeypatch.setattr(botocore_utils, "_aws_region", region_method)
    region_method.return_value = sentinel.RETURNED_REGION

    assert botocore_utils.get_aws_region(aws_plugin) is sentinel.RETURNED_REGION
    passed_args = region_method.call_args
    assert passed_args == call(sentinel.PLUGIN_OPTIONS)
    # args[0]
    assert passed_args[0][0] is sentinel.PLUGIN_OPTIONS


def test_get_aws_region_exception_nested_plugin(monkeypatch, aws_plugin, botocore_utils):
    region_method = MagicMock(name="_aws_region")
    monkeypatch.setattr(botocore_utils, "_aws_region", region_method)

    exception_nested = AnsibleBotocoreError(message=sentinel.ERROR_MSG, exception=sentinel.ERROR_EX)
    region_method.side_effect = exception_nested

    with pytest.raises(FailException):
        assert botocore_utils.get_aws_region(aws_plugin)

    passed_args = region_method.call_args
    assert passed_args == call(sentinel.PLUGIN_OPTIONS)
    # call_args[0] == positional args
    assert passed_args[0][0] is sentinel.PLUGIN_OPTIONS

    fail_args = aws_plugin.fail_aws.call_args
    assert fail_args == call("sentinel.ERROR_MSG: sentinel.ERROR_EX")


def test_get_aws_region_exception_msg_plugin(monkeypatch, aws_plugin, botocore_utils):
    region_method = MagicMock(name="_aws_region")
    monkeypatch.setattr(botocore_utils, "_aws_region", region_method)

    exception_nested = AnsibleBotocoreError(message=sentinel.ERROR_MSG)
    region_method.side_effect = exception_nested

    with pytest.raises(FailException):
        assert botocore_utils.get_aws_region(aws_plugin)

    passed_args = region_method.call_args
    assert passed_args == call(sentinel.PLUGIN_OPTIONS)
    # call_args[0] == positional args
    assert passed_args[0][0] is sentinel.PLUGIN_OPTIONS

    fail_args = aws_plugin.fail_aws.call_args
    assert fail_args == call("sentinel.ERROR_MSG")
