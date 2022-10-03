#
# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from tempfile import NamedTemporaryFile

from ansible_collections.amazon.aws.tests.unit.compat.mock import MagicMock
from ansible_collections.amazon.aws.plugins.modules import lambda_layer


def setup_testing(module_params):
    connection = MagicMock(name="connection")
    module = MagicMock(name="module")
    module.params = module_params
    module.params.setdefault("state", "present")
    module.check_mode = False
    module.exit_json.side_effect = SystemExit(1)
    module.fail_json.side_effect = SystemExit(2)

    conn_paginator = MagicMock(name="connection.paginator")
    paginate = MagicMock(name="paginator.paginate")
    connection.get_paginator.return_value = conn_paginator
    conn_paginator.paginate.return_value = paginate
    connection.delete_layer_version.return_value = None

    return module, connection, conn_paginator, paginate


def test_delete_non_existing_layer():
    module_params = dict(
        state="absent",
        name="testlayer",
        version=4,
    )

    module, lambda_client, conn_paginator, paginate = setup_testing(module_params)
    paginate.build_full_result.return_value = dict(
        LayerVersions=[],
        ResponseMetadata=dict(http_header=True),
        NextMarker="abcdef123"
    )

    with pytest.raises(SystemExit):
        lambda_layer.execute_module(module, lambda_client)

    lambda_client.get_paginator.assert_called_with("list_layer_versions")
    conn_paginator.paginate.assert_called_with(
        LayerName="testlayer",
    )
    paginate.build_full_result.assert_called_once()
    module.exit_json.assert_called_with(
        changed=False,
        layer_versions=[]
    )


def test_delete_layer_non_existing_version():
    module_params = dict(
        state="absent",
        name="testlayer",
        version=4,
    )

    module, lambda_client, conn_paginator, paginate = setup_testing(module_params)
    paginate.build_full_result.return_value = {
        "LayerVersions": [
            {
                'CompatibleRuntimes': ["python3.7"],
                'CreatedDate': "2022-09-29T10:31:35.977+0000",
                'LayerVersionArn': "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:2",
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
                "LayerVersionArn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:1",
                "LicenseInfo": "GPL-3.0-only",
                "Version": 1
            }
        ],
        "ResponseMetadata": {
            "http_header": True
        },
        "NextMarker": "abcdef123"
    }

    with pytest.raises(SystemExit):
        lambda_layer.execute_module(module, lambda_client)

    lambda_client.get_paginator.assert_called_with("list_layer_versions")
    conn_paginator.paginate.assert_called_with(
        LayerName="testlayer",
    )
    paginate.build_full_result.assert_called_once()
    module.exit_json.assert_called_with(
        changed=False,
        layer_versions=[]
    )


def test_delete_layer_existing_version():
    module_params = dict(
        state="absent",
        name="testlayer",
        version=2,
    )

    module, lambda_client, conn_paginator, paginate = setup_testing(module_params)

    paginate.build_full_result.return_value = {
        "LayerVersions": [
            {
                'CompatibleRuntimes': ["python3.7"],
                'CreatedDate': "2022-09-29T10:31:35.977+0000",
                'LayerVersionArn': "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:2",
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
                "LayerVersionArn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:1",
                "LicenseInfo": "GPL-3.0-only",
                "Version": 1
            }
        ],
        "ResponseMetadata": {
            "http_header": True
        },
        "NextMarker": "abcdef123"
    }

    with pytest.raises(SystemExit):
        lambda_layer.execute_module(module, lambda_client)

    lambda_client.get_paginator.assert_called_with("list_layer_versions")
    conn_paginator.paginate.assert_called_with(
        LayerName="testlayer",
    )
    paginate.build_full_result.assert_called_once()
    lambda_client.delete_layer_version.assert_called_with(
        LayerName="testlayer",
        VersionNumber=2,
    )
    module.exit_json.assert_called_with(
        changed=True,
        layer_versions=[
            {
                "compatible_runtimes": ["python3.7"],
                "created_date": "2022-09-29T10:31:35.977+0000",
                "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:2",
                "license_info": "MIT",
                "version": 2,
                'compatible_architectures': [
                    'arm64'
                ]
            },
        ]
    )


def test_delete_layer_existing_version_using_check_mode():
    module_params = dict(
        state="absent",
        name="testlayer",
        version=2,
    )

    module, lambda_client, conn_paginator, paginate = setup_testing(module_params)
    module.check_mode = True
    paginate.build_full_result.return_value = {
        "LayerVersions": [
            {
                'CompatibleRuntimes': ["python3.7"],
                'CreatedDate': "2022-09-29T10:31:35.977+0000",
                'LayerVersionArn': "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:2",
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
                "LayerVersionArn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:1",
                "LicenseInfo": "GPL-3.0-only",
                "Version": 1
            }
        ],
        "ResponseMetadata": {
            "http_header": True
        },
        "NextMarker": "abcdef123"
    }

    with pytest.raises(SystemExit):
        lambda_layer.execute_module(module, lambda_client)

    lambda_client.get_paginator.assert_called_with("list_layer_versions")
    conn_paginator.paginate.assert_called_with(
        LayerName="testlayer",
    )
    paginate.build_full_result.assert_called_once()
    lambda_client.delete_layer_version.assert_not_called()
    module.exit_json.assert_called_with(
        changed=True,
        layer_versions=[
            {
                "compatible_runtimes": ["python3.7"],
                "created_date": "2022-09-29T10:31:35.977+0000",
                "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:2",
                "license_info": "MIT",
                "version": 2,
                'compatible_architectures': [
                    'arm64'
                ]
            },
        ]
    )


def test_delete_all_layer_versions():
    module_params = dict(
        state="absent",
        name="testlayer",
        version=-1,
    )

    module, lambda_client, conn_paginator, paginate = setup_testing(module_params)
    module.check_mode = True
    paginate.build_full_result.return_value = {
        "LayerVersions": [
            {
                'CompatibleRuntimes': ["python3.7"],
                'CreatedDate': "2022-09-29T10:31:35.977+0000",
                'LayerVersionArn': "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:2",
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
                "LayerVersionArn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:1",
                "LicenseInfo": "GPL-3.0-only",
                "Version": 1
            }
        ],
        "ResponseMetadata": {
            "http_header": True
        },
        "NextMarker": "abcdef123"
    }

    with pytest.raises(SystemExit):
        lambda_layer.execute_module(module, lambda_client)

    lambda_client.get_paginator.assert_called_with("list_layer_versions")
    conn_paginator.paginate.assert_called_with(
        LayerName="testlayer",
    )
    paginate.build_full_result.assert_called_once()
    lambda_client.delete_layer_version.assert_not_called()
    module.exit_json.assert_called_with(
        changed=True,
        layer_versions=[
            {
                "compatible_runtimes": ["python3.7"],
                "created_date": "2022-09-29T10:31:35.977+0000",
                "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:2",
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
                "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:1",
                "license_info": "GPL-3.0-only",
                "version": 1
            }
        ]
    )


def test_create_layer_using_check_mode():
    module_params = dict(
        name="testlayer",
        description="ansible units testing sample layer",
        content=dict(
            s3_bucket="mybucket",
            s3_key="mybucket-key",
            s3_object_version="v1"
        ),
        license_info="MIT"
    )

    module, lambda_client, conn_paginator, paginate = setup_testing(module_params)
    module.check_mode = True
    paginate.build_full_result.return_value = None

    with pytest.raises(SystemExit):
        lambda_layer.execute_module(module, lambda_client)

    lambda_client.get_paginator.assert_not_called()
    conn_paginator.paginate.assert_not_called()
    paginate.build_full_result.assert_not_called()
    lambda_client.publish_layer_version.assert_not_called()
    module.exit_json.assert_called_with(
        changed=True,
        msg="Create operation skipped - running in check mode"
    )


def test_create_layer_using_s3_bucket():
    module_params = dict(
        name="testlayer",
        description="ansible units testing sample layer",
        content=dict(
            s3_bucket="mybucket",
            s3_key="mybucket-key",
            s3_object_version="v1"
        ),
        license_info="MIT"
    )

    module, lambda_client, conn_paginator, paginate = setup_testing(module_params)
    paginate.build_full_result.return_value = None
    lambda_client.publish_layer_version.return_value = {
        'CompatibleRuntimes': [
            'python3.6',
            'python3.7',
        ],
        'Content': {
            'CodeSha256': 'tv9jJO+rPbXUUXuRKi7CwHzKtLDkDRJLB3cC3Z/ouXo=',
            'CodeSize': 169,
            'Location': 'https://awslambda-us-west-2-layers.s3.us-west-2.amazonaws.com/snapshots/123456789012/my-layer-4aaa2fbb',
        },
        'CreatedDate': '2018-11-14T23:03:52.894+0000',
        'Description': "ansible units testing sample layer",
        'LayerArn': 'arn:aws:lambda:us-west-2:123456789012:layer:my-layer',
        'LayerVersionArn': 'arn:aws:lambda:us-west-2:123456789012:layer:testlayer:1',
        'LicenseInfo': 'MIT',
        'Version': 1,
        'ResponseMetadata': {
            'http_header': 'true',
        },
    }

    with pytest.raises(SystemExit):
        lambda_layer.execute_module(module, lambda_client)

    lambda_client.get_paginator.assert_not_called()
    conn_paginator.paginate.assert_not_called()
    paginate.build_full_result.assert_not_called()

    lambda_client.publish_layer_version.assert_called_with(
        LayerName="testlayer",
        Description="ansible units testing sample layer",
        LicenseInfo="MIT",
        Content=dict(
            S3Bucket="mybucket",
            S3Key="mybucket-key",
            S3ObjectVersion="v1"
        ),
    )

    module.exit_json.assert_called_with(
        changed=True,
        layer_versions=[
            {
                'compatible_runtimes': ['python3.6', 'python3.7'],
                'content': {
                    'code_sha256': 'tv9jJO+rPbXUUXuRKi7CwHzKtLDkDRJLB3cC3Z/ouXo=',
                    'code_size': 169,
                    'location': 'https://awslambda-us-west-2-layers.s3.us-west-2.amazonaws.com/snapshots/123456789012/my-layer-4aaa2fbb'
                },
                'created_date': '2018-11-14T23:03:52.894+0000',
                'description': 'ansible units testing sample layer',
                'layer_arn': 'arn:aws:lambda:us-west-2:123456789012:layer:my-layer',
                'layer_version_arn': 'arn:aws:lambda:us-west-2:123456789012:layer:testlayer:1',
                'license_info': 'MIT',
                'version': 1
            }
        ]
    )


def test_create_layer_using_zip_file():

    zip_file_content = b"simple lambda layer content"
    with NamedTemporaryFile() as tf:
        tf.write(zip_file_content)
        tf.flush()

        module_params = dict(
            name="testlayer",
            description="ansible units testing sample layer",
            content=dict(
                zip_file=tf.name,
            ),
            compatible_runtimes=[
                "nodejs",
                "python3.9"
            ],
            compatible_architectures=[
                'x86_64',
                'arm64'
            ]
        )

        module, lambda_client, conn_paginator, paginate = setup_testing(module_params)
        paginate.build_full_result.return_value = None
        lambda_client.publish_layer_version.return_value = {
            'CompatibleRuntimes': [
                'nodejs',
                'python3.9',
            ],
            "CompatibleArchitectures": [
                'x86_64',
                'arm64'
            ],
            'Content': {
                'CodeSha256': 'tv9jJO+rPbXUUXuRKi7CwHzKtLDkDRJLB3cC3Z/ouXo=',
                'CodeSize': 169,
                'Location': 'https://awslambda-us-west-2-layers.s3.us-west-2.amazonaws.com/snapshots/123456789012/my-layer-4aaa2fbb',
            },
            'CreatedDate': '2018-11-14T23:03:52.894+0000',
            'Description': "ansible units testing sample layer",
            'LayerArn': 'arn:aws:lambda:us-west-2:123456789012:layer:my-layer',
            'LayerVersionArn': 'arn:aws:lambda:us-west-2:123456789012:layer:testlayer:2',
            'Version': 2,
            'ResponseMetadata': {
                'http_header': 'true',
            },
        }

        with pytest.raises(SystemExit):
            lambda_layer.execute_module(module, lambda_client)

        lambda_client.get_paginator.assert_not_called()
        conn_paginator.paginate.assert_not_called()
        paginate.build_full_result.assert_not_called()

        lambda_client.publish_layer_version.assert_called_with(
            LayerName="testlayer",
            Description="ansible units testing sample layer",
            CompatibleRuntimes=[
                "nodejs",
                "python3.9"
            ],
            CompatibleArchitectures=[
                'x86_64',
                'arm64'
            ],
            Content=dict(
                ZipFile=zip_file_content
            ),
        )

        module.exit_json.assert_called_with(
            changed=True,
            layer_versions=[
                {
                    'compatible_runtimes': ['nodejs', 'python3.9'],
                    "compatible_architectures": ['x86_64', 'arm64'],
                    'content': {
                        'code_sha256': 'tv9jJO+rPbXUUXuRKi7CwHzKtLDkDRJLB3cC3Z/ouXo=',
                        'code_size': 169,
                        'location': 'https://awslambda-us-west-2-layers.s3.us-west-2.amazonaws.com/snapshots/123456789012/my-layer-4aaa2fbb'
                    },
                    'created_date': '2018-11-14T23:03:52.894+0000',
                    'description': 'ansible units testing sample layer',
                    'layer_arn': 'arn:aws:lambda:us-west-2:123456789012:layer:my-layer',
                    'layer_version_arn': 'arn:aws:lambda:us-west-2:123456789012:layer:testlayer:2',
                    'version': 2
                }
            ]
        )
