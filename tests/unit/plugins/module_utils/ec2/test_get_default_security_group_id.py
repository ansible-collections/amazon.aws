# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock

import pytest

import ansible_collections.amazon.aws.plugins.module_utils.ec2 as ec2_utils
from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3

pytest.mark.skipif(
    not HAS_BOTO3,
    reason="test_get_default_security_group_id.py requires the python modules 'boto3' and 'botocore'",
)


@pytest.fixture(name="ec2_client")
def fixture_ec2_client():
    """Mock EC2 client fixture."""
    client = MagicMock()
    return client


def test_get_default_security_group_id_success(ec2_client, monkeypatch):
    """Test successful retrieval of default security group ID."""
    expected_group_id = "sg-12345678"
    vpc_id = "vpc-abcdef01"

    # Mock describe_security_groups to return a single default security group
    monkeypatch.setattr(
        ec2_utils,
        "describe_security_groups",
        lambda client, **kwargs: [{"GroupId": expected_group_id, "GroupName": "default"}],
    )

    result = ec2_utils.get_default_security_group_id(ec2_client, vpc_id)

    assert result == expected_group_id


def test_get_default_security_group_id_not_found(ec2_client, monkeypatch):
    """Test error when no default security group is found."""
    vpc_id = "vpc-abcdef01"

    # Mock describe_security_groups to return empty list
    monkeypatch.setattr(ec2_utils, "describe_security_groups", lambda client, **kwargs: [])

    with pytest.raises(ec2_utils.AnsibleEC2Error) as excinfo:
        ec2_utils.get_default_security_group_id(ec2_client, vpc_id)

    assert f"No default security group found for VPC {vpc_id}" in str(excinfo.value)


def test_get_default_security_group_id_multiple_found(ec2_client, monkeypatch):
    """Test error when multiple default security groups are found."""
    vpc_id = "vpc-abcdef01"

    # Mock describe_security_groups to return multiple default security groups
    monkeypatch.setattr(
        ec2_utils,
        "describe_security_groups",
        lambda client, **kwargs: [
            {"GroupId": "sg-12345678", "GroupName": "default"},
            {"GroupId": "sg-87654321", "GroupName": "default"},
        ],
    )

    with pytest.raises(ec2_utils.AnsibleEC2Error) as excinfo:
        ec2_utils.get_default_security_group_id(ec2_client, vpc_id)

    assert 'Multiple security groups named "default" found for VPC' in str(excinfo.value)
    assert vpc_id in str(excinfo.value)
