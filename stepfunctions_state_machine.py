#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2019, Tom De Keyser (@tdekeyser)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: stepfunctions_state_machine
version_added: 1.0.0
short_description: Manage AWS Step Functions state machines
description:
    - Create, update and delete state machines in AWS Step Functions.
    - Calling the module in C(state=present) for an existing AWS Step Functions state machine
      will attempt to update the state machine definition, IAM Role, or tags with the provided data.
    - Prior to release 5.0.0 this module was called C(community.aws.aws_step_functions_state_machine).
      The usage did not change.

options:
    name:
        description:
            - Name of the state machine.
        required: true
        type: str
    definition:
        description:
            - The Amazon States Language definition of the state machine. See
              U(https://docs.aws.amazon.com/step-functions/latest/dg/concepts-amazon-states-language.html) for more
              information on the Amazon States Language.
            - Required when I(state=present).
        type: json
    role_arn:
        description:
            - The ARN of the IAM Role that will be used by the state machine for its executions.
            - Required when I(state=present).
        type: str
    state:
        description:
            - Desired state for the state machine.
        default: present
        choices: [ present, absent ]
        type: str

author:
    - Tom De Keyser (@tdekeyser)

extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.tags
    - amazon.aws.boto3
"""

EXAMPLES = r"""
# Create a new AWS Step Functions state machine
- name: Setup HelloWorld state machine
  community.aws.stepfunctions_state_machine:
    name: "HelloWorldStateMachine"
    definition: "{{ lookup('file','state_machine.json') }}"
    role_arn: arn:aws:iam::123456789012:role/service-role/invokeLambdaStepFunctionsRole
    tags:
      project: helloWorld

# Update an existing state machine
- name: Change IAM Role and tags of HelloWorld state machine
  community.aws.stepfunctions_state_machine:
    name: HelloWorldStateMachine
    definition: "{{ lookup('file','state_machine.json') }}"
    role_arn: arn:aws:iam::123456789012:role/service-role/anotherStepFunctionsRole
    tags:
      otherTag: aDifferentTag

# Remove the AWS Step Functions state machine
- name: Delete HelloWorld state machine
  community.aws.stepfunctions_state_machine:
    name: HelloWorldStateMachine
    state: absent
"""

RETURN = r"""
state_machine_arn:
    description: ARN of the AWS Step Functions state machine
    type: str
    returned: always
"""

try:
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def manage_state_machine(state, sfn_client, module):
    state_machine_arn = get_state_machine_arn(sfn_client, module)

    if state == "present":
        if state_machine_arn is None:
            create(sfn_client, module)
        else:
            update(state_machine_arn, sfn_client, module)
    elif state == "absent":
        if state_machine_arn is not None:
            remove(state_machine_arn, sfn_client, module)

    check_mode(module, msg="State is up-to-date.")
    module.exit_json(changed=False, state_machine_arn=state_machine_arn)


def create(sfn_client, module):
    check_mode(module, msg="State machine would be created.", changed=True)

    tags = module.params.get("tags")
    sfn_tags = ansible_dict_to_boto3_tag_list(tags, tag_name_key_name="key", tag_value_key_name="value") if tags else []

    state_machine = sfn_client.create_state_machine(
        name=module.params.get("name"),
        definition=module.params.get("definition"),
        roleArn=module.params.get("role_arn"),
        tags=sfn_tags,
    )
    module.exit_json(changed=True, state_machine_arn=state_machine.get("stateMachineArn"))


def remove(state_machine_arn, sfn_client, module):
    check_mode(module, msg=f"State machine would be deleted: {state_machine_arn}", changed=True)

    sfn_client.delete_state_machine(stateMachineArn=state_machine_arn)
    module.exit_json(changed=True, state_machine_arn=state_machine_arn)


def update(state_machine_arn, sfn_client, module):
    tags_to_add, tags_to_remove = compare_tags(state_machine_arn, sfn_client, module)

    if params_changed(state_machine_arn, sfn_client, module) or tags_to_add or tags_to_remove:
        check_mode(module, msg=f"State machine would be updated: {state_machine_arn}", changed=True)

        sfn_client.update_state_machine(
            stateMachineArn=state_machine_arn,
            definition=module.params.get("definition"),
            roleArn=module.params.get("role_arn"),
        )
        sfn_client.untag_resource(resourceArn=state_machine_arn, tagKeys=tags_to_remove)
        sfn_client.tag_resource(
            resourceArn=state_machine_arn,
            tags=ansible_dict_to_boto3_tag_list(tags_to_add, tag_name_key_name="key", tag_value_key_name="value"),
        )

        module.exit_json(changed=True, state_machine_arn=state_machine_arn)


def compare_tags(state_machine_arn, sfn_client, module):
    new_tags = module.params.get("tags")
    current_tags = sfn_client.list_tags_for_resource(resourceArn=state_machine_arn).get("tags")
    return compare_aws_tags(
        boto3_tag_list_to_ansible_dict(current_tags), new_tags if new_tags else {}, module.params.get("purge_tags")
    )


def params_changed(state_machine_arn, sfn_client, module):
    """
    Check whether the state machine definition or IAM Role ARN is different
    from the existing state machine parameters.
    """
    current = sfn_client.describe_state_machine(stateMachineArn=state_machine_arn)
    return current.get("definition") != module.params.get("definition") or current.get("roleArn") != module.params.get(
        "role_arn"
    )


def get_state_machine_arn(sfn_client, module):
    """
    Finds the state machine ARN based on the name parameter. Returns None if
    there is no state machine with this name.
    """
    target_name = module.params.get("name")
    all_state_machines = sfn_client.list_state_machines(aws_retry=True).get("stateMachines")

    for state_machine in all_state_machines:
        if state_machine.get("name") == target_name:
            return state_machine.get("stateMachineArn")


def check_mode(module, msg="", changed=False):
    if module.check_mode:
        module.exit_json(changed=changed, output=msg)


def main():
    module_args = dict(
        name=dict(type="str", required=True),
        definition=dict(type="json"),
        role_arn=dict(type="str"),
        state=dict(choices=["present", "absent"], default="present"),
        tags=dict(default=None, type="dict", aliases=["resource_tags"]),
        purge_tags=dict(default=True, type="bool"),
    )
    module = AnsibleAWSModule(
        argument_spec=module_args,
        required_if=[("state", "present", ["role_arn"]), ("state", "present", ["definition"])],
        supports_check_mode=True,
    )

    sfn_client = module.client("stepfunctions", retry_decorator=AWSRetry.jittered_backoff(retries=5))
    state = module.params.get("state")

    try:
        manage_state_machine(state, sfn_client, module)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to manage state machine")


if __name__ == "__main__":
    main()
