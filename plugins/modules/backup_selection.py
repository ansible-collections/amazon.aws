#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule

DOCUMENTATION = r"""
module: backup_selection
short_description: create, delete and modify AWS Backup selection
version_added: 6.0.0
description:
  - Manages AWS Backup selections.
  - For more information see the AWS documentation for backup selections
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
  - Alina Buzachis (@alinabuzachis)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""


EXAMPLES = r"""
- name: create backup selection
  backup_selection:
    selection_name: elastic
    backup_plan_id: 1111f877-1ecf-4d79-9718-a861cd09df3b
    iam_role_arn: arn:aws:iam::111122223333:role/system-backup
    resources:
    - arn:aws:elasticfilesystem:*:*:file-system/*
"""


RETURN = r"""
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
"""
try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.backup import get_selection_details


def main():
    argument_spec = dict(
        selection_name=dict(type="str", required=True),
        backup_plan_name=dict(type="str", required=True),
        iam_role_arn=dict(type="str", required=True),
        resources=dict(type="list", required=False),
        purge_tags=dict(default=True, type="bool"),
        state=dict(default="present", choices=["present", "absent"]),
    )
    required_if = [
        ("state", "present", ["selection_name", "backup_plan_id", "iam_role_arn"]),
        ("state", "absent", ["selection_name", "backup_plan_id"]),
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

    results = {"changed": False, "exists": False}

    current_selection = get_selection_details(module, client, backup_plan_name, backup_selection_name)

    if state == "present":
        # build data specified by user
        backup_selection_data = {"SelectionName": backup_selection_name, "IamRoleArn": iam_role_arn}
        if resources:
            backup_selection_data["Resources"] = resources
        if list_of_tags:
            backup_selection_data["ListOfTags"] = list_of_tags
        if not_resources:
            backup_selection_data["NotResources"] = not_resources
        if conditions:
            backup_selection_data["Conditions"] = conditions

        if current_selection:
            results["exists"] = True
            results["backup_selection"] = current_selection[0]
        else:
            results["changed"] = True
            results["exists"] = True
            if module.check_mode:
                module.exit_json(**results, msg="Would have created selection if not in check mode")
            try:
              client.create_backup_selection(
                  BackupSelection=backup_selection_data, BackupPlanId=current_selection[0]["backup_plan_id"]
              )
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Failed to create selection")

            new_selection = get_selection_details(module, client, backup_plan_name, backup_selection_name)
            results["backup_selection"] = new_selection[0]

    elif state == "absent":
        if current_selection:
            results["changed"] = True
            if module.check_mode:
                module.exit_json(**results, msg="Would have deleted backup selection if not in check mode")
            try:
                client.delete_backup_selection(
                    aws_retry=True, SelectionId=current_selection[0]["selection_id"], BackupPlanId=current_selection[0]["backup_plan_id"]
                )
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Failed to delete selection")

    module.exit_json(**results)


if __name__ == "__main__":
    main()
