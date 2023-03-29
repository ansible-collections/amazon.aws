#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
from ansible.module_utils.resource_tags import ensure_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule

DOCUMENTATION = r"""
module: backup_plan
short_description: create, delete and modify AWS Backup plans
version_added: 6.0.0
description:
  - Manages AWS Backup plans.
  - For more information see the AWS documentation for backup plans U(https://docs.aws.amazon.com/aws-backup/latest/devguide/about-backup-plans.html).
options:
  backup_plan_name:
    description:
      - The display name of a backup plan. Must contain 1 to 50 alphanumeric or '-_.' characters.
    required: true
    type: str
  rules:
    description:
      - An array of BackupRule objects, each of which specifies a scheduled task that is used to back up a selection of resources.
    required: false
    type: list
  advanced_backup_settings:
    description:
      -  Specifies a list of BackupOptions for each resource type. These settings are only available for Windows Volume Shadow Copy Service (VSS) backup jobs.
    required: false
    type: list
  state:
    description:
      - Create, delete a backup plan.
    required: false
    default: present
    choices: ['present', 'absent']
    type: str
notes: []
author:
  - Kristof Imre Szabo (@krisek)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
  - amazon.aws.tags
"""
EXAMPLES = """
- name: create backup plan
  backup_plan:
    backup_plan_name: elastic
    rules:
    - RuleName: every_morning
      TargetBackupVaultName: elastic
      ScheduleExpression: "cron(0 5 ? * * *)"
      StartWindowMinutes: 120
      CompletionWindowMinutes: 10080
      Lifecycle:
        DeleteAfterDays: 7
      EnableContinuousBackup: true
  register: elastic_plan
- name: show results
  ansible.builtin.debug:
    var: elastic_plan
"""
RETURN = """
backup_plan_name:
  description: backup plan name
  returned: always
  type: str
  sample: elastic
backup_plan_id:
  description: backup plan id
  returned: always
  type: str
  sample: 1111f877-1ecf-4d79-9718-a861cd09df3b
backup_plan:
  description: backup plan details
  returned: always
  type: complex
  contains:
    backup_plan_arn:
      description: backup plan arn
      returned: always
      type: str
      sample: arn:aws:backup:eu-central-1:111122223333:backup-plan:1111f877-1ecf-4d79-9718-a861cd09df3b
    backup_plan_id:
      description: backup plan id
      returned: always
      type: str
      sample: 1111f877-1ecf-4d79-9718-a861cd09df3b
    backup_plan_name:
      description: backup plan name
      returned: always
      type: str
      sample:  elastic
    creation_date:
      description: backup plan creation date
      returned: always
      type: str
      sample: '2023-01-24T10:08:03.193000+01:00'
    last_execution_date:
      description: backup plan last execution date
      returned: always
      type: str
      sample: '2023-03-24T06:30:08.250000+01:00'
    tags:
      description: backup plan tags
      returned: always
      type: str
      sample:
    version_id:
      description: backup plan version id
      returned: always
      type: str
"""
try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule


def main():
    argument_spec = dict(
        backup_plan_name=dict(type="str", required=True),
        rules=dict(type="list", required=False),
        advanced_backup_settings=dict(type="list", required=False),
        tags=dict(required=False, type="dict", aliases=["resource_tags"]),
        purge_tags=dict(default=True, type="bool"),
        state=dict(default="present", choices=["present", "absent"]),
    )
    required_if = [
        ("state", "present", ["backup_plan_name", "rules"]),
        ("state", "absent", ["backup_plan_name"]),
    ]
    module = AnsibleAWSModule(argument_spec=argument_spec, required_if=required_if)
    state = module.params.get("state")
    backup_plan_name = module.params.get("backup_plan_name")
    rules = module.params.get("rules")
    advanced_backup_settings = module.params.get("advanced_backup_settings")
    try:
        client = module.client("backup", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")
    changed = False
    # try to check if backup_plan is there
    paginator = client.get_paginator("list_backup_plans")
    backup_plans = []
    for page in paginator.paginate():
        backup_plans.extend(page["BackupPlansList"])
    exist = False
    response = {}
    for backup_plan in backup_plans:
        if backup_plan["BackupPlanName"] == backup_plan_name:
            exist = True
            response = backup_plan
    if state == "present":
        if exist:  # state is present and backup plan exists => got to update
            # we need to get rules to manage the plan
            full_plan = client.get_backup_plan(
                BackupPlanId=response["BackupPlanId"])

            update_needed = False
            configured_rules = [
                {key: val for key, val in rule.items() if key != "RuleId"}
                for rule in full_plan.get("BackupPlan", {}).get("Rules", [])
            ]

            if json.dumps(configured_rules, sort_keys=True) != json.dumps(rules, sort_keys=True):
                # rules to be updated
                update_needed = True
            advanced_backup_settings_from_aws = json.dumps(
                full_plan.get("BackupPlan", {}).get("AdvancedBackupSettings", None), sort_keys=True
            )
            advanced_backup_settings_from_param = json.dumps(advanced_backup_settings, sort_keys=True)
            if advanced_backup_settings_from_aws != advanced_backup_settings_from_param:
                # advanced settings to be updated
                update_needed = True
            if update_needed:
                backup_plan_data = {"BackupPlanName": backup_plan_name}
                if rules:
                    backup_plan_data["Rules"] = rules
                if advanced_backup_settings:
                    backup_plan_data["AdvancedBackupSettings"] = advanced_backup_settings
                update_response = client.update_backup_plan(
                    aws_retry=True, BackupPlanId=response.get("BackupPlanId"), BackupPlan=backup_plan_data)
                changed = True
            if ensure_tags(client, module, response["BackupPlanArn"],
                           purge_tags=module.params.get("purge_tags"),
                           tags=module.params.get("tags"),
                           resource_type="BackupPlan",
                           ):
                changed = True
        else:  # state is present but backup plan doesnt exist => got to create
            backup_plan_data = {"BackupPlanName": backup_plan_name}
            if rules:
                backup_plan_data["Rules"] = rules
            if advanced_backup_settings:
                backup_plan_data["AdvancedBackupSettings"] = advanced_backup_settings
            response = client.create_backup_plan(
                aws_retry=True, BackupPlan=backup_plan_data)
            ensure_tags(
                client,
                module,
                response["BackupPlanArn"],
                purge_tags=module.params.get("purge_tags"),
                tags=module.params.get("tags"),
                resource_type="BackupPlan",
            )
            changed = True
    elif state == "absent":

        if exist:
            try:
                response_delete = client.delete_backup_plan(aws_retry=True, BackupPlanId=response.get("BackupPlanId"))
                if (response_delete["ResponseMetadata"]["HTTPStatusCode"] == 200):
                    changed = True
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Failed to delete plan")

    formatted_results = camel_dict_to_snake_dict(response)
    # Turn the resource tags from boto3 into an ansible friendly tag dictionary
    formatted_results["tags"] = boto3_tag_list_to_ansible_dict(
        formatted_results.get("tags", []))
    module.exit_json(
        changed=changed,
        backup_plan=formatted_results,
        backup_plan_name=response.get("BackupPlanName"),
        backup_plan_id=response.get("BackupPlanId")
    )


if __name__ == "__main__":
    main()
