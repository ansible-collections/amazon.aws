#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: execute_lambda
version_added: 1.0.0
short_description: Execute an AWS Lambda function
description:
  - This module executes AWS Lambda functions, allowing synchronous and asynchronous
    invocation.
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

author: "Ryan Scott Brown (@ryansb) <ryansb@redhat.com>"
notes:
  - Async invocation will always return an empty C(output) key.
  - Synchronous invocation may result in a function timeout, resulting in an
    empty C(output) key.
options:
  name:
    description:
      - The name of the function to be invoked. This can only be used for
        invocations within the calling account. To invoke a function in another
        account, use I(function_arn) to specify the full ARN.
    type: str
  function_arn:
    description:
      - The name of the function to be invoked
    type: str
  tail_log:
    description:
      - If I(tail_log=yes), the result of the task will include the last 4 KB
        of the CloudWatch log for the function execution. Log tailing only
        works if you use synchronous invocation I(wait=yes). This is usually
        used for development or testing Lambdas.
    type: bool
    default: false
  wait:
    description:
      - Whether to wait for the function results or not. If I(wait=no)
        the task will not return any results. To wait for the Lambda function
        to complete, set I(wait=yes) and the result will be available in the
        I(output) key.
    type: bool
    default: true
  dry_run:
    description:
      - Do not *actually* invoke the function. A C(DryRun) call will check that
        the caller has permissions to call the function, especially for
        checking cross-account permissions.
    type: bool
    default: false
  version_qualifier:
    description:
      - Which version/alias of the function to run. This defaults to the
        C(LATEST) revision, but can be set to any existing version or alias.
        See U(https://docs.aws.amazon.com/lambda/latest/dg/versioning-aliases.html)
        for details.
    type: str
  payload:
    description:
      - A dictionary in any form to be provided as input to the Lambda function.
    default: {}
    type: dict
'''

EXAMPLES = '''
- community.aws.execute_lambda:
    name: test-function
    # the payload is automatically serialized and sent to the function
    payload:
      foo: bar
      value: 8
  register: response

# Test that you have sufficient permissions to execute a Lambda function in
# another account
- community.aws.execute_lambda:
    function_arn: arn:aws:lambda:us-east-1:123456789012:function/some-function
    dry_run: true

- community.aws.execute_lambda:
    name: test-function
    payload:
      foo: bar
      value: 8
    wait: true
    tail_log: true
  register: response
  # the response will have a `logs` key that will contain a log (up to 4KB) of the function execution in Lambda

# Pass the Lambda event payload as a json file.
- community.aws.execute_lambda:
    name: test-function
    payload: "{{ lookup('file','lambda_event.json') }}"
  register: response

- community.aws.execute_lambda:
    name: test-function
    version_qualifier: PRODUCTION
'''

RETURN = '''
result:
    description: Resulting data structure from a successful task execution.
    returned: success
    type: dict
    contains:
        output:
            description: Function output if wait=true and the function returns a value
            returned: success
            type: dict
            sample: "{ 'output': 'something' }"
        logs:
            description: The last 4KB of the function logs. Only provided if I(tail_log) is C(true)
            type: str
            returned: if I(tail_log) == true
        status:
            description: C(StatusCode) of API call exit (200 for synchronous invokes, 202 for async)
            type: int
            sample: 200
            returned: always
'''

import base64
import json

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry


def main():
    argument_spec = dict(
        name=dict(),
        function_arn=dict(),
        wait=dict(default=True, type='bool'),
        tail_log=dict(default=False, type='bool'),
        dry_run=dict(default=False, type='bool'),
        version_qualifier=dict(),
        payload=dict(default={}, type='dict'),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ['name', 'function_arn'],
        ],
        required_one_of=[
            ('name', 'function_arn')
        ],
    )

    name = module.params.get('name')
    function_arn = module.params.get('function_arn')
    await_return = module.params.get('wait')
    dry_run = module.params.get('dry_run')
    tail_log = module.params.get('tail_log')
    version_qualifier = module.params.get('version_qualifier')
    payload = module.params.get('payload')

    try:
        client = module.client('lambda', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    invoke_params = {}

    if await_return:
        # await response
        invoke_params['InvocationType'] = 'RequestResponse'
    else:
        # fire and forget
        invoke_params['InvocationType'] = 'Event'
    if dry_run or module.check_mode:
        # dry_run overrides invocation type
        invoke_params['InvocationType'] = 'DryRun'

    if tail_log and await_return:
        invoke_params['LogType'] = 'Tail'
    elif tail_log and not await_return:
        module.fail_json(msg="The `tail_log` parameter is only available if "
                         "the invocation waits for the function to complete. "
                         "Set `wait` to true or turn off `tail_log`.")
    else:
        invoke_params['LogType'] = 'None'

    if version_qualifier:
        invoke_params['Qualifier'] = version_qualifier

    if payload:
        invoke_params['Payload'] = json.dumps(payload)

    if function_arn:
        invoke_params['FunctionName'] = function_arn
    elif name:
        invoke_params['FunctionName'] = name

    if module.check_mode:
        module.exit_json(changed=True)

    try:
        wait_for_lambda(client, module, name)
        response = client.invoke(**invoke_params, aws_retry=True)
    except is_boto3_error_code('ResourceNotFoundException') as nfe:
        module.fail_json_aws(nfe, msg="Could not find Lambda to execute. Make sure "
                             "the ARN is correct and your profile has "
                             "permissions to execute this function.")
    except botocore.exceptions.ClientError as ce:  # pylint: disable=duplicate-except
        module.fail_json_aws(ce, msg="Client-side error when invoking Lambda, check inputs and specific error")
    except botocore.exceptions.ParamValidationError as ve:  # pylint: disable=duplicate-except
        module.fail_json_aws(ve, msg="Parameters to `invoke` failed to validate")
    except Exception as e:
        module.fail_json_aws(e, msg="Unexpected failure while invoking Lambda function")

    results = {
        'logs': '',
        'status': response['StatusCode'],
        'output': '',
    }

    if response.get('LogResult'):
        try:
            # logs are base64 encoded in the API response
            results['logs'] = base64.b64decode(response.get('LogResult', ''))
        except Exception as e:
            module.fail_json_aws(e, msg="Failed while decoding logs")

    if invoke_params['InvocationType'] == 'RequestResponse':
        try:
            results['output'] = json.loads(response['Payload'].read().decode('utf8'))
        except Exception as e:
            module.fail_json_aws(e, msg="Failed while decoding function return value")

        if isinstance(results.get('output'), dict) and any(
                [results['output'].get('stackTrace'), results['output'].get('errorMessage')]):
            # AWS sends back stack traces and error messages when a function failed
            # in a RequestResponse (synchronous) context.
            template = ("Function executed, but there was an error in the Lambda function. "
                        "Message: {errmsg}, Type: {type}, Stack Trace: {trace}")
            error_data = {
                # format the stacktrace sent back as an array into a multiline string
                'trace': '\n'.join(
                    [' '.join([
                        str(x) for x in line  # cast line numbers to strings
                    ]) for line in results.get('output', {}).get('stackTrace', [])]
                ),
                'errmsg': results['output'].get('errorMessage'),
                'type': results['output'].get('errorType')
            }
            module.fail_json(msg=template.format(**error_data), result=results)

    module.exit_json(changed=True, result=results)


def wait_for_lambda(client, module, name):
    try:
        client_active_waiter = client.get_waiter('function_active')
        client_updated_waiter = client.get_waiter('function_updated')
        client_active_waiter.wait(FunctionName=name)
        client_updated_waiter.wait(FunctionName=name)
    except botocore.exceptions.WaiterError as e:
        module.fail_json_aws(e, msg='Timeout while waiting on lambda to be Active')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed while waiting on lambda to be Active')


if __name__ == '__main__':
    main()
