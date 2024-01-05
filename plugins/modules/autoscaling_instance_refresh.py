#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: autoscaling_instance_refresh
version_added: 3.2.0
short_description: Start or cancel an EC2 Auto Scaling Group (ASG) instance refresh in AWS
description:
  - Start or cancel an EC2 Auto Scaling Group instance refresh in AWS.
  - Can be used with M(community.aws.autoscaling_instance_refresh_info) to track the subsequent progress.
  - Prior to release 5.0.0 this module was called C(community.aws.ec2_asg_instance_refresh).
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
    type: str
    required: true
  strategy:
    description:
      - The strategy to use for the instance refresh. The only valid value is C(Rolling).
      - A rolling update is an update that is applied to all instances in an Auto Scaling group until all instances have been updated.
      - A rolling update can fail due to failed health checks or if instances are on standby or are protected from scale in.
      - If the rolling update process fails, any instances that were already replaced are not rolled back to their previous configuration.
    type: str
    default: 'Rolling'
  preferences:
    description:
      - Set of preferences associated with the instance refresh request.
      - If not provided, the default values are used.
      - For I(min_healthy_percentage), the default value is C(90).
      - For I(instance_warmup), the default is to use the value specified for the health check grace period for the Auto Scaling group.
      - Can not be specified when I(state) is set to 'cancelled'.
    required: false
    suboptions:
      min_healthy_percentage:
        description:
          - Total percent of capacity in ASG that must remain healthy during instance refresh to allow operation to continue.
          - It is rounded up to the nearest integer.
        type: int
        default: 90
      instance_warmup:
        description:
          - The number of seconds until a newly launched instance is configured and ready to use.
          - During this time, Amazon EC2 Auto Scaling does not immediately move on to the next replacement.
          - The default is to use the value for the health check grace period defined for the group.
        type: int
    type: dict
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Start a refresh
  community.aws.autoscaling_instance_refresh:
    name: some-asg
    state: started

- name: Cancel a refresh
  community.aws.autoscaling_instance_refresh:
    name: some-asg
    state: cancelled

- name: Start a refresh and pass preferences
  community.aws.autoscaling_instance_refresh:
    name: some-asg
    state: started
    preferences:
      min_healthy_percentage: 91
      instance_warmup: 60
"""

RETURN = r"""
---
instance_refresh_id:
    description: instance refresh id
    returned: success
    type: str
    sample: "08b91cf7-8fa6-48af-b6a6-d227f40f1b9b"
auto_scaling_group_name:
    description: Name of autoscaling group
    returned: success
    type: str
    sample: "public-webapp-production-1"
status:
    description:
      -  The current state of the group when DeleteAutoScalingGroup is in progress.
      -  The following are the possible statuses
      -    Pending --  The request was created, but the operation has not started.
      -    InProgress --  The operation is in progress.
      -    Successful --  The operation completed successfully.
      -    Failed --  The operation failed to complete. You can troubleshoot using the status reason and the scaling activities.
      -    Cancelling --
      -        An ongoing operation is being cancelled.
      -        Cancellation does not roll back any replacements that have already been completed,
      -        but it prevents new replacements from being started.
      -    Cancelled --  The operation is cancelled.
    returned: success
    type: str
    sample: "Pending"
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
    description: num. of instance to update
    returned: success
    type: int
    sample: 5
"""

try:
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def start_or_cancel_instance_refresh(conn, module):
    """
    Args:
        conn (boto3.AutoScaling.Client): Valid Boto3 ASG client.
        module: AnsibleAWSModule object

    Returns:
        {
            "instance_refreshes": [
                    {
                        'auto_scaling_group_name': 'ansible-test-hermes-63642726-asg',
                        'instance_refresh_id': '6507a3e5-4950-4503-8978-e9f2636efc09',
                        'instances_to_update': 1,
                        'percentage_complete': 0,
                        "preferences": {
                            "instance_warmup": 60,
                            "min_healthy_percentage": 90,
                            "skip_matching": false
                        },
                        'start_time': '2021-02-04T03:39:40+00:00',
                        'status': 'Cancelling',
                        'status_reason': 'Replacing instances before cancelling.',
                    }
              ]
        }
    """

    asg_state = module.params.get("state")
    asg_name = module.params.get("name")
    preferences = module.params.get("preferences")

    args = {}
    args["AutoScalingGroupName"] = asg_name
    if asg_state == "started":
        args["Strategy"] = module.params.get("strategy")
    if preferences:
        if asg_state == "cancelled":
            module.fail_json(msg="can not pass preferences dict when canceling a refresh")
        _prefs = scrub_none_parameters(preferences)
        args["Preferences"] = snake_dict_to_camel_dict(_prefs, capitalize_first=True)
    cmd_invocations = {
        "cancelled": conn.cancel_instance_refresh,
        "started": conn.start_instance_refresh,
    }
    try:
        if module.check_mode:
            if asg_state == "started":
                ongoing_refresh = conn.describe_instance_refreshes(AutoScalingGroupName=asg_name).get(
                    "InstanceRefreshes", "[]"
                )
                if ongoing_refresh:
                    module.exit_json(
                        changed=False,
                        msg="In check_mode - Instance Refresh is already in progress, can not start new instance refresh.",
                    )
                else:
                    module.exit_json(changed=True, msg="Would have started instance refresh if not in check mode.")
            elif asg_state == "cancelled":
                ongoing_refresh = conn.describe_instance_refreshes(AutoScalingGroupName=asg_name).get(
                    "InstanceRefreshes", "[]"
                )[0]
                if ongoing_refresh.get("Status", "") in ["Cancelling", "Cancelled"]:
                    module.exit_json(
                        changed=False,
                        msg="In check_mode - Instance Refresh already cancelled or is pending cancellation.",
                    )
                elif not ongoing_refresh:
                    module.exit_json(chaned=False, msg="In check_mode - No active referesh found, nothing to cancel.")
                else:
                    module.exit_json(changed=True, msg="Would have cancelled instance refresh if not in check mode.")
        result = cmd_invocations[asg_state](aws_retry=True, **args)
        instance_refreshes = conn.describe_instance_refreshes(
            AutoScalingGroupName=asg_name, InstanceRefreshIds=[result["InstanceRefreshId"]]
        )
        result = dict(instance_refreshes=camel_dict_to_snake_dict(instance_refreshes["InstanceRefreshes"][0]))
        return module.exit_json(**result)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg=f"Failed to {asg_state.replace('ed', '')} InstanceRefresh")


def main():
    argument_spec = dict(
        state=dict(
            type="str",
            required=True,
            choices=["started", "cancelled"],
        ),
        name=dict(required=True),
        strategy=dict(type="str", default="Rolling", required=False),
        preferences=dict(
            type="dict",
            required=False,
            options=dict(
                min_healthy_percentage=dict(type="int", default=90),
                instance_warmup=dict(type="int"),
            ),
        ),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    autoscaling = module.client(
        "autoscaling",
        retry_decorator=AWSRetry.jittered_backoff(retries=10, catch_extra_error_codes=["InstanceRefreshInProgress"]),
    )

    start_or_cancel_instance_refresh(autoscaling, module)


if __name__ == "__main__":
    main()
