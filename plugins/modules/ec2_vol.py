#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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
      - Type of EBS volume; standard (magnetic), gp2 (SSD), gp3 (SSD), io1 (Provisioned IOPS), io2 (Provisioned IOPS),
        st1 (Throughput Optimized HDD), sc1 (Cold HDD).
        "Standard" is the old EBS default and continues to remain the Ansible default for backwards compatibility.
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
  state:
    description:
      - Whether to ensure the volume is present or absent.
      - I(state=list) was deprecated in release 1.1.0 and is no longer available
        with release 4.0.0.  The 'list' functionality has been moved to a dedicated
        module M(amazon.aws.ec2_vol_info).
    default: present
    choices: ['absent', 'present']
    type: str
  modify_volume:
    description:
      - The volume won't be modified unless this key is C(true).
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
      - If set to C(yes), Multi-Attach will be enabled when creating the volume.
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
author: "Lester Wade (@lwade)"
notes:
- Support for I(purge_tags) was added in release 1.5.0.
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
- amazon.aws.tags.deprecated_purge
'''

EXAMPLES = '''
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
        "attachment_set": [{
            "attach_time": "2015-10-23T00:22:29.000Z",
            "deleteOnTermination": "false",
            "device": "/dev/sdf",
            "instance_id": "i-8356263c",
            "status": "attached"
        }],
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

from ansible_collections.amazon.aws.plugins.module_utils.arn import is_outpost_arn
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications


try:
    import botocore
except ImportError:
    pass  # Taken care of by AnsibleAWSModule


def get_instance(module, ec2_conn, instance_id=None):
    instance = None
    if not instance_id:
        return instance

    try:
        reservation_response = ec2_conn.describe_instances(aws_retry=True, InstanceIds=[instance_id])
        instance = camel_dict_to_snake_dict(reservation_response['Reservations'][0]['Instances'][0])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Error while getting instance_id with id {0}'.format(instance))

    return instance


def get_volume(module, ec2_conn, vol_id=None, fail_on_not_found=True):
    name = module.params.get('name')
    param_id = module.params.get('id')
    zone = module.params.get('zone')

    if not vol_id:
        vol_id = param_id

    # If no name or id supplied, just try volume creation based on module parameters
    if vol_id is None and name is None:
        return None

    find_params = dict()
    vols = []

    if vol_id:
        find_params['VolumeIds'] = [vol_id]
    elif name:
        find_params['Filters'] = ansible_dict_to_boto3_filter_list({'tag:Name': name})
    elif zone:
        find_params['Filters'] = ansible_dict_to_boto3_filter_list({'availability-zone': zone})

    try:
        paginator = ec2_conn.get_paginator('describe_volumes')
        vols_response = paginator.paginate(**find_params)
        vols = list(vols_response)[0].get('Volumes')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        if is_boto3_error_code('InvalidVolume.NotFound'):
            module.exit_json(msg="Volume {0} does not exist".format(vol_id), changed=False)
        module.fail_json_aws(e, msg='Error while getting EBS volumes with the parameters {0}'.format(find_params))

    if not vols:
        if fail_on_not_found and vol_id:
            msg = "Could not find volume with id: {0}".format(vol_id)
            if name:
                msg += (" and name: {0}".format(name))
            module.fail_json(msg=msg)
        else:
            return None

    if len(vols) > 1:
        module.fail_json(
            msg="Found more than one volume in zone (if specified) with name: {0}".format(name),
            found=[v['VolumeId'] for v in vols]
        )
    vol = camel_dict_to_snake_dict(vols[0])
    return vol


def get_volumes(module, ec2_conn):
    instance = module.params.get('instance')

    find_params = dict()
    if instance:
        find_params['Filters'] = ansible_dict_to_boto3_filter_list({'attachment.instance-id': instance})

    vols = []
    try:
        vols_response = ec2_conn.describe_volumes(aws_retry=True, **find_params)
        vols = [camel_dict_to_snake_dict(vol) for vol in vols_response.get('Volumes', [])]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Error while getting EBS volumes')
    return vols


def delete_volume(module, ec2_conn, volume_id=None):
    changed = False
    if volume_id:
        try:
            ec2_conn.delete_volume(aws_retry=True, VolumeId=volume_id)
            changed = True
        except is_boto3_error_code('InvalidVolume.NotFound'):
            module.exit_json(changed=False)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg='Error while deleting volume')
    return changed


def update_volume(module, ec2_conn, volume):
    changed = False
    req_obj = {'VolumeId': volume['volume_id']}

    if module.params.get('modify_volume'):
        target_type = module.params.get('volume_type')
        original_type = None
        type_changed = False
        if target_type:
            original_type = volume['volume_type']
            if target_type != original_type:
                type_changed = True
                req_obj['VolumeType'] = target_type

        iops_changed = False
        target_iops = module.params.get('iops')
        original_iops = volume.get('iops')
        if target_iops:
            if target_iops != original_iops:
                iops_changed = True
                req_obj['Iops'] = target_iops
            else:
                req_obj['Iops'] = original_iops
        else:
            # If no IOPS value is specified and there was a volume_type update to gp3,
            # the existing value is retained, unless a volume type is modified that supports different values,
            # otherwise, the default iops value is applied.
            if type_changed and target_type == 'gp3':
                if (
                    (original_iops and (int(original_iops) < 3000 or int(original_iops) > 16000)) or not original_iops
                ):
                    req_obj['Iops'] = 3000
                    iops_changed = True

        target_size = module.params.get('volume_size')
        size_changed = False
        if target_size:
            original_size = volume['size']
            if target_size != original_size:
                size_changed = True
                req_obj['Size'] = target_size

        target_type = module.params.get('volume_type')
        original_type = None
        type_changed = False
        if target_type:
            original_type = volume['volume_type']
            if target_type != original_type:
                type_changed = True
                req_obj['VolumeType'] = target_type

        target_throughput = module.params.get('throughput')
        throughput_changed = False
        if target_throughput:
            original_throughput = volume.get('throughput')
            if target_throughput != original_throughput:
                throughput_changed = True
                req_obj['Throughput'] = target_throughput

        target_multi_attach = module.params.get('multi_attach')
        multi_attach_changed = False
        if target_multi_attach is not None:
            original_multi_attach = volume['multi_attach_enabled']
            if target_multi_attach != original_multi_attach:
                multi_attach_changed = True
                req_obj['MultiAttachEnabled'] = target_multi_attach

        changed = iops_changed or size_changed or type_changed or throughput_changed or multi_attach_changed

        if changed:
            if module.check_mode:
                module.exit_json(changed=True, msg='Would have updated volume if not in check mode.')
            response = ec2_conn.modify_volume(**req_obj)

            volume['size'] = response.get('VolumeModification').get('TargetSize')
            volume['volume_type'] = response.get('VolumeModification').get('TargetVolumeType')
            volume['iops'] = response.get('VolumeModification').get('TargetIops')
            volume['multi_attach_enabled'] = response.get('VolumeModification').get('TargetMultiAttachEnabled')
            volume['throughput'] = response.get('VolumeModification').get('TargetThroughput')

    return volume, changed


def create_volume(module, ec2_conn, zone):
    changed = False
    iops = module.params.get('iops')
    encrypted = module.params.get('encrypted')
    kms_key_id = module.params.get('kms_key_id')
    volume_size = module.params.get('volume_size')
    volume_type = module.params.get('volume_type')
    snapshot = module.params.get('snapshot')
    throughput = module.params.get('throughput')
    multi_attach = module.params.get('multi_attach')
    outpost_arn = module.params.get('outpost_arn')
    tags = module.params.get('tags') or {}
    name = module.params.get('name')

    volume = get_volume(module, ec2_conn)

    if module.check_mode:
        module.exit_json(changed=True, msg='Would have created a volume if not in check mode.')

    if volume is None:

        try:
            changed = True
            additional_params = dict()

            if volume_size:
                additional_params['Size'] = int(volume_size)

            if kms_key_id:
                additional_params['KmsKeyId'] = kms_key_id

            if snapshot:
                additional_params['SnapshotId'] = snapshot

            if iops:
                additional_params['Iops'] = int(iops)

            # Use the default value if any iops has been specified when volume_type=gp3
            if volume_type == 'gp3' and not iops:
                additional_params['Iops'] = 3000

            if throughput:
                additional_params['Throughput'] = int(throughput)

            if multi_attach:
                additional_params['MultiAttachEnabled'] = True

            if outpost_arn:
                if is_outpost_arn(outpost_arn):
                    additional_params['OutpostArn'] = outpost_arn
                else:
                    module.fail_json('OutpostArn does not match the pattern specified in API specifications.')

            if name:
                tags['Name'] = name

            if tags:
                additional_params['TagSpecifications'] = boto3_tag_specifications(tags, types=['volume'])

            create_vol_response = ec2_conn.create_volume(
                aws_retry=True,
                AvailabilityZone=zone,
                Encrypted=encrypted,
                VolumeType=volume_type,
                **additional_params
            )

            waiter = ec2_conn.get_waiter('volume_available')
            waiter.wait(
                VolumeIds=[create_vol_response['VolumeId']],
            )
            volume = get_volume(module, ec2_conn, vol_id=create_vol_response['VolumeId'])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg='Error while creating EBS volume')

    return volume, changed


def attach_volume(module, ec2_conn, volume_dict, instance_dict, device_name):
    changed = False

    # If device_name isn't set, make a choice based on best practices here:
    # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/block-device-mapping-concepts.html

    # In future this needs to be more dynamic but combining block device mapping best practices
    # (bounds for devices, as above) with instance.block_device_mapping data would be tricky. For me ;)

    attachment_data = get_attachment_data(volume_dict, wanted_state='attached')
    if attachment_data:
        if module.check_mode:
            if attachment_data[0].get('status') in ['attached', 'attaching']:
                module.exit_json(changed=False, msg='IN CHECK MODE - volume already attached to instance: {0}.'.format(
                                 attachment_data[0].get('instance_id', None)))
        if not volume_dict['multi_attach_enabled']:
            # volumes without MultiAttach Enabled can be attached to 1 instance only
            if attachment_data[0].get('instance_id', None) != instance_dict['instance_id']:
                module.fail_json(msg="Volume {0} is already attached to another instance: {1}."
                                 .format(volume_dict['volume_id'], attachment_data[0].get('instance_id', None)))
            else:
                return volume_dict, changed

    try:
        if module.check_mode:
            module.exit_json(changed=True, msg='Would have attached volume if not in check mode.')
        attach_response = ec2_conn.attach_volume(aws_retry=True, Device=device_name,
                                                 InstanceId=instance_dict['instance_id'],
                                                 VolumeId=volume_dict['volume_id'])

        waiter = ec2_conn.get_waiter('volume_in_use')
        waiter.wait(VolumeIds=[attach_response['VolumeId']])
        changed = True

    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Error while attaching EBS volume')

    modify_dot_attribute(module, ec2_conn, instance_dict, device_name)

    volume = get_volume(module, ec2_conn, vol_id=volume_dict['volume_id'])

    return volume, changed


def modify_dot_attribute(module, ec2_conn, instance_dict, device_name):
    """ Modify delete_on_termination attribute """

    delete_on_termination = module.params.get('delete_on_termination')
    changed = False

    # volume_in_use can return *shortly* before it appears on the instance
    # description
    mapped_block_device = None
    _attempt = 0
    while mapped_block_device is None:
        _attempt += 1
        instance_dict = get_instance(module, ec2_conn=ec2_conn, instance_id=instance_dict['instance_id'])
        mapped_block_device = get_mapped_block_device(instance_dict=instance_dict, device_name=device_name)
        if mapped_block_device is None:
            if _attempt > 2:
                module.fail_json(msg='Unable to find device on instance',
                                 device=device_name, instance=instance_dict)
            time.sleep(1)

    if delete_on_termination != mapped_block_device['ebs'].get('delete_on_termination'):
        try:
            ec2_conn.modify_instance_attribute(
                aws_retry=True,
                InstanceId=instance_dict['instance_id'],
                BlockDeviceMappings=[{
                    "DeviceName": device_name,
                    "Ebs": {
                        "DeleteOnTermination": delete_on_termination
                    }
                }]
            )
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e,
                                 msg='Error while modifying Block Device Mapping of instance {0}'.format(instance_dict['instance_id']))

    return changed


def get_attachment_data(volume_dict, wanted_state=None):
    changed = False

    attachment_data = []
    if not volume_dict:
        return attachment_data
    resource = volume_dict.get('attachments', [])
    if wanted_state:
        # filter 'state', return attachment matching wanted state
        resource = [data for data in resource if data['state'] == wanted_state]

    for data in resource:
        attachment_data.append({
            'attach_time': data.get('attach_time', None),
            'device': data.get('device', None),
            'instance_id': data.get('instance_id', None),
            'status': data.get('state', None),
            'delete_on_termination': data.get('delete_on_termination', None)
        })

    return attachment_data


def detach_volume(module, ec2_conn, volume_dict):
    changed = False

    attachment_data = get_attachment_data(volume_dict, wanted_state='attached')
    # The ID of the instance must be specified if you are detaching a Multi-Attach enabled volume.
    for attachment in attachment_data:
        if module.check_mode:
            module.exit_json(changed=True, msg='Would have detached volume if not in check mode.')
        ec2_conn.detach_volume(aws_retry=True, InstanceId=attachment['instance_id'], VolumeId=volume_dict['volume_id'])
        waiter = ec2_conn.get_waiter('volume_available')
        waiter.wait(
            VolumeIds=[volume_dict['volume_id']],
        )
        changed = True

    volume_dict = get_volume(module, ec2_conn, vol_id=volume_dict['volume_id'])
    return volume_dict, changed


def get_volume_info(module, volume, tags=None):
    if not tags:
        tags = boto3_tag_list_to_ansible_dict(volume.get('tags'))
    attachment_data = get_attachment_data(volume)
    volume_info = {
        'create_time': volume.get('create_time'),
        'encrypted': volume.get('encrypted'),
        'id': volume.get('volume_id'),
        'iops': volume.get('iops'),
        'size': volume.get('size'),
        'snapshot_id': volume.get('snapshot_id'),
        'status': volume.get('state'),
        'type': volume.get('volume_type'),
        'zone': volume.get('availability_zone'),
        'attachment_set': attachment_data,
        'multi_attach_enabled': volume.get('multi_attach_enabled'),
        'tags': tags
    }

    volume_info['throughput'] = volume.get('throughput')

    return volume_info


def get_mapped_block_device(instance_dict=None, device_name=None):
    mapped_block_device = None
    if not instance_dict:
        return mapped_block_device
    if not device_name:
        return mapped_block_device

    for device in instance_dict.get('block_device_mappings', []):
        if device['device_name'] == device_name:
            mapped_block_device = device
            break

    return mapped_block_device


def ensure_tags(module, connection, res_id, res_type, tags, purge_tags):
    if module.check_mode:
        return {}, True
    changed = ensure_ec2_tags(connection, module, res_id, res_type, tags, purge_tags, ['InvalidVolume.NotFound'])
    final_tags = describe_ec2_tags(connection, module, res_id, res_type)

    return final_tags, changed


def main():
    argument_spec = dict(
        instance=dict(),
        id=dict(),
        name=dict(),
        volume_size=dict(type='int'),
        volume_type=dict(default='standard', choices=['standard', 'gp2', 'io1', 'st1', 'sc1', 'gp3', 'io2']),
        iops=dict(type='int'),
        encrypted=dict(default=False, type='bool'),
        kms_key_id=dict(),
        device_name=dict(),
        delete_on_termination=dict(default=False, type='bool'),
        zone=dict(aliases=['availability_zone', 'aws_zone', 'ec2_zone']),
        snapshot=dict(),
        state=dict(default='present', choices=['absent', 'present']),
        tags=dict(type='dict', aliases=['resource_tags']),
        modify_volume=dict(default=False, type='bool'),
        throughput=dict(type='int'),
        outpost_arn=dict(type='str'),
        purge_tags=dict(type='bool'),
        multi_attach=dict(type='bool'),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[
            ['volume_type', 'io1', ['iops']],
            ['volume_type', 'io2', ['iops']],
        ],
        supports_check_mode=True,
    )

    param_id = module.params.get('id')
    name = module.params.get('name')
    instance = module.params.get('instance')
    volume_size = module.params.get('volume_size')
    device_name = module.params.get('device_name')
    zone = module.params.get('zone')
    snapshot = module.params.get('snapshot')
    state = module.params.get('state')
    tags = module.params.get('tags')
    iops = module.params.get('iops')
    volume_type = module.params.get('volume_type')
    throughput = module.params.get('throughput')
    multi_attach = module.params.get('multi_attach')

    if module.params.get('purge_tags') is None:
        module.deprecate(
            'The purge_tags parameter currently defaults to False.'
            ' For consistency across the collection, this default value'
            ' will change to True in release 5.0.0.',
            version='5.0.0', collection_name='amazon.aws')
        module.params['purge_tags'] = False

    # Ensure we have the zone or can get the zone
    if instance is None and zone is None and state == 'present':
        module.fail_json(msg="You must specify either instance or zone")

    # Set volume detach flag
    if instance == 'None' or instance == '':
        instance = None
        detach_vol_flag = True
    else:
        detach_vol_flag = False

    if iops:
        if volume_type in ('gp2', 'st1', 'sc1', 'standard'):
            module.fail_json(msg='IOPS is not supported for gp2, st1, sc1, or standard volumes.')

        if volume_type == 'gp3' and (int(iops) < 3000 or int(iops) > 16000):
            module.fail_json(msg='For a gp3 volume type, IOPS values must be between 3000 and 16000.')

        if volume_type in ('io1', 'io2') and (int(iops) < 100 or int(iops) > 64000):
            module.fail_json(msg='For io1 and io2 volume types, IOPS values must be between 100 and 64000.')

    if throughput:
        if volume_type != 'gp3':
            module.fail_json(msg='Throughput is only supported for gp3 volume.')
        if throughput < 125 or throughput > 1000:
            module.fail_json(msg='Throughput values must be between 125 and 1000.')

    if multi_attach is True and volume_type not in ('io1', 'io2'):
        module.fail_json(msg='multi_attach is only supported for io1 and io2 volumes.')

    # Set changed flag
    changed = False

    ec2_conn = module.client('ec2', AWSRetry.jittered_backoff())

    # Here we need to get the zone info for the instance. This covers situation where
    # instance is specified but zone isn't.
    # Useful for playbooks chaining instance launch with volume create + attach and where the
    # zone doesn't matter to the user.
    inst = None

    # Delaying the checks until after the instance check allows us to get volume ids for existing volumes
    # without needing to pass an unused volume_size
    if not volume_size and not (param_id or name or snapshot):
        module.fail_json(msg="You must specify volume_size or identify an existing volume by id, name, or snapshot")

    # Try getting volume
    volume = get_volume(module, ec2_conn, fail_on_not_found=False)
    if state == 'present':
        if instance:
            inst = get_instance(module, ec2_conn, instance_id=instance)
            zone = inst['placement']['availability_zone']

            # Use platform attribute to guess whether the instance is Windows or Linux
            if device_name is None:
                if inst.get('platform', '') == 'Windows':
                    device_name = '/dev/xvdf'
                else:
                    device_name = '/dev/sdf'

            # Check if there is a volume already mounted there.
            mapped_device = get_mapped_block_device(instance_dict=inst, device_name=device_name)
            if mapped_device:
                other_volume_mapped = False

                if volume:
                    if volume['volume_id'] != mapped_device['ebs']['volume_id']:
                        other_volume_mapped = True
                else:
                    # No volume found so this is another volume
                    other_volume_mapped = True

                if other_volume_mapped:
                    module.exit_json(
                        msg="Volume mapping for {0} already exists on instance {1}".format(device_name, instance),
                        volume_id=mapped_device['ebs']['volume_id'],
                        found_volume=volume,
                        device=device_name,
                        changed=False
                    )

        final_tags = None
        tags_changed = False

        if volume:
            volume, changed = update_volume(module, ec2_conn, volume)
            if name:
                tags['Name'] = name
            final_tags, tags_changed = ensure_tags(module, ec2_conn, volume['volume_id'], 'volume', tags, module.params.get('purge_tags'))
        else:
            volume, changed = create_volume(module, ec2_conn, zone=zone)

        if detach_vol_flag:
            volume, attach_changed = detach_volume(module, ec2_conn, volume_dict=volume)
        elif inst is not None:
            volume, attach_changed = attach_volume(module, ec2_conn, volume_dict=volume, instance_dict=inst, device_name=device_name)
        else:
            attach_changed = False

        # Add device, volume_id and volume_type parameters separately to maintain backward compatibility
        volume_info = get_volume_info(module, volume, tags=final_tags)

        if tags_changed or attach_changed:
            changed = True

        module.exit_json(changed=changed, volume=volume_info, device=device_name,
                         volume_id=volume_info['id'], volume_type=volume_info['type'])
    elif state == 'absent':
        if not name and not param_id:
            module.fail_json('A volume name or id is required for deletion')
        if volume:
            if module.check_mode:
                module.exit_json(changed=True, msg='Would have deleted volume if not in check mode.')
            detach_volume(module, ec2_conn, volume_dict=volume)
            changed = delete_volume(module, ec2_conn, volume_id=volume['volume_id'])
        module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
