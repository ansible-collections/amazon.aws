#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: elasticache_parameter_group
version_added: 1.0.0
short_description: Manage cache parameter groups in Amazon ElastiCache.
description:
  - Manage cache security groups in Amazon ElastiCache.
  - Returns information about the specified cache cluster.
author:
  - "Sloane Hertel (@s-hertel)"

options:
  group_family:
    description:
      - The name of the cache parameter group family that the cache parameter group can be used with.
        Required when creating a cache parameter group.
    choices: ['memcached1.4', 'memcached1.5', 'redis2.6', 'redis2.8', 'redis3.2', 'redis4.0', 'redis5.0', 'redis6.x']
    type: str
  name:
    description:
     - A user-specified name for the cache parameter group.
    required: true
    type: str
  description:
    description:
      - A user-specified description for the cache parameter group.
    type: str
    default: ''
  state:
    description:
      - Idempotent actions that will create/modify, destroy, or reset a cache parameter group as needed.
    choices: ['present', 'absent', 'reset']
    required: true
    type: str
  values:
    description:
      - A user-specified dictionary of parameters to reset or modify for the cache parameter group.
    type: dict

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: None of these examples set aws_access_key, aws_secret_key, or region.
# It is assumed that their matching environment variables are set.
---
- hosts: localhost
  connection: local
  tasks:
    - name: 'Create a test parameter group'
      community.aws.elasticache_parameter_group:
        name: 'test-param-group'
        group_family: 'redis3.2'
        description: 'This is a cache parameter group'
        state: 'present'
    - name: 'Modify a test parameter group'
      community.aws.elasticache_parameter_group:
        name: 'test-param-group'
        values:
          activerehashing: yes
          client-output-buffer-limit-normal-hard-limit: 4
        state: 'present'
    - name: 'Reset all modifiable parameters for the test parameter group'
      community.aws.elasticache_parameter_group:
        name: 'test-param-group'
        state: reset
    - name: 'Delete a test parameter group'
      community.aws.elasticache_parameter_group:
        name: 'test-param-group'
        state: 'absent'
"""

RETURN = r"""
elasticache:
  description: cache parameter group information and response metadata
  returned: always
  type: dict
  sample:
    cache_parameter_group:
      cache_parameter_group_family: redis3.2
      cache_parameter_group_name: test-please-delete
      description: "initial description"
    response_metadata:
      http_headers:
        content-length: "562"
        content-type: text/xml
        date: "Mon, 06 Feb 2017 22:14:08 GMT"
        x-amzn-requestid: 947291f9-ecb9-11e6-85bd-3baa4eca2cc1
      http_status_code: 200
      request_id: 947291f9-ecb9-11e6-85bd-3baa4eca2cc1
      retry_attempts: 0
changed:
  description: if the cache parameter group has changed
  returned: always
  type: bool
  sample:
    changed: true
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils._text import to_text
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.six import string_types

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def create(module, conn, name, group_family, description):
    """Create ElastiCache parameter group."""
    try:
        response = conn.create_cache_parameter_group(
            CacheParameterGroupName=name, CacheParameterGroupFamily=group_family, Description=description
        )
        changed = True
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to create cache parameter group.")
    return response, changed


def delete(module, conn, name):
    """Delete ElastiCache parameter group."""
    try:
        conn.delete_cache_parameter_group(CacheParameterGroupName=name)
        response = {}
        changed = True
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to delete cache parameter group.")
    return response, changed


def make_current_modifiable_param_dict(module, conn, name):
    """Gets the current state of the cache parameter group and creates a dict with the format: {ParameterName: [Allowed_Values, DataType, ParameterValue]}"""
    current_info = get_info(conn, name)
    if current_info is False:
        module.fail_json(msg=f"Could not connect to the cache parameter group {name}.")

    parameters = current_info["Parameters"]
    modifiable_params = {}

    for param in parameters:
        if param["IsModifiable"]:
            modifiable_params[param["ParameterName"]] = [param.get("AllowedValues")]
            modifiable_params[param["ParameterName"]].append(param["DataType"])
            modifiable_params[param["ParameterName"]].append(param.get("ParameterValue"))
    return modifiable_params


def check_valid_modification(module, values, modifiable_params):
    """Check if the parameters and values in values are valid."""
    changed_with_update = False

    for parameter in values:
        new_value = values[parameter]

        # check valid modifiable parameters
        if parameter not in modifiable_params:
            module.fail_json(
                msg=f"{parameter} is not a modifiable parameter. Valid parameters to modify are: {modifiable_params.keys()}."
            )

        # check allowed datatype for modified parameters
        str_to_type = {"integer": int, "string": string_types}
        expected_type = str_to_type[modifiable_params[parameter][1]]
        if not isinstance(new_value, expected_type):
            if expected_type == str:
                if isinstance(new_value, bool):
                    values[parameter] = "yes" if new_value else "no"
                else:
                    values[parameter] = to_text(new_value)
            elif expected_type == int:
                if isinstance(new_value, bool):
                    values[parameter] = 1 if new_value else 0
                else:
                    module.fail_json(
                        msg=(
                            f"{new_value} (type {type(new_value)}) is not an allowed value for the parameter"
                            f" {parameter}. Expected a type {modifiable_params[parameter][1]}."
                        )
                    )
            else:
                module.fail_json(
                    msg=(
                        f"{new_value} (type {type(new_value)}) is not an allowed value for the parameter {parameter}."
                        f" Expected a type {modifiable_params[parameter][1]}."
                    )
                )

        # check allowed values for modifiable parameters
        choices = modifiable_params[parameter][0]
        if choices:
            if not (to_text(new_value) in choices or isinstance(new_value, int)):
                module.fail_json(
                    msg=f"{new_value} is not an allowed value for the parameter {parameter}. Valid parameters are: {choices}."
                )

        # check if a new value is different from current value
        if to_text(values[parameter]) != modifiable_params[parameter][2]:
            changed_with_update = True

    return changed_with_update, values


def check_changed_parameter_values(values, old_parameters, new_parameters):
    """Checking if the new values are different than the old values."""
    changed_with_update = False

    # if the user specified parameters to reset, only check those for change
    if values:
        for parameter in values:
            if old_parameters[parameter] != new_parameters[parameter]:
                changed_with_update = True
                break
    # otherwise check all to find a change
    else:
        for parameter in old_parameters:
            if old_parameters[parameter] != new_parameters[parameter]:
                changed_with_update = True
                break

    return changed_with_update


def modify(module, conn, name, values):
    """Modify ElastiCache parameter group to reflect the new information if it differs from the current."""
    # compares current group parameters with the parameters we've specified to to a value to see if this will change the group
    format_parameters = []
    for key in values:
        value = to_text(values[key])
        format_parameters.append({"ParameterName": key, "ParameterValue": value})
    try:
        response = conn.modify_cache_parameter_group(
            CacheParameterGroupName=name, ParameterNameValues=format_parameters
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to modify cache parameter group.")
    return response


def reset(module, conn, name, values):
    """Reset ElastiCache parameter group if the current information is different from the new information."""
    # used to compare with the reset parameters' dict to see if there have been changes
    old_parameters_dict = make_current_modifiable_param_dict(module, conn, name)

    format_parameters = []

    # determine whether to reset all or specific parameters
    if values:
        all_parameters = False
        format_parameters = []
        for key in values:
            value = to_text(values[key])
            format_parameters.append({"ParameterName": key, "ParameterValue": value})
    else:
        all_parameters = True

    try:
        response = conn.reset_cache_parameter_group(
            CacheParameterGroupName=name, ParameterNameValues=format_parameters, ResetAllParameters=all_parameters
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to reset cache parameter group.")

    # determine changed
    new_parameters_dict = make_current_modifiable_param_dict(module, conn, name)
    changed = check_changed_parameter_values(values, old_parameters_dict, new_parameters_dict)

    return response, changed


def get_info(conn, name):
    """Gets info about the ElastiCache parameter group. Returns false if it doesn't exist or we don't have access."""
    try:
        data = conn.describe_cache_parameters(CacheParameterGroupName=name)
        return data
    except botocore.exceptions.ClientError as e:
        return False


def main():
    argument_spec = dict(
        group_family=dict(
            type="str",
            choices=[
                "memcached1.4",
                "memcached1.5",
                "redis2.6",
                "redis2.8",
                "redis3.2",
                "redis4.0",
                "redis5.0",
                "redis6.x",
            ],
        ),
        name=dict(required=True, type="str"),
        description=dict(default="", type="str"),
        state=dict(required=True, choices=["present", "absent", "reset"]),
        values=dict(type="dict"),
    )
    module = AnsibleAWSModule(argument_spec=argument_spec)

    parameter_group_family = module.params.get("group_family")
    parameter_group_name = module.params.get("name")
    group_description = module.params.get("description")
    state = module.params.get("state")
    values = module.params.get("values")

    try:
        connection = module.client("elasticache")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    exists = get_info(connection, parameter_group_name)

    # check that the needed requirements are available
    if state == "present" and not (exists or parameter_group_family):
        module.fail_json(msg="Creating a group requires a family group.")
    elif state == "reset" and not exists:
        module.fail_json(
            msg=f"No group {parameter_group_name} to reset. Please create the group before using the state 'reset'."
        )

    # Taking action
    changed = False
    if state == "present":
        if exists:
            # confirm that the group exists without any actions
            if not values:
                response = exists
                changed = False
            # modify existing group
            else:
                modifiable_params = make_current_modifiable_param_dict(module, connection, parameter_group_name)
                changed, values = check_valid_modification(module, values, modifiable_params)
                response = modify(module, connection, parameter_group_name, values)
        # create group
        else:
            response, changed = create(
                module, connection, parameter_group_name, parameter_group_family, group_description
            )
            if values:
                modifiable_params = make_current_modifiable_param_dict(module, connection, parameter_group_name)
                changed, values = check_valid_modification(module, values, modifiable_params)
                response = modify(module, connection, parameter_group_name, values)
    elif state == "absent":
        if exists:
            # delete group
            response, changed = delete(module, connection, parameter_group_name)
        else:
            response = {}
            changed = False
    elif state == "reset":
        response, changed = reset(module, connection, parameter_group_name, values)

    facts_result = dict(changed=changed, elasticache=camel_dict_to_snake_dict(response))

    module.exit_json(**facts_result)


if __name__ == "__main__":
    main()
