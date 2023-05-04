#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: lambda_layer_info
version_added: 5.5.0
short_description: List lambda layer or lambda layer versions
description:
  - This module is used to list the versions of an Lambda layer or all available lambda layers.
  - The lambda layer versions that have been deleted aren't listed.

author: "Aubin Bikouo (@abikouo)"
options:
  name:
    description:
    - The name or Amazon Resource Name (ARN) of the Lambda layer.
    type: str
    aliases:
    - layer_name
  compatible_runtime:
    description:
    - A runtime identifier.
    - Specify this option without I(name) to list only latest layers versions of layers that indicate
      that they're compatible with that runtime.
    - Specify this option with I(name) to list only layer versions that indicate that
      they're compatible with that runtime.
    type: str
  compatible_architecture:
    description:
    - A compatible instruction set architectures.
    - Specify this option without I(name) to include only to list only latest layers versions of layers that
      are compatible with that instruction set architecture.
    - Specify this option with I(name) to include only layer versions that are compatible with that architecture.
    type: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
- amazon.aws.boto3

'''

EXAMPLES = '''
---
# Display information about the versions for the layer named blank-java-lib
- name: Retrieve layer versions
  amazon.aws.lambda_layer_info:
    name: blank-java-lib

# Display information about the versions for the layer named blank-java-lib compatible with architecture x86_64
- name: Retrieve layer versions
  amazon.aws.lambda_layer_info:
    name: blank-java-lib
    compatible_architecture: x86_64

# list latest versions of available layers
- name: list latest versions for all layers
  amazon.aws.lambda_layer_info:

# list latest versions of available layers compatible with runtime python3.7
- name: list latest versions for all layers
  amazon.aws.lambda_layer_info:
    compatible_runtime: python3.7
'''

RETURN = '''
layers_versions:
  description:
  - The layers versions that exists.
  returned: success
  type: list
  elements: dict
  contains:
    layer_arn:
        description: The ARN of the layer.
        returned: when C(name) is provided
        type: str
        sample: "arn:aws:lambda:eu-west-2:123456789012:layer:pylayer"
    layer_version_arn:
        description: The ARN of the layer version.
        returned: if the layer version exists or has been created
        type: str
        sample: "arn:aws:lambda:eu-west-2:123456789012:layer:pylayer:2"
    description:
        description: The description of the version.
        returned: I(state=present)
        type: str
    created_date:
        description: The date that the layer version was created, in ISO-8601 format (YYYY-MM-DDThh:mm:ss.sTZD).
        returned: if the layer version exists or has been created
        type: str
        sample: "2022-09-28T14:27:35.866+0000"
    version:
        description: The version number.
        returned: if the layer version exists or has been created
        type: int
        sample: 1
    compatible_runtimes:
        description: A list of compatible runtimes.
        returned: if it was defined for the layer version.
        type: list
        sample: ["python3.7"]
    license_info:
        description: The layer's software license.
        returned: if it was defined for the layer version.
        type: str
        sample: "GPL-3.0-only"
    compatible_architectures:
        description: A list of compatible instruction set architectures.
        returned: if it was defined for the layer version.
        type: list
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry


@AWSRetry.jittered_backoff()
def _list_layer_versions(client, **params):
    paginator = client.get_paginator('list_layer_versions')
    return paginator.paginate(**params).build_full_result()


@AWSRetry.jittered_backoff()
def _list_layers(client, **params):
    paginator = client.get_paginator('list_layers')
    return paginator.paginate(**params).build_full_result()


class LambdaLayerInfoFailure(Exception):
    def __init__(self, exc, msg):
        self.exc = exc
        self.msg = msg
        super().__init__(self)


def list_layer_versions(lambda_client, name, compatible_runtime=None, compatible_architecture=None):

    params = {"LayerName": name}
    if compatible_runtime:
        params["CompatibleRuntime"] = compatible_runtime
    if compatible_architecture:
        params["CompatibleArchitecture"] = compatible_architecture
    try:
        layer_versions = _list_layer_versions(lambda_client, **params)['LayerVersions']
        return [camel_dict_to_snake_dict(layer) for layer in layer_versions]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        raise LambdaLayerInfoFailure(exc=e, msg="Unable to list layer versions for name {0}".format(name))


def list_layers(lambda_client, compatible_runtime=None, compatible_architecture=None):

    params = {}
    if compatible_runtime:
        params["CompatibleRuntime"] = compatible_runtime
    if compatible_architecture:
        params["CompatibleArchitecture"] = compatible_architecture
    try:
        layers = _list_layers(lambda_client, **params)['Layers']
        layer_versions = []
        for item in layers:
            layer = {key: value for key, value in item.items() if key != "LatestMatchingVersion"}
            layer.update(item.get("LatestMatchingVersion"))
            layer_versions.append(camel_dict_to_snake_dict(layer))
        return layer_versions
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        raise LambdaLayerInfoFailure(exc=e, msg="Unable to list layers {0}".format(params))


def execute_module(module, lambda_client):

    params = {}
    f_operation = list_layers
    name = module.params.get("name")
    if name is not None:
        f_operation = list_layer_versions
        params["name"] = name
    compatible_runtime = module.params.get("compatible_runtime")
    if compatible_runtime is not None:
        params["compatible_runtime"] = compatible_runtime
    compatible_architecture = module.params.get("compatible_architecture")
    if compatible_architecture is not None:
        params["compatible_architecture"] = compatible_architecture

    try:
        result = f_operation(lambda_client, **params)
        module.exit_json(changed=False, layers_versions=result)
    except LambdaLayerInfoFailure as e:
        module.fail_json_aws(exception=e.exc, msg=e.msg)


def main():
    argument_spec = dict(
        name=dict(type="str", aliases=["layer_name"]),
        compatible_runtime=dict(type="str"),
        compatible_architecture=dict(type="str"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    lambda_client = module.client('lambda')
    execute_module(module, lambda_client)


if __name__ == '__main__':
    main()
