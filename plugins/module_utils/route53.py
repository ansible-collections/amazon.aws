# -*- coding: utf-8 -*-

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from ansible_collections.amazon.aws.plugins.module_utils.botocore import ClientType

# pylint: disable-next=unused-import
from ansible_collections.amazon.aws.plugins.module_utils._route53.common import AnsibleRoute53Error
from ansible_collections.amazon.aws.plugins.module_utils._route53.common import Route53ErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags


def manage_tags(
    client: ClientType,
    resource_type: str,
    resource_id: str,
    new_tags: dict,
    purge_tags: bool,
    check_mode: bool,
) -> bool:
    if new_tags is None:
        return False

    old_tags = get_tags(client, resource_type, resource_id)
    tags_to_set, tags_to_delete = compare_aws_tags(old_tags, new_tags, purge_tags=purge_tags)

    change_params = {}
    if tags_to_set:
        change_params["AddTags"] = ansible_dict_to_boto3_tag_list(tags_to_set)
    if tags_to_delete:
        change_params["RemoveTagKeys"] = tags_to_delete

    if not change_params:
        return False

    if check_mode:
        return True

    _change_tags_for_resource(client, resource_type, resource_id, **change_params)
    return True


@Route53ErrorHandler.common_error_handler("change tags for resource")
@AWSRetry.jittered_backoff()
def _change_tags_for_resource(client: ClientType, resource_type: str, resource_id: str, **kwargs) -> dict:
    return client.change_tags_for_resource(
        ResourceType=resource_type,
        ResourceId=resource_id,
        **kwargs,
    )


@Route53ErrorHandler.list_error_handler("list tags for resource", {})
@AWSRetry.jittered_backoff()
def get_tags(client: ClientType, resource_type: str, resource_id: str) -> dict:
    tagset = client.list_tags_for_resource(
        ResourceType=resource_type,
        ResourceId=resource_id,
    )
    tags = boto3_tag_list_to_ansible_dict(tagset["ResourceTagSet"]["Tags"])
    return tags
