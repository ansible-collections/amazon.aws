#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: cloudformation_info
version_added: 1.0.0
short_description: Obtain information about an AWS CloudFormation stack
description:
  - Gets information about an AWS CloudFormation stack.
author:
    - Justin Menga (@jmenga)
    - Kevin Coming (@waffie1)
options:
    stack_name:
        description:
          - The name or id of the CloudFormation stack. Gathers information on all stacks by default.
        type: str
    all_facts:
        description:
            - Get all stack information for the stack.
        type: bool
        default: false
    stack_events:
        description:
            - Get stack events for the stack.
        type: bool
        default: false
    stack_template:
        description:
            - Get stack template body for the stack.
        type: bool
        default: false
    stack_resources:
        description:
            - Get stack resources for the stack.
        type: bool
        default: false
    stack_policy:
        description:
            - Get stack policy for the stack.
        type: bool
        default: false
    stack_change_sets:
        description:
            - Get stack change sets for the stack
        type: bool
        default: false
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Get information on all stacks
  amazon.aws.cloudformation_info:
  register: all_stacks_output

- name: Get summary information about a stack
  amazon.aws.cloudformation_info:
    stack_name: my-cloudformation-stack
  register: output

- debug:
    msg: "{{ output['cloudformation']['my-cloudformation-stack'] }}"

# Get stack outputs, when you have the stack name available as a fact
- set_fact:
    stack_name: my-awesome-stack

- amazon.aws.cloudformation_info:
    stack_name: "{{ stack_name }}"
  register: my_stack

- debug:
    msg: "{{ my_stack.cloudformation[stack_name].stack_outputs }}"

# Get all stack information about a stack
- amazon.aws.cloudformation_info:
    stack_name: my-cloudformation-stack
    all_facts: true

# Get stack resource and stack policy information about a stack
- amazon.aws.cloudformation_info:
    stack_name: my-cloudformation-stack
    stack_resources: true
    stack_policy: true

# Fail if the stack doesn't exist
- name: try to get info about a stack but fail if it doesn't exist
  amazon.aws.cloudformation_info:
    stack_name: nonexistent-stack
    all_facts: true
  failed_when: cloudformation['nonexistent-stack'] is undefined
"""

RETURN = r"""
cloudformation:
    description:
        - Dictionary of dictionaries containing info of stack(s).
        - Keys are stack_name(s).
    returned: always
    type: dict
    contains:
        stack_description:
            description: Summary facts about the stack.
            returned: if the stack exists
            type: dict
            contains:
                capabilities:
                    description: The capabilities allowed in the stack.
                    returned: always
                    type: list
                    elements: str
                creation_time:
                    description: The time at which the stack was created.
                    returned: if stack exists
                    type: str
                deletion_time:
                    description: The time at which the stack was deleted.
                    returned: if stack was deleted
                    type: str
                description:
                    description: The user-defined description associated with the stack.
                    returned: always
                    type: str
                disable_rollback:
                    description: Whether or not rollback on stack creation failures is enabled.
                    returned: always
                    type: bool
                drift_information:
                    description: Information about whether a stack's actual configuration differs, or has drifted, from it's expected configuration,
                        as defined in the stack template and any values specified as template parameters.
                    returned: always
                    type: dict
                    contains:
                        stack_drift_status:
                            description: Status of the stack's actual configuration compared to its expected template configuration.
                            returned: always
                            type: str
                        last_check_timestamp:
                            description: Most recent time when a drift detection operation was initiated on the stack,
                                or any of its individual resources that support drift detection.
                            returned: if a drift was detected
                            type: str
                enable_termination_protection:
                    description: Whether termination protection is enabled for the stack.
                    returned: always
                    type: bool
                notification_arns:
                    description: Amazon SNS topic ARNs to which stack related events are published.
                    returned: always
                    type: list
                    elements: str
                outputs:
                    description: A list of output dicts.
                    returned: always
                    type: list
                    elements: dict
                    contains:
                        output_key:
                            description: The key associated with the output.
                            returned: always
                            type: str
                        output_value:
                            description: The value associated with the output.
                            returned: always
                            type: str
                parameters:
                    description: A list of parameter dicts.
                    returned: always
                    type: list
                    elements: dict
                    contains:
                        parameter_key:
                            description: The key associated with the parameter.
                            returned: always
                            type: str
                        parameter_value:
                            description: The value associated with the parameter.
                            returned: always
                            type: str
                rollback_configuration:
                    description: The rollback triggers for CloudFormation to monitor during stack creation and updating operations.
                    returned: always
                    type: dict
                    contains:
                        rollback_triggers:
                            description: The triggers to monitor during stack creation or update actions.
                            returned: when rollback triggers exist
                            type: list
                            elements: dict
                            contains:
                                arn:
                                    description: The ARN of the rollback trigger.
                                    returned: always
                                    type: str
                                type:
                                    description: The resource type of the rollback trigger.
                                    returned: always
                                    type: str
                stack_id:
                    description: The unique ID of the stack.
                    returned: always
                    type: str
                stack_name:
                    description: The name of the stack.
                    returned: always
                    type: str
                stack_status:
                    description: The status of the stack.
                    returned: always
                    type: str
                tags:
                    description: A list of tags associated with the stack.
                    returned: always
                    type: list
                    elements: dict
                    contains:
                        key:
                            description: Key of tag.
                            returned: always
                            type: str
                        value:
                            description: Value of tag.
                            returned: always
                            type: str
        stack_outputs:
            description: Dictionary of stack outputs keyed by the value of each output 'OutputKey' parameter and corresponding value of each
                        output 'OutputValue' parameter.
            returned: if the stack exists
            type: dict
            sample: { ApplicationDatabaseName: dazvlpr01xj55a.ap-southeast-2.rds.amazonaws.com }
        stack_parameters:
            description: Dictionary of stack parameters keyed by the value of each parameter 'ParameterKey' parameter and corresponding value of
                        each parameter 'ParameterValue' parameter.
            returned: if the stack exists
            type: dict
            sample:
                {
                    DatabaseEngine: mysql,
                    DatabasePassword: "***"
                }
        stack_events:
            description: All stack events for the stack.
            returned: only if O(all_facts) or O(stack_events) is V(true) and the stack exists
            type: list
        stack_policy:
            description: Describes the stack policy for the stack.
            returned: only if O(all_facts) or O(stack_policy) is V(true) and the stack exists
            type: dict
        stack_template:
            description: Describes the stack template for the stack.
            returned: only if O(all_facts) or O(stack_policy) is V(true) and the stack exists
            type: dict
        stack_resource_list:
            description: Describes stack resources for the stack.
            returned: only if O(all_facts) or O(stack_policy) is V(true) and the stack exists
            type: list
        stack_resources:
            description: Dictionary of stack resources keyed by the value of each resource 'LogicalResourceId' parameter and corresponding value of each
                        resource 'PhysicalResourceId' parameter.
            returned: only if O(all_facts) or O(stack_policy) is V(true) and the stack exists
            type: dict
            sample: {
                "AutoScalingGroup": "dev-someapp-AutoscalingGroup-1SKEXXBCAN0S7",
                "AutoScalingSecurityGroup": "sg-abcd1234",
                "ApplicationDatabase": "dazvlpr01xj55a"
            }
        stack_change_sets:
            description: A list of stack change sets.  Each item in the list represents the details of a specific changeset.
            returned: only if O(all_facts) or O(stack_policy) is V(true) and the stack exists
            type: list
        stack_tags:
            description: Dictionary of key value pairs of tags.
            returned: only if O(all_facts) or O(stack_policy) is V(true) and the stack exists
            type: dict
            sample: {
                'TagOne': 'ValueOne',
                'TagTwo': 'ValueTwo'
            }
"""

import json

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_message
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict


class CloudFormationServiceManager:
    """Handles CloudFormation Services"""

    def __init__(self, module):
        self.module = module
        self.client = module.client("cloudformation")

    @AWSRetry.exponential_backoff(retries=5, delay=5)
    def describe_stacks_with_backoff(self, **kwargs):
        paginator = self.client.get_paginator("describe_stacks")
        return paginator.paginate(**kwargs).build_full_result()["Stacks"]

    def describe_stacks(self, stack_name=None):
        try:
            kwargs = {"StackName": stack_name} if stack_name else {}
            response = self.describe_stacks_with_backoff(**kwargs)
            if response is not None:
                return response
            self.module.fail_json(msg="Error describing stack(s) - an empty response was returned")
        except is_boto3_error_message("does not exist"):
            return {}
        except (
            botocore.exceptions.BotoCoreError,
            botocore.exceptions.ClientError,
        ) as e:  # pylint: disable=duplicate-except
            self.module.fail_json_aws(e, msg="Error describing stack " + stack_name)

    @AWSRetry.exponential_backoff(retries=5, delay=5)
    def list_stack_resources_with_backoff(self, stack_name):
        paginator = self.client.get_paginator("list_stack_resources")
        return paginator.paginate(StackName=stack_name).build_full_result()["StackResourceSummaries"]

    def list_stack_resources(self, stack_name):
        try:
            return self.list_stack_resources_with_backoff(stack_name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Error listing stack resources for stack " + stack_name)

    @AWSRetry.exponential_backoff(retries=5, delay=5)
    def describe_stack_events_with_backoff(self, stack_name):
        paginator = self.client.get_paginator("describe_stack_events")
        return paginator.paginate(StackName=stack_name).build_full_result()["StackEvents"]

    def describe_stack_events(self, stack_name):
        try:
            return self.describe_stack_events_with_backoff(stack_name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Error listing stack events for stack " + stack_name)

    @AWSRetry.exponential_backoff(retries=5, delay=5)
    def list_stack_change_sets_with_backoff(self, stack_name):
        paginator = self.client.get_paginator("list_change_sets")
        return paginator.paginate(StackName=stack_name).build_full_result()["Summaries"]

    @AWSRetry.exponential_backoff(retries=5, delay=5)
    def describe_stack_change_set_with_backoff(self, **kwargs):
        paginator = self.client.get_paginator("describe_change_set")
        return paginator.paginate(**kwargs).build_full_result()

    def describe_stack_change_sets(self, stack_name):
        changes = []
        try:
            change_sets = self.list_stack_change_sets_with_backoff(stack_name)
            for item in change_sets:
                changes.append(
                    self.describe_stack_change_set_with_backoff(
                        StackName=stack_name, ChangeSetName=item["ChangeSetName"]
                    )
                )
            return changes
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Error describing stack change sets for stack " + stack_name)

    @AWSRetry.exponential_backoff(retries=5, delay=5)
    def get_stack_policy_with_backoff(self, stack_name):
        return self.client.get_stack_policy(StackName=stack_name)

    def get_stack_policy(self, stack_name):
        try:
            response = self.get_stack_policy_with_backoff(stack_name)
            stack_policy = response.get("StackPolicyBody")
            if stack_policy:
                return json.loads(stack_policy)
            return dict()
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Error getting stack policy for stack " + stack_name)

    @AWSRetry.exponential_backoff(retries=5, delay=5)
    def get_template_with_backoff(self, stack_name):
        return self.client.get_template(StackName=stack_name)

    def get_template(self, stack_name):
        try:
            response = self.get_template_with_backoff(stack_name)
            return response.get("TemplateBody")
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Error getting stack template for stack " + stack_name)


def to_dict(items, key, value):
    """Transforms a list of items to a Key/Value dictionary"""
    if items:
        return dict(zip([i.get(key) for i in items], [i.get(value) for i in items]))
    else:
        return dict()


def main():
    argument_spec = dict(
        stack_name=dict(),
        all_facts=dict(required=False, default=False, type="bool"),
        stack_policy=dict(required=False, default=False, type="bool"),
        stack_events=dict(required=False, default=False, type="bool"),
        stack_resources=dict(required=False, default=False, type="bool"),
        stack_template=dict(required=False, default=False, type="bool"),
        stack_change_sets=dict(required=False, default=False, type="bool"),
    )
    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    service_mgr = CloudFormationServiceManager(module)

    result = {"cloudformation": {}}

    for stack_description in service_mgr.describe_stacks(module.params.get("stack_name")):
        facts = {"stack_description": stack_description}
        stack_name = stack_description.get("StackName")

        # Create stack output and stack parameter dictionaries
        if facts["stack_description"]:
            facts["stack_outputs"] = to_dict(facts["stack_description"].get("Outputs"), "OutputKey", "OutputValue")
            facts["stack_parameters"] = to_dict(
                facts["stack_description"].get("Parameters"), "ParameterKey", "ParameterValue"
            )
            facts["stack_tags"] = boto3_tag_list_to_ansible_dict(facts["stack_description"].get("Tags"))

        # Create optional stack outputs
        all_facts = module.params.get("all_facts")
        if all_facts or module.params.get("stack_resources"):
            facts["stack_resource_list"] = service_mgr.list_stack_resources(stack_name)
            facts["stack_resources"] = to_dict(
                facts.get("stack_resource_list"), "LogicalResourceId", "PhysicalResourceId"
            )
        if all_facts or module.params.get("stack_template"):
            facts["stack_template"] = service_mgr.get_template(stack_name)
        if all_facts or module.params.get("stack_policy"):
            facts["stack_policy"] = service_mgr.get_stack_policy(stack_name)
        if all_facts or module.params.get("stack_events"):
            facts["stack_events"] = service_mgr.describe_stack_events(stack_name)
        if all_facts or module.params.get("stack_change_sets"):
            facts["stack_change_sets"] = service_mgr.describe_stack_change_sets(stack_name)

        result["cloudformation"][stack_name] = camel_dict_to_snake_dict(
            facts,
            ignore_list=(
                "stack_outputs",
                "stack_parameters",
                "stack_policy",
                "stack_resources",
                "stack_tags",
                "stack_template",
            ),
        )
    module.exit_json(changed=False, **result)


if __name__ == "__main__":
    main()
