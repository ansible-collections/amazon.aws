#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: ec2_ami
version_added: 1.0.0
short_description: Create or destroy an image (AMI) in ec2
description:
     - Registers or deregisters ec2 images.
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
      - The target architecture of the image to register
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
    default: 900
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
        virtual_name:
          type: str
          description:
          - The virtual name for the device.
          - See the AWS documentation for more detail U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_BlockDeviceMapping.html).
          - Alias C(VirtualName) has been deprecated and will be removed after 2022-06-01.
          aliases: ['VirtualName']
        no_device:
          type: bool
          description:
          - Suppresses the specified device included in the block device mapping of the AMI.
          - Alias C(NoDevice) has been deprecated and will be removed after 2022-06-01.
          aliases: ['NoDevice']
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
          description: When using an C(io1) I(volume_type) this sets the number of IOPS provisioned for the volume
        encrypted:
          type: bool
          description: Whether the volume should be encrypted.
        volume_size:
          aliases: ['size']
          type: int
          description: The size of the volume (in GiB)
  delete_snapshot:
    description:
      - Delete snapshots when deregistering the AMI.
    default: false
    type: bool
  tags:
    description:
      - A dictionary of tags to add to the new image; '{"key":"value"}' and '{"key":"value","key":"value"}'
    type: dict
  purge_tags:
    description: Whether to remove existing tags that aren't passed in the C(tags) parameter
    default: false
    type: bool
  launch_permissions:
    description:
      - Users and groups that should be able to launch the AMI. Expects dictionary with a key of user_ids and/or group_names. user_ids should
        be a list of account ids. group_name should be a list of groups, "all" is the only acceptable value currently.
      - You must pass all desired launch permissions if you wish to modify existing launch permissions (passing just groups will remove all users)
    type: dict
  image_location:
    description:
      - The s3 location of an image to use for the AMI.
    type: str
  enhanced_networking:
    description:
      - A boolean representing whether enhanced networking with ENA is enabled or not.
    type: bool
  billing_products:
    description:
      - A list of valid billing codes. To be used with valid accounts by aws marketplace vendors.
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
author:
    - "Evan Duffield (@scicoin-project) <eduffield@iacquire.com>"
    - "Constantin Bugneac (@Constantin07) <constantin.bugneac@endava.com>"
    - "Ross Williams (@gunzy83) <gunzy83au@gmail.com>"
    - "Willem van Ketwich (@wilvk) <willvk@gmail.com>"
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

# Thank you to iAcquire for sponsoring development of this module.

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Basic AMI Creation
  amazon.aws.ec2_ami:
    instance_id: i-xxxxxx
    wait: yes
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
          no_device: yes

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
'''

RETURN = '''
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
    sample: "315210894379/nat-server"
name:
    description: AMI name of image.
    returned: when AMI is created or already exists
    type: str
    sample: "nat-server"
ownerId:
    description: Owner of image.
    returned: when AMI is created or already exists
    type: str
    sample: "435210894375"
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
'''

import time

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ..module_utils.core import AnsibleAWSModule
from ..module_utils.core import is_boto3_error_code
from ..module_utils.ec2 import ansible_dict_to_boto3_tag_list
from ..module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ..module_utils.ec2 import compare_aws_tags


def get_block_device_mapping(image):
    bdm_dict = dict()
    if image is not None and image.get('block_device_mappings') is not None:
        bdm = image.get('block_device_mappings')
        for device in bdm:
            device_name = device.get('device_name')
            if 'ebs' in device:
                ebs = device.get("ebs")
                bdm_dict_item = {
                    'size': ebs.get("volume_size"),
                    'snapshot_id': ebs.get("snapshot_id"),
                    'volume_type': ebs.get("volume_type"),
                    'encrypted': ebs.get("encrypted"),
                    'delete_on_termination': ebs.get("delete_on_termination")
                }
            elif 'virtual_name' in device:
                bdm_dict_item = dict(virtual_name=device['virtual_name'])
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
        tags=boto3_tag_list_to_ansible_dict(image.get('tags')),
        platform=image.get("platform"),
        enhanced_networking=image.get("ena_support"),
        image_owner_alias=image.get("image_owner_alias"),
        image_type=image.get("image_type"),
        kernel_id=image.get("kernel_id"),
        product_codes=image.get("product_codes"),
        ramdisk_id=image.get("ramdisk_id"),
        sriov_net_support=image.get("sriov_net_support"),
        state_reason=image.get("state_reason"),
        launch_permissions=image.get('launch_permissions')
    )


def create_image(module, connection):
    instance_id = module.params.get('instance_id')
    name = module.params.get('name')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')
    description = module.params.get('description')
    architecture = module.params.get('architecture')
    kernel_id = module.params.get('kernel_id')
    root_device_name = module.params.get('root_device_name')
    virtualization_type = module.params.get('virtualization_type')
    no_reboot = module.params.get('no_reboot')
    device_mapping = module.params.get('device_mapping')
    tags = module.params.get('tags')
    launch_permissions = module.params.get('launch_permissions')
    image_location = module.params.get('image_location')
    enhanced_networking = module.params.get('enhanced_networking')
    billing_products = module.params.get('billing_products')
    ramdisk_id = module.params.get('ramdisk_id')
    sriov_net_support = module.params.get('sriov_net_support')

    try:
        params = {
            'Name': name,
            'Description': description
        }

        block_device_mapping = None

        # Remove empty values injected by using options
        if device_mapping:
            block_device_mapping = []
            for device in device_mapping:
                device = dict((k, v) for k, v in device.items() if v is not None)
                device['Ebs'] = {}
                device = rename_item_if_exists(device, 'device_name', 'DeviceName')
                device = rename_item_if_exists(device, 'virtual_name', 'VirtualName')
                device = rename_item_if_exists(device, 'no_device', 'NoDevice')
                device = rename_item_if_exists(device, 'volume_type', 'VolumeType', 'Ebs')
                device = rename_item_if_exists(device, 'snapshot_id', 'SnapshotId', 'Ebs')
                device = rename_item_if_exists(device, 'delete_on_termination', 'DeleteOnTermination', 'Ebs')
                device = rename_item_if_exists(device, 'size', 'VolumeSize', 'Ebs', attribute_type=int)
                device = rename_item_if_exists(device, 'volume_size', 'VolumeSize', 'Ebs', attribute_type=int)
                device = rename_item_if_exists(device, 'iops', 'Iops', 'Ebs')
                device = rename_item_if_exists(device, 'encrypted', 'Encrypted', 'Ebs')
                block_device_mapping.append(device)
        if block_device_mapping:
            params['BlockDeviceMappings'] = block_device_mapping
        if instance_id:
            params['InstanceId'] = instance_id
            params['NoReboot'] = no_reboot
            image_id = connection.create_image(**params).get('ImageId')
        else:
            if architecture:
                params['Architecture'] = architecture
            if virtualization_type:
                params['VirtualizationType'] = virtualization_type
            if image_location:
                params['ImageLocation'] = image_location
            if enhanced_networking:
                params['EnaSupport'] = enhanced_networking
            if billing_products:
                params['BillingProducts'] = billing_products
            if ramdisk_id:
                params['RamdiskId'] = ramdisk_id
            if sriov_net_support:
                params['SriovNetSupport'] = sriov_net_support
            if kernel_id:
                params['KernelId'] = kernel_id
            if root_device_name:
                params['RootDeviceName'] = root_device_name
            image_id = connection.register_image(**params).get('ImageId')
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Error registering image")

    if wait:
        waiter = connection.get_waiter('image_available')
        delay = wait_timeout // 30
        max_attempts = 30
        waiter.wait(ImageIds=[image_id], WaiterConfig=dict(Delay=delay, MaxAttempts=max_attempts))

    if tags:
        try:
            connection.create_tags(Resources=[image_id], Tags=ansible_dict_to_boto3_tag_list(tags))
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Error tagging image")

    if launch_permissions:
        try:
            params = dict(Attribute='LaunchPermission', ImageId=image_id, LaunchPermission=dict(Add=list()))
            for group_name in launch_permissions.get('group_names', []):
                params['LaunchPermission']['Add'].append(dict(Group=group_name))
            for user_id in launch_permissions.get('user_ids', []):
                params['LaunchPermission']['Add'].append(dict(UserId=str(user_id)))
            if params['LaunchPermission']['Add']:
                connection.modify_image_attribute(**params)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Error setting launch permissions for image %s" % image_id)

    module.exit_json(msg="AMI creation operation complete.", changed=True,
                     **get_ami_info(get_image_by_id(module, connection, image_id)))


def deregister_image(module, connection):
    image_id = module.params.get('image_id')
    delete_snapshot = module.params.get('delete_snapshot')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')
    image = get_image_by_id(module, connection, image_id)

    if image is None:
        module.exit_json(changed=False)

    # Get all associated snapshot ids before deregistering image otherwise this information becomes unavailable.
    snapshots = []
    if 'BlockDeviceMappings' in image:
        for mapping in image.get('BlockDeviceMappings'):
            snapshot_id = mapping.get('Ebs', {}).get('SnapshotId')
            if snapshot_id is not None:
                snapshots.append(snapshot_id)

    # When trying to re-deregister an already deregistered image it doesn't raise an exception, it just returns an object without image attributes.
    if 'ImageId' in image:
        try:
            connection.deregister_image(ImageId=image_id)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Error deregistering image")
    else:
        module.exit_json(msg="Image %s has already been deregistered." % image_id, changed=False)

    image = get_image_by_id(module, connection, image_id)
    wait_timeout = time.time() + wait_timeout

    while wait and wait_timeout > time.time() and image is not None:
        image = get_image_by_id(module, connection, image_id)
        time.sleep(3)

    if wait and wait_timeout <= time.time():
        module.fail_json(msg="Timed out waiting for image to be deregistered.")

    exit_params = {'msg': "AMI deregister operation complete.", 'changed': True}

    if delete_snapshot:
        try:
            for snapshot_id in snapshots:
                connection.delete_snapshot(SnapshotId=snapshot_id)
        # Don't error out if root volume snapshot was already deregistered as part of deregister_image
        except is_boto3_error_code('InvalidSnapshot.NotFound'):
            pass
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg='Failed to delete snapshot.')
        exit_params['snapshots_deleted'] = snapshots

    module.exit_json(**exit_params)


def update_image(module, connection, image_id):
    launch_permissions = module.params.get('launch_permissions')
    image = get_image_by_id(module, connection, image_id)
    if image is None:
        module.fail_json(msg="Image %s does not exist" % image_id, changed=False)
    changed = False

    if launch_permissions is not None:
        current_permissions = image['LaunchPermissions']

        current_users = set(permission['UserId'] for permission in current_permissions if 'UserId' in permission)
        desired_users = set(str(user_id) for user_id in launch_permissions.get('user_ids', []))
        current_groups = set(permission['Group'] for permission in current_permissions if 'Group' in permission)
        desired_groups = set(launch_permissions.get('group_names', []))

        to_add_users = desired_users - current_users
        to_remove_users = current_users - desired_users
        to_add_groups = desired_groups - current_groups
        to_remove_groups = current_groups - desired_groups

        to_add = [dict(Group=group) for group in to_add_groups] + [dict(UserId=user_id) for user_id in to_add_users]
        to_remove = [dict(Group=group) for group in to_remove_groups] + [dict(UserId=user_id) for user_id in to_remove_users]

        if to_add or to_remove:
            try:
                connection.modify_image_attribute(ImageId=image_id, Attribute='launchPermission',
                                                  LaunchPermission=dict(Add=to_add, Remove=to_remove))
                changed = True
            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                module.fail_json_aws(e, msg="Error updating launch permissions of image %s" % image_id)

    desired_tags = module.params.get('tags')
    if desired_tags is not None:
        current_tags = boto3_tag_list_to_ansible_dict(image.get('Tags'))
        tags_to_add, tags_to_remove = compare_aws_tags(current_tags, desired_tags, purge_tags=module.params.get('purge_tags'))

        if tags_to_remove:
            try:
                connection.delete_tags(Resources=[image_id], Tags=[dict(Key=tagkey) for tagkey in tags_to_remove])
                changed = True
            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                module.fail_json_aws(e, msg="Error updating tags")

        if tags_to_add:
            try:
                connection.create_tags(Resources=[image_id], Tags=ansible_dict_to_boto3_tag_list(tags_to_add))
                changed = True
            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                module.fail_json_aws(e, msg="Error updating tags")

    description = module.params.get('description')
    if description and description != image['Description']:
        try:
            connection.modify_image_attribute(Attribute='Description ', ImageId=image_id, Description=dict(Value=description))
            changed = True
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Error setting description for image %s" % image_id)

    if changed:
        module.exit_json(msg="AMI updated.", changed=True,
                         **get_ami_info(get_image_by_id(module, connection, image_id)))
    else:
        module.exit_json(msg="AMI not updated.", changed=False,
                         **get_ami_info(get_image_by_id(module, connection, image_id)))


def get_image_by_id(module, connection, image_id):
    try:
        try:
            images_response = connection.describe_images(ImageIds=[image_id])
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Error retrieving image %s" % image_id)
        images = images_response.get('Images')
        no_images = len(images)
        if no_images == 0:
            return None
        if no_images == 1:
            result = images[0]
            try:
                result['LaunchPermissions'] = connection.describe_image_attribute(Attribute='launchPermission', ImageId=image_id)['LaunchPermissions']
                result['ProductCodes'] = connection.describe_image_attribute(Attribute='productCodes', ImageId=image_id)['ProductCodes']
            except is_boto3_error_code('InvalidAMIID.Unavailable'):
                pass
            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                module.fail_json_aws(e, msg="Error retrieving image attributes for image %s" % image_id)
            return result
        module.fail_json(msg="Invalid number of instances (%s) found for image_id: %s." % (str(len(images)), image_id))
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Error retrieving image by image_id")


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


def main():
    mapping_options = dict(
        device_name=dict(type='str'),
        virtual_name=dict(
            type='str', aliases=['VirtualName'],
            deprecated_aliases=[dict(name='VirtualName', date='2022-06-01', collection_name='amazon.aws')]),
        no_device=dict(
            type='bool', aliases=['NoDevice'],
            deprecated_aliases=[dict(name='NoDevice', date='2022-06-01', collection_name='amazon.aws')]),
        volume_type=dict(type='str'),
        delete_on_termination=dict(type='bool'),
        snapshot_id=dict(type='str'),
        iops=dict(type='int'),
        encrypted=dict(type='bool'),
        volume_size=dict(type='int', aliases=['size']),
    )
    argument_spec = dict(
        instance_id=dict(),
        image_id=dict(),
        architecture=dict(default='x86_64'),
        kernel_id=dict(),
        virtualization_type=dict(default='hvm'),
        root_device_name=dict(),
        delete_snapshot=dict(default=False, type='bool'),
        name=dict(),
        wait=dict(type='bool', default=False),
        wait_timeout=dict(default=900, type='int'),
        description=dict(default=''),
        no_reboot=dict(default=False, type='bool'),
        state=dict(default='present', choices=['present', 'absent']),
        device_mapping=dict(type='list', elements='dict', options=mapping_options),
        tags=dict(type='dict'),
        launch_permissions=dict(type='dict'),
        image_location=dict(),
        enhanced_networking=dict(type='bool'),
        billing_products=dict(type='list', elements='str',),
        ramdisk_id=dict(),
        sriov_net_support=dict(),
        purge_tags=dict(type='bool', default=False)
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[
            ['state', 'absent', ['image_id']],
        ]
    )

    # Using a required_one_of=[['name', 'image_id']] overrides the message that should be provided by
    # the required_if for state=absent, so check manually instead
    if not any([module.params['image_id'], module.params['name']]):
        module.fail_json(msg="one of the following is required: name, image_id")

    connection = module.client('ec2')

    if module.params.get('state') == 'absent':
        deregister_image(module, connection)
    elif module.params.get('state') == 'present':
        if module.params.get('image_id'):
            update_image(module, connection, module.params.get('image_id'))
        if not module.params.get('instance_id') and not module.params.get('device_mapping'):
            module.fail_json(msg="The parameters instance_id or device_mapping (register from EBS snapshot) are required for a new image.")
        create_image(module, connection)


if __name__ == '__main__':
    main()
