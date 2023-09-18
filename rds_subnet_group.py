#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: rds_subnet_group
version_added: 1.0.0
short_description: manage RDS database subnet groups
description:
     - Creates, modifies, and deletes RDS database subnet groups. This module has a dependency on python-boto >= 2.5.
options:
  state:
    description:
      - Specifies whether the subnet should be present or absent.
    required: true
    choices: [ 'present' , 'absent' ]
    type: str
  name:
    description:
      - Database subnet group identifier.
    required: true
    type: str
  description:
    description:
      - Database subnet group description.
      - Required when I(state=present).
    type: str
  subnets:
    description:
      - List of subnet IDs that make up the database subnet group.
      - Required when I(state=present).
    type: list
    elements: str
author: "Scott Anderson (@tastychutney)"
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = r'''
- name: Add or change a subnet group
  community.aws.rds_subnet_group:
    state: present
    name: norwegian-blue
    description: My Fancy Ex Parrot Subnet Group
    subnets:
      - subnet-aaaaaaaa
      - subnet-bbbbbbbb

- name: Remove a subnet group
  community.aws.rds_subnet_group:
    state: absent
    name: norwegian-blue
'''

RETURN = r'''
subnet_group:
    description: Dictionary of DB subnet group values
    returned: I(state=present)
    type: complex
    contains:
        name:
            description: The name of the DB subnet group
            returned: I(state=present)
            type: str
        description:
            description: The description of the DB subnet group
            returned: I(state=present)
            type: str
        vpc_id:
            description: The VpcId of the DB subnet group
            returned: I(state=present)
            type: str
        subnet_ids:
            description: Contains a list of Subnet IDs
            returned: I(state=present)
            type: list
        status:
            description: The status of the DB subnet group
            returned: I(state=present)
            type: str
'''

try:
    import boto.rds
    from boto.exception import BotoServerError
except ImportError:
    pass  # Handled by HAS_BOTO

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import HAS_BOTO
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import connect_to_aws
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import get_aws_connection_info


def get_subnet_group_info(subnet_group):
    return dict(
        name=subnet_group.name,
        description=subnet_group.description,
        vpc_id=subnet_group.vpc_id,
        subnet_ids=subnet_group.subnet_ids,
        status=subnet_group.status
    )


def create_result(changed, subnet_group=None):
    if subnet_group is None:
        return dict(
            changed=changed
        )
    else:
        return dict(
            changed=changed,
            subnet_group=get_subnet_group_info(subnet_group)
        )


def main():
    argument_spec = dict(
        state=dict(required=True, choices=['present', 'absent']),
        name=dict(required=True),
        description=dict(required=False),
        subnets=dict(required=False, type='list', elements='str'),
    )
    module = AnsibleAWSModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    state = module.params.get('state')
    group_name = module.params.get('name').lower()
    group_description = module.params.get('description')
    group_subnets = module.params.get('subnets') or {}

    if state == 'present':
        for required in ['description', 'subnets']:
            if not module.params.get(required):
                module.fail_json(msg=str("Parameter %s required for state='present'" % required))
    else:
        for not_allowed in ['description', 'subnets']:
            if module.params.get(not_allowed):
                module.fail_json(msg=str("Parameter %s not allowed for state='absent'" % not_allowed))

    # Retrieve any AWS settings from the environment.
    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module)

    if not region:
        module.fail_json(msg=str("Either region or AWS_REGION or EC2_REGION environment variable or boto config aws_region or ec2_region must be set."))

    try:
        conn = connect_to_aws(boto.rds, region, **aws_connect_kwargs)
    except BotoServerError as e:
        module.fail_json(msg=e.error_message)

    try:
        exists = False
        result = create_result(False)

        try:
            matching_groups = conn.get_all_db_subnet_groups(group_name, max_records=100)
            exists = len(matching_groups) > 0
        except BotoServerError as e:
            if e.error_code != 'DBSubnetGroupNotFoundFault':
                module.fail_json(msg=e.error_message)

        if state == 'absent':
            if exists:
                conn.delete_db_subnet_group(group_name)
                result = create_result(True)
        else:
            if not exists:
                new_group = conn.create_db_subnet_group(group_name, desc=group_description, subnet_ids=group_subnets)
                result = create_result(True, new_group)
            else:
                # Sort the subnet groups before we compare them
                matching_groups[0].subnet_ids.sort()
                group_subnets.sort()
                if (matching_groups[0].name != group_name or
                        matching_groups[0].description != group_description or
                        matching_groups[0].subnet_ids != group_subnets):
                    changed_group = conn.modify_db_subnet_group(group_name, description=group_description, subnet_ids=group_subnets)
                    result = create_result(True, changed_group)
                else:
                    result = create_result(False, matching_groups[0])
    except BotoServerError as e:
        module.fail_json(msg=e.error_message)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
