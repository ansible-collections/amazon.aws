#!/usr/bin/python
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ec2_eni_info
short_description: Gather information about ec2 ENI interfaces in AWS
description:
    - Gather information about ec2 ENI interfaces in AWS.
    - This module was called C(ec2_eni_facts) before Ansible 2.9. The usage did not change.
author: "Rob White (@wimnat)"
requirements: [ boto3 ]
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeNetworkInterfaces.html) for possible filters.
    type: dict
extends_documentation_fragment:
- ansible.amazon.aws
- ansible.amazon.ec2

'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather information about all ENIs
- ec2_eni_info:

# Gather information about a particular ENI
- ec2_eni_info:
    filters:
      network-interface-id: eni-xxxxxxx

'''

RETURN = '''
network_interfaces:
  description: List of matching elastic network interfaces
  returned: always
  type: complex
  contains:
    association:
      description: Info of associated elastic IP (EIP)
      returned: always, empty dict if no association exists
      type: dict
      sample: {
          allocation_id: "eipalloc-5sdf123",
          association_id: "eipassoc-8sdf123",
          ip_owner_id: "4415120123456",
          public_dns_name: "ec2-52-1-0-63.compute-1.amazonaws.com",
          public_ip: "52.1.0.63"
        }
    attachment:
      description: Info about attached ec2 instance
      returned: always, empty dict if ENI is not attached
      type: dict
      sample: {
        attach_time: "2017-08-05T15:25:47+00:00",
        attachment_id: "eni-attach-149d21234",
        delete_on_termination: false,
        device_index: 1,
        instance_id: "i-15b8d3cadbafa1234",
        instance_owner_id: "4415120123456",
        status: "attached"
      }
    availability_zone:
      description: Availability zone of ENI
      returned: always
      type: str
      sample: "us-east-1b"
    description:
      description: Description text for ENI
      returned: always
      type: str
      sample: "My favourite network interface"
    groups:
      description: List of attached security groups
      returned: always
      type: list
      sample: [
        {
          group_id: "sg-26d0f1234",
          group_name: "my_ec2_security_group"
        }
      ]
    id:
      description: The id of the ENI (alias for network_interface_id)
      returned: always
      type: str
      sample: "eni-392fsdf"
    interface_type:
      description: Type of the network interface
      returned: always
      type: str
      sample: "interface"
    ipv6_addresses:
      description: List of IPv6 addresses for this interface
      returned: always
      type: list
      sample: []
    mac_address:
      description: MAC address of the network interface
      returned: always
      type: str
      sample: "0a:f8:10:2f:ab:a1"
    network_interface_id:
      description: The id of the ENI
      returned: always
      type: str
      sample: "eni-392fsdf"
    owner_id:
      description: AWS account id of the owner of the ENI
      returned: always
      type: str
      sample: "4415120123456"
    private_dns_name:
      description: Private DNS name for the ENI
      returned: always
      type: str
      sample: "ip-172-16-1-180.ec2.internal"
    private_ip_address:
      description: Private IP address for the ENI
      returned: always
      type: str
      sample: "172.16.1.180"
    private_ip_addresses:
      description: List of private IP addresses attached to the ENI
      returned: always
      type: list
      sample: []
    requester_id:
      description: The ID of the entity that launched the ENI
      returned: always
      type: str
      sample: "AIDAIONYVJQNIAZFT3ABC"
    requester_managed:
      description:  Indicates whether the network interface is being managed by an AWS service.
      returned: always
      type: bool
      sample: false
    source_dest_check:
      description: Indicates whether the network interface performs source/destination checking.
      returned: always
      type: bool
      sample: false
    status:
      description: Indicates if the network interface is attached to an instance or not
      returned: always
      type: str
      sample: "in-use"
    subnet_id:
      description: Subnet ID the ENI is in
      returned: always
      type: str
      sample: "subnet-7bbf01234"
    tag_set:
      description: Dictionary of tags added to the ENI
      returned: always
      type: dict
      sample: {}
    vpc_id:
      description: ID of the VPC the network interface it part of
      returned: always
      type: str
      sample: "vpc-b3f1f123"
'''

try:
    from botocore.exceptions import ClientError, NoCredentialsError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ansible.amazon.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list, boto3_conn
from ansible_collections.ansible.amazon.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict, camel_dict_to_snake_dict
from ansible_collections.ansible.amazon.plugins.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info


def list_eni(connection, module):

    if module.params.get("filters") is None:
        filters = []
    else:
        filters = ansible_dict_to_boto3_filter_list(module.params.get("filters"))

    try:
        network_interfaces_result = connection.describe_network_interfaces(Filters=filters)['NetworkInterfaces']
    except (ClientError, NoCredentialsError) as e:
        module.fail_json(msg=e.message)

    # Modify boto3 tags list to be ansible friendly dict and then camel_case
    camel_network_interfaces = []
    for network_interface in network_interfaces_result:
        network_interface['TagSet'] = boto3_tag_list_to_ansible_dict(network_interface['TagSet'])
        # Added id to interface info to be compatible with return values of ec2_eni module:
        network_interface['Id'] = network_interface['NetworkInterfaceId']
        camel_network_interfaces.append(camel_dict_to_snake_dict(network_interface))

    module.exit_json(network_interfaces=camel_network_interfaces)


def get_eni_info(interface):

    # Private addresses
    private_addresses = []
    for ip in interface.private_ip_addresses:
        private_addresses.append({'private_ip_address': ip.private_ip_address, 'primary_address': ip.primary})

    interface_info = {'id': interface.id,
                      'subnet_id': interface.subnet_id,
                      'vpc_id': interface.vpc_id,
                      'description': interface.description,
                      'owner_id': interface.owner_id,
                      'status': interface.status,
                      'mac_address': interface.mac_address,
                      'private_ip_address': interface.private_ip_address,
                      'source_dest_check': interface.source_dest_check,
                      'groups': dict((group.id, group.name) for group in interface.groups),
                      'private_ip_addresses': private_addresses
                      }

    if hasattr(interface, 'publicDnsName'):
        interface_info['association'] = {'public_ip_address': interface.publicIp,
                                         'public_dns_name': interface.publicDnsName,
                                         'ip_owner_id': interface.ipOwnerId
                                         }

    if interface.attachment is not None:
        interface_info['attachment'] = {'attachment_id': interface.attachment.id,
                                        'instance_id': interface.attachment.instance_id,
                                        'device_index': interface.attachment.device_index,
                                        'status': interface.attachment.status,
                                        'attach_time': interface.attachment.attach_time,
                                        'delete_on_termination': interface.attachment.delete_on_termination,
                                        }

    return interface_info


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            filters=dict(default=None, type='dict')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)
    if module._name == 'ec2_eni_facts':
        module.deprecate("The 'ec2_eni_facts' module has been renamed to 'ec2_eni_info'", version='2.13')

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_params)

    list_eni(connection, module)


if __name__ == '__main__':
    main()
