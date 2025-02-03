# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from copy import deepcopy
from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import sentinel

import pytest

try:
    import botocore
except ImportError:
    # Handled by HAS_BOTO3
    pass

import ansible_collections.amazon.aws.plugins.module_utils.botocore as utils_botocore
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleBotocoreError

CREDENTIAL_MAP = dict(
    access_key="aws_access_key_id",
    secret_key="aws_secret_access_key",
    session_token="aws_session_token",
)
BLANK_BOTO_PARAMS = dict(aws_access_key_id=None, aws_secret_access_key=None, aws_session_token=None, verify=None)


class FailException(Exception):
    pass


@pytest.fixture(name="aws_module")
def fixture_aws_module(monkeypatch):
    aws_module = MagicMock()
    aws_module.fail_json.side_effect = FailException()
    aws_module.fail_json_aws.side_effect = FailException()
    monkeypatch.setattr(aws_module, "params", sentinel.MODULE_PARAMS)
    return aws_module


@pytest.fixture(name="fake_botocore")
def fixture_fake_botocore(monkeypatch):
    # Note: this isn't a monkey-patched real-botocore, this is a complete fake.
    fake_session = MagicMock()
    fake_session.get_config_variable.return_value = sentinel.BOTO3_REGION
    fake_session_module = MagicMock()
    fake_session_module.Session.return_value = fake_session
    fake_config_module = MagicMock()
    fake_config_module.Config.return_value = sentinel.BOTO3_CONFIG
    fake_botocore = MagicMock()
    monkeypatch.setattr(fake_botocore, "session", fake_session_module)
    monkeypatch.setattr(fake_botocore, "config", fake_config_module)
    # Patch exceptions in
    monkeypatch.setattr(fake_botocore, "exceptions", botocore.exceptions)

    return fake_botocore


@pytest.fixture(name="botocore_utils")
def fixture_botocore_utils(monkeypatch):
    region_method = MagicMock(name="_aws_region")
    monkeypatch.setattr(utils_botocore, "_aws_region", region_method)
    region_method.return_value = sentinel.RETURNED_REGION
    return utils_botocore


###############################################################
# module_utils.botocore.get_aws_connection_info
###############################################################
def test_get_aws_connection_info_simple(monkeypatch, aws_module, botocore_utils):
    connection_info_method = MagicMock(name="_aws_connection_info")
    monkeypatch.setattr(botocore_utils, "_aws_connection_info", connection_info_method)
    connection_info_method.return_value = sentinel.RETURNED_INFO

    assert botocore_utils.get_aws_connection_info(aws_module) is sentinel.RETURNED_INFO
    passed_args = connection_info_method.call_args
    assert passed_args == call(sentinel.MODULE_PARAMS)
    # args[0]
    assert passed_args[0][0] is sentinel.MODULE_PARAMS


def test_get_aws_connection_info_exception_nested(monkeypatch, aws_module, botocore_utils):
    connection_info_method = MagicMock(name="_aws_connection_info")
    monkeypatch.setattr(botocore_utils, "_aws_connection_info", connection_info_method)

    exception_nested = AnsibleBotocoreError(message=sentinel.ERROR_MSG, exception=sentinel.ERROR_EX)
    connection_info_method.side_effect = exception_nested

    with pytest.raises(FailException):
        botocore_utils.get_aws_connection_info(aws_module)

    passed_args = connection_info_method.call_args
    assert passed_args == call(sentinel.MODULE_PARAMS)
    # call_args[0] == positional args
    assert passed_args[0][0] is sentinel.MODULE_PARAMS

    fail_args = aws_module.fail_json.call_args
    assert fail_args == call(msg=sentinel.ERROR_MSG, exception=sentinel.ERROR_EX)
    # call_args[1] == kwargs
    assert fail_args[1]["msg"] is sentinel.ERROR_MSG
    assert fail_args[1]["exception"] is sentinel.ERROR_EX


def test_get_aws_connection_info_exception_msg(monkeypatch, aws_module, botocore_utils):
    connection_info_method = MagicMock(name="_aws_connection_info")
    monkeypatch.setattr(botocore_utils, "_aws_connection_info", connection_info_method)

    exception_nested = AnsibleBotocoreError(message=sentinel.ERROR_MSG)
    connection_info_method.side_effect = exception_nested

    with pytest.raises(FailException):
        botocore_utils.get_aws_connection_info(aws_module)

    passed_args = connection_info_method.call_args
    assert passed_args == call(sentinel.MODULE_PARAMS)
    # call_args[0] == positional args
    assert passed_args[0][0] is sentinel.MODULE_PARAMS

    fail_args = aws_module.fail_json.call_args
    assert fail_args == call(msg=sentinel.ERROR_MSG)
    # call_args[1] == kwargs
    assert fail_args[1]["msg"] is sentinel.ERROR_MSG


###############################################################
# module_utils.botocore._get_aws_connection_info
###############################################################
@pytest.mark.parametrize("param_name", ["access_key", "secret_key", "session_token"])
def test_aws_connection_info_single_cred(monkeypatch, botocore_utils, param_name):
    options = {param_name: sentinel.PARAM_CRED, "profile": sentinel.PARAM_PROFILE}
    blank_params = deepcopy(BLANK_BOTO_PARAMS)
    boto_param_name = CREDENTIAL_MAP[param_name]
    expected_params = deepcopy(blank_params)
    expected_params[boto_param_name] = sentinel.PARAM_CRED

    # profile + cred is explicitly not supported
    with pytest.raises(AnsibleBotocoreError, match="Passing both"):
        botocore_utils._aws_connection_info(options)

    # However a blank/empty profile is ok.
    options["profile"] = None
    region, endpoint_url, boto_params = botocore_utils._aws_connection_info(options)
    assert region is sentinel.RETURNED_REGION
    assert endpoint_url is None
    assert boto_params == expected_params
    assert boto_params[boto_param_name] is sentinel.PARAM_CRED

    options["profile"] = ""
    region, endpoint_url, boto_params = botocore_utils._aws_connection_info(options)
    assert region is sentinel.RETURNED_REGION
    assert endpoint_url is None
    assert boto_params == expected_params
    assert boto_params[boto_param_name] is sentinel.PARAM_CRED

    del options["profile"]

    region, endpoint_url, boto_params = botocore_utils._aws_connection_info(options)
    assert region is sentinel.RETURNED_REGION
    assert endpoint_url is None
    assert boto_params == expected_params
    assert boto_params[boto_param_name] is sentinel.PARAM_CRED

    options[param_name] = None
    region, endpoint_url, boto_params = botocore_utils._aws_connection_info(options)
    assert region is sentinel.RETURNED_REGION
    assert endpoint_url is None
    assert boto_params == blank_params
    assert boto_params[boto_param_name] is None

    options[param_name] = ""
    region, endpoint_url, boto_params = botocore_utils._aws_connection_info(options)
    assert region is sentinel.RETURNED_REGION
    assert endpoint_url is None
    assert boto_params == blank_params
    assert boto_params[boto_param_name] is None

    options[param_name] = b"Originally bytes String"
    expected_params[boto_param_name] = "Originally bytes String"  # Converted to string
    region, endpoint_url, boto_params = botocore_utils._aws_connection_info(options)
    assert region is sentinel.RETURNED_REGION
    assert endpoint_url is None
    assert boto_params == expected_params


@pytest.mark.parametrize(
    "options, expected_validate",
    [
        (dict(validate_certs=True, aws_ca_bundle=sentinel.PARAM_BUNDLE), sentinel.PARAM_BUNDLE),
        (dict(validate_certs=False, aws_ca_bundle=sentinel.PARAM_BUNDLE), False),
        (dict(validate_certs=True, aws_ca_bundle=""), True),
        (dict(validate_certs=False, aws_ca_bundle=""), False),
        (dict(validate_certs=True, aws_ca_bundle=None), True),
        (dict(validate_certs=False, aws_ca_bundle=None), False),
        (dict(validate_certs=True, aws_ca_bundle=b"Originally bytes String"), "Originally bytes String"),
    ],
)
def test_aws_connection_info_validation(monkeypatch, botocore_utils, options, expected_validate):
    expected_params = deepcopy(BLANK_BOTO_PARAMS)
    expected_params["verify"] = expected_validate

    region, endpoint_url, boto_params = botocore_utils._aws_connection_info(options)
    assert region is sentinel.RETURNED_REGION
    assert endpoint_url is None
    assert boto_params == expected_params
    assert boto_params["verify"] == expected_validate


def test_aws_connection_info_profile(monkeypatch, botocore_utils):
    expected_params = deepcopy(BLANK_BOTO_PARAMS)

    options = {"profile": ""}
    region, endpoint_url, boto_params = botocore_utils._aws_connection_info(options)
    assert region is sentinel.RETURNED_REGION
    assert endpoint_url is None
    assert boto_params == expected_params

    options = {"profile": None}
    region, endpoint_url, boto_params = botocore_utils._aws_connection_info(options)
    assert region is sentinel.RETURNED_REGION
    assert endpoint_url is None
    assert boto_params == expected_params

    options = {"profile": sentinel.PARAM_PROFILE}
    expected_params["profile_name"] = sentinel.PARAM_PROFILE
    region, endpoint_url, boto_params = botocore_utils._aws_connection_info(options)
    assert region is sentinel.RETURNED_REGION
    assert endpoint_url is None
    assert boto_params == expected_params
    assert boto_params["profile_name"] is sentinel.PARAM_PROFILE

    options = {"profile": b"Originally bytes String"}
    expected_params["profile_name"] = "Originally bytes String"
    region, endpoint_url, boto_params = botocore_utils._aws_connection_info(options)
    assert region is sentinel.RETURNED_REGION
    assert endpoint_url is None
    assert boto_params == expected_params


def test_aws_connection_info_config(monkeypatch, botocore_utils, fake_botocore):
    monkeypatch.setattr(botocore_utils, "botocore", fake_botocore)
    expected_params = deepcopy(BLANK_BOTO_PARAMS)

    options = {}
    region, endpoint_url, boto_params = botocore_utils._aws_connection_info(options)
    assert region is sentinel.RETURNED_REGION
    assert endpoint_url is None
    assert boto_params == expected_params
    assert fake_botocore.config.Config.called is False

    options = {"aws_config": None}
    region, endpoint_url, boto_params = botocore_utils._aws_connection_info(options)
    assert region is sentinel.RETURNED_REGION
    assert endpoint_url is None
    assert boto_params == expected_params
    assert fake_botocore.config.Config.called is False

    options = {"aws_config": {"example_config_item": sentinel.PARAM_CONFIG}}
    expected_params["aws_config"] = sentinel.BOTO3_CONFIG
    region, endpoint_url, boto_params = botocore_utils._aws_connection_info(options)
    assert region is sentinel.RETURNED_REGION
    assert endpoint_url is None
    assert boto_params == expected_params
    assert fake_botocore.config.Config.called is True
    config_args = fake_botocore.config.Config.call_args
    assert config_args == call(example_config_item=sentinel.PARAM_CONFIG)


def test_aws_connection_info_endpoint_url(monkeypatch, botocore_utils):
    expected_params = deepcopy(BLANK_BOTO_PARAMS)

    options = {"endpoint_url": sentinel.PARAM_ENDPOINT}
    region, endpoint_url, boto_params = botocore_utils._aws_connection_info(options)
    assert region is sentinel.RETURNED_REGION
    assert endpoint_url is sentinel.PARAM_ENDPOINT
    assert boto_params == expected_params


def test_aws_connection_info_complex(monkeypatch, botocore_utils, fake_botocore):
    monkeypatch.setattr(botocore_utils, "botocore", fake_botocore)

    expected_params = dict(
        aws_access_key_id=sentinel.PARAM_ACCESS,
        aws_secret_access_key=sentinel.PARAM_SECRET,
        aws_session_token=sentinel.PARAM_SESSION,
        verify=sentinel.PARAM_BUNDLE,
        aws_config=sentinel.BOTO3_CONFIG,
    )
    options = dict(
        endpoint_url=sentinel.PARAM_ENDPOINT,
        access_key=sentinel.PARAM_ACCESS,
        secret_key=sentinel.PARAM_SECRET,
        session_token=sentinel.PARAM_SESSION,
        validate_certs=True,
        aws_ca_bundle=sentinel.PARAM_BUNDLE,
        aws_config={"example_config_item": sentinel.PARAM_CONFIG},
    )
    region, endpoint_url, boto_params = botocore_utils._aws_connection_info(options)

    assert region is sentinel.RETURNED_REGION
    assert endpoint_url is sentinel.PARAM_ENDPOINT
    assert boto_params == expected_params
    assert fake_botocore.config.Config.called is True
    config_args = fake_botocore.config.Config.call_args
    assert config_args == call(example_config_item=sentinel.PARAM_CONFIG)
    assert botocore_utils._aws_region.called is True
    region_args = botocore_utils._aws_region.call_args
    assert region_args == call(options)
    assert region_args[0][0] is options


def test_aws_connection_info_complex_profile(monkeypatch, botocore_utils, fake_botocore):
    monkeypatch.setattr(botocore_utils, "botocore", fake_botocore)

    expected_params = dict(
        aws_access_key_id=None,
        aws_secret_access_key=None,
        aws_session_token=None,
        profile_name=sentinel.PARAM_PROFILE,
        verify=sentinel.PARAM_BUNDLE,
        aws_config=sentinel.BOTO3_CONFIG,
    )
    options = dict(
        endpoint_url=sentinel.PARAM_ENDPOINT,
        access_key=None,
        secret_key=None,
        session_token=None,
        profile=sentinel.PARAM_PROFILE,
        validate_certs=True,
        aws_ca_bundle=sentinel.PARAM_BUNDLE,
        aws_config={"example_config_item": sentinel.PARAM_CONFIG},
    )
    region, endpoint_url, boto_params = botocore_utils._aws_connection_info(options)

    assert region is sentinel.RETURNED_REGION
    assert endpoint_url is sentinel.PARAM_ENDPOINT
    assert boto_params == expected_params
    assert fake_botocore.config.Config.called is True
    config_args = fake_botocore.config.Config.call_args
    assert config_args == call(example_config_item=sentinel.PARAM_CONFIG)
    assert botocore_utils._aws_region.called is True
    region_args = botocore_utils._aws_region.call_args
    assert region_args == call(options)
    assert region_args[0][0] is options
