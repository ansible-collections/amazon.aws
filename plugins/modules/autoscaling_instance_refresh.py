#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: autoscaling_instance_refresh
version_added: 3.2.0
version_added_collection: community.aws
short_description: Start or cancel an EC2 Auto Scaling Group (ASG) instance refresh in AWS
description:
  - Start or cancel an EC2 Auto Scaling Group instance refresh in AWS.
  - Can be used with M(amazon.aws.autoscaling_instance_refresh_info) to track the subsequent progress.
  - Prior to release 5.0.0 this module was called M(community.aws.ec2_asg_instance_refresh).
    The usage did not change.
author:
  - "Dan Khersonsky (@danquixote)"
options:
  state:
    description:
      - Desired state of the ASG.
    type: str
    required: true
    choices: [ 'started', 'cancelled' ]
  name:
    description:
      - The name of the auto scaling group you are searching for.
    aliases: ['group_name']
    type: str
    required: true
  strategy:
    description:
      - The strategy to use for the instance refresh. The only valid value is V(Rolling).
      - A rolling update is an update that is applied to all instances in an Auto Scaling group until all instances have been updated.
      - A rolling update can fail due to failed health checks or if instances are on standby or are protected from scale in.
      - If the rolling update process fails, any instances that were already replaced are not rolled back to their previous configuration.
    type: str
    default: 'Rolling'
  preferences:
    description:
      - Set of preferences associated with the instance refresh request.
      - If not provided, the default values are used.
      - For O(preferences.min_healthy_percentage), the default value is V(90).
      - For O(preferences.instance_warmup), the default is to use the value specified for the health check grace period for the Auto Scaling group.
      - Can not be specified when O(state=cancelled).
    required: false
    suboptions:
      min_healthy_percentage:
        description:
          - Total percent of capacity in ASG that must remain healthy during instance refresh to allow operation to continue.
          - It is rounded up to the nearest integer.
          - Value range is V(0) to V(100).
        type: int
        default: 90
      instance_warmup:
        description:
          - The number of seconds until a newly launched instance is configured and ready to use.
          - During this time, Amazon EC2 Auto Scaling does not immediately move on to the next replacement.
          - The default is to use the value for the health check grace period defined for the group.
        type: int
      skip_matching:
        description:
          - Indicates whether skip matching is enabled.
          - If enabled V(true), then Amazon EC2 Auto Scaling skips replacing instances that match the desired configuration.
        type: bool
        version_added: 9.0.0
      max_healthy_percentage:
        description:
          - Specifies the maximum percentage of the group that can be in service and healthy, or pending,
            to support your workload when replacing instances.
          - The value is expressed as a percentage of the desired capacity of the Auto Scaling group.
          - Value range is V(100) to V(200).
          - When specified, you must also specify O(preferences.min_healthy_percentage), and the difference between them cannot be greater than V(100).
        type: int
        version_added: 9.0.0
    type: dict
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Start a refresh
  amazon.aws.autoscaling_instance_refresh:
    name: some-asg
    state: started

- name: Cancel a refresh
  amazon.aws.autoscaling_instance_refresh:
    name: some-asg
    state: cancelled

- name: Start a refresh and pass preferences
  amazon.aws.autoscaling_instance_refresh:
    name: some-asg
    state: started
    preferences:
      min_healthy_percentage: 91
      instance_warmup: 60
      skip_matching: true
"""

RETURN = r"""
instance_refreshes:
    description: Details of the instance refreshes for the Auto Scaling group.
    returned: always
    type: complex
    contains:
        instance_refresh_id:
            description: Instance refresh id.
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
            description: the % of completeness.
            returned: success
            type: int
            sample: 100
        instances_to_update:
            description: number of instances to update.
            returned: success
            type: int
            sample: 5
"""

from typing import Dict
from typing import Optional
from typing import Union

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.autoscaling import AnsibleAutoScalingError
from ansible_collections.amazon.aws.plugins.module_utils.autoscaling import cancel_instance_refresh
from ansible_collections.amazon.aws.plugins.module_utils.autoscaling import describe_instance_refreshes
from ansible_collections.amazon.aws.plugins.module_utils.autoscaling import start_instance_refresh
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters


def validate_healthy_percentage(preferences: Dict[str, Union[bool, int]]) -> Optional[str]:
    min_healthy_percentage = preferences.get("min_healthy_percentage")
    max_healthy_percentage = preferences.get("max_healthy_percentage")

    if min_healthy_percentage is not None and (min_healthy_percentage < 0 or min_healthy_percentage > 100):
        return "The value range for the min_healthy_percentage is 0 to 100."
    if max_healthy_percentage is not None:
        if max_healthy_percentage < 100 or max_healthy_percentage > 200:
            return "The value range for the max_healthy_percentage is 100 to 200."
        if min_healthy_percentage is None:
            return "You must also specify min_healthy_percentage when max_healthy_percentage is specified."
        if (max_healthy_percentage - min_healthy_percentage) > 100:
            return "The difference between the max_healthy_percentage and min_healthy_percentage cannot be greater than 100."
    return None


def start_or_cancel_instance_refresh(conn, module: AnsibleAWSModule) -> None:
    """
    Args:
        conn (boto3.AutoScaling.Client): Valid Boto3 ASG client.
        module: AnsibleAWSModule object
    """

    asg_state = module.params.get("state")
    asg_name = module.params.get("name")
    preferences = module.params.get("preferences")

    args = {}
    if asg_state == "started":
        args["Strategy"] = module.params.get("strategy")
    if preferences:
        if asg_state == "cancelled":
            module.fail_json(msg="can not pass preferences dict when canceling a refresh")
        error = validate_healthy_percentage(preferences)
        if error:
            module.fail_json(msg=error)
        args["Preferences"] = snake_dict_to_camel_dict(scrub_none_parameters(preferences), capitalize_first=True)
    cmd_invocations = {
        "cancelled": cancel_instance_refresh,
        "started": start_instance_refresh,
    }
    try:
        if module.check_mode:
            ongoing_refresh = describe_instance_refreshes(conn, auto_scaling_group_name=asg_name).get(
                "InstanceRefreshes", []
            )
            if asg_state == "started":
                if ongoing_refresh:
                    module.exit_json(
                        changed=False,
                        msg="In check_mode - Instance Refresh is already in progress, can not start new instance refresh.",
                    )
                else:
                    module.exit_json(changed=True, msg="Would have started instance refresh if not in check mode.")
            elif asg_state == "cancelled":
                if ongoing_refresh and ongoing_refresh[0].get("Status", "") in ["Cancelling", "Cancelled"]:
                    module.exit_json(
                        changed=False,
                        msg="In check_mode - Instance Refresh already cancelled or is pending cancellation.",
                    )
                elif not ongoing_refresh:
                    module.exit_json(changed=False, msg="In check_mode - No active referesh found, nothing to cancel.")
                else:
                    module.exit_json(changed=True, msg="Would have cancelled instance refresh if not in check mode.")
        instance_refresh_id = cmd_invocations[asg_state](conn, auto_scaling_group_name=asg_name, **args)
        response = describe_instance_refreshes(
            conn, auto_scaling_group_name=asg_name, instance_refresh_ids=[instance_refresh_id]
        )
        result = dict(instance_refreshes=camel_dict_to_snake_dict(response["InstanceRefreshes"][0]))
        module.exit_json(**result)
    except AnsibleAutoScalingError as e:
        module.fail_json_aws(e, msg=f"Failed to {asg_state.replace('ed', '')} InstanceRefresh: {e}")


def main():
    argument_spec = dict(
        state=dict(
            type="str",
            required=True,
            choices=["started", "cancelled"],
        ),
        name=dict(required=True, aliases=["group_name"]),
        strategy=dict(type="str", default="Rolling", required=False),
        preferences=dict(
            type="dict",
            required=False,
            options=dict(
                min_healthy_percentage=dict(type="int", default=90),
                instance_warmup=dict(type="int"),
                skip_matching=dict(type="bool"),
                max_healthy_percentage=dict(type="int"),
            ),
        ),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    autoscaling = module.client("autoscaling")

    start_or_cancel_instance_refresh(autoscaling, module)


if __name__ == "__main__":
    main()
