#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: ec2_eip_info
version_added: 1.0.0
short_description: List EC2 EIP details
description:
    - List details of EC2 Elastic IP addresses.
    - This module was called C(ec2_eip_facts) before Ansible 2.9. The usage did not change.
author: "Brad Macpherson (@iiibrad)"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and filter
        value.  See U(https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-addresses.html#options)
        for possible filters. Filter names and values are case sensitive.
    required: false
    default: {}
    type: dict
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = r'''
# Note: These examples do not set authentication details or the AWS region,
# see the AWS Guide for details.

- name: List all EIP addresses in the current region.
  community.aws.ec2_eip_info:
  register: regional_eip_addresses

- name: List all EIP addresses for a VM.
  community.aws.ec2_eip_info:
    filters:
       instance-id: i-123456789
  register: my_vm_eips

- ansible.builtin.debug:
    msg: "{{ my_vm_eips.addresses | json_query(\"[?private_ip_address=='10.0.0.5']\") }}"

- name: List all EIP addresses for several VMs.
  community.aws.ec2_eip_info:
    filters:
       instance-id:
         - i-123456789
         - i-987654321
  register: my_vms_eips

- name: List all EIP addresses using the 'Name' tag as a filter.
  community.aws.ec2_eip_info:
    filters:
      tag:Name: www.example.com
  register: my_vms_eips

- name: List all EIP addresses using the Allocation-id as a filter
  community.aws.ec2_eip_info:
    filters:
      allocation-id: eipalloc-64de1b01
  register: my_vms_eips

# Set the variable eip_alloc to the value of the first allocation_id
# and set the variable my_pub_ip to the value of the first public_ip
- ansible.builtin.set_fact:
    eip_alloc: my_vms_eips.addresses[0].allocation_id
    my_pub_ip: my_vms_eips.addresses[0].public_ip

'''


RETURN = '''
addresses:
  description: Properties of all Elastic IP addresses matching the provided filters. Each element is a dict with all the information related to an EIP.
  returned: on success
  type: list
  sample: [{
        "allocation_id": "eipalloc-64de1b01",
        "association_id": "eipassoc-0fe9ce90d6e983e97",
        "domain": "vpc",
        "instance_id": "i-01020cfeb25b0c84f",
        "network_interface_id": "eni-02fdeadfd4beef9323b",
        "network_interface_owner_id": "0123456789",
        "private_ip_address": "10.0.0.1",
        "public_ip": "54.81.104.1",
        "tags": {
            "Name": "test-vm-54.81.104.1"
        }
    }]

'''

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import (ansible_dict_to_boto3_filter_list,
                                                                     boto3_tag_list_to_ansible_dict,
                                                                     camel_dict_to_snake_dict,
                                                                     )
try:
    from botocore.exceptions import (BotoCoreError, ClientError)
except ImportError:
    pass  # caught by imported AnsibleAWSModule


def get_eips_details(module):
    connection = module.client('ec2')
    filters = module.params.get("filters")
    try:
        response = connection.describe_addresses(
            Filters=ansible_dict_to_boto3_filter_list(filters)
        )
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(
            e,
            msg="Error retrieving EIPs")

    addresses = camel_dict_to_snake_dict(response)['addresses']
    for address in addresses:
        if 'tags' in address:
            address['tags'] = boto3_tag_list_to_ansible_dict(address['tags'])
    return addresses


def main():
    module = AnsibleAWSModule(
        argument_spec=dict(
            filters=dict(type='dict', default={})
        ),
        supports_check_mode=True
    )
    if module._module._name == 'ec2_eip_facts':
        module._module.deprecate("The 'ec2_eip_facts' module has been renamed to 'ec2_eip_info'", date='2021-12-01', collection_name='community.aws')

    module.exit_json(changed=False, addresses=get_eips_details(module))


if __name__ == '__main__':
    main()
