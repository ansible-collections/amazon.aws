#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: backup_selection_info
version_added: 6.0.0
short_description: Describe AWS Backup Plans
description:
  - Lists info about Backup Selection configuration for a given Backup Plan.
author:
  - Gomathi Selvi Srinivasan (@GomathiselviS)
  - Kristof Imre Szabo (@krisek)
  - Alina Buzachis (@alinabuzachis)
options:
  backup_plan_name:
    description:
      - Uniquely identifies the backup plan the selections should be listed for.
    required: true
    type: str
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.
# Gather information about all backup selections
- amazon.aws.backup_selection_info
# Gather information about a particular backup selection
- amazon.aws.backup_selection_info:
    backup_selection_names:
      - elastic
"""

RETURN = r"""
backup_selections:
    description: List of backup selection objects. Each element consists of a dict with all the information related to that backup selection.
    type: list
    elements: dict
    returned: always
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
        conditions:
            description: list of conditions (expressed as a dict) that are defined to assign resources to the backup plan using tags
            returned: always
            type: dict
            sample:
        list_of_tags:
            description: conditions defined to assign resources to the backup plans using tags
            returned: always
            type: list
            sample:
        not_resources:
            description: list of Amazon Resource Names (ARNs) that are excluded from the backup plan
            returned: always
            type: list
            sample:
        resources:
            description: list of Amazon Resource Names (ARNs) that are assigned to the backup plan
            returned: always
            type: list
            sample:
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.backup import get_selection_details


def get_backup_selections(connection, module, backup_plan_id):
    all_backup_selections = []
    try:
        result = connection.get_paginator("list_backup_selections")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to get the backup plans.")
    for page in result.paginate(BackupPlanId=backup_plan_id):
        for backup_selection in page["BackupSelectionsList"]:
            all_backup_selections.append(backup_selection["SelectionId"])
    return all_backup_selections


def get_backup_selection_detail(connection, module):
    output = []
    result = {}
    backup_plan_id = module.params.get("backup_plan_id")
    backup_selection_list = get_backup_selections(connection, module, backup_plan_id)

    for backup_selection in backup_selection_list:
        try:
            output.append(connection.get_backup_selection(SelectionId=backup_selection, BackupPlanId=backup_plan_id, aws_retry=True))
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to describe selection SelectionId={0} BackupPlanId={1}".format(backup_selection, backup_plan_id))

    # Turn the boto3 result in to ansible_friendly_snaked_names
    snaked_backup_selection = []

    for backup_selection in output:
        snaked_backup_selection.append(camel_dict_to_snake_dict(backup_selection))

    # Turn the boto3 result in to ansible friendly dictionary
    for v in snaked_backup_selection:
        if "tags_list" in v:
            v["tags"] = boto3_tag_list_to_ansible_dict(v["tags_list"], "key", "value")
            del v["tags_list"]
        if "response_metadata" in v:
            del v["response_metadata"]
        if "backup_selection" in v:
            for backup_selection_key in v['backup_selection']:
                v[backup_selection_key] = v['backup_selection'][backup_selection_key]
        del v["backup_selection"]
    result["backup_selections"] = snaked_backup_selection
    return result


def main():
    argument_spec = dict(
        backup_plan_id=dict(type="str", required=True),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    try:
        connection = module.client("backup", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")
    
    get_backup_selection_detail(connection, module)

if __name__ == "__main__":
    main()
