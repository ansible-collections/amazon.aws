#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: backup_plan_info
version_added: 6.0.0
short_description: Describe AWS Backup Plans
description:
  - Lists info about Backup Plan configuration.
author:
  - Gomathi Selvi Srinivasan (@GomathiselviS)
  - Kristof Imre Szabo (@krisek)
options:
  backup_plan_names:
    type: list
    elements: str
    default: []
    description:
      - Specifies a list of plan names.
      - If an empty list is specified, information for the backup plans in the current region is returned.
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.
# Gather information about all backup plans
- amazon.aws.backup_plan_info
# Gather information about a particular backup plan
- amazon.aws.backup_plan_info:
    backup plan_names:
      - elastic
"""

RETURN = r"""
backup_plans:
    description: List of backup plan objects. Each element consists of a dict with all the information related to that backup plan.
    type: list
    elements: dict
    returned: always
    contains:
        backup_plan_arn:
            description: ARN of the backup plan.
            type: str
            sample: arn:aws:backup:eu-central-1:111122223333:backup-plan:1111f877-1ecf-4d79-9718-a861cd09df3b
        backup_plan_id:
            description: Id of the backup plan.
            type: str
            sample: 1111f877-1ecf-4d79-9718-a861cd09df3b
        backup_plan_name:
            description: Name of the backup plan.
            type: str
            sample: elastic
        creation_date:
            description: Creation date of the backup plan.
            type: str
            sample: '2023-01-24T10:08:03.193000+01:00'
        last_execution_date:
            description: Last execution date of the backup plan.
            type: str
            sample: '2023-03-24T06:30:08.250000+01:00'
        tags:
            description: Tags of the backup plan
            type: str
        version_id:
            description: Version id of the backup plan
            type: str
        backup_plan:
            elements: dict
            returned: always
            description: Detailed information about the backup plan.
            contains:
                backup_plan_name:
                    description: Name of the backup plan.
                    type: str
                    sample: elastic
                advanced_backup_settings:
                    description: Advanced backup settings of the backup plan
                    type: list
                    elements: dict
                    contains:
                        resource_type:
                            description: Resource type of the advanced setting
                            type: str
                        backup_options:
                            description: Options of the advanced setting
                            type: dict
                rules:
                    description:
                    - An array of BackupRule objects, each of which specifies a scheduled task that is used to back up a selection of resources.
                    type: list
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.backup import get_backup_resource_tags


def get_backup_plans(connection, module, backup_plan_name_list):
    all_backup_plans = []
    try:
        result = connection.get_paginator("list_backup_plans")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to get the backup plans.")
    for page in result.paginate():
        for backup_plan in page["BackupPlansList"]:
            if backup_plan["BackupPlanName"] in backup_plan_name_list or len(backup_plan_name_list) == 0:
                all_backup_plans.append(backup_plan["BackupPlanId"])
    return all_backup_plans


def get_backup_plan_detail(connection, module):
    output = []
    result = {}
    backup_plan_name_list = module.params.get("backup_plan_names")
    backup_plan_id_list = get_backup_plans(connection, module, backup_plan_name_list)

    for backup_plan_id in backup_plan_id_list:
        try:
            output.append(connection.get_backup_plan(BackupPlanId=backup_plan_id, aws_retry=True))
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to describe vault {0}".format(backup_plan_id))

    # Turn the boto3 result in to ansible_friendly_snaked_names
    snaked_backup_plan = []

    for backup_plan in output:
        try:
            module.params["resource"] = backup_plan.get("BackupPlanArn", None)
            tag_dict = get_backup_resource_tags(module, connection)
            backup_plan.update({"tags": tag_dict})
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.warn("Failed to get the backup plan tags - {0}".format(e))
        snaked_backup_plan.append(camel_dict_to_snake_dict(backup_plan))

    # Turn the boto3 result in to ansible friendly tag dictionary
    for v in snaked_backup_plan:
        if "tags_list" in v:
            v["tags"] = boto3_tag_list_to_ansible_dict(v["tags_list"], "key", "value")
            del v["tags_list"]
        if "response_metadata" in v:
            del v["response_metadata"]
        v["backup_plan_name"] = v["backup_plan"]["backup_plan_name"]
    result["backup_plans"] = snaked_backup_plan
    return result


def main():
    argument_spec = dict(
        backup_plan_names=dict(type="list", elements="str", default=[]),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    try:
        connection = module.client("backup", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")
    result = get_backup_plan_detail(connection, module)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
