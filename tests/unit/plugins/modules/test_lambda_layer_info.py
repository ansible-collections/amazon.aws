#
# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

import pytest
from botocore.exceptions import BotoCoreError

from ansible_collections.amazon.aws.plugins.modules import lambda_layer_info

mod__list_layer_versions = "ansible_collections.amazon.aws.plugins.modules.lambda_layer_info._list_layer_versions"
mod__list_layers = "ansible_collections.amazon.aws.plugins.modules.lambda_layer_info._list_layers"
mod_list_layer_versions = "ansible_collections.amazon.aws.plugins.modules.lambda_layer_info.list_layer_versions"
mod_list_layers = "ansible_collections.amazon.aws.plugins.modules.lambda_layer_info.list_layers"


list_layers_paginate_result = {
    "NextMarker": "002",
    "Layers": [
        {
            "LayerName": "test-layer-01",
            "LayerArn": "arn:aws:lambda:eu-west-2:123456789012:layer:test-layer-01",
            "LatestMatchingVersion": {
                "LayerVersionArn": "arn:aws:lambda:eu-west-2:123456789012:layer:test-layer-01:1",
                "Version": 1,
                "Description": "lambda layer created for unit tests",
                "CreatedDate": "2022-09-29T10:31:26.341+0000",
                "CompatibleRuntimes": ["nodejs", "nodejs4.3", "nodejs6.10"],
                "LicenseInfo": "MIT",
                "CompatibleArchitectures": ["arm64"],
            },
        },
        {
            "LayerName": "test-layer-02",
            "LayerArn": "arn:aws:lambda:eu-west-2:123456789012:layer:test-layer-02",
            "LatestMatchingVersion": {
                "LayerVersionArn": "arn:aws:lambda:eu-west-2:123456789012:layer:test-layer-02:1",
                "Version": 1,
                "CreatedDate": "2022-09-29T10:31:26.341+0000",
                "CompatibleArchitectures": ["arm64"],
            },
        },
    ],
    "ResponseMetadata": {
        "http": "true",
    },
}

list_layers_result = [
    {
        "layer_name": "test-layer-01",
        "layer_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:test-layer-01",
        "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:test-layer-01:1",
        "version": 1,
        "description": "lambda layer created for unit tests",
        "created_date": "2022-09-29T10:31:26.341+0000",
        "compatible_runtimes": ["nodejs", "nodejs4.3", "nodejs6.10"],
        "license_info": "MIT",
        "compatible_architectures": ["arm64"],
    },
    {
        "layer_name": "test-layer-02",
        "layer_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:test-layer-02",
        "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:test-layer-02:1",
        "version": 1,
        "created_date": "2022-09-29T10:31:26.341+0000",
        "compatible_architectures": ["arm64"],
    },
]


list_layers_versions_paginate_result = {
    "LayerVersions": [
        {
            "CompatibleRuntimes": ["python3.7"],
            "CreatedDate": "2022-09-29T10:31:35.977+0000",
            "LayerVersionArn": "arn:aws:lambda:eu-west-2:123456789012:layer:layer-01:2",
            "LicenseInfo": "MIT",
            "Version": 2,
            "CompatibleArchitectures": ["arm64"],
        },
        {
            "CompatibleRuntimes": ["python3.7"],
            "CreatedDate": "2022-09-29T10:31:26.341+0000",
            "Description": "lambda layer first version",
            "LayerVersionArn": "arn:aws:lambda:eu-west-2:123456789012:layer:layer-01:1",
            "LicenseInfo": "GPL-3.0-only",
            "Version": 1,
        },
    ],
    "ResponseMetadata": {
        "http": "true",
    },
    "NextMarker": "001",
}


list_layers_versions_result = [
    {
        "compatible_runtimes": ["python3.7"],
        "created_date": "2022-09-29T10:31:35.977+0000",
        "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:layer-01:2",
        "license_info": "MIT",
        "version": 2,
        "compatible_architectures": ["arm64"],
    },
    {
        "compatible_runtimes": ["python3.7"],
        "created_date": "2022-09-29T10:31:26.341+0000",
        "description": "lambda layer first version",
        "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:layer-01:1",
        "license_info": "GPL-3.0-only",
        "version": 1,
    },
]


@pytest.mark.parametrize(
    "params,call_args",
    [
        (
            {"compatible_runtime": "nodejs", "compatible_architecture": "arm64"},
            {"CompatibleRuntime": "nodejs", "CompatibleArchitecture": "arm64"},
        ),
        (
            {
                "compatible_runtime": "nodejs",
            },
            {
                "CompatibleRuntime": "nodejs",
            },
        ),
        ({"compatible_architecture": "arm64"}, {"CompatibleArchitecture": "arm64"}),
        ({}, {}),
    ],
)
@patch(mod__list_layers)
def test_list_layers_with_latest_version(m__list_layers, params, call_args):
    lambda_client = MagicMock()

    m__list_layers.return_value = list_layers_paginate_result
    layers = lambda_layer_info.list_layers(lambda_client, **params)

    m__list_layers.assert_has_calls([call(lambda_client, **call_args)])
    assert layers == list_layers_result


@pytest.mark.parametrize(
    "params,call_args",
    [
        (
            {"name": "layer-01", "compatible_runtime": "nodejs", "compatible_architecture": "arm64"},
            {"LayerName": "layer-01", "CompatibleRuntime": "nodejs", "CompatibleArchitecture": "arm64"},
        ),
        (
            {
                "name": "layer-01",
                "compatible_runtime": "nodejs",
            },
            {
                "LayerName": "layer-01",
                "CompatibleRuntime": "nodejs",
            },
        ),
        (
            {"name": "layer-01", "compatible_architecture": "arm64"},
            {"LayerName": "layer-01", "CompatibleArchitecture": "arm64"},
        ),
        ({"name": "layer-01"}, {"LayerName": "layer-01"}),
    ],
)
@patch(mod__list_layer_versions)
def test_list_layer_versions(m__list_layer_versions, params, call_args):
    lambda_client = MagicMock()

    m__list_layer_versions.return_value = list_layers_versions_paginate_result
    layers = lambda_layer_info.list_layer_versions(lambda_client, **params)

    m__list_layer_versions.assert_has_calls([call(lambda_client, **call_args)])
    assert layers == list_layers_versions_result


def raise_botocore_exception():
    return BotoCoreError(error="failed", operation="list_layers")


def test_get_layer_version_success():
    aws_layer_version = {
        "CompatibleRuntimes": ["python3.8"],
        "Content": {
            "CodeSha256": "vqxKx6nTW31obVcB4MYaTWv5H3fBQTn2PHklL9+mF9E=",
            "CodeSize": 9492621,
            "Location": "https://test.s3.us-east-1.amazonaws.com/snapshots/123456789012/test-79b29d149e06?versionId=nmEKA3ZgiP7hce3J",
        },
        "CreatedDate": "2022-12-05T10:47:32.379+0000",
        "Description": "Python units test layer",
        "LayerArn": "arn:aws:lambda:us-east-1:123456789012:layer:test",
        "LayerVersionArn": "arn:aws:lambda:us-east-1:123456789012:layer:test:2",
        "LicenseInfo": "GPL-3.0-only",
        "Version": 2,
        "ResponseMetadata": {"some-metadata": "some-result"},
    }

    ansible_layer_version = {
        "compatible_runtimes": ["python3.8"],
        "content": {
            "code_sha256": "vqxKx6nTW31obVcB4MYaTWv5H3fBQTn2PHklL9+mF9E=",
            "code_size": 9492621,
            "location": "https://test.s3.us-east-1.amazonaws.com/snapshots/123456789012/test-79b29d149e06?versionId=nmEKA3ZgiP7hce3J",
        },
        "created_date": "2022-12-05T10:47:32.379+0000",
        "description": "Python units test layer",
        "layer_arn": "arn:aws:lambda:us-east-1:123456789012:layer:test",
        "layer_version_arn": "arn:aws:lambda:us-east-1:123456789012:layer:test:2",
        "license_info": "GPL-3.0-only",
        "version": 2,
    }

    lambda_client = MagicMock()
    lambda_client.get_layer_version.return_value = aws_layer_version

    layer_name = "test"
    layer_version = 2

    assert [ansible_layer_version] == lambda_layer_info.get_layer_version(lambda_client, layer_name, layer_version)
    lambda_client.get_layer_version.assert_called_once_with(LayerName=layer_name, VersionNumber=layer_version)


def test_get_layer_version_failure():
    lambda_client = MagicMock()
    lambda_client.get_layer_version.side_effect = raise_botocore_exception()

    layer_name = MagicMock()
    layer_version = MagicMock()

    with pytest.raises(lambda_layer_info.LambdaLayerInfoFailure):
        lambda_layer_info.get_layer_version(lambda_client, layer_name, layer_version)


@pytest.mark.parametrize(
    "params",
    [
        ({"name": "test-layer", "compatible_runtime": "nodejs", "compatible_architecture": "arm64"}),
        ({"compatible_runtime": "nodejs", "compatible_architecture": "arm64"}),
    ],
)
@patch(mod__list_layers)
@patch(mod__list_layer_versions)
def test_list_layers_with_failure(m__list_layer_versions, m__list_layers, params):
    lambda_client = MagicMock()

    if "name" in params:
        m__list_layer_versions.side_effect = raise_botocore_exception()
        test_function = lambda_layer_info.list_layer_versions
    else:
        m__list_layers.side_effect = raise_botocore_exception()
        test_function = lambda_layer_info.list_layers

    with pytest.raises(lambda_layer_info.LambdaLayerInfoFailure):
        test_function(lambda_client, **params)


def raise_layer_info_exception(exc, msg):
    return lambda_layer_info.LambdaLayerInfoFailure(exc=exc, msg=msg)


@pytest.mark.parametrize(
    "params,failure",
    [
        ({"name": "test-layer", "compatible_runtime": "nodejs", "compatible_architecture": "arm64"}, False),
        ({"compatible_runtime": "nodejs", "compatible_architecture": "arm64"}, False),
        ({"name": "test-layer", "compatible_runtime": "nodejs", "compatible_architecture": "arm64"}, True),
    ],
)
@patch(mod_list_layers)
@patch(mod_list_layer_versions)
def test_execute_module(m_list_layer_versions, m_list_layers, params, failure):
    lambda_client = MagicMock()

    module = MagicMock()
    module.params = params
    module.exit_json.side_effect = SystemExit(1)
    module.fail_json_aws.side_effect = SystemExit(2)

    method_called, method_not_called = m_list_layers, m_list_layer_versions
    if "name" in params:
        method_not_called, method_called = m_list_layers, m_list_layer_versions

    if failure:
        exc = "lambda_layer_exception"
        msg = "this exception has been generated for unit tests"

        method_called.side_effect = raise_layer_info_exception(exc, msg)

        with pytest.raises(SystemExit):
            lambda_layer_info.execute_module(module, lambda_client)

        module.fail_json_aws.assert_called_with(exception=exc, msg=msg)

    else:
        result = {"A": "valueA", "B": "valueB"}
        method_called.return_value = result

        with pytest.raises(SystemExit):
            lambda_layer_info.execute_module(module, lambda_client)

        module.exit_json.assert_called_with(changed=False, layers_versions=result)
        method_called.assert_called_with(lambda_client, **params)
        method_not_called.list_layers.assert_not_called()
