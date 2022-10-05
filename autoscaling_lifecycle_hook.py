#!/usr/bin/python

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: autoscaling_lifecycle_hook
version_added: 1.0.0
short_description: Create, delete or update AWS ASG Lifecycle Hooks
description:
  - Will create a new hook when I(state=present) and no given Hook is found.
  - Will update an existing hook when I(state=present) and a Hook is found, but current and provided parameters differ.
  - Will delete the hook when I(state=absent) and a Hook is found.
  - Prior to release 5.0.0 this module was called C(community.aws.ec2_asg_lifecycle_hook).
    The usage did not change.
author:
  - Igor 'Tsigankov' Eyrich (@tsiganenok) <tsiganenok@gmail.com>
options:
  state:
    description:
      - Create or delete Lifecycle Hook.
      - When I(state=present) updates existing hook or creates a new hook if not found.
    choices: ['present', 'absent']
    default: present
    type: str
  lifecycle_hook_name:
    description:
      - The name of the lifecycle hook.
    required: true
    type: str
  autoscaling_group_name:
    description:
      - The name of the Auto Scaling group to which you want to assign the lifecycle hook.
    required: true
    type: str
  transition:
    description:
      - The instance state to which you want to attach the lifecycle hook.
      - Required when I(state=present).
    choices: ['autoscaling:EC2_INSTANCE_TERMINATING', 'autoscaling:EC2_INSTANCE_LAUNCHING']
    type: str
  role_arn:
    description:
      - The ARN of the IAM role that allows the Auto Scaling group to publish to the specified notification target.
    type: str
  notification_target_arn:
    description:
      - The ARN of the notification target that Auto Scaling will use to notify you when an
        instance is in the transition state for the lifecycle hook.
      - This target can be either an SQS queue or an SNS topic.
      - If you specify an empty string, this overrides the current ARN.
    type: str
  notification_meta_data:
    description:
      - Contains additional information that you want to include any time Auto Scaling sends a message to the notification target.
    type: str
  heartbeat_timeout:
    description:
      - The amount of time, in seconds, that can elapse before the lifecycle hook times out.
        When the lifecycle hook times out, Auto Scaling performs the default action.
        You can prevent the lifecycle hook from timing out by calling RecordLifecycleActionHeartbeat.
      - By default Amazon AWS will use C(3600) (1 hour).
    type: int
  default_result:
    description:
      - Defines the action the Auto Scaling group should take when the lifecycle hook timeout
        elapses or if an unexpected failure occurs.
    choices: ['ABANDON', 'CONTINUE']
    default: ABANDON
    type: str
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.boto3
'''

EXAMPLES = '''
- name: Create / Update lifecycle hook
  community.aws.autoscaling_lifecycle_hook:
    region: eu-central-1
    state: present
    autoscaling_group_name: example
    lifecycle_hook_name: example
    transition: autoscaling:EC2_INSTANCE_LAUNCHING
    heartbeat_timeout: 7000
    default_result: ABANDON

- name: Delete lifecycle hook
  community.aws.autoscaling_lifecycle_hook:
    region: eu-central-1
    state: absent
    autoscaling_group_name: example
    lifecycle_hook_name: example
'''

RETURN = '''
---
auto_scaling_group_name:
    description: The unique name of the auto scaling group.
    returned: success
    type: str
    sample: "myasg"
default_result:
    description:  Defines the action the Auto Scaling group should take when the lifecycle hook timeout elapses or if an unexpected failure occurs.
    returned: success
    type: str
    sample: CONTINUE
global_timeout:
    description: The maximum time, in seconds, that an instance can remain in a C(Pending:Wait) or C(Terminating:Wait) state.
    returned: success
    type: int
    sample: 172800
heartbeat_timeout:
    description: The maximum time, in seconds, that can elapse before the lifecycle hook times out.
    returned: success
    type: int
    sample: 3600
lifecycle_hook_name:
    description: The name of the lifecycle hook.
    returned: success
    type: str
    sample: "mylifecyclehook"
lifecycle_transition:
    description: The instance state to which lifecycle hook should be attached.
    returned: success
    type: str
    sample: "autoscaling:EC2_INSTANCE_LAUNCHING"
'''


try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict


def create_lifecycle_hook(connection, module):

    lch_name = module.params.get('lifecycle_hook_name')
    asg_name = module.params.get('autoscaling_group_name')
    transition = module.params.get('transition')
    role_arn = module.params.get('role_arn')
    notification_target_arn = module.params.get('notification_target_arn')
    notification_meta_data = module.params.get('notification_meta_data')
    heartbeat_timeout = module.params.get('heartbeat_timeout')
    default_result = module.params.get('default_result')

    return_object = {}
    return_object['changed'] = False

    lch_params = {
        'LifecycleHookName': lch_name,
        'AutoScalingGroupName': asg_name,
        'LifecycleTransition': transition
    }

    if role_arn:
        lch_params['RoleARN'] = role_arn

    if notification_target_arn:
        lch_params['NotificationTargetARN'] = notification_target_arn

    if notification_meta_data:
        lch_params['NotificationMetadata'] = notification_meta_data

    if heartbeat_timeout:
        lch_params['HeartbeatTimeout'] = heartbeat_timeout

    if default_result:
        lch_params['DefaultResult'] = default_result

    try:
        existing_hook = connection.describe_lifecycle_hooks(
            AutoScalingGroupName=asg_name,
            LifecycleHookNames=[lch_name]
        )['LifecycleHooks']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to get Lifecycle Hook")

    if not existing_hook:
        try:
            if module.check_mode:
                module.exit_json(changed=True, msg="Would have created AutoScalingGroup Lifecycle Hook if not in check_mode.")
            return_object['changed'] = True
            connection.put_lifecycle_hook(**lch_params)
            return_object['lifecycle_hook_info'] = connection.describe_lifecycle_hooks(
                AutoScalingGroupName=asg_name, LifecycleHookNames=[lch_name])['LifecycleHooks']
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to create LifecycleHook")

    else:
        added, removed, modified, same = dict_compare(lch_params, existing_hook[0])
        if modified:
            try:
                if module.check_mode:
                    module.exit_json(changed=True, msg="Would have modified AutoScalingGroup Lifecycle Hook if not in check_mode.")
                return_object['changed'] = True
                connection.put_lifecycle_hook(**lch_params)
                return_object['lifecycle_hook_info'] = connection.describe_lifecycle_hooks(
                    AutoScalingGroupName=asg_name, LifecycleHookNames=[lch_name])['LifecycleHooks']
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Failed to create LifecycleHook")

    module.exit_json(**camel_dict_to_snake_dict(return_object))


def dict_compare(d1, d2):
    d1_keys = set(d1.keys())
    d2_keys = set(d2.keys())
    intersect_keys = d1_keys.intersection(d2_keys)
    added = d1_keys - d2_keys
    removed = d2_keys - d1_keys
    modified = False
    for key in d1:
        if d1[key] != d2[key]:
            modified = True
            break

    same = set(o for o in intersect_keys if d1[o] == d2[o])
    return added, removed, modified, same


def delete_lifecycle_hook(connection, module):

    lch_name = module.params.get('lifecycle_hook_name')
    asg_name = module.params.get('autoscaling_group_name')

    return_object = {}
    return_object['changed'] = False

    try:
        all_hooks = connection.describe_lifecycle_hooks(
            AutoScalingGroupName=asg_name
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to get Lifecycle Hooks")

    for hook in all_hooks['LifecycleHooks']:
        if hook['LifecycleHookName'] == lch_name:
            lch_params = {
                'LifecycleHookName': lch_name,
                'AutoScalingGroupName': asg_name
            }

            try:
                if module.check_mode:
                    module.exit_json(changed=True, msg="Would have deleted AutoScalingGroup Lifecycle Hook if not in check_mode.")
                connection.delete_lifecycle_hook(**lch_params)
                return_object['changed'] = True
                return_object['lifecycle_hook_removed'] = {'LifecycleHookName': lch_name, 'AutoScalingGroupName': asg_name}
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Failed to delete LifecycleHook")
        else:
            pass

    module.exit_json(**camel_dict_to_snake_dict(return_object))


def main():
    argument_spec = dict(
        autoscaling_group_name=dict(required=True, type='str'),
        lifecycle_hook_name=dict(required=True, type='str'),
        transition=dict(type='str', choices=['autoscaling:EC2_INSTANCE_TERMINATING', 'autoscaling:EC2_INSTANCE_LAUNCHING']),
        role_arn=dict(type='str'),
        notification_target_arn=dict(type='str'),
        notification_meta_data=dict(type='str'),
        heartbeat_timeout=dict(type='int'),
        default_result=dict(default='ABANDON', choices=['ABANDON', 'CONTINUE']),
        state=dict(default='present', choices=['present', 'absent'])
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[['state', 'present', ['transition']]],
    )

    state = module.params.get('state')

    connection = module.client('autoscaling')

    changed = False

    if state == 'present':
        create_lifecycle_hook(connection, module)
    elif state == 'absent':
        delete_lifecycle_hook(connection, module)


if __name__ == '__main__':
    main()
