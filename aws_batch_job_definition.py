#!/usr/bin/python
# Copyright (c) 2017 Jon Meran <jonathan.meran@sonos.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: aws_batch_job_definition
version_added: 1.0.0
short_description: Manage AWS Batch Job Definitions
description:
    - This module allows the management of AWS Batch Job Definitions.
    - It is idempotent and supports "Check" mode.
    - Use module M(community.aws.aws_batch_compute_environment) to manage the compute
      environment, M(community.aws.aws_batch_job_queue) to manage job queues, M(community.aws.aws_batch_job_definition) to manage job definitions.
author: Jon Meran (@jonmer85)
options:
  job_definition_arn:
    description:
      - The ARN for the job definition.
    type: str
  job_definition_name:
    description:
      - The name for the job definition.
    required: true
    type: str
  state:
    description:
      - Describes the desired state.
    default: "present"
    choices: ["present", "absent"]
    type: str
  type:
    description:
      - The type of job definition.
    required: true
    type: str
  parameters:
    description:
      - Default parameter substitution placeholders to set in the job definition. Parameters are specified as a
        key-value pair mapping. Parameters in a SubmitJob request override any corresponding parameter defaults from
        the job definition.
    type: dict
  image:
    description:
      - The image used to start a container. This string is passed directly to the Docker daemon. Images in the Docker
        Hub registry are available by default. Other repositories are specified with `` repository-url /image <colon>tag ``.
        Up to 255 letters (uppercase and lowercase), numbers, hyphens, underscores, colons, periods, forward slashes,
        and number signs are allowed. This parameter maps to Image in the Create a container section of the Docker
        Remote API and the IMAGE parameter of docker run.
    required: true
    type: str
  vcpus:
    description:
      - The number of vCPUs reserved for the container. This parameter maps to CpuShares in the Create a container
        section of the Docker Remote API and the --cpu-shares option to docker run. Each vCPU is equivalent to
        1,024 CPU shares.
    required: true
    type: int
  memory:
    description:
      - The hard limit (in MiB) of memory to present to the container. If your container attempts to exceed the memory
        specified here, the container is killed. This parameter maps to Memory in the Create a container section of the
        Docker Remote API and the --memory option to docker run.
    required: true
    type: int
  command:
    description:
      - The command that is passed to the container. This parameter maps to Cmd in the Create a container section of
        the Docker Remote API and the COMMAND parameter to docker run. For more information,
        see U(https://docs.docker.com/engine/reference/builder/#cmd).
    type: list
    elements: str
  job_role_arn:
    description:
      - The Amazon Resource Name (ARN) of the IAM role that the container can assume for AWS permissions.
    type: str
  volumes:
    description:
      - A list of data volumes used in a job.
    suboptions:
      host:
        description:
          - The contents of the host parameter determine whether your data volume persists on the host container
            instance and where it is stored. If the host parameter is empty, then the Docker daemon assigns a host
            path for your data volume, but the data is not guaranteed to persist after the containers associated with
            it stop running.
            This is a dictionary with one property, sourcePath - The path on the host container
            instance that is presented to the container. If this parameter is empty,then the Docker daemon has assigned
            a host path for you. If the host parameter contains a sourcePath file location, then the data volume
            persists at the specified location on the host container instance until you delete it manually. If the
            sourcePath value does not exist on the host container instance, the Docker daemon creates it. If the
            location does exist, the contents of the source path folder are exported.
      name:
        description:
          - The name of the volume. Up to 255 letters (uppercase and lowercase), numbers, hyphens, and underscores are
            allowed. This name is referenced in the sourceVolume parameter of container definition mountPoints.
    type: list
    elements: dict
  environment:
    description:
      - The environment variables to pass to a container. This parameter maps to Env in the Create a container section
        of the Docker Remote API and the --env option to docker run.
    suboptions:
      name:
        description:
          - The name of the key value pair. For environment variables, this is the name of the environment variable.
      value:
        description:
          - The value of the key value pair. For environment variables, this is the value of the environment variable.
    type: list
    elements: dict
  mount_points:
    description:
      - The mount points for data volumes in your container. This parameter maps to Volumes in the Create a container
        section of the Docker Remote API and the --volume option to docker run.
    suboptions:
      containerPath:
        description:
          - The path on the container at which to mount the host volume.
      readOnly:
        description:
          - If this value is true , the container has read-only access to the volume; otherwise, the container can write
             to the volume. The default value is C(false).
      sourceVolume:
        description:
          - The name of the volume to mount.
    type: list
    elements: dict
  readonly_root_filesystem:
    description:
      - When this parameter is true, the container is given read-only access to its root file system. This parameter
        maps to ReadonlyRootfs in the Create a container section of the Docker Remote API and the --read-only option
        to docker run.
    type: str
  privileged:
    description:
      - When this parameter is true, the container is given elevated privileges on the host container instance
        (similar to the root user). This parameter maps to Privileged in the Create a container section of the
        Docker Remote API and the --privileged option to docker run.
    type: str
  ulimits:
    description:
      - A list of ulimits to set in the container. This parameter maps to Ulimits in the Create a container section
        of the Docker Remote API and the --ulimit option to docker run.
    suboptions:
      hardLimit:
        description:
          - The hard limit for the ulimit type.
      name:
        description:
          - The type of the ulimit.
      softLimit:
        description:
          - The soft limit for the ulimit type.
    type: list
    elements: dict
  user:
    description:
      - The user name to use inside the container. This parameter maps to User in the Create a container section of
        the Docker Remote API and the --user option to docker run.
    type: str
  attempts:
    description:
      - Retry strategy - The number of times to move a job to the RUNNABLE status. You may specify between 1 and 10
        attempts. If attempts is greater than one, the job is retried if it fails until it has moved to RUNNABLE that
        many times.
    type: int
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = r'''
---
- hosts: localhost
  gather_facts: no
  vars:
    state: present
  tasks:
- name: My Batch Job Definition
  community.aws.aws_batch_job_definition:
    job_definition_name: My Batch Job Definition
    state: present
    type: container
    parameters:
      Param1: Val1
      Param2: Val2
    image: <Docker Image URL>
    vcpus: 1
    memory: 512
    command:
      - python
      - run_my_script.py
      - arg1
    job_role_arn: <Job Role ARN>
    attempts: 3
  register: job_definition_create_result

- name: show results
  ansible.builtin.debug: var=job_definition_create_result
'''

RETURN = r'''
---
output:
  description: "returns what action was taken, whether something was changed, invocation and response"
  returned: always
  sample:
    aws_batch_job_definition_action: none
    changed: false
    response:
      job_definition_arn: "arn:aws:batch:...."
      job_definition_name: <name>
      status: INACTIVE
      type: container
  type: dict
'''

from ansible_collections.amazon.aws.plugins.module_utils.batch import cc, set_api_params
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # Handled by AnsibleAWSModule


# ---------------------------------------------------------------------------------------------------
#
#   Helper Functions & classes
#
# ---------------------------------------------------------------------------------------------------

# logger = logging.getLogger()
# logging.basicConfig(filename='ansible_debug.log')
# logger.setLevel(logging.DEBUG)


def validate_params(module, batch_client):
    """
    Performs basic parameter validation.

    :param module:
    :param batch_client:
    :return:
    """
    return


# ---------------------------------------------------------------------------------------------------
#
#   Batch Job Definition functions
#
# ---------------------------------------------------------------------------------------------------

def get_current_job_definition(module, batch_client):
    try:
        environments = batch_client.describe_job_definitions(
            jobDefinitionName=module.params['job_definition_name']
        )
        if len(environments['jobDefinitions']) > 0:
            latest_revision = max(map(lambda d: d['revision'], environments['jobDefinitions']))
            latest_definition = next((x for x in environments['jobDefinitions'] if x['revision'] == latest_revision),
                                     None)
            return latest_definition
        return None
    except ClientError:
        return None


def create_job_definition(module, batch_client):
    """
        Adds a Batch job definition

        :param module:
        :param batch_client:
        :return:
        """

    changed = False

    # set API parameters
    api_params = set_api_params(module, get_base_params())
    container_properties_params = set_api_params(module, get_container_property_params())
    retry_strategy_params = set_api_params(module, get_retry_strategy_params())

    api_params['retryStrategy'] = retry_strategy_params
    api_params['containerProperties'] = container_properties_params

    try:
        if not module.check_mode:
            batch_client.register_job_definition(**api_params)
        changed = True
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Error registering job definition')

    return changed


def get_retry_strategy_params():
    return 'attempts',


def get_container_property_params():
    return ('image', 'vcpus', 'memory', 'command', 'job_role_arn', 'volumes', 'environment', 'mount_points',
            'readonly_root_filesystem', 'privileged', 'ulimits', 'user')


def get_base_params():
    return 'job_definition_name', 'type', 'parameters'


def get_compute_environment_order_list(module):
    compute_environment_order_list = []
    for ceo in module.params['compute_environment_order']:
        compute_environment_order_list.append(dict(order=ceo['order'], computeEnvironment=ceo['compute_environment']))
    return compute_environment_order_list


def remove_job_definition(module, batch_client):
    """
    Remove a Batch job definition

    :param module:
    :param batch_client:
    :return:
    """

    changed = False

    try:
        if not module.check_mode:
            batch_client.deregister_job_definition(jobDefinition=module.params['job_definition_arn'])
        changed = True
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Error removing job definition')
    return changed


def job_definition_equal(module, current_definition):
    equal = True

    for param in get_base_params():
        if module.params.get(param) != current_definition.get(cc(param)):
            equal = False
            break

    for param in get_container_property_params():
        if module.params.get(param) != current_definition.get('containerProperties').get(cc(param)):
            equal = False
            break

    for param in get_retry_strategy_params():
        if module.params.get(param) != current_definition.get('retryStrategy').get(cc(param)):
            equal = False
            break

    return equal


def manage_state(module, batch_client):
    changed = False
    current_state = 'absent'
    state = module.params['state']
    job_definition_name = module.params['job_definition_name']
    action_taken = 'none'
    response = None

    check_mode = module.check_mode

    # check if the job definition exists
    current_job_definition = get_current_job_definition(module, batch_client)
    if current_job_definition:
        current_state = 'present'

    if state == 'present':
        if current_state == 'present':
            # check if definition has changed and register a new version if necessary
            if not job_definition_equal(module, current_job_definition):
                create_job_definition(module, batch_client)
                action_taken = 'updated with new version'
                changed = True
        else:
            # Create Job definition
            changed = create_job_definition(module, batch_client)
            action_taken = 'added'

        response = get_current_job_definition(module, batch_client)
        if not response:
            module.fail_json(msg='Unable to get job definition information after creating/updating')
    else:
        if current_state == 'present':
            # remove the Job definition
            changed = remove_job_definition(module, batch_client)
            action_taken = 'deregistered'
    return dict(changed=changed, batch_job_definition_action=action_taken, response=response)


# ---------------------------------------------------------------------------------------------------
#
#   MAIN
#
# ---------------------------------------------------------------------------------------------------

def main():
    """
    Main entry point.

    :return dict: ansible facts
    """

    argument_spec = dict(
        state=dict(required=False, default='present', choices=['present', 'absent']),
        job_definition_name=dict(required=True),
        job_definition_arn=dict(),
        type=dict(required=True),
        parameters=dict(type='dict'),
        image=dict(required=True),
        vcpus=dict(type='int', required=True),
        memory=dict(type='int', required=True),
        command=dict(type='list', default=[], elements='str'),
        job_role_arn=dict(),
        volumes=dict(type='list', default=[], elements='dict'),
        environment=dict(type='list', default=[], elements='dict'),
        mount_points=dict(type='list', default=[], elements='dict'),
        readonly_root_filesystem=dict(),
        privileged=dict(),
        ulimits=dict(type='list', default=[], elements='dict'),
        user=dict(),
        attempts=dict(type='int')
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    batch_client = module.client('batch')

    validate_params(module, batch_client)

    results = manage_state(module, batch_client)

    module.exit_json(**camel_dict_to_snake_dict(results))


if __name__ == '__main__':
    main()
