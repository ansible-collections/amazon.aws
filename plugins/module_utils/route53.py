# -*- coding: utf-8 -*-

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import typing

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

if typing.TYPE_CHECKING:
    from ansible_collections.amazon.aws.plugins.module_utils.botocore import ClientType
    from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils._route53.common import AnsibleRoute53Error  # pylint: disable=unused-import
from ansible_collections.amazon.aws.plugins.module_utils._route53.common import Route53ErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags


def manage_tags(
    module: AnsibleAWSModule,
    client: ClientType,
    resource_type: str,
    resource_id: str,
    new_tags: dict,
    purge_tags: bool,
) -> bool:
    if new_tags is None:
        return False

    old_tags = get_tags(module, client, resource_type, resource_id)
    tags_to_set, tags_to_delete = compare_aws_tags(old_tags, new_tags, purge_tags=purge_tags)

    change_params = dict()
    if tags_to_set:
        change_params["AddTags"] = ansible_dict_to_boto3_tag_list(tags_to_set)
    if tags_to_delete:
        change_params["RemoveTagKeys"] = tags_to_delete

    if not change_params:
        return False

    if module.check_mode:
        return True

    try:
        client.change_tags_for_resource(ResourceType=resource_type, ResourceId=resource_id, **change_params)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(
            e,
            msg=f"Failed to update tags on {resource_type}",
            resource_id=resource_id,
            change_params=change_params,
        )
    return True


@Route53ErrorHandler.list_error_handler("list tags for resource", {})
def get_tags(module: AnsibleAWSModule, client: ClientType, resource_type: str, resource_id: str) -> dict:
    tagset = client.list_tags_for_resource(
        ResourceType=resource_type,
        ResourceId=resource_id,
    )
    tags = boto3_tag_list_to_ansible_dict(tagset["ResourceTagSet"]["Tags"])
    return tags
