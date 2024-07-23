# (c) 2024 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.rds import AnsibleRDSError
from ansible_collections.amazon.aws.plugins.modules.rds_instance import get_instance

mod_name = "ansible_collections.amazon.aws.plugins.modules.rds_instance"


@pytest.mark.parametrize(
    "instances, expected",
    [
        ([], {}),
        (
            [
                {
                    "DBInstanceIdentifier": "my-instance",
                    "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:og:my-instance",
                    "TagList": [],
                }
            ],
            {
                "DBInstanceIdentifier": "my-instance",
                "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:og:my-instance",
                "Tags": {},
            },
        ),
        (
            [
                {
                    "DBInstanceIdentifier": "my-instance",
                    "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:og:my-instance",
                    "TagList": [{"Key": "My Tag", "Value": "My Value"}],
                    "ProcessorFeatures": [{"Name": "coreCount", "Value": "1"}],
                    "PendingModifiedValues": {
                        "ProcessorFeatures": [{"Name": "coreCount", "Value": "2"}],
                    },
                }
            ],
            {
                "DBInstanceIdentifier": "my-instance",
                "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:og:my-instance",
                "Tags": {"My Tag": "My Value"},
                "ProcessorFeatures": {"coreCount": "1"},
                "PendingModifiedValues": {"ProcessorFeatures": {"coreCount": "2"}},
            },
        ),
    ],
)
@patch(mod_name + ".describe_db_instances")
def test_get_instance_success(m_describe_db_instances, instances, expected):
    client = MagicMock()
    module = MagicMock()
    m_describe_db_instances.return_value = instances
    assert get_instance(client, module, "my-instance") == expected


@patch(mod_name + ".describe_db_instances")
def test_get_instance_failure(m_describe_db_instances):
    client = MagicMock()
    module = MagicMock()
    e = AnsibleRDSError()
    m_describe_db_instances.side_effect = e
    get_instance(client, module, "my-instance")
    module.fail_json_aws.assert_called_once_with(e, msg="Failed to get DB instance my-instance")
