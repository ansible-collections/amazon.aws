#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: aws_az_info
short_description: Gather information about availability zones in AWS
version_added: 1.0.0
description:
    - Gather information about availability zones in AWS.
author: 'Henrique Rodrigues (@Sodki)'
options:
  filters:
    description:
      - A dict of filters to apply.
      - Each dict item consists of a filter key and a filter value.
      - See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeAvailabilityZones.html) for possible filters.
      - Filter names and values are case sensitive.
      - You can use underscores instead of dashes (-) in the filter keys.
      - Filter keys with underscores will take precedence in case of conflict.
    required: false
    default: {}
    type: dict
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather information about all availability zones
  amazon.aws.aws_az_info:

- name: Gather information about a single availability zone
  amazon.aws.aws_az_info:
    filters:
      zone-name: eu-west-1a
"""

RETURN = r"""
availability_zones:
    returned: on success
    description: >
        Availability zones that match the provided filters. Each element consists of a dict with all the information
        related to that available zone.
    type: list
    elements: dict
    contains:
        state:
            description:
                - The state of the availability zone.
                - The value is always C(available).
            type: str
            returned: on success
            sample: 'available'
        opt_in_status:
            description:
                - The opt-in status.
                - The value is always C(opt-in-not-required) for availability zones.
            type: str
            returned: on success
            sample: 'opt-in-not-required'
        messages:
            description: List of messages about the availability zone.
            type: list
            elements: dict
            contains:
                message:
                    description: The message about the availability zone.
                    type: str
                    returned: on success
                    sample: 'msg'
            returned: on success
            sample: [
                {
                    'message': 'message_one'
                },
                {
                    'message': 'message_two'
                }
            ]
        region_name:
            description: The name of the region.
            type: str
            returned: on success
            sample: 'us-east-1'
        zone_name:
            description: The name of the availability zone.
            type: str
            returned: on success
            sample: 'us-east-1e'
        zone_id:
            description: The ID of the availability zone.
            type: str
            returned: on success
            sample: 'use1-az5'
        group_name:
            description:
                - The name of the associated group.
                - For availability zones, this will be the same as I(region_name).
            type: str
            returned: on success
            sample: 'us-east-1'
        network_border_group:
            description: The name of the network border group.
            type: str
            returned: on success
            sample: 'us-east-1'
        zone_type:
            description: The type of zone.
            type: str
            returned: on success
            sample: 'availability-zone'
    sample: [
        {
            "group_name": "us-east-1",
            "messages": [],
            "network_border_group": "us-east-1",
            "opt_in_status": "opt-in-not-required",
            "region_name": "us-east-1",
            "state": "available",
            "zone_id": "use1-az6",
            "zone_name": "us-east-1a",
            "zone_type": "availability-zone"
        },
        {
            "group_name": "us-east-1",
            "messages": [],
            "network_border_group": "us-east-1",
            "opt_in_status": "opt-in-not-required",
            "region_name": "us-east-1",
            "state": "available",
            "zone_id": "use1-az1",
            "zone_name": "us-east-1b",
            "zone_type": "availability-zone"
        }
    ]
"""

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


def main():
    argument_spec = dict(filters=dict(default={}, type="dict"))

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    connection = module.client("ec2", retry_decorator=AWSRetry.jittered_backoff())

    # Replace filter key underscores with dashes, for compatibility
    sanitized_filters = dict(module.params.get("filters"))
    for k in module.params.get("filters").keys():
        if "_" in k:
            sanitized_filters[k.replace("_", "-")] = sanitized_filters[k]
            del sanitized_filters[k]

    try:
        availability_zones = connection.describe_availability_zones(
            aws_retry=True, Filters=ansible_dict_to_boto3_filter_list(sanitized_filters)
        )
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Unable to describe availability zones.")

    # Turn the boto3 result into ansible_friendly_snaked_names
    snaked_availability_zones = [camel_dict_to_snake_dict(az) for az in availability_zones["AvailabilityZones"]]

    module.exit_json(availability_zones=snaked_availability_zones)


if __name__ == "__main__":
    main()
