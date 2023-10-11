#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: backup_selection_info
version_added: 6.0.0
short_description: Describe AWS Backup Selections
description:
  - Lists info about Backup Selection configuration for a given Backup Plan.
author:
  - Gomathi Selvi Srinivasan (@GomathiselviS)
  - Kristof Imre Szabo (@krisek)
  - Alina Buzachis (@alinabuzachis)
options:
  backup_plan_name:
    description:
      - Uniquely identifies the backup plan to be associated with the selection of resources.
    required: true
    type: str
    aliases:
      - plan_name
  backup_selection_names:
    description:
      - Uniquely identifies the backup plan the selections should be listed for.
    type: list
    elements: str
    aliases:
     - selection_names
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.
- name: Gather information about all backup selections
  amazon.aws.backup_selection_info:
    backup_plan_name: "{{ backup_plan_name }}"

- name: Gather information about a particular backup selection
  amazon.aws.backup_selection_info:
    backup_plan_name: "{{ backup_plan_name }}"
    backup_selection_names:
      - "{{ backup_selection_name }}"
"""

RETURN = r"""
backup_selections:
    description: List of backup selection objects. Each element consists of a dict with all the information related to that backup selection.
    type: list
    elements: dict
    returned: always
    contains:
        backup_plan_id:
            description: Backup plan id.
            returned: always
            type: str
            sample: "1111f877-1ecf-4d79-9718-a861cd09df3b"
        creation_date:
            description: Backup plan creation date.
            returned: always
            type: str
            sample: "2023-01-24T10:08:03.193000+01:00"
        iam_role_arn:
            description: IAM role arn.
            returned: always
            type: str
            sample: "arn:aws:iam::111122223333:role/system-backup"
        selection_id:
            description: Backup selection id.
            returned: always
            type: str
            sample: "1111c217-5d71-4a55-8728-5fc4e63d437b"
        selection_name:
            description: Backup selection name.
            returned: always
            type: str
            sample: elastic
        conditions:
            description: List of conditions (expressed as a dict) that are defined to assign resources to the backup plan using tags.
            returned: always
            type: dict
            sample: {}
        list_of_tags:
            description: Conditions defined to assign resources to the backup plans using tags.
            returned: always
            type: list
            elements: dict
            sample: []
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


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.backup import get_selection_details
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def main():
    argument_spec = dict(
        backup_plan_name=dict(type="str", required=True, aliases=["plan_name"]),
        backup_selection_names=dict(type="list", elements="str", aliases=["selection_names"]),
    )
    result = {}

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    try:
        client = module.client("backup", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    result["backup_selections"] = get_selection_details(
        module, client, module.params.get("backup_plan_name"), module.params.get("backup_selection_names")
    )
    module.exit_json(**camel_dict_to_snake_dict(result))


if __name__ == "__main__":
    main()
