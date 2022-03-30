# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

# import unittest
import pytest

from ansible_collections.amazon.aws.plugins.module_utils.arn import is_outpost_arn
from ansible_collections.amazon.aws.plugins.module_utils.arn import parse_aws_arn

outpost_arn_test_inputs = [
    ("arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0", True),
    ("arn:aws:outposts:us-east-1:123456789012:outpost/op-1234567890abcdef0123", False),
    ("arn:aws:outpost:us-east-1: 123456789012:outpost/ op-1234567890abcdef0", False),
    ("ars:aws:outposts:us-east-1: 123456789012:outpost/ op-1234567890abcdef0", False),
    ("arn:was:outposts:us-east-1: 123456789012:outpost/ op-1234567890abcdef0", False),
]

arn_bad_values = [
    ("arn:aws:outpost:us-east-1: 123456789012:outpost/op-1234567890abcdef0"),
    ("arn:aws:out post:us-east-1:123456789012:outpost/op-1234567890abcdef0"),
    ("arn:aws:outpost:us east 1:123456789012:outpost/op-1234567890abcdef0"),
    ("invalid:aws:outpost:us-east-1:123456789012:outpost/op-1234567890abcdef0"),
    ("arn:junk:outpost:us-east-1:123456789012:outpost/op-1234567890abcdef0"),
    ("arn:aws:outpost:us-east-1:junk:outpost/op-1234567890abcdef0"),
]

arn_good_values = [
    # Play about with partition name in valid ways
    dict(partition='aws', service='outpost', region='us-east-1', account_id='123456789012',
         resource='outpost/op-1234567890abcdef0'),
    dict(partition='aws-gov', service='outpost', region='us-gov-east-1', account_id='123456789012',
         resource='outpost/op-1234567890abcdef0'),
    dict(partition='aws-cn', service='outpost', region='us-east-1', account_id='123456789012',
         resource='outpost/op-1234567890abcdef0'),
    # Start the account ID with 0s, it's a 12 digit *string*, if someone treats
    # it as an integer the leading 0s can disappear.
    dict(partition='aws-cn', service='outpost', region='us-east-1', account_id='000123000123',
         resource='outpost/op-1234567890abcdef0'),
    # S3 doesn't "need" region/account_id as bucket names are globally unique
    dict(partition='aws', service='s3', region='', account_id='', resource='bucket/object'),
    # IAM is a 'global' service, so the ARNs don't have regions
    dict(partition='aws', service='iam', region='', account_id='123456789012',
         resource='policy/foo/bar/PolicyName'),
    dict(partition='aws', service='iam', region='', account_id='123456789012',
         resource='instance-profile/ExampleProfile'),
    dict(partition='aws', service='iam', region='', account_id='123456789012', resource='root'),
    # Some examples with different regions
    dict(partition='aws', service='sqs', region='eu-west-3', account_id='123456789012',
         resource='example-queue'),
    dict(partition='aws', service='sqs', region='us-gov-east-1', account_id='123456789012',
         resource='example-queue'),
    dict(partition='aws', service='sqs', region='sa-east-1', account_id='123456789012',
         resource='example-queue'),
    dict(partition='aws', service='sqs', region='ap-northeast-2', account_id='123456789012',
         resource='example-queue'),
    dict(partition='aws', service='sqs', region='ca-central-1', account_id='123456789012',
         resource='example-queue'),
    # Some more unusual service names
    dict(partition='aws', service='network-firewall', region='us-east-1', account_id='123456789012',
         resource='stateful-rulegroup/ExampleDomainList'),
    dict(partition='aws', service='resource-groups', region='us-east-1', account_id='123456789012',
         resource='group/group-name'),
    # A special case for resources AWS curate
    dict(partition='aws', service='network-firewall', region='us-east-1', account_id='aws-managed',
         resource='stateful-rulegroup/BotNetCommandAndControlDomainsActionOrder'),
    dict(partition='aws', service='iam', region='', account_id='aws',
         resource='policy/AWSDirectConnectReadOnlyAccess'),
]


@pytest.mark.parametrize("outpost_arn, result", outpost_arn_test_inputs)
def test_is_outpost_arn(outpost_arn, result):
    assert is_outpost_arn(outpost_arn) == result


@pytest.mark.parametrize("arn", arn_bad_values)
def test_parse_aws_arn_bad_values(arn):
    # Make sure we get the expected 'None' for various 'bad' ARNs.
    assert parse_aws_arn(arn) is None


@pytest.mark.parametrize("result", arn_good_values)
def test_parse_aws_arn_good_values(result):
    # Something of a cheat, but build the ARN from the result we expect
    arn = 'arn:{partition}:{service}:{region}:{account_id}:{resource}'.format(**result)
    assert parse_aws_arn(arn) == result
