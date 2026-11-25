#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: s3_table_bucket_info
version_added: 12.2.0
short_description: Retrieve information about an S3 table bucket
description:
  - Retrieve information about an Amazon S3 Tables table bucket and the tables it contains.
  - Does not return Iceberg field schemas, which are not present in the S3 Tables API responses.
author:
  - "Jan Likar (@JanLikar)"
options:
  table_bucket_name:
    description:
      - The name of the table bucket to look up.
    required: true
    aliases: ["name"]
    type: str
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
notes:
  - >-
    The following IAM actions are required: C(s3tables:ListTableBuckets), C(s3tables:GetTableBucket),
    C(s3tables:ListTables).
  - >-
    Amazon S3 Tables is available only in selected AWS Regions, see the
    U(https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-tables-regions-quotas.html) guide.
seealso:
  - module: amazon.aws.s3_table_bucket
    description: Create, update or delete an S3 table bucket.
"""

EXAMPLES = r"""
- name: Get information about an S3 table bucket
  amazon.aws.s3_table_bucket_info:
    table_bucket_name: "my-table-bucket"
  register: result
"""

RETURN = r"""
table_buckets:
  description: List containing information about the named table bucket, or an empty list if it was not found.
  returned: always
  type: list
  elements: dict
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
    tables:
      description: List of tables contained in the table bucket.
      returned: always
      type: list
      elements: dict
      contains:
        namespace:
          description: The namespace the table belongs to.
          returned: always
          type: list
          elements: str
          sample: ["my_namespace"]
        name:
          description: The name of the table.
          returned: always
          type: str
          sample: "my_table"
        type:
          description: The type of the table.
          returned: always
          type: str
          sample: "customer"
        table_arn:
          description: The Amazon Resource Name (ARN) of the table.
          returned: always
          type: str
          sample: "arn:aws:s3tables:us-east-1:123456789012:bucket/my-table-bucket/table/abcd1234-ab12-cd34-ef56-abcdef123456"
        created_at:
          description: The date and time the table was created.
          returned: always
          type: str
          sample: "2025-01-01T12:00:00+00:00"
        modified_at:
          description: The date and time the table was last modified.
          returned: always
          type: str
          sample: "2025-01-01T12:00:00+00:00"
        managed_by_service:
          description: The service that manages the table, if any.
          returned: if defined
          type: str
          sample: "Glue"
        namespace_id:
          description: The unique identifier for the namespace.
          returned: if defined
          type: str
          sample: "abcd1234-ab12-cd34-ef56-abcdef123456"
        table_bucket_id:
          description: The unique identifier for the table bucket.
          returned: if defined
          type: str
          sample: "abcd1234-ab12-cd34-ef56-abcdef123456"
"""

from typing import Any
from typing import Dict
from typing import List

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.s3tables import (
    AnsibleS3TablesError,
    find_table_bucket,
    get_table_bucket,
    list_table_summaries,
)


def _describe_table_bucket(client, table_bucket_arn: str) -> Dict[str, Any]:
    bucket = get_table_bucket(client, table_bucket_arn)
    result = camel_dict_to_snake_dict(bucket)
    result["tables"] = [camel_dict_to_snake_dict(table) for table in list_table_summaries(client, table_bucket_arn)]
    return result


def main() -> None:
    argument_spec = dict(
        table_bucket_name=dict(type="str", required=True, aliases=["name"]),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    table_buckets: List[Dict[str, Any]] = []
    try:
        client = module.client("s3tables")
        existing_summary = find_table_bucket(client, module.params.get("table_bucket_name"))
        if existing_summary:
            table_buckets = [_describe_table_bucket(client, existing_summary["arn"])]
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")
    except AnsibleS3TablesError as e:
        module.fail_json_aws_error(e)

    module.exit_json(changed=False, table_buckets=table_buckets)


if __name__ == "__main__":
    main()
