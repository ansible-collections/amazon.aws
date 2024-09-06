# (c) 2024 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.rds import AnsibleRDSError
from ansible_collections.amazon.aws.plugins.modules import rds_instance
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
        (
            [
                {
                    "DBInstanceIdentifier": "my-instance",
                    "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:og:my-instance",
                    "TagList": [{"Key": "My Tag", "Value": "My Value"}],
                    "Engine": "oracle-ee-cdb",
                    "MultiTenant": "True",
                }
            ],
            {
                "DBInstanceIdentifier": "my-instance",
                "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:og:my-instance",
                "Tags": {"My Tag": "My Value"},
                "Engine": "oracle-ee-cdb",
                "MultiTenant": "True",
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


@patch(mod_name + ".describe_db_instances")
@patch(mod_name + ".get_changing_options_with_inconsistent_keys")
def test_get_options_with_changing_values(m_get_changing_options_with_inconsistent_keys, m_describe_db_instances):
    module = MagicMock()
    client = MagicMock()
    instance = {}

    m_describe_db_instances.return_value = [
        {
            "DBInstanceIdentifier": "my-instance",
            "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:og:my-instance",
            "TagList": [{"Key": "My Tag", "Value": "My Value"}],
            "Engine": "oracle-ee-cdb",
            "MultiTenant": True,
            "Endpoint": {"Port": "3000"},
            "DBSubnetGroup": {
                "DBSubnetGroupDescription": "default",
                "DBSubnetGroupName": "default",
            },
        }
    ]

    module.params = {
        "db_instance_identifier": "my-instance",
        "purge_cloudwatch_logs_exports": None,
        "force_update_password": None,
        "port": None,
        "enable_cloudwatch_logs_exports": None,
        "storage_type": None,
        "purge_security_groups": None,
        "ca_certificate_identifier": None,
        "db_instance_arn": "arn:aws:rds:us-east-1:123456789012:og:my-instance",
        "engine": "oracle-ee-cdb",
        "multi_tenant": False,
        "db_subnet_group": {
            "db_subnet_group_description": "default",
            "db_subnet_group_name": "default",
            "subnet_group_status": "Complete",
        },
    }
    m_get_changing_options_with_inconsistent_keys.return_value = {}
    rds_instance.get_options_with_changing_values(client, module, instance)
    assert module.require_botocore_at_least.call_count == 0
    module.fail_json.assert_called_with(
        msg="A DB which is configured to be a multi tenant cannot be modified to use single tenant configuration."
    )


def test_validate_options():
    module = MagicMock()
    client = MagicMock()
    instance = ""

    module.params = {
        "skip_final_snapshot": None,
        "final_db_snapshot_identifier": None,
        "new_db_instance_identifier": None,
        "tde_credential_password": False,
        "tde_credential_arn": False,
        "read_replica": None,
        "creation_source": None,
        "source_db_instance_identifier": None,
        "engine": "Aurora",
        "multi_tenant": True,
        "state": "present",
    }
    rds_instance.validate_options(client, module, instance)
    assert module.require_botocore_at_least.call_count == 0
    module.fail_json.assert_called_with(
        msg="Multi Tenant parameter only applies to RDS for Oracle container database (CDB) engines and not to Aurora."
    )
