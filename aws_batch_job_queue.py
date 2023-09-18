#!/usr/bin/python
# Copyright (c) 2017 Jon Meran <jonathan.meran@sonos.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: aws_batch_job_queue
version_added: 1.0.0
short_description: Manage AWS Batch Job Queues
description:
    - This module allows the management of AWS Batch Job Queues.
    - It is idempotent and supports "Check" mode.
    - Use module M(community.aws.aws_batch_compute_environment) to manage the compute
      environment, M(community.aws.aws_batch_job_queue) to manage job queues, M(community.aws.aws_batch_job_definition) to manage job definitions.
author: Jon Meran (@jonmer85)
options:
  job_queue_name:
    description:
      - The name for the job queue
    required: true
    type: str
  state:
    description:
      - Describes the desired state.
    default: "present"
    choices: ["present", "absent"]
    type: str
  job_queue_state:
    description:
      - The state of the job queue. If the job queue state is ENABLED, it is able to accept jobs.
    default: "ENABLED"
    choices: ["ENABLED", "DISABLED"]
    type: str
  priority:
    description:
      - The priority of the job queue. Job queues with a higher priority (or a lower integer value for the priority
        parameter) are evaluated first when associated with same compute environment. Priority is determined in
        ascending order, for example, a job queue with a priority value of 1 is given scheduling preference over a job
        queue with a priority value of 10.
    required: true
    type: int
  compute_environment_order:
    description:
      - The set of compute environments mapped to a job queue and their order relative to each other. The job
        scheduler uses this parameter to determine which compute environment should execute a given job. Compute
        environments must be in the VALID state before you can associate them with a job queue. You can associate up to
        3 compute environments with a job queue.
    required: true
    type: list
    elements: dict
    suboptions:
        order:
            type: int
            description: The relative priority of the environment.
        compute_environment:
            type: str
            description: The name of the compute environment.
requirements:
    - boto3
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
- name: My Batch Job Queue
  community.aws.aws_batch_job_queue:
    job_queue_name: jobQueueName
    state: present
    region: us-east-1
    job_queue_state: ENABLED
    priority: 1
    compute_environment_order:
    - order: 1
      compute_environment: my_compute_env1
    - order: 2
      compute_environment: my_compute_env2
  register: batch_job_queue_action

- name: show results
  ansible.builtin.debug:
    var: batch_job_queue_action
'''

RETURN = r'''
---
output:
  description: "returns what action was taken, whether something was changed, invocation and response"
  returned: always
  sample:
    batch_job_queue_action: updated
    changed: false
    response:
      job_queue_arn: "arn:aws:batch:...."
      job_queue_name: <name>
      priority: 1
      state: DISABLED
      status: UPDATING
      status_reason: "JobQueue Healthy"
  type: dict
'''

from ansible_collections.amazon.aws.plugins.module_utils.batch import set_api_params
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # Handled by AnsibleAWSModule

# ---------------------------------------------------------------------------------------------------
#
#   Helper Functions & classes
#
# ---------------------------------------------------------------------------------------------------


def validate_params(module):
    """
    Performs basic parameter validation.

    :param module:
    """
    return


# ---------------------------------------------------------------------------------------------------
#
#   Batch Job Queue functions
#
# ---------------------------------------------------------------------------------------------------

def get_current_job_queue(module, client):
    try:
        environments = client.describe_job_queues(
            jobQueues=[module.params['job_queue_name']]
        )
        return environments['jobQueues'][0] if len(environments['jobQueues']) > 0 else None
    except ClientError:
        return None


def create_job_queue(module, client):
    """
        Adds a Batch job queue

        :param module:
        :param client:
        :return:
        """

    changed = False

    # set API parameters
    params = ('job_queue_name', 'priority')
    api_params = set_api_params(module, params)

    if module.params['job_queue_state'] is not None:
        api_params['state'] = module.params['job_queue_state']

    api_params['computeEnvironmentOrder'] = get_compute_environment_order_list(module)

    try:
        if not module.check_mode:
            client.create_job_queue(**api_params)
        changed = True
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Error creating compute environment')

    return changed


def get_compute_environment_order_list(module):
    compute_environment_order_list = []
    for ceo in module.params['compute_environment_order']:
        compute_environment_order_list.append(dict(order=ceo['order'], computeEnvironment=ceo['compute_environment']))
    return compute_environment_order_list


def remove_job_queue(module, client):
    """
    Remove a Batch job queue

    :param module:
    :param client:
    :return:
    """

    changed = False

    # set API parameters
    api_params = {'jobQueue': module.params['job_queue_name']}

    try:
        if not module.check_mode:
            client.delete_job_queue(**api_params)
        changed = True
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Error removing job queue')
    return changed


def manage_state(module, client):
    changed = False
    current_state = 'absent'
    state = module.params['state']
    job_queue_state = module.params['job_queue_state']
    job_queue_name = module.params['job_queue_name']
    priority = module.params['priority']
    action_taken = 'none'
    response = None

    check_mode = module.check_mode

    # check if the job queue exists
    current_job_queue = get_current_job_queue(module, client)
    if current_job_queue:
        current_state = 'present'

    if state == 'present':
        if current_state == 'present':
            updates = False
            # Update Batch Job Queue configuration
            job_kwargs = {'jobQueue': job_queue_name}

            # Update configuration if needed
            if job_queue_state and current_job_queue['state'] != job_queue_state:
                job_kwargs.update({'state': job_queue_state})
                updates = True
            if priority is not None and current_job_queue['priority'] != priority:
                job_kwargs.update({'priority': priority})
                updates = True

            new_compute_environment_order_list = get_compute_environment_order_list(module)
            if new_compute_environment_order_list != current_job_queue['computeEnvironmentOrder']:
                job_kwargs['computeEnvironmentOrder'] = new_compute_environment_order_list
                updates = True

            if updates:
                try:
                    if not check_mode:
                        client.update_job_queue(**job_kwargs)
                    changed = True
                    action_taken = "updated"
                except (BotoCoreError, ClientError) as e:
                    module.fail_json_aws(e, msg="Unable to update job queue")

        else:
            # Create Job Queue
            changed = create_job_queue(module, client)
            action_taken = 'added'

        # Describe job queue
        response = get_current_job_queue(module, client)
        if not response:
            module.fail_json(msg='Unable to get job queue information after creating/updating')
    else:
        if current_state == 'present':
            # remove the Job Queue
            changed = remove_job_queue(module, client)
            action_taken = 'deleted'
    return dict(changed=changed, batch_job_queue_action=action_taken, response=response)


# ---------------------------------------------------------------------------------------------------
#
#   MAIN
#
# ---------------------------------------------------------------------------------------------------

def main():
    """
    Main entry point.

    :return dict: changed, batch_job_queue_action, response
    """

    argument_spec = dict(
        state=dict(required=False, default='present', choices=['present', 'absent']),
        job_queue_name=dict(required=True),
        job_queue_state=dict(required=False, default='ENABLED', choices=['ENABLED', 'DISABLED']),
        priority=dict(type='int', required=True),
        compute_environment_order=dict(type='list', required=True, elements='dict'),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    client = module.client('batch')

    validate_params(module)

    results = manage_state(module, client)

    module.exit_json(**camel_dict_to_snake_dict(results))


if __name__ == '__main__':
    main()
