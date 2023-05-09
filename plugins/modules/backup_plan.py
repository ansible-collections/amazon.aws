#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: backup_plan
version_added: 6.0.0
short_description: Manage AWS Backup Plans
description:
  - Creates, updates, or deletes AWS Backup Plans
  - For more information see the AWS documentation for Backup plans U(https://docs.aws.amazon.com/aws-backup/latest/devguide/about-backup-plans.html).
author:
  - Kristof Imre Szabo (@krisek)
  - Alina Buzachis (@alinabuzachis)
  - Helen Bailey (@hakbailey)
options:
  state:
    description:
      - Create/update or delete a backup plan.
    type: str
    default: present
    choices: ['present', 'absent']
  backup_plan_name:
    description:
      - The display name of a backup plan. Must contain 1 to 50 alphanumeric or '-_.' characters.
    type: str
    required: true
    aliases: ['name']
  rules:
    description:
      - An array of BackupRule objects, each of which specifies a scheduled task that is used to back up a selection of resources.
      - Required when I(state=present).
    type: list
    elements: dict
    suboptions:
      rule_name:
        description: Name of the rule.
        type: str
        required: true
      target_backup_vault_name:
        description: Name of the Backup Vault this rule should target.
        type: str
        required: true
      schedule_expression:
        description: A CRON expression in UTC specifying when Backup initiates a backup
          job. AWS default is used if not supplied.
        type: str
        default: 'cron(0 5 ? * * *)'
      start_window_minutes:
        description:
          - A value in minutes after a backup is scheduled before a job will be
            canceled if it doesn't start successfully. If this value is included, it
            must be at least 60 minutes to avoid errors.
          - AWS default if not supplied is 480.
        type: int
        default: 480
      completion_window_minutes:
        description:
          - A value in minutes after a backup job is successfully started before it
            must be completed or it will be canceled by Backup.
          - AWS default if not supplied is 10080
        type: int
        default: 10080
      lifecycle:
        description:
          - The lifecycle defines when a protected resource is transitioned to cold
            storage and when it expires. Backup will transition and expire backups
            automatically according to the lifecycle that you define.
          - Backups transitioned to cold storage must be stored in cold storage for a
            minimum of 90 days. Therefore, the "retention" setting must be 90 days
            greater than the "transition to cold after days" setting. The "transition
            to cold after days" setting cannot be changed after a backup has been
            transitioned to cold.
        type: dict
        suboptions:
          move_to_cold_storage_after_days:
            description: Specifies the number of days after creation that a recovery point is moved to cold storage.
            type: int
          delete_after_days:
            description: Specifies the number of days after creation that a recovery
              point is deleted. Must be greater than 90 days plus
              move_to_cold_storage_after_days.
            type: int
      recovery_point_tags:
        description: To help organize your resources, you can assign your own metadata to the resources that you create.
        type: dict
      copy_actions:
        description: An array of copy_action objects, which contains the details of the copy operation.
        type: list
        elements: dict
        suboptions:
          destination_backup_vault_arn:
            description: An Amazon Resource Name (ARN) that uniquely identifies the destination backup vault for the copied backup.
            type: str
            required: true
          lifecycle:
            description:
              - Contains an array of Transition objects specifying how long in days
                before a recovery point transitions to cold storage or is deleted.
              - Backups transitioned to cold storage must be stored in cold storage for
                a minimum of 90 days. Therefore, on the console, the "retention"
                setting must be 90 days greater than the "transition to cold after
                days" setting. The "transition to cold after days" setting cannot be
                changed after a backup has been transitioned to cold.
            type: dict
            suboptions:
              move_to_cold_storage_after_days:
                description: Specifies the number of days after creation that a
                  recovery point is moved to cold storage.
                type: int
              delete_after_days:
                description: Specifies the number of days after creation that a
                  recovery point is deleted. Must be greater than 90 days plus
                  move_to_cold_storage_after_days.
                type: int
      enable_continuous_backup:
        description:
          - Specifies whether Backup creates continuous backups. True causes Backup to
            create continuous backups capable of point-in-time restore (PITR). False
            (or not specified) causes Backup to create snapshot backups.
          - AWS default if not supplied is false.
        type: bool
        default: false
  advanced_backup_settings:
    description:
      - Specifies a list of advanced backup settings for each resource type.
      - These settings are only available for Windows Volume Shadow Copy Service (VSS) backup jobs.
    required: false
    type: list
    elements: dict
    suboptions:
      resource_type:
        description:
          - Specifies an object containing resource type and backup options.
          - The only supported resource type is Amazon EC2 instances with Windows Volume Shadow Copy Service (VSS).
        type: str
        choices: ['EC2']
      backup_options:
        description:
          - Specifies the backup option for a selected resource.
          - This option is only available for Windows VSS backup jobs.
        type: dict
        choices: [{'WindowsVSS': 'enabled'}, {'WindowsVSS': 'disabled'}]
  creator_request_id:
    description: Identifies the request and allows failed requests to be retried
      without the risk of running the operation twice. If the request includes a
      CreatorRequestId that matches an existing backup plan, that plan is returned.
    type: str
  tags:
    description: To help organize your resources, you can assign your own metadata to
      the resources that you create. Each tag is a key-value pair. The specified tags
      are assigned to all backups created with this plan.
    type: dict
    aliases: ['resource_tags', 'backup_plan_tags']

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
  - amazon.aws.tags
"""

EXAMPLES = r"""
- name: Create an AWSbackup plan
  amazon.aws.backup_plan:
    state: present
    backup_plan_name: elastic
    rules:
      - rule_name: daily
        target_backup_vault_name: "{{ backup_vault_name }}"
        schedule_expression: 'cron(0 5 ? * * *)'
        start_window_minutes: 60
        completion_window_minutes: 1440
- name: Delete an AWS Backup plan
  amazon.aws.backup_plan:
    backup_plan_name: elastic
    state: absent
"""

RETURN = r"""
exists:
  description: Whether the resource exists.
  returned: always
  type: bool
  sample: true
backup_plan_arn:
  description: ARN of the backup plan.
  returned: always
  type: str
  sample: arn:aws:backup:eu-central-1:111122223333:backup-plan:1111f877-1ecf-4d79-9718-a861cd09df3b
backup_plan_id:
  description: ID of the backup plan.
  returned: always
  type: str
  sample: 1111f877-1ecf-4d79-9718-a861cd09df3b
backup_plan_name:
  description: Name of the backup plan.
  returned: always
  type: str
  sample: elastic
creation_date:
  description: Creation date of the backup plan.
  returned: on create/update
  type: str
  sample: '2023-01-24T10:08:03.193000+01:00'
deletion_date:
  description: Date the backup plan was deleted.
  returned: on delete
  type: str
  sample: '2023-05-05T16:24:51.987000-04:00'
version_id:
  description: Version ID of the backup plan.
  returned: always
  type: str
  sample: ODM3MjVjNjItYWFkOC00NjExLWIwZTYtZDNiNGI5M2I0ZTY1
backup_plan:
  description: Backup plan details.
  returned: on create/update
  type: dict
  contains:
    backup_plan_name:
      description: Name of the backup plan.
      returned: always
      type: str
      sample: elastic
    rules:
      description:
        - An array of BackupRule objects, each of which specifies a scheduled task that is used to back up a selection of resources.
      returned: always
      type: list
      elements: dict
    advanced_backup_settings:
      description: Advanced backup settings of the backup plan.
      returned: when configured
      type: list
      elements: dict
      contains:
        resource_type:
          description: Resource type of the advanced settings.
          type: str
        backup_options:
          description: Backup options of the advanced settings.
          type: dict
    tags:
      description: Tags of the backup plan.
      returned: on create/update
      type: str
"""

import json
from datetime import datetime
from typing import Optional

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags
from ansible_collections.amazon.aws.plugins.module_utils.backup import get_plan_details
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # Handled by AnsibleAWSModule

ARGUMENT_SPEC = dict(
    state=dict(type="str", choices=["present", "absent"], default="present"),
    backup_plan_name=dict(required=True, type="str", aliases=["name"]),
    rules=dict(
        type="list",
        elements="dict",
        options=dict(
            rule_name=dict(required=True, type="str"),
            target_backup_vault_name=dict(required=True, type="str"),
            schedule_expression=dict(type="str", default="cron(0 5 ? * * *)"),
            start_window_minutes=dict(type="int", default=480),
            completion_window_minutes=dict(type="int", default=10080),
            lifecycle=dict(
                type="dict",
                options=dict(
                    move_to_cold_storage_after_days=dict(type="int"),
                    delete_after_days=dict(type="int"),
                ),
            ),
            recovery_point_tags=dict(type="dict"),
            copy_actions=dict(
                type="list",
                elements="dict",
                options=dict(
                    destination_backup_vault_arn=dict(required=True, type="str"),
                    lifecycle=dict(
                        type="dict",
                        options=dict(
                            move_to_cold_storage_after_days=dict(type="int"),
                            delete_after_days=dict(type="int"),
                        ),
                    ),
                ),
            ),
            enable_continuous_backup=dict(type="bool", default=False),
        ),
    ),
    advanced_backup_settings=dict(
        type="list",
        elements="dict",
        options=dict(
            resource_type=dict(type="str", choices=["EC2"]),
            backup_options=dict(
                type="dict",
                choices=[{"WindowsVSS": "enabled"}, {"WindowsVSS": "disabled"}],
            ),
        ),
    ),
    creator_request_id=dict(type="str"),
    tags=dict(type="dict", aliases=["backup_plan_tags", "resource_tags"]),
    purge_tags=dict(default=True, type="bool"),
)

REQUIRED_IF = [
    ("state", "present", ["backup_plan_name", "rules"]),
    ("state", "absent", ["backup_plan_name"]),
]

SUPPORTS_CHECK_MODE = True


def format_client_params(
    module: AnsibleAWSModule,
    plan: dict,
    tags: Optional[dict] = None,
    backup_plan_id: Optional[str] = None,
    operation: Optional[str] = None,
) -> dict:
    """
    Formats plan details to match boto3 backup client param expectations.

    module : AnsibleAWSModule object
    plan: Dict of plan details including name, rules, and advanced settings
    tags: Dict of plan tags
    backup_plan_id: ID of backup plan to update, only needed for update operation
    operation: Operation to add specific params for, either create or update
    """
    params = {
        "BackupPlan": snake_dict_to_camel_dict(
            {k: v for k, v in plan.items() if v != "backup_plan_name"},
            capitalize_first=True,
        )
    }

    if operation == "create":  # Add create-specific params
        if tags:
            params["BackupPlanTags"] = tags
        creator_request_id = module.params["creator_request_id"]
        if creator_request_id:
            params["CreatorRequestId"] = creator_request_id

    elif operation == "update":  # Add update-specific params
        params["BackupPlanId"] = backup_plan_id

    return params


def format_check_mode_response(plan_name: str, plan: dict, tags: dict, delete: bool = False) -> dict:
    """
    Formats plan details in check mode to match result expectations.

    plan_name: Name of backup plan
    plan: Dict of plan details including name, rules, and advanced settings
    tags: Optional dict of plan tags
    delete: Whether the response is for a delete action
    """
    timestamp = datetime.now().isoformat()
    if delete:
        return {
            "backup_plan_name": plan_name,
            "backup_plan_id": "",
            "backup_plan_arn": "",
            "deletion_date": timestamp,
            "version_id": "",
        }
    else:
        return {
            "backup_plan_name": plan_name,
            "backup_plan_id": "",
            "backup_plan_arn": "",
            "creation_date": timestamp,
            "version_id": "",
            "backup_plan": {
                "backup_plan_name": plan_name,
                "rules": plan["rules"],
                "advanced_backup_settings": plan["advanced_backup_settings"],
                "tags": tags,
            },
        }


def create_backup_plan(module: AnsibleAWSModule, client, create_params: dict) -> dict:
    """
    Creates a backup plan.

    module : AnsibleAWSModule object
    client : boto3 backup client connection object
    create_params : The boto3 backup client parameters to create a backup plan
    """
    try:
        response = client.create_backup_plan(**create_params)
    except (
        BotoCoreError,
        ClientError,
    ) as err:
        module.fail_json_aws(err, msg="Failed to create backup plan {err}")
    return response


def plan_update_needed(existing_plan: dict, new_plan: dict) -> bool:
    """
    Determines whether existing and new plan rules/settings match.

    existing_plan: Dict of existing plan details including rules and advanced settings,
        in snake-case format
    new_plan: Dict of existing plan details including rules and advanced settings, in
        snake-case format
    """
    update_needed = False

    # Check whether rules match
    existing_rules = json.dumps(
        [{key: val for key, val in rule.items() if key != "rule_id"} for rule in existing_plan["backup_plan"]["rules"]],
        sort_keys=True,
    )
    new_rules = json.dumps(new_plan["rules"], sort_keys=True)
    if not existing_rules or existing_rules != new_rules:
        update_needed = True

    # Check whether advanced backup settings match
    existing_advanced_backup_settings = json.dumps(
        existing_plan["backup_plan"].get("advanced_backup_settings", []),
        sort_keys=True,
    )
    new_advanced_backup_settings = json.dumps(new_plan.get("advanced_backup_settings", []), sort_keys=True)
    if existing_advanced_backup_settings != new_advanced_backup_settings:
        update_needed = True

    return update_needed


def update_backup_plan(module: AnsibleAWSModule, client, update_params: dict) -> dict:
    """
    Updates a backup plan.

    module : AnsibleAWSModule object
    client : boto3 backup client connection object
    update_params : The boto3 backup client parameters to update a backup plan
    """
    try:
        response = client.update_backup_plan(**update_params)
    except (
        BotoCoreError,
        ClientError,
    ) as err:
        module.fail_json_aws(err, msg="Failed to update backup plan {err}")
    return response


def tag_backup_plan(
    module: AnsibleAWSModule,
    client,
    new_tags: Optional[dict],
    plan_arn: str,
    current_tags: Optional[dict] = None,
):
    """
    Creates, updates, and/or removes tags on a Backup Plan resource.

    module : AnsibleAWSModule object
    client : boto3 client connection object
    new_tags : Dict of tags converted from ansible_dict to boto3 list of dicts
    plan_arn : The ARN of the Backup Plan to operate on
    curr_tags : Dict of the current tags on resource, if any
    """

    if not new_tags and not current_tags:
        return False

    if module.check_mode:
        return True

    new_tags = new_tags or {}
    current_tags = current_tags or {}
    tags_to_add, tags_to_remove = compare_aws_tags(current_tags, new_tags, purge_tags=module.params["purge_tags"])

    if not tags_to_add and not tags_to_remove:
        return False

    if tags_to_remove:
        try:
            client.untag_resource(ResourceArn=plan_arn, TagKeyList=tags_to_remove)
        except (BotoCoreError, ClientError) as err:
            module.fail_json_aws(err, msg="Failed to remove tags from the plan")

    if tags_to_add:
        try:
            client.tag_resource(ResourceArn=plan_arn, Tags=tags_to_add)
        except (BotoCoreError, ClientError) as err:
            module.fail_json_aws(err, msg="Failed to add tags to the plan")

    return True


def delete_backup_plan(module: AnsibleAWSModule, client, backup_plan_id: str) -> dict:
    """
    Deletes a Backup Plan

    module : AnsibleAWSModule object
    client : boto3 backup client connection object
    backup_plan_id : ID (*not* name or ARN) of Backup plan to delete
    """
    try:
        response = client.delete_backup_plan(BackupPlanId=backup_plan_id)
    except (BotoCoreError, ClientError) as err:
        module.fail_json_aws(err, msg="Failed to delete the Backup Plan")
    return response


def main():
    module = AnsibleAWSModule(
        argument_spec=ARGUMENT_SPEC,
        required_if=REQUIRED_IF,
        supports_check_mode=SUPPORTS_CHECK_MODE,
    )

    # Set initial result values
    result = dict(changed=False, exists=False)

    # Get supplied params from module
    client = module.client("backup")
    state = module.params["state"]
    plan_name = module.params["backup_plan_name"]
    plan = {
        "backup_plan_name": module.params["backup_plan_name"],
        "rules": [{k: v for k, v in rule.items() if v is not None} for rule in module.params["rules"] or []],
        "advanced_backup_settings": [
            {k: v for k, v in setting.items() if v is not None}
            for setting in module.params["advanced_backup_settings"] or []
        ],
    }
    tags = module.params["tags"]

    # Get existing backup plan details and ID if present
    existing_plan = get_plan_details(module, client, plan_name)
    if existing_plan:
        existing_plan_id = existing_plan[0]["backup_plan_id"]
        existing_plan = existing_plan[0]
    else:
        existing_plan = existing_plan_id = None

    if state == "present":  # Create or update plan
        if existing_plan_id is None:  # Plan does not exist, create it
            if module.check_mode:  # Use supplied params as result data in check mode
                backup_plan = format_check_mode_response(plan_name, plan, tags)
            else:
                client_params = format_client_params(module, plan, tags=tags, operation="create")
                response = create_backup_plan(module, client, client_params)
                backup_plan = get_plan_details(module, client, plan_name)[0]
            result["exists"] = True
            result["changed"] = True
            result.update(backup_plan)

        else:  # Plan exists, update as needed
            result["exists"] = True
            if plan_update_needed(existing_plan, plan):
                if not module.check_mode:
                    client_params = format_client_params(
                        module,
                        plan,
                        backup_plan_id=existing_plan_id,
                        operation="update",
                    )
                    update_backup_plan(module, client, client_params)
                result["changed"] = True
            if tag_backup_plan(
                module,
                client,
                tags,
                existing_plan["backup_plan_arn"],
                existing_plan["tags"],
            ):
                result["changed"] = True
            if module.check_mode:
                backup_plan = format_check_mode_response(plan_name, plan, tags)
            else:
                backup_plan = get_plan_details(module, client, plan_name)[0]
            result.update(backup_plan)

    elif state == "absent":  # Delete plan
        if existing_plan_id is None:  # Plan does not exist, can't delete it
            module.debug(msg=f"Backup plan {plan_name} not found.")
        else:  # Plan exists, delete it
            if module.check_mode:
                response = format_check_mode_response(plan_name, existing_plan, tags, True)
            else:
                response = delete_backup_plan(module, client, existing_plan_id)
            result["changed"] = True
            result["exists"] = False
            result.update(camel_dict_to_snake_dict(response))

    module.exit_json(**result)


if __name__ == "__main__":
    main()
