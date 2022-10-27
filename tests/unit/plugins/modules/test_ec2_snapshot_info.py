# (c) 2022 Red Hat Inc.

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock, Mock, patch, ANY, call

from ansible_collections.amazon.aws.plugins.modules import ec2_snapshot_info

module_name = "ansible_collections.amazon.aws.plugins.modules.ec2_snapshot_info"


def test_describe_snapshots():
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
                    {
                        'Key': 'TagKey',
                        'Value': 'TagValue'
                    },
                ],
                "VolumeId": "vol-0ae6c5e1234567890",
                "VolumeSize": 10
            }
        ]}

    params = {
        "SnapshotIds": ["snap-0f00cba1234567890"]
    }

    snapshot_info = ec2_snapshot_info._describe_snapshots(connection, module, **params)

    connection.describe_snapshots.assert_called_with(aws_retry=True, SnapshotIds=["snap-0f00cba1234567890"])
    assert connection.describe_snapshots.call_count == 1
    assert len(snapshot_info['Snapshots']) > 0
    assert 'SnapshotId' in snapshot_info['Snapshots'][0]


@patch(module_name + "._describe_snapshots")
def test_get_snapshot_info_by_id(mock__describe_snapshots):
    module = MagicMock()
    connection = MagicMock()

    mock__describe_snapshots.return_value = {
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
                    {
                        'Key': 'TagKey',
                        'Value': 'TagValue'
                    },
                ],
                "VolumeId": "vol-0ae6c5e1234567890",
                "VolumeSize": 10
            }
        ]}

    module.params = {
        "snapshot_ids": ["snap-0f00cba1234567890"]
    }

    ec2_snapshot_info.list_ec2_snapshots(connection, module)

    assert mock__describe_snapshots.call_count == 1
    mock__describe_snapshots.assert_has_calls(
        [
            call(connection, module, SnapshotIds=["snap-0f00cba1234567890"]),
        ]
    )


@patch(module_name + ".AnsibleAWSModule")
def test_main_success(m_AnsibleAWSModule):
    m_module = MagicMock()
    m_AnsibleAWSModule.return_value = m_module

    ec2_snapshot_info.main()

    m_module.client.assert_called_with("ec2", retry_decorator=ANY)
