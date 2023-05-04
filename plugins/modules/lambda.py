#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: lambda
version_added: 5.0.0
short_description: Manage AWS Lambda functions
description:
  - Allows for the management of Lambda functions.
  - This module was originally added to C(community.aws) in release 1.0.0.
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
    default: ''
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
  kms_key_arn:
    description:
      - The KMS key ARN used to encrypt the function's environment variables.
    type: str
    version_added: 3.3.0
    version_added_collection: community.aws
  architecture:
    description:
      - The instruction set architecture that the function supports.
      - Requires one of I(s3_bucket) or I(zip_file).
    type: str
    choices: ['x86_64', 'arm64']
    aliases: ['architectures']
    version_added: 5.0.0
  layers:
    description:
      - A list of function layers to add to the function's execution environment.
      - Specify each layer by its ARN, including the version.
    suboptions:
        layer_version_arn:
            description:
            - The ARN of the layer version.
            - Mutually exclusive with I(layer_version_arn).
            type: str
        layer_name:
            description:
            - The name or Amazon Resource Name (ARN) of the layer.
            - Mutually exclusive with I(layer_version_arn).
            type: str
            aliases: ['layer_arn']
        version:
            description:
            - The version number.
            - Required when I(layer_name) is provided, ignored if not.
            type: int
            aliases: ['layer_version']
    type: list
    elements: dict
    version_added: 5.5.0
author:
  - 'Steyn Huizinga (@steynovich)'
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Create Lambda functions
- name: looped creation
  amazon.aws.lambda:
    name: '{{ item.name }}'
    state: present
    zip_file: '{{ item.zip_file }}'
    runtime: 'python2.7'
    role: 'arn:aws:iam::123456789012:role/lambda_basic_execution'
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
  amazon.aws.lambda:
    name: 'Lambda function'
    state: present
    zip_file: 'code.zip'
    runtime: 'python2.7'
    role: 'arn:aws:iam::123456789012:role/lambda_basic_execution'
    handler: 'hello_python.my_handler'
    tags: {}

# Basic Lambda function deletion
- name: Delete Lambda functions HelloWorld and ByeBye
  amazon.aws.lambda:
    name: '{{ item }}'
    state: absent
  loop:
    - HelloWorld
    - ByeBye

# Create Lambda functions with function layers
- name: looped creation
  amazon.aws.lambda:
    name: 'HelloWorld'
    state: present
    zip_file: 'hello-code.zip'
    runtime: 'python2.7'
    role: 'arn:aws:iam::123456789012:role/lambda_basic_execution'
    handler: 'hello_python.my_handler'
    layers:
        - layer_version_arn: 'arn:aws:lambda:us-east-1:123456789012:layer:python27-env:7'
"""

RETURN = r"""
code:
    description: The lambda function's code returned by get_function in boto3.
    returned: success
    type: dict
    contains:
        location:
            description:
                - The presigned URL you can use to download the function's .zip file that you previously uploaded.
                - The URL is valid for up to 10 minutes.
            returned: success
            type: str
            sample: 'https://prod-04-2014-tasks.s3.us-east-1.amazonaws.com/snapshots/sample'
        repository_type:
            description: The repository from which you can download the function.
            returned: success
            type: str
            sample: 'S3'
configuration:
    description: the lambda function's configuration metadata returned by get_function in boto3
    returned: success
    type: dict
    contains:
        architectures:
            description: The architectures supported by the function.
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
        memory_size:
            description: The memory allocated to the function.
            returned: on success
            type: int
            sample: 128
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
        vpc_config:
            description: The function's networking configuration.
            returned: on success
            type: dict
            sample: {
              'security_group_ids': [],
              'subnet_ids': [],
              'vpc_id': '123'
            }
        layers:
            description: The function's layers.
            returned: on success
            version_added: 5.5.0
            type: complex
            contains:
                arn:
                    description: The Amazon Resource Name (ARN) of the function layer.
                    returned: always
                    type: str
                    sample: active
                code_size:
                    description: The size of the layer archive in bytes.
                    returned: always
                    type: str
                signing_profile_version_arn:
                    description: The Amazon Resource Name (ARN) for a signing profile version.
                    returned: always
                    type: str
                signing_job_arn:
                    description: The Amazon Resource Name (ARN) of a signing job.
                    returned: always
                    type: str
"""

import base64
import hashlib
import traceback
import re
from collections import Counter

try:
    from botocore.exceptions import ClientError, BotoCoreError, WaiterError
except ImportError:
    pass  # protected by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags
from ansible_collections.amazon.aws.plugins.module_utils.iam import get_aws_account_info


def get_current_function(connection, function_name, qualifier=None):
    try:
        if qualifier is not None:
            return connection.get_function(FunctionName=function_name, Qualifier=qualifier, aws_retry=True)
        return connection.get_function(FunctionName=function_name, aws_retry=True)
    except is_boto3_error_code("ResourceNotFoundException"):
        return None


def get_layer_version_arn(module, connection, layer_name, version_number):
    try:
        layer_versions = connection.list_layer_versions(LayerName=layer_name, aws_retry=True)["LayerVersions"]
        for v in layer_versions:
            if v["Version"] == version_number:
                return v["LayerVersionArn"]
        module.fail_json(msg=f"Unable to find version {version_number} from Lambda layer {layer_name}")
    except is_boto3_error_code("ResourceNotFoundException"):
        module.fail_json(msg=f"Lambda layer {layer_name} not found")


def sha256sum(filename):
    hasher = hashlib.sha256()
    with open(filename, "rb") as f:
        hasher.update(f.read())

    code_hash = hasher.digest()
    code_b64 = base64.b64encode(code_hash)
    hex_digest = code_b64.decode("utf-8")

    return hex_digest


def set_tag(client, module, tags, function, purge_tags):
    if tags is None:
        return False

    changed = False
    arn = function["Configuration"]["FunctionArn"]

    try:
        current_tags = client.list_tags(Resource=arn, aws_retry=True).get("Tags", {})
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Unable to list tags")

    tags_to_add, tags_to_remove = compare_aws_tags(current_tags, tags, purge_tags=purge_tags)

    if not tags_to_remove and not tags_to_add:
        return False

    if module.check_mode:
        return True

    try:
        if tags_to_remove:
            client.untag_resource(
                Resource=arn,
                TagKeys=tags_to_remove,
                aws_retry=True,
            )
            changed = True

        if tags_to_add:
            client.tag_resource(
                Resource=arn,
                Tags=tags_to_add,
                aws_retry=True,
            )
            changed = True

    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg=f"Unable to tag resource {arn}")

    return changed


def wait_for_lambda(client, module, name):
    try:
        client_active_waiter = client.get_waiter("function_active")
        client_updated_waiter = client.get_waiter("function_updated")
        client_active_waiter.wait(FunctionName=name)
        client_updated_waiter.wait(FunctionName=name)
    except WaiterError as e:
        module.fail_json_aws(e, msg="Timeout while waiting on lambda to finish updating")
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed while waiting on lambda to finish updating")


def format_response(response):
    tags = response.get("Tags", {})
    result = camel_dict_to_snake_dict(response)
    # Lambda returns a dict rather than the usual boto3 list of dicts
    result["tags"] = tags
    return result


def _zip_args(zip_file, current_config, ignore_checksum):
    if not zip_file:
        return {}

    # If there's another change that needs to happen, we always re-upload the code
    if not ignore_checksum:
        local_checksum = sha256sum(zip_file)
        remote_checksum = current_config.get("CodeSha256", "")
        if local_checksum == remote_checksum:
            return {}

    with open(zip_file, "rb") as f:
        zip_content = f.read()
    return {"ZipFile": zip_content}


def _s3_args(s3_bucket, s3_key, s3_object_version):
    if not s3_bucket:
        return {}
    if not s3_key:
        return {}

    code = {"S3Bucket": s3_bucket, "S3Key": s3_key}
    if s3_object_version:
        code.update({"S3ObjectVersion": s3_object_version})

    return code


def _code_args(module, current_config):
    s3_bucket = module.params.get("s3_bucket")
    s3_key = module.params.get("s3_key")
    s3_object_version = module.params.get("s3_object_version")
    zip_file = module.params.get("zip_file")
    architectures = module.params.get("architecture")

    code_kwargs = {}

    if architectures and current_config.get("Architectures", None) != [architectures]:
        module.warn("Arch Change")
        code_kwargs.update({"Architectures": [architectures]})

    try:
        code_kwargs.update(_zip_args(zip_file, current_config, bool(code_kwargs)))
    except IOError as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())

    code_kwargs.update(_s3_args(s3_bucket, s3_key, s3_object_version))

    if not code_kwargs:
        return {}

    if not architectures and current_config.get("Architectures", None):
        code_kwargs.update({"Architectures": current_config.get("Architectures", None)})

    return code_kwargs


def main():
    argument_spec = dict(
        name=dict(required=True),
        state=dict(default="present", choices=["present", "absent"]),
        runtime=dict(),
        role=dict(),
        handler=dict(),
        zip_file=dict(aliases=["src"]),
        s3_bucket=dict(),
        s3_key=dict(no_log=False),
        s3_object_version=dict(),
        description=dict(default=""),
        timeout=dict(type="int", default=3),
        memory_size=dict(type="int", default=128),
        vpc_subnet_ids=dict(type="list", elements="str"),
        vpc_security_group_ids=dict(type="list", elements="str"),
        environment_variables=dict(type="dict"),
        dead_letter_arn=dict(),
        kms_key_arn=dict(type="str", no_log=False),
        tracing_mode=dict(choices=["Active", "PassThrough"]),
        architecture=dict(choices=["x86_64", "arm64"], type="str", aliases=["architectures"]),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        layers=dict(
            type="list",
            elements="dict",
            options=dict(
                layer_version_arn=dict(type="str"),
                layer_name=dict(type="str", aliases=["layer_arn"]),
                version=dict(type="int", aliases=["layer_version"]),
            ),
            required_together=[["layer_name", "version"]],
            required_one_of=[["layer_version_arn", "layer_name"]],
            mutually_exclusive=[["layer_name", "layer_version_arn"], ["version", "layer_version_arn"]],
        ),
    )

    mutually_exclusive = [
        ["zip_file", "s3_key"],
        ["zip_file", "s3_bucket"],
        ["zip_file", "s3_object_version"],
    ]

    required_together = [
        ["s3_key", "s3_bucket"],
        ["vpc_subnet_ids", "vpc_security_group_ids"],
    ]

    required_if = [
        ["state", "present", ["runtime", "handler", "role"]],
        ["architecture", "x86_64", ["zip_file", "s3_bucket"], True],
        ["architecture", "arm64", ["zip_file", "s3_bucket"], True],
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=mutually_exclusive,
        required_together=required_together,
        required_if=required_if,
    )

    name = module.params.get("name")
    state = module.params.get("state").lower()
    runtime = module.params.get("runtime")
    role = module.params.get("role")
    handler = module.params.get("handler")
    description = module.params.get("description")
    timeout = module.params.get("timeout")
    memory_size = module.params.get("memory_size")
    vpc_subnet_ids = module.params.get("vpc_subnet_ids")
    vpc_security_group_ids = module.params.get("vpc_security_group_ids")
    environment_variables = module.params.get("environment_variables")
    dead_letter_arn = module.params.get("dead_letter_arn")
    tracing_mode = module.params.get("tracing_mode")
    tags = module.params.get("tags")
    purge_tags = module.params.get("purge_tags")
    kms_key_arn = module.params.get("kms_key_arn")
    architectures = module.params.get("architecture")
    layers = []

    check_mode = module.check_mode
    changed = False

    try:
        client = module.client("lambda", retry_decorator=AWSRetry.jittered_backoff())
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, msg="Trying to connect to AWS")

    if state == "present":
        if re.match(r"^arn:aws(-([a-z\-]+))?:iam", role):
            role_arn = role
        else:
            # get account ID and assemble ARN
            account_id, partition = get_aws_account_info(module)
            role_arn = f"arn:{partition}:iam::{account_id}:role/{role}"

        # create list of layer version arn
        if module.params.get("layers"):
            for layer in module.params.get("layers"):
                layer_version_arn = layer.get("layer_version_arn")
                if layer_version_arn is None:
                    layer_version_arn = get_layer_version_arn(
                        module, client, layer.get("layer_name"), layer.get("version")
                    )
                layers.append(layer_version_arn)

    # Get function configuration if present, False otherwise
    current_function = get_current_function(client, name)

    # Update existing Lambda function
    if state == "present" and current_function:
        # Get current state
        current_config = current_function["Configuration"]
        current_version = None

        # Update function configuration
        func_kwargs = {"FunctionName": name}

        # Update configuration if needed
        if role_arn and current_config["Role"] != role_arn:
            func_kwargs.update({"Role": role_arn})
        if handler and current_config["Handler"] != handler:
            func_kwargs.update({"Handler": handler})
        if description and current_config["Description"] != description:
            func_kwargs.update({"Description": description})
        if timeout and current_config["Timeout"] != timeout:
            func_kwargs.update({"Timeout": timeout})
        if memory_size and current_config["MemorySize"] != memory_size:
            func_kwargs.update({"MemorySize": memory_size})
        if runtime and current_config["Runtime"] != runtime:
            func_kwargs.update({"Runtime": runtime})
        if (environment_variables is not None) and (
            current_config.get("Environment", {}).get("Variables", {}) != environment_variables
        ):
            func_kwargs.update({"Environment": {"Variables": environment_variables}})
        if dead_letter_arn is not None:
            if current_config.get("DeadLetterConfig"):
                if current_config["DeadLetterConfig"]["TargetArn"] != dead_letter_arn:
                    func_kwargs.update({"DeadLetterConfig": {"TargetArn": dead_letter_arn}})
            else:
                if dead_letter_arn != "":
                    func_kwargs.update({"DeadLetterConfig": {"TargetArn": dead_letter_arn}})
        if tracing_mode and (current_config.get("TracingConfig", {}).get("Mode", "PassThrough") != tracing_mode):
            func_kwargs.update({"TracingConfig": {"Mode": tracing_mode}})
        if kms_key_arn:
            func_kwargs.update({"KMSKeyArn": kms_key_arn})

        # If VPC configuration is desired
        if vpc_subnet_ids:
            if "VpcConfig" in current_config:
                # Compare VPC config with current config
                current_vpc_subnet_ids = current_config["VpcConfig"]["SubnetIds"]
                current_vpc_security_group_ids = current_config["VpcConfig"]["SecurityGroupIds"]

                subnet_net_id_changed = sorted(vpc_subnet_ids) != sorted(current_vpc_subnet_ids)
                vpc_security_group_ids_changed = sorted(vpc_security_group_ids) != sorted(
                    current_vpc_security_group_ids
                )

            if "VpcConfig" not in current_config or subnet_net_id_changed or vpc_security_group_ids_changed:
                new_vpc_config = {"SubnetIds": vpc_subnet_ids, "SecurityGroupIds": vpc_security_group_ids}
                func_kwargs.update({"VpcConfig": new_vpc_config})
        else:
            # No VPC configuration is desired, assure VPC config is empty when present in current config
            if "VpcConfig" in current_config and current_config["VpcConfig"].get("VpcId"):
                func_kwargs.update({"VpcConfig": {"SubnetIds": [], "SecurityGroupIds": []}})

        # Check layers
        if layers:
            # compare two lists to see if the target layers are equal to the current
            current_layers = current_config.get("Layers", [])
            if Counter(layers) != Counter((f["Arn"] for f in current_layers)):
                func_kwargs.update({"Layers": layers})

        # Upload new configuration if configuration has changed
        if len(func_kwargs) > 1:
            if not check_mode:
                wait_for_lambda(client, module, name)

            try:
                if not check_mode:
                    response = client.update_function_configuration(aws_retry=True, **func_kwargs)
                    current_version = response["Version"]
                changed = True
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg="Trying to update lambda configuration")

        # Tag Function
        if tags is not None:
            if set_tag(client, module, tags, current_function, purge_tags):
                changed = True

        code_kwargs = _code_args(module, current_config)
        if code_kwargs:
            # Update code configuration
            code_kwargs.update({"FunctionName": name, "Publish": True})

            if not check_mode:
                wait_for_lambda(client, module, name)

            try:
                if not check_mode:
                    response = client.update_function_code(aws_retry=True, **code_kwargs)
                    current_version = response["Version"]
                changed = True
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg="Trying to upload new code")

        # Describe function code and configuration
        response = get_current_function(client, name, qualifier=current_version)
        if not response:
            module.fail_json(msg="Unable to get function information after updating")
        response = format_response(response)
        # We're done
        module.exit_json(changed=changed, code_kwargs=code_kwargs, func_kwargs=func_kwargs, **response)

    # Function doesn't exists, create new Lambda function
    elif state == "present":
        func_kwargs = {
            "FunctionName": name,
            "Publish": True,
            "Runtime": runtime,
            "Role": role_arn,
            "Timeout": timeout,
            "MemorySize": memory_size,
        }

        code = _code_args(module, {})
        if not code:
            module.fail_json(msg="Either S3 object or path to zipfile required")
        if "Architectures" in code:
            func_kwargs.update({"Architectures": code.pop("Architectures")})
        func_kwargs.update({"Code": code})

        if description is not None:
            func_kwargs.update({"Description": description})

        if handler is not None:
            func_kwargs.update({"Handler": handler})

        if environment_variables:
            func_kwargs.update({"Environment": {"Variables": environment_variables}})

        if dead_letter_arn:
            func_kwargs.update({"DeadLetterConfig": {"TargetArn": dead_letter_arn}})

        if tracing_mode:
            func_kwargs.update({"TracingConfig": {"Mode": tracing_mode}})

        if kms_key_arn:
            func_kwargs.update({"KMSKeyArn": kms_key_arn})

        # If VPC configuration is given
        if vpc_subnet_ids:
            func_kwargs.update({"VpcConfig": {"SubnetIds": vpc_subnet_ids, "SecurityGroupIds": vpc_security_group_ids}})

        # Layers
        if layers:
            func_kwargs.update({"Layers": layers})

        # Tag Function
        if tags:
            func_kwargs.update({"Tags": tags})

        # Function would have been created if not check mode
        if check_mode:
            module.exit_json(changed=True)

        # Finally try to create function
        current_version = None
        try:
            response = client.create_function(aws_retry=True, **func_kwargs)
            current_version = response["Version"]
            changed = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Trying to create function")

        response = get_current_function(client, name, qualifier=current_version)
        if not response:
            module.fail_json(msg="Unable to get function information after creating")
        response = format_response(response)
        module.exit_json(changed=changed, **response)

    # Delete existing Lambda function
    if state == "absent" and current_function:
        try:
            if not check_mode:
                client.delete_function(FunctionName=name, aws_retry=True)
            changed = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Trying to delete Lambda function")

        module.exit_json(changed=changed)

    # Function already absent, do nothing
    elif state == "absent":
        module.exit_json(changed=changed)


if __name__ == "__main__":
    main()
