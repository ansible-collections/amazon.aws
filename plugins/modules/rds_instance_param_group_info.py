#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2024 Ansible Project
# Copyright (c) 2024 Mandar Vijay Kulkarni (@mandar242)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: rds_instance_param_group_info
version_added: 9.1.0
short_description: Describes the RDS parameter group.
description:
  - Describe a specific RDS parameter group, the parameter group associated with a specified RDS instance, or all parameter groups available in the current region.
options:
  db_instance_identifier:
    description:
      - The RDS instance's unique identifier.
    required: false
    type: str
  db_parameter_group_name:
    description:
      - The name of a specific DB parameter group to return details for.
    required: false
    type: str
author:
  - Mandar Vijay Kulkarni (@mandar242)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Get specific DB instance's parameter group info
  amazon.aws.rds_instance_param_group_info:
    db_instance_identifier: database-1

- name: Get specific DB parameter group's info
  amazon.aws.rds_instance_param_group_info:
    db_parameter_group_name: my-test-pg

- name: Get all parameter group info from the region
  amazon.aws.rds_instance_param_group_info:
"""

RETURN = r"""
db_parameter_groups:
  description: List of RDS instance parameter groups.
  returned: always
  type: list
  contains:
    db_parameter_group_name:
      description:
        - The name of the RDS instance parameter group.
      type: str
    db_parameter_group_family:
      description:
        - The name of the RDS parameter group family that this RDS instance parameter group is compatible with.
      type: str
    description:
      description:
        - Provides the customer-specified description for this RDS instance parameter group.
      type: str
    db_parameter_group_arn:
      description:
        - The Amazon Resource Name (ARN) for the RDS instance parameter group.
      type: str
"""

from typing import Any, List

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.rds import describe_db_instances
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def get_db_instance_param_group_name(connection: Any, module: AnsibleAWSModule) -> str:
    db_instance_identifier = module.params.get("db_instance_identifier")
    if not db_instance_identifier:
        return None

    response = describe_db_instances(connection, DBInstanceIdentifier=db_instance_identifier)
    return response[0]["DBParameterGroups"][0]["DBParameterGroupName"] if response else None


def describe_db_parameter_groups(connection: Any, module: AnsibleAWSModule, db_parameter_group_name: str = None) -> List[dict]:
    try:
        if db_parameter_group_name:
            result = connection.describe_db_parameter_groups(DBParameterGroupName=db_parameter_group_name)["DBParameterGroups"]
            return [camel_dict_to_snake_dict(result[0])] if result else []
        else:
            result = connection.describe_db_parameter_groups()["DBParameterGroups"]
            return [camel_dict_to_snake_dict(group) for group in result] if result else []

    except is_boto3_error_code("DBParameterGroupNotFound"):
        return []
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e, msg="Couldn't access parameter group information")


def main() -> None:
    argument_spec = {
        "db_instance_identifier": {"type": "str", "required": False},
        "db_parameter_group_name": {"type": "str", "required": False},
    }

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[["db_instance_identifier", "db_parameter_group_name"]],
    )

    try:
        client = module.client("rds", retry_decorator=AWSRetry.jittered_backoff(retries=10))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    db_parameter_group_name = (
        get_db_instance_param_group_name(client, module)
        if module.params.get("db_instance_identifier") 
        else module.params.get("db_parameter_group_name")
    )

    if db_parameter_group_name:
        result = describe_db_parameter_groups(client, module, db_parameter_group_name)
    else:
        result = describe_db_parameter_groups(client, module)

    module.exit_json(changed=False, db_parameter_groups=result)


if __name__ == "__main__":
    main()

