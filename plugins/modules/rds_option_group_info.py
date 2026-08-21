#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: rds_option_group_info
short_description: rds_option_group_info module
version_added: 5.0.0
description:
  - Gather information about RDS option groups.
  - This module was originally added to C(community.aws) in release 2.1.0.
author: "Alina Buzachis (@alinabuzachis)"
options:
    option_group_name:
        description:
            - The name of the option group to describe.
            - Can't be supplied together with O(engine_name) or O(major_engine_version).
        default: ''
        required: false
        type: str
    marker:
        description:
            - If this parameter is specified, the response includes only records beyond the marker, up to the value specified by O(max_records).
        required: false
        type: str
    max_records:
        description:
            - The maximum number of records to include in the response.
            - Allowed values are between V(20) and V(100).
        type: int
        default: 100
        required: false
    engine_name:
        description: Filters the list of option groups to only include groups associated with a specific database engine.
        type: str
        default: ''
        required: false
    major_engine_version:
        description:
            - Filters the list of option groups to only include groups associated with a specific database engine version.
            - If specified, then O(engine_name) must also be specified.
        type: str
        default: ''
        required: false
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: List an option group
  amazon.aws.rds_option_group_info:
    option_group_name: test-mysql-option-group
  register: option_group

- name: List all the option groups
  amazon.aws.rds_option_group_info:
    region: ap-southeast-2
    profile: production
  register: option_group
"""

RETURN = r"""
changed:
    description: True if listing the RDS option group succeeds.
    type: bool
    returned: always
    sample: false
result:
    description: The available RDS option groups.
    returned: always
    type: complex
    contains:
        allows_vpc_and_non_vpc_instance_memberships:
            description: Indicates whether this option group can be applied to both VPC and non-VPC instances.
            returned: always
            type: bool
            sample: false
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
            type: complex
            contains:
                db_security_group_memberships:
                    description: If the option requires access to a port, then this DB security group allows access to the port.
                    returned: always
                    type: complex
                    sample: list
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
                    type: complex
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
            description: The tags associated the RDS option group.
            type: dict
            returned: always
            sample: {
                "Ansible": "Test"
            }

"""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.rds import AnsibleRDSError
from ansible_collections.amazon.aws.plugins.module_utils.rds import describe_option_groups
from ansible_collections.amazon.aws.plugins.module_utils.rds import get_tags


def option_group_info(
    client,
    module: AnsibleAWSModule,
    option_group_name: str,
    engine_name: str,
    major_engine_version: str,
    marker: Optional[str],
    max_records: int,
) -> List[Dict[str, Any]]:
    """Return attributes of RDS option group(s), optionally filtered.

    Parameters:
        client: boto3 rds client
        module: AnsibleAWSModule
        option_group_name: Name of a specific option group to describe
        engine_name: Filter by database engine
        major_engine_version: Filter by major engine version
        marker: Pagination marker
        max_records: Maximum number of records to return

    Returns:
        List of option group attribute dicts in snake_case format
    """
    params = {}

    if option_group_name:
        params["OptionGroupName"] = option_group_name
    if engine_name:
        params["EngineName"] = engine_name
    if major_engine_version:
        params["MajorEngineVersion"] = major_engine_version

    if marker:
        params["Marker"] = marker

    if max_records:
        if max_records < 20 or max_records > 100:
            module.fail_json(msg="The maximum number of records to include in the response must be between 20 and 100.")
        params["MaxRecords"] = max_records

    results = describe_option_groups(client, **params)

    output = []
    for option_group in results:
        option_group["Tags"] = get_tags(client, module, option_group["OptionGroupArn"])
        output.append(camel_dict_to_snake_dict(option_group, ignore_list=["Tags"]))

    return output


def main():
    argument_spec = dict(
        option_group_name=dict(default="", type="str"),
        marker=dict(type="str"),
        max_records=dict(type="int", default=100),
        engine_name=dict(type="str", default=""),
        major_engine_version=dict(type="str", default=""),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ["option_group_name", "engine_name"],
            ["option_group_name", "major_engine_version"],
        ],
        required_together=[
            ["engine_name", "major_engine_version"],
        ],
    )

    client = module.client("rds")

    try:
        module.exit_json(
            changed=False,
            result=option_group_info(
                client,
                module,
                option_group_name=module.params.get("option_group_name"),
                engine_name=module.params.get("engine_name"),
                major_engine_version=module.params.get("major_engine_version"),
                marker=module.params.get("marker"),
                max_records=module.params.get("max_records"),
            ),
        )
    except AnsibleRDSError as e:
        module.fail_json_aws(e, msg="Could not describe option groups.")


if __name__ == "__main__":
    main()
