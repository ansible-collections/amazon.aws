#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: autoscaling_complete_lifecycle_action
short_description: Completes the lifecycle action of an instance
description:
  - Used to complete the lifecycle action for the specified instance with the specified result.
version_added: "4.1.0"
author:
  - Saleh Abbas (@salehabbas) <saleh.abbas@thetradedesk.com>
options:
  asg_name:
    description:
      - The name of the Auto Scaling Group which the instance belongs to.
    type: str
    required: true
  lifecycle_hook_name:
    description:
      - The name of the lifecycle hook to complete.
    type: str
    required: true
  lifecycle_action_result:
    description:
      - The action for the lifecycle hook to take.
    choices: ['CONTINUE', 'ABANDON']
    type: str
    required: true
  instance_id:
    description:
      - The ID of the instance.
    type: str
    required: true
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.
# Complete the lifecycle action
- aws_asg_complete_lifecycle_action:
    asg_name: my-auto-scaling-group
    lifecycle_hook_name: my-lifecycle-hook
    lifecycle_action_result: CONTINUE
    instance_id: i-123knm1l2312
"""

RETURN = r"""
---
status:
    description: How things went
    returned: success
    type: str
    sample: ["OK"]
"""

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def main():
    argument_spec = dict(
        asg_name=dict(required=True, type="str"),
        lifecycle_hook_name=dict(required=True, type="str"),
        lifecycle_action_result=dict(required=True, type="str", choices=["CONTINUE", "ABANDON"]),
        instance_id=dict(required=True, type="str"),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec)

    asg_name = module.params.get("asg_name")
    lifecycle_hook_name = module.params.get("lifecycle_hook_name")
    lifecycle_action_result = module.params.get("lifecycle_action_result")
    instance_id = module.params.get("instance_id")

    autoscaling = module.client("autoscaling")
    try:
        results = autoscaling.complete_lifecycle_action(
            LifecycleHookName=lifecycle_hook_name,
            AutoScalingGroupName=asg_name,
            LifecycleActionResult=lifecycle_action_result,
            InstanceId=instance_id,
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to completes the lifecycle action")

    module.exit_json(results=results)


if __name__ == "__main__":
    main()
