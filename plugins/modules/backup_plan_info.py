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
  - Alina Buzachis (@alinabuzachis)
options:
  backup_plan_names:
    type: list
    elements: str
    description:
      - Specifies a list of plan names.
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.
- name: Gather information about all backup plans
  amazon.aws.backup_plan_info:

- name: Gather information about a particular backup plan
  amazon.aws.backup_plan_info:
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
            returned: always
            description: Detailed information about the backup plan.
            type: list
            elements: dict
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


from ansible_collections.amazon.aws.plugins.module_utils.backup import get_plan_details
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def get_all_backup_plans_info(client):
    paginator = client.get_paginator("list_backup_plans")
    return paginator.paginate().build_full_result()


def get_backup_plan_detail(client, module):
    backup_plan_list = []
    backup_plan_names = module.params.get("backup_plan_names")

    if backup_plan_names is None:
        backup_plan_names = []
        backup_plan_list_info = get_all_backup_plans_info(client)["BackupPlansList"]
        for backup_plan in backup_plan_list_info:
            backup_plan_names.append(backup_plan["BackupPlanName"])

    for name in backup_plan_names:
        backup_plan_list.extend(get_plan_details(module, client, name))

    module.exit_json(**{"backup_plans": backup_plan_list})


def main():
    argument_spec = dict(
        backup_plan_names=dict(type="list", elements="str"),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    try:
        connection = module.client("backup", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    get_backup_plan_detail(connection, module)


if __name__ == "__main__":
    main()
