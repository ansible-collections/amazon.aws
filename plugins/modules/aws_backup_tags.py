#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""

"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: List tags on a backup vault
    amazon.aws.aws_backup_tags:
    method: list
    resource_arn: "{{ backup_vault_arn }}"

- name: Add tags on a resource
    amazon.aws.aws_backup_tags:
    resource_arn: "{{ backup_vault_arn }}"
    method: update
    state: present
    tags:
        CamelCaseKey: CamelCaseValue
        pascalCaseKey: pascalCaseValue
        snake_case_key: snake_case_value
        test_tag_key_1: tag_tag_value_1
        test_tag_key_2: tag_tag_value_2

- name: Remove only specified tags on a resource
    amazon.aws.aws_backup_tags:
    resource_arn: "{{ backup_vault_arn }}"
    method: update
    state: absent
    tags:
        CamelCaseKey: CamelCaseValue

- name: Remove all tags except for specified tags
    amazon.aws.aws_backup_tags:
    resource_arn: "{{ backup_vault_arn }}"
    method: update
    state: absent
    tags:
        test_tag_key_1: tag_tag_value_1
        test_tag_key_2: tag_tag_value_2
    purge_tags: true

- name: Update value of tag key on a resource
    amazon.aws.aws_backup_tags:
    resource_arn: "{{ backup_vault_arn }}"
    method: update
    state: present
    tags:
        test_tag_key_1: tag_tag_value_NEW_1

- name: Remove only one of the tags on a resource
    amazon.aws.aws_backup_tags:
    resource_arn: "{{ backup_vault_arn }}"
    method: update
    state: absent
    tags: {}
    purge_tags: true

"""

RETURN = r"""

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
        tags=dict(required=False, type='dict'),
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
