#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: ec2_spot_instance
version_added: 2.0.0
short_description: request, stop, reboot or cancel spot instance
description:
    - Creates, stops, reboots or cancels spot instances.
    - >
      Note: This module uses the boto3 Python module to interact with the EC2 API.
      M(amazon.aws.ec2) will still support the older boto Python module to interact with spot instances.
options:
  zone_group:
    description:
      - Name for logical grouping of spot requests.
      - All spot instances in the request are launched in the same availability zone. 
    type: str
  block_duration:
    description:
      - The required duration for spot instances in minutes (in multiple of 60 - 60, 120, 180, 240, 300, or 360)
      - Zone group or Launch group cannot be specified along with this attribute.
    type: int
    sample: 60
  client_token:
    description: The idempotency token you provided when you launched the instance, if applicable.
    type: str
    returned: always
    sample: ""
  count:
    description:
      - Number of instances to launch.
    default: 1
    type: int
  interruption:
    description:
      - The behavior when a Spot Instance is interrupted.
    choices: [ "hibernate", "stop", "terminate" ]
    type: str
  launch_group:
    description:
      - Launch group for spot requests, see U(https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/how-spot-instances-work.html#spot-launch-group).
    type: str
  launch_specification:
    description: 
      - The launch specification.
    type: dict
  group_id:
    description:
      - Security group id (or list of ids) to use with the instance.
    type: list
    elements: str
  group:
    description:
      - Security group (or list of groups) to use with the instance.
    aliases: [ 'groups' ]
    type: list
    elements: str
  price:
    description:
      - Maximum spot price to bid. If not set, a regular on-demand instance is requested.
      - A spot request is made with this maximum bid. When it is filled, the instance is started.
    type: str
  request_type:
    description:
      - The type of spot request.
      - After being interrupted a C(persistent) spot instance will be started once there is capacity to fill the request again.
    default: "one-time"
    choices: [ "one-time", "persistent" ]
    type: str
  state:
    description:
      - Create, terminate, start, stop or restart instances. The state 'restarted' was added in Ansible 2.2.
      - When I(state=absent), I(instance_ids) is required.
      - When I(state=running), I(state=stopped) or I(state=restarted) then either I(instance_ids) or I(instance_tags) is required.
    default: 'present'
    choices: ['absent', 'present', 'restarted', 'running', 'stopped']
    type: str
  key_name:
    description:
      - Key pair to use on the instance.
      - The SSH key must already exist in AWS in order to use this argument.
      - Keys can be created / deleted using the M(amazon.aws.ec2_key) module.
    aliases: ['keypair']
    type: str
  user_data:
    description:
      - Opaque blob of data which is made available to the EC2 instance.
    type: str
  volumes:
    description:
      - A list of hash/dictionaries of volumes to add to the new instance.
    type: list
    elements: dict
  ebs_optimized:
    description:
      - Whether instance is using optimized EBS volumes, see U(https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSOptimized.html).
    default: false
    type: bool
  instance_profile_name:
    description:
      - Name of the IAM instance profile (i.e. what the EC2 console refers to as an "IAM Role") to use. Boto library must be 2.5.0+.
    type: str
  image_id:
    description:
      -  The ID of the AMI.
    type: str
  instance_type:
    description:
      - Instance type to use for the instance, see U(https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-types.html).
      - Required when creating a new instance.
    type: str
  kernel:
    description:
      - Kernel eki to use for the instance.
    type: str
  network_interfaces:
    description:
      - A list of existing network interfaces to attach to the instance at launch. When specifying existing network interfaces,
        none of the I(assign_public_ip), I(private_ip), I(vpc_subnet_id), I(group), or I(group_id) parameters may be used. (Those parameters are
        for creating a new network interface at launch.)
    aliases: ['network_interface']
    type: list
    elements: str
  placement_group:
    description:
      - Placement group for the instance when using EC2 Clustered Compute.
    type: str
  ramdisk:
    description:
      - Ramdisk eri to use for the instance.
    type: str
  spot_price:
    description:
      - Maximum spot price to bid. If not set, a regular on-demand instance is requested.
      - A spot request is made with this maximum bid. When it is filled, the instance is started.
    type: str
  spot_type:
    description:
      - The type of spot request.
      - After being interrupted a C(persistent) spot instance will be started once there is capacity to fill the request again.
    default: "one-time"
    choices: [ "one-time", "persistent" ]
    type: str
  monitoring:
    description:
      - Enable detailed monitoring (CloudWatch) for the instance.
    type: bool
    default: false
  valid_from:
    description:
      -  The start date of the request. If this is a one-time request, the request becomes active at this date and time and remains active until all instances launch, the request expires, or the request is canceled.
      -  If the request is persistent, the request becomes active at this date and time and remains active until it expires or is canceled.      
  valid_until:
    description:
      - The end date of the request, 
'''
import time
import datetime

try:
    import botocore
except ImportError:
    pass  # Taken care of by AnsibleAWSModule
from ..module_utils.core import AnsibleAWSModule
from ..module_utils.ec2 import AWSRetry
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict


def request_spot_instance(module, connection):
    launch_specification = module.params.get('launch_specification')
    launch_specification = snake_dict_to_camel_dict(launch_specification, capitalize_first=True)
    params = dict()
    params['LaunchSpecification'] = launch_specification
    import q
    q(params['LaunchSpecification'])
    request_spot_instance_response = connection.request_spot_instances(**params)
    return request_spot_instance_response


def main():
    argument_spec = dict(
        zone_group=dict(type='str'),
        block_duration=dict(type='int'),
        count=dict(type='int', default='1'),
        interruption=dict(type='str'),
        launch_group=dict(type='str'),
        launch_specification=dict(),
        price=dict(type='str'),
        request_type=dict(default='one-time', choices=["one-time", "persistent"]),
        state=dict(default='present', choices=['present', 'absent', 'running', 'restarted', 'stopped']),
        group_id=dict(type='list', elements='str'),
        group=dict(type='list', elements='str'),
        key_name=dict(aliases=['keypair']),
        user_data=dict(),
        volumes=dict(type='list', elements='dict'),
        ebs_optimized=dict(type='bool', default=False),
        instance_profile_name=dict(),
        image_id=dict(type='string'),
        instance_type=dict(type='string'),
        kernel=dict(),
        network_interfaces=dict(type='list', elements='str', aliases=['network_interface']),
        placement_group=dict(),
        ramdisk=dict(),
        spot_price=dict(),
        spot_type=dict(default='one-time', choices=["one-time", "persistent"]),
        monitoring=dict(type='bool', default=False),
        valid_from=dict(),
        valid_until=dict()

        # vpc_subnet_id=dict(),
        # launched_availibility_zone=dict(type='string'),
        # product_description=dict(type='string'),
        # spot_launch_group=dict(),
        # image=dict(),
        # wait=dict(type='bool', default=False),
        # wait_timeout=dict(type='int', default=300),
        # spot_wait_timeout=dict(type='int', default=600),
        # instance_tags=dict(type='dict'),
        # private_ip=dict(),
        # instance_ids=dict(type='list', elements='str', aliases=['instance_id']),
        # source_dest_check=dict(type='bool', default=None),
        # instance_initiated_shutdown_behavior=dict(default='stop', choices=['stop', 'terminate']),
        # exact_count=dict(type='int', default=None),
        # count_tag=dict(type='raw'),
        # tenancy=dict(default='default', choices=['default', 'dedicated']),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        check_boto3=False,
        mutually_exclusive=[
            ['block_duration', 'zone_group'],
            ['block_duration', 'launch_group'],
        ],
        supports_check_mode=True
    )

    connection = module.client('ec2', AWSRetry.jittered_backoff())

    state = module.params['state']

    if state == 'present':
        response = request_spot_instance(module, connection)


if __name__ == '__main__':
    main()
