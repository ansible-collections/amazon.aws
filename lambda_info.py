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
  - Use module M(community.aws.lambda) to manage the lambda function itself, M(community.aws.lambda_alias) to manage function aliases and
    M(community.aws.lambda_event) to manage lambda event source mappings.


options:
  query:
    description:
      - Specifies the resource type for which to gather information.  Leave blank to retrieve all information.
    choices: [ "aliases", "all", "config", "mappings", "policy", "versions" ]
    default: "all"
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
requirements:
    - boto3
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
# List all lambda function versions
- name: List all function
  community.aws.lambda_info:
    query: all
    max_items: 20
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


def alias_details(client, module):
    """
    Returns list of aliases for a specified function.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

    lambda_info = dict()

    function_name = module.params.get('function_name')
    if function_name:
        params = dict()
        if module.params.get('max_items'):
            params['MaxItems'] = module.params.get('max_items')

        if module.params.get('next_marker'):
            params['Marker'] = module.params.get('next_marker')
        try:
            lambda_info.update(aliases=client.list_aliases(FunctionName=function_name, **params)['Aliases'])
        except is_boto3_error_code('ResourceNotFoundException'):
            lambda_info.update(aliases=[])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Trying to get aliases")
    else:
        module.fail_json(msg='Parameter function_name required for query=aliases.')

    return {function_name: camel_dict_to_snake_dict(lambda_info)}


def all_details(client, module):
    """
    Returns all lambda related facts.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

    if module.params.get('max_items') or module.params.get('next_marker'):
        module.fail_json(msg='Cannot specify max_items nor next_marker for query=all.')

    lambda_info = dict()

    function_name = module.params.get('function_name')
    if function_name:
        lambda_info[function_name] = {}
        lambda_info[function_name].update(config_details(client, module)[function_name])
        lambda_info[function_name].update(alias_details(client, module)[function_name])
        lambda_info[function_name].update(policy_details(client, module)[function_name])
        lambda_info[function_name].update(version_details(client, module)[function_name])
        lambda_info[function_name].update(mapping_details(client, module)[function_name])
    else:
        lambda_info.update(config_details(client, module))

    return lambda_info


def config_details(client, module):
    """
    Returns configuration details for one or all lambda functions.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

    lambda_info = dict()

    function_name = module.params.get('function_name')
    if function_name:
        try:
            lambda_info.update(client.get_function_configuration(FunctionName=function_name))
        except is_boto3_error_code('ResourceNotFoundException'):
            lambda_info.update(function={})
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Trying to get {0} configuration".format(function_name))
    else:
        params = dict()
        if module.params.get('max_items'):
            params['MaxItems'] = module.params.get('max_items')

        if module.params.get('next_marker'):
            params['Marker'] = module.params.get('next_marker')

        try:
            lambda_info.update(function_list=client.list_functions(**params)['Functions'])
        except is_boto3_error_code('ResourceNotFoundException'):
            lambda_info.update(function_list=[])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Trying to get function list")

        functions = dict()
        for func in lambda_info.pop('function_list', []):
            functions[func['FunctionName']] = camel_dict_to_snake_dict(func)
        return functions

    return {function_name: camel_dict_to_snake_dict(lambda_info)}


def mapping_details(client, module):
    """
    Returns all lambda event source mappings.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

    lambda_info = dict()
    params = dict()
    function_name = module.params.get('function_name')

    if function_name:
        params['FunctionName'] = module.params.get('function_name')

    if module.params.get('event_source_arn'):
        params['EventSourceArn'] = module.params.get('event_source_arn')

    if module.params.get('max_items'):
        params['MaxItems'] = module.params.get('max_items')

    if module.params.get('next_marker'):
        params['Marker'] = module.params.get('next_marker')

    try:
        lambda_info.update(mappings=client.list_event_source_mappings(**params)['EventSourceMappings'])
    except is_boto3_error_code('ResourceNotFoundException'):
        lambda_info.update(mappings=[])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Trying to get source event mappings")

    if function_name:
        return {function_name: camel_dict_to_snake_dict(lambda_info)}

    return camel_dict_to_snake_dict(lambda_info)


def policy_details(client, module):
    """
    Returns policy attached to a lambda function.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

    if module.params.get('max_items') or module.params.get('next_marker'):
        module.fail_json(msg='Cannot specify max_items nor next_marker for query=policy.')

    lambda_info = dict()

    function_name = module.params.get('function_name')
    if function_name:
        try:
            # get_policy returns a JSON string so must convert to dict before reassigning to its key
            lambda_info.update(policy=json.loads(client.get_policy(FunctionName=function_name)['Policy']))
        except is_boto3_error_code('ResourceNotFoundException'):
            lambda_info.update(policy={})
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Trying to get {0} policy".format(function_name))
    else:
        module.fail_json(msg='Parameter function_name required for query=policy.')

    return {function_name: camel_dict_to_snake_dict(lambda_info)}


def version_details(client, module):
    """
    Returns all lambda function versions.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

    lambda_info = dict()

    function_name = module.params.get('function_name')
    if function_name:
        params = dict()
        if module.params.get('max_items'):
            params['MaxItems'] = module.params.get('max_items')

        if module.params.get('next_marker'):
            params['Marker'] = module.params.get('next_marker')

        try:
            lambda_info.update(versions=client.list_versions_by_function(FunctionName=function_name, **params)['Versions'])
        except is_boto3_error_code('ResourceNotFoundException'):
            lambda_info.update(versions=[])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Trying to get {0} versions".format(function_name))
    else:
        module.fail_json(msg='Parameter function_name required for query=versions.')

    return {function_name: camel_dict_to_snake_dict(lambda_info)}


def main():
    """
    Main entry point.

    :return dict: ansible facts
    """
    argument_spec = dict(
        function_name=dict(required=False, default=None, aliases=['function', 'name']),
        query=dict(required=False, choices=['aliases', 'all', 'config', 'mappings', 'policy', 'versions'], default='all'),
        event_source_arn=dict(required=False, default=None)
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

    client = module.client('lambda')

    invocations = dict(
        aliases='alias_details',
        all='all_details',
        config='config_details',
        mappings='mapping_details',
        policy='policy_details',
        versions='version_details',
    )

    this_module_function = globals()[invocations[module.params['query']]]
    all_facts = fix_return(this_module_function(client, module))

    results = dict(function=all_facts, changed=False)

    if module.check_mode:
        results['msg'] = 'Check mode set but ignored for fact gathering only.'

    module.exit_json(**results)


if __name__ == '__main__':
    main()
