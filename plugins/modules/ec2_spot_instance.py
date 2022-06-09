#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: ec2_spot_instance
version_added: 2.0.0
short_description: Request, stop, reboot or cancel spot instance
description:
    - Creates or cancels spot instance requests.
author:
  - Sri Rachana Achyuthuni (@srirachanaachyuthuni)
options:
  zone_group:
    description:
      - Name for logical grouping of spot requests.
      - All spot instances in the request are launched in the same availability zone.
    type: str
  client_token:
    description: The idempotency token you provided when you launched the instance, if applicable.
    type: str
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
    default: terminate
  launch_group:
    description:
      - Launch group for spot requests, see U(https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/how-spot-instances-work.html#spot-launch-group).
    type: str
  launch_specification:
    description:
      - The launch specification.
    type: dict
    suboptions:
      security_group_ids:
        description:
          - Security group id (or list of ids) to use with the instance.
        type: list
        elements: str
      security_groups:
        description:
          - Security group name (or list of group names) to use with the instance.
          - Only supported with EC2 Classic. To launch in a VPC, use C(group_id)
        type: list
        elements: str
      key_name:
        description:
          - Key to use on the instance.
          - The SSH key must already exist in AWS in order to use this argument.
          - Keys can be created / deleted using the M(amazon.aws.ec2_key) module.
        type: str
      subnet_id:
        description:
          - The ID of the subnet in which to launch the instance.
        type: str
      user_data:
        description:
          - The base64-encoded user data for the instance. User data is limited to 16 KB.
        type: str
      block_device_mappings:
        description:
          - A list of hash/dictionaries of volumes to add to the new instance.
        type: list
        elements: dict
        suboptions:
          device_name:
            description:
              - The device name (for example, /dev/sdh or xvdh ).
            type: str
          virtual_name:
            description:
              - The virtual device name
            type: str
          ebs:
            description:
              - Parameters used to automatically set up EBS volumes when the instance is launched,
                see U(https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.request_spot_instances)
            type: dict
          no_device:
            description:
              - To omit the device from the block device mapping, specify an empty string.
            type: str
      ebs_optimized:
        description:
          - Whether instance is using optimized EBS volumes, see U(https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSOptimized.html).
        default: false
        type: bool
      iam_instance_profile:
        description:
          - The IAM instance profile.
        type: dict
        suboptions:
          arn:
            description:
              - The Amazon Resource Name (ARN) of the instance profile.
              - Only one of I(arn) or I(name) may be specified.
            type: str
          name:
            description:
              - The name of the instance profile.
              - Only one of I(arn) or I(name) may be specified.
            type: str
      image_id:
        description:
          - The ID of the AMI.
        type: str
      instance_type:
        description:
          - Instance type to use for the instance, see U(https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-types.html).
          - Required when creating a new instance.
        type: str
      kernel_id:
        description:
          - The ID of the kernel.
        type: str
      network_interfaces:
        description:
          - One or more network interfaces. If you specify a network interface, you must specify subnet IDs and security group IDs using the network interface.
        type: list
        elements: dict
        suboptions:
          associate_public_ip_address:
            description:
              - Indicates whether to assign a public IPv4 address to an instance you launch in a VPC.
            type: bool
          delete_on_termination:
            description:
              - If set to true , the interface is deleted when the instance is terminated.
                You can specify true only if creating a new network interface when launching an instance.
            type: bool
          description:
            description:
              - The description of the network interface. Applies only if creating a network interface when launching an instance.
            type: str
          device_index:
            description:
              - The position of the network interface in the attachment order. A primary network interface has a device index of 0.
              - If you specify a network interface when launching an instance, you must specify the device index.
            type: int
          groups:
            description:
              - The IDs of the security groups for the network interface. Applies only if creating a network interface when launching an instance.
            type: list
            elements: str
          ipv6_address_count:
            description:
              - A number of IPv6 addresses to assign to the network interface
            type: int
          ipv6_addresses:
            description:
              - One or more IPv6 addresses to assign to the network interface.
            type: list
            elements: dict
            suboptions:
              ipv6address:
                description: The IPv6 address.
                type: str
          network_interface_id:
            description:
              - The ID of the network interface.
            type: str
          private_ip_address:
            description:
              - The private IPv4 address of the network interface
            type: str
          private_ip_addresses:
            description:
              - One or more private IPv4 addresses to assign to the network interface
            type: list
            elements: dict
          secondary_private_ip_address_count:
            description:
              - The number of secondary private IPv4 addresses.
            type: int
          subnet_id:
            description:
              - The ID of the subnet associated with the network interface
            type: str
          associate_carrier_ip_address:
            description:
              - Indicates whether to assign a carrier IP address to the network interface.
            type: bool
          interface_type:
            description:
              - The type of network interface.
            type: str
            choices: ['interface', 'efa']
          network_card_index:
            description:
              - The index of the network card.
            type: int
          ipv4_prefixes:
            description:
              - One or more IPv4 delegated prefixes to be assigned to the network interface.
            type: list
            elements: dict
          ipv4_prefix_count:
            description:
              - The number of IPv4 delegated prefixes to be automatically assigned to the network interface
            type: int
          ipv6_prefixes:
            description:
              - One or more IPv6 delegated prefixes to be assigned to the network interface
            type: list
            elements: dict
          ipv6_prefix_count:
            description:
              - The number of IPv6 delegated prefixes to be automatically assigned to the network interface
            type: int
      placement:
        description:
          - The placement information for the instance.
        type: dict
        suboptions:
          availability_zone:
            description:
              - The Availability Zone.
            type: str
          group_name:
            description:
              - The name of the placement group.
            type: str
          tenancy:
            description:
              - the tenancy of the host
            type: str
            choices: ['default', 'dedicated', 'host']
            default: default
      ramdisk_id:
        description:
          - The ID of the RAM disk.
        type: str
      monitoring:
        description:
          - Indicates whether basic or detailed monitoring is enabled for the instance.
        type: dict
        suboptions:
          enabled:
            description:
              - Indicates whether detailed monitoring is enabled. Otherwise, basic monitoring is enabled.
            type: bool
            default: false
  state:
    description:
      - Whether the spot request should be created or removed.
      - When I(state=present), I(launch_specification) is required.
      - When I(state=absent), I(spot_instance_request_ids) is required.
    default: 'present'
    choices: [ 'absent', 'present' ]
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
    default: 'one-time'
    choices: [ "one-time", "persistent" ]
    type: str
  tags:
    description:
      - A dictionary of key-value pairs for tagging the Spot Instance request on creation.
    type: dict
  spot_instance_request_ids:
    description:
      - List of strings with IDs of spot requests to be cancelled
    default: []
    type: list
    elements: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Simple Spot Request Creation
  amazon.aws.ec2_spot_instance:
    launch_specification:
      image_id: ami-123456789
      key_name: my-keypair
      instance_type: t2.medium

- name: Spot Request Creation with more options
  amazon.aws.ec2_spot_instance:
    launch_specification:
      image_id: ami-123456789
      key_name: my-keypair
      instance_type: t2.medium
      subnet_id: subnet-12345678
      block_device_mappings:
        - device_name: /dev/sdb
          ebs:
            delete_on_termination: True
            volume_type: gp3
            volume_size: 5
        - device_name: /dev/sdc
          ebs:
            delete_on_termination: True
            volume_type: io2
            volume_size: 30
      network_interfaces:
        - associate_public_ip_address: False
          delete_on_termination: True
          device_index: 0
      placement:
        availability_zone: us-west-2a
      monitoring:
        enabled: False
    spot_price: 0.002
    tags:
      Environment: Testing

- name: Spot Request Termination
  amazon.aws.ec2_spot_instance:
    spot_instance_request_ids: ['sir-12345678', 'sir-abcdefgh']
    state: absent
'''

RETURN = '''
spot_request:
    description: The spot instance request details after creation
    returned: when success
    type: dict
    sample: {
        "create_time": "2021-08-23T22:59:12+00:00",
        "instance_interruption_behavior": "terminate",
        "launch_specification": {
            "block_device_mappings": [
                {
                    "device_name": "/dev/sdb",
                    "ebs": {
                        "delete_on_termination": true,
                        "volume_size": 5,
                        "volume_type": "gp3"
                    }
                }
            ],
            "ebs_optimized": false,
            "iam_instance_profile": {
                "arn": "arn:aws:iam::EXAMPLE:instance-profile/myinstanceprofile"
            },
            "image_id": "ami-083ac7c7ecf9bb9b0",
            "instance_type": "t2.small",
            "key_name": "mykey",
            "monitoring": {
                "enabled": false
            },
            "network_interfaces": [
                {
                    "associate_public_ip_address": false,
                    "delete_on_termination": true,
                    "device_index": 0
                }
            ],
            "placement": {
                "availability_zone": "us-west-2a",
                "tenancy": "default"
            },
            "security_groups": [
                {
                    "group_name": "default"
                }
            ]
        },
        "product_description": "Linux/UNIX",
        "spot_instance_request_id": "sir-1234abcd",
        "spot_price": "0.00600",
        "state": "open",
        "status": {
            "code": "pending-evaluation",
            "message": "Your Spot request has been submitted for review, and is pending evaluation.",
            "update_time": "2021-08-23T22:59:12+00:00"
        },
        "type": "one-time"

        }

cancelled_spot_request:
    description: The spot instance request details that has been cancelled
    returned: always
    type: str
    sample: 'Spot requests with IDs: sir-1234abcd have been cancelled'
'''
# TODO: add support for datetime-based parameters
# import datetime
# import time

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code


def build_launch_specification(launch_spec):
    """
    Remove keys that have a value of None from Launch Specification
    Descend into these subkeys:
    network_interfaces
    block_device_mappings
    monitoring
    placement
    iam_instance_profile
    """
    assigned_keys = dict((k, v) for k, v in launch_spec.items() if v is not None)

    sub_key_to_build = ['placement', 'iam_instance_profile', 'monitoring']
    for subkey in sub_key_to_build:
        if launch_spec[subkey] is not None:
            assigned_keys[subkey] = dict((k, v) for k, v in launch_spec[subkey].items() if v is not None)

    if launch_spec['network_interfaces'] is not None:
        interfaces = []
        for iface in launch_spec['network_interfaces']:
            interfaces.append(dict((k, v) for k, v in iface.items() if v is not None))
        assigned_keys['network_interfaces'] = interfaces

    if launch_spec['block_device_mappings'] is not None:
        block_devs = []
        for dev in launch_spec['block_device_mappings']:
            block_devs.append(
                dict((k, v) for k, v in dev.items() if v is not None))
        assigned_keys['block_device_mappings'] = block_devs

    return snake_dict_to_camel_dict(assigned_keys, capitalize_first=True)


def request_spot_instances(module, connection):

    # connection.request_spot_instances() always creates a new spot request
    changed = True

    if module.check_mode:
        module.exit_json(changed=changed)

    params = {}

    if module.params.get('launch_specification'):
        params['LaunchSpecification'] = build_launch_specification(module.params.get('launch_specification'))

    if module.params.get('zone_group'):
        params['AvailabilityZoneGroup'] = module.params.get('zone_group')

    if module.params.get('count'):
        params['InstanceCount'] = module.params.get('count')

    if module.params.get('launch_group'):
        params['LaunchGroup'] = module.params.get('launch_group')

    if module.params.get('spot_price'):
        params['SpotPrice'] = module.params.get('spot_price')

    if module.params.get('spot_type'):
        params['Type'] = module.params.get('spot_type')

    if module.params.get('client_token'):
        params['ClientToken'] = module.params.get('client_token')

    if module.params.get('interruption'):
        params['InstanceInterruptionBehavior'] = module.params.get('interruption')

    if module.params.get('tags'):
        params['TagSpecifications'] = [{
            'ResourceType': 'spot-instances-request',
            'Tags': ansible_dict_to_boto3_tag_list(module.params.get('tags')),
        }]

    # TODO: add support for datetime-based parameters
    # params['ValidFrom'] = module.params.get('valid_from')
    # params['ValidUntil'] = module.params.get('valid_until')

    try:
        request_spot_instance_response = (connection.request_spot_instances(aws_retry=True, **params))['SpotInstanceRequests'][0]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Error while creating the spot instance request')

    request_spot_instance_response['Tags'] = boto3_tag_list_to_ansible_dict(request_spot_instance_response.get('Tags', []))
    spot_request = camel_dict_to_snake_dict(request_spot_instance_response, ignore_list=['Tags'])
    module.exit_json(spot_request=spot_request, changed=changed)


def cancel_spot_instance_requests(module, connection):

    changed = False
    spot_instance_request_ids = module.params.get('spot_instance_request_ids')
    requests_exist = dict()
    try:
        paginator = connection.get_paginator('describe_spot_instance_requests').paginate(SpotInstanceRequestIds=spot_instance_request_ids,
                                                                                         Filters=[{'Name': 'state', 'Values': ['open', 'active']}])
        jittered_retry = AWSRetry.jittered_backoff()
        requests_exist = jittered_retry(paginator.build_full_result)()
    except is_boto3_error_code('InvalidSpotInstanceRequestID.NotFound'):
        requests_exist['SpotInstanceRequests'] = []
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failure when describing spot requests")

    try:
        if len(requests_exist['SpotInstanceRequests']) > 0:
            changed = True
            if module.check_mode:
                module.exit_json(changed=changed,
                                 msg='Would have cancelled Spot request {0}'.format(spot_instance_request_ids))

            connection.cancel_spot_instance_requests(aws_retry=True, SpotInstanceRequestIds=module.params.get('spot_instance_request_ids'))
            module.exit_json(changed=changed, msg='Cancelled Spot request {0}'.format(module.params.get('spot_instance_request_ids')))
        else:
            module.exit_json(changed=changed, msg='Spot request not found or already cancelled')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Error while cancelling the spot instance request')


def main():
    network_interface_options = dict(
        associate_public_ip_address=dict(type='bool'),
        delete_on_termination=dict(type='bool'),
        description=dict(type='str'),
        device_index=dict(type='int'),
        groups=dict(type='list', elements='str'),
        ipv6_address_count=dict(type='int'),
        ipv6_addresses=dict(type='list', elements='dict', options=dict(ipv6address=dict(type='str'))),
        network_interface_id=dict(type='str'),
        private_ip_address=dict(type='str'),
        private_ip_addresses=dict(type='list', elements='dict'),
        secondary_private_ip_address_count=dict(type='int'),
        subnet_id=dict(type='str'),
        associate_carrier_ip_address=dict(type='bool'),
        interface_type=dict(type='str', choices=['interface', 'efa']),
        network_card_index=dict(type='int'),
        ipv4_prefixes=dict(type='list', elements='dict'),
        ipv4_prefix_count=dict(type='int'),
        ipv6_prefixes=dict(type='list', elements='dict'),
        ipv6_prefix_count=dict(type='int')
    )
    block_device_mappings_options = dict(
        device_name=dict(type='str'),
        virtual_name=dict(type='str'),
        ebs=dict(type='dict'),
        no_device=dict(type='str'),
    )
    monitoring_options = dict(
        enabled=dict(type='bool', default=False)
    )
    placement_options = dict(
        availability_zone=dict(type='str'),
        group_name=dict(type='str'),
        tenancy=dict(type='str', choices=['default', 'dedicated', 'host'], default='default')
    )
    iam_instance_profile_options = dict(
        arn=dict(type='str'),
        name=dict(type='str')
    )
    launch_specification_options = dict(
        security_group_ids=dict(type='list', elements='str'),
        security_groups=dict(type='list', elements='str'),
        block_device_mappings=dict(type='list', elements='dict', options=block_device_mappings_options),
        ebs_optimized=dict(type='bool', default=False),
        iam_instance_profile=dict(type='dict', options=iam_instance_profile_options),
        image_id=dict(type='str'),
        instance_type=dict(type='str'),
        kernel_id=dict(type='str'),
        key_name=dict(type='str'),
        monitoring=dict(type='dict', options=monitoring_options),
        network_interfaces=dict(type='list', elements='dict', options=network_interface_options, default=[]),
        placement=dict(type='dict', options=placement_options),
        ramdisk_id=dict(type='str'),
        user_data=dict(type='str'),
        subnet_id=dict(type='str')
    )

    argument_spec = dict(
        zone_group=dict(type='str'),
        client_token=dict(type='str', no_log=False),
        count=dict(type='int', default=1),
        interruption=dict(type='str', default="terminate", choices=['hibernate', 'stop', 'terminate']),
        launch_group=dict(type='str'),
        launch_specification=dict(type='dict', options=launch_specification_options),
        state=dict(default='present', choices=['present', 'absent']),
        spot_price=dict(type='str'),
        spot_type=dict(default='one-time', choices=["one-time", "persistent"]),
        tags=dict(type='dict'),
        # valid_from=dict(type='datetime', default=datetime.datetime.now()),
        # valid_until=dict(type='datetime', default=(datetime.datetime.now() + datetime.timedelta(minutes=60))
        spot_instance_request_ids=dict(type='list', elements='str'),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    connection = module.client('ec2', retry_decorator=AWSRetry.jittered_backoff())

    state = module.params['state']

    if state == 'present':
        request_spot_instances(module, connection)

    if state == 'absent':
        cancel_spot_instance_requests(module, connection)


if __name__ == '__main__':
    main()
