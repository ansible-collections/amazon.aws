#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: ec2_vol
version_added: 1.0.0
short_description: Create and attach a volume, return volume id and device map
description:
    - Creates an EBS volume and optionally attaches it to an instance.
    - If both I(instance) and I(name) are given and the instance has a device at the device name, then no volume is created and no attachment is made.
    - This module has a dependency on python-boto.
options:
  instance:
    description:
      - Instance ID if you wish to attach the volume. Since 1.9 you can set to None to detach.
    type: str
  name:
    description:
      - Volume Name tag if you wish to attach an existing volume (requires instance)
    type: str
  id:
    description:
      - Volume id if you wish to attach an existing volume (requires instance) or remove an existing volume
    type: str
  volume_size:
    description:
      - Size of volume (in GiB) to create.
    type: int
  volume_type:
    description:
      - Type of EBS volume; standard (magnetic), gp2 (SSD), io1 (Provisioned IOPS), st1 (Throughput Optimized HDD), sc1 (Cold HDD).
        "Standard" is the old EBS default and continues to remain the Ansible default for backwards compatibility.
    default: standard
    choices: ['standard', 'gp2', 'io1', 'st1', 'sc1']
    type: str
  iops:
    description:
      - The provisioned IOPs you want to associate with this volume (integer).
      - By default AWS will set this to 100.
    type: int
  encrypted:
    description:
      - Enable encryption at rest for this volume.
    default: false
    type: bool
  kms_key_id:
    description:
      - Specify the id of the KMS key to use.
    type: str
  device_name:
    description:
      - Device id to override device mapping. Assumes /dev/sdf for Linux/UNIX and /dev/xvdf for Windows.
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
  validate_certs:
    description:
      - When set to "no", SSL certificates will not be validated for boto versions >= 2.6.0.
    type: bool
    default: true
  state:
    description:
      - Whether to ensure the volume is present or absent.
      - The use of I(state=list) to interrogate the volume has been deprecated
        and will be removed after 2022-06-01.  The 'list' functionality
        has been moved to a dedicated module M(amazon.aws.ec2_vol_info).
    default: present
    choices: ['absent', 'present', 'list']
    type: str
  tags:
    description:
      - tag:value pairs to add to the volume after creation.
    default: {}
    type: dict
author: "Lester Wade (@lwade)"
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
# Simple attachment action
- amazon.aws.ec2_vol:
    instance: XXXXXX
    volume_size: 5
    device_name: sdd

# Example using custom iops params
- amazon.aws.ec2_vol:
    instance: XXXXXX
    volume_size: 5
    iops: 100
    device_name: sdd

# Example using snapshot id
- amazon.aws.ec2_vol:
    instance: XXXXXX
    snapshot: "{{ snapshot }}"

# Playbook example combined with instance launch
- amazon.aws.ec2:
    keypair: "{{ keypair }}"
    image: "{{ image }}"
    wait: yes
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
#   * Requires Ansible 2.0

- amazon.aws.ec2:
    keypair: "{{ keypair }}"
    image: "{{ image }}"
    zone: YYYYYY
    id: my_instance
    wait: yes
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

# List volumes for an instance
- amazon.aws.ec2_vol:
    instance: i-XXXXXX
    state: list

# Create new volume using SSD storage
- amazon.aws.ec2_vol:
    instance: XXXXXX
    volume_size: 50
    volume_type: gp2
    device_name: /dev/xvdf

# Attach an existing volume to instance. The volume will be deleted upon instance termination.
- amazon.aws.ec2_vol:
    instance: XXXXXX
    id: XXXXXX
    device_name: /dev/sdf
    delete_on_termination: yes
'''

RETURN = '''
device:
    description: device name of attached volume
    returned: when success
    type: str
    sample: "/def/sdf"
volume_id:
    description: the id of volume
    returned: when success
    type: str
    sample: "vol-35b333d9"
volume_type:
    description: the volume type
    returned: when success
    type: str
    sample: "standard"
volume:
    description: a dictionary containing detailed attributes of the volume
    returned: when success
    type: str
    sample: {
        "attachment_set": {
            "attach_time": "2015-10-23T00:22:29.000Z",
            "deleteOnTermination": "false",
            "device": "/dev/sdf",
            "instance_id": "i-8356263c",
            "status": "attached"
        },
        "create_time": "2015-10-21T14:36:08.870Z",
        "encrypted": false,
        "id": "vol-35b333d9",
        "iops": null,
        "size": 1,
        "snapshot_id": "",
        "status": "in-use",
        "tags": {
            "env": "dev"
        },
        "type": "standard",
        "zone": "us-east-1b"
    }
'''

import time

from distutils.version import LooseVersion

try:
    import boto
    import boto.ec2
    import boto.exception
    from boto.exception import BotoServerError
    from boto.ec2.blockdevicemapping import BlockDeviceType
    from boto.ec2.blockdevicemapping import BlockDeviceMapping
except ImportError:
    pass  # Taken care of by ec2.HAS_BOTO

from ..module_utils.core import AnsibleAWSModule
from ..module_utils.ec2 import AnsibleAWSError
from ..module_utils.ec2 import HAS_BOTO
from ..module_utils.ec2 import connect_to_aws
from ..module_utils.ec2 import get_aws_connection_info


def get_volume(module, ec2):
    name = module.params.get('name')
    id = module.params.get('id')
    zone = module.params.get('zone')
    filters = {}
    volume_ids = None

    # If no name or id supplied, just try volume creation based on module parameters
    if id is None and name is None:
        return None

    if zone:
        filters['availability_zone'] = zone
    if name:
        filters['tag:Name'] = name
    if id:
        volume_ids = [id]
    try:
        vols = ec2.get_all_volumes(volume_ids=volume_ids, filters=filters)
    except boto.exception.BotoServerError as e:
        module.fail_json_aws(e)

    if not vols:
        if id:
            msg = "Could not find the volume with id: %s" % id
            if name:
                msg += (" and name: %s" % name)
            module.fail_json(msg=msg)
        else:
            return None

    if len(vols) > 1:
        module.fail_json(msg="Found more than one volume in zone (if specified) with name: %s" % name)
    return vols[0]


def get_volumes(module, ec2):

    instance = module.params.get('instance')

    try:
        if not instance:
            vols = ec2.get_all_volumes()
        else:
            vols = ec2.get_all_volumes(filters={'attachment.instance-id': instance})
    except boto.exception.BotoServerError as e:
        module.fail_json_aws(e)
    return vols


def delete_volume(module, ec2):
    volume_id = module.params['id']
    try:
        ec2.delete_volume(volume_id)
        module.exit_json(changed=True)
    except boto.exception.EC2ResponseError as ec2_error:
        if ec2_error.code == 'InvalidVolume.NotFound':
            module.exit_json(changed=False)
        module.fail_json_aws(ec2_error)


def boto_supports_volume_encryption():
    """
    Check if Boto library supports encryption of EBS volumes (added in 2.29.0)

    Returns:
        True if boto library has the named param as an argument on the request_spot_instances method, else False
    """
    return hasattr(boto, 'Version') and LooseVersion(boto.Version) >= LooseVersion('2.29.0')


def boto_supports_kms_key_id():
    """
    Check if Boto library supports kms_key_ids (added in 2.39.0)

    Returns:
        True if version is equal to or higher then the version needed, else False
    """
    return hasattr(boto, 'Version') and LooseVersion(boto.Version) >= LooseVersion('2.39.0')


def create_volume(module, ec2, zone):
    changed = False
    name = module.params.get('name')
    iops = module.params.get('iops')
    encrypted = module.params.get('encrypted')
    kms_key_id = module.params.get('kms_key_id')
    volume_size = module.params.get('volume_size')
    volume_type = module.params.get('volume_type')
    snapshot = module.params.get('snapshot')
    tags = module.params.get('tags')
    # If custom iops is defined we use volume_type "io1" rather than the default of "standard"
    if iops:
        volume_type = 'io1'

    volume = get_volume(module, ec2)
    if volume is None:
        try:
            if boto_supports_volume_encryption():
                if kms_key_id is not None:
                    volume = ec2.create_volume(volume_size, zone, snapshot, volume_type, iops, encrypted, kms_key_id)
                else:
                    volume = ec2.create_volume(volume_size, zone, snapshot, volume_type, iops, encrypted)
                changed = True
            else:
                volume = ec2.create_volume(volume_size, zone, snapshot, volume_type, iops)
                changed = True

            while volume.status != 'available':
                time.sleep(3)
                volume.update()

            if name:
                tags["Name"] = name
            if tags:
                ec2.create_tags([volume.id], tags)
        except boto.exception.BotoServerError as e:
            module.fail_json_aws(e)

    return volume, changed


def attach_volume(module, ec2, volume, instance):

    device_name = module.params.get('device_name')
    delete_on_termination = module.params.get('delete_on_termination')
    changed = False

    # If device_name isn't set, make a choice based on best practices here:
    # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/block-device-mapping-concepts.html

    # In future this needs to be more dynamic but combining block device mapping best practices
    # (bounds for devices, as above) with instance.block_device_mapping data would be tricky. For me ;)

    # Use password data attribute to tell whether the instance is Windows or Linux
    if device_name is None:
        try:
            if not ec2.get_password_data(instance.id):
                device_name = '/dev/sdf'
            else:
                device_name = '/dev/xvdf'
        except boto.exception.BotoServerError as e:
            module.fail_json_aws(e)

    if volume.attachment_state() is not None:
        adata = volume.attach_data
        if adata.instance_id != instance.id:
            module.fail_json(msg="Volume %s is already attached to another instance: %s"
                             % (volume.id, adata.instance_id))
        else:
            # Volume is already attached to right instance
            changed = modify_dot_attribute(module, ec2, instance, device_name)
    else:
        try:
            volume.attach(instance.id, device_name)
            while volume.attachment_state() != 'attached':
                time.sleep(3)
                volume.update()
            changed = True
        except boto.exception.BotoServerError as e:
            module.fail_json_aws(e)

        modify_dot_attribute(module, ec2, instance, device_name)

    return volume, changed


def modify_dot_attribute(module, ec2, instance, device_name):
    """ Modify delete_on_termination attribute """

    delete_on_termination = module.params.get('delete_on_termination')
    changed = False

    try:
        instance.update()
        dot = instance.block_device_mapping[device_name].delete_on_termination
    except boto.exception.BotoServerError as e:
        module.fail_json_aws(e)

    if delete_on_termination != dot:
        try:
            bdt = BlockDeviceType(delete_on_termination=delete_on_termination)
            bdm = BlockDeviceMapping()
            bdm[device_name] = bdt

            ec2.modify_instance_attribute(instance_id=instance.id, attribute='blockDeviceMapping', value=bdm)

            while instance.block_device_mapping[device_name].delete_on_termination != delete_on_termination:
                time.sleep(3)
                instance.update()
            changed = True
        except boto.exception.BotoServerError as e:
            module.fail_json_aws(e)

    return changed


def detach_volume(module, ec2, volume):

    changed = False

    if volume.attachment_state() is not None:
        adata = volume.attach_data
        volume.detach()
        while volume.attachment_state() is not None:
            time.sleep(3)
            volume.update()
        changed = True

    return volume, changed


def get_volume_info(volume, state):

    # If we're just listing volumes then do nothing, else get the latest update for the volume
    if state != 'list':
        volume.update()

    volume_info = {}
    attachment = volume.attach_data

    volume_info = {
        'create_time': volume.create_time,
        'encrypted': volume.encrypted,
        'id': volume.id,
        'iops': volume.iops,
        'size': volume.size,
        'snapshot_id': volume.snapshot_id,
        'status': volume.status,
        'type': volume.type,
        'zone': volume.zone,
        'attachment_set': {
            'attach_time': attachment.attach_time,
            'device': attachment.device,
            'instance_id': attachment.instance_id,
            'status': attachment.status
        },
        'tags': volume.tags
    }
    if hasattr(attachment, 'deleteOnTermination'):
        volume_info['attachment_set']['deleteOnTermination'] = attachment.deleteOnTermination

    return volume_info


def main():
    argument_spec = dict(
        instance=dict(),
        id=dict(),
        name=dict(),
        volume_size=dict(type='int'),
        volume_type=dict(choices=['standard', 'gp2', 'io1', 'st1', 'sc1'], default='standard'),
        iops=dict(type='int'),
        encrypted=dict(type='bool', default=False),
        kms_key_id=dict(),
        device_name=dict(),
        delete_on_termination=dict(type='bool', default=False),
        zone=dict(aliases=['availability_zone', 'aws_zone', 'ec2_zone']),
        snapshot=dict(),
        state=dict(choices=['absent', 'present', 'list'], default='present'),
        tags=dict(type='dict', default={})
    )
    module = AnsibleAWSModule(argument_spec=argument_spec, check_boto3=False)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    id = module.params.get('id')
    name = module.params.get('name')
    instance = module.params.get('instance')
    volume_size = module.params.get('volume_size')
    encrypted = module.params.get('encrypted')
    kms_key_id = module.params.get('kms_key_id')
    device_name = module.params.get('device_name')
    zone = module.params.get('zone')
    snapshot = module.params.get('snapshot')
    state = module.params.get('state')
    tags = module.params.get('tags')

    if state == 'list':
        module.deprecate(
            'Using the "list" state has been deprecated.  Please use the ec2_vol_info module instead', date='2022-06-01', collection_name='amazon.aws')

    # Ensure we have the zone or can get the zone
    if instance is None and zone is None and state == 'present':
        module.fail_json(msg="You must specify either instance or zone")

    # Set volume detach flag
    if instance == 'None' or instance == '':
        instance = None
        detach_vol_flag = True
    else:
        detach_vol_flag = False

    # Set changed flag
    changed = False

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    if region:
        try:
            ec2 = connect_to_aws(boto.ec2, region, **aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError) as e:
            module.fail_json_aws(e)
    else:
        module.fail_json(msg="region must be specified")

    if state == 'list':
        returned_volumes = []
        vols = get_volumes(module, ec2)

        for v in vols:
            attachment = v.attach_data

            returned_volumes.append(get_volume_info(v, state))

        module.exit_json(changed=False, volumes=returned_volumes)

    if encrypted and not boto_supports_volume_encryption():
        module.fail_json(msg="You must use boto >= v2.29.0 to use encrypted volumes")

    if kms_key_id is not None and not boto_supports_kms_key_id():
        module.fail_json(msg="You must use boto >= v2.39.0 to use kms_key_id")

    # Here we need to get the zone info for the instance. This covers situation where
    # instance is specified but zone isn't.
    # Useful for playbooks chaining instance launch with volume create + attach and where the
    # zone doesn't matter to the user.
    inst = None
    if instance:
        try:
            reservation = ec2.get_all_instances(instance_ids=instance)
        except BotoServerError as e:
            module.fail_json_aws(e)
        inst = reservation[0].instances[0]
        zone = inst.placement

        # Check if there is a volume already mounted there.
        if device_name:
            if device_name in inst.block_device_mapping:
                module.exit_json(msg="Volume mapping for %s already exists on instance %s" % (device_name, instance),
                                 volume_id=inst.block_device_mapping[device_name].volume_id,
                                 device=device_name,
                                 changed=False)

    # Delaying the checks until after the instance check allows us to get volume ids for existing volumes
    # without needing to pass an unused volume_size
    if not volume_size and not (id or name or snapshot):
        module.fail_json(msg="You must specify volume_size or identify an existing volume by id, name, or snapshot")

    if volume_size and id:
        module.fail_json(msg="Cannot specify volume_size together with id")

    if state == 'present':
        volume, changed = create_volume(module, ec2, zone)
        if detach_vol_flag:
            volume, changed = detach_volume(module, ec2, volume)
        elif inst is not None:
            volume, changed = attach_volume(module, ec2, volume, inst)

        # Add device, volume_id and volume_type parameters separately to maintain backward compatibility
        volume_info = get_volume_info(volume, state)

        # deleteOnTermination is not correctly reflected on attachment
        if module.params.get('delete_on_termination'):
            for attempt in range(0, 8):
                if volume_info['attachment_set'].get('deleteOnTermination') == 'true':
                    break
                time.sleep(5)
                volume = ec2.get_all_volumes(volume_ids=volume.id)[0]
                volume_info = get_volume_info(volume, state)
        module.exit_json(changed=changed, volume=volume_info, device=volume_info['attachment_set']['device'],
                         volume_id=volume_info['id'], volume_type=volume_info['type'])
    elif state == 'absent':
        delete_volume(module, ec2)


if __name__ == '__main__':
    main()
