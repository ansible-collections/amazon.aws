# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import sentinel
import warnings

from ansible.errors import AnsibleError

import ansible_collections.amazon.aws.plugins.plugin_utils.base as utils_base


def test_debug(monkeypatch):
    monkeypatch.setattr(utils_base.display, "debug", warnings.warn)
    base_plugin = utils_base.AWSPluginBase()

    with pytest.warns(UserWarning, match="My debug message"):
        base_plugin.debug("My debug message")


def test_warn(monkeypatch):
    monkeypatch.setattr(utils_base.display, "warning", warnings.warn)
    base_plugin = utils_base.AWSPluginBase()

    with pytest.warns(UserWarning, match="My warning message"):
        base_plugin.warn("My warning message")


def test_do_fail():
    base_plugin = utils_base.AWSPluginBase()

    with pytest.raises(AnsibleError, match="My exception message"):
        base_plugin._do_fail("My exception message")


def test_fail_aws():
    base_plugin = utils_base.AWSPluginBase()
    example_exception = Exception("My example exception")
    example_message = "My example failure message"

    with pytest.raises(AnsibleError, match="My example failure message"):
        base_plugin.fail_aws(example_message)

    with pytest.raises(AnsibleError, match="My example failure message"):
        base_plugin.fail_aws(message=example_message)

    # As long as example_example_exception is supported by to_native, we're good.
    with pytest.raises(AnsibleError, match="My example exception"):
        base_plugin.fail_aws(example_exception)

    with pytest.raises(AnsibleError, match="My example failure message: My example exception"):
        base_plugin.fail_aws(example_message, example_exception)

    with pytest.raises(AnsibleError, match="My example failure message: My example exception"):
        base_plugin.fail_aws(message=example_message, exception=example_exception)


def test_region(monkeypatch):
    get_aws_region = MagicMock(name="get_aws_region")
    get_aws_region.return_value = sentinel.RETURNED_REGION
    monkeypatch.setattr(utils_base, "get_aws_region", get_aws_region)
    base_plugin = utils_base.AWSPluginBase()

    assert base_plugin.region is sentinel.RETURNED_REGION
    assert get_aws_region.call_args == call(base_plugin)


def test_require_aws_sdk(monkeypatch):
    require_sdk = MagicMock(name="check_sdk_version_supported")
    require_sdk.return_value = sentinel.RETURNED_SDK
    monkeypatch.setattr(utils_base, "check_sdk_version_supported", require_sdk)

    base_plugin = utils_base.AWSPluginBase()
    assert base_plugin.require_aws_sdk() is sentinel.RETURNED_SDK
    assert require_sdk.call_args == call(botocore_version=None, boto3_version=None, warn=base_plugin.warn)

    base_plugin = utils_base.AWSPluginBase()
    assert (
        base_plugin.require_aws_sdk(botocore_version=sentinel.PARAM_BOTOCORE, boto3_version=sentinel.PARAM_BOTO3)
        is sentinel.RETURNED_SDK
    )
    assert require_sdk.call_args == call(
        botocore_version=sentinel.PARAM_BOTOCORE, boto3_version=sentinel.PARAM_BOTO3, warn=base_plugin.warn
    )


def test_client_no_wrapper(monkeypatch):
    get_aws_connection_info = MagicMock(name="get_aws_connection_info")
    sentinel.CONN_ARGS = dict()
    get_aws_connection_info.return_value = (sentinel.CONN_REGION, sentinel.CONN_URL, sentinel.CONN_ARGS)
    monkeypatch.setattr(utils_base, "get_aws_connection_info", get_aws_connection_info)
    boto3_conn = MagicMock(name="boto3_conn")
    boto3_conn.return_value = sentinel.BOTO3_CONN
    monkeypatch.setattr(utils_base, "boto3_conn", boto3_conn)

    base_plugin = utils_base.AWSPluginBase()
    assert base_plugin.client(sentinel.PARAM_SERVICE) is sentinel.BOTO3_CONN
    assert get_aws_connection_info.call_args == call(base_plugin)
    assert boto3_conn.call_args == call(
        base_plugin,
        conn_type="client",
        resource=sentinel.PARAM_SERVICE,
        region=sentinel.CONN_REGION,
        endpoint=sentinel.CONN_URL,
    )


def test_client_wrapper(monkeypatch):
    get_aws_connection_info = MagicMock(name="get_aws_connection_info")
    sentinel.CONN_ARGS = dict()
    get_aws_connection_info.return_value = (sentinel.CONN_REGION, sentinel.CONN_URL, sentinel.CONN_ARGS)
    monkeypatch.setattr(utils_base, "get_aws_connection_info", get_aws_connection_info)
    boto3_conn = MagicMock(name="boto3_conn")
    boto3_conn.return_value = sentinel.BOTO3_CONN
    monkeypatch.setattr(utils_base, "boto3_conn", boto3_conn)

    base_plugin = utils_base.AWSPluginBase()
    wrapped_conn = base_plugin.client(sentinel.PARAM_SERVICE, sentinel.PARAM_WRAPPER)
    assert wrapped_conn.client is sentinel.BOTO3_CONN
    assert wrapped_conn.retry is sentinel.PARAM_WRAPPER
    assert get_aws_connection_info.call_args == call(base_plugin)
    assert boto3_conn.call_args == call(
        base_plugin,
        conn_type="client",
        resource=sentinel.PARAM_SERVICE,
        region=sentinel.CONN_REGION,
        endpoint=sentinel.CONN_URL,
    )

    # Check that we can override parameters
    wrapped_conn = base_plugin.client(sentinel.PARAM_SERVICE, sentinel.PARAM_WRAPPER, region=sentinel.PARAM_REGION)
    assert wrapped_conn.client is sentinel.BOTO3_CONN
    assert wrapped_conn.retry is sentinel.PARAM_WRAPPER
    assert get_aws_connection_info.call_args == call(base_plugin)
    assert boto3_conn.call_args == call(
        base_plugin,
        conn_type="client",
        resource=sentinel.PARAM_SERVICE,
        region=sentinel.PARAM_REGION,
        endpoint=sentinel.CONN_URL,
    )


def test_resource(monkeypatch):
    get_aws_connection_info = MagicMock(name="get_aws_connection_info")
    sentinel.CONN_ARGS = dict()
    get_aws_connection_info.return_value = (sentinel.CONN_REGION, sentinel.CONN_URL, sentinel.CONN_ARGS)
    monkeypatch.setattr(utils_base, "get_aws_connection_info", get_aws_connection_info)
    boto3_conn = MagicMock(name="boto3_conn")
    boto3_conn.return_value = sentinel.BOTO3_CONN
    monkeypatch.setattr(utils_base, "boto3_conn", boto3_conn)

    base_plugin = utils_base.AWSPluginBase()
    assert base_plugin.resource(sentinel.PARAM_SERVICE) is sentinel.BOTO3_CONN
    assert get_aws_connection_info.call_args == call(base_plugin)
    assert boto3_conn.call_args == call(
        base_plugin,
        conn_type="resource",
        resource=sentinel.PARAM_SERVICE,
        region=sentinel.CONN_REGION,
        endpoint=sentinel.CONN_URL,
    )

    assert base_plugin.resource(sentinel.PARAM_SERVICE, region=sentinel.PARAM_REGION) is sentinel.BOTO3_CONN
    assert get_aws_connection_info.call_args == call(base_plugin)
    assert boto3_conn.call_args == call(
        base_plugin,
        conn_type="resource",
        resource=sentinel.PARAM_SERVICE,
        region=sentinel.PARAM_REGION,
        endpoint=sentinel.CONN_URL,
    )
