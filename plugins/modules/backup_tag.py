#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: backup_tag
version_added: 6.0.0
short_description: Manage tags on backup plan, backup vault, recovery point
description:
    - Create, list, update, remove tags on AWS backup resources such as backup plan, backup vault, and recovery point.
    - Resources are referenced using ARN.
author:
    - Mandar Vijay Kulkarni (@mandar242)
options:
  resource:
    description:
      - The Amazon Resource Name (ARN) of the backup resource.
    required: true
    type: str
  state:
    description:
      - Whether the tags should be present or absent on the resource.
    default: present
    choices: ['present', 'absent']
    type: str
  tags:
    description:
      - A dictionary of tags to add or remove from the resource.
      - If the value provided for a tag key is null and I(state=absent), the tag will be removed regardless of its current value.
    type: dict
    required: true
    aliases: ['resource_tags']
  purge_tags:
    description:
      - Whether unspecified tags should be removed from the resource.
      - Note that when combined with I(state=absent), specified tag keys are not purged regardless of its current value.
    type: bool
    default: false

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Add tags on a resource
  amazon.aws.backup_tag:
    resource: "{{ backup_resource_arn }}"
    state: present
    tags:
      CamelCaseKey: CamelCaseValue
      pascalCaseKey: pascalCaseValue
      snake_case_key: snake_case_value
      test_tag_key_1: tag_tag_value_1
      test_tag_key_2: tag_tag_value_2

- name: Remove only specified tags on a resource
  amazon.aws.backup_tag:
    resource: "{{ backup_resource_arn }}"
    state: absent
    tags:
        CamelCaseKey: CamelCaseValue

- name: Remove all tags except for specified tags
  amazon.aws.backup_tag:
    resource: "{{ backup_resource_arn }}"
    state: absent
    tags:
        test_tag_key_1: tag_tag_value_1
        test_tag_key_2: tag_tag_value_2
    purge_tags: true

- name: Update value of tag key on a resource
  amazon.aws.backup_tag:
    resource: "{{ backup_resource_arn }}"
    state: present
    tags:
        test_tag_key_1: tag_tag_value_NEW_1

- name: Remove all of the tags on a resource
  amazon.aws.backup_tag:
    resource: "{{ backup_resource_arn }}"
    state: absent
    tags: {}
    purge_tags: true
"""

RETURN = r"""
tags:
  description: A dict containing the tags on the resource
  returned: always
  type: dict
added_tags:
  description: A dict of tags that were added to the resource
  returned: When tags are added to the resource
  type: dict
removed_tags:
  description: A dict of tags that were removed from the resource
  returned: When tags are removed from the resource
  type: dict
"""

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags
from ansible_collections.amazon.aws.plugins.module_utils.backup import get_backup_resource_tags


def manage_tags(module, backup_client):
    result = {"changed": False}

    resource = module.params.get("resource")
    tags = module.params.get("tags")
    state = module.params.get("state")
    purge_tags = module.params.get("purge_tags")

    current_tags = get_backup_resource_tags(module, backup_client, resource)
    tags_to_add, tags_to_remove = compare_aws_tags(current_tags, tags, purge_tags=purge_tags)

    remove_tags = {}
    if state == "absent":
        for key in tags:
            if purge_tags is False and key in current_tags and (tags[key] is None or current_tags[key] == tags[key]):
                remove_tags[key] = current_tags[key]

        for key in tags_to_remove:
            remove_tags[key] = current_tags[key]

        if remove_tags:
            result["changed"] = True
            result["removed_tags"] = remove_tags
            if not module.check_mode:
                try:
                    backup_client.untag_resource(ResourceArn=resource, TagKeyList=list(remove_tags.keys()))
                except (BotoCoreError, ClientError) as remove_tag_error:
                    module.fail_json_aws(
                        remove_tag_error,
                        msg=f"Failed to remove tags {remove_tags} from resource {resource}",
                    )

    if state == "present" and tags_to_add:
        result["changed"] = True
        result["added_tags"] = tags_to_add
        if not module.check_mode:
            try:
                backup_client.tag_resource(ResourceArn=resource, Tags=tags_to_add)
            except (BotoCoreError, ClientError) as set_tag_error:
                module.fail_json_aws(set_tag_error, msg=f"Failed to set tags {tags_to_add} on resource {resource}")

    result["tags"] = get_backup_resource_tags(module, backup_client, resource)
    return result


def main():
    argument_spec = dict(
        state=dict(default="present", choices=["present", "absent"]),
        resource=dict(required=True, type="str"),
        tags=dict(required=True, type="dict", aliases=["resource_tags"]),
        purge_tags=dict(default=False, type="bool"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    backup_client = module.client("backup")

    result = {}

    result = manage_tags(module, backup_client)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
