#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: backup_plan
version_added: 6.0.0
short_description: create, delete and modify AWS Backup plans
description:
  - Manage AWS Backup plans.
  - For more information see the AWS documentation for Backup plans U(https://docs.aws.amazon.com/aws-backup/latest/devguide/about-backup-plans.html).
author:
  - Kristof Imre Szabo (@krisek)
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
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
  - amazon.aws.tags
"""

EXAMPLES = r"""
- name: create backup plan
  amazon.aws.backup_plan:
    state: present
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

"""
RETURN = r"""
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

import json
from typing import Optional
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # Handled by AnsibleAWSModule


def create_backup_plan(module: AnsibleAWSModule, client, params: dict):
    """
    Creates a Backup Plan

    module : AnsibleAWSModule object
    client : boto3 backup client connection object
    params : The parameters to create a backup plan
    """
    params = {k: v for k, v in params.items() if v is not None}
    try:
        response = client.create_backup_plan(**params)
    except (
        BotoCoreError,
        ClientError,
    ) as err:
        module.fail_json_aws(err, msg="Failed to create Backup Plan")
    return response


def get_plan_details(module, client, backup_plan_name: str):
    try:
        plan = paginated_list(client, filter_by=backup_plan_name)[0]
    except (BotoCoreError, ClientError) as err:
        module.debug("Unable to get backup plan details {0}".format(err))
        plan = None
    except IndexError:
        plan = None
    return plan


def paginated_list(
    client, filter_by: Optional[str] = None, **pagination_params
) -> list[dict]:
    results = []
    paginator = client.get_paginator("list_backup_plans")
    page_iterator = paginator.paginate(**pagination_params)
    if filter_by:
        filtered_iterator = page_iterator.search(
            f"BackupPlansList[?BackupPlanName=='{filter_by}']"
        )
        results.extend(list(filtered_iterator))
    else:
        results.extend([item["BackupPlansList"] for item in page_iterator])
    return results


def plan_update_needed(client, backup_plan_id: str, backup_plan_data: dict) -> bool:
    update_needed = False

    # we need to get current rules to manage the plan
    full_plan = client.get_backup_plan(BackupPlanId=backup_plan_id)

    configured_rules = json.dumps(
        [
            {key: val for key, val in rule.items() if key != "RuleId"}
            for rule in full_plan.get("BackupPlan", {}).get("Rules", [])
        ],
        sort_keys=True,
    )
    supplied_rules = json.dumps(backup_plan_data["BackupPlan"]["Rules"], sort_keys=True)

    if configured_rules != supplied_rules:
        # rules to be updated
        update_needed = True

    configured_advanced_backup_settings = json.dumps(
        full_plan.get("BackupPlan", {}).get("AdvancedBackupSettings", None),
        sort_keys=True,
    )
    supplied_advanced_backup_settings = json.dumps(
        backup_plan_data["BackupPlan"]["AdvancedBackupSettings"], sort_keys=True
    )
    if configured_advanced_backup_settings != supplied_advanced_backup_settings:
        # advanced settings to be updated
        update_needed = True
    return update_needed


def update_backup_plan(
    module: AnsibleAWSModule, client, backup_plan_id: str, backup_plan_data: dict
):
    try:
        response = client.update_backup_plan(
            BackupPlanId=backup_plan_id,
            BackupPlan=backup_plan_data["BackupPlan"],
        )
    except (
        BotoCoreError,
        ClientError,
    ) as err:
        module.fail_json_aws(err, msg="Failed to create Backup Plan")
    return response


def delete_backup_plan(module: AnsibleAWSModule, client, backup_plan_id: str):
    """
    Delete a Backup Plan

    module : AnsibleAWSModule object
    client : boto3 client connection object
    backup_plan_id : Backup Plan ID
    """
    try:
        client.delete_backup_plan(BackupPlanId=backup_plan_id)
    except (BotoCoreError, ClientError) as err:
        module.fail_json_aws(err, msg="Failed to delete the Backup Plan")


def main():
    argument_spec = dict(
        state=dict(default="present", choices=["present", "absent"]),
        backup_plan_name=dict(required=True, type="str"),
        rules=dict(type="list"),
        advanced_backup_settings=dict(default=[], type="list"),
        creator_request_id=dict(type="str"),
        tags=dict(required=False, type="dict", aliases=["resource_tags"]),
        purge_tags=dict(default=True, type="bool"),
    )

    required_if = [
        ("state", "present", ["backup_plan_name", "rules"]),
        ("state", "absent", ["backup_plan_name"]),
    ]

    module = AnsibleAWSModule(argument_spec=argument_spec, required_if=required_if)

    # collect parameters
    state = module.params.get("state")
    backup_plan_name = module.params["backup_plan_name"]
    purge_tags = module.params["purge_tags"]
    client = module.client("backup")
    results = {"changed": False, "exists": False}

    # TODO: support check mode?

    current_plan = get_plan_details(module, client, backup_plan_name)

    if state == "present":
        new_plan_data = {
            "BackupPlan": {
                "BackupPlanName": backup_plan_name,
                "Rules": module.params["rules"],
                "AdvancedBackupSettings": module.params.get("advanced_backup_settings"),
            },
            "BackupPlanTags": module.params.get("tags"),
            "CreatorRequestId": module.params.get("creator_request_id"),
        }

        if current_plan is None:  # Plan does not exist, create it
            create_backup_plan(module, client, new_plan_data)
            # TODO: add tags
            # ensure_tags(
            #     client,
            #     module,
            #     response["BackupPlanArn"],
            #     purge_tags=module.params.get("purge_tags"),
            #     tags=module.params.get("tags"),
            #     resource_type="BackupPlan",
            # )
            results["exists"] = True

        else:  # Plan exists, update if needed
            results["exists"] = True
            current_plan_id = current_plan["BackupPlanId"]
            if plan_update_needed(client, current_plan_id, new_plan_data):
                update_backup_plan(module, client, current_plan_id, new_plan_data)
            if purge_tags:
                pass
                # TODO: Update plan tags
                # ensure_tags(
                #     client,
                #     module,
                #     response["BackupPlanArn"],
                #     purge_tags=module.params.get("purge_tags"),
                #     tags=module.params.get("tags"),
                #     resource_type="BackupPlan",
                # )
        results["changed"] = True
        new_plan = get_plan_details(module, client, backup_plan_name)
        results["backup_plan"] = camel_dict_to_snake_dict(new_plan)

    elif state == "absent":
        if current_plan is None:  # Plan does not exist, can't delete it
            module.fail_json(
                msg=f"Backup plan {backup_plan_name} not found.",
                # TODO: existing_backup_plans="list existing backup plan names",
            )
        else:  # Plan exists, delete it
            delete_backup_plan(module, client, current_plan["BackupPlanId"])
            results["changed"] = True
            results["exists"] = False

    module.exit_json(**results)


if __name__ == "__main__":
    main()
