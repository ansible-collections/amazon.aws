#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
import json
from ansible.module_utils.resource_tags import ensure_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
__metaclass__ = type
DOCUMENTATION = '''
module: backup_selection
short_description: create, delete backup selection
version_added: 1.0.0
description:
  - Read the AWS documentation for backup selections
    U(https://docs.aws.amazon.com/aws-backup/latest/devguide/assigning-resources.html).
options:
  backup_plan_id:
    description:
      - Uniquely identifies the backup plan to be associated with the selection of resources.
    required: true
    type: str
  selection_name:
    description:
      - The display name of a resource selection document. Must contain 1 to 50 alphanumeric or '-_.' characters.
    required: true
    type: str
  iam_role_arn:
    description:
      - The ARN of the IAM role that Backup uses to authenticate when backing up the target resource;
        for example, arn:aws:iam::111122223333:role/system-backup .
    required: true
    type: str
  resources:
    description:
      - A list of Amazon Resource Names (ARNs) to assign to a backup plan. The maximum number of ARNs is 500 without wildcards,
        or 30 ARNs with wildcards. If you need to assign many resources to a backup plan, consider a different resource selection
        strategy, such as assigning all resources of a resource type or refining your resource selection using tags.
    required: false
    type: list
  list_of_tags:
    description:
      - A list of conditions that you define to assign resources to your backup plans using tags.
        Condition operators are case sensitive.
    required: false
    type: list
  not_resources:
    description:
      - A list of Amazon Resource Names (ARNs) to exclude from a backup plan. The maximum number of ARNs is 500 without wildcards,
        or 30 ARNs with wildcards. If you need to exclude many resources from a backup plan, consider a different resource
        selection strategy, such as assigning only one or a few resource types or refining your resource selection using tags.
    required: false
    type: list
  conditions:
    description:
      - A list of conditions (expressed as a dict) that you define to assign resources to your backup plans using tags.
    required: false
    type: dict
  state:
    description:
      - Create, delete a backup selection.
    required: false
    default: present
    choices: ['present', 'absent']
    type: str
notes: []
author:
  - Kristof Imre Szabo (@krisek)
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.boto3
  - amazon.aws.tags
'''
EXAMPLES = '''
- name: create backup selection
  backup_selection:
    selection_name: elastic
    backup_plan_id: 1111f877-1ecf-4d79-9718-a861cd09df3b
    iam_role_arn: arn:aws:iam::111122223333:role/system-backup
    resources:
    - arn:aws:elasticfilesystem:*:*:file-system/*
'''
RETURN = '''
selection_name:
  description: backup selection name
  returned: always
  type: str
  sample: elastic
backup_selection:
  description: backup selection details
  returned: always
  type: complex
  contains:
    backup_plan_id:
      description: backup plan id
      returned: always
      type: str
      sample: 1111f877-1ecf-4d79-9718-a861cd09df3b
    creation_date:
      description: backup plan creation date
      returned: always
      type: str
      sample: 2023-01-24T10:08:03.193000+01:00
    iam_role_arn:
      description: iam role arn
      returned: always
      type: str
      sample: arn:aws:iam::111122223333:role/system-backup
    selection_id:
      description: backup selection id
      returned: always
      type: str
      sample: 1111c217-5d71-4a55-8728-5fc4e63d437b
    selection_name:
      description: backup selection name
      returned: always
      type: str
      sample: elastic
    tags:
      description: backup selection tags
      returned: always
      type: str
      sample:
'''
try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule


def main():
    argument_spec = dict(
        selection_name=dict(type='str', required=True),
        backup_plan_id=dict(type='str', required=True),
        iam_role_arn=dict(type='str', required=True),
        resources=dict(type='list', required=False),
        tags=dict(required=False, type='dict', aliases=['resource_tags']),
        purge_tags=dict(default=True, type='bool'),
        state=dict(default='present', choices=['present', 'absent'])
    )
    required_if = [
        ('state', 'present', ['selection_name',
         'backup_plan_id', 'iam_role_arn']),
        ('state', 'absent', ['selection_name', 'backup_plan_id']),
    ]
    module = AnsibleAWSModule(
        argument_spec=argument_spec, required_if=required_if)
    state = module.params.get('state')
    selection_name = module.params.get('selection_name')
    backup_plan_id = module.params.get('backup_plan_id')
    iam_role_arn = module.params.get('iam_role_arn')
    resources = module.params.get('resources')
    list_of_tags = module.params.get('list_of_tags')
    not_resources = module.params.get('not_resources')
    conditions = module.params.get('conditions')
    try:
        client = module.client(
            'backup', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')
    changed = False
    # try to check if backup_selection is there
    paginator = client.get_paginator('list_backup_selections')
    backup_selections = []
    for page in paginator.paginate(BackupPlanId=backup_plan_id):
        backup_selections.extend(page['BackupSelectionsList'])
    exist = False
    response = {}
    for backup_selection in backup_selections:
        if backup_selection['SelectionName'] == selection_name:
            exist = True
            response = backup_selection
    if state == 'present':
        # build data specified by user
        backup_selection_data = {
            'SelectionName': selection_name,
            'IamRoleArn': iam_role_arn
        }
        if resources:
            backup_selection_data['Resources'] = resources
        if list_of_tags:
            backup_selection_data['ListOfTags'] = list_of_tags
        if not_resources:
            backup_selection_data['NotResources'] = not_resources
        if conditions:
            backup_selection_data['Conditions'] = conditions
        # print(backup_selection_data)
        # print(exist)
        if (exist):
            # we need to get everything to manage the selection
            full_selection = client.get_backup_selection(
                SelectionId=response['SelectionId'], BackupPlanId=backup_plan_id)
            update_needed = False
            if (full_selection.get('BackupSelection', {}).get('IamRoleArn', None) != iam_role_arn):
                update_needed = True
            fields_to_check = [
                {
                    'field_name': 'Resources',
                    'field_value_from_aws': json.dumps(full_selection.get('BackupSelection', {}).get('Resources', None), sort_keys=True),
                    'field_value': json.dumps(resources, sort_keys=True)
                },
                {
                    'field_name': 'ListOfTags',
                    'field_value_from_aws': json.dumps(full_selection.get('BackupSelection', {}).get('ListOfTags', None), sort_keys=True),
                    'field_value': json.dumps(list_of_tags, sort_keys=True)
                },
                {
                    'field_name': 'NotResources',
                    'field_value_from_aws': json.dumps(full_selection.get('BackupSelection', {}).get('NotResources', None), sort_keys=True),
                    'field_value': json.dumps(not_resources, sort_keys=True)
                },
                {
                    'field_name': 'Conditions',
                    'field_value_from_aws': json.dumps(full_selection.get('BackupSelection', {}).get('Conditions', None), sort_keys=True),
                    'field_value': json.dumps(conditions, sort_keys=True)
                }
            ]
            for field_to_check in fields_to_check:
                if field_to_check['field_value_from_aws'] != field_to_check['field_value']:
                    if (field_to_check['field_name'] != 'Conditions'
                            and field_to_check['field_value_from_aws'] != '[]'
                            and field_to_check['field_value'] != 'null'):
                        # advanced settings to be updated
                        update_needed = True
                    if (field_to_check['field_name'] == 'Conditions'
                            and field_to_check['field_value_from_aws'] != '{"StringEquals": [], "StringLike": [], "StringNotEquals": [], "StringNotLike": []}'
                            and field_to_check['field_value'] != 'null'):
                        update_needed = True
            if update_needed:
                response_delete = client.delete_backup_selection(
                    aws_retry=True, SelectionId=response['SelectionID'], BackupPlanId=backup_plan_id)
    # state is present but backup vault doesnt exist
        if (not exist or update_needed):
            response = client.create_backup_selection(
                aws_retry=True, BackupPlanId=backup_plan_id, BackupSelection=backup_selection_data)
            ensure_tags(client, module, response['SelectionId'],
                        purge_tags=module.params.get('purge_tags'),
                        tags=module.params.get('tags'),
                        resource_type='BackupSelection',
                        )
            changed = True
    elif state == 'absent':
        if exist:
            try:
                response_delete = client.delete_backup_selection(
                    aws_retry=True, SelectionId=response['SelectionID'], BackupPlanId=backup_plan_id)
                if (response_delete['ResponseMetadata']['HTTPStatusCode'] == 200):
                    changed = True
            except Exception as e:
                module.exit_json(changed=changed, failed=True)
        # remove_peer_connection(client, module)
    formatted_results = camel_dict_to_snake_dict(response)
    # Turn the resource tags from boto3 into an ansible friendly tag dictionary
    formatted_results['tags'] = boto3_tag_list_to_ansible_dict(
        formatted_results.get('tags', []))
    module.exit_json(
        changed=changed, backup_selection=formatted_results, selection_name=selection_name)


if __name__ == '__main__':
    main()
