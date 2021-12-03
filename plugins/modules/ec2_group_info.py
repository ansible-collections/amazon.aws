#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: ec2_group_info
version_added: 1.0.0
short_description: Gather information about ec2 security groups in AWS.
description:
    - Gather information about ec2 security groups in AWS.
author:
- Henrique Rodrigues (@Sodki)
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. See
        U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeSecurityGroups.html) for
        possible filters. Filter names and values are case sensitive. You can also use underscores (_)
        instead of dashes (-) in the filter keys, which will take precedence in case of conflict.
    required: false
    default: {}
    type: dict
notes:
  - By default, the module will return all security groups. To limit results use the appropriate filters.

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather information about all security groups
- amazon.aws.ec2_group_info:

# Gather information about all security groups in a specific VPC
- amazon.aws.ec2_group_info:
    filters:
      vpc-id: vpc-12345678

# Gather information about all security groups in a specific VPC
- amazon.aws.ec2_group_info:
    filters:
      vpc-id: vpc-12345678

# Gather information about a security group
- amazon.aws.ec2_group_info:
    filters:
      group-name: example-1

# Gather information about a security group by id
- amazon.aws.ec2_group_info:
    filters:
      group-id: sg-12345678

# Gather information about a security group with multiple filters, also mixing the use of underscores as filter keys
- amazon.aws.ec2_group_info:
    filters:
      group_id: sg-12345678
      vpc-id: vpc-12345678

# Gather information about various security groups
- amazon.aws.ec2_group_info:
    filters:
      group-name:
        - example-1
        - example-2
        - example-3

# Gather information about any security group with a tag key Name and value Example.
# The quotes around 'tag:name' are important because of the colon in the value
- amazon.aws.ec2_group_info:
    filters:
      "tag:Name": Example
'''

RETURN = '''
security_groups:
    description: Security groups that match the provided filters. Each element consists of a dict with all the information related to that security group.
    type: list
    returned: always
    sample:
'''

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ..module_utils.core import AnsibleAWSModule
from ..module_utils.ec2 import AWSRetry
from ..module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ..module_utils.ec2 import boto3_tag_list_to_ansible_dict


def main():
    argument_spec = dict(
        filters=dict(default={}, type='dict')
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client('ec2', AWSRetry.jittered_backoff())

    # Replace filter key underscores with dashes, for compatibility, except if we're dealing with tags
    filters = module.params.get("filters")
    sanitized_filters = dict()

    for key in filters:
        if key.startswith("tag:"):
            sanitized_filters[key] = filters[key]
        else:
            sanitized_filters[key.replace("_", "-")] = filters[key]

    try:
        security_groups = connection.describe_security_groups(
            aws_retry=True,
            Filters=ansible_dict_to_boto3_filter_list(sanitized_filters)
        )
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to describe security groups')

    snaked_security_groups = []
    for security_group in security_groups['SecurityGroups']:
        # Modify boto3 tags list to be ansible friendly dict
        # but don't camel case tags
        security_group = camel_dict_to_snake_dict(security_group)
        security_group['tags'] = boto3_tag_list_to_ansible_dict(security_group.get('tags', {}), tag_name_key_name='key', tag_value_key_name='value')
        snaked_security_groups.append(security_group)

    module.exit_json(security_groups=snaked_security_groups)


if __name__ == '__main__':
    main()
