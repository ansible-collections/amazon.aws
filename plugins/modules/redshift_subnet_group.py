#!/usr/bin/python

# Copyright 2014 Jens Carl, Hothead Games Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: redshift_subnet_group
version_added: 1.0.0
short_description: manage Redshift cluster subnet groups
description:
  - Create, modifies, and deletes Redshift cluster subnet groups.
options:
  state:
    description:
      - Specifies whether the subnet group should be present or absent.
    default: 'present'
    choices: ['present', 'absent' ]
    type: str
  name:
    description:
      - Cluster subnet group name.
    required: true
    aliases: ['group_name']
    type: str
  description:
    description:
      - Cluster subnet group description.
    aliases: ['group_description']
    type: str
  subnets:
    description:
      - List of subnet IDs that make up the cluster subnet group.
      - At least one subnet must be provided when creating a cluster subnet group.
    aliases: ['group_subnets']
    type: list
    elements: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
author:
  - "Jens Carl (@j-carl), Hothead Games Inc."
'''

EXAMPLES = r'''
- name: Create a Redshift subnet group
  community.aws.redshift_subnet_group:
    state: present
    group_name: redshift-subnet
    group_description: Redshift subnet
    group_subnets:
        - 'subnet-aaaaa'
        - 'subnet-bbbbb'

- name: Remove subnet group
  community.aws.redshift_subnet_group:
    state: absent
    group_name: redshift-subnet
'''

RETURN = r'''
cluster_subnet_group:
    description: A dictionary containing information about the Redshift subnet group.
    returned: success
    type: dict
    contains:
        name:
            description: Name of the Redshift subnet group.
            returned: when the cache subnet group exists
            type: str
            sample: "redshift_subnet_group_name"
        vpc_id:
            description: Id of the VPC where the subnet is located.
            returned: when the cache subnet group exists
            type: str
            sample: "vpc-aabb1122"
        description:
            description: The description of the cache subnet group.
            returned: when the cache subnet group exists
            type: str
            sample: Redshift subnet
        subnet_ids:
            description: The IDs of the subnets beloging to the Redshift subnet group.
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
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict


def get_subnet_group(name):
    try:
        groups = client.describe_cluster_subnet_groups(
            aws_retry=True,
            ClusterSubnetGroupName=name,
        )['ClusterSubnetGroups']
    except is_boto3_error_code('ClusterSubnetGroupNotFoundFault'):
        return None
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to describe subnet group")

    if not groups:
        return None

    if len(groups) > 1:
        module.fail_aws(
            msg="Found multiple matches for subnet group",
            cluster_subnet_groups=camel_dict_to_snake_dict(groups),
        )

    # No support for managing tags yet, but make sure that we don't need to
    # change the return value structure after it's been available in a release.
    tags = boto3_tag_list_to_ansible_dict(groups[0]['Tags'])

    subnet_group = camel_dict_to_snake_dict(groups[0])

    subnet_group['tags'] = tags
    subnet_group['name'] = subnet_group['cluster_subnet_group_name']

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
        client.create_cluster_subnet_group(
            aws_retry=True,
            ClusterSubnetGroupName=name,
            Description=description,
            SubnetIds=subnets,
        )
        return True
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to create subnet group")


def update_subnet_group(subnet_group, name, description, subnets):
    update_params = dict()
    if description and subnet_group['description'] != description:
        update_params['Description'] = description
    if subnets:
        old_subnets = set(subnet_group['subnet_ids'])
        new_subnets = set(subnets)
        if old_subnets != new_subnets:
            update_params['SubnetIds'] = list(subnets)

    if not update_params:
        return False

    if module.check_mode:
        return True

    # Description is optional, SubnetIds is not
    if 'SubnetIds' not in update_params:
        update_params['SubnetIds'] = subnet_group['subnet_ids']

    try:
        client.modify_cluster_subnet_group(
            aws_retry=True,
            ClusterSubnetGroupName=name,
            **update_params,
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to update subnet group")

    return True


def delete_subnet_group(name):

    if module.check_mode:
        return True

    try:
        client.delete_cluster_subnet_group(
            aws_retry=True,
            ClusterSubnetGroupName=name,
        )
        return True
    except is_boto3_error_code('ClusterSubnetGroupNotFoundFault'):
        # AWS is "eventually consistent", cope with the race conditions where
        # deletion hadn't completed when we ran describe
        return False
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to delete subnet group")


def main():
    argument_spec = dict(
        state=dict(default='present', choices=['present', 'absent']),
        name=dict(required=True, aliases=['group_name']),
        description=dict(required=False, aliases=['group_description']),
        subnets=dict(required=False, aliases=['group_subnets'], type='list', elements='str'),
    )

    global module
    global client

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    state = module.params.get('state')
    name = module.params.get('name')
    description = module.params.get('description')
    subnets = module.params.get('subnets')

    client = module.client('redshift', retry_decorator=AWSRetry.jittered_backoff())

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

    compat_results = dict()
    if subnet_group:
        compat_results['group'] = dict(
            name=subnet_group['name'],
            vpc_id=subnet_group['vpc_id'],
        )

    module.exit_json(
        changed=changed,
        cluster_subnet_group=subnet_group,
        **compat_results,
    )


if __name__ == '__main__':
    main()
