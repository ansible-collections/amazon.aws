#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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
      user_data:
        description:
          - Opaque blob of data which is made available to the EC2 instance.
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
              - Parameters used to automatically set up EBS volumes when the instance is launched, see U(https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.request_spot_instances)
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
            type: str
          name:
            description:
              - The name of the instance profile.
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
              - If set to true , the interface is deleted when the instance is terminated. You can specify true only if creating a new network interface when launching an instance.
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
          secondary_private_address_count:
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
              - the tenancy of the host
            type: str
            choices: ['default'|'dedicated'|'host']
      ramdisk_id:
        description:
          - The ID of the RAM disk.
        type: str
      monitoring:
        description:
          -Indicates whether basic or detailed monitoring is enabled for the instance.
        type: dict
        suboptions:
          enabled:
            description:
              - Indicates whether detailed monitoring is enabled. Otherwise, basic monitoring is enabled.
            type: bool
            default:false
      user_data:
        description:
          - The Base64-encoded user data for the instance. User data is limited to 16 KB.
        type: str
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
      - When I(state=present), I(launch_specification) is required.
      - When I(state=absent), I(spot_instance_request_ids) is required.
    default: 'present'
    choices: ['absent', 'present']
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
  valid_from:
    description:
      -  The start date of the request. If this is a one-time request, the request becomes active at this date and time and remains active until all instances launch, the request expires, or the request is canceled.
      -  If the request is persistent, the request becomes active at this date and time and remains active until it expires or is canceled.      
  valid_until:
    description:
      - The end date of the request
  tags:
    description:
      - tag:value pairs to add to the volume after creation.
    default: []
    type: list
  spot_instance_request_ids:
    description:
        - List of strings with IDs of spot requests to be cancelled
    default: []
    type: list
'''

EXAMPLES = '''
# Simple Spot Request Creation
- hosts: localhost
  tasks:
    - name: Test EC2 spot instance module
      amazon.aws.ec2_spot_instance:
        launch_specification:
          image_id: "ami-123456789"
          key_name: "my-keypair"
          instance_type: "t2.medium"

# Simple Spot Request Termination
- hosts: localhost
  tasks:
    - name: Test EC2 spot instance cancel module
      amazon.aws.ec2_spot_instance:
        spot_instance_request_ids: ['sir-d8468pbj', 'sir-qph6aytk']
        state: 'absent'
'''

RETURN = '''
spot_request:
    description: The spot instance request details after creation
    returned: when success
    type: dict
    sample: {
            "CreateTime": "2021-07-21T18:33:47+00:00",
            "InstanceInterruptionBehavior": "terminate",
            "LaunchSpecification": {
                "ImageId": "ami-0d5eff06f840b45e9",
                "InstanceType": "t2.medium",
                "KeyName": "zuul",
                "Monitoring": {
                    "Enabled": false
                },
                "Placement": {
                    "AvailabilityZone": "us-east-1e"
                },
                "SecurityGroups": [
                    {
                        "GroupId": "sg-0fa9a734e7111af56",
                        "GroupName": "default"
                    }
                ],
                "SubnetId": "subnet-0ff1d9ce7798affb1"
            },
            "ProductDescription": "Linux/UNIX",
            "SpotInstanceRequestId": "sir-d8468pbj",
            "SpotPrice": "0.046400",
            "State": "open",
            "Status": {
                "Code": "pending-evaluation",
                "Message": "Your Spot request has been submitted for review, and is pending evaluation.",
                "UpdateTime": "2021-07-21T18:33:47+00:00"
            },
            "Type": "one-time"
        }

cancelled_spot_request:
    description: The spot instance request details that has been cancelled
    returned: always
    type: str
    sample: 'Spot requests with IDs: sir-1w76bbrh have been cancelled'
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


def request_spot_instances(module, connection):
    if module.check_mode:
        return

    params = {}

    if module.params.get('launch_specification') is not None:
        params['LaunchSpecification'] = {}

    if module.params.get('launch_specification').get('security_group_ids') is not None:
        params['LaunchSpecification']['SecurityGroupIds'] = module.params.get('launch_specification').get(
            'security_group_ids')

    if module.params.get('launch_specification').get('security_groups') is not None:
        params['LaunchSpecification']['SecurityGroups'] = module.params.get('launch_specification').get(
            'security_groups')

    if module.params.get('launch_specification').get('ebs_optimized') is not None:
        params['LaunchSpecification']['EbsOptimized'] = module.params.get('launch_specification').get('ebs_optimized')

    if module.params.get('launch_specification').get('image_id') is not None:
        params['LaunchSpecification']['ImageId'] = module.params.get('launch_specification').get('image_id')

    import q
    q(params['LaunchSpecification']['ImageId'])

    if module.params.get('launch_specification').get('instance_type') is not None:
        params['LaunchSpecification']['InstanceType'] = module.params.get('launch_specification').get('instance_type')

    if module.params.get('launch_specification').get('kernel_id') is not None:
        params['LaunchSpecification']['KernelId'] = module.params.get('launch_specification').get('kernel_id')

    if module.params.get('launch_specification').get('key_name') is not None:
        params['LaunchSpecification']['KeyName'] = module.params.get('launch_specification').get('key_name')

    if module.params.get('launch_specification').get('ramdisk_id') is not None:
        params['LaunchSpecification']['RamdiskId'] = module.params.get('launch_specification').get('ramdisk_id')

    if module.params.get('launch_specification').get('user_data') is not None:
        params['LaunchSpecification']['UserData'] = module.params.get('launch_specification').get('user_data')

    if module.params.get('launch_specification').get('block_device_mappings') is not None:
        params['LaunchSpecification']['BlockDeviceMappings'] = {}

        if module.params.get('launch_specification').get('block_device_mappings').get('device_name') is not None:
            params['LaunchSpecification']['BlockDeviceMappings']['DeviceName'] = module.params.get('launch_specification').get('block_device_mappings').get('device_name')

        if module.params.get('launch_specification').get('block_device_mappings').get('virtual_name') is not None:
            params['LaunchSpecification']['BlockDeviceMappings']['VirtualName'] = module.params.get('launch_specification').get('block_device_mappings').get('virtual_name')

        if module.params.get('launch_specification').get('block_device_mappings').get('ebs') is not None:
            params['LaunchSpecification']['BlockDeviceMappings']['Ebs'] = module.params.get('launch_specification').get('block_device_mappings').get('ebs')

        if module.params.get('launch_specification').get('block_device_mappings').get('no_device') is not None:
            params['LaunchSpecification']['BlockDeviceMappings']['NoDevice'] = module.params.get('launch_specification').get('block_device_mappings').get('no_device')

    if module.params.get('launch_specification').get('network_interfaces') is not None:
        params['LaunchSpecification']['NetworkInterfaces'] = []

        # for each_item in module.params.get('launch_specification').get('network_interfaces'):

        # if module.params.get('launch_specification').get('network_interfaces').get('associate_public_ip_address') is not None:
        #     params['LaunchSpecification']['NetworkInterfaces']['AssociatePublicIpAddress'] = module.params.get('launch_specification').get('network_interfaces').get('associate_public_ip_address')
        #
        # if module.params.get('launch_specification').get('network_interfaces').get('delete_on_termination') is not None:
        #     params['LaunchSpecification']['NetworkInterfaces']['DeleteOnTermination'] = module.params.get('launch_specification').get('network_interfaces').get('delete_on_termination')
        #
        # if module.params.get('launch_specification').get('network_interfaces').get('description') is not None:
        #     params['LaunchSpecification']['NetworkInterfaces']['Description'] = module.params.get('launch_specification').get('network_interfaces').get('description')
        #
        # if module.params.get('launch_specification').get('network_interfaces').get('device_index') is not None:
        #     params['LaunchSpecification']['NetworkInterfaces']['DeviceIndex'] = module.params.get('launch_specification').get('network_interfaces').get('device_index')
        #
        # if module.params.get('launch_specification').get('network_interfaces').get('groups') is not None:
        #     params['LaunchSpecification']['NetworkInterfaces']['Groups'] = module.params.get('launch_specification').get('network_interfaces').get('groups')
        #
        # if module.params.get('launch_specification').get('network_interfaces').get('ipv6_address_count') is not None:
        #     params['LaunchSpecification']['NetworkInterfaces']['Ipv6AddressCount'] = module.params.get('launch_specification').get('network_interfaces').get('ipv6_address_count')
        #
        # if module.params.get('launch_specification').get('network_interfaces').get('ipv6_addresses') is not None:
        #     params['LaunchSpecification']['NetworkInterfaces']['Ipv6Addresses'] = module.params.get('launch_specification').get('network_interfaces').get('ipv6_addresses')
        #
        # if module.params.get('launch_specification').get('network_interfaces').get('network_interface_id') is not None:
        #     params['LaunchSpecification']['NetworkInterfaces']['NetworkInterfaceId'] = module.params.get('launch_specification').get('network_interfaces').get('network_interface_id')
        #
        # if module.params.get('launch_specification').get('network_interfaces').get('private_ip_addresses') is not None:
        #     params['LaunchSpecification']['NetworkInterfaces']['PrivateIpAddresses'] = module.params.get('launch_specification').get('network_interfaces').get('private_ip_addresses')
        #
        # if module.params.get('launch_specification').get('network_interfaces').get('secondary_private_ip_address_count') is not None:
        #     params['LaunchSpecification']['NetworkInterfaces']['SecondaryPrivateIpAddressCount'] = module.params.get('launch_specification').get('network_interfaces').get('secondary_private_ip_address_count')
        #
        # if module.params.get('launch_specification').get('network_interfaces').get('subnet_id') is not None:
        #     params['LaunchSpecification']['NetworkInterfaces']['SubnetId'] = module.params.get('launch_specification').get('network_interfaces').get('subnet_id')
        #
        # if module.params.get('launch_specification').get('network_interfaces').get('associate_carrier_ip_address') is not None:
        #     params['LaunchSpecification']['NetworkInterfaces']['AssociateCarrierIpAddress'] = module.params.get('launch_specification').get('network_interfaces').get('associate_carrier_ip_address')
        #
        # if module.params.get('launch_specification').get('network_interfaces').get('interface_type') is not None:
        #     params['LaunchSpecification']['NetworkInterfaces']['InterfaceType'] = module.params.get('launch_specification').get('network_interfaces').get('interface_type')
        #
        # if module.params.get('launch_specification').get('network_interfaces').get('network_card_index') is not None:
        #     params['LaunchSpecification']['NetworkInterfaces']['NetworkCardIndex'] = module.params.get('launch_specification').get('network_interfaces').get('network_card_index')
        #
        # if module.params.get('launch_specification').get('network_interfaces').get('ipv4_prefixes') is not None:
        #     params['LaunchSpecification']['NetworkInterfaces']['Ipv4Prefixes'] = module.params.get('launch_specification').get('network_interfaces').get('ipv4_prefixes')
        #
        # if module.params.get('launch_specification').get('network_interfaces').get('ipv4_prefix_count') is not None:
        #     params['LaunchSpecification']['NetworkInterfaces']['Ipv4PrefixCount'] = module.params.get('launch_specification').get('network_interfaces').get('ipv4_prefix_count')
        #
        # if module.params.get('launch_specification').get('network_interfaces').get('ipv6_prefixes') is not None:
        #     params['LaunchSpecification']['NetworkInterfaces']['Ipv6Prefixes'] = module.params.get('launch_specification').get('network_interfaces').get('ipv6_prefixes')
        #
        # if module.params.get('launch_specification').get('network_interfaces').get('ipv6_prefix_count') is not None:
        #     params['LaunchSpecification']['NetworkInterfaces']['Ipv6PrefixCount'] = module.params.get('launch_specification').get('network_interfaces').get('ipv6_prefix_count')

    if module.params.get('launch_specification').get('monitoring') is not None:
        params['LaunchSpecification']['Monitoring'] = {}

        if module.params.get('launch_specification').get('monitoring').get('enabled') is not None:
            params['LaunchSpecification']['Monitoring']['Enabled'] = module.params.get('launch_specification').get('monitoring').get('enabled')

    if module.params.get('launch_specification').get('placement') is not None:
        params['LaunchSpecification']['Placement'] = {}

        if module.params.get('launch_specification').get('placement').get('availability_zone') is not None:
            params['LaunchSpecification']['Placement']['AvailabilityZone'] = module.params.get('launch_specification').get('placement').get('availability_zone')

        if module.params.get('launch_specification').get('placement').get('tenancy') is not None:
            params['LaunchSpecification']['Placement']['Tenancy'] = module.params.get('launch_specification').get('placement').get('tenancy')

        if module.params.get('launch_specification').get('placement').get('group_name') is not None:
            params['LaunchSpecification']['Placement']['GroupName'] = module.params.get('launch_specification').get('placement').get('group_name')

    if module.params.get('launch_specification').get('iam_instance_profile') is not None:
        params['LaunchSpecification']['IamInstanceProfile'] = {}

        if module.params.get('launch_specification').get('iam_instance_profile').get('arn') is not None:
            params['LaunchSpecification']['IamInstanceProfile']['Arn'] = module.params.get('launch_specification').get('iam_instance_profile').get('arn')

        if module.params.get('launch_specification').get('iam_instance_profile').get('name') is not None:
            params['LaunchSpecification']['IamInstanceProfile']['Name'] = module.params.get('launch_specification').get('iam_instance_profile').get('name')

    if module.params.get('zone_group') is not None:
        params['AvailabilityZoneGroup'] = module.params.get('zone_group')

    if module.params.get('count') is not None:
        params['InstanceCount'] = module.params.get('count')

    if module.params.get('launch_group') is not None:
        params['LaunchGroup'] = module.params.get('launch_group')

    if module.params.get('spot_price') is not None:
        params['SpotPrice'] = module.params.get('spot_price')

    if module.params.get('spot_type') is not None:
        params['Type'] = module.params.get('spot_type')

    if module.params.get('client_token') is not None:
        params['ClientToken'] = module.params.get('client_token')

    if module.params.get('interruption') is not None:
        params['InstanceInterruptionBehavior'] = module.params.get('interruption')

    if module.params.get('tags') is not None:
        params['TagSpecifications'] = module.params.get('tags')

    # params['ValidFrom'] = module.params.get('valid_from')
    # params['ValidUntil'] = module.params.get('valid_until')
    try:
        request_spot_instance_response = connection.request_spot_instances(**params)
        return request_spot_instance_response
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Error while creating the spot instance request')


def cancel_spot_instance_requests(module, connection):
    if module.check_mode:
        return

    spot_instance_request_ids = module.params.get('spot_instance_request_ids')
    params = dict()
    params['SpotInstanceRequestIds'] = spot_instance_request_ids
    try:
        response = connection.cancel_spot_instance_requests(**params)
        changed = True
        for each_item in response['CancelledSpotInstanceRequests']:
            if each_item['State'] != 'cancelled':
                changed = False
                break

        module.exit_json(changed=changed,
                         msg='Cancelled Spot request {}'.format(module.params.get('spot_instance_request_ids')))
        return cancel_spot_instance_request_response
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Error while cancelling the spot instance request')


def main():
    network_interface_options = dict(
        associate_public_ip_address=dict(type='bool'),
        delete_on_termination=dict(type='bool'),
        description=dict(type='str'),
        device_index=dict(type='int'),
        groups=dict(type='list'),
        ipv6_address_count=dict(type='int'),
        ipv6_addresses=dict(type=list, elements='dict'),
        network_interface_id=dict(type='str'),
        private_ip_address=dict(type='str'),
        private_ip_addresses=dict(type='list', elements='dict'),
        secondary_private_ip_address_count=dict(type='int'),
        subnet_id=dict(type='str'),
        associate_carrier_ip_address=dict(type='boolean'),
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
        iam_instance_profile=dict(type='dict',options=iam_instance_profile_options),
        image_id=dict(type='str'),
        instance_type=dict(type='str'),
        kernel_id=dict(type='str'),
        key_name=dict(type='str'),
        monitoring=dict(type='dict', options=monitoring_options),
        network_interfaces=dict(type='list', elements='dict', options=network_interface_options, default=[]),
        placement=dict(type='dict', options=placement_options, default={}),
        ramdisk_id=dict(type='str', default=''),
        user_data=dict(type='str', default='')
    )

    argument_spec = dict(
        zone_group=dict(type='str'),
        client_token=dict(type='str'),
        count=dict(type='int', default=1),
        interruption=dict(type='str', default="terminate"),
        launch_group=dict(type='str'),
        launch_specification=dict(type='dict', options=launch_specification_options),
        request_type=dict(default='one-time', choices=["one-time", "persistent"]),
        state=dict(default='present', choices=['present', 'absent', 'running', 'restarted', 'stopped']),
        spot_price=dict(type='str'),
        spot_type=dict(default='one-time', choices=["one-time", "persistent"]),
        tags=dict(type='list'),
        # valid_from=dict(type='datetime', default=datetime.datetime.now()),
        # valid_until=dict(type='datetime', default=(datetime.datetime.now() + datetime.timedelta(minutes=60))
        spot_instance_request_ids=dict(type='list', elements='str'),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ['block_duration', 'zone_group'],
            ['block_duration', 'launch_group'],
        ],
        supports_check_mode=True
    )

    connection = module.client('ec2', AWSRetry.jittered_backoff())

    state = module.params['state']

    if state == 'present':
        response = request_spot_instances(module, connection)
        changed = True
        spot_request = response.get('SpotInstanceRequests')[0]
        module.exit_json(changed=changed, spot_request=spot_request)

    if state == 'absent':
        cancel_spot_instance_requests(module, connection)


if __name__ == '__main__':
    main()
