#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: backup_restore_job_info
version_added: 6.0.0
short_description: List information about backup restore jobs
description:
    - List detailed information about AWS Backup restore jobs initiated to restore a saved resource.
author:
    - Mandar Vijay Kulkarni (@mandar242)
options:
  account_id:
    description:
      - The account ID to list the restore jobs from.
    required: false
    type: str
  status:
    description:
      - Status of restore jobs to filter the result based on job status.
    required: false
    choices: ['PENDING', 'RUNNING', 'COMPLETED', 'ABORTED', 'FAILED']
    type: str
  created_before:
    description:
      - Specified date to filter result based on the restore job creation datetime.
      - If specified, only the restore jobs created before the specified datetime will be returned.
      - The date must be in Unix format and Coordinated Universal Time (UTC), example "2023-02-25T00:05:36.309Z".
    required: false
    type: str
  created_after:
    description:
      - Specified date to filter result based on the restore job creation datetime.
      - If specified, only the restore jobs created after the specified datetime will be returned.
      - The date must be in Unix format and Coordinated Universal Time (UTC), example "2023-02-25T00:05:36.309Z".
    required: false
    type: str
  completed_before:
    description:
      - Specified date to filter result based on the restore job completion datetime.
      - If specified, only the restore jobs created before the specified datetime will be returned.
      - The date must be in Unix format and Coordinated Universal Time (UTC), example "2023-02-25T00:05:36.309Z".
    required: false
    type: str
  completed_after:
    description:
      - Specified date to filter result based on the restore job completion datetime.
      - If specified, only the restore jobs created after the specified datetime will be returned.
      - The date must be in Unix format and Coordinated Universal Time (UTC), example "2023-02-25T00:05:36.309Z".
    required: false
    type: str
  restore_job_id:
      description:
        - ID of the restore job to get information about.
        - This parameter is mutually exlusive with all other parameters.
      required: false
      type: str
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: List all restore jobs
  amazon.aws.backup_restore_job_info:

- name: List specific restore job's info by job ID
  amazon.aws.backup_restore_job_info:
    restore_job_id: "52BEE289-xxxx-xxxx-xxxx-47DCAA2E7ACD"

- name: List restore jobs based on Account ID
  amazon.aws.backup_restore_job_info:
    account_id: xx1234567890

- name: List restore jobs based on status and created_before time
  amazon.aws.backup_restore_job_info:
    status: completed
    created_before: "2023-02-25T00:05:36.309Z"
"""

RETURN = r"""
restore_jobs:
    returned: always
    description:
        - restore jobs that match the provided filters.
        - Each element consists of a dict with details related to that restore job.
    type: list
    elements: dict
    contains:
        account_id:
            description:
                - The account ID that owns the restore job.
            type: str
            returned: if restore job exists
            sample: "123456789012"
        created_resource_arn:
            description:
                - An Amazon Resource Name (ARN) that uniquely identifies a resource whose recovery point is being restored.
                - The format of the ARN depends on the resource type of the backed-up resource.
            type: str
            returned: if restore job exists
            sample: "arn:aws:ec2:us-east-2:xxxxxxxxxx..."
        creation_date:
            description:
                - The date and time that a restore job is created, in Unix format and Coordinated Universal Time (UTC).
            type: str
            returned: if restore job exists
            sample: "2023-03-13T15:53:07.172000-07:00"
        iam_role_arn:
            description:
                - The IAM role ARN used to create the target recovery point.
            type: str
            returned: if restore job exists
            sample: "arn:aws:ec2:us-east-2:xxxxxxxxxx..."
        percent_done:
            description:
                - The estimated percentage that is complete of a job at the time the job status was queried.
            type: str
            returned: if restore job exists
            sample: "0.00%"
        recovery_point_arn:
            description:
                - An ARN that uniquely identifies a recovery point.
            type: str
            returned: if restore job exists
            sample: "arn:aws:ec2:us-east-2:xxxxxxxxxx..."
        restore_job_id:
            description:
                - The ID of the job that restores a recovery point.
            type: str
            returned: if restore job exists
            sample: "AAAA1234-1D1D-1234-3F8E-1EB111EEEE00"
        status:
            description:
                - The state of the job initiated by Backup to restore a recovery point.
            type: str
            returned: if restore job exists
            sample: "COMPLETED"
"""

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def build_request_args(account_id, status, created_before, created_after, completed_before, completed_after):
    request_args = {
        "ByAccountId": account_id if account_id else "",
        "ByStatus": status if status else "",
        "ByCreatedBefore": created_before if created_before else "",
        "ByCreatedAfter": created_after if created_after else "",
        "ByCompleteBefore": completed_before if completed_before else "",
        "ByCompleteAfter": completed_after if completed_after else "",
    }

    request_args = {k: v for k, v in request_args.items() if v}

    return request_args


def _describe_restore_job(connection, module, restore_job_id):
    try:
        response = connection.describe_restore_job(RestoreJobId=restore_job_id)
        response.pop("ResponseMetadata", None)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg=f"Failed to describe restore job with ID: {restore_job_id}")

    return [camel_dict_to_snake_dict(response)]


@AWSRetry.jittered_backoff()
def _list_restore_jobs(connection, **params):
    paginator = connection.get_paginator("list_restore_jobs")
    return paginator.paginate(**params).build_full_result()


def list_restore_jobs(connection, module, request_args):
    try:
        response = _list_restore_jobs(connection, **request_args)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to list restore jobs")

    return [camel_dict_to_snake_dict(restore_job) for restore_job in response["RestoreJobs"]]


def main():
    argument_spec = dict(
        account_id=dict(required=False, type="str"),
        status=dict(required=False, type="str", choices=["PENDING", "RUNNING", "COMPLETED", "ABORTED", "FAILED"]),
        created_before=dict(required=False, type="str"),
        created_after=dict(required=False, type="str"),
        completed_before=dict(required=False, type="str"),
        completed_after=dict(required=False, type="str"),
        restore_job_id=dict(required=False, type="str"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    backup_client = module.client("backup")

    module.require_botocore_at_least("1.25.13", reason="to list restore jobs info")

    request_args = build_request_args(
        account_id=module.params["account_id"],
        status=module.params["status"],
        created_before=module.params["created_before"],
        created_after=module.params["created_after"],
        completed_before=module.params["completed_before"],
        completed_after=module.params["completed_after"],
    )

    if module.params.get("restore_job_id"):
        restore_jobs = _describe_restore_job(backup_client, module, module.params.get("restore_job_id"))
    else:
        restore_jobs = list_restore_jobs(backup_client, module, request_args)

    module.exit_json(changed=False, restore_jobs=restore_jobs)


if __name__ == "__main__":
    main()
