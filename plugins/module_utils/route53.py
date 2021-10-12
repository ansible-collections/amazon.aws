# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import compare_aws_tags


def manage_tags(module, client, resource_type, resource_spec, resource_id):
    tagset = client.list_tags_for_resource(
        ResourceType=resource_type,
        ResourceId=resource_id,
    )
    old_tags = boto3_tag_list_to_ansible_dict(tagset['ResourceTagSet']['Tags'])
    new_tags = {}
    if resource_spec['tags']:
        new_tags = resource_spec['tags']
    tags_to_set, tags_to_delete = compare_aws_tags(
        old_tags, new_tags,
        purge_tags=resource_spec['purge_tags'],
    )

    if not tags_to_set and not tags_to_delete:
        return False

    if module.check_mode:
        return True

    # boto3 does not provide create/remove functions for tags in Route 53,
    # neither it works with empty values as parameters to change_tags_for_resource,
    # so we need to call the change function twice
    if tags_to_set:
        client.change_tags_for_resource(
            ResourceType=resource_type,
            ResourceId=resource_id,
            AddTags=ansible_dict_to_boto3_tag_list(tags_to_set),
        )
    if tags_to_delete:
        client.change_tags_for_resource(
            ResourceType=resource_type,
            ResourceId=resource_id,
            RemoveTagKeys=tags_to_delete,
        )
    return True
