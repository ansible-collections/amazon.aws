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
  amazon.aws.rds_cluster_param_group:
      state: absent
      name: test-cluster-group
"""

RETURN = r"""
db_cluster_parameter_group:
    description: dictionary containing all the RDS cluster parameter group information.
    returned: success
    type: complex
    contains:
        db_cluster_parameter_group_arn:
            description: The Amazon Resource Name (ARN) for the RDS cluster parameter group.
            type: str
            returned: when O(state=present)
            sample: "arn:aws:rds:us-west-2:123456789012:cluster-pg:ansible-test-123456789012-redhat-cluster-param-group"
        db_cluster_parameter_group_name:
            description: The name of the RDS cluster parameter group.
            type: str
            returned: when O(state=present)
            sample: "ansible-test-123456789012-redhat-cluster-param-group"
        db_parameter_group_family:
            description: The name of the RDS parameter group family that this RDS cluster parameter group is compatible with.
            type: str
            returned: when O(state=present)
            sample: "postgres16"
        description:
            description: Provides the customer-specified description for this RDS cluster parameter group.
            type: str
            returned: when O(state=present)
            sample: "RDS cluster param group"
        tags:
            description: A dictionary of tags.
            type: dict
            returned: when O(state=present)
            sample: {
                "another": "tag",
                "resource_prefix": "ansible-test-53268383-redhat",
                "some": "tag"
            }
"""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.rds import AnsibleRDSError
from ansible_collections.amazon.aws.plugins.module_utils.rds import create_db_cluster_parameter_group
from ansible_collections.amazon.aws.plugins.module_utils.rds import delete_db_cluster_parameter_group
from ansible_collections.amazon.aws.plugins.module_utils.rds import describe_db_cluster_parameter_groups
from ansible_collections.amazon.aws.plugins.module_utils.rds import describe_db_cluster_parameters
from ansible_collections.amazon.aws.plugins.module_utils.rds import ensure_tags
from ansible_collections.amazon.aws.plugins.module_utils.rds import get_tags
from ansible_collections.amazon.aws.plugins.module_utils.rds import modify_db_cluster_parameter_group
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list


def get_parameter_group(client, group_name: str) -> Optional[Dict[str, Any]]:
    """Return the RDS cluster parameter group with the given name.

    Args:
        client: A boto3 RDS client.
        group_name: Name of the RDS cluster parameter group.

    Returns:
        The parameter group as returned by the RDS API, or None if it does not exist.

    Raises:
        AnsibleRDSError: If the parameter groups could not be described.
    """
    groups = describe_db_cluster_parameter_groups(client, DBClusterParameterGroupName=group_name)
    return groups[0] if groups else None


def has_changed_parameters(
    module: AnsibleAWSModule, current_params: List[Dict[str, Any]], desired_params: List[Dict[str, Any]]
) -> bool:
    """Compare the desired parameters against their current values.

    Fails the module if a desired parameter is unknown or is not modifiable.

    Args:
        module: The AnsibleAWSModule instance.
        current_params: Parameters currently set on the RDS cluster parameter group.
        desired_params: Desired parameters, camel-cased and capitalized.

    Returns:
        True if any desired parameter differs from its current value.
    """
    current_by_name = {param["ParameterName"]: param for param in current_params}
    changed = False
    for param in desired_params:
        name = param.get("ParameterName")
        current_param = current_by_name.get(name)
        if current_param is None:
            module.fail_json(msg=f"Could not find parameter with name: {name}")
        if not current_param["IsModifiable"]:
            module.fail_json(msg=f"The parameter {name} cannot be modified")
        changed |= any(current_param.get(key) != value for key, value in param.items())
    return changed


def modify_parameters(client, module: AnsibleAWSModule, group_name: str, parameters: List[Dict[str, Any]]) -> bool:
    """Compare desired parameters against current values and apply the ones that changed.

    Args:
        client: A boto3 RDS client.
        module: The AnsibleAWSModule instance.
        group_name: Name of the RDS cluster parameter group.
        parameters: Desired parameters as dicts of parameter_name, parameter_value and apply_method.

    Returns:
        True if a change was made.

    Raises:
        AnsibleRDSError: If the parameters could not be described or modified.
    """
    current_params = describe_db_cluster_parameters(client, DBClusterParameterGroupName=group_name)
    desired_params = snake_dict_to_camel_dict(parameters, capitalize_first=True)
    changed = has_changed_parameters(module, current_params, desired_params)
    if changed and not module.check_mode:
        modify_db_cluster_parameter_group(client, group_name, desired_params)
    return changed


def create_parameter_group(client, module: AnsibleAWSModule) -> Dict[str, Any]:
    """Create an RDS cluster parameter group.

    Args:
        client: A boto3 RDS client.
        module: The AnsibleAWSModule instance.

    Returns:
        The newly created parameter group as returned by the RDS API.

    Raises:
        AnsibleRDSError: If the parameter group could not be created.
    """
    params = dict(
        DBClusterParameterGroupName=module.params["name"],
        DBParameterGroupFamily=module.params["db_parameter_group_family"],
        Description=module.params["description"],
    )
    tags = module.params.get("tags")
    if tags:
        params["Tags"] = ansible_dict_to_boto3_tag_list(tags)
    return create_db_cluster_parameter_group(client, **params)["DBClusterParameterGroup"]


def update_parameter_group(client, module: AnsibleAWSModule, group: Dict[str, Any]) -> bool:
    """Update the tags of an existing RDS cluster parameter group.

    Warns if a different parameter group family is requested, as the family is immutable.

    Args:
        client: A boto3 RDS client.
        module: The AnsibleAWSModule instance.
        group: The existing parameter group as returned by the RDS API.

    Returns:
        True if a change was made.
    """
    if module.params["db_parameter_group_family"] != group["DBParameterGroupFamily"]:
        module.warn(
            "The RDS cluster parameter group family is immutable and can't be changed when updating a RDS cluster parameter group."
        )

    tags = module.params.get("tags")
    if not tags:
        return False

    group_arn = group["DBClusterParameterGroupArn"]
    existing_tags = get_tags(client, module, group_arn)
    return ensure_tags(client, module, group_arn, existing_tags, tags, module.params["purge_tags"])


def ensure_present(client, module: AnsibleAWSModule) -> None:
    """Create or update an RDS cluster parameter group, including its tags and parameters.

    Args:
        client: A boto3 RDS client.
        module: The AnsibleAWSModule instance.

    Raises:
        AnsibleRDSError: If the parameter group could not be created or updated.
    """
    group_name = module.params["name"]
    group = get_parameter_group(client, group_name)

    if group is None:
        if module.check_mode:
            module.exit_json(changed=True, msg="Would have create RDS parameter group if not in check mode.")
        group = create_parameter_group(client, module)
        changed = True
    else:
        changed = update_parameter_group(client, module, group)

    if module.params.get("parameters"):
        changed |= modify_parameters(client, module, group_name, module.params["parameters"])

    result = camel_dict_to_snake_dict(group)
    result["tags"] = get_tags(client, module, group["DBClusterParameterGroupArn"])

    module.exit_json(changed=changed, db_cluster_parameter_group=result)


def ensure_absent(client, module: AnsibleAWSModule) -> None:
    """Delete an RDS cluster parameter group if it exists.

    Args:
        client: A boto3 RDS client.
        module: The AnsibleAWSModule instance.

    Raises:
        AnsibleRDSError: If the parameter group could not be deleted.
    """
    group_name = module.params["name"]
    if get_parameter_group(client, group_name) is None:
        module.exit_json(changed=False, msg="The RDS cluster parameter group does not exist.")

    if not module.check_mode:
        delete_db_cluster_parameter_group(client, group_name)
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

    client = module.client("rds", retry_decorator=AWSRetry.jittered_backoff())

    try:
        if module.params["state"] == "present":
            ensure_present(client, module)
        else:
            ensure_absent(client, module)
    except AnsibleRDSError as e:
        module.fail_json_aws(e, msg="Failed to manage RDS cluster parameter group")


if __name__ == "__main__":
    main()
