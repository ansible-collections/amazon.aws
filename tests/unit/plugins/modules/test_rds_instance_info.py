# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from unittest.mock import ANY
from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

import botocore.exceptions
import pytest

from ansible_collections.amazon.aws.plugins.modules import rds_instance_info

mod_name = "ansible_collections.amazon.aws.plugins.modules.rds_instance_info"


def a_boto_exception():
    return botocore.exceptions.UnknownServiceError(service_name="Whoops", known_service_names="Oula")


@patch(mod_name + "._describe_db_instances")
@patch(mod_name + ".get_instance_tags")
def test_instance_info_one_instance(m_get_instance_tags, m_describe_db_instances):
    conn = MagicMock()
    instance_name = "my-instance"
    m_get_instance_tags.return_value = []
    m_describe_db_instances.return_value = [
        {
            "DBInstanceIdentifier": instance_name,
            "DBInstanceArn": "arn:aws:rds:us-east-2:123456789012:og:" + instance_name,
        }
    ]
    rds_instance_info.instance_info(conn, instance_name, filters={})

    m_describe_db_instances.assert_called_with(conn, DBInstanceIdentifier=instance_name)
    m_get_instance_tags.assert_called_with(conn, arn="arn:aws:rds:us-east-2:123456789012:og:" + instance_name)


@patch(mod_name + "._describe_db_instances")
@patch(mod_name + ".get_instance_tags")
def test_instance_info_all_instances(m_get_instance_tags, m_describe_db_instances):
    conn = MagicMock()
    m_get_instance_tags.return_value = []
    m_describe_db_instances.return_value = [
        {
            "DBInstanceIdentifier": "first-instance",
            "DBInstanceArn": "arn:aws:rds:us-east-2:123456789012:og:first-instance",
        },
        {
            "DBInstanceIdentifier": "second-instance",
            "DBInstanceArn": "arn:aws:rds:us-east-2:123456789012:og:second-instance",
        },
    ]
    rds_instance_info.instance_info(conn, instance_name=None, filters={"engine": "postgres"})

    m_describe_db_instances.assert_called_with(conn, Filters=[{"Name": "engine", "Values": ["postgres"]}])
    assert m_get_instance_tags.call_count == 2
    m_get_instance_tags.assert_has_calls(
        [
            call(conn, arn="arn:aws:rds:us-east-2:123456789012:og:first-instance"),
            call(conn, arn="arn:aws:rds:us-east-2:123456789012:og:second-instance"),
        ]
    )


def test_get_instance_tags():
    conn = MagicMock()
    conn.list_tags_for_resource.return_value = {
        "TagList": [
            {"Key": "My-tag", "Value": "the-value$"},
        ],
        "NextToken": "some-token",
    }

    tags = rds_instance_info.get_instance_tags(conn, "arn:aws:rds:us-east-2:123456789012:og:second-instance")
    conn.list_tags_for_resource.assert_called_with(
        ResourceName="arn:aws:rds:us-east-2:123456789012:og:second-instance",
        aws_retry=True,
    )
    assert tags == {"My-tag": "the-value$"}


def test_api_failure_get_tag():
    conn = MagicMock()
    conn.list_tags_for_resource.side_effect = a_boto_exception()

    with pytest.raises(rds_instance_info.RdsInstanceInfoFailure):
        rds_instance_info.get_instance_tags(conn, "arn:blabla")


def test_api_failure_describe():
    conn = MagicMock()
    conn.get_paginator.side_effect = a_boto_exception()

    with pytest.raises(rds_instance_info.RdsInstanceInfoFailure):
        rds_instance_info.instance_info(conn, None, {})


@patch(mod_name + ".AnsibleAWSModule")
def test_main_success(m_AnsibleAWSModule):
    m_module = MagicMock()
    m_AnsibleAWSModule.return_value = m_module

    rds_instance_info.main()

    m_module.client.assert_called_with("rds", retry_decorator=ANY)
    m_module.exit_json.assert_called_with(changed=False, instances=[])


@patch(mod_name + "._describe_db_instances")
@patch(mod_name + ".AnsibleAWSModule")
def test_main_failure(m_AnsibleAWSModule, m_describe_db_instances):
    m_module = MagicMock()
    m_AnsibleAWSModule.return_value = m_module
    m_describe_db_instances.side_effect = a_boto_exception()

    rds_instance_info.main()

    m_module.client.assert_called_with("rds", retry_decorator=ANY)
    m_module.fail_json_aws.assert_called_with(ANY, "Couldn't get instance information")
