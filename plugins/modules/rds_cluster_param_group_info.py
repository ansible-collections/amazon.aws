#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024 Aubin Bikouo (@abikouo)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: rds_cluster_param_group_info
version_added: 7.5.0
short_description: Describes the properties of specific RDS cluster parameter group.
description:
  - Obtain information about one specific RDS cluster parameter group.
options:
    name:
        description:
          - The RDS cluster parameter group name.
        type: str
        required: true
author:
  - Aubin Bikouo (@abikouo)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Describe a specific RDS cluster parameter group
  amazon.aws.rds_cluster_param_group_info:
    name: myrdsclustergroup
"""

RETURN = r"""
db_cluster_parameter_groups:
  description: List of RDS cluster parameter groups.
  returned: always
  type: list
  contains:
    db_cluster_parameter_group_name:
        description:
        - The name of the RDS cluster parameter group.
        type: str
    db_parameter_group_family:
        description:
        - The name of the RDS parameter group family that this RDS cluster parameter group is compatible with.
        type: str
    description:
        description:
        - Provides the customer-specified description for this RDS cluster parameter group.
        type: str
    db_cluster_parameter_group_arn:
        description:
        - The Amazon Resource Name (ARN) for the RDS cluster parameter group.
        type: str
    tags:
        description: A dictionary of key value pairs.
        type: dict
        sample: {
            "Name": "rds-cluster-demo"
        }
"""


try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.rds import get_tags
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _describe_db_cluster_parameter_group(module, connection, group_name):
    try:
        response = connection.describe_db_cluster_parameter_groups(
            aws_retry=True, DBClusterParameterGroupName=group_name
        )
    except is_boto3_error_code("DBParameterGroupNotFound"):
        response = None
    except botocore.exceptions.ClientError as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Couldn't access parameter group information")
    return response


def describe_db_engine_versions(connection, module):
    group_name = module.params.get("name")
    results = []
    response = _describe_db_cluster_parameter_group(module, connection, group_name)
    if response:
        resource = response["DBClusterParameterGroups"][0]
        resource["tags"] = get_tags(connection, module, resource["DBClusterParameterGroupArn"])
        results.append(camel_dict_to_snake_dict(resource, ignore_list=["tags"]))
    module.exit_json(changed=False, db_cluster_parameter_groups=results)


def main():
    argument_spec = dict(
        name=dict(required=True),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        client = module.client("rds", retry_decorator=AWSRetry.jittered_backoff(retries=10))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    describe_db_engine_versions(client, module)


if __name__ == "__main__":
    main()
