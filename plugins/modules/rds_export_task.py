#!/usr/bin/python

# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r"""
---
module: rds_export_task
version_added: 5.0.0
short_description: Starts and cancels an export of a snapshot to Amazon S3
author: Alina Buzachis (@alinabuzachis)
description:
    - Starts an export of a snapshot to Amazon S3.
    - Cancels an export task in progress that is exporting a snapshot to Amazon S3.
options:
    state:
        description:
            - Specifies whether the export task should be C(present) or C(absent).
        choices: [ 'present', 'absent' ]
        default: present
        type: str
    export_task_id:
        description:
            - A unique identifier for the snapshot export task.
        aliases:
            - task_id
        type: str
        required: true
    source_arn:
        description:
            - The Amazon Resource Name (ARN) of the snapshot to export to Amazon S3.
        type: str
    s3_bucket_name:
        description:
            - The name of the Amazon S3 bucket to export the snapshot to.
        aliases:
            - s3_bucket
        type: str
    iam_role_arn:
        description:
            - The name of the IAM role to use for writing to the Amazon S3 bucket when exporting a snapshot.
        aliases:
            - iam_role
        type: str
    kms_key_id:
        description:
            - The ID of the Amazon Web Services KMS customer master key (CMK) to use to encrypt the snapshot exported to Amazon S3.
        type: str
        aliases:
            - key_id
    s3_prefix:
        description:
            - The Amazon S3 bucket prefix to use as the file name and path of the exported snapshot.
        type: str
    export_only:
        description:
            - The data to be exported from the snapshot.
            - If this parameter is not provided, all the snapshot data is exported.
            - Valid values are the following
            - 'C(database): Export all the data from a specified database'
            - 'C(database.table) table-name: Export a table of the snapshot.
               This format is valid only for RDS for MySQL, RDS for MariaDB, and Aurora MySQL.'
            - 'C(database.schema) schema: Export a database schema of the snapshot.
               This format is valid only for RDS for PostgreSQL and Aurora PostgreSQL.'
            - 'C(database.schema) table-name: Export a table of the database schema.
               This format is valid only for RDS for PostgreSQL and Aurora PostgreSQL.'
        type: list
        elements: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
- amazon.aws.aws_boto3
"""

EXAMPLES = r"""
- name: Export snapshot to S3
  amazon.aws.rds_export_task:
    export_task_id: "{{ export_task_id }}"
    source_arn: "{{ db_snapshot_arn }}"
    s3_bucket_name: "{{ bucket_name }}"
    iam_role_arn: "{{ iam_role_arn }}"
    kms_key_id: "{{ kms_key_arn }}"
    state: present
  register: _result_export_task

- name: Delete an export task
  amazon.aws.rds_export_task:
    export_task_id: "{{ export_task_id }}"
    state: absent
"""

RETURN = r"""

"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry


def describe_export_task():
    result = None

    try:
        result = client.describe_export_tasks(ExportTaskIdentifier=module.params.get("export_task_id"), aws_retry=True)
    except is_boto3_error_code("ExportTaskNotFound"):
        return None
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Couldn't describe export task")

    return result


def start_export_task():
    results = {}
    changed = True
    existing = None

    existing = describe_export_task()
    if existing:
        changed = False
        return changed, existing

    params = {
        "ExportTaskIdentifier": module.params.get("export_task_id"),
        "SourceArn": module.params.get("source_arn"),
        "S3BucketName": module.params.get("s3_bucket_name"),
        "IamRoleArn": module.params.get("iam_role_arn"),
        "KmsKeyId": module.params.get("kms_key_id"),
    }

    if module.params.get("s3_prefix"):
        params["S3Prefix"] = module.params.get("s3_prefix")

    if module.params.get("export_only"):
        params["ExportOnly"] = module.params.get("export_only")

    try:
        if module.check_mode:
            return changed, results

        results = client.start_export_task(**params, aws_retry=True)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't start export task")

    return changed, results


def cancel_export_task():
    results = {}
    changed = False

    try:
        if module.check_mode:
            return True, results

        results = client.cancel_export_task(ExportTaskIdentifier=module.params.get("export_task_id"), aws_retry=True)
        changed = True
    except is_boto3_error_code('ExportTaskNotFoundFault'):
        return False, results
    except is_boto3_error_code('ExportTaskNotFound'):  # pylint: disable=duplicate-except
        return False, results
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Couldn't cancel export task")

    return changed, results


def main():
    global module
    global client

    argument_spec = dict(
        state=dict(choices=["present", "absent"], default='present'),
        export_task_id=dict(type="str", aliases=['task_id'], required=True),
        source_arn=dict(type="str"),
        s3_bucket_name=dict(type="str", aliases=['s3_bucket']),
        iam_role_arn=dict(type="str", aliases=['iam_role']),
        kms_key_id=dict(type="str", aliases=['key_id']),
        s3_prefix=dict(type="str"),
        export_only=dict(type="list", elements="str"),
    )

    required_if = [
        ('state', 'present', ['export_task_id', 'source_arn', 's3_bucket_name', 'iam_role_arn', 'kms_key_id']),
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=required_if,
        supports_check_mode=True,
    )

    try:
        client = module.client("rds", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    state = module.params.get("state")

    if state == "present":
        changed, results = start_export_task()
    else:
        changed, results = cancel_export_task()

    module.exit_json(changed=changed, **results)


if __name__ == "__main__":
    main()
