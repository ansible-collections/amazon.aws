#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = """
module: ssm_inventory_info
version_added: 6.0.0
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
- amazon.aws.common.modules
- amazon.aws.region.modules
- amazon.aws.boto3
"""

EXAMPLES = """
- name: Retrieve SSM inventory info for instance id 'i-012345678902'
  community.aws.ssm_inventory_info:
    instance_id: 'i-012345678902'
"""


RETURN = """
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
"""


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


class SsmInventoryInfoFailure(Exception):
    def __init__(self, exc, msg):
        self.exc = exc
        self.msg = msg
        super().__init__(self)


def get_ssm_inventory(connection, filters):
    try:
        return connection.get_inventory(Filters=filters)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        raise SsmInventoryInfoFailure(exc=e, msg="get_ssm_inventory() failed.")


def execute_module(module, connection):
    instance_id = module.params.get("instance_id")
    try:
        filters = [{"Key": "AWS:InstanceInformation.InstanceId", "Values": [instance_id]}]

        response = get_ssm_inventory(connection, filters)
        entities = response.get("Entities", [])
        ssm_inventory = {}
        if entities:
            content = entities[0].get("Data", {}).get("AWS:InstanceInformation", {}).get("Content", [])
            if content:
                ssm_inventory = camel_dict_to_snake_dict(content[0])
        module.exit_json(changed=False, ssm_inventory=ssm_inventory)
    except SsmInventoryInfoFailure as e:
        module.fail_json_aws(exception=e.exc, msg=e.msg)


def main():
    argument_spec = dict(
        instance_id=dict(required=True, type="str"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    connection = module.client("ssm")
    execute_module(module, connection)


if __name__ == "__main__":
    main()
