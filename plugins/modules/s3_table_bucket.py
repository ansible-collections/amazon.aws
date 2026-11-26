#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: s3_table_bucket
version_added: 12.2.0
short_description: Create, update or delete an S3 table bucket
description:
  - Create, update or delete an Amazon S3 Tables table bucket.
  - Does not manage namespaces, tables, or bucket policy.
author:
  - "Jan Likar (@JanLikar)"
options:
  state:
    description:
      - Create or delete the table bucket.
    choices: [present, absent]
    default: present
    type: str
  table_bucket_name:
    description:
      - The name of the table bucket.
      - Table bucket names are immutable; changing this value targets a different bucket rather
        than renaming the existing one.
    required: true
    aliases: ["name"]
    type: str
  encryption_configuration:
    description:
      - The encryption configuration to apply to the table bucket.
      - When not specified on an existing bucket, the current encryption configuration is preserved.
      - There is no option in this module to remove an existing custom encryption configuration.
    type: dict
    suboptions:
      sse_algorithm:
        description:
          - The server-side encryption algorithm to use.
        required: true
        choices: ["AES256", "aws:kms"]
        type: str
      kms_key_arn:
        description:
          - The ARN of the KMS key to use for encryption.
          - Required when O(encryption_configuration.sse_algorithm=aws:kms).
        type: str
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
  - amazon.aws.tags
notes:
  - >-
    The following IAM actions are required: C(s3tables:ListTableBuckets), C(s3tables:GetTableBucket),
    C(s3tables:CreateTableBucket), C(s3tables:DeleteTableBucket); C(s3tables:ListTagsForResource),
    C(s3tables:TagResource) and C(s3tables:UntagResource) when O(tags) is specified; and
    C(s3tables:GetTableBucketEncryption) and C(s3tables:PutTableBucketEncryption) when
    O(encryption_configuration) is specified.
  - >-
    Amazon S3 Tables is available only in selected AWS Regions, see the
    U(https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-tables-regions-quotas.html) guide.
seealso:
  - module: amazon.aws.s3_table_bucket_info
    description: Retrieve information about S3 table buckets.
"""

EXAMPLES = r"""
- name: Create an S3 table bucket
  amazon.aws.s3_table_bucket:
    table_bucket_name: "my-table-bucket"
    tags:
      Environment: "Test"

- name: Create an S3 table bucket encrypted with a customer managed KMS key
  amazon.aws.s3_table_bucket:
    table_bucket_name: "my-table-bucket"
    encryption_configuration:
      sse_algorithm: "aws:kms"
      kms_key_arn: "arn:aws:kms:us-east-1:123456789012:key/1234abcd-12ab-34cd-56ef-1234567890ab"

- name: Delete an S3 table bucket
  amazon.aws.s3_table_bucket:
    table_bucket_name: "my-table-bucket"
    state: absent
"""

RETURN = r"""
table_bucket:
  description: Information about the S3 table bucket.
  returned: on success when O(state=present)
  type: dict
  contains:
    arn:
      description: The Amazon Resource Name (ARN) of the table bucket.
      returned: always
      type: str
      sample: "arn:aws:s3tables:us-east-1:123456789012:bucket/my-table-bucket"
    name:
      description: The name of the table bucket.
      returned: always
      type: str
      sample: "my-table-bucket"
    owner_account_id:
      description: The ID of the account that owns the table bucket.
      returned: always
      type: str
      sample: "123456789012"
    created_at:
      description: The date and time the table bucket was created.
      returned: always
      type: str
      sample: "2025-01-01T12:00:00+00:00"
    table_bucket_id:
      description: The unique identifier for the table bucket.
      returned: always
      type: str
      sample: "abcd1234-ab12-cd34-ef56-abcdef123456"
    type:
      description: The type of the table bucket.
      returned: always
      type: str
      sample: "customer"
    tags:
      description: Dictionary of tags applied to the table bucket.
      returned: when O(tags) is specified
      type: dict
      sample: {"Environment": "Test"}
    encryption_configuration:
      description: The encryption configuration of the table bucket.
      returned: when O(encryption_configuration) is specified
      type: dict
      contains:
        sse_algorithm:
          description: The server-side encryption algorithm used.
          returned: always
          type: str
          sample: "aws:kms"
        kms_key_arn:
          description: The ARN of the KMS key used for encryption.
          returned: when O(encryption_configuration.sse_algorithm=aws:kms)
          type: str
          sample: "arn:aws:kms:us-east-1:123456789012:key/1234abcd-12ab-34cd-56ef-1234567890ab"
"""

from typing import Any
from typing import Dict
from typing import Optional

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.s3tables import (
    AnsibleS3TablesError,
    create_table_bucket,
    delete_table_bucket,
    find_table_bucket,
    get_table_bucket,
    get_table_bucket_encryption,
    list_tags_for_resource,
    put_table_bucket_encryption,
    tag_resource,
    untag_resource,
)
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags


def _validate_encryption_configuration(module: AnsibleAWSModule, encryption_configuration: Optional[Dict[str, Any]]):
    if not encryption_configuration:
        return
    if encryption_configuration.get("sse_algorithm") == "aws:kms" and not encryption_configuration.get("kms_key_arn"):
        module.fail_json(
            msg="encryption_configuration.kms_key_arn is required when encryption_configuration.sse_algorithm is 'aws:kms'."
        )


def _desired_encryption_configuration(encryption_configuration: Dict[str, Any]) -> Dict[str, Any]:
    params = {"sseAlgorithm": encryption_configuration["sse_algorithm"]}
    if encryption_configuration.get("kms_key_arn"):
        params["kmsKeyArn"] = encryption_configuration["kms_key_arn"]
    return params


def _encryption_needs_update(current: Optional[Dict[str, Any]], desired: Dict[str, Any]) -> bool:
    if not current:
        return True
    return current.get("sseAlgorithm") != desired.get("sseAlgorithm") or current.get("kmsKeyArn") != desired.get(
        "kmsKeyArn"
    )


def _format_table_bucket(
    bucket: Dict[str, Any],
    tags: Optional[Dict[str, str]] = None,
    encryption_configuration: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    result = camel_dict_to_snake_dict(bucket)
    if tags is not None:
        result["tags"] = tags
    if encryption_configuration is not None:
        result["encryption_configuration"] = camel_dict_to_snake_dict(encryption_configuration)
    return result


def _read_table_bucket(client, module: AnsibleAWSModule, table_bucket_arn: str) -> Dict[str, Any]:
    bucket = get_table_bucket(client, table_bucket_arn)
    tags = None
    if module.params.get("tags") is not None:
        tags = list_tags_for_resource(client, table_bucket_arn)
    encryption_configuration = None
    if module.params.get("encryption_configuration"):
        encryption_configuration = get_table_bucket_encryption(client, table_bucket_arn)
    return _format_table_bucket(bucket, tags=tags, encryption_configuration=encryption_configuration)


def ensure_present(client, module: AnsibleAWSModule, existing: Optional[Dict[str, Any]]) -> None:
    table_bucket_name = module.params.get("table_bucket_name")
    tags = module.params.get("tags")
    purge_tags = module.params.get("purge_tags")
    encryption_configuration = module.params.get("encryption_configuration")
    changed = False

    if not existing:
        changed = True
        if module.check_mode:
            module.exit_json(changed=True, msg=f"Check mode: would have created table bucket '{table_bucket_name}'.")

        params = {}
        if tags:
            params["tags"] = tags
        if encryption_configuration:
            params["encryptionConfiguration"] = _desired_encryption_configuration(encryption_configuration)
        table_bucket_arn = create_table_bucket(client, table_bucket_name, **params)
    else:
        table_bucket_arn = existing["arn"]

        tags_to_set, tags_to_unset = {}, []
        if tags is not None:
            current_tags = list_tags_for_resource(client, table_bucket_arn)
            tags_to_set, tags_to_unset = compare_aws_tags(current_tags, tags, purge_tags)

        encryption_to_set = None
        if encryption_configuration:
            current_encryption = get_table_bucket_encryption(client, table_bucket_arn)
            desired_encryption = _desired_encryption_configuration(encryption_configuration)
            if _encryption_needs_update(current_encryption, desired_encryption):
                encryption_to_set = desired_encryption

        if tags_to_set or tags_to_unset or encryption_to_set:
            changed = True
            if module.check_mode:
                module.exit_json(
                    changed=True,
                    msg=f"Check mode: would have updated table bucket '{table_bucket_name}'.",
                )
            if tags_to_unset:
                untag_resource(client, table_bucket_arn, tags_to_unset)
            if tags_to_set:
                tag_resource(client, table_bucket_arn, tags_to_set)
            if encryption_to_set:
                put_table_bucket_encryption(client, table_bucket_arn, encryption_to_set)

    result = _read_table_bucket(client, module, table_bucket_arn)
    msg = "Table bucket is up to date." if not changed else "Table bucket updated."
    module.exit_json(changed=changed, table_bucket=result, msg=msg)


def ensure_absent(client, module: AnsibleAWSModule, existing: Optional[Dict[str, Any]]) -> None:
    table_bucket_name = module.params.get("table_bucket_name")
    if not existing:
        module.exit_json(changed=False, table_bucket={}, msg=f"Table bucket '{table_bucket_name}' does not exist.")

    if module.check_mode:
        module.exit_json(changed=True, msg=f"Check mode: would have deleted table bucket '{table_bucket_name}'.")

    delete_table_bucket(client, existing["arn"])
    module.exit_json(changed=True, table_bucket={}, msg=f"Table bucket '{table_bucket_name}' deleted.")


def main() -> None:
    argument_spec = dict(
        state=dict(type="str", choices=["present", "absent"], default="present"),
        table_bucket_name=dict(type="str", required=True, aliases=["name"]),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        encryption_configuration=dict(
            type="dict",
            options=dict(
                sse_algorithm=dict(type="str", required=True, choices=["AES256", "aws:kms"]),
                kms_key_arn=dict(type="str"),
            ),
        ),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    _validate_encryption_configuration(module, module.params.get("encryption_configuration"))

    try:
        client = module.client("s3tables")
        existing_summary = find_table_bucket(client, module.params.get("table_bucket_name"))

        state = module.params.get("state")
        if state == "absent":
            ensure_absent(client, module, existing_summary)
        else:
            ensure_present(client, module, existing_summary)
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")
    except AnsibleS3TablesError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
