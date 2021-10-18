# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags


def manage_tags(module, client, resource_type, resource_id, new_tags, purge_tags):
    if new_tags is None:
        return False

    old_tags = get_tags(module, client, resource_type, resource_id)
    tags_to_set, tags_to_delete = compare_aws_tags(old_tags, new_tags, purge_tags=purge_tags)

    change_params = dict()
    if tags_to_set:
        change_params['AddTags'] = ansible_dict_to_boto3_tag_list(tags_to_set)
    if tags_to_delete:
        change_params['RemoveTagKeys'] = tags_to_delete

    if not change_params:
        return False

    if module.check_mode:
        return True

    try:
        client.change_tags_for_resource(
            ResourceType=resource_type,
            ResourceId=resource_id,
            **change_params
        )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg='Failed to update tags on {0}'.format(resource_type),
                             resource_id=resource_id, change_params=change_params)
    return True


def get_tags(module, client, resource_type, resource_id):
    try:
        tagset = client.list_tags_for_resource(
            ResourceType=resource_type,
            ResourceId=resource_id,
        )
    except is_boto3_error_code('NoSuchHealthCheck'):
        return {}
    except is_boto3_error_code('NoSuchHostedZone'):   # pylint: disable=duplicate-except
        return {}
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg='Failed to fetch tags on {0}'.format(resource_type),
                             resource_id=resource_id)

    tags = boto3_tag_list_to_ansible_dict(tagset['ResourceTagSet']['Tags'])
    return tags
