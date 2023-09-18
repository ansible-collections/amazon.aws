#!/usr/bin/python
# Copyright (c) 2017 Jon Meran <jonathan.meran@sonos.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: batch_compute_environment
version_added: 1.0.0
short_description: Manage AWS Batch Compute Environments
description:
  - This module allows the management of AWS Batch Compute Environments.
  - It is idempotent and supports "Check" mode.
  - Use module M(community.aws.batch_compute_environment) to manage the compute
    environment, M(community.aws.batch_job_queue) to manage job queues, M(community.aws.batch_job_definition) to manage job definitions.
  - Prior to release 5.0.0 this module was called C(community.aws.aws_batch_compute_environment).
    The usage did not change.
author:
  - Jon Meran (@jonmer85)
options:
  compute_environment_name:
    description:
      - The name for your compute environment.
      - Up to 128 letters (uppercase and lowercase), numbers, and underscores are allowed.
    required: true
    type: str
  type:
    description:
      - The type of the compute environment.
    required: true
    choices: ["MANAGED", "UNMANAGED"]
    type: str
  state:
    description:
      - Describes the desired state.
    default: "present"
    choices: ["present", "absent"]
    type: str
  compute_environment_state:
    description:
      - The state of the compute environment.
      - If the state is C(ENABLED), then the compute environment accepts jobs
        from a queue and can scale out automatically based on queues.
    default: "ENABLED"
    choices: ["ENABLED", "DISABLED"]
    type: str
  service_role:
    description:
      - The full Amazon Resource Name (ARN) of the IAM role that allows AWS Batch to make calls to other AWS
        services on your behalf.
    required: true
    type: str
  compute_resource_type:
    description:
      - The type of compute resource.
    required: true
    choices: ["EC2", "SPOT"]
    type: str
  minv_cpus:
    description:
      - The minimum number of EC2 vCPUs that an environment should maintain.
    required: true
    type: int
  maxv_cpus:
    description:
      - The maximum number of EC2 vCPUs that an environment can reach.
    required: true
    type: int
  desiredv_cpus:
    description:
      - The desired number of EC2 vCPUS in the compute environment.
    type: int
  instance_types:
    description:
      - The instance types that may be launched.
    required: true
    type: list
    elements: str
  image_id:
    description:
      - The Amazon Machine Image (AMI) ID used for instances launched in the compute environment.
    type: str
  subnets:
    description:
      - The VPC subnets into which the compute resources are launched.
    required: true
    type: list
    elements: str
  security_group_ids:
    description:
      - The EC2 security groups that are associated with instances launched in the compute environment.
    required: true
    type: list
    elements: str
  ec2_key_pair:
    description:
      - The EC2 key pair that is used for instances launched in the compute environment.
    type: str
  instance_role:
    description:
      - The Amazon ECS instance role applied to Amazon EC2 instances in a compute environment.
    required: true
    type: str
  tags:
    description:
      - Key-value pair tags to be applied to resources that are launched in the compute environment.
    type: dict
  bid_percentage:
    description:
      - The minimum percentage that a Spot Instance price must be when compared with the On-Demand price for that
        instance type before instances are launched.
      - For example, if your bid percentage is 20%, then the Spot price
        must be below 20% of the current On-Demand price for that EC2 instance.
    type: int
  spot_iam_fleet_role:
    description:
      - The Amazon Resource Name (ARN) of the Amazon EC2 Spot Fleet IAM role applied to a SPOT compute environment.
    type: str
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.boto3
'''

EXAMPLES = r'''
- name: My Batch Compute Environment
  community.aws.batch_compute_environment:
    compute_environment_name: computeEnvironmentName
    state: present
    region: us-east-1
    compute_environment_state: ENABLED
    type: MANAGED
    compute_resource_type: EC2
    minv_cpus: 0
    maxv_cpus: 2
    desiredv_cpus: 1
    instance_types:
      - optimal
    subnets:
      - my-subnet1
      - my-subnet2
    security_group_ids:
      - my-sg1
      - my-sg2
    instance_role: arn:aws:iam::<account>:instance-profile/<role>
    tags:
      tag1: value1
      tag2: value2
    service_role: arn:aws:iam::<account>:role/service-role/<role>
  register: aws_batch_compute_environment_action

- name: show results
  ansible.builtin.debug:
    var: aws_batch_compute_environment_action
'''

RETURN = r'''
---
output:
  description: "returns what action was taken, whether something was changed, invocation and response"
  returned: always
  sample:
    batch_compute_environment_action: none
    changed: false
    invocation:
      module_args:
        aws_access_key: ~
        aws_secret_key: ~
        bid_percentage: ~
        compute_environment_name: <name>
        compute_environment_state: ENABLED
        compute_resource_type: EC2
        desiredv_cpus: 0
        ec2_key_pair: ~
        ec2_url: ~
        image_id: ~
        instance_role: "arn:aws:iam::..."
        instance_types:
          - optimal
        maxv_cpus: 8
        minv_cpus: 0
        profile: ~
        region: us-east-1
        security_group_ids:
          - "*******"
        security_token: ~
        service_role: "arn:aws:iam::...."
        spot_iam_fleet_role: ~
        state: present
        subnets:
          - "******"
        tags:
          Environment: <name>
          Name: <name>
        type: MANAGED
        validate_certs: true
    response:
      computeEnvironmentArn: "arn:aws:batch:...."
      computeEnvironmentName: <name>
      computeResources:
        desiredvCpus: 0
        instanceRole: "arn:aws:iam::..."
        instanceTypes:
          - optimal
        maxvCpus: 8
        minvCpus: 0
        securityGroupIds:
          - "******"
        subnets:
          - "*******"
        tags:
          Environment: <name>
          Name: <name>
        type: EC2
      ecsClusterArn: "arn:aws:ecs:....."
      serviceRole: "arn:aws:iam::..."
      state: ENABLED
      status: VALID
      statusReason: "ComputeEnvironment Healthy"
      type: MANAGED
  type: dict
'''

import re
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import snake_dict_to_camel_dict, camel_dict_to_snake_dict

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # Handled by AnsibleAWSModule


# ---------------------------------------------------------------------------------------------------
#
#   Helper Functions & classes
#
# ---------------------------------------------------------------------------------------------------

def set_api_params(module, module_params):
    """
    Sets module parameters to those expected by the boto3 API.

    :param module:
    :param module_params:
    :return:
    """
    api_params = dict((k, v) for k, v in dict(module.params).items() if k in module_params and v is not None)
    return snake_dict_to_camel_dict(api_params)


def validate_params(module):
    """
    Performs basic parameter validation.

    :param module:
    :return:
    """

    compute_environment_name = module.params['compute_environment_name']

    # validate compute environment name
    if not re.search(r'^[\w\_:]+$', compute_environment_name):
        module.fail_json(
            msg="Function compute_environment_name {0} is invalid. Names must contain only alphanumeric characters "
                "and underscores.".format(compute_environment_name)
        )
    if not compute_environment_name.startswith('arn:aws:batch:'):
        if len(compute_environment_name) > 128:
            module.fail_json(msg='compute_environment_name "{0}" exceeds 128 character limit'
                             .format(compute_environment_name))

    return


# ---------------------------------------------------------------------------------------------------
#
#   Batch Compute Environment functions
#
# ---------------------------------------------------------------------------------------------------

def get_current_compute_environment(module, client):
    try:
        environments = client.describe_compute_environments(
            computeEnvironments=[module.params['compute_environment_name']]
        )
        if len(environments['computeEnvironments']) > 0:
            return environments['computeEnvironments'][0]
        else:
            return None
    except ClientError:
        return None


def create_compute_environment(module, client):
    """
        Adds a Batch compute environment

        :param module:
        :param client:
        :return:
        """

    changed = False

    # set API parameters
    params = (
        'compute_environment_name', 'type', 'service_role')
    api_params = set_api_params(module, params)

    if module.params['compute_environment_state'] is not None:
        api_params['state'] = module.params['compute_environment_state']

    compute_resources_param_list = ('minv_cpus', 'maxv_cpus', 'desiredv_cpus', 'instance_types', 'image_id', 'subnets',
                                    'security_group_ids', 'ec2_key_pair', 'instance_role', 'tags', 'bid_percentage',
                                    'spot_iam_fleet_role')
    compute_resources_params = set_api_params(module, compute_resources_param_list)

    if module.params['compute_resource_type'] is not None:
        compute_resources_params['type'] = module.params['compute_resource_type']

    # if module.params['minv_cpus'] is not None:
    #     compute_resources_params['minvCpus'] = module.params['minv_cpus']

    api_params['computeResources'] = compute_resources_params

    try:
        if not module.check_mode:
            client.create_compute_environment(**api_params)
        changed = True
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, msg='Error creating compute environment')

    return changed


def remove_compute_environment(module, client):
    """
    Remove a Batch compute environment

    :param module:
    :param client:
    :return:
    """

    changed = False

    # set API parameters
    api_params = {'computeEnvironment': module.params['compute_environment_name']}

    try:
        if not module.check_mode:
            client.delete_compute_environment(**api_params)
        changed = True
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, msg='Error removing compute environment')
    return changed


def manage_state(module, client):
    changed = False
    current_state = 'absent'
    state = module.params['state']
    compute_environment_state = module.params['compute_environment_state']
    compute_environment_name = module.params['compute_environment_name']
    service_role = module.params['service_role']
    minv_cpus = module.params['minv_cpus']
    maxv_cpus = module.params['maxv_cpus']
    desiredv_cpus = module.params['desiredv_cpus']
    action_taken = 'none'
    update_env_response = ''

    check_mode = module.check_mode

    # check if the compute environment exists
    current_compute_environment = get_current_compute_environment(module, client)
    response = current_compute_environment
    if current_compute_environment:
        current_state = 'present'

    if state == 'present':
        if current_state == 'present':
            updates = False
            # Update Batch Compute Environment configuration
            compute_kwargs = {'computeEnvironment': compute_environment_name}

            # Update configuration if needed
            compute_resources = {}
            if compute_environment_state and current_compute_environment['state'] != compute_environment_state:
                compute_kwargs.update({'state': compute_environment_state})
                updates = True
            if service_role and current_compute_environment['serviceRole'] != service_role:
                compute_kwargs.update({'serviceRole': service_role})
                updates = True
            if minv_cpus is not None and current_compute_environment['computeResources']['minvCpus'] != minv_cpus:
                compute_resources['minvCpus'] = minv_cpus
            if maxv_cpus is not None and current_compute_environment['computeResources']['maxvCpus'] != maxv_cpus:
                compute_resources['maxvCpus'] = maxv_cpus
            if desiredv_cpus is not None and current_compute_environment['computeResources']['desiredvCpus'] != desiredv_cpus:
                compute_resources['desiredvCpus'] = desiredv_cpus
            if len(compute_resources) > 0:
                compute_kwargs['computeResources'] = compute_resources
                updates = True
            if updates:
                try:
                    if not check_mode:
                        update_env_response = client.update_compute_environment(**compute_kwargs)
                    if not update_env_response:
                        module.fail_json(msg='Unable to get compute environment information after creating')
                    changed = True
                    action_taken = "updated"
                except (BotoCoreError, ClientError) as e:
                    module.fail_json_aws(e, msg="Unable to update environment.")

        else:
            # Create Batch Compute Environment
            changed = create_compute_environment(module, client)
            # Describe compute environment
            action_taken = 'added'
        response = get_current_compute_environment(module, client)
        if not response:
            module.fail_json(msg='Unable to get compute environment information after creating')
    else:
        if current_state == 'present':
            # remove the compute environment
            changed = remove_compute_environment(module, client)
            action_taken = 'deleted'
    return dict(changed=changed, batch_compute_environment_action=action_taken, response=response)


# ---------------------------------------------------------------------------------------------------
#
#   MAIN
#
# ---------------------------------------------------------------------------------------------------

def main():
    """
    Main entry point.

    :return dict: changed, batch_compute_environment_action, response
    """

    argument_spec = dict(
        state=dict(default='present', choices=['present', 'absent']),
        compute_environment_name=dict(required=True),
        type=dict(required=True, choices=['MANAGED', 'UNMANAGED']),
        compute_environment_state=dict(required=False, default='ENABLED', choices=['ENABLED', 'DISABLED']),
        service_role=dict(required=True),
        compute_resource_type=dict(required=True, choices=['EC2', 'SPOT']),
        minv_cpus=dict(type='int', required=True),
        maxv_cpus=dict(type='int', required=True),
        desiredv_cpus=dict(type='int'),
        instance_types=dict(type='list', required=True, elements='str'),
        image_id=dict(),
        subnets=dict(type='list', required=True, elements='str'),
        security_group_ids=dict(type='list', required=True, elements='str'),
        ec2_key_pair=dict(no_log=False),
        instance_role=dict(required=True),
        tags=dict(type='dict'),
        bid_percentage=dict(type='int'),
        spot_iam_fleet_role=dict(),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    client = module.client('batch')

    validate_params(module)

    results = manage_state(module, client)

    module.exit_json(**camel_dict_to_snake_dict(results, ignore_list=['Tags']))


if __name__ == '__main__':
    main()
