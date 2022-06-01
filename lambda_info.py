#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: lambda_info
version_added: 1.0.0
short_description: Gathers AWS Lambda function details
description:
  - Gathers various details related to Lambda functions, including aliases, versions and event source mappings.
  - Use module M(community.aws.lambda) to manage the lambda function itself, M(community.aws.lambda_alias) to manage function aliases,
    M(community.aws.lambda_event) to manage lambda event source mappings, and M(community.aws.lambda_policy) to manage policy statements.


options:
  query:
    description:
      - Specifies the resource type for which to gather information.
      - Defaults to C(all) when I(function_name) is specified.
      - Defaults to C(config) when I(function_name) is NOT specified.
    choices: [ "aliases", "all", "config", "mappings", "policy", "versions", "tags" ]
    type: str
  function_name:
    description:
      - The name of the lambda function for which information is requested.
    aliases: [ "function", "name"]
    type: str
  event_source_arn:
    description:
      - When I(query=mappings), this is the Amazon Resource Name (ARN) of the Amazon Kinesis or DynamoDB stream.
    type: str
author: Pierre Jodouin (@pjodouin)
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
---
# Simple example of listing all info for a function
- name: List all for a specific function
  community.aws.lambda_info:
    query: all
    function_name: myFunction
  register: my_function_details

# List all versions of a function
- name: List function versions
  community.aws.lambda_info:
    query: versions
    function_name: myFunction
  register: my_function_versions

# List all info for all functions
- name: List all functions
  community.aws.lambda_info:
    query: all
  register: output

- name: show Lambda information
  ansible.builtin.debug:
    msg: "{{ output['function'] }}"
'''

RETURN = '''
---
function:
    description: lambda function list
    returned: success
    type: dict
function.TheName:
    description: lambda function information, including event, mapping, and version information
    returned: success
    type: dict
'''
import json
import datetime
import re

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry


@AWSRetry.jittered_backoff()
def _paginate(client, function, **params):
    paginator = client.get_paginator(function)
    return paginator.paginate(**params).build_full_result()


def fix_return(node):
    """
    fixup returned dictionary

    :param node:
    :return:
    """

    if isinstance(node, datetime.datetime):
        node_value = str(node)

    elif isinstance(node, list):
        node_value = [fix_return(item) for item in node]

    elif isinstance(node, dict):
        node_value = dict([(item, fix_return(node[item])) for item in node.keys()])

    else:
        node_value = node

    return node_value


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
        lambda_info.update(aliases=_paginate(client, 'list_aliases', FunctionName=function_name)['Aliases'])
    except is_boto3_error_code('ResourceNotFoundException'):
        lambda_info.update(aliases=[])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Trying to get aliases")

    return camel_dict_to_snake_dict(lambda_info)


def list_lambdas(client, module):
    """
    Returns queried facts for a specified function (or all functions).

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

    function_name = module.params.get('function_name')
    if function_name:
        # Function name is specified - retrieve info on that function
        function_names = [function_name]

    else:
        # Function name is not specified - retrieve all function names
        all_function_info = _paginate(client, 'list_functions')['Functions']
        function_names = [function_info['FunctionName'] for function_info in all_function_info]

    query = module.params['query']
    lambdas = dict()

    for function_name in function_names:
        lambdas[function_name] = {}

        if query == 'all':
            lambdas[function_name].update(config_details(client, module, function_name))
            lambdas[function_name].update(alias_details(client, module, function_name))
            lambdas[function_name].update(policy_details(client, module, function_name))
            lambdas[function_name].update(version_details(client, module, function_name))
            lambdas[function_name].update(mapping_details(client, module, function_name))
            lambdas[function_name].update(tags_details(client, module, function_name))

        elif query == 'config':
            lambdas[function_name].update(config_details(client, module, function_name))

        elif query == 'aliases':
            lambdas[function_name].update(alias_details(client, module, function_name))

        elif query == 'policy':
            lambdas[function_name].update(policy_details(client, module, function_name))

        elif query == 'versions':
            lambdas[function_name].update(version_details(client, module, function_name))

        elif query == 'mappings':
            lambdas[function_name].update(mapping_details(client, module, function_name))

        elif query == 'tags':
            lambdas[function_name].update(tags_details(client, module, function_name))

    return lambdas


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
    except is_boto3_error_code('ResourceNotFoundException'):
        lambda_info.update(function={})
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Trying to get {0} configuration".format(function_name))

    return camel_dict_to_snake_dict(lambda_info)


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

    params['FunctionName'] = function_name

    if module.params.get('event_source_arn'):
        params['EventSourceArn'] = module.params.get('event_source_arn')

    try:
        lambda_info.update(mappings=_paginate(client, 'list_event_source_mappings', **params)['EventSourceMappings'])
    except is_boto3_error_code('ResourceNotFoundException'):
        lambda_info.update(mappings=[])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
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
        lambda_info.update(policy=json.loads(client.get_policy(aws_retry=True, FunctionName=function_name)['Policy']))
    except is_boto3_error_code('ResourceNotFoundException'):
        lambda_info.update(policy={})
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Trying to get {0} policy".format(function_name))

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
        lambda_info.update(versions=_paginate(client, 'list_versions_by_function', FunctionName=function_name)['Versions'])
    except is_boto3_error_code('ResourceNotFoundException'):
        lambda_info.update(versions=[])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Trying to get {0} versions".format(function_name))

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
        lambda_info.update(tags=client.get_function(aws_retry=True, FunctionName=function_name).get('Tags', {}))
    except is_boto3_error_code('ResourceNotFoundException'):
        lambda_info.update(function={})
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Trying to get {0} tags".format(function_name))

    return camel_dict_to_snake_dict(lambda_info)


def main():
    """
    Main entry point.

    :return dict: ansible facts
    """
    argument_spec = dict(
        function_name=dict(required=False, default=None, aliases=['function', 'name']),
        query=dict(required=False, choices=['aliases', 'all', 'config', 'mappings', 'policy', 'versions', 'tags'], default=None),
        event_source_arn=dict(required=False, default=None),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[],
        required_together=[]
    )

    # validate function_name if present
    function_name = module.params['function_name']
    if function_name:
        if not re.search(r"^[\w\-:]+$", function_name):
            module.fail_json(
                msg='Function name {0} is invalid. Names must contain only alphanumeric characters and hyphens.'.format(function_name)
            )
        if len(function_name) > 64:
            module.fail_json(msg='Function name "{0}" exceeds 64 character limit'.format(function_name))

    # create default values for query if not specified.
    # if function name exists, query should default to 'all'.
    # if function name does not exist, query should default to 'config' to limit the runtime when listing all lambdas.
    if not module.params.get('query'):
        if function_name:
            module.params['query'] = 'all'
        else:
            module.params['query'] = 'config'

    client = module.client('lambda', retry_decorator=AWSRetry.jittered_backoff())

    all_facts = fix_return(list_lambdas(client, module))

    results = dict(function=all_facts, changed=False)

    if module.check_mode:
        results['msg'] = 'Check mode set but ignored for fact gathering only.'

    module.exit_json(**results)


if __name__ == '__main__':
    main()
