# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

from ansible_collections.amazon.aws.plugins.module_utils.rds import AnsibleRDSError
from ansible_collections.amazon.aws.plugins.modules import rds_instance_info
from ansible_collections.amazon.aws.plugins.modules.rds_instance_info import instance_info

mod_name = "ansible_collections.amazon.aws.plugins.modules.rds_instance_info"


@patch(mod_name + ".describe_db_instances")
def test_instance_info_one_instance(m_describe_db_instances):
    conn = MagicMock()
    module = MagicMock()
    instance_name = "my-instance"
    m_describe_db_instances.return_value = [
        {
            "DBInstanceIdentifier": instance_name,
            "DBInstanceArn": "arn:aws:rds:us-east-2:123456789012:og:" + instance_name,
            "TagList": [],
        }
    ]

    assert instance_info(conn, module, instance_name, filters={}) == [
        {
            "db_instance_identifier": instance_name,
            "db_instance_arn": "arn:aws:rds:us-east-2:123456789012:og:" + instance_name,
            "tags": {},
        }
    ]
    m_describe_db_instances.assert_called_with(conn, DBInstanceIdentifier=instance_name)


@patch(mod_name + ".describe_db_instances")
def test_instance_info_all_instances(m_describe_db_instances):
    conn = MagicMock()
    module = MagicMock()
    m_describe_db_instances.return_value = [
        {
            "DBInstanceIdentifier": "first-instance",
            "DBInstanceArn": "arn:aws:rds:us-east-2:123456789012:og:first-instance",
            "TagList": [],
        },
        {
            "DBInstanceIdentifier": "second-instance",
            "DBInstanceArn": "arn:aws:rds:us-east-2:123456789012:og:second-instance",
            "TagList": [{"Key": "MyTag", "Value": "My tag value"}],
        },
    ]

    assert instance_info(conn, module, instance_name=None, filters={"engine": "postgres"}) == [
        {
            "db_instance_identifier": "first-instance",
            "db_instance_arn": "arn:aws:rds:us-east-2:123456789012:og:first-instance",
            "tags": {},
        },
        {
            "db_instance_identifier": "second-instance",
            "db_instance_arn": "arn:aws:rds:us-east-2:123456789012:og:second-instance",
            "tags": {"MyTag": "My tag value"},
        },
    ]
    m_describe_db_instances.assert_called_with(conn, Filters=[{"Name": "engine", "Values": ["postgres"]}])


@patch(mod_name + ".AnsibleAWSModule")
def test_main_success(m_AnsibleAWSModule):
    m_module = MagicMock()
    m_AnsibleAWSModule.return_value = m_module

    rds_instance_info.main()

    m_module.client.assert_called_with("rds")
    m_module.exit_json.assert_called_with(changed=False, instances=[])


@patch(mod_name + ".describe_db_instances")
@patch(mod_name + ".AnsibleAWSModule")
def test_main_failure(m_AnsibleAWSModule, m_describe_db_instances):
    m_module = MagicMock()
    m_AnsibleAWSModule.return_value = m_module
    e = AnsibleRDSError()
    m_describe_db_instances.side_effect = e

    rds_instance_info.main()

    m_module.client.assert_called_with("rds")
    m_module.fail_json_aws.assert_called_with(e)
