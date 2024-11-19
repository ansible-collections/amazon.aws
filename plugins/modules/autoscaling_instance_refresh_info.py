#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: autoscaling_instance_refresh_info
version_added: 3.2.0
version_added_collection: community.aws
short_description: Gather information about EC2 Auto Scaling Group (ASG) Instance Refreshes in AWS
description:
  - Describes one or more instance refreshes.
  - You can determine the status of a request by looking at the RV(instance_refreshes.status) return value.
  - Prior to release 5.0.0 this module was called M(community.aws.ec2_asg_instance_refresh_info).
    The usage did not change.
author:
  - "Dan Khersonsky (@danquixote)"
options:
  name:
    description:
      - The name of the Auto Scaling group.
    type: str
    required: true
    aliases: ["group_name"]
  ids:
    description:
      - One or more instance refresh IDs.
    type: list
    elements: str
    default: []
  next_token:
    description:
      - The token for the next set of items to return. (You received this token from a previous call.)
    type: str
  max_records:
    description:
      - The maximum number of items to return with this call. The default value is V(50) and the maximum value is V(100).
    type: int
    required: false
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Find an refresh by ASG name
  amazon.aws.autoscaling_instance_refresh_info:
    name: somename-asg

- name: Find an refresh by ASG name and one or more refresh-IDs
  amazon.aws.autoscaling_instance_refresh_info:
    name: somename-asg
    ids: ['some-id-123']
  register: asgs

- name: Find an refresh by ASG name and set max_records
  amazon.aws.autoscaling_instance_refresh_info:
    name: somename-asg
    max_records: 4
  register: asgs

- name: Find an refresh by ASG name and NextToken, if received from a previous call
  amazon.aws.autoscaling_instance_refresh_info:
    name: somename-asg
    next_token: 'some-token-123'
  register: asgs
"""

RETURN = r"""
next_token:
  description: A string that indicates that the response contains more items than can be returned in a single response.
  returned: always
  type: str
instance_refreshes:
    description: A list of instance refreshes.
    returned: always
    type: complex
    contains:
        instance_refresh_id:
            description: instance refresh id.
            returned: success
            type: str
            sample: "08b91cf7-8fa6-48af-b6a6-d227f40f1b9b"
        auto_scaling_group_name:
            description: Name of autoscaling group.
            returned: success
            type: str
            sample: "public-webapp-production-1"
        status:
            description:
              - The current state of the group when DeleteAutoScalingGroup is in progress.
              - The following are the possible statuses
              - Pending - The request was created, but the operation has not started.
              - InProgress - The operation is in progress.
              - Successful - The operation completed successfully.
              - Failed - The operation failed to complete.
                You can troubleshoot using the status reason and the scaling activities.
              - Cancelling - An ongoing operation is being cancelled.
                Cancellation does not roll back any replacements that have already been
                completed, but it prevents new replacements from being started.
              - Cancelled - The operation is cancelled.
            returned: success
            type: str
            sample: "Pending"
        preferences:
            description: The preferences for an instance refresh.
            returned: always
            type: dict
            sample: {
                'AlarmSpecification': {
                    'Alarms': [
                        'my-alarm',
                    ],
                },
                'AutoRollback': True,
                'InstanceWarmup': 200,
                'MinHealthyPercentage': 90,
                'ScaleInProtectedInstances': 'Ignore',
                'SkipMatching': False,
                'StandbyInstances': 'Ignore',
            }
        start_time:
            description: The date and time this ASG was created, in ISO 8601 format.
            returned: success
            type: str
            sample: "2015-11-25T00:05:36.309Z"
        end_time:
            description: The date and time this ASG was created, in ISO 8601 format.
            returned: success
            type: str
            sample: "2015-11-25T00:05:36.309Z"
        percentage_complete:
            description: the % of completeness
            returned: success
            type: int
            sample: 100
        instances_to_update:
            description: number of instances to update.
            returned: success
            type: int
            sample: 5
"""

from typing import Any
from typing import Dict

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.autoscaling import AnsibleAutoScalingError
from ansible_collections.amazon.aws.plugins.module_utils.autoscaling import describe_instance_refreshes
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule


def format_response(response: Dict[str, Any]) -> Dict[str, Any]:
    result = {}
    if "InstanceRefreshes" in response:
        instance_refreshes_dict = {
            "instance_refreshes": response["InstanceRefreshes"],
            "next_token": response.get("NextToken", ""),
        }
        result = camel_dict_to_snake_dict(instance_refreshes_dict)
    return result


def find_asg_instance_refreshes(client, module: AnsibleAWSModule) -> None:
    """
    Args:
        client (boto3.AutoScaling.Client): Valid Boto3 ASG client.
        module: AnsibleAWSModule object
    """

    try:
        max_records = module.params.get("max_records")
        response = describe_instance_refreshes(
            client,
            auto_scaling_group_name=module.params.get("name"),
            instance_refresh_ids=module.params.get("ids"),
            next_token=module.params.get("next_token"),
            max_records=max_records,
        )
        instance_refreshes_result = format_response(response)

        if max_records is None:
            while "NextToken" in response:
                response = describe_instance_refreshes(
                    client,
                    auto_scaling_group_name=module.params.get("name"),
                    instance_refresh_ids=module.params.get("ids"),
                    next_token=response["NextToken"],
                    max_records=max_records,
                )
                f_response = format_response(response)
                if "instance_refreshes" in f_response:
                    instance_refreshes_result["instance_refreshes"].extend(f_response["instance_refreshes"])
                    instance_refreshes_result["next_token"] = f_response["next_token"]

        module.exit_json(changed=False, **instance_refreshes_result)
    except AnsibleAutoScalingError as e:
        module.fail_json_aws(e, msg=f"Failed to describe InstanceRefreshes: {e}")


def main():
    argument_spec = dict(
        name=dict(required=True, type="str", aliases=["group_name"]),
        ids=dict(required=False, default=[], elements="str", type="list"),
        next_token=dict(required=False, default=None, type="str", no_log=True),
        max_records=dict(required=False, type="int"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    autoscaling = module.client("autoscaling")
    find_asg_instance_refreshes(autoscaling, module)


if __name__ == "__main__":
    main()
