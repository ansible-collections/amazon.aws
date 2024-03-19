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
  immediate:
    description:
      - Whether to apply the changes immediately, or after the next reboot of any associated instances.
      - Ignored when O(state=absent)
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
  - "Aubin Bikouo (@abikouo)"
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Add or change a parameter group, in this case setting auto_increment_increment to 42 * 1024
  amazon.aws.rds_cluster_param_group:
      state: present
      name: test-cluster-group
      description: 'My test RDS cluster group'
      db_parameter_group_family: 'mysql5.6'
      params:
          auto_increment_increment: "42K"
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
from ansible.module_utils.parsing.convert_bool import BOOLEANS_TRUE
from ansible.module_utils.six import string_types

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
def _describe_db_cluster_parameters(module, connection, group_name):
    try:
        paginator = connection.get_paginator("describe_db_cluster_parameters")
        return paginator.paginate(DBClusterParameterGroupName=group_name).build_full_result()
    except is_boto3_error_code("DBParameterGroupNotFound"):
        return None
    except botocore.exceptions.ClientError as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to describe existing RDS cluster parameter groups")


def convert_parameter(param, value):
    """
    Allows setting parameters with 10M = 10* 1024 * 1024 and so on.
    """
    converted_value = value

    if param["DataType"] == "integer":
        if isinstance(value, string_types):
            try:
                for modifier in INT_MODIFIERS.keys():
                    if value.endswith(modifier):
                        converted_value = int(value[:-1]) * INT_MODIFIERS[modifier]
            except ValueError:
                # may be based on a variable (ie. {foo*3/4}) so
                # just pass it on through to the AWS SDK
                pass
        elif isinstance(value, bool):
            converted_value = 1 if value else 0

    elif param["DataType"] == "boolean":
        if isinstance(value, string_types):
            converted_value = value in BOOLEANS_TRUE
        # convert True/False to 1/0
        converted_value = 1 if converted_value else 0
    return str(converted_value)


def update_parameters(module, connection):
    group_name = module.params["name"]
    db_parameter_group_family = module.params["db_parameter_group_family"]
    user_params = module.params["params"]
    apply_method = "immediate" if module.params["immediate"] else "pending-reboot"
    modify_list = []
    db_cluster_params = []
    response = _describe_db_cluster_parameters(module, connection, group_name)
    if response:
        db_cluster_params = response["Parameters"]
    invalids, not_modifiable = [], []
    for param_key, param_value in user_params.items():
        found = list(filter(lambda x: x["ParameterName"] == param_key, db_cluster_params))
        if not found:
            invalids.append(param_key)
            continue
        param_def = found[0]
        converted_value = convert_parameter(param_def, param_value)
        # engine-default parameters do not have a ParameterValue, so we'll always override those.
        if converted_value != param_def.get("ParameterValue"):
            if param_def["IsModifiable"]:
                modify_list.append(
                    dict(ParameterValue=converted_value, ParameterName=param_key, ApplyMethod=apply_method)
                )
            else:
                not_modifiable.append(param_key)
    if not_modifiable or invalids:
        error = ""
        if not_modifiable:
            error += f"The following parameters are not modifiable: {','.join(not_modifiable)}. "
        if invalids:
            error += (
                "The following parameters are not available parameters for the '%s' DB parameter group family: %s."
                % (db_parameter_group_family, ",".join(invalids))
            )
        return False, error

    # modify_db_parameters takes at most 20 parameters
    if modify_list and not module.check_mode:
        for modify_slice in zip_longest(*[iter(modify_list)] * 20, fillvalue=None):
            non_empty_slice = [item for item in modify_slice if item]
            try:
                connection.modify_db_cluster_parameter_group(
                    aws_retry=True, DBClusterParameterGroupName=group_name, Parameters=non_empty_slice
                )
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Couldn't update RDS cluster parameters")
        return True, None
    return False, None


def _list_resource_tags(module, connection, resource_arn):
    try:
        return connection.list_tags_for_resource(aws_retry=True, ResourceName=resource_arn)["TagList"]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't obtain RDS cluster parameter group tags")


def update_tags(module, connection, group_arn, tags):
    if tags is None:
        return False
    changed = False

    existing_tags = _list_resource_tags(module, connection, group_arn)
    to_update, to_delete = compare_aws_tags(
        boto3_tag_list_to_ansible_dict(existing_tags), tags, module.params["purge_tags"]
    )

    if module.check_mode:
        return to_delete or to_update

    if to_update:
        try:
            connection.add_tags_to_resource(
                aws_retry=True,
                ResourceName=group_arn,
                Tags=ansible_dict_to_boto3_tag_list(to_update),
            )
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't add tags to RDS cluster parameter group")
    if to_delete:
        try:
            connection.remove_tags_from_resource(aws_retry=True, ResourceName=group_arn, TagKeys=to_delete)
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't remove tags from RDS cluster parameter group")
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
            changed = update_tags(module, connection, group["DBClusterParameterGroupArn"], tags)

    if module.params.get("params"):
        params_changed, err = update_parameters(module, connection)
        if err:
            module.fail_json(changed=changed, msg=err)
        changed = changed or params_changed

    response = _describe_db_cluster_parameter_group(module=module, connection=connection, group_name=group_name)
    group = camel_dict_to_snake_dict(response["DBClusterParameterGroups"][0])
    group["tags"] = boto3_tag_list_to_ansible_dict(
        _list_resource_tags(module, connection, group["db_cluster_parameter_group_arn"])
    )

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
        params=dict(aliases=["parameters"], type="dict"),
        immediate=dict(type="bool", aliases=["apply_immediately"]),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
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
