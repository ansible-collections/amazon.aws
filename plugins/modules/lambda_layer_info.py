#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
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
  version_number:
    description:
    - The Lambda layer version number to retrieve.
    - Requires O(name) to be provided.
    type: int
    aliases:
    - layer_version
    version_added: 6.0.0
  compatible_runtime:
    description:
    - A runtime identifier.
    - Specify this option without O(name) to list only latest layers versions of layers that indicate
      that they're compatible with that runtime.
    - Specify this option with O(name) to list only layer versions that indicate that
      they're compatible with that runtime.
    type: str
  compatible_architecture:
    description:
    - A compatible instruction set architectures.
    - Specify this option without O(name) to include only to list only latest layers versions of layers that
      are compatible with that instruction set architecture.
    - Specify this option with O(name) to include only layer versions that are compatible with that architecture.
    type: str
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
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

# Retrieve specific lambda layer information
- name: Get lambda layer version information
  amazon.aws.lambda_layer_info:
    name: my-layer
    version_number: 1
"""

RETURN = r"""
layers_versions:
  description:
  - The layers versions that exists.
  returned: success
  type: list
  elements: dict
  contains:
    layer_arn:
        description: The ARN of the layer.
        returned: when O(name) is provided
        type: str
        sample: "arn:aws:lambda:eu-west-2:123456789012:layer:pylayer"
    layer_version_arn:
        description: The ARN of the layer version.
        returned: if the layer version exists or has been created
        type: str
        sample: "arn:aws:lambda:eu-west-2:123456789012:layer:pylayer:2"
    description:
        description: The description of the version.
        returned: always
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
    content:
        description: Details about the layer version.
        returned: if O(version_number) was provided
        type: complex
        version_added: 6.0.0
        contains:
            location:
                description: A link to the layer archive in Amazon S3 that is valid for 10 minutes.
                type: str
                sample: 'https://awslambda-us-east-2-layers.s3.us-east-2.amazonaws.com/snapshots/123456789012/mylayer-4aaa2fbb-96a?versionId=27iWyA73c...'
            code_sha256:
                description: The SHA-256 hash of the layer archive.
                type: str
                sample: 'tv9jJO+rPbXUUXuRKi7CwHzKtLDkDRJLB3cC3Z/ouXo='
            code_size:
                description: The size of the layer archive in bytes.
                type: int
                sample: 169
            signing_profile_version_arn:
                description: The Amazon Resource Name (ARN) for a signing profile version.
                type: str
            signing_job_arn:
                description: The Amazon Resource Name (ARN) of a signing job.
                type: str
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


@AWSRetry.jittered_backoff()
def _list_layer_versions(client, **params):
    paginator = client.get_paginator("list_layer_versions")
    return paginator.paginate(**params).build_full_result()


@AWSRetry.jittered_backoff()
def _list_layers(client, **params):
    paginator = client.get_paginator("list_layers")
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
        layer_versions = _list_layer_versions(lambda_client, **params)["LayerVersions"]
        return [camel_dict_to_snake_dict(layer) for layer in layer_versions]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        raise LambdaLayerInfoFailure(exc=e, msg=f"Unable to list layer versions for name {name}")


def list_layers(lambda_client, compatible_runtime=None, compatible_architecture=None):
    params = {}
    if compatible_runtime:
        params["CompatibleRuntime"] = compatible_runtime
    if compatible_architecture:
        params["CompatibleArchitecture"] = compatible_architecture
    try:
        layers = _list_layers(lambda_client, **params)["Layers"]
        layer_versions = []
        for item in layers:
            layer = {key: value for key, value in item.items() if key != "LatestMatchingVersion"}
            layer.update(item.get("LatestMatchingVersion"))
            layer_versions.append(camel_dict_to_snake_dict(layer))
        return layer_versions
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        raise LambdaLayerInfoFailure(exc=e, msg=f"Unable to list layers {params}")


def get_layer_version(lambda_client, layer_name, version_number):
    try:
        layer_version = lambda_client.get_layer_version(LayerName=layer_name, VersionNumber=version_number)
        if layer_version:
            layer_version.pop("ResponseMetadata")
        return [camel_dict_to_snake_dict(layer_version)]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        raise LambdaLayerInfoFailure(exc=e, msg="get_layer_version() failed.")


def execute_module(module, lambda_client):
    name = module.params.get("name")
    version_number = module.params.get("version_number")

    try:
        if name is not None and version_number is not None:
            result = get_layer_version(lambda_client, name, version_number)
        else:
            params = {}
            f_operation = list_layers
            if name is not None:
                f_operation = list_layer_versions
                params["name"] = name
            compatible_runtime = module.params.get("compatible_runtime")
            if compatible_runtime is not None:
                params["compatible_runtime"] = compatible_runtime
            compatible_architecture = module.params.get("compatible_architecture")
            if compatible_architecture is not None:
                params["compatible_architecture"] = compatible_architecture
            result = f_operation(lambda_client, **params)

        module.exit_json(changed=False, layers_versions=result)
    except LambdaLayerInfoFailure as e:
        module.fail_json_aws(exception=e.exc, msg=e.msg)


def main():
    argument_spec = dict(
        name=dict(type="str", aliases=["layer_name"]),
        compatible_runtime=dict(type="str"),
        compatible_architecture=dict(type="str"),
        version_number=dict(type="int", aliases=["layer_version"]),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec, supports_check_mode=True, required_by=dict(version_number=("name",))
    )

    lambda_client = module.client("lambda")
    execute_module(module, lambda_client)


if __name__ == "__main__":
    main()
