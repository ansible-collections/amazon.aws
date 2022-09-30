#
# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible_collections.amazon.aws.tests.unit.compat.mock import MagicMock
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


def setup_testing(module_params, paginate_results):
    connection = MagicMock(name="connection")
    module = MagicMock(name="module")
    module.params = module_params

    module.exit_json.side_effect = SystemExit(1)
    module.fail_json.side_effect = SystemExit(2)

    conn_paginator = MagicMock(name="connection.paginator")
    paginate = MagicMock(name="paginator.paginate")
    connection.get_paginator.return_value = conn_paginator
    conn_paginator.paginate.return_value = paginate
    paginate.build_full_result.return_value = paginate_results

    return module, connection, conn_paginator, paginate


def test_list_layers_with_latest_version_with_compatible_runtimes_and_architectures():

    module_params = dict(compatible_runtime="nodejs", compatible_architecture="arm64")
    module, connection, conn_paginator, paginate = setup_testing(module_params, list_layers_paginate_result)

    with pytest.raises(SystemExit):
        lambda_layer_info.execute_module(module, connection)

    connection.get_paginator.assert_called_with("list_layers")
    conn_paginator.paginate.assert_called_with(
        CompatibleRuntime="nodejs",
        CompatibleArchitecture="arm64",
    )
    paginate.build_full_result.assert_called_once()

    module.exit_json.assert_called_with(
        changed=False,
        layers_versions=list_layers_result
    )


def test_list_layers_with_latest_version_with_compatible_runtimes_only():

    module_params = dict(compatible_runtime="nodejs")
    module, connection, conn_paginator, paginate = setup_testing(module_params, list_layers_paginate_result)

    with pytest.raises(SystemExit):
        lambda_layer_info.execute_module(module, connection)

    connection.get_paginator.assert_called_with("list_layers")
    conn_paginator.paginate.assert_called_with(
        CompatibleRuntime="nodejs"
    )
    paginate.build_full_result.assert_called_once()

    module.exit_json.assert_called_with(
        changed=False,
        layers_versions=list_layers_result
    )


def test_list_layers_with_latest_version_with_compatible_architectures_only():

    module_params = dict(compatible_architecture="arm64")
    module, connection, conn_paginator, paginate = setup_testing(module_params, list_layers_paginate_result)

    with pytest.raises(SystemExit):
        lambda_layer_info.execute_module(module, connection)

    connection.get_paginator.assert_called_with("list_layers")
    conn_paginator.paginate.assert_called_with(
        CompatibleArchitecture="arm64"
    )
    paginate.build_full_result.assert_called_once()

    module.exit_json.assert_called_with(
        changed=False,
        layers_versions=list_layers_result
    )


def test_list_layers_with_latest_version_without_any_params():

    module_params = dict()
    module, connection, conn_paginator, paginate = setup_testing(module_params, list_layers_paginate_result)

    with pytest.raises(SystemExit):
        lambda_layer_info.execute_module(module, connection)

    connection.get_paginator.assert_called_with("list_layers")
    conn_paginator.paginate.assert_called_with()
    paginate.build_full_result.assert_called_once()

    module.exit_json.assert_called_with(
        changed=False,
        layers_versions=list_layers_result
    )


def test_list_layers_versions_with_latest_version_with_all_parameters():

    module_params = dict(name="layer-01", compatible_runtime="nodejs", compatible_architecture="arm64")
    module, connection, conn_paginator, paginate = setup_testing(module_params, list_layers_versions_paginate_result)

    with pytest.raises(SystemExit):
        lambda_layer_info.execute_module(module, connection)

    connection.get_paginator.assert_called_with("list_layer_versions")
    conn_paginator.paginate.assert_called_with(
        LayerName="layer-01",
        CompatibleRuntime="nodejs",
        CompatibleArchitecture="arm64",
    )
    paginate.build_full_result.assert_called_once()

    module.exit_json.assert_called_with(
        changed=False,
        layers_versions=list_layers_versions_result
    )


def test_list_layers_versions_with_latest_version_with_name_and_compatible_runtimes_only():

    module_params = dict(name="layer-01", compatible_runtime="nodejs")
    module, connection, conn_paginator, paginate = setup_testing(module_params, list_layers_versions_paginate_result)

    with pytest.raises(SystemExit):
        lambda_layer_info.execute_module(module, connection)

    connection.get_paginator.assert_called_with("list_layer_versions")
    conn_paginator.paginate.assert_called_with(
        LayerName="layer-01",
        CompatibleRuntime="nodejs"
    )
    paginate.build_full_result.assert_called_once()

    module.exit_json.assert_called_with(
        changed=False,
        layers_versions=list_layers_versions_result
    )


def test_list_layers_versions_with_name_and_compatible_architectures_only():

    module_params = dict(name="layer-01", compatible_architecture="arm64")
    module, connection, conn_paginator, paginate = setup_testing(module_params, list_layers_versions_paginate_result)

    with pytest.raises(SystemExit):
        lambda_layer_info.execute_module(module, connection)

    connection.get_paginator.assert_called_with("list_layer_versions")
    conn_paginator.paginate.assert_called_with(
        LayerName="layer-01",
        CompatibleArchitecture="arm64"
    )
    paginate.build_full_result.assert_called_once()

    module.exit_json.assert_called_with(
        changed=False,
        layers_versions=list_layers_versions_result
    )


def test_list_layers_versions_with_name_only():

    module_params = dict(name="layer-01")
    module, connection, conn_paginator, paginate = setup_testing(module_params, list_layers_versions_paginate_result)

    with pytest.raises(SystemExit):
        lambda_layer_info.execute_module(module, connection)

    connection.get_paginator.assert_called_with("list_layer_versions")
    conn_paginator.paginate.assert_called_with(
        LayerName="layer-01",
    )
    paginate.build_full_result.assert_called_once()

    module.exit_json.assert_called_with(
        changed=False,
        layers_versions=list_layers_versions_result
    )
