#
# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from botocore.exceptions import BotoCoreError

from unittest.mock import MagicMock, call
from unittest import TestCase
from ansible_collections.amazon.aws.plugins.modules import lambda_layer_info


list_layers_paginate_result = {
    'NextMarker': '002',
    'Layers': [
        {
            'LayerName': "test-layer-01",
            'LayerArn': "arn:aws:lambda:eu-west-2:123456789012:layer:test-layer-01",
            'LatestMatchingVersion': {
                'LayerVersionArn': "arn:aws:lambda:eu-west-2:123456789012:layer:test-layer-01:1",
                'Version': 1,
                'Description': "lambda layer created for unit tests",
                'CreatedDate': "2022-09-29T10:31:26.341+0000",
                'CompatibleRuntimes': [
                    'nodejs',
                    'nodejs4.3',
                    'nodejs6.10'
                ],
                'LicenseInfo': 'MIT',
                'CompatibleArchitectures': [
                    'arm64'
                ]
            }
        },
        {
            'LayerName': "test-layer-02",
            'LayerArn': "arn:aws:lambda:eu-west-2:123456789012:layer:test-layer-02",
            'LatestMatchingVersion': {
                'LayerVersionArn': "arn:aws:lambda:eu-west-2:123456789012:layer:test-layer-02:1",
                'Version': 1,
                'CreatedDate': "2022-09-29T10:31:26.341+0000",
                'CompatibleArchitectures': [
                    'arm64'
                ]
            }
        },
    ],
    'ResponseMetadata': {
        'http': 'true',
    },
}

list_layers_result = [
    {
        'layer_name': "test-layer-01",
        'layer_arn': "arn:aws:lambda:eu-west-2:123456789012:layer:test-layer-01",
        'layer_version_arn': "arn:aws:lambda:eu-west-2:123456789012:layer:test-layer-01:1",
        'version': 1,
        'description': "lambda layer created for unit tests",
        'created_date': "2022-09-29T10:31:26.341+0000",
        'compatible_runtimes': [
            'nodejs',
            'nodejs4.3',
            'nodejs6.10'
        ],
        'license_info': 'MIT',
        'compatible_architectures': [
            'arm64'
        ]
    },
    {
        'layer_name': "test-layer-02",
        'layer_arn': "arn:aws:lambda:eu-west-2:123456789012:layer:test-layer-02",
        'layer_version_arn': "arn:aws:lambda:eu-west-2:123456789012:layer:test-layer-02:1",
        'version': 1,
        'created_date': "2022-09-29T10:31:26.341+0000",
        'compatible_architectures': [
            'arm64'
        ]
    }
]


list_layers_versions_paginate_result = {
    'LayerVersions': [
        {
            'CompatibleRuntimes': ["python3.7"],
            'CreatedDate': "2022-09-29T10:31:35.977+0000",
            'LayerVersionArn': "arn:aws:lambda:eu-west-2:123456789012:layer:layer-01:2",
            "LicenseInfo": "MIT",
            'Version': 2,
            'CompatibleArchitectures': [
                'arm64'
            ]
        },
        {
            "CompatibleRuntimes": ["python3.7"],
            "CreatedDate": "2022-09-29T10:31:26.341+0000",
            "Description": "lambda layer first version",
            "LayerVersionArn": "arn:aws:lambda:eu-west-2:123456789012:layer:layer-01:1",
            "LicenseInfo": "GPL-3.0-only",
            "Version": 1
        }
    ],
    'ResponseMetadata': {
        'http': 'true',
    },
    'NextMarker': '001',
}


list_layers_versions_result = [
    {
        "compatible_runtimes": ["python3.7"],
        "created_date": "2022-09-29T10:31:35.977+0000",
        "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:layer-01:2",
        "license_info": "MIT",
        "version": 2,
        'compatible_architectures': [
            'arm64'
        ]
    },
    {
        "compatible_runtimes": ["python3.7"],
        "created_date": "2022-09-29T10:31:26.341+0000",
        "description": "lambda layer first version",
        "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:layer-01:1",
        "license_info": "GPL-3.0-only",
        "version": 1
    }
]


@pytest.mark.parametrize(
    "params,call_args",
    [
        (
            {
                "compatible_runtime": "nodejs",
                "compatible_architecture": "arm64"
            },
            {
                "CompatibleRuntime": "nodejs",
                "CompatibleArchitecture": "arm64"
            }
        ),
        (
            {
                "compatible_runtime": "nodejs",
            },
            {
                "CompatibleRuntime": "nodejs",
            }
        ),
        (
            {
                "compatible_architecture": "arm64"
            },
            {
                "CompatibleArchitecture": "arm64"
            }
        ),
        (
            {}, {}
        )
    ]
)
def test_list_layers_with_latest_version(params, call_args):

    lambda_client = MagicMock()
    lambda_layer_info._list_layers = MagicMock()

    lambda_layer_info._list_layers.return_value = list_layers_paginate_result
    layers = lambda_layer_info.list_layers(lambda_client, **params)

    lambda_layer_info._list_layers.assert_has_calls(
        [
            call(lambda_client, **call_args)
        ]
    )
    assert layers == list_layers_result


@pytest.mark.parametrize(
    "params,call_args",
    [
        (
            {
                "name": "layer-01",
                "compatible_runtime": "nodejs",
                "compatible_architecture": "arm64"
            },
            {
                "LayerName": "layer-01",
                "CompatibleRuntime": "nodejs",
                "CompatibleArchitecture": "arm64"
            }
        ),
        (
            {
                "name": "layer-01",
                "compatible_runtime": "nodejs",
            },
            {
                "LayerName": "layer-01",
                "CompatibleRuntime": "nodejs",
            }
        ),
        (
            {
                "name": "layer-01",
                "compatible_architecture": "arm64"
            },
            {
                "LayerName": "layer-01",
                "CompatibleArchitecture": "arm64"
            }
        ),
        (
            {"name": "layer-01"}, {"LayerName": "layer-01"}
        )
    ]
)
def test_list_layer_versions(params, call_args):

    lambda_client = MagicMock()
    lambda_layer_info._list_layer_versions = MagicMock()

    lambda_layer_info._list_layer_versions.return_value = list_layers_versions_paginate_result
    layers = lambda_layer_info.list_layer_versions(lambda_client, **params)

    lambda_layer_info._list_layer_versions.assert_has_calls(
        [
            call(lambda_client, **call_args)
        ]
    )
    assert layers == list_layers_versions_result


def raise_botocore_exception():
    return BotoCoreError(error="failed", operation="list_layers")


@pytest.mark.parametrize(
    "params",
    [
        (
            {
                "name": "test-layer",
                "compatible_runtime": "nodejs",
                "compatible_architecture": "arm64"
            }
        ),
        (
            {
                "compatible_runtime": "nodejs",
                "compatible_architecture": "arm64"
            }
        )
    ]
)
def test_list_layers_with_failure(params):

    lambda_client = MagicMock()
    lambda_layer_info._list_layers = MagicMock()
    lambda_layer_info._list_layer_versions = MagicMock()

    if "name" in params:
        lambda_layer_info._list_layer_versions.side_effect = raise_botocore_exception()
        test_function = lambda_layer_info.list_layer_versions
    else:
        lambda_layer_info._list_layers.side_effect = raise_botocore_exception()
        test_function = lambda_layer_info.list_layers

    with pytest.raises(lambda_layer_info.LambdaLayerInfoFailure):
        test_function(lambda_client, **params)


class ExecuteModuleTestCase(TestCase):

    def setUp(self):

        self.lambda_client = MagicMock()
        self.module = MagicMock()

        self.module.exit_json.side_effect = SystemExit(1)
        self.module.fail_json_aws.side_effect = SystemExit(2)

        lambda_layer_info.list_layer_versions = MagicMock()
        lambda_layer_info.list_layers = MagicMock()

        self.exc = "lambda_layer_exception"
        self.msg = "this exception has been generated for unit tests"

    def raise_layer_info_exception(self):
        return lambda_layer_info.LambdaLayerInfoFailure(exc=self.exc, msg=self.msg)

    def test_list_layer_exit_json(self):
        self.module.params = {
            "name": "test-layer",
            "compatible_runtime": "nodejs",
            "compatible_architecture": "arm64"
        }

        result = {"key": "value", "anotherkey": "another_value"}
        lambda_layer_info.list_layer_versions.return_value = result

        with pytest.raises(SystemExit):
            lambda_layer_info.execute_module(self.module, self.lambda_client)

        self.module.exit_json.assert_called_with(
            changed=False, layers_versions=result
        )
        lambda_layer_info.list_layer_versions.assert_called_with(
            self.lambda_client,
            name=self.module.params.get("name"),
            compatible_runtime=self.module.params.get("compatible_runtime"),
            compatible_architecture=self.module.params.get("compatible_architecture"),
        )
        lambda_layer_info.list_layers.assert_not_called()

    def test_list_layer_version_exit_json(self):
        self.module.params = {
            "compatible_runtime": "nodejs",
            "compatible_architecture": "arm64"
        }

        result = {"key": "value", "anotherkey": "another_value"}
        lambda_layer_info.list_layers.return_value = result

        with pytest.raises(SystemExit):
            lambda_layer_info.execute_module(self.module, self.lambda_client)

        self.module.exit_json.assert_called_with(
            changed=False, layers_versions=result
        )
        lambda_layer_info.list_layers.assert_called_with(
            self.lambda_client,
            compatible_runtime=self.module.params.get("compatible_runtime"),
            compatible_architecture=self.module.params.get("compatible_architecture"),
        )
        lambda_layer_info.list_layer_versions.assert_not_called()

    def test_failure(self):

        self.module.params = {
            "name": "test-layer",
            "compatible_runtime": "nodejs",
            "compatible_architecture": "arm64"
        }
        lambda_layer_info.list_layer_versions.side_effect = self.raise_layer_info_exception()

        with pytest.raises(SystemExit):
            lambda_layer_info.execute_module(self.module, self.lambda_client)

        self.module.fail_json_aws.assert_called_with(exception=self.exc, msg=self.msg)
