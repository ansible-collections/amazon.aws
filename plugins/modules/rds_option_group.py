#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: rds_option_group
short_description: Manages the creation, modification, deletion of RDS option groups
version_added: 5.0.0
description:
  - Manages the creation, modification, deletion of RDS option groups.
  - This module was originally added to C(community.aws) in release 2.1.0.
author:
  - "Nick Aslanidis (@naslanidis)"
  - "Will Thames (@willthames)"
  - "Alina Buzachis (@alinabuzachis)"
options:
  state:
    description:
      - Specifies whether the option group should be C(present) or C(absent).
    required: true
    choices: [ 'present', 'absent' ]
    type: str
  option_group_name:
    description:
      - Specifies the name of the option group to be created.
    required: true
    type: str
  engine_name:
    description:
      - Specifies the name of the engine that this option group should be associated with.
    type: str
  major_engine_version:
    description:
      - Specifies the major version of the engine that this option group should be associated with.
    type: str
  option_group_description:
    description:
      - The description of the option group.
    type: str
  apply_immediately:
    description:
      - Indicates whether the changes should be applied immediately, or during the next maintenance window.
    required: false
    type: bool
    default: false
  options:
    description:
      - Options in this list are added to the option group.
      - If already present, the specified configuration is used to update the existing configuration.
      - If none are supplied, any existing options are removed.
    type: list
    elements: dict
    suboptions:
        option_name:
            description: The configuration of options to include in a group.
            required: false
            type: str
        port:
            description: The optional port for the option.
            required: false
            type: int
        option_version:
            description: The version for the option.
            required: false
            type: str
        option_settings:
            description: The option settings to include in an option group.
            required: false
            type: list
            elements: dict
            suboptions:
                name:
                    description: The name of the option that has settings that you can set.
                    required: false
                    type: str
                value:
                    description: The current value of the option setting.
                    required: false
                    type: str
                default_value:
                    description: The default value of the option setting.
                    required: false
                    type: str
                description:
                    description: The description of the option setting.
                    required: false
                    type: str
                apply_type:
                    description: The DB engine specific parameter type.
                    required: false
                    type: str
                data_type:
                    description: The data type of the option setting.
                    required: false
                    type: str
                allowed_values:
                    description: The allowed values of the option setting.
                    required: false
                    type: str
                is_modifiable:
                    description: A Boolean value that, when C(true), indicates the option setting can be modified from the default.
                    required: false
                    type: bool
                is_collection:
                    description: Indicates if the option setting is part of a collection.
                    required: false
                    type: bool
        db_security_group_memberships:
            description: A list of C(DBSecurityGroupMembership) name strings used for this option.
            required: false
            type: list
            elements: str
        vpc_security_group_memberships:
            description: A list of C(VpcSecurityGroupMembership) name strings used for this option.
            required: false
            type: list
            elements: str
  wait:
    description: Whether to wait for the cluster to be available or deleted.
    type: bool
    default: True
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Create an RDS Mysql Option group
- name: Create an RDS Mysql option group
  amazon.aws.rds_option_group:
    state: present
    option_group_name: test-mysql-option-group
    engine_name: mysql
    major_engine_version: 5.6
    option_group_description: test mysql option group
    apply_immediately: true
    options:
        - option_name: MEMCACHED
          port: 11211
          vpc_security_group_memberships:
            - "sg-d188c123"
          option_settings:
            - name: MAX_SIMULTANEOUS_CONNECTIONS
              value: "20"
            - name: CHUNK_SIZE_GROWTH_FACTOR
              value: "1.25"
  register: new_rds_mysql_option_group

# Remove currently configured options for an option group by removing options argument
- name: Create an RDS Mysql option group
  amazon.aws.rds_option_group:
    state: present
    option_group_name: test-mysql-option-group
    engine_name: mysql
    major_engine_version: 5.6
    option_group_description: test mysql option group
    apply_immediately: true
  register: rds_mysql_option_group

- name: Create an RDS Mysql option group using tags
  amazon.aws.rds_option_group:
    state: present
    option_group_name: test-mysql-option-group
    engine_name: mysql
    major_engine_version: 5.6
    option_group_description: test mysql option group
    apply_immediately: true
    tags:
        Tag1: tag1
        Tag2: tag2
  register: rds_mysql_option_group

# Delete an RDS Mysql Option group
- name: Delete an RDS Mysql option group
  amazon.aws.rds_option_group:
    state: absent
    option_group_name: test-mysql-option-group
  register: deleted_rds_mysql_option_group
"""

RETURN = r"""
allows_vpc_and_non_vpc_instance_memberships:
    description: Indicates whether this option group can be applied to both VPC and non-VPC instances.
    returned: always
    type: bool
    sample: false
changed:
    description: If the Option Group has changed.
    type: bool
    returned: always
    sample: true
engine_name:
    description: Indicates the name of the engine that this option group can be applied to.
    returned: always
    type: str
    sample: "mysql"
major_engine_version:
    description: Indicates the major engine version associated with this option group.
    returned: always
    type: str
    sample: "5.6"
option_group_arn:
    description: The Amazon Resource Name (ARN) for the option group.
    returned: always
    type: str
    sample: "arn:aws:rds:ap-southeast-2:123456789012:og:ansible-test-option-group"
option_group_description:
    description: Provides a description of the option group.
    returned: always
    type: str
    sample: "test mysql option group"
option_group_name:
    description: Specifies the name of the option group.
    returned: always
    type: str
    sample: "test-mysql-option-group"
options:
    description: Indicates what options are available in the option group.
    returned: always
    type: list
    elements: dict
    contains:
        db_security_group_memberships:
            description: If the option requires access to a port, then this DB security group allows access to the port.
            returned: always
            type: list
            elements: dict
            contains:
                status:
                    description: The status of the DB security group.
                    returned: always
                    type: str
                    sample: "available"
                db_security_group_name:
                    description: The name of the DB security group.
                    returned: always
                    type: str
                    sample: "mydbsecuritygroup"
        option_description:
            description: The description of the option.
            returned: always
            type: str
            sample: "Innodb Memcached for MySQL"
        option_name:
            description: The name of the option.
            returned: always
            type: str
            sample: "MEMCACHED"
        option_settings:
            description: The name of the option.
            returned: always
            type: list
            contains:
                allowed_values:
                    description: The allowed values of the option setting.
                    returned: always
                    type: str
                    sample: "1-2048"
                apply_type:
                    description: The DB engine specific parameter type.
                    returned: always
                    type: str
                    sample: "STATIC"
                data_type:
                    description: The data type of the option setting.
                    returned: always
                    type: str
                    sample: "INTEGER"
                default_value:
                    description: The default value of the option setting.
                    returned: always
                    type: str
                    sample: "1024"
                description:
                    description: The description of the option setting.
                    returned: always
                    type: str
                    sample: "Verbose level for memcached."
                is_collection:
                    description: Indicates if the option setting is part of a collection.
                    returned: always
                    type: bool
                    sample: true
                is_modifiable:
                    description: A Boolean value that, when true, indicates the option setting can be modified from the default.
                    returned: always
                    type: bool
                    sample: true
                name:
                    description: The name of the option that has settings that you can set.
                    returned: always
                    type: str
                    sample: "INNODB_API_ENABLE_MDL"
                value:
                    description: The current value of the option setting.
                    returned: always
                    type: str
                    sample: "0"
        permanent:
            description: Indicate if this option is permanent.
            returned: always
            type: bool
            sample: true
        persistent:
            description: Indicate if this option is persistent.
            returned: always
            type: bool
            sample: true
        port:
            description: If required, the port configured for this option to use.
            returned: always
            type: int
            sample: 11211
        vpc_security_group_memberships:
            description: If the option requires access to a port, then this VPC security group allows access to the port.
            returned: always
            type: list
            elements: dict
            contains:
                status:
                    description: The status of the VPC security group.
                    returned: always
                    type: str
                    sample: "available"
                vpc_security_group_id:
                    description: The name of the VPC security group.
                    returned: always
                    type: str
                    sample: "sg-0cd636a23ae76e9a4"
vpc_id:
    description: If present, this option group can only be applied to instances that are in the VPC indicated by this field.
    returned: always
    type: str
    sample: "vpc-bf07e9d6"
tags:
    description: The tags associated the Internet Gateway.
    type: dict
    returned: always
    sample: {
        "Ansible": "Test"
    }
"""


from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.rds import get_tags

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule


@AWSRetry.jittered_backoff(retries=10)
def _describe_option_groups(client, **params):
    try:
        paginator = client.get_paginator("describe_option_groups")
        return paginator.paginate(**params).build_full_result()["OptionGroupsList"][0]
    except is_boto3_error_code("OptionGroupNotFoundFault"):
        return {}


def get_option_group(client, module):
    params = dict()
    params["OptionGroupName"] = module.params.get("option_group_name")

    try:
        result = camel_dict_to_snake_dict(_describe_option_groups(client, **params))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't describe option groups.")

    if result:
        result["tags"] = get_tags(client, module, result["option_group_arn"])

    return result


def create_option_group_options(client, module):
    changed = True
    params = dict()
    params["OptionGroupName"] = module.params.get("option_group_name")
    options_to_include = module.params.get("options")
    params["OptionsToInclude"] = snake_dict_to_camel_dict(options_to_include, capitalize_first=True)

    if module.params.get("apply_immediately"):
        params["ApplyImmediately"] = module.params.get("apply_immediately")

    if module.check_mode:
        return changed

    try:
        client.modify_option_group(aws_retry=True, **params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to update Option Group.")

    return changed


def remove_option_group_options(client, module, options_to_remove):
    changed = True
    params = dict()
    params["OptionGroupName"] = module.params.get("option_group_name")
    params["OptionsToRemove"] = options_to_remove

    if module.params.get("apply_immediately"):
        params["ApplyImmediately"] = module.params.get("apply_immediately")

    if module.check_mode:
        return changed

    try:
        client.modify_option_group(aws_retry=True, **params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e)

    return changed


def create_option_group(client, module):
    changed = True
    params = dict()
    params["OptionGroupName"] = module.params.get("option_group_name")
    params["EngineName"] = module.params.get("engine_name")
    params["MajorEngineVersion"] = str(module.params.get("major_engine_version"))
    params["OptionGroupDescription"] = module.params.get("option_group_description")

    if module.params.get("tags"):
        params["Tags"] = ansible_dict_to_boto3_tag_list(module.params.get("tags"))
    else:
        params["Tags"] = list()

        if module.check_mode:
            return changed
    try:
        client.create_option_group(aws_retry=True, **params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to create Option Group.")

    return changed


def match_option_group_options(client, module):
    requires_update = False
    new_options = module.params.get("options")

    # Get existing option groups and compare to our new options spec
    current_option = get_option_group(client, module)

    if current_option["options"] == [] and new_options:
        requires_update = True
    else:
        for option in current_option["options"]:
            for setting_name in new_options:
                if setting_name["option_name"] == option["option_name"]:
                    # Security groups need to be handled separately due to different keys on request and what is
                    # returned by the API
                    if any(
                        name in option.keys() - ["option_settings", "vpc_security_group_memberships"]
                        and setting_name[name] != option[name]
                        for name in setting_name
                    ):
                        requires_update = True

                    if any(name in option and name == "vpc_security_group_memberships" for name in setting_name):
                        current_sg = set(sg["vpc_security_group_id"] for sg in option["vpc_security_group_memberships"])
                        new_sg = set(setting_name["vpc_security_group_memberships"])
                        if current_sg != new_sg:
                            requires_update = True

                    if any(
                        new_option_setting["name"] == current_option_setting["name"]
                        and new_option_setting["value"] != current_option_setting["value"]
                        for new_option_setting in setting_name["option_settings"]
                        for current_option_setting in option["option_settings"]
                    ):
                        requires_update = True
                else:
                    requires_update = True

    return requires_update


def compare_option_group(client, module):
    to_be_added = None
    to_be_removed = None
    current_option = get_option_group(client, module)
    new_options = module.params.get("options")
    new_settings = set([item["option_name"] for item in new_options])
    old_settings = set([item["option_name"] for item in current_option["options"]])

    if new_settings != old_settings:
        to_be_added = list(new_settings - old_settings)
        to_be_removed = list(old_settings - new_settings)

    return to_be_added, to_be_removed


def setup_option_group(client, module):
    results = []
    changed = False
    to_be_added = None
    to_be_removed = None

    # Check if there is an existing options group
    existing_option_group = get_option_group(client, module)

    if existing_option_group:
        results = existing_option_group

        # Check tagging
        changed |= update_tags(client, module, existing_option_group)

        if module.params.get("options"):
            # Check if existing options require updating
            update_required = match_option_group_options(client, module)

            # Check if there are options to be added or removed
            if update_required:
                to_be_added, to_be_removed = compare_option_group(client, module)

            if to_be_added or update_required:
                changed |= create_option_group_options(client, module)

            if to_be_removed:
                changed |= remove_option_group_options(client, module, to_be_removed)

            # If changed, get updated version of option group
            if changed:
                results = get_option_group(client, module)
        else:
            # No options were supplied. If options exist, remove them
            current_option_group = get_option_group(client, module)

            if current_option_group["options"] != []:
                # Here we would call our remove options function
                options_to_remove = []

                for option in current_option_group["options"]:
                    options_to_remove.append(option["option_name"])

                changed |= remove_option_group_options(client, module, options_to_remove)

            # If changed, get updated version of option group
            if changed:
                results = get_option_group(client, module)
    else:
        changed = create_option_group(client, module)

        if module.params.get("options"):
            changed = create_option_group_options(client, module)

        results = get_option_group(client, module)

    return changed, results


def remove_option_group(client, module):
    changed = False
    params = dict()
    params["OptionGroupName"] = module.params.get("option_group_name")

    # Check if there is an existing options group
    existing_option_group = get_option_group(client, module)

    if existing_option_group:
        if module.check_mode:
            return True, {}

        changed = True
        try:
            client.delete_option_group(aws_retry=True, **params)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Unable to delete option group.")

    return changed, {}


def update_tags(client, module, option_group):
    if module.params.get("tags") is None:
        return False

    try:
        existing_tags = client.list_tags_for_resource(aws_retry=True, ResourceName=option_group["option_group_arn"])[
            "TagList"
        ]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't obtain option group tags.")

    to_update, to_delete = compare_aws_tags(
        boto3_tag_list_to_ansible_dict(existing_tags), module.params["tags"], module.params["purge_tags"]
    )
    changed = bool(to_update or to_delete)

    if to_update:
        try:
            if module.check_mode:
                return changed
            client.add_tags_to_resource(
                aws_retry=True,
                ResourceName=option_group["option_group_arn"],
                Tags=ansible_dict_to_boto3_tag_list(to_update),
            )
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't add tags to option group.")
    if to_delete:
        try:
            if module.check_mode:
                return changed
            client.remove_tags_from_resource(
                aws_retry=True, ResourceName=option_group["option_group_arn"], TagKeys=to_delete
            )
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't remove tags from option group.")

    return changed


def main():
    argument_spec = dict(
        option_group_name=dict(required=True, type="str"),
        engine_name=dict(type="str"),
        major_engine_version=dict(type="str"),
        option_group_description=dict(type="str"),
        options=dict(required=False, type="list", elements="dict"),
        apply_immediately=dict(type="bool", default=False),
        state=dict(required=True, choices=["present", "absent"]),
        tags=dict(required=False, type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        wait=dict(type="bool", default=True),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[["state", "present", ["engine_name", "major_engine_version", "option_group_description"]]],
    )

    try:
        client = module.client("rds", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    state = module.params.get("state")

    if state == "present":
        changed, results = setup_option_group(client, module)
    else:
        changed, results = remove_option_group(client, module)

    module.exit_json(changed=changed, **results)


if __name__ == "__main__":
    main()
