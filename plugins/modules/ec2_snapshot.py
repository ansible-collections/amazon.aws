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
      - If the volume has a V(Name) tag this will be automatically added to the
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
      - If the volume's most recent snapshot has started less than O(last_snapshot_min_age) minutes ago, a new snapshot will not be created.
    required: false
    default: 0
    type: int
  modify_create_vol_permission:
    description:
      - If set to V(true), ec2 snapshot's createVolumePermissions can be modified.
    required: false
    type: bool
    version_added: 6.1.0
  purge_create_vol_permission:
    description:
      - Whether unspecified group names or user IDs should be removed from the snapshot createVolumePermission.
      - Must set O(modify_create_vol_permission) to V(True) for when O(purge_create_vol_permission) is set to V(True).
    required: False
    type: bool
    default: False
    version_added: 6.1.0
  group_names:
    description:
      - The group to be added or removed. The possible value is V(all).
      - Mutually exclusive with O(user_ids).
    required: false
    type: list
    elements: str
    choices: ["all"]
    version_added: 6.1.0
  user_ids:
    description:
      - The account user IDs to be added or removed.
      - If createVolumePermission on snapshot is currently set to Public i.e. O(group_names=all),
        providing O(user_ids) will not make createVolumePermission Private unless O(modify_create_vol_permission) is set to V(true).
      - Mutually exclusive with O(group_names).
    required: false
    type: list
    elements: str
    version_added: 6.1.0
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

- name: Reset snapshot createVolumePermission (change permission to "Private")
  amazon.aws.ec2_snapshot:
    snapshot_id: snap-06a6f641234567890
    modify_create_vol_permission: true
    purge_create_vol_permission: true

- name: Modify snapshot createVolmePermission to add user IDs (specify purge_create_vol_permission=true to change permssion to "Private")
  amazon.aws.ec2_snapshot:
    snapshot_id: snap-06a6f641234567890
    modify_create_vol_permission: true
    user_ids:
      - '123456789012'
      - '098765432109'

- name: Modify snapshot createVolmePermission - remove all except specified user_ids
  amazon.aws.ec2_snapshot:
    snapshot_id: snap-06a6f641234567890
    modify_create_vol_permission: true
    purge_create_vol_permission: true
    user_ids:
      - '123456789012'

- name: Replace (purge existing) snapshot createVolmePermission annd add user IDs
  amazon.aws.ec2_snapshot:
    snapshot_id: snap-06a6f641234567890
    modify_create_vol_permission: true
    purge_create_vol_permission: true
    user_ids:
      - '111111111111'

- name: Modify snapshot createVolmePermission - make createVolumePermission "Public"
  amazon.aws.ec2_snapshot:
    snapshot_id: snap-06a6f641234567890
    modify_create_vol_permission: true
    purge_create_vol_permission: true
    group_names:
      - all
"""

RETURN = r"""
snapshot_id:
    description: The ID of the snapshot. Each snapshot receives a unique identifier when it is created.
    type: str
    returned: always
    sample: snap-01234567
snapshots:
    description: List of snapshots.
    returned: always
    type: list
    elements: dict
    contains:
        description:
            description: Description specified by the CreateSnapshotRequest that has been applied to all snapshots.
            type: str
            returned: always
            sample: ""
        encrypted:
            description: Indicates whether the snapshot is encrypted.
            type: bool
            returned: always
            sample: false
        owner_id:
            description: Account id used when creating this snapshot.
            type: str
            returned: always
            sample: 123456
        progress:
            description: Progress this snapshot has made towards completing.
            type: str
            returned: always
            sample: ""
        snapshot_id:
            description: Snapshot id that can be used to describe this snapshot.
            type: str
            returned: always
            sample: snap-1234
        start_time:
            description: Time this snapshot was started. This is the same for all snapshots initiated by the same request.
            type: str
            returned: always
            sample: "2024-05-07T14:29:24.523000+00:00"
        state:
            description: Current state of the snapshot.
            type: str
            returned: always
            sample: pending
        tags:
            description: Tags associated with this snapshot.
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
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import create_snapshot
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import delete_snapshot
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_snapshot_attribute
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_snapshots
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_volumes
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import modify_snapshot_attribute
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import reset_snapshot_attribute
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.waiters import wait_for_resource_state


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


def get_volume_by_instance(module: AnsibleAWSModule, ec2, device_name: str, instance_id: str) -> Dict[str, Any]:
    try:
        _filter = {"attachment.instance-id": instance_id, "attachment.device": device_name}
        volumes = describe_volumes(ec2, Filters=ansible_dict_to_boto3_filter_list(_filter))
    except AnsibleEC2Error as e:
        module.fail_json_aws(e, msg="Failed to describe Volume")

    if not volumes:
        module.fail_json(msg=f"Could not find volume with name {device_name} attached to instance {instance_id}")

    volume = volumes[0]
    return volume


def get_volume_by_id(module: AnsibleAWSModule, ec2, volume: str) -> Dict[str, Any]:
    try:
        volumes = describe_volumes(ec2, VolumeIds=[volume])
    except AnsibleEC2Error as e:
        module.fail_json_aws(e, msg="Failed to describe Volume")

    if not volumes:
        module.fail_json(msg=f"Could not find volume with id {volume}")

    return volumes[0]


def get_snapshots_by_volume(module: AnsibleAWSModule, ec2, volume_id: str) -> Optional[List[Dict[str, Any]]]:
    _filter = {"volume-id": volume_id}
    try:
        results = describe_snapshots(ec2, Filters=ansible_dict_to_boto3_filter_list(_filter))
    except AnsibleEC2Error as e:
        module.fail_json_aws(e, msg="Failed to describe snapshots from volume")

    return results.get("Snapshots", [])


def _create_snapshot(module, ec2):
    snapshot = None
    changed = False

    volume_id = module.params.get("volume_id")
    description = module.params.get("description")
    instance_id = module.params.get("instance_id")
    device_name = module.params.get("device_name")
    wait = module.params.get("wait")
    wait_timeout = module.params.get("wait_timeout")
    last_snapshot_min_age = module.params.get("last_snapshot_min_age")
    snapshot_tags = module.params.get("snapshot_tags")

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
            volume_id = params.pop("VolumeId")
            snapshot = create_snapshot(ec2, volume_id=volume_id, **params)
        except AnsibleEC2Error as e:
            module.fail_json_aws(e, msg="Failed to create snapshot")
        changed = True
    if wait:
        wait_for_resource_state(
            ec2,
            module,
            "snapshot_completed",
            delay=3,
            max_attempts=wait_timeout // 3,
            SnapshotIds=[snapshot["SnapshotId"]],
        )

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


def _delete_snapshot(module: AnsibleAWSModule, connection) -> None:
    snapshot_id = module.params.get("snapshot_id")
    if module.check_mode:
        try:
            snapshots = describe_snapshots(connection, SnapshotIds=[(snapshot_id)])
            if not snapshots:
                module.exit_json(changed=False, msg="snapshot not found")
            module.exit_json(changed=True, msg="Would have deleted snapshot if not in check mode")
        except AnsibleEC2Error as e:
            module.fail_json_aws(e, msg="Failed to describe snapshots")
    try:
        changed = delete_snapshot(connection, snapshot_id)
    except AnsibleEC2Error as e:
        module.fail_json_aws(e, msg="Failed to delete snapshot")

    # successful delete
    module.exit_json(changed=changed)


def build_modify_createVolumePermission_params(module):
    snapshot_id = module.params.get("snapshot_id")
    user_ids = module.params.get("user_ids")
    group_names = module.params.get("group_names")

    if not user_ids and not group_names:
        module.fail_json(msg="Please provide either Group IDs or User IDs to modify permissions")

    params = {
        "Attribute": "createVolumePermission",
        "OperationType": "add",
        "SnapshotId": snapshot_id,
        "GroupNames": group_names,
        "UserIds": user_ids,
    }

    # remove empty value params
    params = {k: v for k, v in params.items() if v}

    return params


def check_user_or_group_update_needed(module: AnsibleAWSModule, ec2) -> bool:
    try:
        existing_create_vol_permission = describe_snapshot_attribute(
            ec2, snapshot_id=module.params.get("snapshot_id"), attribute="createVolumePermission"
        )["CreateVolumePermissions"]
    except AnsibleEC2Error as e:
        module.fail_json_aws(e, failed="Failed to describe snapshot attribute")
    purge_permission = module.params.get("purge_create_vol_permission")
    supplied_group_names = module.params.get("group_names")
    supplied_user_ids = module.params.get("user_ids")

    # if createVolumePermission is already "Public", adding "user_ids" is not needed
    if any(item.get("Group") == "all" for item in existing_create_vol_permission) and not purge_permission:
        return False

    if supplied_group_names:
        existing_group_names = {item.get("Group") for item in existing_create_vol_permission or []}
        if set(supplied_group_names) == set(existing_group_names):
            return False
        else:
            return True

    if supplied_user_ids:
        existing_user_ids = {item.get("UserId") for item in existing_create_vol_permission or []}
        if set(supplied_user_ids) == set(existing_user_ids):
            return False
        else:
            return True

    if purge_permission and existing_create_vol_permission == []:
        return False

    return True


def _modify_snapshot_createVolumePermission(module: AnsibleAWSModule, ec2) -> None:
    snapshot_id = module.params.get("snapshot_id")
    purge_create_vol_permission = module.params.get("purge_create_vol_permission")
    update_needed = check_user_or_group_update_needed(module, ec2)

    if not update_needed:
        module.exit_json(changed=False, msg="Supplied CreateVolumePermission already applied, update not needed")

    if purge_create_vol_permission:
        if module.check_mode:
            module.exit_json(changed=True, msg="Would have reset CreateVolumePermission")
        try:
            reset_snapshot_attribute(ec2, attribute="createVolumePermission", snapshot_id=snapshot_id)
        except AnsibleEC2Error as e:
            module.fail_json_aws(e, msg="Failed to reset createVolumePermission")
        if not module.params.get("user_ids") and not module.params.get("group_names"):
            module.exit_json(changed=True, msg="Reset createVolumePermission successfully")

    params = build_modify_createVolumePermission_params(module)

    if module.check_mode:
        module.exit_json(changed=True, msg="Would have modified CreateVolumePermission")

    try:
        snapshot_id = params.pop("SnapshotId")
        modify_snapshot_attribute(ec2, snapshot_id=snapshot_id, **params)
    except AnsibleEC2Error as e:
        module.fail_json_aws(e, msg="Failed to modify createVolumePermission")

    module.exit_json(changed=True, msg="Successfully modified CreateVolumePermission")


def create_snapshot_ansible_module() -> AnsibleAWSModule:
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
        modify_create_vol_permission=dict(type="bool"),
        purge_create_vol_permission=dict(type="bool", default=False),
        user_ids=dict(type="list", elements="str"),
        group_names=dict(type="list", elements="str", choices=["all"]),
    )
    mutually_exclusive = [
        ("instance_id", "snapshot_id", "volume_id"),
        ("group_names", "user_ids"),
    ]
    required_if = [
        ("state", "absent", ("snapshot_id",)),
        ("purge_create_vol_permission", True, ("modify_create_vol_permission",)),
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

    state = module.params.get("state")
    modify_create_vol_permission = module.params.get("modify_create_vol_permission")

    ec2 = module.client("ec2")

    if state == "absent":
        _delete_snapshot(module, ec2)
    elif modify_create_vol_permission is True:
        _modify_snapshot_createVolumePermission(module, ec2)
    elif state == "present":
        _create_snapshot(module, ec2)


if __name__ == "__main__":
    main()
