#!/usr/bin/python
# encoding: utf-8

# (c) 2015, Jose Armesto <jose@armesto.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: autoscaling_launch_config_find
version_added: 1.0.0
short_description: Find AWS Autoscaling Launch Configurations
description:
  - Returns list of matching Launch Configurations for a given name, along with other useful information.
  - Results can be sorted and sliced.
  - Based on the work by Tom Bamford U(https://github.com/tombamford).
  - Prior to release 5.0.0 this module was called C(community.aws.ec2_lc_find).
    The usage did not change.
author:
  - "Jose Armesto (@fiunchinho)"
options:
  name_regex:
    description:
      - A Launch Configuration to match.
      - It'll be compiled as regex.
    required: True
    type: str
  sort_order:
    description:
      - Order in which to sort results.
    choices: ['ascending', 'descending']
    default: 'ascending'
    type: str
  limit:
    description:
      - How many results to show.
      - Corresponds to Python slice notation like list[:limit].
    type: int
extends_documentation_fragment:
  - amazon.aws.ec2
  - amazon.aws.aws
  - amazon.aws.boto3
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Search for the Launch Configurations that start with "app"
  community.aws.autoscaling_launch_config_find:
    name_regex: app.*
    sort_order: descending
    limit: 2
'''

RETURN = '''
image_id:
    description: AMI id
    returned: when Launch Configuration was found
    type: str
    sample: "ami-0d75df7e"
user_data:
    description: User data used to start instance
    returned: when Launch Configuration was found
    type: str
    sample: "ZXhwb3J0IENMT1VE"
name:
    description: Name of the Launch Configuration
    returned: when Launch Configuration was found
    type: str
    sample: "myapp-v123"
arn:
    description: Name of the AMI
    returned: when Launch Configuration was found
    type: str
    sample: "arn:aws:autoscaling:eu-west-1:12345:launchConfiguration:d82f050e-e315:launchConfigurationName/yourproject"
instance_type:
    description: Type of ec2 instance
    returned: when Launch Configuration was found
    type: str
    sample: "t2.small"
created_time:
    description: When it was created
    returned: when Launch Configuration was found
    type: str
    sample: "2016-06-29T14:59:22.222000+00:00"
ebs_optimized:
    description: Launch Configuration EBS optimized property
    returned: when Launch Configuration was found
    type: bool
    sample: False
instance_monitoring:
    description: Launch Configuration instance monitoring property
    returned: when Launch Configuration was found
    type: str
    sample: {"Enabled": false}
classic_link_vpc_security_groups:
    description: Launch Configuration classic link vpc security groups property
    returned: when Launch Configuration was found
    type: list
    sample: []
block_device_mappings:
    description: Launch Configuration block device mappings property
    returned: when Launch Configuration was found
    type: list
    sample: []
keyname:
    description: Launch Configuration ssh key
    returned: when Launch Configuration was found
    type: str
    sample: mykey
security_groups:
    description: Launch Configuration security groups
    returned: when Launch Configuration was found
    type: list
    sample: []
kernel_id:
    description: Launch Configuration kernel to use
    returned: when Launch Configuration was found
    type: str
    sample: ''
ram_disk_id:
    description: Launch Configuration ram disk property
    returned: when Launch Configuration was found
    type: str
    sample: ''
associate_public_address:
    description: Assign public address or not
    returned: when Launch Configuration was found
    type: bool
    sample: True
...
'''
import re

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule


def find_launch_configs(client, module):
    name_regex = module.params.get('name_regex')
    sort_order = module.params.get('sort_order')
    limit = module.params.get('limit')

    paginator = client.get_paginator('describe_launch_configurations')

    response_iterator = paginator.paginate(
        PaginationConfig={
            'MaxItems': 1000,
            'PageSize': 100
        }
    )

    results = []

    for response in response_iterator:
        response['LaunchConfigurations'] = filter(lambda lc: re.compile(name_regex).match(lc['LaunchConfigurationName']),
                                                  response['LaunchConfigurations'])

        for lc in response['LaunchConfigurations']:
            data = {
                'name': lc['LaunchConfigurationName'],
                'arn': lc['LaunchConfigurationARN'],
                'created_time': lc['CreatedTime'],
                'user_data': lc['UserData'],
                'instance_type': lc['InstanceType'],
                'image_id': lc['ImageId'],
                'ebs_optimized': lc['EbsOptimized'],
                'instance_monitoring': lc['InstanceMonitoring'],
                'classic_link_vpc_security_groups': lc['ClassicLinkVPCSecurityGroups'],
                'block_device_mappings': lc['BlockDeviceMappings'],
                'keyname': lc['KeyName'],
                'security_groups': lc['SecurityGroups'],
                'kernel_id': lc['KernelId'],
                'ram_disk_id': lc['RamdiskId'],
                'associate_public_address': lc.get('AssociatePublicIpAddress', False),
            }

            results.append(data)

    results.sort(key=lambda e: e['name'], reverse=(sort_order == 'descending'))

    if limit:
        results = results[:int(limit)]

    module.exit_json(changed=False, results=results)


def main():
    argument_spec = dict(
        name_regex=dict(required=True),
        sort_order=dict(required=False, default='ascending', choices=['ascending', 'descending']),
        limit=dict(required=False, type='int'),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
    )

    try:
        client = module.client('autoscaling')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    find_launch_configs(client, module)


if __name__ == '__main__':
    main()
