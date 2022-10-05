#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
module: networkfirewall_info
short_description: describe AWS Network Firewall firewalls
version_added: 4.0.0
description:
  - A module for describing AWS Network Firewall firewalls.
options:
  arn:
    description:
      - The ARN of the Network Firewall.
      - Mutually exclusive with I(name) and I(vpc_ids).
    required: false
    type: str
  name:
    description:
      - The name of the Network Firewall.
      - Mutually exclusive with I(arn) and I(vpc_ids).
    required: false
    type: str
  vpc_ids:
    description:
      - A List of VPCs to retrieve the firewalls for.
      - Mutually exclusive with I(name) and I(arn).
    required: false
    type: list
    elements: str
    aliases: ['vpcs', 'vpc_id']

author: Mark Chappell (@tremble)
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.boto3
'''

EXAMPLES = '''

# Describe all firewalls in an account
- community.aws.networkfirewall_info: {}

# Describe a firewall by ARN
- community.aws.networkfirewall_info:
    arn: arn:aws:network-firewall:us-east-1:123456789012:firewall/ExampleFirewall

# Describe a firewall by name
- community.aws.networkfirewall_info:
    name: ExampleFirewall
'''

RETURN = '''
firewall_list:
  description: A list of ARNs of the matching firewalls.
  type: list
  elements: str
  returned: When a firewall name isn't specified
  example: ['arn:aws:network-firewall:us-east-1:123456789012:firewall/Example1',
            'arn:aws:network-firewall:us-east-1:123456789012:firewall/Example2']

firewalls:
  description: The details of the firewalls
  returned: success
  type: list
  elements: dict
  contains:
    firewall:
      description: The details of the firewall
      type: dict
      returned: success
      contains:
        delete_protection:
          description: A flag indicating whether it is possible to delete the firewall.
          type: str
          returned: success
          example: true
        description:
          description: A description of the firewall.
          type: str
          returned: success
          example: "Description"
        firewall_arn:
          description: The ARN of the firewall.
          type: str
          returned: success
          example: "arn:aws:network-firewall:us-east-1:123456789012:firewall/ExampleFirewall"
        firewall_id:
          description: A unique ID for the firewall.
          type: str
          returned: success
          example: "12345678-abcd-1234-abcd-123456789abc"
        firewall_name:
          description: The name of the firewall.
          type: str
          returned: success
          example: "ExampleFirewall"
        firewall_policy_arn:
          description:  The ARN of the firewall policy used by the firewall.
          type: str
          returned: success
          example: "arn:aws:network-firewall:us-east-1:123456789012:firewall-policy/ExamplePolicy"
        firewall_policy_change_protection:
          description:
            - A flag indicating whether it is possible to change which firewall
              policy is used by the firewall.
          type: bool
          returned: success
          example: false
        subnet_change_protection:
          description:
            - A flag indicating whether it is possible to change which subnets
              the firewall endpoints are in.
          type: bool
          returned: success
          example: true
        subnet_mappings:
          description: A list of the subnets the firewall endpoints are in.
          type: list
          elements: dict
          contains:
            subnet_id:
              description: The ID of the subnet.
              type: str
              returned: success
              example: "subnet-12345678"
        tags:
          description: The tags associated with the firewall.
          type: dict
          returned: success
          example: '{"SomeTag": "SomeValue"}'
        vpc_id:
          description: The ID of the VPC that the firewall is used by.
          type: str
          returned: success
          example: "vpc-0123456789abcdef0"
    firewall_metadata:
      description: Metadata about the firewall
      type: dict
      returned: success
      contains:
        configuration_sync_state_summary:
          description:
            - A short summary of the synchronization status of the
              policy and rule groups.
          type: str
          returned: success
          example: "IN_SYNC"
        status:
          description:
            - A short summary of the status of the firewall endpoints.
          type: str
          returned: success
          example: "READY"
        sync_states:
          description:
            - A description, broken down by availability zone, of the status
              of the firewall endpoints as well as the synchronization status
              of the policies and rule groups.
          type: dict
          returned: success
          example:
            {
              "us-east-1a": {
                "attachment": {
                  "endpoint_id": "vpce-123456789abcdef01",
                  "status": "READY",
                  "subnet_id": "subnet-12345678"
                },
                "config": {
                  "arn:aws:network-firewall:us-east-1:123456789012:firewall-policy/Ansible-Example": {
                    "sync_status": "IN_SYNC",
                    "update_token": "abcdef01-0000-0000-0000-123456789abc"
                  },
                  "arn:aws:network-firewall:us-east-1:123456789012:stateful-rulegroup/ExampleDomainList": {
                    "sync_status": "IN_SYNC",
                    "update_token": "12345678-0000-0000-0000-abcdef012345"
                  }
                }
              }
            }
'''


from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.community.aws.plugins.module_utils.networkfirewall import NetworkFirewallManager


def main():

    argument_spec = dict(
        name=dict(type='str', required=False),
        arn=dict(type='str', required=False),
        vpc_ids=dict(type='list', required=False, elements='str', aliases=['vpcs', 'vpc_id']),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ('arn', 'name', 'vpc_ids',),
        ],
    )

    arn = module.params.get('arn')
    name = module.params.get('name')
    vpcs = module.params.get('vpc_ids')

    manager = NetworkFirewallManager(module)

    results = dict(changed=False)

    if name or arn:
        firewall = manager.get_firewall(name=name, arn=arn)
        if firewall:
            results['firewalls'] = [firewall]
        else:
            results['firewalls'] = []
    else:
        if vpcs:
            firewall_list = manager.list(vpc_ids=vpcs)
        else:
            firewall_list = manager.list()
        results['firewall_list'] = firewall_list
        firewalls = [manager.get_firewall(arn=f) for f in firewall_list]
        results['firewalls'] = firewalls

    module.exit_json(**results)


if __name__ == '__main__':
    main()
