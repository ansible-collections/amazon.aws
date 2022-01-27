from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.core import parse_aws_arn


arn_data = [
    ("arn:aws-us-gov:iam::0123456789:role/foo-role",
     dict(partition="aws-us-gov", account_id="0123456789", resource="role/foo-role", service="iam", region="")
     ),
    ("arn:aws:iam::123456789012:user/dev/*",
     dict(partition="aws", account_id="123456789012", resource="user/dev/*", service='iam', region="")
     ),
    ("arn:aws:iam::123456789012:user:test",
     dict(partition="aws", account_id="123456789012", resource="user:test", service="iam", region="")
     ),
    ("arn:aws-cn:iam::123456789012:user:test",
     dict(partition="aws-cn", account_id="123456789012", resource="user:test", service="iam", region="")
     ),
    ("arn:aws:iam::123456789012:user",
     dict(partition="aws", account_id="123456789012", resource="user", service="iam", region="")
     ),
    ("arn:aws:s3:::my_corporate_bucket/*",
     dict(partition="aws", account_id="", resource="my_corporate_bucket/*", service="s3", region="")
     ),
    ("arn:aws:s3:::my_corporate_bucket/Development/*",
     dict(partition="aws", account_id="", resource="my_corporate_bucket/Development/*", service="s3", region="")
     ),
    ("arn:aws:rds:es-east-1:000000000000:snapshot:rds:my-db-snapshot",
     dict(partition="aws", account_id="000000000000", resource="snapshot:rds:my-db-snapshot", service="rds", region="es-east-1")
     ),
    ("arn:aws:cloudformation:us-east-1:012345678901:changeSet/Ansible-StackName-c6884247ede41eb0",
     dict(partition="aws", account_id="012345678901", resource="changeSet/Ansible-StackName-c6884247ede41eb0", service="cloudformation", region="us-east-1")
     ),
    ("test:aws:iam::123456789012:user", None),
    ("arn:aws::us-east-1:123456789012:user", None),
]


@pytest.mark.parametrize("input_params, output_params", arn_data)
def test_parse_aws_iam_arn(input_params, output_params):

    assert parse_aws_arn(input_params) == output_params
