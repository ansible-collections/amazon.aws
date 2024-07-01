#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: aws_region_info
short_description: Gather information about AWS regions
version_added: 1.0.0
version_added_collection: community.aws
description:
  - Gather information about AWS regions.
author:
  - 'Henrique Rodrigues (@Sodki)'
options:
  filters:
    description:
      - A dict of filters to apply.
      - Each dict item consists of a filter key and a filter value.
      - See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeRegions.html) for possible filters.
      - Filter names and values are case sensitive.
      - You can use underscores instead of dashes (-) in the filter keys.
      - Filter keys with underscores will take precedence in case of conflict.
    default: {}
    type: dict
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather information about all regions
- amazon.aws.aws_region_info:

# Gather information about a single region
- amazon.aws.aws_region_info:
    filters:
      region-name: eu-west-1
"""

RETURN = r"""
regions:
    returned: on success
    description:
        - Information about the regions that match the provided filters. Retruns information about all the regions if no filters specified.
        - Each element consists of a dict with all the information related to that region.
    type: list
    elements: dict
    sample: "[{
        'endpoint': 'ec2.us-west-1.amazonaws.com',
        'region_name': 'us-west-1'
    }]"
    contains:
        endpoint:
            description: The Region service endpoint.
            type: str
            sample: "ec2.us-east-2.amazonaws.com"
        opt_in_status:
            description: The Region opt-in status.
            type: str
            sample: "opt-in-not-required"
        region_name:
            description: The name of the Region.
            type: str
            sample: "us-east-2"
"""

try:
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_regions
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.transformation import sanitize_filters_to_boto3_filter_list


def main():
    argument_spec = dict(
        filters=dict(default={}, type="dict"),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client("ec2")

    # Sanitize filters
    sanitized_filters = sanitize_filters_to_boto3_filter_list(module.params.get("filters"))
    try:
        regions = describe_regions(connection, Filters=sanitized_filters)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Unable to describe regions.")

    module.exit_json(regions=[camel_dict_to_snake_dict(r) for r in regions])


if __name__ == "__main__":
    main()
