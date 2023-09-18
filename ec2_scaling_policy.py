#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
module: ec2_scaling_policy
short_description: Create or delete AWS scaling policies for Autoscaling groups
version_added: 1.0.0
description:
  - Can create or delete scaling policies for autoscaling groups.
  - Referenced autoscaling groups must already exist.
author: "Zacharie Eakin (@Zeekin)"
options:
  state:
    description:
      - Register or deregister the policy.
    default: present
    choices: ['present', 'absent']
    type: str
  name:
    description:
      - Unique name for the scaling policy.
    required: true
    type: str
  asg_name:
    description:
      - Name of the associated autoscaling group.
    required: true
    type: str
  adjustment_type:
    description:
      - The type of change in capacity of the autoscaling group.
    choices: ['ChangeInCapacity','ExactCapacity','PercentChangeInCapacity']
    type: str
  scaling_adjustment:
    description:
      - The amount by which the autoscaling group is adjusted by the policy.
    type: int
  min_adjustment_step:
    description:
      - Minimum amount of adjustment when policy is triggered.
    type: int
  cooldown:
    description:
      - The minimum period of time (in seconds) between which autoscaling actions can take place.
    type: int
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
- community.aws.ec2_scaling_policy:
    state: present
    region: US-XXX
    name: "scaledown-policy"
    adjustment_type: "ChangeInCapacity"
    asg_name: "slave-pool"
    scaling_adjustment: -1
    min_adjustment_step: 1
    cooldown: 300
'''

try:
    import boto.ec2.autoscale
    import boto.exception
    from boto.ec2.autoscale import ScalingPolicy
    from boto.exception import BotoServerError
except ImportError:
    pass  # Taken care of by ec2.HAS_BOTO

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import HAS_BOTO
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import connect_to_aws
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import get_aws_connection_info


def create_scaling_policy(connection, module):
    sp_name = module.params.get('name')
    adjustment_type = module.params.get('adjustment_type')
    asg_name = module.params.get('asg_name')
    scaling_adjustment = module.params.get('scaling_adjustment')
    min_adjustment_step = module.params.get('min_adjustment_step')
    cooldown = module.params.get('cooldown')

    scalingPolicies = connection.get_all_policies(as_group=asg_name, policy_names=[sp_name])

    if not scalingPolicies:
        sp = ScalingPolicy(
            name=sp_name,
            adjustment_type=adjustment_type,
            as_name=asg_name,
            scaling_adjustment=scaling_adjustment,
            min_adjustment_step=min_adjustment_step,
            cooldown=cooldown)

        try:
            connection.create_scaling_policy(sp)
            policy = connection.get_all_policies(as_group=asg_name, policy_names=[sp_name])[0]
            module.exit_json(changed=True, name=policy.name, arn=policy.policy_arn, as_name=policy.as_name, scaling_adjustment=policy.scaling_adjustment,
                             cooldown=policy.cooldown, adjustment_type=policy.adjustment_type, min_adjustment_step=policy.min_adjustment_step)
        except BotoServerError as e:
            module.fail_json(msg=str(e))
    else:
        policy = scalingPolicies[0]
        changed = False

        # min_adjustment_step attribute is only relevant if the adjustment_type
        # is set to percentage change in capacity, so it is a special case
        if getattr(policy, 'adjustment_type') == 'PercentChangeInCapacity':
            if getattr(policy, 'min_adjustment_step') != module.params.get('min_adjustment_step'):
                changed = True

        # set the min adjustment step in case the user decided to change their
        # adjustment type to percentage
        setattr(policy, 'min_adjustment_step', module.params.get('min_adjustment_step'))

        # check the remaining attributes
        for attr in ('adjustment_type', 'scaling_adjustment', 'cooldown'):
            if getattr(policy, attr) != module.params.get(attr):
                changed = True
                setattr(policy, attr, module.params.get(attr))

        try:
            if changed:
                connection.create_scaling_policy(policy)
                policy = connection.get_all_policies(as_group=asg_name, policy_names=[sp_name])[0]
            module.exit_json(changed=changed, name=policy.name, arn=policy.policy_arn, as_name=policy.as_name, scaling_adjustment=policy.scaling_adjustment,
                             cooldown=policy.cooldown, adjustment_type=policy.adjustment_type, min_adjustment_step=policy.min_adjustment_step)
        except BotoServerError as e:
            module.fail_json(msg=str(e))


def delete_scaling_policy(connection, module):
    sp_name = module.params.get('name')
    asg_name = module.params.get('asg_name')

    scalingPolicies = connection.get_all_policies(as_group=asg_name, policy_names=[sp_name])

    if scalingPolicies:
        try:
            connection.delete_policy(sp_name, asg_name)
            module.exit_json(changed=True)
        except BotoServerError as e:
            module.exit_json(changed=False, msg=str(e))
    else:
        module.exit_json(changed=False)


def main():
    argument_spec = dict(
        name=dict(required=True, type='str'),
        adjustment_type=dict(type='str', choices=['ChangeInCapacity', 'ExactCapacity', 'PercentChangeInCapacity']),
        asg_name=dict(required=True, type='str'),
        scaling_adjustment=dict(type='int'),
        min_adjustment_step=dict(type='int'),
        cooldown=dict(type='int'),
        state=dict(default='present', choices=['present', 'absent']),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, check_boto3=False)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    state = module.params.get('state')

    try:
        connection = connect_to_aws(boto.ec2.autoscale, region, **aws_connect_params)
    except (boto.exception.NoAuthHandlerFound, AnsibleAWSError) as e:
        module.fail_json(msg=str(e))

    if state == 'present':
        create_scaling_policy(connection, module)
    elif state == 'absent':
        delete_scaling_policy(connection, module)


if __name__ == '__main__':
    main()
