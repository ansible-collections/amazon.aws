# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.arn import parse_aws_arn

arn_bad_values = [
    "arn:aws:outpost:us-east-1: 123456789012:outpost/op-1234567890abcdef0",
    "arn:aws:out post:us-east-1:123456789012:outpost/op-1234567890abcdef0",
    "arn:aws:outpost:us east 1:123456789012:outpost/op-1234567890abcdef0",
    "invalid:aws:outpost:us-east-1:123456789012:outpost/op-1234567890abcdef0",
    "arn:junk:outpost:us-east-1:123456789012:outpost/op-1234567890abcdef0",
    "arn:aws:outpost:us-east-1:junk:outpost/op-1234567890abcdef0",
]

arn_good_values = [
    # Play about with partition name in valid ways
    dict(
        partition="aws",
        service="outpost",
        region="us-east-1",
        account_id="123456789012",
        resource="outpost/op-1234567890abcdef0",
        resource_type="outpost",
        resource_id="op-1234567890abcdef0",
    ),
    dict(
        partition="aws-gov",
        service="outpost",
        region="us-gov-east-1",
        account_id="123456789012",
        resource="outpost/op-1234567890abcdef0",
        resource_type="outpost",
        resource_id="op-1234567890abcdef0",
    ),
    dict(
        partition="aws-cn",
        service="outpost",
        region="us-east-1",
        account_id="123456789012",
        resource="outpost/op-1234567890abcdef0",
        resource_type="outpost",
        resource_id="op-1234567890abcdef0",
    ),
    # Start the account ID with 0s, it's a 12 digit *string*, if someone treats
    # it as an integer the leading 0s can disappear.
    dict(
        partition="aws-cn",
        service="outpost",
        region="us-east-1",
        account_id="000123000123",
        resource="outpost/op-1234567890abcdef0",
        resource_type="outpost",
        resource_id="op-1234567890abcdef0",
    ),
    # S3 doesn't "need" region/account_id as bucket names are globally unique
    dict(
        partition="aws",
        service="s3",
        region="",
        account_id="",
        resource="bucket/object",
        resource_type="bucket",
        resource_id="object",
    ),
    # IAM is a 'global' service, so the ARNs don't have regions
    dict(
        partition="aws",
        service="iam",
        region="",
        account_id="123456789012",
        resource="policy/foo/bar/PolicyName",
        resource_type="policy",
        resource_id="foo/bar/PolicyName",
    ),
    dict(
        partition="aws",
        service="iam",
        region="",
        account_id="123456789012",
        resource="instance-profile/ExampleProfile",
        resource_type="instance-profile",
        resource_id="ExampleProfile",
    ),
    dict(
        partition="aws",
        service="iam",
        region="",
        account_id="123456789012",
        resource="root",
        resource_type=None,
        resource_id="root",
    ),
    # Some examples with different regions
    dict(
        partition="aws",
        service="sqs",
        region="eu-west-3",
        account_id="123456789012",
        resource="example-queue",
        resource_type=None,
        resource_id="example-queue",
    ),
    dict(
        partition="aws",
        service="sqs",
        region="us-gov-east-1",
        account_id="123456789012",
        resource="example-queue",
        resource_type=None,
        resource_id="example-queue",
    ),
    dict(
        partition="aws",
        service="sqs",
        region="sa-east-1",
        account_id="123456789012",
        resource="example-queue",
        resource_type=None,
        resource_id="example-queue",
    ),
    dict(
        partition="aws",
        service="sqs",
        region="ap-northeast-2",
        account_id="123456789012",
        resource="example-queue",
        resource_type=None,
        resource_id="example-queue",
    ),
    dict(
        partition="aws",
        service="sqs",
        region="ca-central-1",
        account_id="123456789012",
        resource="example-queue",
        resource_type=None,
        resource_id="example-queue",
    ),
    # Some more unusual service names
    dict(
        partition="aws",
        service="network-firewall",
        region="us-east-1",
        account_id="123456789012",
        resource="stateful-rulegroup/ExampleDomainList",
        resource_type="stateful-rulegroup",
        resource_id="ExampleDomainList",
    ),
    dict(
        partition="aws",
        service="resource-groups",
        region="us-east-1",
        account_id="123456789012",
        resource="group/group-name",
        resource_type="group",
        resource_id="group-name",
    ),
    # A special case for resources AWS curate
    dict(
        partition="aws",
        service="network-firewall",
        region="us-east-1",
        account_id="aws-managed",
        resource="stateful-rulegroup/BotNetCommandAndControlDomainsActionOrder",
        resource_type="stateful-rulegroup",
        resource_id="BotNetCommandAndControlDomainsActionOrder",
    ),
    dict(
        partition="aws",
        service="iam",
        region="",
        account_id="aws",
        resource="policy/AWSDirectConnectReadOnlyAccess",
        resource_type="policy",
        resource_id="AWSDirectConnectReadOnlyAccess",
    ),
    # Examples merged in from test_arn.py
    dict(
        partition="aws-us-gov",
        service="iam",
        region="",
        account_id="0123456789",
        resource="role/foo-role",
        resource_type="role",
        resource_id="foo-role",
    ),
    dict(
        partition="aws",
        service="iam",
        region="",
        account_id="123456789012",
        resource="user/dev/*",
        resource_type="user",
        resource_id="dev/*",
    ),
    dict(
        partition="aws",
        service="iam",
        region="",
        account_id="123456789012",
        resource="user:test",
        resource_type="user",
        resource_id="test",
    ),
    dict(
        partition="aws-cn",
        service="iam",
        region="",
        account_id="123456789012",
        resource="user:test",
        resource_type="user",
        resource_id="test",
    ),
    dict(
        partition="aws",
        service="iam",
        region="",
        account_id="123456789012",
        resource="user",
        resource_type=None,
        resource_id="user",
    ),
    dict(
        partition="aws",
        service="s3",
        region="",
        account_id="",
        resource="my_corporate_bucket/*",
        resource_type="my_corporate_bucket",
        resource_id="*",
    ),
    dict(
        partition="aws",
        service="s3",
        region="",
        account_id="",
        resource="my_corporate_bucket/Development/*",
        resource_type="my_corporate_bucket",
        resource_id="Development/*",
    ),
    dict(
        partition="aws",
        service="rds",
        region="es-east-1",
        account_id="000000000000",
        resource="snapshot:rds:my-db-snapshot",
        resource_type="snapshot",
        resource_id="rds:my-db-snapshot",
    ),
    dict(
        partition="aws",
        service="cloudformation",
        region="us-east-1",
        account_id="012345678901",
        resource="changeSet/Ansible-StackName-c6884247ede41eb0",
        resource_type="changeSet",
        resource_id="Ansible-StackName-c6884247ede41eb0",
    ),
]


@pytest.mark.parametrize("arn", arn_bad_values)
def test_parse_aws_arn_bad_values(arn):
    # Make sure we get the expected 'None' for various 'bad' ARNs.
    assert parse_aws_arn(arn) is None


@pytest.mark.parametrize("result", arn_good_values)
def test_parse_aws_arn_good_values(result):
    # Something of a cheat, but build the ARN from the result we expect
    arn = "arn:{partition}:{service}:{region}:{account_id}:{resource}".format(**result)
    assert parse_aws_arn(arn) == result
