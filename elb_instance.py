#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: elb_instance
version_added: 1.0.0
short_description: De-registers or registers instances from EC2 ELBs
description:
  - This module de-registers or registers an AWS EC2 instance from the ELBs
    that it belongs to.
  - Will be marked changed when called only if there are ELBs found to operate on.
author: "John Jarvis (@jarv)"
options:
  state:
    description:
      - Register or deregister the instance.
    required: true
    choices: ['present', 'absent']
    type: str
  instance_id:
    description:
      - EC2 Instance ID.
    required: true
    type: str
  ec2_elbs:
    description:
      - List of ELB names
      - Required when I(state=present).
    type: list
    elements: str
  enable_availability_zone:
    description:
      - Whether to enable the availability zone of the instance on the target ELB if the availability zone has not already
        been enabled.
      - If I(enable_availability_zone=no), the task will fail if the availability zone is not enabled on the ELB.
    type: bool
    default: true
  wait:
    description:
      - Wait for instance registration or deregistration to complete successfully before returning.
    type: bool
    default: true
  wait_timeout:
    description:
      - Number of seconds to wait for an instance to change state.
      - If I(wait_timeout=0) then this module may return an error if a transient error occurs.
      - If non-zero then any transient errors are ignored until the timeout is reached.
      - Ignored when I(wait=no).
    default: 0
    type: int
notes:
- The ec2_elbs fact previously set by this module was deprecated in release 2.1.0 and since release
  4.0.0 is no longer set.
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
- amazon.aws.boto3
'''

EXAMPLES = r"""
# basic pre_task and post_task example
pre_tasks:
  - name: Instance De-register
    community.aws.elb_instance:
      instance_id: "{{ ansible_ec2_instance_id }}"
      state: absent
    register: deregister_instances
    delegate_to: localhost
roles:
  - myrole
post_tasks:
  - name: Instance Register
    community.aws.elb_instance:
      instance_id: "{{ ansible_ec2_instance_id }}"
      ec2_elbs: "{{ deregister_instances.updated_elbs }}"
      state: present
    delegate_to: localhost
"""

RETURN = '''
updated_elbs:
  description: A list of ELB names that the instance has been added to or removed from.
  returned: always
  type: list
  elements: str
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry


class ElbManager:
    """Handles EC2 instance ELB registration and de-registration"""

    def __init__(self, module, instance_id=None, ec2_elbs=None):
        retry_decorator = AWSRetry.jittered_backoff()
        self.module = module
        self.client_asg = module.client('autoscaling', retry_decorator=retry_decorator)
        self.client_ec2 = module.client('ec2', retry_decorator=retry_decorator)
        self.client_elb = module.client('elb', retry_decorator=retry_decorator)
        self.instance_id = instance_id
        self.lbs = self._get_instance_lbs(ec2_elbs)
        self.changed = False
        self.updated_elbs = set()

    def deregister(self, wait, timeout):
        """De-register the instance from all ELBs and wait for the ELB
        to report it out-of-service"""

        for lb in self.lbs:
            instance_ids = [i['InstanceId'] for i in lb['Instances']]
            if self.instance_id not in instance_ids:
                continue

            self.updated_elbs.add(lb['LoadBalancerName'])

            if self.module.check_mode:
                self.changed = True
                continue

            try:
                self.client_elb.deregister_instances_from_load_balancer(
                    aws_retry=True,
                    LoadBalancerName=lb['LoadBalancerName'],
                    Instances=[{"InstanceId": self.instance_id}],
                )
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                self.module.fail_json_aws(e, 'Failed to deregister instance from load balancer',
                                          load_balancer=lb, instance=self.instance_id)

            # The ELB is changing state in some way. Either an instance that's
            # InService is moving to OutOfService, or an instance that's
            # already OutOfService is being deregistered.
            self.changed = True

        if wait:
            for lb in self.lbs:
                self._await_elb_instance_state(lb, 'Deregistered', timeout)

    def register(self, wait, enable_availability_zone, timeout):
        """Register the instance for all ELBs and wait for the ELB
        to report the instance in-service"""
        for lb in self.lbs:
            instance_ids = [i['InstanceId'] for i in lb['Instances']]
            if self.instance_id in instance_ids:
                continue

            self.updated_elbs.add(lb['LoadBalancerName'])

            if enable_availability_zone:
                self.changed |= self._enable_availailability_zone(lb)

            if self.module.check_mode:
                self.changed = True
                continue

            try:
                self.client_elb.register_instances_with_load_balancer(
                    aws_retry=True,
                    LoadBalancerName=lb['LoadBalancerName'],
                    Instances=[{"InstanceId": self.instance_id}],
                )
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                self.module.fail_json_aws(e, 'Failed to register instance with load balancer',
                                          load_balancer=lb, instance=self.instance_id)

            self.changed = True

        if wait:
            for lb in self.lbs:
                self._await_elb_instance_state(lb, 'InService', timeout)

    @AWSRetry.jittered_backoff()
    def _describe_elbs(self, **params):
        paginator = self.client_elb.get_paginator('describe_load_balancers')
        results = paginator.paginate(**params).build_full_result()
        return results['LoadBalancerDescriptions']

    def exists(self, lbtest):
        """ Verify that the named ELB actually exists """

        found = False
        for lb in self.lbs:
            if lb['LoadBalancerName'] == lbtest:
                found = True
                break
        return found

    def _enable_availailability_zone(self, lb):
        """Enable the current instance's availability zone in the provided lb.
        Returns True if the zone was enabled or False if no change was made.
        lb: load balancer"""
        instance = self._get_instance()
        desired_zone = instance['Placement']['AvailabilityZone']

        if desired_zone in lb['AvailabilityZones']:
            return False

        if self.module.check_mode:
            return True

        try:
            self.client_elb.enable_availability_zones_for_load_balancer(
                aws_retry=True,
                LoadBalancerName=lb['LoadBalancerName'],
                AvailabilityZones=[desired_zone],
            )
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, 'Failed to enable AZ on load balancers',
                                      load_balancer=lb, zone=desired_zone)

        return True

    def _await_elb_instance_state(self, lb, awaited_state, timeout):
        """Wait for an ELB to change state"""
        if self.module.check_mode:
            return

        initial_state = self._get_instance_health(lb)

        if awaited_state == initial_state:
            return

        if awaited_state == 'InService':
            waiter = self.client_elb.get_waiter('instance_in_service')
        elif awaited_state == 'Deregistered':
            waiter = self.client_elb.get_waiter('instance_deregistered')
        elif awaited_state == 'OutOfService':
            waiter = self.client_elb.get_waiter('instance_deregistered')
        else:
            self.module.fail_json(msg='Could not wait for unknown state', awaited_state=awaited_state)

        try:
            waiter.wait(
                LoadBalancerName=lb['LoadBalancerName'],
                Instances=[{"InstanceId": self.instance_id}],
                WaiterConfig={'Delay': 1, 'MaxAttempts': timeout},
            )
        except botocore.exceptions.WaiterError as e:
            self.module.fail_json_aws(e, msg='Timeout waiting for instance to reach desired state',
                                      awaited_state=awaited_state)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg='Error while waiting for instance to reach desired state',
                                      awaited_state=awaited_state)

        return

    def _get_instance_health(self, lb):
        """
        Check instance health, should return status object or None under
        certain error conditions.
        """
        try:
            status = self.client_elb.describe_instance_health(
                aws_retry=True,
                LoadBalancerName=lb['LoadBalancerName'],
                Instances=[{'InstanceId': self.instance_id}],
            )['InstanceStates']
        except is_boto3_error_code('InvalidInstance'):
            return None
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
            self.module.fail_json_aws(e, msg='Failed to get instance health')

        if not status:
            return None

        return status[0]['State']

    def _get_instance_lbs(self, ec2_elbs=None):
        """Returns a list of ELBs attached to self.instance_id
        ec2_elbs: an optional list of elb names that will be used
                  for elb lookup instead of returning what elbs
                  are attached to self.instance_id"""

        list_params = dict()
        if not ec2_elbs:
            ec2_elbs = self._get_auto_scaling_group_lbs()

        if ec2_elbs:
            list_params['LoadBalancerNames'] = ec2_elbs

        try:
            elbs = self._describe_elbs(**list_params)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, 'Failed to describe load balancers')

        if ec2_elbs:
            return elbs

        # If ec2_elbs wasn't specified, then filter out LBs we're not a member
        # of.
        lbs = []
        for lb in elbs:
            instance_ids = [i['InstanceId'] for i in lb['Instances']]
            if self.instance_id in instance_ids:
                lbs.append(lb)

        return lbs

    def _get_auto_scaling_group_lbs(self):
        """Returns a list of ELBs associated with self.instance_id
           indirectly through its auto scaling group membership"""

        try:
            asg_instances = self.client_asg.describe_auto_scaling_instances(
                aws_retry=True,
                InstanceIds=[self.instance_id])['AutoScalingInstances']
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg='Failed to describe ASG Instance')

        if len(asg_instances) > 1:
            self.module.fail_json(msg="Illegal state, expected one auto scaling group instance.")

        if not asg_instances:
            # Instance isn't a member of an ASG
            return []

        asg_name = asg_instances[0]['AutoScalingGroupName']

        try:
            asg_instances = self.client_asg.describe_auto_scaling_groups(
                aws_retry=True,
                AutoScalingGroupNames=[asg_name])['AutoScalingGroups']
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg='Failed to describe ASG Instance')

        if len(asg_instances) != 1:
            self.module.fail_json(msg="Illegal state, expected one auto scaling group.")

        return asg_instances[0]['LoadBalancerNames']

    def _get_instance(self):
        """Returns the description of an instance"""
        try:
            result = self.client_ec2.describe_instances(
                aws_retry=True,
                InstanceIds=[self.instance_id])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg='Failed to describe ASG Instance')
        return result['Reservations'][0]['Instances'][0]


def main():
    argument_spec = dict(
        state={'required': True, 'choices': ['present', 'absent']},
        instance_id={'required': True},
        ec2_elbs={'default': None, 'required': False, 'type': 'list', 'elements': 'str'},
        enable_availability_zone={'default': True, 'required': False, 'type': 'bool'},
        wait={'required': False, 'default': True, 'type': 'bool'},
        wait_timeout={'required': False, 'default': 0, 'type': 'int'},
    )
    required_if = [
        ('state', 'present', ['ec2_elbs']),
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=required_if,
        supports_check_mode=True,
    )

    ec2_elbs = module.params['ec2_elbs']
    wait = module.params['wait']
    enable_availability_zone = module.params['enable_availability_zone']
    timeout = module.params['wait_timeout']
    instance_id = module.params['instance_id']

    elb_man = ElbManager(module, instance_id, ec2_elbs)

    if ec2_elbs is not None:
        for elb in ec2_elbs:
            if not elb_man.exists(elb):
                module.fail_json(msg="ELB {0} does not exist".format(elb))

    if module.params['state'] == 'present':
        elb_man.register(wait, enable_availability_zone, timeout)
    elif module.params['state'] == 'absent':
        elb_man.deregister(wait, timeout)

    module.exit_json(
        changed=elb_man.changed,
        updated_elbs=list(elb_man.updated_elbs),
    )


if __name__ == '__main__':
    main()
