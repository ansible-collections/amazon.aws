#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: lambda_info
version_added: 5.0.0
short_description: Gathers AWS Lambda function details
description:
  - Gathers various details related to Lambda functions, including aliases, versions and event source mappings.
  - Use module M(amazon.aws.lambda) to manage the lambda function itself, M(amazon.aws.lambda_alias) to manage function aliases,
    M(amazon.aws.lambda_event) to manage lambda event source mappings, and M(amazon.aws.lambda_policy) to manage policy statements.
  - This module was originally added to C(community.aws) in release 1.0.0.
options:
  query:
    description:
      - Specifies the resource type for which to gather information.
      - Defaults to V(all) when O(function_name) is specified.
      - Defaults to V(config) when O(function_name) is NOT specified.
    choices: [ "aliases", "all", "config", "mappings", "policy", "versions", "tags" ]
    type: str
  function_name:
    description:
      - The name of the lambda function for which information is requested.
    aliases: [ "function", "name"]
    type: str
  event_source_arn:
    description:
      - When O(query=mappings), this is the Amazon Resource Name (ARN) of the Amazon Kinesis or DynamoDB stream.
    type: str
author:
  - Pierre Jodouin (@pjodouin)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
---
# Simple example of listing all info for a function
- name: List all for a specific function
  amazon.aws.lambda_info:
    query: all
    function_name: myFunction
  register: my_function_details

# Get basic information about AWS Lambda Functions in the current region
- name: List Lambda Functions
  amazon.aws.lambda_info:
  register: lambda_functions

# List all versions of a function
- name: List function versions
  amazon.aws.lambda_info:
    query: versions
    function_name: myFunction
  register: my_function_versions

# List all info for all functions
- name: List all functions
  amazon.aws.lambda_info:
    query: all
  register: output

- name: show Lambda information
  ansible.builtin.debug:
    msg: "{{ output['function'] }}"
"""

RETURN = r"""
---
function:
    description:
        - Lambda function list.
        - RV(function) has been deprecated in will be removed in the next major release after 2025-01-01.
    returned: success
    type: dict
function.TheName:
    description:
        - Lambda function information, including event, mapping, and version information.
        - RV(function) has been deprecated in will be removed in the next major release after 2025-01-01.
    returned: success
    type: dict
functions:
    description: List of information for each lambda function matching the query.
    returned: always
    type: list
    elements: dict
    version_added: 4.1.0
    version_added_collection: community.aws
    contains:
        aliases:
            description: The aliases associated with the function.
            returned: when O(query=aliases) or O(query=all)
            type: list
            elements: str
        architectures:
            description: The architectures supported by the function.
            returned: success
            type: list
            elements: str
            sample: ['arm64']
        code_sha256:
            description: The SHA256 hash of the function's deployment package.
            returned: success
            type: str
            sample: 'zOAGfF5JLFuzZoSNirUtOrQp+S341IOA3BcoXXoaIaU='
        code_size:
            description: The size of the function's deployment package in bytes.
            returned: success
            type: int
            sample: 123
        dead_letter_config:
            description: The function's dead letter queue.
            returned: when the function has a dead letter queue configured
            type: dict
            sample: { 'target_arn': arn:aws:lambda:us-east-1:123456789012:function:myFunction:1 }
            contains:
                target_arn:
                    description: The ARN of an SQS queue or SNS topic.
                    returned: when the function has a dead letter queue configured
                    type: str
                    sample: arn:aws:lambda:us-east-1:123456789012:function:myFunction:1
        description:
            description: The function's description.
            returned: success
            type: str
            sample: 'My function'
        ephermal_storage:
            description: The size of the function /tmp directory in MB.
            type: dict
            contains:
                size:
                    description: The size of the function /tmp directory.
                    type: int
                    returned: always
                    sample: 512
        environment:
            description: The function's environment variables.
            returned: when environment variables exist
            type: dict
            contains:
                variables:
                    description: Environment variable key-value pairs.
                    returned: when environment variables exist
                    type: dict
                    sample: {'key': 'value'}
                error:
                    description: Error message for environment variables that could not be applied.
                    returned: when there is an error applying environment variables
                    type: dict
                    contains:
                        error_code:
                            description: The error code.
                            returned: when there is an error applying environment variables
                            type: str
                        message:
                            description: The error message.
                            returned: when there is an error applying environment variables
                            type: str
        function_arn:
            description: The function's Amazon Resource Name (ARN).
            returned: on success
            type: str
            sample: 'arn:aws:lambda:us-east-1:123456789012:function:myFunction:1'
        function_name:
            description: The function's name.
            returned: on success
            type: str
            sample: 'myFunction'
        handler:
            description: The function Lambda calls to begin executing your function.
            returned: on success
            type: str
            sample: 'index.handler'
        last_modified:
            description: The date and time that the function was last updated, in ISO-8601 format (YYYY-MM-DDThh:mm:ssTZD).
            returned: on success
            type: str
            sample: '2017-08-01T00:00:00.000+0000'
        mappings:
            description: List of configuration information for each event source mapping.
            returned: when O(query=all) or O(query=mappings)
            type: list
            elements: dict
            contains:
                uuid:
                    description: The AWS Lambda assigned opaque identifier for the mapping.
                    returned: on success
                    type: str
                batch_size:
                    description: The largest number of records that AWS Lambda will retrieve from the event source at the time of invoking the function.
                    returned: on success
                    type: int
                event_source_arn:
                    description: The ARN of the Amazon Kinesis or DyanmoDB stream that is the source of events.
                    returned: on success
                    type: str
                function_arn:
                    description: The Lambda function to invoke when AWS Lambda detects an event on the poll-based source.
                    returned: on success
                    type: str
                last_modified:
                    description: The UTC time string indicating the last time the event mapping was updated.
                    returned: on success
                    type: str
                last_processing_result:
                    description: The result of the last AWS Lambda invocation of your Lambda function.
                    returned: on success
                    type: str
                state:
                    description: The state of the event source mapping.
                    returned: on success
                    type: str
                state_transition_reason:
                    description: The reason the event source mapping is in its current state.
                    returned: on success
                    type: str
        memory_size:
            description: The memory allocated to the function.
            returned: on success
            type: int
            sample: 128
        package_type:
            description: The type of deployment package.
            type: str
            returned: always
            sample: "Zip"
        policy:
            description: The policy associated with the function.
            returned: when O(query=all) or O(query=policy)
            type: dict
        revision_id:
            description: The latest updated revision of the function or alias.
            returned: on success
            type: str
            sample: 'a2x9886d-d48a-4a0c-ab64-82abc005x80c'
        role:
            description: The function's execution role.
            returned: on success
            type: str
            sample: 'arn:aws:iam::123456789012:role/lambda_basic_execution'
        runtime:
            description: The funtime environment for the Lambda function.
            returned: on success
            type: str
            sample: 'nodejs6.10'
        runtime_version_config:
            description: The ARN of the runtime and any errors that occured.
            type: dict
            contains:
                runtime_version_arn:
                    description: The ARN of the runtime version you want the function to use.
                    type: str
                    returned: always
                    sample: "arn:aws:lambda:us-west-2::runtime:123456789012"
        snap_start:
            description: Snapshot of the initialized execution environment when you publish a function version.
            type: dict
            contains:
                apply_on:
                    description: When set to V(PublishedVersions), Lambda creates a snapshot of the execution environment when you publish a function version.
                    type: str
                    sample: "None"
                    returned: always
                optimization_status:
                    description: This element indicates whether SnapStart is activated for the specified function version.
                    type: str
                    returned: always
                    sample: "Off"
        tracing_config:
            description: The function's AWS X-Ray tracing configuration.
            returned: on success
            type: dict
            sample: { 'mode': 'Active' }
            contains:
                mode:
                    description: The tracing mode.
                    returned: on success
                    type: str
                    sample: 'Active'
        timeout:
            description: The amount of time that Lambda allows a function to run before terminating it.
            returned: on success
            type: int
            sample: 3
        version:
            description: The version of the Lambda function.
            returned: on success
            type: str
            sample: '1'
        versions:
            description: List of Lambda function versions.
            returned: when O(query=all) or O(query=versions)
            type: list
            elements: dict
        vpc_config:
            description: The function's networking configuration.
            returned: on success
            type: dict
            sample: {
            'security_group_ids': [],
            'subnet_ids': [],
            'vpc_id': '123'
            }
"""

import json
import re

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


@AWSRetry.jittered_backoff()
def _paginate(client, function, **params):
    paginator = client.get_paginator(function)
    return paginator.paginate(**params).build_full_result()


def alias_details(client, module, function_name):
    """
    Returns list of aliases for a specified function.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :param function_name (str): Name of Lambda function to query
    :return dict:
    """

    lambda_info = dict()

    try:
        lambda_info.update(aliases=_paginate(client, "list_aliases", FunctionName=function_name)["Aliases"])
    except is_boto3_error_code("ResourceNotFoundException"):
        lambda_info.update(aliases=[])
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Trying to get aliases")

    return camel_dict_to_snake_dict(lambda_info)


def _get_query(query, function_name):
    # create default values for query if not specified.
    # if function name exists, query should default to 'all'.
    # if function name does not exist, query should default to 'config' to limit the runtime when listing all lambdas.
    if query:
        return query
    if function_name:
        return "all"
    return "config"


def list_functions(client, module):
    """
    Returns queried facts for a specified function (or all functions).

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    """

    function_name = module.params.get("function_name")
    if function_name:
        # Function name is specified - retrieve info on that function
        function_names = [function_name]

    else:
        # Function name is not specified - retrieve all function names
        all_function_info = _paginate(client, "list_functions")["Functions"]
        function_names = [function_info["FunctionName"] for function_info in all_function_info]

    query = _get_query(module.params["query"], function_name)
    functions = []

    # keep returning deprecated response (dict of dicts) until removed
    all_facts = {}

    for function_name in function_names:
        function = {}

        # query = 'config' returns info such as FunctionName, FunctionArn, Description, etc
        # these details should be returned regardless of the query
        function.update(config_details(client, module, function_name))

        if query in ["all", "aliases"]:
            function.update(alias_details(client, module, function_name))

        if query in ["all", "policy"]:
            function.update(policy_details(client, module, function_name))

        if query in ["all", "versions"]:
            function.update(version_details(client, module, function_name))

        if query in ["all", "mappings"]:
            function.update(mapping_details(client, module, function_name))

        if query in ["all", "tags"]:
            function.update(tags_details(client, module, function_name))

        all_facts[function["function_name"]] = function

        # add current lambda to list of lambdas
        functions.append(function)

    # return info
    module.exit_json(function=all_facts, functions=functions, changed=False)


def config_details(client, module, function_name):
    """
    Returns configuration details for a lambda function.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :param function_name (str): Name of Lambda function to query
    :return dict:
    """

    lambda_info = dict()

    try:
        lambda_info.update(client.get_function_configuration(aws_retry=True, FunctionName=function_name))
    except is_boto3_error_code("ResourceNotFoundException"):
        lambda_info.update(function={})
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg=f"Trying to get {function_name} configuration")

    if "Environment" in lambda_info and "Variables" in lambda_info["Environment"]:
        env_vars = lambda_info["Environment"]["Variables"]
        snaked_lambda_info = camel_dict_to_snake_dict(lambda_info)
        snaked_lambda_info["environment"]["variables"] = env_vars
    else:
        snaked_lambda_info = camel_dict_to_snake_dict(lambda_info)

    return snaked_lambda_info


def mapping_details(client, module, function_name):
    """
    Returns all lambda event source mappings.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :param function_name (str): Name of Lambda function to query
    :return dict:
    """

    lambda_info = dict()
    params = dict()

    params["FunctionName"] = function_name

    if module.params.get("event_source_arn"):
        params["EventSourceArn"] = module.params.get("event_source_arn")

    try:
        lambda_info.update(mappings=_paginate(client, "list_event_source_mappings", **params)["EventSourceMappings"])
    except is_boto3_error_code("ResourceNotFoundException"):
        lambda_info.update(mappings=[])
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Trying to get source event mappings")

    return camel_dict_to_snake_dict(lambda_info)


def policy_details(client, module, function_name):
    """
    Returns policy attached to a lambda function.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :param function_name (str): Name of Lambda function to query
    :return dict:
    """

    lambda_info = dict()

    try:
        # get_policy returns a JSON string so must convert to dict before reassigning to its key
        lambda_info.update(policy=json.loads(client.get_policy(aws_retry=True, FunctionName=function_name)["Policy"]))
    except is_boto3_error_code("ResourceNotFoundException"):
        lambda_info.update(policy={})
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg=f"Trying to get {function_name} policy")

    return camel_dict_to_snake_dict(lambda_info)


def version_details(client, module, function_name):
    """
    Returns all lambda function versions.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :param function_name (str): Name of Lambda function to query
    :return dict:
    """

    lambda_info = dict()

    try:
        lambda_info.update(
            versions=_paginate(client, "list_versions_by_function", FunctionName=function_name)["Versions"]
        )
    except is_boto3_error_code("ResourceNotFoundException"):
        lambda_info.update(versions=[])
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg=f"Trying to get {function_name} versions")

    return camel_dict_to_snake_dict(lambda_info)


def tags_details(client, module, function_name):
    """
    Returns tag details for a lambda function.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :param function_name (str): Name of Lambda function to query
    :return dict:
    """

    lambda_info = dict()

    try:
        lambda_info.update(tags=client.get_function(aws_retry=True, FunctionName=function_name).get("Tags", {}))
    except is_boto3_error_code("ResourceNotFoundException"):
        lambda_info.update(function={})
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg=f"Trying to get {function_name} tags")

    return camel_dict_to_snake_dict(lambda_info)


def main():
    """
    Main entry point.

    :return dict: ansible facts
    """
    argument_spec = dict(
        function_name=dict(required=False, default=None, aliases=["function", "name"]),
        query=dict(
            required=False, choices=["aliases", "all", "config", "mappings", "policy", "versions", "tags"], default=None
        ),
        event_source_arn=dict(required=False, default=None),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec, supports_check_mode=True, mutually_exclusive=[], required_together=[]
    )

    # validate function_name if present
    function_name = module.params["function_name"]
    if function_name:
        if not re.search(r"^[\w\-:]+$", function_name):
            module.fail_json(
                msg=f"Function name {function_name} is invalid. Names must contain only alphanumeric characters and hyphens.",
            )
        if len(function_name) > 64:
            module.fail_json(msg=f'Function name "{function_name}" exceeds 64 character limit')

    client = module.client("lambda", retry_decorator=AWSRetry.jittered_backoff())

    # Deprecate previous return key of `function`, as it was a dict of dicts, as opposed to a list of dicts
    module.deprecate(
        (
            "The returned key 'function', which returned a dictionary of dictionaries, is deprecated and will be"
            " replaced by 'functions', which returns a list of dictionaries. Both keys are returned for now."
        ),
        date="2025-01-01",
        collection_name="amazon.aws",
    )

    list_functions(client, module)


if __name__ == "__main__":
    main()
