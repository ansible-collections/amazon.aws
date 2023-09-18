#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: lambda
version_added: 1.0.0
short_description: Manage AWS Lambda functions
description:
     - Allows for the management of Lambda functions.
requirements: [ boto3 ]
options:
  name:
    description:
      - The name you want to assign to the function you are uploading. Cannot be changed.
    required: true
    type: str
  state:
    description:
      - Create or delete Lambda function.
    default: present
    choices: [ 'present', 'absent' ]
    type: str
  runtime:
    description:
      - The runtime environment for the Lambda function you are uploading.
      - Required when creating a function. Uses parameters as described in boto3 docs.
      - Required when I(state=present).
      - For supported list of runtimes, see U(https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html).
    type: str
  role:
    description:
      - The Amazon Resource Name (ARN) of the IAM role that Lambda assumes when it executes your function to access any other Amazon Web Services (AWS)
        resources. You may use the bare ARN if the role belongs to the same AWS account.
      - Required when I(state=present).
    type: str
  handler:
    description:
      - The function within your code that Lambda calls to begin execution.
    type: str
  zip_file:
    description:
      - A .zip file containing your deployment package
      - If I(state=present) then either I(zip_file) or I(s3_bucket) must be present.
    aliases: [ 'src' ]
    type: str
  s3_bucket:
    description:
      - Amazon S3 bucket name where the .zip file containing your deployment package is stored.
      - If I(state=present) then either I(zip_file) or I(s3_bucket) must be present.
      - I(s3_bucket) and I(s3_key) are required together.
    type: str
  s3_key:
    description:
      - The Amazon S3 object (the deployment package) key name you want to upload.
      - I(s3_bucket) and I(s3_key) are required together.
    type: str
  s3_object_version:
    description:
      - The Amazon S3 object (the deployment package) version you want to upload.
    type: str
  description:
    description:
      - A short, user-defined function description. Lambda does not use this value. Assign a meaningful description as you see fit.
    type: str
  timeout:
    description:
      - The function maximum execution time in seconds after which Lambda should terminate the function.
    default: 3
    type: int
  memory_size:
    description:
      - The amount of memory, in MB, your Lambda function is given.
    default: 128
    type: int
  vpc_subnet_ids:
    description:
      - List of subnet IDs to run Lambda function in.
      - Use this option if you need to access resources in your VPC. Leave empty if you don't want to run the function in a VPC.
      - If set, I(vpc_security_group_ids) must also be set.
    type: list
    elements: str
  vpc_security_group_ids:
    description:
      - List of VPC security group IDs to associate with the Lambda function.
      - Required when I(vpc_subnet_ids) is used.
    type: list
    elements: str
  environment_variables:
    description:
      - A dictionary of environment variables the Lambda function is given.
    type: dict
  dead_letter_arn:
    description:
      - The parent object that contains the target Amazon Resource Name (ARN) of an Amazon SQS queue or Amazon SNS topic.
    type: str
  tracing_mode:
    description:
      - Set mode to 'Active' to sample and trace incoming requests with AWS X-Ray. Turned off (set to 'PassThrough') by default.
    choices: ['Active', 'PassThrough']
    type: str
  tags:
    description:
      - tag dict to apply to the function (requires botocore 1.5.40 or above).
    type: dict
author:
    - 'Steyn Huizinga (@steynovich)'
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = r'''
# Create Lambda functions
- name: looped creation
  community.aws.lambda:
    name: '{{ item.name }}'
    state: present
    zip_file: '{{ item.zip_file }}'
    runtime: 'python2.7'
    role: 'arn:aws:iam::987654321012:role/lambda_basic_execution'
    handler: 'hello_python.my_handler'
    vpc_subnet_ids:
    - subnet-123abcde
    - subnet-edcba321
    vpc_security_group_ids:
    - sg-123abcde
    - sg-edcba321
    environment_variables: '{{ item.env_vars }}'
    tags:
      key1: 'value1'
  loop:
    - name: HelloWorld
      zip_file: hello-code.zip
      env_vars:
        key1: "first"
        key2: "second"
    - name: ByeBye
      zip_file: bye-code.zip
      env_vars:
        key1: "1"
        key2: "2"

# To remove previously added tags pass an empty dict
- name: remove tags
  community.aws.lambda:
    name: 'Lambda function'
    state: present
    zip_file: 'code.zip'
    runtime: 'python2.7'
    role: 'arn:aws:iam::987654321012:role/lambda_basic_execution'
    handler: 'hello_python.my_handler'
    tags: {}

# Basic Lambda function deletion
- name: Delete Lambda functions HelloWorld and ByeBye
  community.aws.lambda:
    name: '{{ item }}'
    state: absent
  loop:
    - HelloWorld
    - ByeBye
'''

RETURN = r'''
code:
    description: the lambda function location returned by get_function in boto3
    returned: success
    type: dict
    sample:
      {
        'location': 'a presigned S3 URL',
        'repository_type': 'S3',
      }
configuration:
    description: the lambda function metadata returned by get_function in boto3
    returned: success
    type: dict
    sample:
      {
        'code_sha256': 'zOAGfF5JLFuzZoSNirUtOrQp+S341IOA3BcoXXoaIaU=',
        'code_size': 123,
        'description': 'My function',
        'environment': {
          'variables': {
            'key': 'value'
          }
        },
        'function_arn': 'arn:aws:lambda:us-east-1:123456789012:function:myFunction:1',
        'function_name': 'myFunction',
        'handler': 'index.handler',
        'last_modified': '2017-08-01T00:00:00.000+0000',
        'memory_size': 128,
        'revision_id': 'a2x9886d-d48a-4a0c-ab64-82abc005x80c',
        'role': 'arn:aws:iam::123456789012:role/lambda_basic_execution',
        'runtime': 'nodejs6.10',
        'tracing_config': { 'mode': 'Active' },
        'timeout': 3,
        'version': '1',
        'vpc_config': {
          'security_group_ids': [],
          'subnet_ids': [],
          'vpc_id': '123'
        }
      }
'''

import base64
import hashlib
import traceback
import re

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # protected by AnsibleAWSModule

from ansible.module_utils._text import to_native
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import compare_aws_tags


def get_account_info(module):
    """return the account information (account id and partition) we are currently working on

    get_account_info tries too find out the account that we are working
    on.  It's not guaranteed that this will be easy so we try in
    several different ways.  Giving either IAM or STS privileges to
    the account should be enough to permit this.
    """
    account_id = None
    partition = None
    try:
        sts_client = module.client('sts', retry_decorator=AWSRetry.jittered_backoff())
        caller_id = sts_client.get_caller_identity(aws_retry=True)
        account_id = caller_id.get('Account')
        partition = caller_id.get('Arn').split(':')[1]
    except (BotoCoreError, ClientError):
        try:
            iam_client = module.client('iam', retry_decorator=AWSRetry.jittered_backoff())
            arn, partition, service, reg, account_id, resource = iam_client.get_user(aws_retry=True)['User']['Arn'].split(':')
        except is_boto3_error_code('AccessDenied') as e:
            try:
                except_msg = to_native(e.message)
            except AttributeError:
                except_msg = to_native(e)
            m = re.search(r"arn:(aws(-([a-z\-]+))?):iam::([0-9]{12,32}):\w+/", except_msg)
            if m is None:
                module.fail_json_aws(e, msg="getting account information")
            account_id = m.group(4)
            partition = m.group(1)
        except (BotoCoreError, ClientError) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="getting account information")

    return account_id, partition


def get_current_function(connection, function_name, qualifier=None):
    try:
        if qualifier is not None:
            return connection.get_function(FunctionName=function_name, Qualifier=qualifier, aws_retry=True)
        return connection.get_function(FunctionName=function_name, aws_retry=True)
    except is_boto3_error_code('ResourceNotFoundException'):
        return None


def sha256sum(filename):
    hasher = hashlib.sha256()
    with open(filename, 'rb') as f:
        hasher.update(f.read())

    code_hash = hasher.digest()
    code_b64 = base64.b64encode(code_hash)
    hex_digest = code_b64.decode('utf-8')

    return hex_digest


def set_tag(client, module, tags, function):

    changed = False
    arn = function['Configuration']['FunctionArn']

    try:
        current_tags = client.list_tags(Resource=arn, aws_retry=True).get('Tags', {})
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Unable to list tags")

    tags_to_add, tags_to_remove = compare_aws_tags(current_tags, tags, purge_tags=True)

    try:
        if tags_to_remove:
            client.untag_resource(
                Resource=arn,
                TagKeys=tags_to_remove,
                aws_retry=True
            )
            changed = True

        if tags_to_add:
            client.tag_resource(
                Resource=arn,
                Tags=tags_to_add,
                aws_retry=True
            )
            changed = True

    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Unable to tag resource {0}".format(arn))

    return changed


def main():
    argument_spec = dict(
        name=dict(required=True),
        state=dict(default='present', choices=['present', 'absent']),
        runtime=dict(),
        role=dict(),
        handler=dict(),
        zip_file=dict(aliases=['src']),
        s3_bucket=dict(),
        s3_key=dict(no_log=False),
        s3_object_version=dict(),
        description=dict(default=''),
        timeout=dict(type='int', default=3),
        memory_size=dict(type='int', default=128),
        vpc_subnet_ids=dict(type='list', elements='str'),
        vpc_security_group_ids=dict(type='list', elements='str'),
        environment_variables=dict(type='dict'),
        dead_letter_arn=dict(),
        tracing_mode=dict(choices=['Active', 'PassThrough']),
        tags=dict(type='dict'),
    )

    mutually_exclusive = [['zip_file', 's3_key'],
                          ['zip_file', 's3_bucket'],
                          ['zip_file', 's3_object_version']]

    required_together = [['s3_key', 's3_bucket'],
                         ['vpc_subnet_ids', 'vpc_security_group_ids']]

    required_if = [['state', 'present', ['runtime', 'handler', 'role']]]

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True,
                              mutually_exclusive=mutually_exclusive,
                              required_together=required_together,
                              required_if=required_if)

    name = module.params.get('name')
    state = module.params.get('state').lower()
    runtime = module.params.get('runtime')
    role = module.params.get('role')
    handler = module.params.get('handler')
    s3_bucket = module.params.get('s3_bucket')
    s3_key = module.params.get('s3_key')
    s3_object_version = module.params.get('s3_object_version')
    zip_file = module.params.get('zip_file')
    description = module.params.get('description')
    timeout = module.params.get('timeout')
    memory_size = module.params.get('memory_size')
    vpc_subnet_ids = module.params.get('vpc_subnet_ids')
    vpc_security_group_ids = module.params.get('vpc_security_group_ids')
    environment_variables = module.params.get('environment_variables')
    dead_letter_arn = module.params.get('dead_letter_arn')
    tracing_mode = module.params.get('tracing_mode')
    tags = module.params.get('tags')

    check_mode = module.check_mode
    changed = False

    try:
        client = module.client('lambda', retry_decorator=AWSRetry.jittered_backoff())
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, msg="Trying to connect to AWS")

    if tags is not None:
        if not hasattr(client, "list_tags"):
            module.fail_json(msg="Using tags requires botocore 1.5.40 or above")

    if state == 'present':
        if re.match(r'^arn:aws(-([a-z\-]+))?:iam', role):
            role_arn = role
        else:
            # get account ID and assemble ARN
            account_id, partition = get_account_info(module)
            role_arn = 'arn:{0}:iam::{1}:role/{2}'.format(partition, account_id, role)

    # Get function configuration if present, False otherwise
    current_function = get_current_function(client, name)

    # Update existing Lambda function
    if state == 'present' and current_function:

        # Get current state
        current_config = current_function['Configuration']
        current_version = None

        # Update function configuration
        func_kwargs = {'FunctionName': name}

        # Update configuration if needed
        if role_arn and current_config['Role'] != role_arn:
            func_kwargs.update({'Role': role_arn})
        if handler and current_config['Handler'] != handler:
            func_kwargs.update({'Handler': handler})
        if description and current_config['Description'] != description:
            func_kwargs.update({'Description': description})
        if timeout and current_config['Timeout'] != timeout:
            func_kwargs.update({'Timeout': timeout})
        if memory_size and current_config['MemorySize'] != memory_size:
            func_kwargs.update({'MemorySize': memory_size})
        if runtime and current_config['Runtime'] != runtime:
            func_kwargs.update({'Runtime': runtime})
        if (environment_variables is not None) and (current_config.get(
                'Environment', {}).get('Variables', {}) != environment_variables):
            func_kwargs.update({'Environment': {'Variables': environment_variables}})
        if dead_letter_arn is not None:
            if current_config.get('DeadLetterConfig'):
                if current_config['DeadLetterConfig']['TargetArn'] != dead_letter_arn:
                    func_kwargs.update({'DeadLetterConfig': {'TargetArn': dead_letter_arn}})
            else:
                if dead_letter_arn != "":
                    func_kwargs.update({'DeadLetterConfig': {'TargetArn': dead_letter_arn}})
        if tracing_mode and (current_config.get('TracingConfig', {}).get('Mode', 'PassThrough') != tracing_mode):
            func_kwargs.update({'TracingConfig': {'Mode': tracing_mode}})

        # If VPC configuration is desired
        if vpc_subnet_ids:

            if 'VpcConfig' in current_config:
                # Compare VPC config with current config
                current_vpc_subnet_ids = current_config['VpcConfig']['SubnetIds']
                current_vpc_security_group_ids = current_config['VpcConfig']['SecurityGroupIds']

                subnet_net_id_changed = sorted(vpc_subnet_ids) != sorted(current_vpc_subnet_ids)
                vpc_security_group_ids_changed = sorted(vpc_security_group_ids) != sorted(current_vpc_security_group_ids)

            if 'VpcConfig' not in current_config or subnet_net_id_changed or vpc_security_group_ids_changed:
                new_vpc_config = {'SubnetIds': vpc_subnet_ids,
                                  'SecurityGroupIds': vpc_security_group_ids}
                func_kwargs.update({'VpcConfig': new_vpc_config})
        else:
            # No VPC configuration is desired, assure VPC config is empty when present in current config
            if 'VpcConfig' in current_config and current_config['VpcConfig'].get('VpcId'):
                func_kwargs.update({'VpcConfig': {'SubnetIds': [], 'SecurityGroupIds': []}})

        # Upload new configuration if configuration has changed
        if len(func_kwargs) > 1:
            try:
                if not check_mode:
                    response = client.update_function_configuration(aws_retry=True, **func_kwargs)
                    current_version = response['Version']
                changed = True
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg="Trying to update lambda configuration")

        # Update code configuration
        code_kwargs = {'FunctionName': name, 'Publish': True}

        # Update S3 location
        if s3_bucket and s3_key:
            # If function is stored on S3 always update
            code_kwargs.update({'S3Bucket': s3_bucket, 'S3Key': s3_key})

            # If S3 Object Version is given
            if s3_object_version:
                code_kwargs.update({'S3ObjectVersion': s3_object_version})

        # Compare local checksum, update remote code when different
        elif zip_file:
            local_checksum = sha256sum(zip_file)
            remote_checksum = current_config['CodeSha256']

            # Only upload new code when local code is different compared to the remote code
            if local_checksum != remote_checksum:
                try:
                    with open(zip_file, 'rb') as f:
                        encoded_zip = f.read()
                    code_kwargs.update({'ZipFile': encoded_zip})
                except IOError as e:
                    module.fail_json(msg=str(e), exception=traceback.format_exc())

        # Tag Function
        if tags is not None:
            if set_tag(client, module, tags, current_function):
                changed = True

        # Upload new code if needed (e.g. code checksum has changed)
        if len(code_kwargs) > 2:
            try:
                if not check_mode:
                    response = client.update_function_code(aws_retry=True, **code_kwargs)
                    current_version = response['Version']
                changed = True
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg="Trying to upload new code")

        # Describe function code and configuration
        response = get_current_function(client, name, qualifier=current_version)
        if not response:
            module.fail_json(msg='Unable to get function information after updating')

        # We're done
        module.exit_json(changed=changed, **camel_dict_to_snake_dict(response))

    # Function doesn't exists, create new Lambda function
    elif state == 'present':
        if s3_bucket and s3_key:
            # If function is stored on S3
            code = {'S3Bucket': s3_bucket,
                    'S3Key': s3_key}
            if s3_object_version:
                code.update({'S3ObjectVersion': s3_object_version})
        elif zip_file:
            # If function is stored in local zipfile
            try:
                with open(zip_file, 'rb') as f:
                    zip_content = f.read()

                code = {'ZipFile': zip_content}
            except IOError as e:
                module.fail_json(msg=str(e), exception=traceback.format_exc())

        else:
            module.fail_json(msg='Either S3 object or path to zipfile required')

        func_kwargs = {'FunctionName': name,
                       'Publish': True,
                       'Runtime': runtime,
                       'Role': role_arn,
                       'Code': code,
                       'Timeout': timeout,
                       'MemorySize': memory_size,
                       }

        if description is not None:
            func_kwargs.update({'Description': description})

        if handler is not None:
            func_kwargs.update({'Handler': handler})

        if environment_variables:
            func_kwargs.update({'Environment': {'Variables': environment_variables}})

        if dead_letter_arn:
            func_kwargs.update({'DeadLetterConfig': {'TargetArn': dead_letter_arn}})

        if tracing_mode:
            func_kwargs.update({'TracingConfig': {'Mode': tracing_mode}})

        # If VPC configuration is given
        if vpc_subnet_ids:
            func_kwargs.update({'VpcConfig': {'SubnetIds': vpc_subnet_ids,
                                              'SecurityGroupIds': vpc_security_group_ids}})

        # Finally try to create function
        current_version = None
        try:
            if not check_mode:
                response = client.create_function(aws_retry=True, **func_kwargs)
                current_version = response['Version']
            changed = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Trying to create function")

        # Tag Function
        if tags is not None:
            if set_tag(client, module, tags, get_current_function(client, name)):
                changed = True

        response = get_current_function(client, name, qualifier=current_version)
        if not response:
            module.fail_json(msg='Unable to get function information after creating')
        module.exit_json(changed=changed, **camel_dict_to_snake_dict(response))

    # Delete existing Lambda function
    if state == 'absent' and current_function:
        try:
            if not check_mode:
                client.delete_function(FunctionName=name, aws_retry=True)
            changed = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Trying to delete Lambda function")

        module.exit_json(changed=changed)

    # Function already absent, do nothing
    elif state == 'absent':
        module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
