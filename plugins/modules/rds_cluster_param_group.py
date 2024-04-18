#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: rds_cluster_param_group
version_added: 7.6.0
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
from typing import Any
from typing import Dict
from typing import List

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.rds import describe_db_cluster_parameter_groups
from ansible_collections.amazon.aws.plugins.module_utils.rds import describe_db_cluster_parameters
from ansible_collections.amazon.aws.plugins.module_utils.rds import ensure_tags
from ansible_collections.amazon.aws.plugins.module_utils.rds import get_tags
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list


def modify_parameters(
    module: AnsibleAWSModule, connection: Any, group_name: str, parameters: List[Dict[str, Any]]
) -> bool:
    current_params = describe_db_cluster_parameters(module, connection, group_name)
    parameters = snake_dict_to_camel_dict(parameters, capitalize_first=True)
    # compare current resource parameters with the value from module parameters
    changed = False
    for param in parameters:
        found = False
        for current_p in current_params:
            if param.get("ParameterName") == current_p.get("ParameterName"):
                found = True
                if not current_p["IsModifiable"]:
                    module.fail_json(f"The parameter {param.get('ParameterName')} cannot be modified")
                changed |= any((current_p.get(k) != v for k, v in param.items()))
        if not found:
            module.fail_json(msg=f"Could not find parameter with name: {param.get('ParameterName')}")
    if changed:
        if not module.check_mode:
            # When calling modify_db_cluster_parameter_group() function
            # A maximum of 20 parameters can be modified in a single request.
            # This is why we are creating chunk containing at max 20 items
            for chunk in zip_longest(*[iter(parameters)] * 20, fillvalue=None):
                non_empty_chunk = [item for item in chunk if item]
                try:
                    connection.modify_db_cluster_parameter_group(
                        aws_retry=True, DBClusterParameterGroupName=group_name, Parameters=non_empty_chunk
                    )
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    module.fail_json_aws(e, msg="Couldn't update RDS cluster parameters")
    return changed


def ensure_present(module: AnsibleAWSModule, connection: Any) -> None:
    group_name = module.params["name"]
    db_parameter_group_family = module.params["db_parameter_group_family"]
    tags = module.params.get("tags")
    purge_tags = module.params.get("purge_tags")
    changed = False

    response = describe_db_cluster_parameter_groups(module=module, connection=connection, group_name=group_name)
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
            module.exit_json(changed=True, msg="Would have create RDS parameter group if not in check mode.")
        try:
            response = connection.create_db_cluster_parameter_group(aws_retry=True, **params)
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't create parameter group")
    else:
        group = response[0]
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

    response = describe_db_cluster_parameter_groups(module=module, connection=connection, group_name=group_name)
    group = camel_dict_to_snake_dict(response[0])
    group["tags"] = get_tags(connection, module, group["db_cluster_parameter_group_arn"])

    module.exit_json(changed=changed, db_cluster_parameter_group=group)


def ensure_absent(module: AnsibleAWSModule, connection: Any) -> None:
    group = module.params["name"]
    response = describe_db_cluster_parameter_groups(module=module, connection=connection, group_name=group)
    if not response:
        module.exit_json(changed=False, msg="The RDS cluster parameter group does not exist.")

    if not module.check_mode:
        try:
            response = connection.delete_db_cluster_parameter_group(aws_retry=True, DBClusterParameterGroupName=group)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't delete RDS cluster parameter group")
    module.exit_json(changed=True)


def main() -> None:
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
            ),
        ),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[["state", "present", ["description", "db_parameter_group_family"]]],
        supports_check_mode=True,
    )

    try:
        connection = module.client("rds", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    if module.params.get("state") == "present":
        ensure_present(module=module, connection=connection)
    else:
        ensure_absent(module=module, connection=connection)


if __name__ == "__main__":
    main()
