#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: lambda_layer
version_added: 5.5.0
short_description: Creates an AWS Lambda layer or deletes an AWS Lambda layer version
description:
  - This module allows the management of AWS Lambda functions aliases via the Ansible
  - Creates an Lambda layer from a ZIP archive.
    Each time you call this module with the same layer name, a new version is created.
  - Deletes a version of an Lambda layer.

author: "Aubin Bikouo (@abikouo)"
options:
  state:
    description:
    - Determines if an Lambda layer should be created, or deleted. When set to C(present), an Lambda layer version will be
      created. If set to C(absent), an existing Lambda layer version will be deleted.
    type: str
    default: present
    choices: [ absent, present ]
  name:
    description:
    - The name or Amazon Resource Name (ARN) of the Lambda layer.
    type: str
    required: true
    aliases:
    - layer_name
  description:
    description:
    - The description of the version.
    - Ignored when I(state=absent).
    - Mutually exclusive with I(version).
    type: str
  content:
    description:
    - The function layer archive.
    - Required when I(state=present).
    - Ignored when I(state=absent).
    - Mutually exclusive with I(version).
    type: dict
    suboptions:
      s3_bucket:
        description:
        - The Amazon S3 bucket of the layer archive.
        type: str
      s3_key:
        description:
        - The Amazon S3 key of the layer archive.
        type: str
      s3_object_version:
        description:
        - For versioned objects, the version of the layer archive object to use.
        type: str
      zip_file:
        description:
        - Path to the base64-encoded file of the layer archive.
        type: path
  compatible_runtimes:
    description:
    - A list of compatible function runtimes.
    - Ignored when I(state=absent).
    - Mutually exclusive with I(version).
    type: list
    elements: str
  license_info:
    description:
    - The layer's software license. It can be any of an SPDX license identifier,
      the URL of a license hosted on the internet or the full text of the license.
    - Ignored when I(state=absent).
    - Mutually exclusive with I(version).
    type: str
  compatible_architectures:
    description:
    - A list of compatible instruction set architectures. For example, x86_64.
    - Mutually exclusive with I(version).
    type: list
    elements: str
  version:
    description:
    - The version number of the layer to delete.
    - Set to C(-1) to delete all versions for the specified layer name.
    - Required when I(state=absent).
    - Ignored when I(state=present).
    - Mutually exclusive with I(description), I(content), I(compatible_runtimes),
      I(license_info), I(compatible_architectures).
    type: int
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
---
# Create a new Python library layer version from a zip archive located into a S3 bucket
- name: Create a new python library layer
  amazon.aws.lambda_layer:
    state: present
    name: sample-layer
    description: 'My Python layer'
    content:
      s3_bucket: 'lambda-layers-us-west-2-123456789012'
      s3_key: 'python_layer.zip'
    compatible_runtimes:
      - python3.6
      - python3.7
    license_info: MIT
    compatible_architectures:
      - x86_64

# Create a layer version from a zip in the local filesystem
- name: Create a new layer from a zip in the local filesystem
  amazon.aws.lambda_layer:
    state: present
    name: sample-layer
    description: 'My Python layer'
    content:
      zip_file: 'python_layer.zip'
    compatible_runtimes:
      - python3.6
      - python3.7
    license_info: MIT
    compatible_architectures:
      - x86_64

# Delete a layer version
- name: Delete a layer version
  amazon.aws.lambda_layer:
    state: absent
    name: sample-layer
    version: 2

# Delete all versions of test-layer
- name: Delete all versions
  amazon.aws.lambda_layer:
    state: absent
    name: test-layer
    version: -1
"""

RETURN = r"""
layer_version:
  description: info about the layer version that was created or deleted.
  returned: always
  type: list
  elements: dict
  contains:
    content:
        description: Details about the layer version.
        returned: I(state=present)
        type: complex
        contains:
          location:
            description: A link to the layer archive in Amazon S3 that is valid for 10 minutes.
            returned: I(state=present)
            type: str
            sample: "https://awslambda-us-east-1-layers.s3.us-east-1.amazonaws.com/snapshots/123456789012/pylayer-9da91deffd3b4941b8baeeae5daeffe4"
          code_sha256:
            description: The SHA-256 hash of the layer archive.
            returned: I(state=present)
            type: str
            sample: "VLluleJZ3HTwDrdYolSMrS+8iPwEkcoXXaegjXf+dmc="
          code_size:
            description: The size of the layer archive in bytes.
            returned: I(state=present)
            type: int
            sample: 9473675
          signing_profile_version_arn:
            description: The Amazon Resource Name (ARN) for a signing profile version.
            returned: When a signing profile is defined
            type: str
          signing_job_arn:
            description: The Amazon Resource Name (ARN) of a signing job.
            returned: When a signing profile is defined
            type: str
    layer_arn:
        description: The ARN of the layer.
        returned: if the layer version exists or has been created
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


class LambdaLayerFailure(Exception):
    def __init__(self, exc, msg):
        self.exc = exc
        self.msg = msg
        super().__init__(self)


def list_layer_versions(lambda_client, name):
    try:
        layer_versions = _list_layer_versions(lambda_client, LayerName=name)["LayerVersions"]
        return [camel_dict_to_snake_dict(layer) for layer in layer_versions]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        raise LambdaLayerFailure(e, f"Unable to list layer versions for name {name}")


def create_layer_version(lambda_client, params, check_mode=False):
    if check_mode:
        return {"msg": "Create operation skipped - running in check mode", "changed": True}

    opt = {"LayerName": params.get("name"), "Content": {}}
    keys = [
        ("description", "Description"),
        ("compatible_runtimes", "CompatibleRuntimes"),
        ("license_info", "LicenseInfo"),
        ("compatible_architectures", "CompatibleArchitectures"),
    ]
    for k, d in keys:
        if params.get(k) is not None:
            opt[d] = params.get(k)

    # Read zip file if any
    zip_file = params["content"].get("zip_file")
    if zip_file is not None:
        with open(zip_file, "rb") as zf:
            opt["Content"]["ZipFile"] = zf.read()
    else:
        opt["Content"]["S3Bucket"] = params["content"].get("s3_bucket")
        opt["Content"]["S3Key"] = params["content"].get("s3_key")
        if params["content"].get("s3_object_version") is not None:
            opt["Content"]["S3ObjectVersion"] = params["content"].get("s3_object_version")

    try:
        layer_version = lambda_client.publish_layer_version(**opt)
        layer_version.pop("ResponseMetadata", None)
        return {"changed": True, "layer_versions": [camel_dict_to_snake_dict(layer_version)]}
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        raise LambdaLayerFailure(e, "Failed to publish a new layer version (check that you have required permissions).")


def delete_layer_version(lambda_client, params, check_mode=False):
    name = params.get("name")
    version = params.get("version")
    layer_versions = list_layer_versions(lambda_client, name)
    deleted_versions = []
    changed = False
    for layer in layer_versions:
        if version == -1 or layer["version"] == version:
            deleted_versions.append(layer)
            changed = True
            if not check_mode:
                try:
                    lambda_client.delete_layer_version(LayerName=name, VersionNumber=layer["version"])
                except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                    raise LambdaLayerFailure(
                        e, f"Failed to delete layer version LayerName={name}, VersionNumber={version}."
                    )
    return {"changed": changed, "layer_versions": deleted_versions}


def execute_module(module, lambda_client):
    try:
        state = module.params.get("state")
        f_operation = create_layer_version
        if state == "absent":
            f_operation = delete_layer_version

        module.exit_json(**f_operation(lambda_client, module.params, module.check_mode))
    except LambdaLayerFailure as e:
        module.fail_json_aws(e.exc, msg=e.msg)


def main():
    argument_spec = dict(
        state=dict(type="str", choices=["present", "absent"], default="present"),
        name=dict(type="str", required=True, aliases=["layer_name"]),
        description=dict(type="str"),
        content=dict(
            type="dict",
            options=dict(
                s3_bucket=dict(type="str"),
                s3_key=dict(type="str", no_log=False),
                s3_object_version=dict(type="str"),
                zip_file=dict(type="path"),
            ),
            required_together=[["s3_bucket", "s3_key"]],
            required_one_of=[["s3_bucket", "zip_file"]],
            mutually_exclusive=[["s3_bucket", "zip_file"]],
        ),
        compatible_runtimes=dict(type="list", elements="str"),
        license_info=dict(type="str"),
        compatible_architectures=dict(type="list", elements="str"),
        version=dict(type="int"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[
            ("state", "present", ["content"]),
            ("state", "absent", ["version"]),
        ],
        mutually_exclusive=[
            ["version", "description"],
            ["version", "content"],
            ["version", "compatible_runtimes"],
            ["version", "license_info"],
            ["version", "compatible_architectures"],
        ],
        supports_check_mode=True,
    )

    lambda_client = module.client("lambda")
    execute_module(module, lambda_client)


if __name__ == "__main__":
    main()
