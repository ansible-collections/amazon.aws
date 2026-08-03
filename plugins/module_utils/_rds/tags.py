# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from typing import Dict
from typing import Optional

from ..tagging import ansible_dict_to_boto3_tag_list
from ..tagging import boto3_tag_list_to_ansible_dict
from ..tagging import compare_aws_tags
from .api import call_method
from .api import list_tags_for_resource
from .common import AnsibleRDSError


def get_tags(client, module, resource_arn: str) -> Dict[str, str]:
    """
    Returns tags for provided RDS resource, formatted as an Ansible dict.

    Fails the module if an error is raised while retrieving resource tags.

        Parameters:
            client: boto3 rds client
            module: AnsibleAWSModule
            resource_arn (str): AWS resource ARN

        Returns:
            tags (dict): Tags for resource, formatted as an Ansible dict. An empty list is returned if the resource has no tags.
    """
    try:
        tags = list_tags_for_resource(client, resource_arn)
    except AnsibleRDSError as e:
        module.fail_json_aws(e, msg=f"Unable to list tags for resource {resource_arn}")
    return boto3_tag_list_to_ansible_dict(tags)


def ensure_tags(
    client,
    module,
    resource_arn: str,
    existing_tags: Dict[str, str],
    tags: Optional[Dict[str, str]],
    purge_tags: bool,
) -> bool:
    """
    Compares current resource tages to desired tags and adds/removes tags to ensure desired tags are present.

    A value of None for desired tags results in resource tags being left as is.

        Parameters:
            client: boto3 rds client
            module: AnsibleAWSModule
            resource_arn (str): AWS resource ARN
            existing_tags (dict): Current resource tags formatted as an Ansible dict
            tags (dict): Desired resource tags formatted as an Ansible dict
            purge_tags (bool): Whether to remove any existing resource tags not present in desired tags

        Returns:
            True if resource tags are updated, False if not.
    """
    if tags is None:
        return False
    tags_to_add, tags_to_remove = compare_aws_tags(existing_tags, tags, purge_tags)
    changed = bool(tags_to_add or tags_to_remove)
    if tags_to_add:
        call_method(
            client,
            module,
            method_name="add_tags_to_resource",
            parameters={"ResourceName": resource_arn, "Tags": ansible_dict_to_boto3_tag_list(tags_to_add)},
        )
    if tags_to_remove:
        call_method(
            client,
            module,
            method_name="remove_tags_from_resource",
            parameters={"ResourceName": resource_arn, "TagKeys": tags_to_remove},
        )
    return changed
