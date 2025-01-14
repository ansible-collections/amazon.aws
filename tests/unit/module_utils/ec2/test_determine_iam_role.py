# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import sentinel

import pytest

import ansible_collections.amazon.aws.plugins.module_utils.arn as utils_arn
import ansible_collections.amazon.aws.plugins.module_utils.ec2 as ec2_utils
from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3

try:
    import botocore
except ImportError:
    pass

pytest.mark.skipif(
    not HAS_BOTO3, reason="test_determine_iam_role.py requires the python modules 'boto3' and 'botocore'"
)


def _client_error(code="GenericError"):
    return botocore.exceptions.ClientError(
        {
            "Error": {"Code": code, "Message": "Something went wrong"},
            "ResponseMetadata": {"RequestId": "01234567-89ab-cdef-0123-456789abcdef"},
        },
        "some_called_method",
    )


class FailJsonException(Exception):
    def __init__(self):
        pass


@pytest.fixture(name="ec2_utils_fixture")
def fixture_ec2_utils_fixture(monkeypatch):
    monkeypatch.setattr(ec2_utils, "validate_aws_arn", lambda arn, service, resource_type: None)
    return ec2_utils


@pytest.fixture(name="iam_client")
def fixture_iam_client():
    client = MagicMock()
    return client


def test_determine_iam_role_arn(ec2_utils_fixture, iam_client, monkeypatch):
    # Revert the default monkey patch to make it simple to try passing a valid ARNs
    monkeypatch.setattr(ec2_utils_fixture, "validate_aws_arn", utils_arn.validate_aws_arn)

    # Simplest example, someone passes a valid instance profile ARN
    arn = ec2_utils_fixture.determine_iam_arn_from_name(
        iam_client, "arn:aws:iam::123456789012:instance-profile/myprofile"
    )
    assert arn == "arn:aws:iam::123456789012:instance-profile/myprofile"


def test_determine_iam_role_name(ec2_utils_fixture, iam_client, monkeypatch):
    monkeypatch.setattr(
        ec2_utils_fixture, "list_iam_instance_profiles", lambda arn, **kwargs: [{"Arn": sentinel.IAM_PROFILE_ARN}]
    )
    arn = ec2_utils_fixture.determine_iam_arn_from_name(iam_client, sentinel.IAM_PROFILE_NAME)
    assert arn == sentinel.IAM_PROFILE_ARN


def test_determine_iam_role_missing(ec2_utils_fixture, iam_client, monkeypatch):
    monkeypatch.setattr(ec2_utils_fixture, "list_iam_instance_profiles", lambda arn, **kwargs: [])
    with pytest.raises(ec2_utils.AnsibleEC2Error) as excinfo:
        ec2_utils_fixture.determine_iam_arn_from_name(iam_client, sentinel.IAM_PROFILE_NAME)
    assert "Could not find IAM instance profile" in str(excinfo.value)
