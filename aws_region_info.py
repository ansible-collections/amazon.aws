#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: aws_region_info
short_description: Gather information about AWS regions
version_added: 1.0.0
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
- community.aws.aws_region_info:

# Gather information about a single region
- community.aws.aws_region_info:
    filters:
      region-name: eu-west-1
"""

RETURN = r"""
regions:
    returned: on success
    description: >
        Regions that match the provided filters. Each element consists of a dict with all the information related
        to that region.
    type: list
    sample: "[{
        'endpoint': 'ec2.us-west-1.amazonaws.com',
        'region_name': 'us-west-1'
    }]"
"""

try:
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def main():
    argument_spec = dict(
        filters=dict(default={}, type="dict"),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client("ec2", retry_decorator=AWSRetry.jittered_backoff())

    # Replace filter key underscores with dashes, for compatibility
    sanitized_filters = dict(module.params.get("filters"))
    for k in module.params.get("filters").keys():
        if "_" in k:
            sanitized_filters[k.replace("_", "-")] = sanitized_filters[k]
            del sanitized_filters[k]

    try:
        regions = connection.describe_regions(
            aws_retry=True, Filters=ansible_dict_to_boto3_filter_list(sanitized_filters)
        )
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Unable to describe regions.")

    module.exit_json(regions=[camel_dict_to_snake_dict(r) for r in regions["Regions"]])


if __name__ == "__main__":
    main()
