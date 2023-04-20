# (c) 2022 Red Hat Inc.

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest
from unittest.mock import MagicMock
from unittest.mock import patch

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.modules import backup_restore_job_info

module_name = "ansible_collections.amazon.aws.plugins.modules.backup_restore_job_info"


@pytest.mark.parametrize(
    "account_id, status, created_before, created_after, completed_before, completed_after,expected",
    [
        ("", "", "", "", "", "", {}),
        ("123456789012", "", "", "", "", "", {"ByAccountId": "123456789012"}),
        (
            "123456789012",
            "COMPLETED",
            "",
            "",
            "",
            "",
            {"ByAccountId": "123456789012", "ByStatus": "COMPLETED"},
        ),
    ],
)
def test_build_request_args(
    account_id, status, created_before, created_after, completed_before, completed_after, expected
):
    assert (
        backup_restore_job_info.build_request_args(
            account_id, status, created_before, created_after, completed_before, completed_after
        )
        == expected
    )


def test__describe_restore_job():
    connection = MagicMock()
    module = MagicMock()

    restore_job_id = "52BEE289-xxxx-xxxx-xxxx-47DCAA2E7ACD"
    restore_job_info = {
        "AccountId": "123456789012",
        "BackupSizeInBytes": "8589934592",
        "CompletionDate": "2023-03-13T15:53:07.172000-07:00",
        "CreatedResourceArn": "arn:aws:ec2:us-east-2:123456789012:instance/i-01234567ec51af3f",
        "CreationDate": "2023-03-13T15:53:07.172000-07:00",
        "IamRoleArn": "arn:aws:iam::123456789012:role/service-role/AWSBackupDefaultServiceRole",
        "PercentDone": "0.00%",
        "RecoveryPointArn": "arn:aws:ec2:us-east-2::image/ami-01234567ec51af3f",
        "ResourceType": "EC2",
        "RestoreJobId": "52BEE289-xxxx-xxxx-xxxx-47DCAA2E7ACD",
        "Status": "COMPLETED",
    }

    connection.describe_restore_job.return_value = restore_job_info

    result = backup_restore_job_info._describe_restore_job(connection, module, restore_job_id)

    assert result == [camel_dict_to_snake_dict(restore_job_info)]
    connection.describe_restore_job.assert_called_with(RestoreJobId=restore_job_id)
    connection.describe_restore_job.call_count == 1


def test__list_restore_jobs():
    connection = MagicMock()
    conn_paginator = MagicMock()
    paginate = MagicMock()

    request_args = {"ByAccountId": "123456789012"}

    restore_job = {
        "AccountId": "123456789012",
        "BackupSizeInBytes": "8589934592",
        "CompletionDate": "2023-03-13T15:53:07.172000-07:00",
        "CreatedResourceArn": "arn:aws:ec2:us-east-2:123456789012:instance/i-01234567ec51af3f",
        "CreationDate": "2023-03-13T15:53:07.172000-07:00",
        "IamRoleArn": "arn:aws:iam::123456789012:role/service-role/AWSBackupDefaultServiceRole",
        "PercentDone": "0.00%",
        "RecoveryPointArn": "arn:aws:ec2:us-east-2::image/ami-01234567ec51af3f",
        "ResourceType": "EC2",
        "RestoreJobId": "52BEE289-xxxx-xxxx-xxxx-47DCAA2E7ACD",
        "Status": "COMPLETED",
    }

    connection.get_paginator.return_value = conn_paginator
    conn_paginator.paginate.return_value = paginate

    paginate.build_full_result.return_value = {"RestoreJobs": [restore_job]}

    result = backup_restore_job_info._list_restore_jobs(connection=connection, **request_args)

    assert result == paginate.build_full_result.return_value
    connection.get_paginator.assert_called_with("list_restore_jobs")
    conn_paginator.paginate.assert_called_with(**request_args)


@patch(module_name + "._list_restore_jobs")
def test_list_restore_jobs(m__list_restore_jobs):
    connection = MagicMock()
    module = MagicMock()

    request_args = {"ByAccountId": "123456789012"}

    m__list_restore_jobs.return_value = {
        "RestoreJobs": [
            {
                "AccountId": "123456789012",
                "BackupSizeInBytes": "8589934592",
                "CompletionDate": "2023-03-13T15:53:07.172000-07:00",
                "CreatedResourceArn": "arn:aws:ec2:us-east-2:123456789012:instance/i-01234567ec51af3f",
                "CreationDate": "2023-03-13T15:53:07.172000-07:00",
                "IamRoleArn": "arn:aws:iam::123456789012:role/service-role/AWSBackupDefaultServiceRole",
                "PercentDone": "0.00%",
                "RecoveryPointArn": "arn:aws:ec2:us-east-2::image/ami-01234567ec51af3f",
                "ResourceType": "EC2",
                "RestoreJobId": "52BEE289-xxxx-xxxx-xxxx-47DCAA2E7ACD",
                "Status": "COMPLETED",
            }
        ]
    }

    list_restore_jobs_result = backup_restore_job_info.list_restore_jobs(connection, module, request_args)

    assert m__list_restore_jobs.call_count == 1
    m__list_restore_jobs.assert_called_with(connection, **request_args)
    assert len(list_restore_jobs_result) == 1


@patch(module_name + ".AnsibleAWSModule")
def test_main_success(m_AnsibleAWSModule):
    m_module = MagicMock()
    m_AnsibleAWSModule.return_value = m_module

    backup_restore_job_info.main()

    m_module.client.assert_called_with("backup")
    m_module.exit_json.assert_called_with(changed=False, restore_jobs=[{}])
