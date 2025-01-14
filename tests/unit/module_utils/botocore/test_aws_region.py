# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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


class FailException(Exception):
    pass


@pytest.fixture(name="aws_module")
def fixture_aws_module(monkeypatch):
    aws_module = MagicMock()
    aws_module.fail_json.side_effect = FailException()
    aws_module.fail_json_aws.side_effect = FailException()
    monkeypatch.setattr(aws_module, "params", sentinel.MODULE_PARAMS)
    return aws_module


@pytest.fixture(name="fake_boto3")
def fixture_fake_boto3(monkeypatch):
    # Note: this isn't a monkey-patched real-botocore, this is a complete fake.
    fake_session = MagicMock()
    fake_session.region_name = sentinel.BOTO3_REGION
    fake_session_module = MagicMock()
    fake_session_module.Session.return_value = fake_session
    fake_boto3 = MagicMock()
    monkeypatch.setattr(fake_boto3, "session", fake_session_module)
    # Patch exceptions back in
    monkeypatch.setattr(fake_boto3, "exceptions", botocore.exceptions)

    return fake_boto3


@pytest.fixture(name="botocore_utils")
def fixture_botocore_utils(monkeypatch):
    return utils_botocore


###############################################################
# module_utils.botocore.get_aws_region
###############################################################
def test_get_aws_region_simple(monkeypatch, aws_module, botocore_utils):
    region_method = MagicMock(name="_aws_region")
    monkeypatch.setattr(botocore_utils, "_aws_region", region_method)
    region_method.return_value = sentinel.RETURNED_REGION

    assert botocore_utils.get_aws_region(aws_module) is sentinel.RETURNED_REGION
    passed_args = region_method.call_args
    assert passed_args == call(sentinel.MODULE_PARAMS)
    # args[0]
    assert passed_args[0][0] is sentinel.MODULE_PARAMS


def test_get_aws_region_exception_nested(monkeypatch, aws_module, botocore_utils):
    region_method = MagicMock(name="_aws_region")
    monkeypatch.setattr(botocore_utils, "_aws_region", region_method)

    exception_nested = AnsibleBotocoreError(message=sentinel.ERROR_MSG, exception=sentinel.ERROR_EX)
    region_method.side_effect = exception_nested

    with pytest.raises(FailException):
        assert botocore_utils.get_aws_region(aws_module)

    passed_args = region_method.call_args
    assert passed_args == call(sentinel.MODULE_PARAMS)
    # call_args[0] == positional args
    assert passed_args[0][0] is sentinel.MODULE_PARAMS

    fail_args = aws_module.fail_json.call_args
    assert fail_args == call(msg=sentinel.ERROR_MSG, exception=sentinel.ERROR_EX)
    # call_args[1] == kwargs
    assert fail_args[1]["msg"] is sentinel.ERROR_MSG
    assert fail_args[1]["exception"] is sentinel.ERROR_EX


def test_get_aws_region_exception_msg(monkeypatch, aws_module, botocore_utils):
    region_method = MagicMock(name="_aws_region")
    monkeypatch.setattr(botocore_utils, "_aws_region", region_method)

    exception_nested = AnsibleBotocoreError(message=sentinel.ERROR_MSG)
    region_method.side_effect = exception_nested

    with pytest.raises(FailException):
        assert botocore_utils.get_aws_region(aws_module)

    passed_args = region_method.call_args
    assert passed_args == call(sentinel.MODULE_PARAMS)
    # call_args[0] == positional args
    assert passed_args[0][0] is sentinel.MODULE_PARAMS

    fail_args = aws_module.fail_json.call_args
    assert fail_args == call(msg=sentinel.ERROR_MSG)
    # call_args[1] == kwargs
    assert fail_args[1]["msg"] is sentinel.ERROR_MSG


###############################################################
# module_utils.botocore._aws_region
###############################################################
def test_aws_region_no_boto(monkeypatch, botocore_utils):
    monkeypatch.setattr(botocore_utils, "HAS_BOTO3", False)
    monkeypatch.setattr(botocore_utils, "BOTO3_IMP_ERR", sentinel.BOTO3_IMPORT_EXCEPTION)

    assert botocore_utils._aws_region(dict(region=sentinel.PARAM_REGION)) is sentinel.PARAM_REGION

    with pytest.raises(AnsibleBotocoreError) as e:
        utils_botocore._aws_region(dict())
    assert "boto3" in e.value.message
    assert "botocore" in e.value.message
    assert e.value.exception is sentinel.BOTO3_IMPORT_EXCEPTION


def test_aws_region_no_profile(monkeypatch, botocore_utils, fake_boto3):
    monkeypatch.setattr(botocore_utils, "boto3", fake_boto3)
    fake_session_module = fake_boto3.session

    assert botocore_utils._aws_region(dict(region=sentinel.PARAM_REGION)) is sentinel.PARAM_REGION

    assert botocore_utils._aws_region(dict()) is sentinel.BOTO3_REGION
    assert fake_session_module.Session.call_args == call(profile_name=None)


def test_aws_region_none_profile(monkeypatch, botocore_utils, fake_boto3):
    monkeypatch.setattr(botocore_utils, "boto3", fake_boto3)
    fake_session_module = fake_boto3.session

    assert botocore_utils._aws_region(dict(region=sentinel.PARAM_REGION, profile=None)) is sentinel.PARAM_REGION

    assert utils_botocore._aws_region(dict(profile=None)) is sentinel.BOTO3_REGION
    assert fake_session_module.Session.call_args == call(profile_name=None)


def test_aws_region_empty_profile(monkeypatch, botocore_utils, fake_boto3):
    monkeypatch.setattr(botocore_utils, "boto3", fake_boto3)
    fake_session_module = fake_boto3.session

    assert botocore_utils._aws_region(dict(region=sentinel.PARAM_REGION, profile="")) is sentinel.PARAM_REGION

    assert utils_botocore._aws_region(dict(profile="")) is sentinel.BOTO3_REGION
    assert fake_session_module.Session.call_args == call(profile_name=None)


def test_aws_region_with_profile(monkeypatch, botocore_utils, fake_boto3):
    monkeypatch.setattr(botocore_utils, "boto3", fake_boto3)
    fake_session_module = fake_boto3.session

    assert (
        botocore_utils._aws_region(dict(region=sentinel.PARAM_REGION, profile=sentinel.PARAM_PROFILE))
        is sentinel.PARAM_REGION
    )

    assert utils_botocore._aws_region(dict(profile=sentinel.PARAM_PROFILE)) is sentinel.BOTO3_REGION
    assert fake_session_module.Session.call_args == call(profile_name=sentinel.PARAM_PROFILE)


def test_aws_region_bad_profile(monkeypatch, botocore_utils, fake_boto3):
    not_found_exception = botocore.exceptions.ProfileNotFound(profile=sentinel.ERROR_PROFILE)

    monkeypatch.setattr(botocore_utils, "boto3", fake_boto3)
    fake_session_module = fake_boto3.session

    assert (
        botocore_utils._aws_region(dict(region=sentinel.PARAM_REGION, profile=sentinel.PARAM_PROFILE))
        is sentinel.PARAM_REGION
    )
    # We've always just returned a blank region if we're passed a bad profile.
    # However, it's worth noting however that once someone tries to build a connection passing the
    # bad profile name they'll see the ProfileNotFound exception
    fake_session_module.Session.side_effect = not_found_exception
    assert utils_botocore._aws_region(dict(profile=sentinel.PARAM_PROFILE)) is None
    assert fake_session_module.Session.call_args == call(profile_name=sentinel.PARAM_PROFILE)
