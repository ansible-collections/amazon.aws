#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: backup_tag
version_added: 6.0.0
short_description: Manage tags on backup plan, backup vault, recovery point.
description:
    - Create, list, update, remove tags on AWS backup resources such as backup plan, backup vault, and recovery point.
    - Resources are referenced using ARN.
author:
    - Mandar Vijay Kulkarni (@mandar242)
options:
  resource_arn:
    description:
      - The Amazon Resource Name (ARN) of the backup resource.
    required: true
    type: str
    sample: 'arn:aws:backup:us-east-2:123456789012:backup-vault:my-backup-valult'
  method:
    description:
      - Whether to list or update(create, remove, modify) tags.
      - Set I(method=update) to perform create, update, remove operations on resource tags.
      - Set I(method=list) to only list the resource tags without any modifications.
    choices: ['update', 'list']
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
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: List tags on a resource
    amazon.aws.backup_tag:
    method: list
    resource_arn: "{{ backup_resource_arn }}"

- name: Add tags on a resource
    amazon.aws.backup_tag:
    resource_arn: "{{ backup_resource_arn }}"
    method: update
    state: present
    tags:
        CamelCaseKey: CamelCaseValue
        pascalCaseKey: pascalCaseValue
        snake_case_key: snake_case_value
        test_tag_key_1: tag_tag_value_1
        test_tag_key_2: tag_tag_value_2

- name: Remove only specified tags on a resource
    amazon.aws.backup_tag:
    resource_arn: "{{ backup_resource_arn }}"
    method: update
    state: absent
    tags:
        CamelCaseKey: CamelCaseValue

- name: Remove all tags except for specified tags
    amazon.aws.backup_tag:
    resource_arn: "{{ backup_resource_arn }}"
    method: update
    state: absent
    tags:
        test_tag_key_1: tag_tag_value_1
        test_tag_key_2: tag_tag_value_2
    purge_tags: true

- name: Update value of tag key on a resource
    amazon.aws.backup_tag:
    resource_arn: "{{ backup_resource_arn }}"
    method: update
    state: present
    tags:
        test_tag_key_1: tag_tag_value_NEW_1

- name: Remove all of the tags on a resource
    amazon.aws.backup_tag:
    resource_arn: "{{ backup_resource_arn }}"
    method: update
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

def manage_tags(module, backup_client):
    result = {'changed': False}

    resource_arn = module.params.get('resource_arn')
    tags = module.params.get('tags')
    state = module.params.get('state')
    purge_tags = module.params.get('purge_tags')

    current_tags = get_current_tags(module, backup_client)
    tags_to_add, tags_to_remove = compare_aws_tags(current_tags, tags, purge_tags=purge_tags)

    remove_tags = {}
    if state == 'absent':
        for key in tags:
            if purge_tags == False and key in current_tags and (tags[key] is None or current_tags[key] == tags[key]):
                remove_tags[key] = current_tags[key]

        for key in tags_to_remove:
            remove_tags[key] = current_tags[key]

        if remove_tags:
            result['changed'] = True
            result['removed_tags'] = remove_tags
            if not module.check_mode:
                try:
                    backup_client.untag_resource(ResourceArn=resource_arn, TagKeyList=list(remove_tags.keys()))
                except (BotoCoreError, ClientError) as remove_tag_error:
                    module.fail_json_aws(remove_tag_error, msg='Failed to remove tags {0} from resource {1}'.format(remove_tags, resource_arn))

    if state == 'present' and tags_to_add:
        result['changed'] = True
        result['added_tags'] = tags_to_add
        if not module.check_mode:
            try:
                backup_client.tag_resource(ResourceArn=resource_arn, Tags=tags_to_add)
            except (BotoCoreError, ClientError) as set_tag_error:
                module.fail_json_aws(set_tag_error, msg='Failed to set tags {0} on resource {1}'.format(tags_to_add, resource_arn))

    result['tags'] = get_current_tags(module, backup_client)
    return result

def get_current_tags(module, backup_client):
    resource_arn = module.params.get('resource_arn')

    try:
        response = backup_client.list_tags(ResourceArn=resource_arn)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to list tags on the resource {0}'.format(resource_arn))

    current_tags = response['Tags']

    return current_tags


def main():
    argument_spec = dict(
        method=dict(required=True, type='str', choices=['update', 'list']),
        state=dict(default='present', choices=['present', 'absent']),
        resource_arn=dict(required=True, type='str'),
        tags=dict(type='dict'),
        purge_tags=dict(default=False, type='bool'),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    backup_client = module.client('backup')

    result = {}

    if module.params.get('method') == 'list':
        result['changed'], result['tags'] = False, get_current_tags(module, backup_client)
    else:
        result = manage_tags(module, backup_client)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
