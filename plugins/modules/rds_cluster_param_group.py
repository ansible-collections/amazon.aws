#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: rds_cluster_param_group
version_added: 7.5.0
short_description: Manage RDS cluster parameter groups
description:
  - Creates, modifies, and deletes RDS cluster parameter groups.
options:
  state:
    description:
      - Specifies whether the RDS cluster parameter group should be present or absent.
    default: present
    choices: [ 'present' , 'absent' ]
    type: str
  name:
    description:
      - The name of the RDS cluster parameter group to create, modify or delete.
    required: true
    type: str
  description:
    description:
      - The description for the RDS cluster parameter group.
      - Required for O(state=present).
    type: str
  db_parameter_group_family:
    description:
      - The RDS cluster parameter group family name.
      - An RDS cluster parameter group can be associated with one and only one RDS cluster parameter group family,
        and can be applied only to a RDS cluster running a database engine and engine version compatible with that RDS cluster parameter group family.
      - Please use M(amazon.aws.rds_engine_versions_info) module To list all of the available parameter group families for a DB engine.
      - The RDS cluster parameter group family is immutable and can't be changed when updating a RDS cluster parameter group.
        See U(https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-rds-dbclusterparametergroup.html)
      - Required for O(state=present).
    type: str
  parameters:
    description:
      - A list of parameters to update.
    type: list
    elements: dict
    suboptions:
      parameter_name:
        description: Specifies the name of the parameter.
        type: str
        required: true
      parameter_value:
        description:
        - Specifies the value of the parameter.
        type: str
        required: true
      apply_method:
        description:
        - Indicates when to apply parameter updates.
        choices:
        - immediate
        - pending-reboot
        type: str
        required: true
      description:
        description:
        - Provides a description of the parameter.
        type: str
      source:
        description:
        - Indicates the source of the parameter value.
        type: str
      apply_type:
        description:
        - Specifies the engine specific parameters type.
        type: str
      data_type:
        description:
        - Specifies the valid data type for the parameter.
        type: str
      allowed_values:
        description:
        - Specifies the valid range of values for the parameter.
        type: str
      is_modifiable:
        description:
        - Indicates whether V(True) or not V(False) the parameter can be modified.
        type: bool
      minimum_engine_version:
        description:
        - The earliest engine version to which the parameter can apply.
        type: str
      supported_engine_modes:
        description:
        - The valid DB engine modes.
        type: list
        elements: str
author:
  - "Aubin Bikouo (@abikouo)"
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Add or change a parameter group, in this case setting authentication_timeout to 200
  amazon.aws.rds_cluster_param_group:
      state: present
      name: test-cluster-group
      description: 'My test RDS cluster group'
      db_parameter_group_family: 'mysql5.6'
      parameters:
          - parameter_name: authentication_timeout
            parameter_value: "200"
            apply_method: immediate
      tags:
          Environment: production
          Application: parrot

- name: Remove a parameter group
  amazon.aws.rds_param_group:
      state: absent
      name: test-cluster-group
"""

RETURN = r"""
db_cluster_parameter_group:
    description: dictionary containing all the RDS cluster parameter group information
    returned: success
    type: complex
    contains:
        db_cluster_parameter_group_arn:
            description: The Amazon Resource Name (ARN) for the RDS cluster parameter group.
            type: str
            returned: when state is present
        db_cluster_parameter_group_name:
            description: The name of the RDS cluster parameter group.
            type: str
            returned: when state is present
        db_parameter_group_family:
            description: The name of the RDS parameter group family that this RDS cluster parameter group is compatible with.
            type: str
            returned: when state is present
        description:
            description: Provides the customer-specified description for this RDS cluster parameter group.
            type: str
            returned: when state is present
        tags:
            description: dictionary of tags
            type: dict
            returned: when state is present
"""

from itertools import zip_longest

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.rds import ensure_tags
from ansible_collections.amazon.aws.plugins.module_utils.rds import get_tags
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list


@AWSRetry.jittered_backoff()
def _describe_db_cluster_parameters(module, connection, group_name):
    try:
        paginator = connection.get_paginator("describe_db_cluster_parameters")
        return paginator.paginate(DBClusterParameterGroupName=group_name).build_full_result()["Parameters"]
    except is_boto3_error_code("DBParameterGroupNotFound"):
        return None
    except botocore.exceptions.ClientError as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to describe existing RDS cluster parameter groups")


def modify_parameters(module, connection, group_name, parameters):
    if module.check_mode:
        return True

    current_params = _describe_db_cluster_parameters(module, connection, group_name)
    parameters_names = [x["parameter_name"] for x in parameters]
    parameters = snake_dict_to_camel_dict(
        list(map(lambda x: {k: v for k, v in x.items() if v is not None}, parameters)), capitalize_first=True
    )
    for chunk in zip_longest(*[iter(parameters)] * 20, fillvalue=None):
        non_empty_chunk = [item for item in chunk if item]
        try:
            connection.modify_db_cluster_parameter_group(
                aws_retry=True, DBClusterParameterGroupName=group_name, Parameters=non_empty_chunk
            )
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't update RDS cluster parameters")
    update_params = _describe_db_cluster_parameters(module, connection, group_name)
    changed = False
    for name in parameters_names:
        previous = list(filter(lambda x: x["ParameterName"] == name, current_params))[0]
        new = list(filter(lambda x: x["ParameterName"] == name, update_params))[0]
        if new != previous:
            changed = True
            break
    return changed


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


def ensure_present(module, connection):
    group_name = module.params["name"]
    db_parameter_group_family = module.params["db_parameter_group_family"]
    tags = module.params.get("tags")
    purge_tags = module.params.get("purge_tags")
    changed = False

    response = _describe_db_cluster_parameter_group(module=module, connection=connection, group_name=group_name)
    if not response:
        # Create RDS cluster parameter group
        params = dict(
            DBClusterParameterGroupName=group_name,
            DBParameterGroupFamily=db_parameter_group_family,
            Description=module.params["description"],
        )
        if tags:
            params["Tags"] = ansible_dict_to_boto3_tag_list(tags)
        if module.check_mode:
            module.exit_json(changed=True)
        try:
            response = connection.create_db_cluster_parameter_group(aws_retry=True, **params)
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't create parameter group")
    else:
        group = response["DBClusterParameterGroups"][0]
        if db_parameter_group_family != group["DBParameterGroupFamily"]:
            module.warn(
                "The RDS cluster parameter group family is immutable and can't be changed when updating a RDS cluster parameter group."
            )

        if tags:
            existing_tags = get_tags(connection, module, group["DBClusterParameterGroupArn"])
            changed = ensure_tags(
                connection, module, group["DBClusterParameterGroupArn"], existing_tags, tags, purge_tags
            )

    parameters = module.params.get("parameters")
    if parameters:
        changed |= modify_parameters(module, connection, group_name, parameters)

    response = _describe_db_cluster_parameter_group(module=module, connection=connection, group_name=group_name)
    group = camel_dict_to_snake_dict(response["DBClusterParameterGroups"][0])
    group["tags"] = get_tags(connection, module, group["db_cluster_parameter_group_arn"])

    module.exit_json(changed=changed, db_cluster_parameter_group=group)


def ensure_absent(module, connection):
    group = module.params["name"]
    response = _describe_db_cluster_parameter_group(module=module, connection=connection, group_name=group)
    if not response:
        module.exit_json(changed=False, msg="The RDS cluster parameter group does not exist.")

    if not module.check_mode:
        try:
            response = connection.delete_db_cluster_parameter_group(aws_retry=True, DBClusterParameterGroupName=group)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't delete RDS cluster parameter group")
    module.exit_json(changed=True)


def main():
    argument_spec = dict(
        state=dict(default="present", choices=["present", "absent"]),
        name=dict(required=True),
        db_parameter_group_family=dict(),
        description=dict(),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        parameters=dict(
            type="list",
            elements="dict",
            options=dict(
                parameter_name=dict(required=True),
                parameter_value=dict(required=True),
                apply_method=dict(choices=["immediate", "pending-reboot"], required=True),
                description=dict(),
                source=dict(),
                apply_type=dict(),
                data_type=dict(),
                allowed_values=dict(),
                is_modifiable=dict(type="bool"),
                minimum_engine_version=dict(),
                supported_engine_modes=dict(type="list", elements="str"),
            ),
        ),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[["state", "present", ["description", "db_parameter_group_family"]]],
        supports_check_mode=True,
    )

    try:
        client = module.client("rds", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    func_mapping = {
        "present": ensure_present,
        "absent": ensure_absent,
    }
    state = module.params.get("state")
    func_mapping.get(state)(module, client)


if __name__ == "__main__":
    main()
