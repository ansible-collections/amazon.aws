#!/usr/bin/python
# Copyright (c) 2023 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = '''
module: test_get_ssm_inventory
short_description: Get SSM inventory information for EC2 instance
description:
    - Gather SSM inventory for EC2 instance configured with SSM.
author: 'Aubin Bikouo (@abikouo)'
options:
  instance_id:
    description:
      - EC2 instance id.
    required: true
    type: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
- amazon.aws.boto3
'''


RETURN = '''
ssm_inventory:
    returned: on success
    description: >
        SSM inventory information.
    type: dict
    sample: {
        'agent_type': 'amazon-ssm-agent',
        'agent_version': '3.2.582.0',
        'computer_name': 'ip-172-31-44-166.ec2.internal',
        'instance_id': 'i-039eb9b1f55934ab6',
        'instance_status': 'Active',
        'ip_address': '172.31.44.166',
        'platform_name': 'Fedora Linux',
        'platform_type': 'Linux',
        'platform_version': '37',
        'resource_type': 'EC2Instance'
    }
'''


from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict


def main():
    argument_spec = dict(
        instance_id=dict(required=True, type='str')
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client('ssm')

    filters = [
        {
            'Key': 'AWS:InstanceInformation.InstanceId',
            'Values': [module.params.get('instance_id')]
        }
    ]
    response = connection.get_inventory(Filters=filters)
    entities = response.get("Entities", [])
    ssm_inventory = {}
    if entities:
        content = entities[0].get('Data', {}).get('AWS:InstanceInformation', {}).get('Content', [])
        if content:
            ssm_inventory = camel_dict_to_snake_dict(content[0])
    module.exit_json(ssm_inventory=ssm_inventory)


if __name__ == '__main__':
    main()
