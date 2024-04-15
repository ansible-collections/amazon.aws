# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import warnings
from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import sentinel

import pytest

import ansible_collections.amazon.aws.plugins.module_utils.modules as utils_module


@pytest.mark.parametrize("stdin", [{}], indirect=["stdin"])
def test_params(monkeypatch, stdin):
    aws_module = utils_module.AnsibleAWSModule(argument_spec=dict())
    monkeypatch.setattr(aws_module._module, "params", sentinel.RETURNED_PARAMS)

    assert aws_module.params is sentinel.RETURNED_PARAMS


@pytest.mark.parametrize("stdin", [{}], indirect=["stdin"])
def test_debug(monkeypatch, stdin):
    aws_module = utils_module.AnsibleAWSModule(argument_spec=dict())
    monkeypatch.setattr(aws_module._module, "debug", warnings.warn)

    with pytest.warns(UserWarning, match="My debug message"):
        aws_module.debug("My debug message")


@pytest.mark.parametrize("stdin", [{}], indirect=["stdin"])
def test_warn(monkeypatch, stdin):
    aws_module = utils_module.AnsibleAWSModule(argument_spec=dict())
    monkeypatch.setattr(aws_module._module, "warn", warnings.warn)

    with pytest.warns(UserWarning, match="My warning message"):
        aws_module.warn("My warning message")


@pytest.mark.parametrize("stdin", [{}], indirect=["stdin"])
def test_deprecate(monkeypatch, stdin):
    kwargs = {"example": sentinel.KWARG}
    deprecate = MagicMock(name="deprecate")
    deprecate.return_value = sentinel.RET_DEPRECATE

    aws_module = utils_module.AnsibleAWSModule(argument_spec=dict())
    monkeypatch.setattr(aws_module._module, "deprecate", deprecate)
    assert aws_module.deprecate(sentinel.PARAM_DEPRECATE, **kwargs) is sentinel.RET_DEPRECATE
    assert deprecate.call_args == call(sentinel.PARAM_DEPRECATE, **kwargs)


@pytest.mark.parametrize("stdin", [{}], indirect=["stdin"])
def test_gather_versions(monkeypatch, stdin):
    gather_sdk_versions = MagicMock(name="gather_sdk_versions")
    gather_sdk_versions.return_value = sentinel.RETURNED_SDK_VERSIONS
    monkeypatch.setattr(utils_module, "gather_sdk_versions", gather_sdk_versions)
    aws_module = utils_module.AnsibleAWSModule(argument_spec=dict())

    assert aws_module._gather_versions() is sentinel.RETURNED_SDK_VERSIONS
    assert gather_sdk_versions.call_args == call()


@pytest.mark.parametrize("stdin", [{}], indirect=["stdin"])
def test_region(monkeypatch, stdin):
    get_aws_region = MagicMock(name="get_aws_region")
    get_aws_region.return_value = sentinel.RETURNED_REGION
    monkeypatch.setattr(utils_module, "get_aws_region", get_aws_region)
    aws_module = utils_module.AnsibleAWSModule(argument_spec=dict())

    assert aws_module.region is sentinel.RETURNED_REGION
    assert get_aws_region.call_args == call(aws_module)


@pytest.mark.parametrize("stdin", [{}], indirect=["stdin"])
def test_boto3_at_least(monkeypatch, stdin):
    boto3_at_least = MagicMock(name="boto3_at_least")
    boto3_at_least.return_value = sentinel.RET_BOTO3_AT_LEAST
    monkeypatch.setattr(utils_module, "boto3_at_least", boto3_at_least)

    aws_module = utils_module.AnsibleAWSModule(argument_spec=dict())
    assert aws_module.boto3_at_least(sentinel.PARAM_BOTO3) is sentinel.RET_BOTO3_AT_LEAST
    assert boto3_at_least.call_args == call(sentinel.PARAM_BOTO3)


@pytest.mark.parametrize("stdin", [{}], indirect=["stdin"])
def test_botocore_at_least(monkeypatch, stdin):
    botocore_at_least = MagicMock(name="botocore_at_least")
    botocore_at_least.return_value = sentinel.RET_BOTOCORE_AT_LEAST
    monkeypatch.setattr(utils_module, "botocore_at_least", botocore_at_least)

    aws_module = utils_module.AnsibleAWSModule(argument_spec=dict())
    assert aws_module.botocore_at_least(sentinel.PARAM_BOTOCORE) is sentinel.RET_BOTOCORE_AT_LEAST
    assert botocore_at_least.call_args == call(sentinel.PARAM_BOTOCORE)


@pytest.mark.parametrize("stdin", [{}], indirect=["stdin"])
def test_boolean(monkeypatch, stdin):
    boolean = MagicMock(name="boolean")
    boolean.return_value = sentinel.RET_BOOLEAN

    aws_module = utils_module.AnsibleAWSModule(argument_spec=dict())
    monkeypatch.setattr(aws_module._module, "boolean", boolean)
    assert aws_module.boolean(sentinel.PARAM_BOOLEAN) is sentinel.RET_BOOLEAN
    assert boolean.call_args == call(sentinel.PARAM_BOOLEAN)


@pytest.mark.parametrize("stdin", [{}], indirect=["stdin"])
def test_md5(monkeypatch, stdin):
    md5 = MagicMock(name="md5")
    md5.return_value = sentinel.RET_MD5

    aws_module = utils_module.AnsibleAWSModule(argument_spec=dict())
    monkeypatch.setattr(aws_module._module, "md5", md5)
    assert aws_module.md5(sentinel.PARAM_MD5) is sentinel.RET_MD5
    assert md5.call_args == call(sentinel.PARAM_MD5)


@pytest.mark.parametrize("stdin", [{}], indirect=["stdin"])
def test_client_no_wrapper(monkeypatch, stdin):
    get_aws_connection_info = MagicMock(name="get_aws_connection_info")
    sentinel.CONN_ARGS = dict()
    get_aws_connection_info.return_value = (sentinel.CONN_REGION, sentinel.CONN_URL, sentinel.CONN_ARGS)
    monkeypatch.setattr(utils_module, "get_aws_connection_info", get_aws_connection_info)
    boto3_conn = MagicMock(name="boto3_conn")
    boto3_conn.return_value = sentinel.BOTO3_CONN
    monkeypatch.setattr(utils_module, "boto3_conn", boto3_conn)

    aws_module = utils_module.AnsibleAWSModule(argument_spec=dict())
    assert aws_module.client(sentinel.PARAM_SERVICE) is sentinel.BOTO3_CONN
    assert get_aws_connection_info.call_args == call(aws_module)
    assert boto3_conn.call_args == call(
        aws_module,
        conn_type="client",
        resource=sentinel.PARAM_SERVICE,
        region=sentinel.CONN_REGION,
        endpoint=sentinel.CONN_URL,
    )


@pytest.mark.parametrize("stdin", [{}], indirect=["stdin"])
def test_client_wrapper(monkeypatch, stdin):
    get_aws_connection_info = MagicMock(name="get_aws_connection_info")
    sentinel.CONN_ARGS = dict()
    get_aws_connection_info.return_value = (sentinel.CONN_REGION, sentinel.CONN_URL, sentinel.CONN_ARGS)
    monkeypatch.setattr(utils_module, "get_aws_connection_info", get_aws_connection_info)
    boto3_conn = MagicMock(name="boto3_conn")
    boto3_conn.return_value = sentinel.BOTO3_CONN
    monkeypatch.setattr(utils_module, "boto3_conn", boto3_conn)

    aws_module = utils_module.AnsibleAWSModule(argument_spec=dict())
    wrapped_conn = aws_module.client(sentinel.PARAM_SERVICE, sentinel.PARAM_WRAPPER)
    assert wrapped_conn.client is sentinel.BOTO3_CONN
    assert wrapped_conn.retry is sentinel.PARAM_WRAPPER
    assert get_aws_connection_info.call_args == call(aws_module)
    assert boto3_conn.call_args == call(
        aws_module,
        conn_type="client",
        resource=sentinel.PARAM_SERVICE,
        region=sentinel.CONN_REGION,
        endpoint=sentinel.CONN_URL,
    )

    # Check that we can override parameters
    wrapped_conn = aws_module.client(sentinel.PARAM_SERVICE, sentinel.PARAM_WRAPPER, region=sentinel.PARAM_REGION)
    assert wrapped_conn.client is sentinel.BOTO3_CONN
    assert wrapped_conn.retry is sentinel.PARAM_WRAPPER
    assert get_aws_connection_info.call_args == call(aws_module)
    assert boto3_conn.call_args == call(
        aws_module,
        conn_type="client",
        resource=sentinel.PARAM_SERVICE,
        region=sentinel.PARAM_REGION,
        endpoint=sentinel.CONN_URL,
    )


@pytest.mark.parametrize("stdin", [{}], indirect=["stdin"])
def test_resource(monkeypatch, stdin):
    get_aws_connection_info = MagicMock(name="get_aws_connection_info")
    sentinel.CONN_ARGS = dict()
    get_aws_connection_info.return_value = (sentinel.CONN_REGION, sentinel.CONN_URL, sentinel.CONN_ARGS)
    monkeypatch.setattr(utils_module, "get_aws_connection_info", get_aws_connection_info)
    boto3_conn = MagicMock(name="boto3_conn")
    boto3_conn.return_value = sentinel.BOTO3_CONN
    monkeypatch.setattr(utils_module, "boto3_conn", boto3_conn)

    aws_module = utils_module.AnsibleAWSModule(argument_spec=dict())
    assert aws_module.resource(sentinel.PARAM_SERVICE) is sentinel.BOTO3_CONN
    assert get_aws_connection_info.call_args == call(aws_module)
    assert boto3_conn.call_args == call(
        aws_module,
        conn_type="resource",
        resource=sentinel.PARAM_SERVICE,
        region=sentinel.CONN_REGION,
        endpoint=sentinel.CONN_URL,
    )

    # Check that we can override parameters
    assert aws_module.resource(sentinel.PARAM_SERVICE, region=sentinel.PARAM_REGION) is sentinel.BOTO3_CONN
    assert get_aws_connection_info.call_args == call(aws_module)
    assert boto3_conn.call_args == call(
        aws_module,
        conn_type="resource",
        resource=sentinel.PARAM_SERVICE,
        region=sentinel.PARAM_REGION,
        endpoint=sentinel.CONN_URL,
    )
