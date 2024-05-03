#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_security_group_info
version_added: 1.0.0
short_description: Gather information about EC2 security groups in AWS
description:
    - Gather information about EC2 security groups in AWS.
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
  - By default, the module will return all security groups in a region. To limit results use the
    appropriate filters.
  - Prior to release 5.0.0 this module was called C(amazon.aws.ec2_group_info). The usage did not
    change.

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather information about all security groups
- amazon.aws.ec2_security_group_info:

# Gather information about all security groups in a specific VPC
- amazon.aws.ec2_security_group_info:
    filters:
      vpc-id: vpc-12345678

# Gather information about all security groups in a specific VPC
- amazon.aws.ec2_security_group_info:
    filters:
      vpc-id: vpc-12345678

# Gather information about a security group
- amazon.aws.ec2_security_group_info:
    filters:
      group-name: example-1

# Gather information about a security group by id
- amazon.aws.ec2_security_group_info:
    filters:
      group-id: sg-12345678

# Gather information about a security group with multiple filters, also mixing the use of underscores as filter keys
- amazon.aws.ec2_security_group_info:
    filters:
      group_id: sg-12345678
      vpc-id: vpc-12345678

# Gather information about various security groups
- amazon.aws.ec2_security_group_info:
    filters:
      group-name:
        - example-1
        - example-2
        - example-3

# Gather information about any security group with a tag key Name and value Example.
# The quotes around 'tag:name' are important because of the colon in the value
- amazon.aws.ec2_security_group_info:
    filters:
      "tag:Name": Example
"""

RETURN = r"""
security_groups:
    description: Security groups that match the provided filters. Each element consists of a dict with all the information related to that security group.
    type: list
    returned: always
    elements: dict
    contains:
        description:
            description: The description of the security group.
            returned: always
            type: str
        group_id:
            description: The ID of the security group.
            returned: always
            type: str
        group_name:
            description: The name of the security group.
            returned: always
            type: str
        ip_permissions:
            description: The inbound rules associated with the security group.
            returned: always
            type: list
            elements: dict
            contains:
                from_port:
                    description: If the protocol is TCP or UDP, this is the start of the port range.
                    type: int
                    sample: 80
                ip_protocol:
                    description: The IP protocol name or number.
                    returned: always
                    type: str
                ip_ranges:
                    description: The IPv4 ranges.
                    returned: always
                    type: list
                    elements: dict
                    contains:
                        cidr_ip:
                            description: The IPv4 CIDR range.
                            returned: always
                            type: str
                ipv6_ranges:
                    description: The IPv6 ranges.
                    returned: always
                    type: list
                    elements: dict
                    contains:
                        cidr_ipv6:
                            description: The IPv6 CIDR range.
                            returned: always
                            type: str
                prefix_list_ids:
                    description: The prefix list IDs.
                    returned: always
                    type: list
                    elements: dict
                    contains:
                        prefix_list_id:
                            description: The ID of the prefix.
                            returned: always
                            type: str
                to_group:
                    description: If the protocol is TCP or UDP, this is the end of the port range.
                    type: int
                    sample: 80
                user_id_group_pairs:
                    description: The security group and AWS account ID pairs.
                    returned: always
                    type: list
                    elements: dict
                    contains:
                        group_id:
                            description: The security group ID of the pair.
                            returned: always
                            type: str
                        user_id:
                            description: The user ID of the pair.
                            returned: always
                            type: str
        ip_permissions_egress:
            description: The outbound rules associated with the security group.
            returned: always
            type: list
            elements: dict
            contains:
                ip_protocol:
                    description: The IP protocol name or number.
                    returned: always
                    type: str
                ip_ranges:
                    description: The IPv4 ranges.
                    returned: always
                    type: list
                    elements: dict
                    contains:
                        cidr_ip:
                            description: The IPv4 CIDR range.
                            returned: always
                            type: str
                ipv6_ranges:
                    description: The IPv6 ranges.
                    returned: always
                    type: list
                    elements: dict
                    contains:
                        cidr_ipv6:
                            description: The IPv6 CIDR range.
                            returned: always
                            type: str
                prefix_list_ids:
                    description: The prefix list IDs.
                    returned: always
                    type: list
                    elements: dict
                    contains:
                        prefix_list_id:
                            description: The ID of the prefix.
                            returned: always
                            type: str
                user_id_group_pairs:
                    description: The security group and AWS account ID pairs.
                    returned: always
                    type: list
                    elements: dict
                    contains:
                        group_id:
                            description: The security group ID of the pair.
                            returned: always
                            type: str
                        user_id:
                            description: The user ID of the pair.
                            returned: always
                            type: str
        owner_id:
            description: The AWS account ID of the owner of the security group.
            returned: always
            type: str
        tags:
            description: The tags associated with the security group.
            returned: always
            type: dict
        vpc_id:
            description: The ID of the VPC for the security group.
            returned: always
            type: str
    sample: [
        {
            "description": "created by rds_instance integration tests",
            "group_id": "sg-036496a610b79da88",
            "group_name": "ansible-test-89355088-unknown5c5f67f3ad09-sg-1",
            "ip_permissions": [],
            "ip_permissions_egress": [
                {
                    "ip_protocol": "-1",
                    "ip_ranges": [
                        {
                            "cidr_ip": "0.0.0.0/0"
                        }
                    ],
                    "ipv6_ranges": [],
                    "prefix_list_ids": [],
                    "user_id_group_pairs": []
                }
            ],
            "owner_id": "123456789012",
            "tags": {},
            "vpc_id": "vpc-0bc3bb03f97405435"
        }
    ]
"""

try:
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


def main():
    argument_spec = dict(filters=dict(default={}, type="dict"))

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client("ec2", AWSRetry.jittered_backoff())

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
            aws_retry=True, Filters=ansible_dict_to_boto3_filter_list(sanitized_filters)
        )
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to describe security groups")

    snaked_security_groups = []
    for security_group in security_groups["SecurityGroups"]:
        # Modify boto3 tags list to be ansible friendly dict
        # but don't camel case tags
        security_group = camel_dict_to_snake_dict(security_group)
        security_group["tags"] = boto3_tag_list_to_ansible_dict(
            security_group.get("tags", {}), tag_name_key_name="key", tag_value_key_name="value"
        )
        snaked_security_groups.append(security_group)

    module.exit_json(security_groups=snaked_security_groups)


if __name__ == "__main__":
    main()
