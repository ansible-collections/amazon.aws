#!/usr/bin/python
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
---
module: aws_ssm_parameter_store
version_added: 1.0.0
short_description: Manage key-value pairs in AWS SSM parameter store
description:
  - Manage key-value pairs in AWS SSM parameter store.
  - To retreive SSM parameters use the M(amazon.aws.aws_ssm_parameter) lookup
    plugin.
options:
  name:
    description:
      - Parameter key name.
    required: true
    type: str
  description:
    description:
      - Parameter key description.
    required: false
    type: str
  value:
    description:
      - Parameter value.
    required: false
    type: str
  state:
    description:
      - Creates or modifies an existing parameter.
      - Deletes a parameter.
    required: false
    choices: ['present', 'absent']
    default: present
    type: str
  string_type:
    description:
      - Parameter String type.
    required: false
    choices: ['String', 'StringList', 'SecureString']
    default: String
    type: str
    aliases: ['type']
  decryption:
    description:
      - Work with SecureString type to get plain text secrets
    type: bool
    required: false
    default: true
  key_id:
    description:
      - AWS KMS key to decrypt the secrets.
      - The default key (C(alias/aws/ssm)) is automatically generated the first
        time it's requested.
    required: false
    default: alias/aws/ssm
    type: str
  overwrite_value:
    description:
      - Option to overwrite an existing value if it already exists.
    required: false
    choices: ['never', 'changed', 'always']
    default: changed
    type: str
  tier:
    description:
      - Parameter store tier type.
    required: false
    choices: ['Standard', 'Advanced', 'Intelligent-Tiering']
    default: Standard
    type: str
    version_added: 1.5.0

author:
  - "Davinder Pal (@116davinder) <dpsangwal@gmail.com>"
  - "Nathan Webster (@nathanwebsterdotme)"
  - "Bill Wang (@ozbillwang) <ozbillwang@gmail.com>"
  - "Michael De La Rue (@mikedlr)"

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
'''

EXAMPLES = '''
- name: Create or update key/value pair in AWS SSM parameter store
  community.aws.aws_ssm_parameter_store:
    name: "Hello"
    description: "This is your first key"
    value: "World"

- name: Delete the key
  community.aws.aws_ssm_parameter_store:
    name: "Hello"
    state: absent

- name: Create or update secure key/value pair with default kms key (aws/ssm)
  community.aws.aws_ssm_parameter_store:
    name: "Hello"
    description: "This is your first key"
    string_type: "SecureString"
    value: "World"

- name: Create or update secure key/value pair with nominated kms key
  community.aws.aws_ssm_parameter_store:
    name: "Hello"
    description: "This is your first key"
    string_type: "SecureString"
    key_id: "alias/demo"
    value: "World"

- name: Always update a parameter store value and create a new version
  community.aws.aws_ssm_parameter_store:
    name: "overwrite_example"
    description: "This example will always overwrite the value"
    string_type: "String"
    value: "Test1234"
    overwrite_value: "always"

- name: Create or update key/value pair in AWS SSM parameter store with tier
  community.aws.aws_ssm_parameter_store:
    name: "Hello"
    description: "This is your first key"
    value: "World"
    tier: "Advanced"

- name: recommend to use with aws_ssm lookup plugin
  ansible.builtin.debug:
    msg: "{{ lookup('amazon.aws.aws_ssm', 'Hello') }}"
'''

RETURN = '''
parameter_metadata:
  type: dict
  description:
    - Information about a parameter.
    - Does not include the value of the parameter as this can be sensitive
      information.
  returned: success
  contains:
    data_type:
      type: str
      description: Parameter Data type.
      example: text
      returned: success
    description:
      type: str
      description: Parameter key description.
      example: This is your first key
      returned: success
    last_modified_date:
      type: str
      description: Time and date that the parameter was last modified.
      example: '2022-06-20T09:56:58.573000+00:00'
      returned: success
    last_modified_user:
      type: str
      description: ARN of the last user to modify the parameter.
      example: 'arn:aws:sts::123456789012:assumed-role/example-role/session=example'
      returned: success
    name:
      type: str
      description: Parameter key name.
      example: Hello
      returned: success
    policies:
      type: list
      description: A list of policies associated with a parameter.
      elements: dict
      returned: success
      contains:
        policy_text:
          type: str
          description: The JSON text of the policy.
          returned: success
        policy_type:
          type: str
          description: The type of policy.
          example: Expiration
          returned: success
        policy_status:
          type: str
          description: The status of the policy.
          example: Pending
          returned: success
    tier:
      type: str
      description: Parameter tier.
      example: Standard
      returned: success
    type:
      type: str
      description: Parameter type
      example: String
      returned: success
    version:
      type: int
      description: Parameter version number
      example: 3
      returned: success
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code


def update_parameter(client, module, **args):
    changed = False
    response = {}

    try:
        response = client.put_parameter(**args)
        changed = True
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="setting parameter")

    return changed, response


def describe_parameter(client, module, **args):
    paginator = client.get_paginator('describe_parameters')
    existing_parameter = paginator.paginate(**args).build_full_result()

    if not existing_parameter['Parameters']:
        return None

    return existing_parameter['Parameters'][0]


def create_update_parameter(client, module):
    changed = False
    existing_parameter = None
    response = {}

    args = dict(
        Name=module.params.get('name'),
        Type=module.params.get('string_type'),
        Tier=module.params.get('tier')
    )

    if (module.params.get('overwrite_value') in ("always", "changed")):
        args.update(Overwrite=True)
    else:
        args.update(Overwrite=False)

    if module.params.get('value') is not None:
        args.update(Value=module.params.get('value'))

    if module.params.get('description'):
        args.update(Description=module.params.get('description'))

    if module.params.get('string_type') == 'SecureString':
        args.update(KeyId=module.params.get('key_id'))

    try:
        existing_parameter = client.get_parameter(Name=args['Name'], WithDecryption=True)
    except Exception:
        pass

    if existing_parameter:
        if 'Value' not in args:
            args['Value'] = existing_parameter['Parameter']['Value']

        if (module.params.get('overwrite_value') == 'always'):
            (changed, response) = update_parameter(client, module, **args)

        elif (module.params.get('overwrite_value') == 'changed'):
            if existing_parameter['Parameter']['Type'] != args['Type']:
                (changed, response) = update_parameter(client, module, **args)

            elif existing_parameter['Parameter']['Value'] != args['Value']:
                (changed, response) = update_parameter(client, module, **args)

            elif args.get('Description'):
                # Description field not available from get_parameter function so get it from describe_parameters
                try:
                    describe_existing_parameter = describe_parameter(
                        client, module,
                        Filters=[{"Key": "Name", "Values": [args['Name']]}])
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    module.fail_json_aws(e, msg="getting description value")

                if describe_existing_parameter['Description'] != args['Description']:
                    (changed, response) = update_parameter(client, module, **args)
    else:
        (changed, response) = update_parameter(client, module, **args)

    return changed, response


def delete_parameter(client, module):
    response = {}

    try:
        response = client.delete_parameter(
            Name=module.params.get('name')
        )
    except is_boto3_error_code('ParameterNotFound'):
        return False, {}
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="deleting parameter")

    return True, response


def setup_client(module):
    connection = module.client('ssm')
    return connection


def setup_module_object():
    argument_spec = dict(
        name=dict(required=True),
        description=dict(),
        value=dict(required=False, no_log=True),
        state=dict(default='present', choices=['present', 'absent']),
        string_type=dict(default='String', choices=['String', 'StringList', 'SecureString'], aliases=['type']),
        decryption=dict(default=True, type='bool'),
        key_id=dict(default="alias/aws/ssm"),
        overwrite_value=dict(default='changed', choices=['never', 'changed', 'always']),
        tier=dict(default='Standard', choices=['Standard', 'Advanced', 'Intelligent-Tiering']),
    )

    return AnsibleAWSModule(
        argument_spec=argument_spec,
    )


def main():
    module = setup_module_object()
    state = module.params.get('state')
    client = setup_client(module)

    invocations = {
        "present": create_update_parameter,
        "absent": delete_parameter,
    }
    (changed, response) = invocations[state](client, module)

    result = {"response": response}

    parameter_metadata = describe_parameter(
        client, module,
        Filters=[{"Key": "Name", "Values": [module.params.get('name')]}])
    if parameter_metadata:
        result['parameter_metadata'] = camel_dict_to_snake_dict(parameter_metadata)

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
