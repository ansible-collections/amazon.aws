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
  - Describe a specific RDS parameter group, or
    all parameter groups available in the current region.
options:
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
- name: Get specific DB parameter group's info
  amazon.aws.rds_instance_param_group_info:
    db_parameter_group_name: my-test-pg

- name: Get all parameter group info from the region
  amazon.aws.rds_instance_param_group_info:
"""

RETURN = r"""
db_instance_parameter_groups:
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
    tags:
      description: Any tags associated to the parameter group.
      returned: always
      type: dict
      sample: {
                "Name": "test-parameter-group",
                "Env": "Dev001"
              }
"""

from typing import Any

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.rds import AnsibleRDSError
from ansible_collections.amazon.aws.plugins.module_utils.rds import describe_db_instance_parameter_groups
from ansible_collections.amazon.aws.plugins.module_utils.rds import get_tags
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry

def describe_rds_instance_parameter_group(connection: Any, module: AnsibleAWSModule) -> None:
    """
    Describes DB parameter groups and formats the response.
    
    Args:
        connection: boto3 RDS client
        module: AnsibleAWSModule
    """
    group_name = module.params.get("db_parameter_group_name")
    results = []
    
    response = describe_db_instance_parameter_groups(connection, group_name)
    if response:
        for resource in response:
            resource["tags"] = get_tags(connection, module, resource["DBParameterGroupArn"])
            results.append(camel_dict_to_snake_dict(resource, ignore_list=["tags"]))
    
    module.exit_json(changed=False, db_instance_parameter_groups=results)


def main() -> None:
    argument_spec = {
        "db_parameter_group_name": {"type": "str", "required": False},
    }

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    connection = module.client("rds", retry_decorator=AWSRetry.jittered_backoff(retries=10))
    try:
        describe_rds_instance_parameter_group(connection, module)
    except AnsibleRDSError as e:
        module.fail_json_aws(e, msg="Failed to describe DB parameter groups")


if __name__ == "__main__":
    main()
