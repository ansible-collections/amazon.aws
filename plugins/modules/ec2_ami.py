#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_ami
version_added: 1.0.0
short_description: Create or destroy an image (AMI) in EC2
description:
   - Registers or deregisters EC2 images.
options:
  instance_id:
    description:
      - Instance ID to create the AMI from.
    type: str
  name:
    description:
      - The name of the new AMI.
    type: str
  architecture:
    description:
      - The target architecture of the image to register.
    default: "x86_64"
    type: str
  kernel_id:
    description:
      - The target kernel id of the image to register.
    type: str
  virtualization_type:
    description:
      - The virtualization type of the image to register.
    default: "hvm"
    type: str
  root_device_name:
    description:
      - The root device name of the image to register.
    type: str
  wait:
    description:
      - Wait for the AMI to be in state 'available' before returning.
    default: false
    type: bool
  wait_timeout:
    description:
      - How long before wait gives up, in seconds.
    default: 1200
    type: int
  state:
    description:
      - Register or deregister an AMI.
    default: 'present'
    choices: [ "absent", "present" ]
    type: str
  description:
    description:
      - Human-readable string describing the contents and purpose of the AMI.
    type: str
    default: ''
  no_reboot:
    description:
      - Flag indicating that the bundling process should not attempt to shutdown the instance before bundling. If this flag is True, the
        responsibility of maintaining file system integrity is left to the owner of the instance.
    default: false
    type: bool
  image_id:
    description:
      - Image ID to be deregistered.
    type: str
  device_mapping:
    description:
      - List of device hashes/dictionaries with custom configurations (same block-device-mapping parameters).
    type: list
    elements: dict
    suboptions:
      device_name:
        type: str
        description:
          - The device name. For example C(/dev/sda).
        required: true
      virtual_name:
        type: str
        description:
          - The virtual name for the device.
          - See the AWS documentation for more detail U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_BlockDeviceMapping.html).
      no_device:
        type: bool
        description:
          - Suppresses the specified device included in the block device mapping of the AMI.
      volume_type:
        type: str
        description: The volume type.  Defaults to C(gp2) when not set.
      delete_on_termination:
        type: bool
        description: Whether the device should be automatically deleted when the Instance is terminated.
      snapshot_id:
        type: str
        description: The ID of the Snapshot.
      iops:
        type: int
        description: When using an C(io1) I(volume_type) this sets the number of IOPS provisioned for the volume.
      encrypted:
        type: bool
        description: Whether the volume should be encrypted.
      volume_size:
        aliases: ['size']
        type: int
        description: The size of the volume (in GiB).
  delete_snapshot:
    description:
      - Delete snapshots when deregistering the AMI.
    default: false
    type: bool
  launch_permissions:
    description:
      - Users and groups that should be able to launch the AMI.
      - Expects dictionary with a key of C(user_ids) and/or C(group_names).
      - C(user_ids) should be a list of account IDs.
      - C(group_name) should be a list of groups, C(all) is the only acceptable value currently.
      - You must pass all desired launch permissions if you wish to modify existing launch permissions (passing just groups will remove all users).
    type: dict
  image_location:
    description:
      - The S3 location of an image to use for the AMI.
    type: str
  enhanced_networking:
    description:
      - A boolean representing whether enhanced networking with ENA is enabled or not.
    type: bool
  billing_products:
    description:
      - A list of valid billing codes. To be used with valid accounts by AWS Marketplace vendors.
    type: list
    elements: str
  ramdisk_id:
    description:
      - The ID of the RAM disk.
    type: str
  sriov_net_support:
    description:
      - Set to simple to enable enhanced networking with the Intel 82599 Virtual Function interface for the AMI and any instances that you launch from the AMI.
    type: str
  boot_mode:
    description:
      - The boot mode of the AMI.
      - See the AWS documentation for more detail U(https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ami-boot.html).
    type: str
    choices: ['legacy-bios', 'uefi']
    version_added: 5.5.0
  tpm_support:
    description:
      - Set to v2.0 to enable Trusted Platform Module (TPM) support.
      - If the image is configured for NitroTPM support, the value is v2.0 .
      - Requires I(boot_mode) to be set to 'uefi'.
      - Requires an instance type that is compatible with Nitro.
      - Requires minimum botocore version 1.26.0.
      - See the AWS documentation for more detail U(https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/nitrotpm.html).
    type: str
    version_added: 5.5.0
  uefi_data:
    description:
      - Base64 representation of the non-volatile UEFI variable store.
      - Requires minimum botocore version 1.26.0.
      - See the AWS documentation for more detail U(https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/uefi-secure-boot.html).
    type: str
    version_added: 5.5.0
author:
  - "Evan Duffield (@scicoin-project) <eduffield@iacquire.com>"
  - "Constantin Bugneac (@Constantin07) <constantin.bugneac@endava.com>"
  - "Ross Williams (@gunzy83) <gunzy83au@gmail.com>"
  - "Willem van Ketwich (@wilvk) <willvk@gmail.com>"
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

# Thank you to iAcquire for sponsoring development of this module.

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Basic AMI Creation
  amazon.aws.ec2_ami:
    instance_id: i-xxxxxx
    wait: true
    name: newtest
    tags:
      Name: newtest
      Service: TestService

- name: Basic AMI Creation, without waiting
  amazon.aws.ec2_ami:
    instance_id: i-xxxxxx
    wait: no
    name: newtest

- name: AMI Registration from EBS Snapshot
  amazon.aws.ec2_ami:
    name: newtest
    state: present
    architecture: x86_64
    virtualization_type: hvm
    root_device_name: /dev/xvda
    device_mapping:
      - device_name: /dev/xvda
        volume_size: 8
        snapshot_id: snap-xxxxxxxx
        delete_on_termination: true
        volume_type: gp2

- name: AMI Creation, with a custom root-device size and another EBS attached
  amazon.aws.ec2_ami:
    instance_id: i-xxxxxx
    name: newtest
    device_mapping:
        - device_name: /dev/sda1
          size: XXX
          delete_on_termination: true
          volume_type: gp2
        - device_name: /dev/sdb
          size: YYY
          delete_on_termination: false
          volume_type: gp2

- name: AMI Creation, excluding a volume attached at /dev/sdb
  amazon.aws.ec2_ami:
    instance_id: i-xxxxxx
    name: newtest
    device_mapping:
        - device_name: /dev/sda1
          size: XXX
          delete_on_termination: true
          volume_type: gp2
        - device_name: /dev/sdb
          no_device: true

- name: AMI Creation with boot_mode and tpm_support
  amazon.aws.ec2_ami:
    name: newtest
    state: present
    architecture: x86_64
    virtualization_type: hvm
    root_device_name: /dev/sda1
    device_mapping:
        - device_name: /dev/sda1
          snapshot_id: "{{ snapshot_id }}"
    wait: yes
    region: us-east-1
    boot_mode: uefi
    uefi_data: data_file.bin
    tpm_support: v2.0

- name: Deregister/Delete AMI (keep associated snapshots)
  amazon.aws.ec2_ami:
    image_id: "{{ instance.image_id }}"
    delete_snapshot: False
    state: absent

- name: Deregister AMI (delete associated snapshots too)
  amazon.aws.ec2_ami:
    image_id: "{{ instance.image_id }}"
    delete_snapshot: True
    state: absent

- name: Update AMI Launch Permissions, making it public
  amazon.aws.ec2_ami:
    image_id: "{{ instance.image_id }}"
    state: present
    launch_permissions:
      group_names: ['all']

- name: Allow AMI to be launched by another account
  amazon.aws.ec2_ami:
    image_id: "{{ instance.image_id }}"
    state: present
    launch_permissions:
      user_ids: ['123456789012']
"""

RETURN = r"""
architecture:
    description: Architecture of image.
    returned: when AMI is created or already exists
    type: str
    sample: "x86_64"
block_device_mapping:
    description: Block device mapping associated with image.
    returned: when AMI is created or already exists
    type: dict
    sample: {
        "/dev/sda1": {
            "delete_on_termination": true,
            "encrypted": false,
            "size": 10,
            "snapshot_id": "snap-1a03b80e7",
            "volume_type": "standard"
        }
    }
creationDate:
    description: Creation date of image.
    returned: when AMI is created or already exists
    type: str
    sample: "2015-10-15T22:43:44.000Z"
description:
    description: Description of image.
    returned: when AMI is created or already exists
    type: str
    sample: "nat-server"
hypervisor:
    description: Type of hypervisor.
    returned: when AMI is created or already exists
    type: str
    sample: "xen"
image_id:
    description: ID of the image.
    returned: when AMI is created or already exists
    type: str
    sample: "ami-1234abcd"
is_public:
    description: Whether image is public.
    returned: when AMI is created or already exists
    type: bool
    sample: false
launch_permission:
    description: Permissions allowing other accounts to access the AMI.
    returned: when AMI is created or already exists
    type: list
    sample:
      - group: "all"
location:
    description: Location of image.
    returned: when AMI is created or already exists
    type: str
    sample: "123456789012/nat-server"
name:
    description: AMI name of image.
    returned: when AMI is created or already exists
    type: str
    sample: "nat-server"
ownerId:
    description: Owner of image.
    returned: when AMI is created or already exists
    type: str
    sample: "123456789012"
platform:
    description: Platform of image.
    returned: when AMI is created or already exists
    type: str
    sample: null
root_device_name:
    description: Root device name of image.
    returned: when AMI is created or already exists
    type: str
    sample: "/dev/sda1"
root_device_type:
    description: Root device type of image.
    returned: when AMI is created or already exists
    type: str
    sample: "ebs"
state:
    description: State of image.
    returned: when AMI is created or already exists
    type: str
    sample: "available"
tags:
    description: A dictionary of tags assigned to image.
    returned: when AMI is created or already exists
    type: dict
    sample: {
        "Env": "devel",
        "Name": "nat-server"
    }
virtualization_type:
    description: Image virtualization type.
    returned: when AMI is created or already exists
    type: str
    sample: "hvm"
snapshots_deleted:
    description: A list of snapshot ids deleted after deregistering image.
    returned: after AMI is deregistered, if I(delete_snapshot=true)
    type: list
    sample: [
        "snap-fbcccb8f",
        "snap-cfe7cdb4"
    ]
"""

import time

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import add_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications
from ansible_collections.amazon.aws.plugins.module_utils.waiters import get_waiter


class Ec2AmiFailure(Exception):
    def __init__(self, message=None, original_e=None):
        super().__init__(message)
        self.original_e = original_e
        self.message = message


def get_block_device_mapping(image):
    bdm_dict = {}
    if image is not None and image.get("block_device_mappings") is not None:
        bdm = image.get("block_device_mappings")
        for device in bdm:
            device_name = device.get("device_name")
            if "ebs" in device:
                ebs = device.get("ebs")
                bdm_dict_item = {
                    "size": ebs.get("volume_size"),
                    "snapshot_id": ebs.get("snapshot_id"),
                    "volume_type": ebs.get("volume_type"),
                    "encrypted": ebs.get("encrypted"),
                    "delete_on_termination": ebs.get("delete_on_termination"),
                }
            elif "virtual_name" in device:
                bdm_dict_item = dict(virtual_name=device["virtual_name"])
            bdm_dict[device_name] = bdm_dict_item
    return bdm_dict


def get_ami_info(camel_image):
    image = camel_dict_to_snake_dict(camel_image)
    return dict(
        image_id=image.get("image_id"),
        state=image.get("state"),
        architecture=image.get("architecture"),
        block_device_mapping=get_block_device_mapping(image),
        creationDate=image.get("creation_date"),
        description=image.get("description"),
        hypervisor=image.get("hypervisor"),
        is_public=image.get("public"),
        location=image.get("image_location"),
        ownerId=image.get("owner_id"),
        root_device_name=image.get("root_device_name"),
        root_device_type=image.get("root_device_type"),
        virtualization_type=image.get("virtualization_type"),
        name=image.get("name"),
        tags=boto3_tag_list_to_ansible_dict(image.get("tags")),
        platform=image.get("platform"),
        enhanced_networking=image.get("ena_support"),
        image_owner_alias=image.get("image_owner_alias"),
        image_type=image.get("image_type"),
        kernel_id=image.get("kernel_id"),
        product_codes=image.get("product_codes"),
        ramdisk_id=image.get("ramdisk_id"),
        sriov_net_support=image.get("sriov_net_support"),
        state_reason=image.get("state_reason"),
        launch_permissions=image.get("launch_permissions"),
    )


def get_image_by_id(connection, image_id):
    try:
        images_response = connection.describe_images(aws_retry=True, ImageIds=[image_id])
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        raise Ec2AmiFailure("Error retrieving image by image_id", e)

    images = images_response.get("Images", [])
    image_counter = len(images)
    if image_counter == 0:
        return None

    if image_counter > 1:
        raise Ec2AmiFailure(f"Invalid number of instances ({str(len(images))}) found for image_id: {image_id}.")

    result = images[0]
    try:
        result["LaunchPermissions"] = connection.describe_image_attribute(
            aws_retry=True, Attribute="launchPermission", ImageId=image_id
        )["LaunchPermissions"]
        result["ProductCodes"] = connection.describe_image_attribute(
            aws_retry=True, Attribute="productCodes", ImageId=image_id
        )["ProductCodes"]
    except is_boto3_error_code("InvalidAMIID.Unavailable"):
        pass
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        raise Ec2AmiFailure(f"Error retrieving image attributes for image {image_id}", e)
    return result


def rename_item_if_exists(dict_object, attribute, new_attribute, child_node=None, attribute_type=None):
    new_item = dict_object.get(attribute)
    if new_item is not None:
        if attribute_type is not None:
            new_item = attribute_type(new_item)
        if child_node is None:
            dict_object[new_attribute] = new_item
        else:
            dict_object[child_node][new_attribute] = new_item
        dict_object.pop(attribute)
    return dict_object


def validate_params(
    module,
    image_id=None,
    instance_id=None,
    name=None,
    state=None,
    tpm_support=None,
    uefi_data=None,
    boot_mode=None,
    device_mapping=None,
    **_,
):
    # Using a required_one_of=[['name', 'image_id']] overrides the message that should be provided by
    # the required_if for state=absent, so check manually instead
    if not (image_id or name):
        module.fail_json("one of the following is required: name, image_id")

    if tpm_support or uefi_data:
        module.require_botocore_at_least(
            "1.26.0", reason="required for ec2.register_image with tpm_support or uefi_data"
        )
    if tpm_support and boot_mode != "uefi":
        module.fail_json("To specify 'tpm_support', 'boot_mode' must be 'uefi'.")

    if state == "present" and not image_id and not (instance_id or device_mapping):
        module.fail_json(
            "The parameters instance_id or device_mapping (register from EBS snapshot) are required for a new image."
        )


class DeregisterImage:
    @staticmethod
    def do_check_mode(module, connection, image_id):
        image = get_image_by_id(connection, image_id)

        if image is None:
            module.exit_json(changed=False)

        if "ImageId" in image:
            module.exit_json(changed=True, msg="Would have deregistered AMI if not in check mode.")
        else:
            module.exit_json(msg=f"Image {image_id} has already been deregistered.", changed=False)

    @staticmethod
    def defer_purge_snapshots(image):
        def purge_snapshots(connection):
            try:
                for mapping in image.get("BlockDeviceMappings") or []:
                    snapshot_id = mapping.get("Ebs", {}).get("SnapshotId")
                    if snapshot_id is None:
                        continue
                    connection.delete_snapshot(aws_retry=True, SnapshotId=snapshot_id)
                    yield snapshot_id
            except is_boto3_error_code("InvalidSnapshot.NotFound"):
                pass
            except (
                botocore.exceptions.ClientError,
                botocore.exceptions.BotoCoreError,
            ) as e:  # pylint: disable=duplicate-except
                raise Ec2AmiFailure("Failed to delete snapshot.", e)

        return purge_snapshots

    @staticmethod
    def timeout(connection, image_id, wait_timeout):
        image = get_image_by_id(connection, image_id)
        wait_till = time.time() + wait_timeout

        while wait_till > time.time() and image is not None:
            image = get_image_by_id(connection, image_id)
            time.sleep(3)

        if wait_till <= time.time():
            raise Ec2AmiFailure("Timed out waiting for image to be deregistered.")

    @classmethod
    def do(cls, module, connection, image_id):
        """Entry point to deregister an image"""
        delete_snapshot = module.params.get("delete_snapshot")
        wait = module.params.get("wait")
        wait_timeout = module.params.get("wait_timeout")
        image = get_image_by_id(connection, image_id)

        if image is None:
            module.exit_json(changed=False)

        # Get all associated snapshot ids before deregistering image otherwise this information becomes unavailable.
        purge_snapshots = cls.defer_purge_snapshots(image)

        # When trying to re-deregister an already deregistered image it doesn't raise an exception, it just returns an object without image attributes.
        if "ImageId" in image:
            try:
                connection.deregister_image(aws_retry=True, ImageId=image_id)
            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                raise Ec2AmiFailure("Error deregistering image", e)
        else:
            module.exit_json(msg=f"Image {image_id} has already been deregistered.", changed=False)

        if wait:
            cls.timeout(connection, image_id, wait_timeout)

        exit_params = {"msg": "AMI deregister operation complete.", "changed": True}

        if delete_snapshot:
            exit_params["snapshots_deleted"] = list(purge_snapshots(connection))

        module.exit_json(**exit_params)


class UpdateImage:
    @staticmethod
    def set_launch_permission(connection, image, launch_permissions, check_mode):
        if launch_permissions is None:
            return False

        current_permissions = image["LaunchPermissions"]

        current_users = set(permission["UserId"] for permission in current_permissions if "UserId" in permission)
        desired_users = set(str(user_id) for user_id in launch_permissions.get("user_ids", []))
        current_groups = set(permission["Group"] for permission in current_permissions if "Group" in permission)
        desired_groups = set(launch_permissions.get("group_names", []))

        to_add_users = desired_users - current_users
        to_remove_users = current_users - desired_users
        to_add_groups = desired_groups - current_groups
        to_remove_groups = current_groups - desired_groups

        to_add = [dict(Group=group) for group in sorted(to_add_groups)] + [
            dict(UserId=user_id) for user_id in sorted(to_add_users)
        ]
        to_remove = [dict(Group=group) for group in sorted(to_remove_groups)] + [
            dict(UserId=user_id) for user_id in sorted(to_remove_users)
        ]

        if not (to_add or to_remove):
            return False

        try:
            if not check_mode:
                connection.modify_image_attribute(
                    aws_retry=True,
                    ImageId=image["ImageId"],
                    Attribute="launchPermission",
                    LaunchPermission=dict(Add=to_add, Remove=to_remove),
                )
            changed = True
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            raise Ec2AmiFailure(f"Error updating launch permissions of image {image['ImageId']}", e)
        return changed

    @staticmethod
    def set_tags(connection, module, image_id, tags, purge_tags):
        if not tags:
            return False

        return ensure_ec2_tags(connection, module, image_id, tags=tags, purge_tags=purge_tags)

    @staticmethod
    def set_description(connection, module, image, description):
        if not description:
            return False

        if description == image["Description"]:
            return False

        try:
            if not module.check_mode:
                connection.modify_image_attribute(
                    aws_retry=True,
                    Attribute="Description",
                    ImageId=image["ImageId"],
                    Description={"Value": description},
                )
            return True
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            raise Ec2AmiFailure(f"Error setting description for image {image['ImageId']}", e)

    @classmethod
    def do(cls, module, connection, image_id):
        """Entry point to update an image"""
        launch_permissions = module.params.get("launch_permissions")
        image = get_image_by_id(connection, image_id)
        if image is None:
            raise Ec2AmiFailure(f"Image {image_id} does not exist")

        changed = False
        changed |= cls.set_launch_permission(connection, image, launch_permissions, module.check_mode)
        changed |= cls.set_tags(connection, module, image_id, module.params["tags"], module.params["purge_tags"])
        changed |= cls.set_description(connection, module, image, module.params["description"])

        if changed and module.check_mode:
            module.exit_json(changed=True, msg="Would have updated AMI if not in check mode.")
        elif changed:
            module.exit_json(msg="AMI updated.", changed=True, **get_ami_info(get_image_by_id(connection, image_id)))
        else:
            module.exit_json(msg="AMI not updated.", changed=False, **get_ami_info(image))


class CreateImage:
    @staticmethod
    def do_check_mode(module, connection, _image_id):
        image = connection.describe_images(Filters=[{"Name": "name", "Values": [str(module.params["name"])]}])
        if not image["Images"]:
            module.exit_json(changed=True, msg="Would have created a AMI if not in check mode.")
        else:
            module.exit_json(changed=False, msg="Error registering image: AMI name is already in use by another AMI")

    @staticmethod
    def wait(connection, wait_timeout, image_id):
        if not wait_timeout:
            return

        delay = 15
        max_attempts = wait_timeout // delay
        waiter = get_waiter(connection, "image_available")
        waiter.wait(ImageIds=[image_id], WaiterConfig={"Delay": delay, "MaxAttempts": max_attempts})

    @staticmethod
    def set_tags(connection, module, tags, image_id):
        if not tags:
            return

        image_info = get_image_by_id(connection, image_id)
        add_ec2_tags(connection, module, image_id, module.params["tags"])
        if image_info and image_info.get("BlockDeviceMappings"):
            for mapping in image_info.get("BlockDeviceMappings"):
                # We can only tag Ebs volumes
                if "Ebs" not in mapping:
                    continue
                add_ec2_tags(connection, module, mapping.get("Ebs").get("SnapshotId"), tags)

    @staticmethod
    def set_launch_permissions(connection, launch_permissions, image_id):
        if not launch_permissions:
            return

        try:
            params = {"Attribute": "LaunchPermission", "ImageId": image_id, "LaunchPermission": {"Add": []}}
            for group_name in launch_permissions.get("group_names", []):
                params["LaunchPermission"]["Add"].append(dict(Group=group_name))
            for user_id in launch_permissions.get("user_ids", []):
                params["LaunchPermission"]["Add"].append(dict(UserId=str(user_id)))
            if params["LaunchPermission"]["Add"]:
                connection.modify_image_attribute(aws_retry=True, **params)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            raise Ec2AmiFailure(f"Error setting launch permissions for image {image_id}", e)

    @staticmethod
    def create_or_register(connection, create_image_parameters):
        create_from_instance = "InstanceId" in create_image_parameters
        func = connection.create_image if create_from_instance else connection.register_image
        return func

    @staticmethod
    def build_block_device_mapping(device_mapping):
        # Remove empty values injected by using options
        block_device_mapping = []
        for device in device_mapping:
            device = {k: v for k, v in device.items() if v is not None}
            device["Ebs"] = {}
            rename_item_if_exists(device, "delete_on_termination", "DeleteOnTermination", "Ebs")
            rename_item_if_exists(device, "device_name", "DeviceName")
            rename_item_if_exists(device, "encrypted", "Encrypted", "Ebs")
            rename_item_if_exists(device, "iops", "Iops", "Ebs")
            rename_item_if_exists(device, "no_device", "NoDevice")
            rename_item_if_exists(device, "size", "VolumeSize", "Ebs", attribute_type=int)
            rename_item_if_exists(device, "snapshot_id", "SnapshotId", "Ebs")
            rename_item_if_exists(device, "virtual_name", "VirtualName")
            rename_item_if_exists(device, "volume_size", "VolumeSize", "Ebs", attribute_type=int)
            rename_item_if_exists(device, "volume_type", "VolumeType", "Ebs")

            # The NoDevice parameter in Boto3 is a string. Empty string omits the device from block device mapping
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.create_image
            if "NoDevice" in device:
                if device["NoDevice"] is True:
                    device["NoDevice"] = ""
                else:
                    del device["NoDevice"]
            block_device_mapping.append(device)
        return block_device_mapping

    @staticmethod
    def build_create_image_parameters(**kwargs):
        architecture = kwargs.get("architecture")
        billing_products = kwargs.get("billing_products")
        boot_mode = kwargs.get("boot_mode")
        description = kwargs.get("description")
        device_mapping = kwargs.get("device_mapping") or []
        enhanced_networking = kwargs.get("enhanced_networking")
        image_location = kwargs.get("image_location")
        instance_id = kwargs.get("instance_id")
        kernel_id = kwargs.get("kernel_id")
        name = kwargs.get("name")
        no_reboot = kwargs.get("no_reboot")
        ramdisk_id = kwargs.get("ramdisk_id")
        root_device_name = kwargs.get("root_device_name")
        sriov_net_support = kwargs.get("sriov_net_support")
        tags = kwargs.get("tags")
        tpm_support = kwargs.get("tpm_support")
        uefi_data = kwargs.get("uefi_data")
        virtualization_type = kwargs.get("virtualization_type")

        params = {
            "Name": name,
            "Description": description,
            "BlockDeviceMappings": CreateImage.build_block_device_mapping(device_mapping),
        }

        # Remove empty values injected by using options
        if instance_id:
            params.update(
                {
                    "InstanceId": instance_id,
                    "NoReboot": no_reboot,
                    "TagSpecifications": boto3_tag_specifications(tags, types=["image", "snapshot"]),
                }
            )
        else:
            params.update(
                {
                    "Architecture": architecture,
                    "BillingProducts": billing_products,
                    "BootMode": boot_mode,
                    "EnaSupport": enhanced_networking,
                    "ImageLocation": image_location,
                    "KernelId": kernel_id,
                    "RamdiskId": ramdisk_id,
                    "RootDeviceName": root_device_name,
                    "SriovNetSupport": sriov_net_support,
                    "TpmSupport": tpm_support,
                    "UefiData": uefi_data,
                    "VirtualizationType": virtualization_type,
                }
            )

        return {k: v for k, v in params.items() if v}

    @classmethod
    def do(cls, module, connection, _image_id):
        """Entry point to create image"""
        create_image_parameters = cls.build_create_image_parameters(**module.params)

        func = cls.create_or_register(connection, create_image_parameters)
        try:
            image = func(aws_retry=True, **create_image_parameters)
            image_id = image.get("ImageId")
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            raise Ec2AmiFailure("Error registering image", e)

        cls.wait(connection, module.params.get("wait") and module.params.get("wait_timeout"), image_id)

        if "TagSpecifications" not in create_image_parameters:
            CreateImage.set_tags(connection, module, module.params.get("tags"), image_id)

        cls.set_launch_permissions(connection, module.params.get("launch_permissions"), image_id)

        module.exit_json(
            msg="AMI creation operation complete.", changed=True, **get_ami_info(get_image_by_id(connection, image_id))
        )


def main():
    mapping_options = {
        "delete_on_termination": {"type": "bool"},
        "device_name": {"type": "str", "required": True},
        "encrypted": {"type": "bool"},
        "iops": {"type": "int"},
        "no_device": {"type": "bool"},
        "snapshot_id": {"type": "str"},
        "virtual_name": {"type": "str"},
        "volume_size": {"type": "int", "aliases": ["size"]},
        "volume_type": {"type": "str"},
    }
    argument_spec = dict(
        architecture={"default": "x86_64"},
        billing_products={"type": "list", "elements": "str"},
        boot_mode={"type": "str", "choices": ["legacy-bios", "uefi"]},
        delete_snapshot={"default": False, "type": "bool"},
        description={"default": ""},
        device_mapping={"type": "list", "elements": "dict", "options": mapping_options},
        enhanced_networking={"type": "bool"},
        image_id={},
        image_location={},
        instance_id={},
        kernel_id={},
        launch_permissions={"type": "dict"},
        name={},
        no_reboot={"default": False, "type": "bool"},
        purge_tags={"type": "bool", "default": True},
        ramdisk_id={},
        root_device_name={},
        sriov_net_support={},
        state={"default": "present", "choices": ["present", "absent"]},
        tags={"type": "dict", "aliases": ["resource_tags"]},
        tpm_support={"type": "str"},
        uefi_data={"type": "str"},
        virtualization_type={"default": "hvm"},
        wait={"type": "bool", "default": False},
        wait_timeout={"default": 1200, "type": "int"},
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[
            ["state", "absent", ["image_id"]],
        ],
        supports_check_mode=True,
    )

    validate_params(module, **module.params)

    connection = module.client("ec2", retry_decorator=AWSRetry.jittered_backoff())

    CHECK_MODE_TRUE = True
    CHECK_MODE_FALSE = False
    HAS_IMAGE_ID_TRUE = True
    HAS_IMAGE_ID_FALSE = False

    func_mapping = {
        CHECK_MODE_TRUE: {
            HAS_IMAGE_ID_TRUE: {"absent": DeregisterImage.do_check_mode, "present": UpdateImage.do},
            HAS_IMAGE_ID_FALSE: {"present": CreateImage.do_check_mode},
        },
        CHECK_MODE_FALSE: {
            HAS_IMAGE_ID_TRUE: {"absent": DeregisterImage.do, "present": UpdateImage.do},
            HAS_IMAGE_ID_FALSE: {"present": CreateImage.do},
        },
    }
    func = func_mapping[module.check_mode][bool(module.params.get("image_id"))][module.params["state"]]
    try:
        func(module, connection, module.params.get("image_id"))
    except Ec2AmiFailure as e:
        if e.original_e:
            module.fail_json_aws(e.original_e, e.message)
        else:
            module.fail_json(e.message)


if __name__ == "__main__":
    main()
