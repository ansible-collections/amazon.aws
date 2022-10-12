#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
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
            - Can't be supplied together with I(engine_name) or I(major_engine_version).
        default: ''
        required: false
        type: str
    marker:
        description:
            - If this parameter is specified, the response includes only records beyond the marker, up to the value specified by I(max_records).
            - Allowed values are between C(20) and C(100).
        default: ''
        required: false
        type: str
    max_records:
        description:
            - The maximum number of records to include in the response.
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
            - If specified, then I(engine_name) must also be specified.
        type: str
        default: ''
        required: false
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.boto3
'''

EXAMPLES = r'''
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
'''

RETURN = r'''
changed:
    description: True if listing the RDS option group succeeds.
    type: bool
    returned: always
    sample: false
option_groups_list:
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
            description: The tags associated the Internet Gateway.
            type: dict
            returned: always
            sample: {
                "Ansible": "Test"
            }

'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.rds import get_tags


@AWSRetry.jittered_backoff(retries=10)
def _describe_option_groups(client, **params):
    try:
        paginator = client.get_paginator('describe_option_groups')
        return paginator.paginate(**params).build_full_result()
    except is_boto3_error_code('OptionGroupNotFoundFault'):
        return {}


def list_option_groups(client, module):
    option_groups = list()
    params = dict()
    params['OptionGroupName'] = module.params.get('option_group_name')

    if module.params.get('marker'):
        params['Marker'] = module.params.get('marker')
        if int(params['Marker']) < 20 or int(params['Marker']) > 100:
            module.fail_json(msg="marker must be between 20 and 100 minutes")

    if module.params.get('max_records'):
        params['MaxRecords'] = module.params.get('max_records')
        if params['MaxRecords'] > 100:
            module.fail_json(msg="The maximum number of records to include in the response is 100.")

    params['EngineName'] = module.params.get('engine_name')
    params['MajorEngineVersion'] = module.params.get('major_engine_version')

    try:
        result = _describe_option_groups(client, **params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't describe option groups.")

    for option_group in result['OptionGroupsList']:
        # Turn the boto3 result into ansible_friendly_snaked_names
        converted_option_group = camel_dict_to_snake_dict(option_group)
        converted_option_group['tags'] = get_tags(client, module, converted_option_group['option_group_arn'])
        option_groups.append(converted_option_group)

    return option_groups


def main():
    argument_spec = dict(
        option_group_name=dict(default='', type='str'),
        marker=dict(type='str'),
        max_records=dict(type='int', default=100),
        engine_name=dict(type='str', default=''),
        major_engine_version=dict(type='str', default=''),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ['option_group_name', 'engine_name'],
            ['option_group_name', 'major_engine_version'],
        ],
        required_together=[
            ['engine_name', 'major_engine_version'],
        ],
    )

    # Validate Requirements
    try:
        connection = module.client('rds', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    results = list_option_groups(connection, module)

    module.exit_json(result=results)


if __name__ == '__main__':
    main()
