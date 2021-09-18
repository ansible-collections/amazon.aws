#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: elasticache_subnet_group
version_added: 1.0.0
short_description: manage ElastiCache subnet groups
description:
     - Creates, modifies, and deletes ElastiCache subnet groups.
options:
  state:
    description:
      - Specifies whether the subnet should be present or absent.
    choices: [ 'present' , 'absent' ]
    default: 'present'
    type: str
  name:
    description:
      - Database subnet group identifier.
      - This value is automatically converted to lowercase.
    required: true
    type: str
  description:
    description:
      - ElastiCache subnet group description.
      - When not provided defaults to I(name) on subnet group creation.
    type: str
  subnets:
    description:
      - List of subnet IDs that make up the ElastiCache subnet group.
      - At least one subnet must be provided when creating an ElastiCache subnet group.
    type: list
    elements: str
author:
  - "Tim Mahoney (@timmahoney)"
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
'''

EXAMPLES = r'''
- name: Add or change a subnet group
  community.aws.elasticache_subnet_group:
    state: present
    name: norwegian-blue
    description: My Fancy Ex Parrot Subnet Group
    subnets:
      - subnet-aaaaaaaa
      - subnet-bbbbbbbb

- name: Remove a subnet group
  community.aws.elasticache_subnet_group:
    state: absent
    name: norwegian-blue
'''

RETURN = r'''
cache_subnet_group:
  description: Description of the Elasticache Subnet Group.
  returned: always
  type: dict
  contains:
    arn:
      description: The Amazon Resource Name (ARN) of the cache subnet group.
      returned: when the subnet group exists
      type: str
      sample: arn:aws:elasticache:us-east-1:012345678901:subnetgroup:norwegian-blue
    description:
      description: The description of the cache subnet group.
      returned: when the cache subnet group exists
      type: str
      sample: My Fancy Ex Parrot Subnet Group
    name:
      description: The name of the cache subnet group.
      returned: when the cache subnet group exists
      type: str
      sample: norwegian-blue
    vpc_id:
      description: The VPC ID of the cache subnet group.
      returned: when the cache subnet group exists
      type: str
      sample: norwegian-blue
    subnet_ids:
      description: The IDs of the subnets beloging to the cache subnet group.
      returned: when the cache subnet group exists
      type: list
      elements: str
      sample:
        - subnet-aaaaaaaa
        - subnet-bbbbbbbb
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry


def get_subnet_group(name):
    try:
        groups = client.describe_cache_subnet_groups(
            aws_retry=True,
            CacheSubnetGroupName=name,
        )['CacheSubnetGroups']
    except is_boto3_error_code('CacheSubnetGroupNotFoundFault'):
        return None
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to describe subnet group")

    if not groups:
        return None

    if len(groups) > 1:
        module.fail_aws(
            msg="Found multiple matches for subnet group",
            cache_subnet_groups=camel_dict_to_snake_dict(groups),
        )

    subnet_group = camel_dict_to_snake_dict(groups[0])

    subnet_group['name'] = subnet_group['cache_subnet_group_name']
    subnet_group['description'] = subnet_group['cache_subnet_group_description']

    subnet_ids = list(s['subnet_identifier'] for s in subnet_group['subnets'])
    subnet_group['subnet_ids'] = subnet_ids

    return subnet_group


def create_subnet_group(name, description, subnets):

    if not subnets:
        module.fail_json(msg='At least one subnet must be provided when creating a subnet group')

    if module.check_mode:
        return True

    try:
        if not description:
            description = name
        client.create_cache_subnet_group(
            aws_retry=True,
            CacheSubnetGroupName=name,
            CacheSubnetGroupDescription=description,
            SubnetIds=subnets,
        )
        return True
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to create subnet group")


def update_subnet_group(subnet_group, name, description, subnets):
    update_params = dict()
    if description and subnet_group['description'] != description:
        update_params['CacheSubnetGroupDescription'] = description
    if subnets:
        old_subnets = set(subnet_group['subnet_ids'])
        new_subnets = set(subnets)
        if old_subnets != new_subnets:
            update_params['SubnetIds'] = list(subnets)

    if not update_params:
        return False

    if module.check_mode:
        return True

    try:
        client.modify_cache_subnet_group(
            aws_retry=True,
            CacheSubnetGroupName=name,
            **update_params,
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to update subnet group")

    return True


def delete_subnet_group(name):

    if module.check_mode:
        return True

    try:
        client.delete_cache_subnet_group(
            aws_retry=True,
            CacheSubnetGroupName=name,
        )
        return True
    except is_boto3_error_code('CacheSubnetGroupNotFoundFault'):
        # AWS is "eventually consistent", cope with the race conditions where
        # deletion hadn't completed when we ran describe
        return False
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to delete subnet group")


def main():
    argument_spec = dict(
        state=dict(default='present', choices=['present', 'absent']),
        name=dict(required=True),
        description=dict(required=False),
        subnets=dict(required=False, type='list', elements='str'),
    )

    global module
    global client

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    state = module.params.get('state')
    name = module.params.get('name').lower()
    description = module.params.get('description')
    subnets = module.params.get('subnets')

    client = module.client('elasticache', retry_decorator=AWSRetry.jittered_backoff())

    subnet_group = get_subnet_group(name)
    changed = False

    if state == 'present':
        if not subnet_group:
            result = create_subnet_group(name, description, subnets)
            changed |= result
        else:
            result = update_subnet_group(subnet_group, name, description, subnets)
            changed |= result
        subnet_group = get_subnet_group(name)
    else:
        if subnet_group:
            result = delete_subnet_group(name)
            changed |= result
        subnet_group = None

    module.exit_json(changed=changed, cache_subnet_group=subnet_group)


if __name__ == '__main__':
    main()
