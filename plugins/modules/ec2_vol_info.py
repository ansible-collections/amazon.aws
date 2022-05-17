#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: ec2_vol_info
version_added: 1.0.0
short_description: Gather information about ec2 volumes in AWS
description:
    - Gather information about ec2 volumes in AWS.
author: "Rob White (@wimnat)"
options:
  filters:
    type: dict
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
      - See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVolumes.html) for possible filters.
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather information about all volumes
- amazon.aws.ec2_vol_info:

# Gather information about a particular volume using volume ID
- amazon.aws.ec2_vol_info:
    filters:
      volume-id: vol-00112233

# Gather information about any volume with a tag key Name and value Example
- amazon.aws.ec2_vol_info:
    filters:
      "tag:Name": Example

# Gather information about any volume that is attached
- amazon.aws.ec2_vol_info:
    filters:
      attachment.status: attached

# Gather information about all volumes related to an EC2 Instance
# register information to `volumes` variable
# Replaces functionality of `amazon.aws.ec2_vol` - `state: list`
- name: get volume(s) info from EC2 Instance
  amazon.aws.ec2_vol_info:
    filters:
      attachment.instance-id: "i-000111222333"
  register: volumes

'''

RETURN = '''
volumes:
    description: Volumes that match the provided filters. Each element consists of a dict with all the information related to that volume.
    type: list
    elements: dict
    returned: always
    contains:
        attachment_set:
            description:
                - Information about the volume attachments.
                - This was changed in version 2.0.0 from a dictionary to a list of dictionaries.
            type: list
            elements: dict
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
            sample: "2015-10-21T14:36:08.870Z"
        encrypted:
            description: Indicates whether the volume is encrypted.
            type: bool
            sample: False
        id:
            description: The ID of the volume.
            type: str
            sample: "vol-35b333d9"
        iops:
            description: The number of I/O operations per second (IOPS) that the volume supports.
            type: int
            sample: null
        size:
            description: The size of the volume, in GiBs.
            type: int
            sample: 1
        snapshot_id:
            description: The snapshot from which the volume was created, if applicable.
            type: str
            sample: ""
        status:
            description: The volume state.
            type: str
            sample: "in-use"
        tags:
            description: Any tags assigned to the volume.
            type: dict
            sample: {
                env: "dev"
                }
        type:
            description: The volume type. This can be gp2, io1, st1, sc1, or standard.
            type: str
            sample: "standard"
        zone:
            description: The Availability Zone of the volume.
            type: str
            sample: "us-east-1b"
        throughput:
            description: The throughput that the volume supports, in MiB/s.
            type: int
            sample: 131
'''

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict


def get_volume_info(volume, region):

    attachment = volume["attachments"]

    attachment_data = []
    for data in volume["attachments"]:
        attachment_data.append({
            'attach_time': data.get('attach_time', None),
            'device': data.get('device', None),
            'instance_id': data.get('instance_id', None),
            'status': data.get('state', None),
            'delete_on_termination': data.get('delete_on_termination', None)
        })

    volume_info = {
        'create_time': volume["create_time"],
        'id': volume["volume_id"],
        'encrypted': volume["encrypted"],
        'iops': volume["iops"] if "iops" in volume else None,
        'size': volume["size"],
        'snapshot_id': volume["snapshot_id"],
        'status': volume["state"],
        'type': volume["volume_type"],
        'zone': volume["availability_zone"],
        'region': region,
        'attachment_set': attachment_data,
        'tags': boto3_tag_list_to_ansible_dict(volume['tags']) if "tags" in volume else None
    }

    if 'throughput' in volume:
        volume_info['throughput'] = volume["throughput"]

    return volume_info


@AWSRetry.jittered_backoff()
def describe_volumes_with_backoff(connection, filters):
    paginator = connection.get_paginator('describe_volumes')
    return paginator.paginate(Filters=filters).build_full_result()


def list_ec2_volumes(connection, module):

    # Replace filter key underscores with dashes, for compatibility, except if we're dealing with tags
    sanitized_filters = module.params.get("filters")
    for key in list(sanitized_filters):
        if not key.startswith("tag:"):
            sanitized_filters[key.replace("_", "-")] = sanitized_filters.pop(key)
    volume_dict_array = []

    try:
        all_volumes = describe_volumes_with_backoff(connection, ansible_dict_to_boto3_filter_list(sanitized_filters))
    except ClientError as e:
        module.fail_json_aws(e, msg="Failed to describe volumes.")

    for volume in all_volumes["Volumes"]:
        volume = camel_dict_to_snake_dict(volume, ignore_list=['Tags'])
        volume_dict_array.append(get_volume_info(volume, module.region))
    module.exit_json(volumes=volume_dict_array)


def main():
    argument_spec = dict(filters=dict(default={}, type='dict'))

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client('ec2')

    list_ec2_volumes(connection, module)


if __name__ == '__main__':
    main()
