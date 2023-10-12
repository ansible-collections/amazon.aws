# (c) 2022 Red Hat Inc.

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import ANY
from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_snapshot_info

module_name = "ansible_collections.amazon.aws.plugins.modules.ec2_snapshot_info"


@pytest.mark.parametrize(
    "snapshot_ids,owner_ids,restorable_by_user_ids,filters,max_results,next_token_id,expected",
    [([], [], [], {}, None, None, {})],
)
def test_build_request_args(
    snapshot_ids, owner_ids, restorable_by_user_ids, filters, max_results, next_token_id, expected
):
    assert (
        ec2_snapshot_info.build_request_args(
            snapshot_ids, owner_ids, restorable_by_user_ids, filters, max_results, next_token_id
        )
        == expected
    )


def test_get_snapshots():
    module = MagicMock()
    connection = MagicMock()

    connection.describe_snapshots.return_value = {
        "Snapshots": [
            {
                "Description": "Created by CreateImage(i-083b9dd1234567890) for ami-01486e111234567890",
                "Encrypted": False,
                "OwnerId": "123456789000",
                "Progress": "100%",
                "SnapshotId": "snap-0f00cba1234567890",
                "StartTime": "2021-09-30T01:04:49.724000+00:00",
                "State": "completed",
                "StorageTier": "standard",
                "Tags": [
                    {"Key": "TagKey", "Value": "TagValue"},
                ],
                "VolumeId": "vol-0ae6c5e1234567890",
                "VolumeSize": 10,
            },
            {
                "Description": "Created by CreateImage(i-083b9dd1234567890) for ami-01486e111234567890",
                "Encrypted": False,
                "OwnerId": "123456789000",
                "Progress": "100%",
                "SnapshotId": "snap-0f00cba1234567890",
                "StartTime": "2021-09-30T01:04:49.724000+00:00",
                "State": "completed",
                "StorageTier": "standard",
                "Tags": [
                    {"Key": "TagKey", "Value": "TagValue"},
                ],
                "VolumeId": "vol-0ae6c5e1234567890",
                "VolumeSize": 10,
            },
        ]
    }

    request_args = {"SnapshotIds": ["snap-0f00cba1234567890"]}

    snapshot_info = ec2_snapshot_info.get_snapshots(connection, module, request_args)

    assert connection.describe_snapshots.call_count == 1
    connection.describe_snapshots.assert_called_with(aws_retry=True, SnapshotIds=["snap-0f00cba1234567890"])
    assert len(snapshot_info["Snapshots"]) == 2


@patch(module_name + ".build_request_args")
@patch(module_name + ".get_snapshots")
def test_list_ec2_snapshots(m_get_snapshots, m_build_request_args):
    module = MagicMock()
    connection = MagicMock()

    m_get_snapshots.return_value = {
        "Snapshots": [
            {
                "Description": "Created by CreateImage(i-083b9dd1234567890) for ami-01486e111234567890",
                "Encrypted": False,
                "OwnerId": "123456789000",
                "Progress": "100%",
                "SnapshotId": "snap-0f00cba1234567890",
                "StartTime": "2021-09-30T01:04:49.724000+00:00",
                "State": "completed",
                "StorageTier": "standard",
                "Tags": [
                    {"Key": "TagKey", "Value": "TagValue"},
                ],
                "VolumeId": "vol-0ae6c5e1234567890",
                "VolumeSize": 10,
            }
        ]
    }

    m_build_request_args.return_value = {"SnapshotIds": ["snap-0f00cba1234567890"]}

    request_args = ec2_snapshot_info.build_request_args()

    ec2_snapshot_info.list_ec2_snapshots(connection, module, request_args)

    assert m_get_snapshots.call_count == 1
    m_get_snapshots.assert_has_calls(
        [
            call(connection, module, m_build_request_args.return_value),
        ]
    )


@patch(module_name + ".AnsibleAWSModule")
def test_main_success(m_AnsibleAWSModule):
    m_module = MagicMock()
    m_AnsibleAWSModule.return_value = m_module

    ec2_snapshot_info.main()

    m_module.client.assert_called_with("ec2", retry_decorator=ANY)
