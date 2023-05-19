#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_snapshot
version_added: 1.0.0
short_description: Creates a snapshot from an existing volume
description:
    - Creates an EC2 snapshot from an existing EBS volume.
options:
  volume_id:
    description:
      - Volume from which to take the snapshot.
    required: false
    type: str
  description:
    description:
      - Description to be applied to the snapshot.
    required: false
    type: str
  instance_id:
    description:
      - Instance that has the required volume to snapshot mounted.
    required: false
    type: str
  device_name:
    description:
      - Device name of a mounted volume to be snapshotted.
    required: false
    type: str
  snapshot_tags:
    description:
      - A dictionary of tags to add to the snapshot.
      - If the volume has a C(Name) tag this will be automatically added to the
        snapshot.
    type: dict
    required: false
    default: {}
  wait:
    description:
      - Wait for the snapshot to be ready.
    type: bool
    required: false
    default: true
  wait_timeout:
    description:
      - How long before wait gives up, in seconds.
    required: false
    default: 600
    type: int
  state:
    description:
      - Whether to add or create a snapshot.
    required: false
    default: present
    choices: ['absent', 'present']
    type: str
  snapshot_id:
    description:
      - Snapshot id to remove.
    required: false
    type: str
  last_snapshot_min_age:
    description:
      - If the volume's most recent snapshot has started less than I(last_snapshot_min_age) minutes ago, a new snapshot will not be created.
    required: false
    default: 0
    type: int
author: "Will Thames (@willthames)"
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Simple snapshot of volume using volume_id
- amazon.aws.ec2_snapshot:
    volume_id: vol-abcdef12
    description: snapshot of /data from DB123 taken 2013/11/28 12:18:32

# Snapshot of volume mounted on device_name attached to instance_id
- amazon.aws.ec2_snapshot:
    instance_id: i-12345678
    device_name: /dev/sdb1
    description: snapshot of /data from DB123 taken 2013/11/28 12:18:32

# Snapshot of volume with tagging
- amazon.aws.ec2_snapshot:
    instance_id: i-12345678
    device_name: /dev/sdb1
    snapshot_tags:
        frequency: hourly
        source: /data

# Remove a snapshot
- amazon.aws.ec2_snapshot:
    snapshot_id: snap-abcd1234
    state: absent

# Create a snapshot only if the most recent one is older than 1 hour
- amazon.aws.ec2_snapshot:
    volume_id: vol-abcdef12
    last_snapshot_min_age: 60
"""

RETURN = r"""
snapshot_id:
    description: The ID of the snapshot. Each snapshot receives a unique identifier when it is created.
    type: str
    returned: always
    sample: snap-01234567
tags:
    description: Any tags assigned to the snapshot.
    type: dict
    returned: always
    sample: "{ 'Name': 'instance-name' }"
volume_id:
    description: The ID of the volume that was used to create the snapshot.
    type: str
    returned: always
    sample: vol-01234567
volume_size:
    description: The size of the volume, in GiB.
    type: int
    returned: always
    sample: 8
"""

import datetime

try:
    import botocore
except ImportError:
    pass  # Taken care of by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.waiters import get_waiter


def _get_most_recent_snapshot(snapshots, max_snapshot_age_secs=None, now=None):
    """
    Gets the most recently created snapshot and optionally filters the result
    if the snapshot is too old
    :param snapshots: list of snapshots to search
    :param max_snapshot_age_secs: filter the result if its older than this
    :param now: simulate time -- used for unit testing
    :return:
    """
    if len(snapshots) == 0:
        return None

    if not now:
        now = datetime.datetime.now(datetime.timezone.utc)

    youngest_snapshot = max(snapshots, key=lambda s: s["StartTime"])
    snapshot_start = youngest_snapshot["StartTime"]
    snapshot_age = now - snapshot_start

    if max_snapshot_age_secs is not None:
        if snapshot_age.total_seconds() > max_snapshot_age_secs:
            return None

    return youngest_snapshot


def get_volume_by_instance(module, ec2, device_name, instance_id):
    try:
        _filter = {"attachment.instance-id": instance_id, "attachment.device": device_name}
        volumes = ec2.describe_volumes(aws_retry=True, Filters=ansible_dict_to_boto3_filter_list(_filter))["Volumes"]
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to describe Volume")

    if not volumes:
        module.fail_json(msg=f"Could not find volume with name {device_name} attached to instance {instance_id}")

    volume = volumes[0]
    return volume


def get_volume_by_id(module, ec2, volume):
    try:
        volumes = ec2.describe_volumes(
            aws_retry=True,
            VolumeIds=[volume],
        )["Volumes"]
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to describe Volume")

    if not volumes:
        module.fail_json(msg=f"Could not find volume with id {volume}")

    volume = volumes[0]
    return volume


@AWSRetry.jittered_backoff()
def _describe_snapshots(ec2, **params):
    paginator = ec2.get_paginator("describe_snapshots")
    return paginator.paginate(**params).build_full_result()


# Handle SnapshotCreationPerVolumeRateExceeded separately because we need a much
# longer delay than normal
@AWSRetry.jittered_backoff(catch_extra_error_codes=["SnapshotCreationPerVolumeRateExceeded"], delay=15)
def _create_snapshot(ec2, **params):
    # Fast retry on common failures ('global' rate limits)
    return ec2.create_snapshot(aws_retry=True, **params)


def get_snapshots_by_volume(module, ec2, volume_id):
    _filter = {"volume-id": volume_id}
    try:
        results = _describe_snapshots(ec2, Filters=ansible_dict_to_boto3_filter_list(_filter))
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to describe snapshots from volume")

    return results["Snapshots"]


def create_snapshot(
    module,
    ec2,
    description=None,
    wait=None,
    wait_timeout=None,
    volume_id=None,
    instance_id=None,
    snapshot_id=None,
    device_name=None,
    snapshot_tags=None,
    last_snapshot_min_age=None,
):
    snapshot = None
    changed = False

    if instance_id:
        volume = get_volume_by_instance(module, ec2, device_name, instance_id)
        volume_id = volume["VolumeId"]
    else:
        volume = get_volume_by_id(module, ec2, volume_id)
    if "Tags" not in volume:
        volume["Tags"] = {}
    if last_snapshot_min_age > 0:
        current_snapshots = get_snapshots_by_volume(module, ec2, volume_id)
        last_snapshot_min_age = last_snapshot_min_age * 60  # Convert to seconds
        snapshot = _get_most_recent_snapshot(current_snapshots, max_snapshot_age_secs=last_snapshot_min_age)
    # Create a new snapshot if we didn't find an existing one to use
    if snapshot is None:
        volume_tags = boto3_tag_list_to_ansible_dict(volume["Tags"])
        volume_name = volume_tags.get("Name")
        _tags = dict()
        if volume_name:
            _tags["Name"] = volume_name
        if snapshot_tags:
            _tags.update(snapshot_tags)

        params = {"VolumeId": volume_id}
        if description:
            params["Description"] = description
        if _tags:
            params["TagSpecifications"] = [
                {
                    "ResourceType": "snapshot",
                    "Tags": ansible_dict_to_boto3_tag_list(_tags),
                }
            ]
        try:
            if module.check_mode:
                module.exit_json(
                    changed=True,
                    msg="Would have created a snapshot if not in check mode",
                    volume_id=volume["VolumeId"],
                    volume_size=volume["Size"],
                )
            snapshot = _create_snapshot(ec2, **params)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed to create snapshot")
        changed = True
    if wait:
        waiter = get_waiter(ec2, "snapshot_completed")
        try:
            waiter.wait(SnapshotIds=[snapshot["SnapshotId"]], WaiterConfig=dict(Delay=3, MaxAttempts=wait_timeout // 3))
        except botocore.exceptions.WaiterError as e:
            module.fail_json_aws(e, msg="Timed out while creating snapshot")
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Error while waiting for snapshot creation")

    _tags = boto3_tag_list_to_ansible_dict(snapshot["Tags"])
    _snapshot = camel_dict_to_snake_dict(snapshot)
    _snapshot["tags"] = _tags
    results = {
        "snapshot_id": snapshot["SnapshotId"],
        "volume_id": snapshot["VolumeId"],
        "volume_size": snapshot["VolumeSize"],
        "tags": _tags,
        "snapshots": [_snapshot],
    }

    module.exit_json(changed=changed, **results)


def delete_snapshot(module, ec2, snapshot_id):
    if module.check_mode:
        try:
            _describe_snapshots(ec2, SnapshotIds=[(snapshot_id)])
            module.exit_json(changed=True, msg="Would have deleted snapshot if not in check mode")
        except is_boto3_error_code("InvalidSnapshot.NotFound"):
            module.exit_json(changed=False, msg="Invalid snapshot ID - snapshot not found")
    try:
        ec2.delete_snapshot(aws_retry=True, SnapshotId=snapshot_id)
    except is_boto3_error_code("InvalidSnapshot.NotFound"):
        module.exit_json(changed=False)
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to delete snapshot")

    # successful delete
    module.exit_json(changed=True)


def create_snapshot_ansible_module():
    argument_spec = dict(
        volume_id=dict(),
        description=dict(),
        instance_id=dict(),
        snapshot_id=dict(),
        device_name=dict(),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(type="int", default=600),
        last_snapshot_min_age=dict(type="int", default=0),
        snapshot_tags=dict(type="dict", default=dict()),
        state=dict(choices=["absent", "present"], default="present"),
    )
    mutually_exclusive = [
        ("instance_id", "snapshot_id", "volume_id"),
    ]
    required_if = [
        ("state", "absent", ("snapshot_id",)),
    ]
    required_one_of = [
        ("instance_id", "snapshot_id", "volume_id"),
    ]
    required_together = [
        ("instance_id", "device_name"),
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=mutually_exclusive,
        required_if=required_if,
        required_one_of=required_one_of,
        required_together=required_together,
        supports_check_mode=True,
    )

    return module


def main():
    module = create_snapshot_ansible_module()

    volume_id = module.params.get("volume_id")
    snapshot_id = module.params.get("snapshot_id")
    description = module.params.get("description")
    instance_id = module.params.get("instance_id")
    device_name = module.params.get("device_name")
    wait = module.params.get("wait")
    wait_timeout = module.params.get("wait_timeout")
    last_snapshot_min_age = module.params.get("last_snapshot_min_age")
    snapshot_tags = module.params.get("snapshot_tags")
    state = module.params.get("state")

    ec2 = module.client("ec2", retry_decorator=AWSRetry.jittered_backoff(retries=10))

    if state == "absent":
        delete_snapshot(
            module=module,
            ec2=ec2,
            snapshot_id=snapshot_id,
        )
    else:
        create_snapshot(
            module=module,
            description=description,
            wait=wait,
            wait_timeout=wait_timeout,
            ec2=ec2,
            volume_id=volume_id,
            instance_id=instance_id,
            snapshot_id=snapshot_id,
            device_name=device_name,
            snapshot_tags=snapshot_tags,
            last_snapshot_min_age=last_snapshot_min_age,
        )


if __name__ == "__main__":
    main()
