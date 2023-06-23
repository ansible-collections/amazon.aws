# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.arn import validate_aws_arn

arn_test_inputs = [
    # Just test it's a valid ARN
    ("arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0", True, None),
    # Bad ARN
    ("arn:was:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0", False, None),
    # Individual options
    (
        "arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0",
        True,
        {"partition": "aws"},
    ),
    (
        "arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0",
        False,
        {"partition": "aws-cn"},
    ),
    (
        "arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0",
        True,
        {"service": "outposts"},
    ),
    (
        "arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0",
        False,
        {"service": "iam"},
    ),
    (
        "arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0",
        True,
        {"region": "us-east-1"},
    ),
    (
        "arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0",
        False,
        {"region": "us-east-2"},
    ),
    (
        "arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0",
        True,
        {"account_id": "123456789012"},
    ),
    (
        "arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0",
        False,
        {"account_id": "111111111111"},
    ),
    (
        "arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0",
        True,
        {"resource": "outpost/op-1234567890abcdef0"},
    ),
    (
        "arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0",
        False,
        {"resource": "outpost/op-11111111111111111"},
    ),
    (
        "arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0",
        True,
        {"resource_type": "outpost"},
    ),
    (
        "arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0",
        False,
        {"resource_type": "notpost"},
    ),
    (
        "arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0",
        True,
        {"resource_id": "op-1234567890abcdef0"},
    ),
    (
        "arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0",
        False,
        {"resource_id": "op-11111111111111111"},
    ),
    (
        "arn:aws:states:us-west-2:123456789012:stateMachine:HelloWorldStateMachine",
        True,
        {"resource_type": "stateMachine"},
    ),
    (
        "arn:aws:states:us-west-2:123456789012:stateMachine:HelloWorldStateMachine",
        False,
        {"resource_type": "nopeMachine"},
    ),
    (
        "arn:aws:states:us-west-2:123456789012:stateMachine:HelloWorldStateMachine",
        True,
        {"resource_id": "HelloWorldStateMachine"},
    ),
    (
        "arn:aws:states:us-west-2:123456789012:stateMachine:HelloWorldStateMachine",
        False,
        {"resource_id": "CruelWorldStateMachine"},
    ),
    # All options
    (
        "arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0",
        True,
        {
            "partition": "aws",
            "service": "outposts",
            "region": "us-east-1",
            "account_id": "123456789012",
            "resource": "outpost/op-1234567890abcdef0",
            "resource_type": "outpost",
            "resource_id": "op-1234567890abcdef0",
        },
    ),
    (
        "arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0",
        False,
        {
            "partition": "aws-cn",
            "service": "outposts",
            "region": "us-east-1",
            "account_id": "123456789012",
            "resource": "outpost/op-1234567890abcdef0",
            "resource_type": "outpost",
            "resource_id": "op-1234567890abcdef0",
        },
    ),
    (
        "arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0",
        False,
        {
            "partition": "aws",
            "service": "iam",
            "region": "us-east-1",
            "account_id": "123456789012",
            "resource": "outpost/op-1234567890abcdef0",
            "resource_type": "outpost",
            "resource_id": "op-1234567890abcdef0",
        },
    ),
    (
        "arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0",
        False,
        {
            "partition": "aws",
            "service": "outposts",
            "region": "us-east-2",
            "account_id": "123456789012",
            "resource": "outpost/op-1234567890abcdef0",
            "resource_type": "outpost",
            "resource_id": "op-1234567890abcdef0",
        },
    ),
    (
        "arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0",
        False,
        {
            "partition": "aws",
            "service": "outposts",
            "region": "us-east-1",
            "account_id": "111111111111",
            "resource": "outpost/op-1234567890abcdef0",
            "resource_type": "outpost",
            "resource_id": "op-1234567890abcdef0",
        },
    ),
    (
        "arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0",
        False,
        {
            "partition": "aws",
            "service": "outposts",
            "region": "us-east-1",
            "account_id": "123456789012",
            "resource": "outpost/op-11111111111111111",
            "resource_type": "outpost",
            "resource_id": "op-1234567890abcdef0",
        },
    ),
    (
        "arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0",
        False,
        {
            "partition": "aws",
            "service": "outposts",
            "region": "us-east-1",
            "account_id": "123456789012",
            "resource": "outpost/op-1234567890abcdef0",
            "resource_type": "notpost",
            "resource_id": "op-1234567890abcdef0",
        },
    ),
    (
        "arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0",
        False,
        {
            "partition": "aws",
            "service": "outposts",
            "region": "us-east-1",
            "account_id": "123456789012",
            "resource": "outpost/op-1234567890abcdef0",
            "resource_type": "outpost",
            "resource_id": "op-11111111111111111",
        },
    ),
]


@pytest.mark.parametrize("arn, result, kwargs", arn_test_inputs)
def test_validate_aws_arn(arn, result, kwargs):
    kwargs = kwargs or {}
    assert validate_aws_arn(arn, **kwargs) == result
