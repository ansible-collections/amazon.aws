#!/usr/bin/python
# -*- coding: utf-8 -*-

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
  - Creates, modifies, and deletes RDS database subnet groups.
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
notes:
  - Support for I(tags) and I(purge_tags) was added in release 3.2.0.
author:
  - "Scott Anderson (@tastychutney)"
  - "Alina Buzachis (@alinabuzachis)"
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.tags

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

- name: Add or change a subnet group and associate tags
  community.aws.rds_subnet_group:
    state: present
    name: norwegian-blue
    description: My Fancy Ex Parrot Subnet Group
    subnets:
      - subnet-aaaaaaaa
      - subnet-bbbbbbbb
    tags:
      tag1: Tag1
      tag2: Tag2

- name: Remove a subnet group
  community.aws.rds_subnet_group:
    state: absent
    name: norwegian-blue
'''

RETURN = r'''
changed:
    description: True if listing the RDS subnet group succeeds.
    type: bool
    returned: always
    sample: "false"
subnet_group:
    description: Dictionary of DB subnet group values
    returned: I(state=present)
    type: complex
    contains:
        name:
            description: The name of the DB subnet group (maintained for backward compatibility)
            returned: I(state=present)
            type: str
            sample: "ansible-test-mbp-13950442"
        db_subnet_group_name:
            description: The name of the DB subnet group
            returned: I(state=present)
            type: str
            sample: "ansible-test-mbp-13950442"
        description:
            description: The description of the DB subnet group (maintained for backward compatibility)
            returned: I(state=present)
            type: str
            sample: "Simple description."
        db_subnet_group_description:
            description: The description of the DB subnet group
            returned: I(state=present)
            type: str
            sample: "Simple description."
        vpc_id:
            description: The VpcId of the DB subnet group
            returned: I(state=present)
            type: str
            sample: "vpc-0acb0ba033ff2119c"
        subnet_ids:
            description: Contains a list of Subnet IDs
            returned: I(state=present)
            type: list
            sample:
                "subnet-08c94870f4480797e"
        subnets:
            description: Contains a list of Subnet elements (@see https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rds.html#RDS.Client.describe_db_subnet_groups) # noqa
            returned: I(state=present)
            type: list
            contains:
                subnet_availability_zone:
                    description: Contains Availability Zone information.
                    returned: I(state=present)
                    type: dict
                    version_added: 3.2.0
                    sample:
                        name: "eu-north-1b"
                subnet_identifier:
                    description: The identifier of the subnet.
                    returned: I(state=present)
                    type: str
                    version_added: 3.2.0
                    sample: "subnet-08c94870f4480797e"
                subnet_outpost:
                    description: This value specifies the Outpost.
                    returned: I(state=present)
                    type: dict
                    version_added: 3.2.0
                    sample: {}
                subnet_status:
                    description: The status of the subnet.
                    returned: I(state=present)
                    type: str
                    version_added: 3.2.0
                    sample: "Active"
        status:
            description: The status of the DB subnet group (maintained for backward compatibility)
            returned: I(state=present)
            type: str
            sample: "Complete"
        subnet_group_status:
            description: The status of the DB subnet group
            returned: I(state=present)
            type: str
            sample: "Complete"
        db_subnet_group_arn:
            description: The ARN of the DB subnet group
            returned: I(state=present)
            type: str
            sample: "arn:aws:rds:eu-north-1:721066863947:subgrp:ansible-test-13950442"
        tags:
            description: The tags associated with the subnet group
            returned: I(state=present)
            type: dict
            version_added: 3.2.0
            sample:
                tag1: Tag1
                tag2: Tag2
'''

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.rds import get_tags
from ansible_collections.amazon.aws.plugins.module_utils.rds import ensure_tags


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule


def create_result(changed, subnet_group=None):
    if subnet_group is None:
        return dict(
            changed=changed
        )
    result_subnet_group = dict(subnet_group)
    result_subnet_group['name'] = result_subnet_group.get(
        'db_subnet_group_name')
    result_subnet_group['description'] = result_subnet_group.get(
        'db_subnet_group_description')
    result_subnet_group['status'] = result_subnet_group.get(
        'subnet_group_status')
    result_subnet_group['subnet_ids'] = create_subnet_list(
        subnet_group.get('subnets'))
    return dict(
        changed=changed,
        subnet_group=result_subnet_group
    )


@AWSRetry.jittered_backoff()
def _describe_db_subnet_groups_with_backoff(client, **kwargs):
    paginator = client.get_paginator('describe_db_subnet_groups')
    return paginator.paginate(**kwargs).build_full_result()


def get_subnet_group(client, module):
    params = dict()
    params['DBSubnetGroupName'] = module.params.get('name').lower()

    try:
        _result = _describe_db_subnet_groups_with_backoff(client, **params)
    except is_boto3_error_code('DBSubnetGroupNotFoundFault'):
        return None
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Couldn't describe subnet groups.")

    if _result:
        result = camel_dict_to_snake_dict(_result['DBSubnetGroups'][0])
        result['tags'] = get_tags(client, module, result['db_subnet_group_arn'])

    return result


def create_subnet_list(subnets):
    r'''
    Construct a list of subnet ids from a list of subnets dicts returned by boto3.
    Parameters:
        subnets (list): A list of subnets definitions.
        @see https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rds.html#RDS.Client.describe_db_subnet_groups
    Returns:
        (list): List of subnet ids (str)
    '''
    subnets_ids = []
    for subnet in subnets:
        subnets_ids.append(subnet.get('subnet_identifier'))
    return subnets_ids


def main():
    argument_spec = dict(
        state=dict(required=True, choices=['present', 'absent']),
        name=dict(required=True),
        description=dict(required=False),
        subnets=dict(required=False, type='list', elements='str'),
        tags=dict(required=False, type='dict', aliases=['resource_tags']),
        purge_tags=dict(type='bool', default=True),
    )
    required_if = [('state', 'present', ['description', 'subnets'])]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=required_if,
        supports_check_mode=True
    )

    state = module.params.get('state')
    group_name = module.params.get('name').lower()
    group_description = module.params.get('description')
    group_subnets = module.params.get('subnets') or []

    try:
        connection = module.client('rds', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, 'Failed to instantiate AWS connection.')

    # Default.
    changed = None
    result = create_result(False)
    tags_update = False
    subnet_update = False

    if module.params.get("tags") is not None:
        _tags = ansible_dict_to_boto3_tag_list(module.params.get("tags"))
    else:
        _tags = list()

    matching_groups = get_subnet_group(connection, module)

    if state == 'present':
        if matching_groups:
            # We have one or more subnets at this point.

            # Check if there is any tags update
            tags_update = ensure_tags(
                connection,
                module,
                matching_groups['db_subnet_group_arn'],
                matching_groups['tags'],
                module.params.get("tags"),
                module.params['purge_tags']
            )

            # Sort the subnet groups before we compare them
            existing_subnets = create_subnet_list(matching_groups['subnets'])
            existing_subnets.sort()
            group_subnets.sort()

            # See if anything changed.
            if (
                matching_groups['db_subnet_group_name'] != group_name or
                matching_groups['db_subnet_group_description'] != group_description or
                existing_subnets != group_subnets
            ):
                if not module.check_mode:
                    # Modify existing group.
                    try:
                        connection.modify_db_subnet_group(
                            aws_retry=True,
                            DBSubnetGroupName=group_name,
                            DBSubnetGroupDescription=group_description,
                            SubnetIds=group_subnets
                        )
                    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                        module.fail_json_aws(e, 'Failed to update a subnet group.')
                subnet_update = True
        else:
            if not module.check_mode:
                try:
                    connection.create_db_subnet_group(
                        aws_retry=True,
                        DBSubnetGroupName=group_name,
                        DBSubnetGroupDescription=group_description,
                        SubnetIds=group_subnets,
                        Tags=_tags
                    )
                except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                    module.fail_json_aws(e, 'Failed to create a new subnet group.')
            subnet_update = True
    elif state == 'absent':
        if not module.check_mode:
            try:
                connection.delete_db_subnet_group(aws_retry=True, DBSubnetGroupName=group_name)
            except is_boto3_error_code('DBSubnetGroupNotFoundFault'):
                module.exit_json(**result)
            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
                module.fail_json_aws(e, 'Failed to delete a subnet group.')
        else:
            subnet_group = get_subnet_group(connection, module)
            if subnet_group:
                subnet_update = True
            result = create_result(subnet_update, subnet_group)
            module.exit_json(**result)

        subnet_update = True

    subnet_group = get_subnet_group(connection, module)
    changed = tags_update or subnet_update
    result = create_result(changed, subnet_group)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
