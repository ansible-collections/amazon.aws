# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

try:
    import botocore
except ImportError:
    pass

from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import sentinel

import pytest

import ansible_collections.amazon.aws.plugins.module_utils.botocore as utils_botocore


class FailException(Exception):
    pass


@pytest.fixture
def aws_module(monkeypatch):
    aws_module = MagicMock()
    aws_module.fail_json.side_effect = FailException()
    monkeypatch.setattr(aws_module, "_name", sentinel.MODULE_NAME)
    return aws_module


@pytest.fixture
def botocore_utils(monkeypatch):
    return utils_botocore


###############################################################
# module_utils.botocore.boto3_conn
###############################################################
def test_boto3_conn_success(monkeypatch, aws_module, botocore_utils):
    connection_method = MagicMock(name="_boto3_conn")
    monkeypatch.setattr(botocore_utils, "_boto3_conn", connection_method)
    connection_method.return_value = sentinel.RETURNED_CONNECTION

    assert botocore_utils.boto3_conn(aws_module) is sentinel.RETURNED_CONNECTION
    passed_args = connection_method.call_args
    assert passed_args == call(conn_type=None, resource=None, region=None, endpoint=None)

    result = botocore_utils.boto3_conn(
        aws_module,
        conn_type=sentinel.PARAM_CONNTYPE,
        resource=sentinel.PARAM_RESOURCE,
        region=sentinel.PARAM_REGION,
        endpoint=sentinel.PARAM_ENDPOINT,
        extra_arg=sentinel.PARAM_EXTRA,
    )
    assert result is sentinel.RETURNED_CONNECTION
    passed_args = connection_method.call_args
    assert passed_args == call(
        conn_type=sentinel.PARAM_CONNTYPE,
        resource=sentinel.PARAM_RESOURCE,
        region=sentinel.PARAM_REGION,
        endpoint=sentinel.PARAM_ENDPOINT,
        extra_arg=sentinel.PARAM_EXTRA,
    )


@pytest.mark.parametrize(
    "failure, custom_error",
    [
        (
            ValueError(sentinel.VALUE_ERROR),
            "Couldn't connect to AWS: sentinel.VALUE_ERROR",
        ),
        (
            botocore.exceptions.ProfileNotFound(
                profile=sentinel.PROFILE_ERROR,
            ),
            None,
        ),
        (
            botocore.exceptions.PartialCredentialsError(
                provider=sentinel.CRED_ERROR_PROV,
                cred_var=sentinel.CRED_ERROR_VAR,
            ),
            None,
        ),
        (
            botocore.exceptions.NoCredentialsError(),
            None,
        ),
        (
            botocore.exceptions.ConfigParseError(path=sentinel.PARSE_ERROR),
            None,
        ),
        (
            botocore.exceptions.NoRegionError(),
            "The sentinel.MODULE_NAME module requires a region and none was found",
        ),
    ],
)
def test_boto3_conn_exception(monkeypatch, aws_module, botocore_utils, failure, custom_error):
    connection_method = MagicMock(name="_boto3_conn")
    monkeypatch.setattr(botocore_utils, "_boto3_conn", connection_method)
    connection_method.side_effect = failure

    if custom_error is None:
        custom_error = str(failure)

    with pytest.raises(FailException):
        botocore_utils.boto3_conn(aws_module)

    fail_args = aws_module.fail_json.call_args
    assert custom_error in fail_args[1]["msg"]
