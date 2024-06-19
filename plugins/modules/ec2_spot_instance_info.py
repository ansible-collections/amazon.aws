#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://wwww.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_spot_instance_info
version_added: 2.0.0
short_description: Gather information about ec2 spot instance requests
description:
  - Describes the specified Spot Instance requests.
author:
  - Mandar Vijay Kulkarni (@mandar242)
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
      - Filter names and values are case sensitive.
      - See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeSpotInstanceRequests.html) for possible filters.
    required: false
    default: {}
    type: dict
  spot_instance_request_ids:
    description:
      - One or more Spot Instance request IDs.
    required: false
    type: list
    elements: str
    default: []

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: describe the Spot Instance requests based on request IDs
  amazon.aws.ec2_spot_instance_info:
    spot_instance_request_ids:
      - sir-12345678

- name: describe the Spot Instance requests and filter results based on instance type
  amazon.aws.ec2_spot_instance_info:
    spot_instance_request_ids:
      - sir-12345678
      - sir-13579246
      - sir-87654321
    filters:
      launch.instance-type: t3.medium

- name: describe the Spot requests filtered using multiple filters
  amazon.aws.ec2_spot_instance_info:
    filters:
      state: active
      launch.block-device-mapping.device-name: /dev/sdb
"""

RETURN = r"""
spot_request:
    description: The gathered information about specified spot instance requests.
    returned: when success
    type: list
    elements: dict
    contains:
        create_time:
            description: The date and time when the Spot Instance request was created.
            returned: always
            type: str
        instance_id:
            description: The instance ID, if an instance has been launched to fulfill the Spot Instance request.
            returned: when instance exists
            type: str
        instance_interruption_behavior:
            description: The behavior when a Spot Instance is interruped.
            returned: always
            type: str
        launch_specification:
            description: Additional information for launching instances.
            returned: always
            type: dict
            contains:
                ebs_optimized:
                    description: Indicates whether the instance is optimized for EBS I/O.
                    returned: always
                    type: bool
                image_id:
                    description: The ID of the AMI.
                    returned: always
                    type: str
                instance_type:
                    description: The instance type.
                    returned: always
                    type: str
                key_name:
                    description: The name of the key pair.
                    returned: always
                    type: str
                monitoring:
                    description: Described the monitoring of an instance.
                    returned: always
                    type: dict
                    contains:
                        enabled:
                            description: Indicated whether detailed monitoring is enabled.
                            returned: always
                            type: bool
                placement:
                    description: The placement information for the instance.
                    returned: always
                    type: dict
                    contains:
                        availability_zone:
                            description: The name of the availability zone.
                            returned: always
                            type: str
                security_groups:
                    description: List of security groups.
                    returned: always
                    type: list
                    elements: dict
                    contains:
                        group_id:
                            description: The ID of the security group.
                            returned: always
                            type: str
                        group_name:
                            description: The name of the security group.
                            returned: always
                            type: str
                subnet_id:
                    description: The ID of the subnet.
                    returned: when creating a network interface when launching an instance
                    type: str
        launched_availability_zone:
            description: The availability zone in which the request is launched.
            returned: always
            type: str
        product_description:
            description: The product description associated with the Spot Instance.
            returned: always
            type: str
        spot_instance_request_id:
            description: The ID of the Spot Instance request.
            returned: always
            type: str
        spot_price:
            description: The maximum price per hour that you are willing to pay for a Spot Instance.
            returned: always
            type: str
        state:
            description: The state of the Spot Instance request.
            returned: always
            type: str
        status:
            description: Extra information about the status of the Spot Instance request.
            returned: always
            type: dict
            contains:
                code:
                    description:
                        - The status code.
                        - See https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-request-status.html#spot-instance-request-status-understand for codes.
                    returned: always
                    type: str
                message:
                    description: The description of the status code.
                    returned: always
                    type: str
                update_time:
                    description: The date and time of the most recent status update in UTC format.
                    returned: always
                    type: str
        tags:
            description: List of tags associated with the resource.
            returned: always
            type: list
            elements: dict
            contains:
                key:
                    description: The key of the tag.
                    returned: always
                    type: str
                value:
                    description: The value of the tag.
                    returned: always
                    type: str
        type:
            description: The Spot Instance request type.
            returned: always
            type: str
        valid_until:
            description: The end date of the request in UTC format.
            returned: always
            type: str
    sample: {
        "create_time": "2021-09-01T21:05:57+00:00",
        "instance_id": "i-08877936b801ac475",
        "instance_interruption_behavior": "terminate",
        "launch_specification": {
            "ebs_optimized": false,
            "image_id": "ami-0443305dabd4be2bc",
            "instance_type": "t2.medium",
            "key_name": "zuul",
            "monitoring": {
                "enabled": false
            },
            "placement": {
                "availability_zone": "us-east-2b"
            },
            "security_groups": [
                {
                    "group_id": "sg-01f9833207d53b937",
                    "group_name": "default"
                }
            ],
            "subnet_id": "subnet-07d906b8358869bda"
        },
        "launched_availability_zone": "us-east-2b",
        "product_description": "Linux/UNIX",
        "spot_instance_request_id": "sir-c3cp9jsk",
        "spot_price": "0.046400",
        "state": "active",
        "status": {
            "code": "fulfilled",
            "message": "Your spot request is fulfilled.",
            "update_time": "2021-09-01T21:05:59+00:00"
        },
        "tags": {},
        "type": "one-time",
        "valid_until": "2021-09-08T21:05:57+00:00"
      }
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_spot_instance_requests
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list


def list_spot_instance_requests(connection, module: AnsibleAWSModule) -> None:
    params = {}

    if module.params.get("filters"):
        params["Filters"] = ansible_dict_to_boto3_filter_list(module.params.get("filters"))
    if module.params.get("spot_instance_request_ids"):
        params["SpotInstanceRequestIds"] = module.params.get("spot_instance_request_ids")

    try:
        describe_spot_instance_requests_response = describe_spot_instance_requests(connection, **params)
    except AnsibleEC2Error as e:
        module.fail_json_aws(e, msg="Failed to describe spot instance requests")

    spot_request = []
    for response_list_item in describe_spot_instance_requests_response:
        spot_request.append(camel_dict_to_snake_dict(response_list_item))

    if len(spot_request) == 0:
        module.exit_json(msg="No spot requests found for specified options")

    module.exit_json(spot_request=spot_request)


def main():
    argument_spec = dict(
        filters=dict(default={}, type="dict"),
        spot_instance_request_ids=dict(default=[], type="list", elements="str"),
    )
    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)
    try:
        connection = module.client("ec2")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    list_spot_instance_requests(connection, module)


if __name__ == "__main__":
    main()
