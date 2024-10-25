#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_vol
version_added: 1.0.0
short_description: Create and attach a volume, return volume ID and device map
description:
  - Creates an EBS volume and optionally attaches it to an instance.
  - If both O(instance) and O(name) are given and the instance has a device at the device name, then no volume is created and no attachment is made.
options:
  instance:
    description:
      - Instance ID if you wish to attach the volume.
      - Set to V(None) to detach the volume.
    type: str
  name:
    description:
      - Volume Name tag if you wish to attach an existing volume (requires instance).
    type: str
  id:
    description:
      - Volume ID if you wish to attach an existing volume (requires instance) or remove an existing volume.
    type: str
  volume_size:
    description:
      - Size of volume (in GiB) to create.
    type: int
  volume_type:
    description:
      - Type of EBS volume; V(standard) (magnetic), V(gp2) (SSD), V(gp3) (SSD), V(io1) (Provisioned IOPS), V(io2) (Provisioned IOPS),
        V(st1) (Throughput Optimized HDD), V(sc1) (Cold HDD).
      - V(standard) is the old EBS default and continues to remain the Ansible default for backwards compatibility.
    default: standard
    choices: ['standard', 'gp2', 'io1', 'st1', 'sc1', 'gp3', 'io2']
    type: str
  iops:
    description:
      - The provisioned IOPs you want to associate with this volume (integer).
    type: int
  encrypted:
    description:
      - Enable encryption at rest for this volume.
    default: false
    type: bool
  kms_key_id:
    description:
      - Specify the ID of the KMS key to use.
    type: str
  device_name:
    description:
      - Device ID to override device mapping. Assumes /dev/sdf for Linux/UNIX and /dev/xvdf for Windows.
    type: str
  delete_on_termination:
    description:
      - When set to C(true), the volume will be deleted upon instance termination.
    type: bool
    default: false
  zone:
    description:
      - Zone in which to create the volume, if unset uses the zone the instance is in (if set).
    aliases: ['availability_zone', 'aws_zone', 'ec2_zone']
    type: str
  snapshot:
    description:
      - Snapshot ID on which to base the volume.
    type: str
  state:
    description:
      - Whether to ensure the volume is present or absent.
      - O(state=list) was deprecated in release 1.1.0 and is no longer available
        with release 4.0.0.
      - The V(list) functionality has been moved to a dedicated module M(amazon.aws.ec2_vol_info).
    default: present
    choices: ['absent', 'present']
    type: str
  modify_volume:
    description:
      - The volume won't be modified unless this key is V(true).
    type: bool
    default: false
    version_added: 1.4.0
  throughput:
    description:
      - Volume throughput in MB/s.
      - This parameter is only valid for gp3 volumes.
      - Valid range is from 125 to 1000.
    type: int
    version_added: 1.4.0
  multi_attach:
    description:
      - If set to V(true), Multi-Attach will be enabled when creating the volume.
      - When you create a new volume, Multi-Attach is disabled by default.
      - This parameter is supported with io1 and io2 volumes only.
    type: bool
    version_added: 2.0.0
  outpost_arn:
    description:
      - The Amazon Resource Name (ARN) of the Outpost.
      - If set, allows to create volume in an Outpost.
    type: str
    version_added: 3.1.0
author:
  - "Lester Wade (@lwade)"
notes:
  - Support for O(purge_tags) was added in release 1.5.0.
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Simple attachment action
- amazon.aws.ec2_vol:
    instance: XXXXXX
    volume_size: 5
    device_name: sdd
    region: us-west-2

# Example using custom iops params
- amazon.aws.ec2_vol:
    instance: XXXXXX
    volume_size: 5
    iops: 100
    device_name: sdd
    region: us-west-2

# Example using snapshot id
- amazon.aws.ec2_vol:
    instance: XXXXXX
    snapshot: "{{ snapshot }}"

# Playbook example combined with instance launch
- amazon.aws.ec2:
    keypair: "{{ keypair }}"
    image: "{{ image }}"
    wait: true
    count: 3
  register: ec2
- amazon.aws.ec2_vol:
    instance: "{{ item.id }}"
    volume_size: 5
  loop: "{{ ec2.instances }}"
  register: ec2_vol

# Example: Launch an instance and then add a volume if not already attached
#   * Volume will be created with the given name if not already created.
#   * Nothing will happen if the volume is already attached.

- amazon.aws.ec2:
    keypair: "{{ keypair }}"
    image: "{{ image }}"
    zone: YYYYYY
    id: my_instance
    wait: true
    count: 1
  register: ec2

- amazon.aws.ec2_vol:
    instance: "{{ item.id }}"
    name: my_existing_volume_Name_tag
    device_name: /dev/xvdf
  loop: "{{ ec2.instances }}"
  register: ec2_vol

# Remove a volume
- amazon.aws.ec2_vol:
    id: vol-XXXXXXXX
    state: absent

# Detach a volume (since 1.9)
- amazon.aws.ec2_vol:
    id: vol-XXXXXXXX
    instance: None
    region: us-west-2

# Create new volume using SSD storage
- amazon.aws.ec2_vol:
    instance: XXXXXX
    volume_size: 50
    volume_type: gp2
    device_name: /dev/xvdf

# Create new volume with multi-attach enabled
- amazon.aws.ec2_vol:
    zone: XXXXXX
    multi_attach: true
    volume_size: 4
    volume_type: io1
    iops: 102

# Attach an existing volume to instance. The volume will be deleted upon instance termination.
- amazon.aws.ec2_vol:
    instance: XXXXXX
    id: XXXXXX
    device_name: /dev/sdf
    delete_on_termination: true
"""

RETURN = r"""
device:
    description: Device name of attached volume.
    returned: when success
    type: str
    sample: "/dev/sdf"
volume_id:
    description: The id of volume.
    returned: when success
    type: str
    sample: "vol-35b333d9"
volume_type:
    description: The volume type.
    returned: when success
    type: str
    sample: "standard"
volume:
    description: A dictionary containing detailed attributes of the volume.
    returned: when success
    type: dict
    contains:
        attachment_set:
            description:
                - Information about the volume attachments.
                - This was changed in version 2.0.0 from a dictionary to a list of dictionaries.
            type: list
            elements: dict
            returned: when success
            sample: [{
                "attach_time": "2015-10-23T00:22:29.000Z",
                "deleteOnTermination": "false",
                "device": "/dev/sdf",
                "instance_id": "i-8356263c",
                "status": "attached"
            }]
        create_time:
            description: The time stamp when volume creation was initiated.
            type: str
            returned: when success
            sample: "2015-10-21T14:36:08.870Z"
        encrypted:
            description: Indicates whether the volume is encrypted.
            type: bool
            returned: when success
            sample: False
        id:
            description: The ID of the volume.
            type: str
            returned: when success
            sample: "vol-35b333d9"
        iops:
            description: The number of I/O operations per second (IOPS) that the volume supports.
            type: int
            returned: when success
            sample: null
        size:
            description: The size of the volume, in GiBs.
            type: int
            returned: when success
            sample: 1
        snapshot_id:
            description: The snapshot from which the volume was created, if applicable.
            type: str
            returned: when success
            sample: ""
        status:
            description: The volume state.
            type: str
            returned: when success
            sample: "in-use"
        tags:
            description: Any tags assigned to the volume.
            type: dict
            returned: when success
            sample: {
                env: "dev"
                }
        type:
            description: The volume type. This can be gp2, io1, st1, sc1, or standard.
            type: str
            returned: when success
            sample: "standard"
        zone:
            description: The Availability Zone of the volume.
            type: str
            returned: when success
            sample: "us-east-1b"
        throughput:
            description: The throughput that the volume supports, in MiB/s.
            type: int
            returned: when success
            sample: 131
"""

import time
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.arn import is_outpost_arn
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import attach_volume as attach_ec2_volume
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import create_volume as create_ec2_volume
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import delete_volume as delete_ec2_volume
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_instances
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_volumes
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import detach_volume as detach_ec2_volume
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import modify_instance_attribute
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import modify_volume
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.waiters import wait_for_resource_state


def get_instance(module: AnsibleAWSModule, ec2_conn, instance_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    instance = None
    if not instance_id:
        return instance

    try:
        reservation_response = describe_instances(ec2_conn, InstanceIds=[instance_id])
        if reservation_response:
            instance = camel_dict_to_snake_dict(reservation_response[0]["Instances"][0])
    except AnsibleEC2Error as e:
        module.fail_json_aws(e, msg=f"Error while getting instance_id with id {instance_id}")

    return instance


def get_volume(module, ec2_conn, vol_id=None, fail_on_not_found=True):
    name = module.params.get("name")
    param_id = module.params.get("id")
    zone = module.params.get("zone")

    if not vol_id:
        vol_id = param_id

    # If no name or id supplied, just try volume creation based on module parameters
    if vol_id is None and name is None:
        return None

    find_params = dict()
    vols = []

    if vol_id:
        find_params["VolumeIds"] = [vol_id]
    elif name:
        find_params["Filters"] = ansible_dict_to_boto3_filter_list({"tag:Name": name})
    elif zone:
        find_params["Filters"] = ansible_dict_to_boto3_filter_list({"availability-zone": zone})

    try:
        vols = describe_volumes(ec2_conn, **find_params)
        if not vols:
            if fail_on_not_found and vol_id:
                msg = f"Could not find volume with id: {vol_id}"
                if name:
                    msg += f" and name: {name}"
                module.fail_json(msg=msg)
            else:
                return None
    except AnsibleEC2Error as e:
        module.fail_json_aws(e, msg=f"Error while getting EBS volumes with the parameters {find_params}")

    if len(vols) > 1:
        module.fail_json(
            msg=f"Found more than one volume in zone (if specified) with name: {name}",
            found=[v["VolumeId"] for v in vols],
        )
    vol = camel_dict_to_snake_dict(vols[0])
    return vol


def delete_volume(module: AnsibleAWSModule, ec2_conn, volume_id: Optional[str] = None) -> bool:
    changed = False
    if volume_id:
        try:
            changed = delete_ec2_volume(ec2_conn, volume_id)
        except AnsibleEC2Error as e:
            module.fail_json_aws(e, msg="Error while deleting volume")
        wait_for_resource_state(ec2_conn, module, "volume_deleted", VolumeIds=[volume_id])
    return changed


def update_volume(module: AnsibleAWSModule, ec2_conn, volume: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    changed = False
    req_obj = {"VolumeId": volume["volume_id"]}

    if module.params.get("modify_volume"):
        target_type = module.params.get("volume_type")
        original_type = None
        type_changed = False
        if target_type:
            original_type = volume["volume_type"]
            if target_type != original_type:
                type_changed = True
                req_obj["VolumeType"] = target_type

        iops_changed = False
        target_iops = module.params.get("iops")
        original_iops = volume.get("iops")
        if target_iops:
            if target_iops != original_iops:
                iops_changed = True
                req_obj["Iops"] = target_iops
            else:
                req_obj["Iops"] = original_iops
        else:
            # If no IOPS value is specified and there was a volume_type update to gp3,
            # the existing value is retained, unless a volume type is modified that supports different values,
            # otherwise, the default iops value is applied.
            if type_changed and target_type == "gp3":
                if (original_iops and (int(original_iops) < 3000 or int(original_iops) > 16000)) or not original_iops:
                    req_obj["Iops"] = 3000
                    iops_changed = True

        target_size = module.params.get("volume_size")
        size_changed = False
        if target_size:
            original_size = volume["size"]
            if target_size != original_size:
                size_changed = True
                req_obj["Size"] = target_size

        target_type = module.params.get("volume_type")
        original_type = None
        type_changed = False
        if target_type:
            original_type = volume["volume_type"]
            if target_type != original_type:
                type_changed = True
                req_obj["VolumeType"] = target_type

        target_throughput = module.params.get("throughput")
        throughput_changed = False
        if target_throughput:
            original_throughput = volume.get("throughput")
            if target_throughput != original_throughput:
                throughput_changed = True
                req_obj["Throughput"] = target_throughput

        target_multi_attach = module.params.get("multi_attach")
        multi_attach_changed = False
        if target_multi_attach is not None:
            original_multi_attach = volume["multi_attach_enabled"]
            if target_multi_attach != original_multi_attach:
                multi_attach_changed = True
                req_obj["MultiAttachEnabled"] = target_multi_attach

        changed = iops_changed or size_changed or type_changed or throughput_changed or multi_attach_changed

        if changed:
            if module.check_mode:
                module.exit_json(changed=True, msg="Would have updated volume if not in check mode.")
            try:
                response = modify_volume(ec2_conn, **req_obj)
            except AnsibleEC2Error as e:
                module.fail_json_aws(e, msg="Error while modifying volume")

            volume["size"] = response.get("TargetSize")
            volume["volume_type"] = response.get("TargetVolumeType")
            volume["iops"] = response.get("TargetIops")
            volume["multi_attach_enabled"] = response.get("TargetMultiAttachEnabled")
            volume["throughput"] = response.get("TargetThroughput")

    return volume, changed


def create_volume(module: AnsibleAWSModule, ec2_conn, zone: str) -> Tuple[Dict[str, Any], bool]:
    changed = False
    iops = module.params.get("iops")
    encrypted = module.params.get("encrypted")
    kms_key_id = module.params.get("kms_key_id")
    volume_size = module.params.get("volume_size")
    volume_type = module.params.get("volume_type")
    snapshot = module.params.get("snapshot")
    throughput = module.params.get("throughput")
    multi_attach = module.params.get("multi_attach")
    outpost_arn = module.params.get("outpost_arn")
    tags = module.params.get("tags") or {}
    name = module.params.get("name")

    volume = get_volume(module, ec2_conn)

    if module.check_mode:
        module.exit_json(changed=True, msg="Would have created a volume if not in check mode.")

    if volume is None:
        changed = True
        additional_params = dict()

        if volume_size:
            additional_params["Size"] = int(volume_size)

        if kms_key_id:
            additional_params["KmsKeyId"] = kms_key_id

        if snapshot:
            additional_params["SnapshotId"] = snapshot

        if iops:
            additional_params["Iops"] = int(iops)

        # Use the default value if any iops has been specified when volume_type=gp3
        if volume_type == "gp3" and not iops:
            additional_params["Iops"] = 3000

        if throughput:
            additional_params["Throughput"] = int(throughput)

        if multi_attach:
            additional_params["MultiAttachEnabled"] = True

        if outpost_arn:
            if is_outpost_arn(outpost_arn):
                additional_params["OutpostArn"] = outpost_arn
            else:
                module.fail_json("OutpostArn does not match the pattern specified in API specifications.")

        if name:
            tags["Name"] = name

        if tags:
            additional_params["TagSpecifications"] = boto3_tag_specifications(tags, types=["volume"])

        try:
            create_vol_response = create_ec2_volume(
                ec2_conn, AvailabilityZone=zone, Encrypted=encrypted, VolumeType=volume_type, **additional_params
            )
        except AnsibleEC2Error as e:
            module.fail_json_aws(e, msg="Error while creating EBS volume")

        wait_for_resource_state(ec2_conn, module, "volume_available", VolumeIds=[create_vol_response["VolumeId"]])
        volume = get_volume(module, ec2_conn, vol_id=create_vol_response["VolumeId"])

    return volume, changed


def attach_volume(
    module: AnsibleAWSModule, ec2_conn, volume_dict: Dict[str, Any], instance_dict: Dict[str, Any], device_name: str
) -> Tuple[Dict[str, Any], bool]:
    changed = False

    # If device_name isn't set, make a choice based on best practices here:
    # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/block-device-mapping-concepts.html

    # In future this needs to be more dynamic but combining block device mapping best practices
    # (bounds for devices, as above) with instance.block_device_mapping data would be tricky. For me ;)

    attachment_data = get_attachment_data(volume_dict, wanted_state="attached")
    if attachment_data:
        if module.check_mode:
            if attachment_data[0].get("status") in ["attached", "attaching"]:
                instance_id = attachment_data[0].get("instance_id", "None")
                module.exit_json(
                    changed=False,
                    msg=f"IN CHECK MODE - volume already attached to instance: {instance_id}.",
                    volume=volume_dict,
                )
        if not volume_dict["multi_attach_enabled"]:
            # volumes without MultiAttach Enabled can be attached to 1 instance only
            if attachment_data[0].get("instance_id", None) != instance_dict["instance_id"]:
                instance_id = attachment_data[0].get("instance_id", "None")
                module.fail_json(
                    msg=f"Volume {volume_dict['volume_id']} is already attached to another instance: {instance_id}."
                )
            else:
                return volume_dict, changed

    try:
        if module.check_mode:
            module.exit_json(changed=True, msg="Would have attached volume if not in check mode.")
        attach_response = attach_ec2_volume(
            ec2_conn, device=device_name, instance_id=instance_dict["instance_id"], volume_id=volume_dict["volume_id"]
        )
    except AnsibleEC2Error as e:
        module.fail_json_aws(e, msg="Error while attaching EBS volume")

    wait_for_resource_state(ec2_conn, module, "volume_in_use", VolumeIds=[attach_response["VolumeId"]])
    changed = True

    modify_dot_attribute(module, ec2_conn, instance_dict, device_name)

    volume = get_volume(module, ec2_conn, vol_id=volume_dict["volume_id"])

    return volume, changed


def modify_dot_attribute(module: AnsibleAWSModule, ec2_conn, instance_dict: Dict[str, Any], device_name: str) -> bool:
    """Modify delete_on_termination attribute"""

    delete_on_termination = module.params.get("delete_on_termination")
    changed = False

    # volume_in_use can return *shortly* before it appears on the instance
    # description
    mapped_block_device = None
    _attempt = 0
    while mapped_block_device is None:
        _attempt += 1
        instance_dict = get_instance(module, ec2_conn=ec2_conn, instance_id=instance_dict["instance_id"])
        mapped_block_device = get_mapped_block_device(instance_dict=instance_dict, device_name=device_name)
        if mapped_block_device is None:
            if _attempt > 2:
                module.fail_json(msg="Unable to find device on instance", device=device_name, instance=instance_dict)
            time.sleep(1)

    if delete_on_termination != mapped_block_device["ebs"].get("delete_on_termination"):
        try:
            modify_instance_attribute(
                ec2_conn,
                instance_id=instance_dict["instance_id"],
                BlockDeviceMappings=[
                    {"DeviceName": device_name, "Ebs": {"DeleteOnTermination": delete_on_termination}}
                ],
            )
            changed = True
        except AnsibleEC2Error as e:
            module.fail_json_aws(
                e, msg=f"Error while modifying Block Device Mapping of instance {instance_dict['instance_id']}"
            )

    return changed


def get_attachment_data(volume_dict: Dict[str, Any], wanted_state: Optional[str] = None) -> List[Dict[str, Any]]:
    attachment_data = []
    if not volume_dict:
        return attachment_data
    resource = volume_dict.get("attachments", [])
    if wanted_state:
        # filter 'state', return attachment matching wanted state
        resource = [data for data in resource if data["state"] == wanted_state]

    for data in resource:
        attachment_data.append(
            {
                "attach_time": data.get("attach_time", None),
                "device": data.get("device", None),
                "instance_id": data.get("instance_id", None),
                "status": data.get("state", None),
                "delete_on_termination": data.get("delete_on_termination", None),
            }
        )

    return attachment_data


def detach_volume(module: AnsibleAWSModule, ec2_conn, volume_dict: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    changed = False

    attachment_data = get_attachment_data(volume_dict, wanted_state="attached")
    # The ID of the instance must be specified if you are detaching a Multi-Attach enabled volume.
    for attachment in attachment_data:
        if module.check_mode:
            module.exit_json(changed=True, msg="Would have detached volume if not in check mode.")
        try:
            detach_ec2_volume(ec2_conn, volume_id=volume_dict["volume_id"], InstanceId=attachment["instance_id"])
        except AnsibleEC2Error as e:
            module.fail_json_aws(e, msg="Error while detaching volume")

        wait_for_resource_state(ec2_conn, module, "volume_available", VolumeIds=[volume_dict["volume_id"]])
        changed = True

    volume_dict = get_volume(module, ec2_conn, vol_id=volume_dict["volume_id"])
    return volume_dict, changed


def get_volume_info(volume: Dict[str, Any], tags: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    if not tags:
        tags = boto3_tag_list_to_ansible_dict(volume.get("tags"))
    attachment_data = get_attachment_data(volume)
    volume_info = {
        "create_time": volume.get("create_time"),
        "encrypted": volume.get("encrypted"),
        "id": volume.get("volume_id"),
        "iops": volume.get("iops"),
        "size": volume.get("size"),
        "snapshot_id": volume.get("snapshot_id"),
        "status": volume.get("state"),
        "type": volume.get("volume_type"),
        "zone": volume.get("availability_zone"),
        "attachment_set": attachment_data,
        "multi_attach_enabled": volume.get("multi_attach_enabled"),
        "tags": tags,
    }

    volume_info["throughput"] = volume.get("throughput")

    return volume_info


def get_mapped_block_device(
    instance_dict: Optional[Dict[str, Any]] = None, device_name: Optional[str] = None
) -> Optional[str]:
    mapped_block_device = None
    if not instance_dict:
        return mapped_block_device
    if not device_name:
        return mapped_block_device

    for device in instance_dict.get("block_device_mappings", []):
        if device["device_name"] == device_name:
            mapped_block_device = device
            break

    return mapped_block_device


def ensure_tags(
    module: AnsibleAWSModule, connection, res_id: str, res_type: str, tags: Dict[str, Any], purge_tags: bool
) -> Tuple[Dict[str, Any], bool]:
    if module.check_mode:
        return {}, True
    changed = ensure_ec2_tags(connection, module, res_id, res_type, tags, purge_tags, ["InvalidVolume.NotFound"])
    final_tags = describe_ec2_tags(connection, module, res_id, res_type)

    return final_tags, changed


def ensure_present(ec2_conn, module: AnsibleAWSModule, volume: Optional[Dict[str, Any]]) -> None:
    instance = module.params.get("instance")
    name = module.params.get("name")
    zone = module.params.get("zone")
    device_name = module.params.get("device_name")
    tags = module.params.get("tags")

    # Ensure we have the zone or can get the zone
    if instance is None and zone is None:
        module.fail_json(msg="You must specify either instance or zone")

    # Set volume detach flag
    if instance == "None" or instance == "":
        instance = None
        detach_vol_flag = True
    else:
        detach_vol_flag = False

    # Here we need to get the zone info for the instance. This covers situation where
    # instance is specified but zone isn't.
    # Useful for playbooks chaining instance launch with volume create + attach and where the
    # zone doesn't matter to the user.
    inst = None
    if instance:
        inst = get_instance(module, ec2_conn, instance_id=instance)
        zone = inst["placement"]["availability_zone"]

        # Use platform attribute to guess whether the instance is Windows or Linux
        if device_name is None:
            if inst.get("platform", "") == "Windows":
                device_name = "/dev/xvdf"
            else:
                device_name = "/dev/sdf"

        # Check if there is a volume already mounted there.
        mapped_device = get_mapped_block_device(instance_dict=inst, device_name=device_name)
        if mapped_device:
            other_volume_mapped = False
            if volume:
                if volume["volume_id"] != mapped_device["ebs"]["volume_id"]:
                    other_volume_mapped = True
            else:
                # No volume found so this is another volume
                other_volume_mapped = True

            if other_volume_mapped:
                module.exit_json(
                    msg=f"Volume mapping for {device_name} already exists on instance {instance}",
                    volume_id=mapped_device["ebs"]["volume_id"],
                    found_volume=volume,
                    device=device_name,
                    changed=False,
                )
    final_tags = None
    tags_changed = False
    if volume:
        volume, changed = update_volume(module, ec2_conn, volume)
        if name:
            if not tags:
                tags = boto3_tag_list_to_ansible_dict(volume.get("tags"))
            tags["Name"] = name
        final_tags, tags_changed = ensure_tags(
            module, ec2_conn, volume["volume_id"], "volume", tags, module.params.get("purge_tags")
        )
    else:
        volume, changed = create_volume(module, ec2_conn, zone=zone)

    if detach_vol_flag:
        volume, attach_changed = detach_volume(module, ec2_conn, volume_dict=volume)
    elif inst is not None:
        volume, attach_changed = attach_volume(
            module, ec2_conn, volume_dict=volume, instance_dict=inst, device_name=device_name
        )
    else:
        attach_changed = False

    # Add device, volume_id and volume_type parameters separately to maintain backward compatibility
    volume_info = get_volume_info(volume, tags=final_tags)

    if tags_changed or attach_changed:
        changed = True

    module.exit_json(
        changed=changed,
        volume=volume_info,
        device=device_name,
        volume_id=volume_info["id"],
        volume_type=volume_info["type"],
    )


def ensure_absent(ec2_conn, module: AnsibleAWSModule, volume: Optional[Dict[str, Any]]) -> None:
    name = module.params.get("name")
    param_id = module.params.get("id")
    changed = False
    if not name and not param_id:
        module.fail_json("A volume name or id is required for deletion")
    if volume and volume.get("state") not in ("deleting", "deleted"):
        if module.check_mode:
            module.exit_json(changed=True, msg="Would have deleted volume if not in check mode.")
        detach_volume(module, ec2_conn, volume_dict=volume)
        changed = delete_volume(module, ec2_conn, volume_id=volume["volume_id"])
    module.exit_json(changed=changed)


def main():
    argument_spec = dict(
        instance=dict(),
        id=dict(),
        name=dict(),
        volume_size=dict(type="int"),
        volume_type=dict(default="standard", choices=["standard", "gp2", "io1", "st1", "sc1", "gp3", "io2"]),
        iops=dict(type="int"),
        encrypted=dict(default=False, type="bool"),
        kms_key_id=dict(),
        device_name=dict(),
        delete_on_termination=dict(default=False, type="bool"),
        zone=dict(aliases=["availability_zone", "aws_zone", "ec2_zone"]),
        snapshot=dict(),
        state=dict(default="present", choices=["absent", "present"]),
        tags=dict(type="dict", aliases=["resource_tags"]),
        modify_volume=dict(default=False, type="bool"),
        throughput=dict(type="int"),
        outpost_arn=dict(type="str"),
        purge_tags=dict(type="bool", default=True),
        multi_attach=dict(type="bool"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[
            ["volume_type", "io1", ["iops"]],
            ["volume_type", "io2", ["iops"]],
        ],
        supports_check_mode=True,
    )

    param_id = module.params.get("id")
    name = module.params.get("name")
    volume_size = module.params.get("volume_size")
    snapshot = module.params.get("snapshot")
    state = module.params.get("state")
    iops = module.params.get("iops")
    volume_type = module.params.get("volume_type")
    throughput = module.params.get("throughput")
    multi_attach = module.params.get("multi_attach")

    if iops:
        if volume_type in ("gp2", "st1", "sc1", "standard"):
            module.fail_json(msg="IOPS is not supported for gp2, st1, sc1, or standard volumes.")

        if volume_type == "gp3" and (int(iops) < 3000 or int(iops) > 16000):
            module.fail_json(msg="For a gp3 volume type, IOPS values must be between 3000 and 16000.")

        if volume_type in ("io1", "io2") and (int(iops) < 100 or int(iops) > 64000):
            module.fail_json(msg="For io1 and io2 volume types, IOPS values must be between 100 and 64000.")

    if throughput:
        if volume_type != "gp3":
            module.fail_json(msg="Throughput is only supported for gp3 volume.")
        if throughput < 125 or throughput > 1000:
            module.fail_json(msg="Throughput values must be between 125 and 1000.")

    if multi_attach is True and volume_type not in ("io1", "io2"):
        module.fail_json(msg="multi_attach is only supported for io1 and io2 volumes.")

    ec2_conn = module.client("ec2")

    # Delaying the checks until after the instance check allows us to get volume ids for existing volumes
    # without needing to pass an unused volume_size
    if not volume_size and not (param_id or name or snapshot):
        module.fail_json(msg="You must specify volume_size or identify an existing volume by id, name, or snapshot")

    # Try getting volume
    volume = get_volume(module, ec2_conn, fail_on_not_found=False)
    if state == "present":
        ensure_present(ec2_conn, module, volume)
    elif state == "absent":
        ensure_absent(ec2_conn, module, volume)


if __name__ == "__main__":
    main()
