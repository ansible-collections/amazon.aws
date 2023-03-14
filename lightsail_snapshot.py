#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: lightsail_snapshot
version_added: "6.0.0"
short_description: Creates snapshots of AWS Lightsail instances
description:
    - Creates snapshots of AWS Lightsail instances.
author:
    - "Nuno Saavedra (@Nfsaavedra)"
options:
  state:
    description:
      - Indicate desired state of the target.
    default: present
    choices: ['present', 'absent']
    type: str
  snapshot_name:
    description: Name of the new instance snapshot.
    required: true
    type: str
  instance_name:
    description:
      - Name of the instance to create the snapshot.
      - Required when I(state=present).
    type: str
  wait:
    description:
      - Wait for the instance snapshot to be created before returning.
    type: bool
    default: true
  wait_timeout:
    description:
      - How long before I(wait) gives up, in seconds.
    default: 300
    type: int

extends_documentation_fragment:
- amazon.aws.common.modules
- amazon.aws.region.modules
- amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Create AWS Lightsail snapshot
  lightsail_snapshot:
    region: us-east-1
    snapshot_name: "my_instance_snapshot"
    instance_name: "my_instance"

- name: Delete AWS Lightsail snapshot
  lightsail_snapshot:
    region: us-east-1
    snapshot_name: "my_instance_snapshot"
    state: absent
"""

RETURN = r"""
changed:
  description: if a snapshot has been modified/created
  returned: always
  type: bool
  sample:
    changed: true
snapshot:
  description: instance snapshot data
  type: dict
  returned: always
  sample:
    arn: "arn:aws:lightsail:us-east-1:070807442430:InstanceSnapshot/54b0f785-7132-443d-9e32-95a6825636a4"
    created_at: "2023-02-23T18:46:11.183000+00:00"
    from_attached_disks: []
    from_blueprint_id: "amazon_linux_2"
    from_bundle_id: "nano_2_0"
    from_instance_arn: "arn:aws:lightsail:us-east-1:070807442430:Instance/5ca1e7ca-a994-4e19-bb82-deb9d79e9ca3"
    from_instance_name: "my_instance"
    is_from_auto_snapshot: false
    location:
      availability_zone: "all"
      region_name: "us-east-1"
    name: "my_instance_snapshot"
    resource_type: "InstanceSnapshot"
    size_in_gb: 20
    state: "available"
    support_code: "351201681302/ami-06b48e5589f1e248b"
    tags: []
"""

import time

try:
    import botocore
except ImportError:
    # will be caught by AnsibleAWSModule
    pass

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def find_instance_snapshot_info(module, client, instance_snapshot_name, fail_if_not_found=False):
    try:
        res = client.get_instance_snapshot(instanceSnapshotName=instance_snapshot_name)
    except is_boto3_error_code("NotFoundException") as e:
        if fail_if_not_found:
            module.fail_json_aws(e)
        return None
    except botocore.exceptions.ClientError as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e)
    return res["instanceSnapshot"]


def wait_for_instance_snapshot(module, client, instance_snapshot_name):
    wait_timeout = module.params.get("wait_timeout")
    wait_max = time.time() + wait_timeout
    snapshot = find_instance_snapshot_info(module, client, instance_snapshot_name)

    while wait_max > time.time():
        snapshot = find_instance_snapshot_info(module, client, instance_snapshot_name)
        current_state = snapshot["state"]
        if current_state != "pending":
            break
        time.sleep(5)
    else:
        module.fail_json(msg=f'Timed out waiting for instance snapshot "{instance_snapshot_name}" to be created.')

    return snapshot


def create_snapshot(module, client):
    snapshot = find_instance_snapshot_info(module, client, module.params.get("snapshot_name"))
    new_instance = snapshot is None

    if module.check_mode or not new_instance:
        snapshot = snapshot if snapshot is not None else {}
        module.exit_json(
            changed=new_instance,
            instance_snapshot=camel_dict_to_snake_dict(snapshot),
        )

    try:
        snapshot = client.create_instance_snapshot(
            instanceSnapshotName=module.params.get("snapshot_name"),
            instanceName=module.params.get("instance_name"),
        )
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)

    if module.params.get("wait"):
        snapshot = wait_for_instance_snapshot(module, client, module.params.get("snapshot_name"))

    module.exit_json(
        changed=new_instance,
        instance_snapshot=camel_dict_to_snake_dict(snapshot),
    )


def delete_snapshot(module, client):
    snapshot = find_instance_snapshot_info(module, client, module.params.get("snapshot_name"))
    if module.check_mode or snapshot is None:
        changed = not (snapshot is None)
        instance = snapshot if changed else {}
        module.exit_json(changed=changed, instance=instance)

    try:
        client.delete_instance_snapshot(instanceSnapshotName=module.params.get("snapshot_name"))
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)

    module.exit_json(changed=True, instance=camel_dict_to_snake_dict(snapshot))


def main():
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        snapshot_name=dict(type="str", required=True),
        instance_name=dict(type="str"),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(default=300, type="int"),
    )
    required_if = [
        ["state", "present", ("instance_name",)],
    ]

    module = AnsibleAWSModule(argument_spec=argument_spec, required_if=required_if, supports_check_mode=True)
    client = module.client("lightsail")

    state = module.params.get("state")

    if state == "present":
        create_snapshot(module, client)
    elif state == "absent":
        delete_snapshot(module, client)


if __name__ == "__main__":
    main()
