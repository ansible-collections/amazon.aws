#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
module: backup_selection
short_description: Create, delete and modify AWS Backup selection
version_added: 6.0.0
description:
  - Manages AWS Backup selections.
  - For more information see the AWS documentation for backup selections
    U(https://docs.aws.amazon.com/aws-backup/latest/devguide/assigning-resources.html).
options:
  backup_plan_name:
    description:
      - Uniquely identifies the backup plan to be associated with the selection of resources.
    required: true
    type: str
    aliases:
      - plan_name
  backup_selection_name:
    description:
      - The display name of a resource selection document. Must contain 1 to 50 alphanumeric or '-_.' characters.
    required: true
    type: str
    aliases:
      - selection_name
  iam_role_arn:
    description:
      - The ARN of the IAM role that Backup uses to authenticate when backing up the target resource.
    type: str
  resources:
    description:
      - A list of Amazon Resource Names (ARNs) to assign to a backup plan. The maximum number of ARNs is 500 without wildcards,
        or 30 ARNs with wildcards. If you need to assign many resources to a backup plan, consider a different resource selection
        strategy, such as assigning all resources of a resource type or refining your resource selection using tags.
    type: list
    elements: str
  list_of_tags:
    description:
      - A list of conditions that you define to assign resources to your backup plans using tags.
      - Condition operators are case sensitive.
      - When you specify more than one condition in O(list_of_tags), you assign all resources that match AT LEAST ONE condition (using OR logic).
    type: list
    elements: dict
    suboptions:
        condition_type:
            description:
            - An operation applied to a key-value pair used to assign resources to your backup plan.
            - Condition only supports V(STRINGEQUALS).
            type: str
        condition_key:
            description:
            - The key in a key-value pair.
            type: str
        condition_value:
            description:
            - The value in a key-value pair.
            type: str
  not_resources:
    description:
      - A list of Amazon Resource Names (ARNs) to exclude from a backup plan. The maximum number of ARNs is 500 without wildcards,
        or 30 ARNs with wildcards. If you need to exclude many resources from a backup plan, consider a different resource
        selection strategy, such as assigning only one or a few resource types or refining your resource selection using tags.
    type: list
    elements: str
  conditions:
    description:
      - A list of conditions (expressed as a dict) that you define to assign resources to your backup plans using tags.
      - When you specify more than one condition in I(conditions), you only assign the resources that match ALL conditions (using AND logic).
      - O(conditions) supports V(string_equals), V(string_like), V(string_not_equals), and V(string_not_like). O(list_of_tags) only supports V(string_equals).
    type: dict
    suboptions:
      string_equals:
        description:
          - Filters the values of your tagged resources for only those resources that you tagged with the same value.
        type: list
        default: []
        elements: dict
        suboptions:
          condition_key:
            description:
              - The key in a key-value pair.
              - O(conditions.string_equals.condition_key) in the O(conditions) option must use the AWS resource tag prefix, e.g. 'aws:ResourceTag/key-name'
            type: str
          condition_value:
            description: The value in a key-value pair.
            type: str
      string_like:
        description:
          - Filters the values of your tagged resources for matching tag values with the use of a wildcard character (*) anywhere in the string.
            For example, "prod*" or "*rod*" matches the tag value "production".
        type: list
        default: []
        elements: dict
        suboptions:
          condition_key:
            description:
              - The key in a key-value pair.
              - O(conditions.string_like.condition_key) in the O(conditions) option must use the AWS resource tag prefix, e.g. 'aws:ResourceTag/key-name'
            type: str
          condition_value:
            description: The value in a key-value pair.
            type: str
      string_not_equals:
        description:
          - Filters the values of your tagged resources for only those resources that you tagged that do not have the same value.
        type: list
        default: []
        elements: dict
        suboptions:
          condition_key:
            description:
              - The key in a key-value pair.
              - O(conditions.string_not_equals.condition_key) in the O(conditions) option must use the AWS resource tag prefix, e.g. 'aws:ResourceTag/key-name'
            type: str
          condition_value:
            description: The value in a key-value pair.
            type: str
      string_not_like:
        description:
          - Filters the values of your tagged resources for non-matching tag values with the use of a wildcard character (*) anywhere in the string.
        type: list
        default: []
        elements: dict
        suboptions:
          condition_key:
            description:
              - The key in a key-value pair.
              - O(conditions.string_not_like.condition_key) in the O(conditions) option must use the AWS resource tag prefix, e.g. 'aws:ResourceTag/key-name'
            type: str
          condition_value:
            description: The value in a key-value pair.
            type: str
  state:
    description:
      - Create, delete a backup selection.
    default: present
    choices: ['present', 'absent']
    type: str
author:
  - Kristof Imre Szabo (@krisek)
  - Alina Buzachis (@alinabuzachis)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""


EXAMPLES = r"""
- name: Create backup selection
  amazon.aws.backup_selection:
    selection_name: elastic
    backup_plan_name: test-backup-plan
    iam_role_arn: arn:aws:iam::111122223333:role/system-backup
    resources:
      - arn:aws:elasticfilesystem:*:*:file-system/*

- name: Create backup selection, assign resources using tags
  amazon.aws.backup_selection:
    selection_name: elastic
    backup_plan_name: test-backup-plan
    iam_role_arn: arn:aws:iam::111122223333:role/system-backup
    list_of_tags:
      - condition_type: STRINGEQUALS
        condition_key: Owner
        condition_value: Dev01
"""


RETURN = r"""
backup_selection:
  description: Backup selection details.
  returned: always
  type: complex
  contains:
    backup_plan_id:
      description: ID of the backup plan.
      returned: always
      type: str
      sample: "1111f877-1ecf-4d79-9718-a861cd09df3b"
    creation_date:
      description: Creation date of the backup plan.
      returned: on create/update
      type: str
      sample: '2023-01-24T10:08:03.193000+01:00'
    iam_role_arn:
      description: The ARN of the IAM role that Backup uses to authenticate when backing up the target resource.
      returned: always
      type: str
      sample: "arn:aws:iam::111122223333:role/system-backup"
    selection_id:
      description: Backup selection id.
      returned: always
      type: str
      sample: "1111c217-5d71-4a55-8728-5fc4e63d437b"
    selection_name:
      description: The display name of a resource selection document.
      returned: always
      type: str
      sample: elastic
    conditions:
      description: A list of conditions that defines how resources are assigned to backup plans using tags.
      returned: always
      type: dict
      sample: {
                "string_equals": [],
                "string_like": [],
                "string_not_equals": [],
                "string_not_like": []
            }
      contains:
        string_equals:
          description: Filters the values of tagged resources for only those resources that are tagged with the same value.
          returned: always
          type: list
          sample: []
        string_like:
          description: Filters the values of tagged resources for matching tag values with the use of a wildcard character (*) anywhere in the string.
          returned: always
          type: list
          sample: []
        string_not_equals:
          description: Filters the values of tagged resources for only those resources that are not tagged with the same value.
          returned: always
          type: list
          sample: []
        string_not_like:
          description: Filters the values of tagged resources for non-matching tag values with the use of a wildcard character (*) anywhere in the string.
          returned: always
          type: list
          sample: []
    list_of_tags:
      description: Conditions defined to assign resources to the backup plans using tags.
      returned: always
      type: list
      elements: dict
      sample: [
                {
                    "condition_key": "Environment",
                    "condition_type": "STRINGEQUALS",
                    "condition_value": "Dev"
                }
            ]
      contains:
        condition_key:
          description: The key in a key-value pair.
          returned: always
          type: str
          sample: "Environment"
        condition_type:
          description: An operation applied to a key-value pair used to assign resources to backup plan.
          returned: always
          type: str
          sample: "STRINGEQUALS"
        condition_value:
          description: The value in a key-value pair.
          returned: always
          type: str
          sample: "Dev"
    not_resources:
      description: List of Amazon Resource Names (ARNs) that are excluded from the backup plan.
      returned: always
      type: list
      sample: []
    resources:
      description: List of Amazon Resource Names (ARNs) that are assigned to the backup plan.
      returned: always
      type: list
      sample: []
"""

import json

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.backup import get_plan_details
from ansible_collections.amazon.aws.plugins.module_utils.backup import get_selection_details
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry


def check_for_update(current_selection, backup_selection_data, iam_role_arn):
    update_needed = False
    if current_selection[0].get("IamRoleArn", None) != iam_role_arn:
        update_needed = True

    fields_to_check = ["Resources", "ListOfTags", "NotResources", "Conditions"]
    for field_name in fields_to_check:
        field_value_from_aws = json.dumps(current_selection[0].get(field_name, []), sort_keys=True)
        new_field_value = json.dumps(backup_selection_data.get(field_name, []), sort_keys=True)
        if new_field_value != field_value_from_aws:
            if field_name != "Conditions":
                update_needed = True
            elif not (  # Check that Conditions values are not both empty
                field_value_from_aws
                == '{"StringEquals": [], "StringLike": [], "StringNotEquals": [], "StringNotLike": []}'  # Default AWS Conditions return value
                and new_field_value == "[]"
            ):
                update_needed = True
    return update_needed


def main():
    argument_spec = dict(
        backup_selection_name=dict(type="str", required=True, aliases=["selection_name"]),
        backup_plan_name=dict(type="str", required=True, aliases=["plan_name"]),
        iam_role_arn=dict(type="str"),
        resources=dict(type="list", elements="str"),
        conditions=dict(
            type="dict",
            options=dict(
                string_equals=dict(
                    type="list",
                    default=[],
                    elements="dict",
                    options=dict(
                        condition_key=dict(type="str", no_log=False),
                        condition_value=dict(type="str"),
                    ),
                ),
                string_like=dict(
                    type="list",
                    default=[],
                    elements="dict",
                    options=dict(
                        condition_key=dict(type="str", no_log=False),
                        condition_value=dict(type="str"),
                    ),
                ),
                string_not_equals=dict(
                    type="list",
                    default=[],
                    elements="dict",
                    options=dict(
                        condition_key=dict(type="str", no_log=False),
                        condition_value=dict(type="str"),
                    ),
                ),
                string_not_like=dict(
                    type="list",
                    default=[],
                    elements="dict",
                    options=dict(
                        condition_key=dict(type="str", no_log=False),
                        condition_value=dict(type="str"),
                    ),
                ),
            ),
        ),
        not_resources=dict(type="list", elements="str"),
        list_of_tags=dict(
            type="list",
            elements="dict",
            options=dict(
                condition_type=dict(type="str"),
                condition_key=dict(type="str", no_log=False),
                condition_value=dict(type="str"),
            ),
        ),
        state=dict(default="present", choices=["present", "absent"]),
    )
    required_if = [
        ("state", "present", ["backup_selection_name", "backup_plan_name", "iam_role_arn"]),
        ("state", "absent", ["backup_selection_name", "backup_plan_name"]),
    ]
    module = AnsibleAWSModule(argument_spec=argument_spec, required_if=required_if, supports_check_mode=True)
    state = module.params.get("state")
    backup_selection_name = module.params.get("selection_name")
    backup_plan_name = module.params.get("backup_plan_name")
    iam_role_arn = module.params.get("iam_role_arn")
    resources = module.params.get("resources")
    list_of_tags = module.params.get("list_of_tags")
    not_resources = module.params.get("not_resources")
    conditions = module.params.get("conditions")

    try:
        client = module.client("backup", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    results = {"changed": False, "exists": False, "backup_selection": {}}

    current_selection = get_selection_details(module, client, backup_plan_name, backup_selection_name)
    results["current_selection"] = current_selection

    if state == "present":
        # build data specified by user
        update_needed = False
        backup_selection_data = {"SelectionName": backup_selection_name, "IamRoleArn": iam_role_arn}
        if resources:
            backup_selection_data["Resources"] = resources
        if list_of_tags:
            backup_selection_data["ListOfTags"] = snake_dict_to_camel_dict(list_of_tags, capitalize_first=True)
        if not_resources:
            backup_selection_data["NotResources"] = not_resources
        if conditions:
            backup_selection_data["Conditions"] = snake_dict_to_camel_dict(conditions, capitalize_first=True)

        if current_selection:
            results["exists"] = True
            update_needed = check_for_update(current_selection, backup_selection_data, iam_role_arn)
            if update_needed:
                if module.check_mode:
                    results["changed"] = True
                    module.exit_json(**results, msg="Would have created selection if not in check mode")

                try:
                    client.delete_backup_selection(
                        aws_retry=True,
                        SelectionId=current_selection[0]["SelectionId"],
                        BackupPlanId=current_selection[0]["BackupPlanId"],
                    )
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    module.fail_json_aws(e, msg="Failed to delete selection")
            elif not update_needed:
                results["exists"] = True
        # state is present but backup vault doesnt exist
        if not current_selection or update_needed:
            results["changed"] = True
            results["exists"] = True
            plan = get_plan_details(module, client, backup_plan_name)

            if module.check_mode:
                module.exit_json(**results, msg="Would have created selection if not in check mode")
            try:
                client.create_backup_selection(
                    BackupSelection=backup_selection_data, BackupPlanId=plan[0]["backup_plan_id"]
                )
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Failed to create selection")

        new_selection = get_selection_details(module, client, backup_plan_name, backup_selection_name)
        results["backup_selection"] = camel_dict_to_snake_dict(*new_selection)

    elif state == "absent":
        if current_selection:
            results["changed"] = True
            if module.check_mode:
                module.exit_json(**results, msg="Would have deleted backup selection if not in check mode")
            try:
                client.delete_backup_selection(
                    aws_retry=True,
                    SelectionId=current_selection[0]["SelectionId"],
                    BackupPlanId=current_selection[0]["BackupPlanId"],
                )
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Failed to delete selection")

    module.exit_json(**results)


if __name__ == "__main__":
    main()
