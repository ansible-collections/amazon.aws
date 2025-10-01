#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: rds_instance_param_group
version_added: 5.0.0
short_description: manage RDS parameter groups
description:
  - Creates, modifies, and deletes RDS parameter groups.
  - This module was originally added to C(community.aws) in release 1.0.0.
options:
  state:
    description:
      - Specifies whether the group should be present or absent.
    required: true
    choices: [ 'present' , 'absent' ]
    type: str
  name:
    description:
      - Database parameter group identifier.
    required: true
    type: str
  description:
    description:
      - Database parameter group description. Only set when a new group is added.
    type: str
  engine:
    description:
      - The type of database for this group.
      - Please use M(amazon.aws.rds_engine_versions_info) to get list of all supported db engines and their respective versions.
      - The DB parameter group family is immutable and can't be changed when updating a DB parameter group.
        See U(https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-rds-dbparametergroup.html)
      - Required for O(state=present).
    type: str
  immediate:
    description:
      - Whether to apply the changes immediately, or after the next reboot of any associated instances.
    aliases:
      - apply_immediately
    type: bool
  params:
    description:
      - Map of parameter names and values. Numeric values may be represented as K for kilo (1024), M for mega (1024^2), G for giga (1024^3),
        or T for tera (1024^4), and these values will be expanded into the appropriate number before being set in the parameter group.
    aliases: [parameters]
    type: dict
author:
  - "Scott Anderson (@tastychutney)"
  - "Will Thames (@willthames)"
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Add or change a parameter group, in this case setting auto_increment_increment to 42 * 1024
  amazon.aws.rds_instance_param_group:
      state: present
      name: norwegian-blue
      description: 'My Fancy Ex Parrot Group'
      engine: 'mysql5.6'
      params:
          auto_increment_increment: "42K"
      tags:
          Environment: production
          Application: parrot

- name: Remove a parameter group
  amazon.aws.rds_instance_param_group:
      state: absent
      name: norwegian-blue
"""

RETURN = r"""
db_parameter_group_name:
    description: Name of DB parameter group.
    type: str
    returned: when O(state=present)
db_parameter_group_family:
    description: DB parameter group family that this DB parameter group is compatible with.
    type: str
    returned: when O(state=present)
db_parameter_group_arn:
    description: ARN of the DB parameter group.
    type: str
    returned: when O(state=present)
description:
    description: description of the DB parameter group.
    type: str
    returned: when O(state=present)
errors:
    description: List of errors from attempting to modify parameters that are not modifiable.
    type: list
    returned: when O(state=present)
tags:
    description: A dictionary of tags.
    type: dict
    returned: when O(state=present)
"""

from itertools import zip_longest

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.parsing.convert_bool import BOOLEANS_TRUE

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags

INT_MODIFIERS = {
    "K": 1024,
    "M": pow(1024, 2),
    "G": pow(1024, 3),
    "T": pow(1024, 4),
}


@AWSRetry.jittered_backoff()
def _describe_db_parameters(connection, **params):
    try:
        paginator = connection.get_paginator("describe_db_parameters")
        return paginator.paginate(**params).build_full_result()
    except is_boto3_error_code("DBParameterGroupNotFound"):
        return None


def convert_parameter(param, value):
    """
    Allows setting parameters with 10M = 10* 1024 * 1024 and so on.
    """
    converted_value = value

    if param["DataType"] == "integer":
        if isinstance(value, str):
            try:
                for name, modifier in INT_MODIFIERS.items():
                    if value.endswith(name):
                        converted_value = int(value[:-1]) * modifier
            except ValueError:
                # may be based on a variable (ie. {foo*3/4}) so
                # just pass it on through to the AWS SDK
                pass
        elif isinstance(value, bool):
            converted_value = 1 if value else 0

    elif param["DataType"] == "boolean":
        if isinstance(value, str):
            converted_value = value in BOOLEANS_TRUE
        # convert True/False to 1/0
        converted_value = 1 if converted_value else 0
    return str(converted_value)


def update_parameters(module, connection):
    groupname = module.params["name"]
    desired = module.params["params"]
    apply_method = "immediate" if module.params["immediate"] else "pending-reboot"
    errors = []
    modify_list = []
    existing = {}
    try:
        _existing = _describe_db_parameters(connection, DBParameterGroupName=groupname)
        if _existing:
            existing = _existing["Parameters"]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to describe existing parameter groups")
    lookup = dict((param["ParameterName"], param) for param in existing)
    for param_key, param_value in desired.items():
        if param_key not in lookup:
            errors.append(
                f"Parameter {param_key} is not an available parameter for the {module.params.get('engine')} engine"
            )
        else:
            converted_value = convert_parameter(lookup[param_key], param_value)
            # engine-default parameters do not have a ParameterValue, so we'll always override those.
            if converted_value != lookup[param_key].get("ParameterValue"):
                if lookup[param_key]["IsModifiable"]:
                    modify_list.append(
                        dict(ParameterValue=converted_value, ParameterName=param_key, ApplyMethod=apply_method)
                    )
                else:
                    errors.append(f"Parameter {param_key} is not modifiable")

    # modify_db_parameters takes at most 20 parameters
    if modify_list and not module.check_mode:
        for modify_slice in zip_longest(*[iter(modify_list)] * 20, fillvalue=None):
            non_empty_slice = [item for item in modify_slice if item]
            try:
                connection.modify_db_parameter_group(
                    aws_retry=True, DBParameterGroupName=groupname, Parameters=non_empty_slice
                )
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Couldn't update parameters")
        return True, errors
    return False, errors


def update_tags(module, connection, group, tags):
    if tags is None:
        return False
    changed = False

    existing_tags = connection.list_tags_for_resource(aws_retry=True, ResourceName=group["DBParameterGroupArn"])[
        "TagList"
    ]
    to_update, to_delete = compare_aws_tags(
        boto3_tag_list_to_ansible_dict(existing_tags), tags, module.params["purge_tags"]
    )

    if module.check_mode:
        if not to_update and not to_delete:
            return False
        else:
            return True

    if to_update:
        try:
            connection.add_tags_to_resource(
                aws_retry=True,
                ResourceName=group["DBParameterGroupArn"],
                Tags=ansible_dict_to_boto3_tag_list(to_update),
            )
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't add tags to parameter group")
    if to_delete:
        try:
            connection.remove_tags_from_resource(
                aws_retry=True, ResourceName=group["DBParameterGroupArn"], TagKeys=to_delete
            )
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't remove tags from parameter group")
    return changed


def ensure_present(module, connection):
    groupname = module.params["name"]
    tags = module.params.get("tags")
    changed = False
    errors = []
    try:
        response = connection.describe_db_parameter_groups(aws_retry=True, DBParameterGroupName=groupname)
    except is_boto3_error_code("DBParameterGroupNotFound"):
        response = None
    except botocore.exceptions.ClientError as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Couldn't access parameter group information")
    if not response:
        params = dict(
            DBParameterGroupName=groupname,
            DBParameterGroupFamily=module.params["engine"],
            Description=module.params["description"],
        )
        if tags:
            params["Tags"] = ansible_dict_to_boto3_tag_list(tags)
        if not module.check_mode:
            try:
                response = connection.create_db_parameter_group(aws_retry=True, **params)
                changed = True
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Couldn't create parameter group")
    else:
        group = response["DBParameterGroups"][0]
        db_parameter_group_family = group["DBParameterGroupFamily"]

        if module.params.get("engine") != db_parameter_group_family:
            module.warn("The DB parameter group family (engine) can't be changed when updating a DB parameter group.")

        if tags:
            changed = update_tags(module, connection, group, tags)

    if module.params.get("params"):
        params_changed, errors = update_parameters(module, connection)
        changed = changed or params_changed

    try:
        response = connection.describe_db_parameter_groups(aws_retry=True, DBParameterGroupName=groupname)
        group = camel_dict_to_snake_dict(response["DBParameterGroups"][0])
    except is_boto3_error_code("DBParameterGroupNotFound"):
        module.exit_json(changed=True, errors=errors)
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Couldn't obtain parameter group information")
    try:
        tags = connection.list_tags_for_resource(aws_retry=True, ResourceName=group["db_parameter_group_arn"])[
            "TagList"
        ]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't obtain parameter group tags")
    group["tags"] = boto3_tag_list_to_ansible_dict(tags)

    module.exit_json(changed=changed, errors=errors, **group)


def ensure_absent(module, connection):
    group = module.params["name"]
    try:
        response = connection.describe_db_parameter_groups(DBParameterGroupName=group)
    except is_boto3_error_code("DBParameterGroupNotFound"):
        module.exit_json(changed=False)
    except botocore.exceptions.ClientError as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Couldn't access parameter group information")

    if response and module.check_mode:
        module.exit_json(changed=True)

    try:
        response = connection.delete_db_parameter_group(aws_retry=True, DBParameterGroupName=group)
        module.exit_json(changed=True)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't delete parameter group")


def main():
    argument_spec = dict(
        state=dict(required=True, choices=["present", "absent"]),
        name=dict(required=True),
        engine=dict(),
        description=dict(),
        params=dict(aliases=["parameters"], type="dict"),
        immediate=dict(type="bool", aliases=["apply_immediately"]),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[["state", "present", ["description", "engine"]]],
        supports_check_mode=True,
    )

    try:
        conn = module.client("rds", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    state = module.params.get("state")
    if state == "present":
        ensure_present(module, conn)
    if state == "absent":
        ensure_absent(module, conn)


if __name__ == "__main__":
    main()
