#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: backup_restore_job_info
version_added: 6.0.0
short_description: List information about backup restore jobs.
description:
    - List detailed information about AWS Backup restore jobs initiated to restore a saved resource.
author:
    - Mandar Vijay Kulkarni (@mandar242)
options:
    - to be added
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: List all restore jobs
    amazon.aws.backup_restore_job_info:

- name: List restore jobs based on Account ID
    amazon.aws.backup_restore_job_info:
        account_id: xx1234567890

- name: List restore jobs based on status and created_before time
    amazon.aws.backup_restore_job_info:
        status: completed
        created_before: "2023-02-25T00:05:36.309Z"
"""

RETURN = r"""
"""

try:
    import botocore, boto3
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def build_params_dict(module):

    parameters = {
        "ByAccountId": "account_id",
        "ByStatus": "status",
        "ByCreatedBefore": "created_before",
        "ByCreatedAfter": "created_after",
        "ByCompleteBefore": "completed_before",
        "ByCompleteAfter": "completed_after"
    }

    params_dict = {k: module.params.get(v) for k, v in parameters.items() if module.params.get(v)}

    return params_dict


@AWSRetry.jittered_backoff()
def _list_restore_jobs(connection, **params):
    import q; q('here 0'    )
    paginator = connection.get_paginator('list_restore_jobs')
    import q; q('here 1')
    return paginator.paginate(**params).build_full_result()


def list_restore_jobs(connection, module):

    params_dict = build_params_dict(module)

    try:
        response = _list_restore_jobs(connection, **params_dict)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to list restore jobs")

    snaked_restore_jobs = [camel_dict_to_snake_dict(restore_job) for restore_job in response["RestoreJobs"]]

    return snaked_restore_jobs

def main():
    argument_spec = dict(
        account_id=dict(required=False, type='str'),
        status=dict(required=False, type='str', choices=['PENDING', 'RUNNING', 'COMPLETED', 'ABORTED', 'FAILED']),
        created_before=dict(required=False, type='str'),
        created_after=dict(required=False, type='str'),
        completed_before=dict(required=False, type='str'),
        completed_after=dict(required=False, type='str'),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    backup_client = module.client("backup")

    module.require_botocore_at_least('1.25.13', reason='to list restore jobs info')

    restore_jobs = list_restore_jobs(backup_client, module)

    module.exit_json(changed=False, restore_jobs=restore_jobs)


if __name__ == "__main__":
    main()