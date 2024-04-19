#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024 Aubin Bikouo (@abikouo)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: rds_engine_versions_info
version_added: 7.6.0
short_description: Describes the properties of specific versions of DB engines.
description:
  - Obtain information about a specific versions of DB engines.
options:
    engine:
        description:
          - The database engine to return version details for.
        type: str
        choices:
          - aurora-mysql
          - aurora-postgresql
          - custom-oracle-ee
          - db2-ae
          - db2-se
          - mariadb
          - mysql
          - oracle-ee
          - oracle-ee-cdb
          - oracle-se2
          - oracle-se2-cdb
          - postgres
          - sqlserver-ee
          - sqlserver-se
          - sqlserver-ex
          - sqlserver-web
    engine_version:
        description:
          - A specific database engine version to return details for.
        type: str
    db_parameter_group_family:
        description:
          - The name of a specific RDS parameter group family to return details for.
        type: str
    default_only:
        description:
          - Specifies whether to return only the default version of the specified engine
            or the engine and major version combination.
        type: bool
        default: False
    filters:
        description:
            - A filter that specifies one or more DB engine versions to describe.
              See U(https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DescribeDBEngineVersions.html).
        type: dict
author:
  - Aubin Bikouo (@abikouo)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: List all of the available parameter group families for the Aurora PostgreSQL DB engine
  amazon.aws.rds_engine_versions_info:
    engine: aurora-postgresql

- name: List all of the available parameter group families for the Aurora PostgreSQL DB engine on a specific version
  amazon.aws.rds_engine_versions_info:
    engine: aurora-postgresql
    engine_version: 16.1

- name: Get default engine version for DB parameter group family postgres16
  amazon.aws.rds_engine_versions_info:
    engine: postgres
    default_only: true
    db_parameter_group_family: postgres16
"""

RETURN = r"""
db_engine_versions:
  description: List of RDS engine versions.
  returned: always
  type: list
  contains:
    engine:
        description:
        - The name of the database engine.
        type: str
    engine_version:
        description:
        - The version number of the database engine.
        type: str
    db_parameter_group_family:
        description:
        - The name of the DB parameter group family for the database engine.
        type: str
    db_engine_description:
        description:
        - The description of the database engine.
        type: str
    db_engine_version_description:
        description:
        - The description of the database engine version.
        type: str
    default_character_set:
        description:
        - The default character set for new instances of this engine version.
        type: dict
        sample: {
            "character_set_description": "Unicode 5.0 UTF-8 Universal character set",
            "character_set_name": "AL32UTF8"
        }
    image:
        description:
        - The EC2 image
        type: complex
        contains:
            image_id:
                description:
                - A value that indicates the ID of the AMI.
                type: str
            status:
                description:
                - A value that indicates the status of a custom engine version (CEV).
                type: str
    db_engine_media_type:
        description:
        - A value that indicates the source media provider of the AMI based on the usage operation.
        type: str
    supported_character_sets:
        description:
        - A list of the character sets supported by this engine for the CharacterSetName parameter of the CreateDBInstance operation.
        type: list
        elements: dict
        contains:
            character_set_name:
                description:
                - The name of the character set.
                type: str
            character_set_description:
                description:
                - The description of the character set.
                type: str
    supported_nchar_character_sets:
        description:
        - A list of the character sets supported by the Oracle DB engine.
        type: list
        elements: dict
        contains:
            character_set_name:
                description:
                - The name of the character set.
                type: str
            character_set_description:
                description:
                - The description of the character set.
                type: str
    valid_upgrade_target:
        description:
        - A list of engine versions that this database engine version can be upgraded to.
        type: list
        elements: dict
        sample: [
            {
                "auto_upgrade": false,
                "description": "Aurora PostgreSQL (Compatible with PostgreSQL 15.5)",
                "engine": "aurora-postgresql",
                "engine_version": "15.5",
                "is_major_version_upgrade": false,
                "supported_engine_modes": [
                    "provisioned"
                ],
                "supports_babelfish": true,
                "supports_global_databases": true,
                "supports_integrations": false,
                "supports_local_write_forwarding": true,
                "supports_parallel_query": false
            }
        ]
    supported_timezones:
        description:
        - A list of the time zones supported by this engine for the Timezone parameter of the CreateDBInstance action.
        type: list
        elements: dict
        sample: [
            {"TimezoneName": "xxx"}
        ]
    exportable_log_types:
        description:
        - The types of logs that the database engine has available for export to CloudWatch Logs.
        type: list
        elements: str
    supports_log_exports_to_cloudwatchLogs:
        description:
        - Indicates whether the engine version supports exporting the log types specified by ExportableLogTypes to CloudWatch Logs.
        type: bool
    supports_read_replica:
        description:
        - Indicates whether the database engine version supports read replicas.
        type: bool
    supported_engine_modes:
        description:
        - A list of the supported DB engine modes.
        type: list
        elements: str
    supported_feature_names:
        description:
        - A list of features supported by the DB engine.
        type: list
        elements: str
        sample: [
            "Comprehend",
            "Lambda",
            "s3Export",
            "s3Import",
            "SageMaker"
        ]
    status:
        description:
        - The status of the DB engine version, either available or deprecated.
        type: str
    supports_parallel_query:
        description:
        - Indicates whether you can use Aurora parallel query with a specific DB engine version.
        type: bool
    supports_global_databases:
        description:
        - Indicates whether you can use Aurora global databases with a specific DB engine version.
        type: bool
    major_engine_version:
        description:
        - The major engine version of the CEV.
        type: str
    database_installation_files_s3_bucket_name:
        description:
        - The name of the Amazon S3 bucket that contains your database installation files.
        type: str
    database_installation_files_s3_prefix:
        description:
        - The Amazon S3 directory that contains the database installation files.
        type: str
    db_engine_version_arn:
        description:
        - The ARN of the custom engine version.
        type: str
    kms_key_id:
        description:
        - The Amazon Web Services KMS key identifier for an encrypted CEV.
        type: str
    create_time:
        description:
        - The creation time of the DB engine version.
        type: str
    tags:
        description: A dictionary of key value pairs.
        type: dict
        sample: {
            "some": "tag"
        }
    supports_babelfish:
        description:
        - Indicates whether the engine version supports Babelfish for Aurora PostgreSQL.
        type: bool
    custom_db_engine_version_manifest:
        description:
        - JSON string that lists the installation files and parameters that RDS Custom uses to create a custom engine version (CEV).
        type: str
    supports_certificate_rotation_without_restart:
        description:
        - Indicates whether the engine version supports rotating the server certificate without rebooting the DB instance.
        type: bool
    supported_ca_certificate_identifiers:
        description:
        - A list of the supported CA certificate identifiers.
        type: list
        elements: str
        sample: [
            "rds-ca-2019",
            "rds-ca-ecc384-g1",
            "rds-ca-rsa4096-g1",
            "rds-ca-rsa2048-g1"
        ]
    supports_local_write_forwarding:
        description:
        - Indicates whether the DB engine version supports forwarding write operations from reader DB instances to the writer DB instance in the DB cluster.
        type: bool
    supports_integrations:
        description:
        - Indicates whether the DB engine version supports zero-ETL integrations with Amazon Redshift.
        type: bool
"""

from typing import Any
from typing import Dict
from typing import List

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict


@AWSRetry.jittered_backoff(retries=10)
def _describe_db_engine_versions(connection: Any, **params: Dict[str, Any]) -> List[Dict[str, Any]]:
    paginator = connection.get_paginator("describe_db_engine_versions")
    return paginator.paginate(**params).build_full_result()["DBEngineVersions"]


def describe_db_engine_versions(connection: Any, module: AnsibleAWSModule) -> Dict[str, Any]:
    engine = module.params.get("engine")
    engine_version = module.params.get("engine_version")
    db_parameter_group_family = module.params.get("db_parameter_group_family")
    default_only = module.params.get("default_only")
    filters = module.params.get("filters")

    params = {"DefaultOnly": default_only}
    if engine:
        params["Engine"] = engine
    if engine_version:
        params["EngineVersion"] = engine_version
    if db_parameter_group_family:
        params["DBParameterGroupFamily"] = db_parameter_group_family
    if filters:
        params["Filters"] = filters

    try:
        result = _describe_db_engine_versions(connection, **params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, "Couldn't get RDS engine versions.")

    def _transform_item(v):
        tag_list = v.pop("TagList", [])
        v = camel_dict_to_snake_dict(v)
        v["tags"] = boto3_tag_list_to_ansible_dict(tag_list)
        return v

    return dict(changed=False, db_engine_versions=[_transform_item(v) for v in result])


def main() -> None:
    argument_spec = dict(
        engine=dict(
            choices=[
                "aurora-mysql",
                "aurora-postgresql",
                "custom-oracle-ee",
                "db2-ae",
                "db2-se",
                "mariadb",
                "mysql",
                "oracle-ee",
                "oracle-ee-cdb",
                "oracle-se2",
                "oracle-se2-cdb",
                "postgres",
                "sqlserver-ee",
                "sqlserver-se",
                "sqlserver-ex",
                "sqlserver-web",
            ]
        ),
        engine_version=dict(),
        db_parameter_group_family=dict(),
        default_only=dict(type="bool", default=False),
        filters=dict(type="dict"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        client = module.client("rds", retry_decorator=AWSRetry.jittered_backoff(retries=10))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    module.exit_json(**describe_db_engine_versions(client, module))


if __name__ == "__main__":
    main()
