#
# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from tempfile import NamedTemporaryFile
import os

from unittest.mock import MagicMock, call
from unittest import TestCase
from ansible_collections.amazon.aws.plugins.modules import lambda_layer


def raise_lambdalayer_exception(e=None, m=None):
    e = e or "lambda layer exc"
    m = m or "unit testing"
    return lambda_layer.LambdaLayerFailure(exc=e, msg=m)


@pytest.mark.parametrize(
    "params,api_result,calls,ansible_result",
    [
        (
            {
                "name": "testlayer",
                "version": 4
            },
            [],
            [],
            {"changed": False, "layer_versions": []}
        ),
        (
            {
                "name": "testlayer",
                "version": 4
            },
            [
                {
                    'compatible_runtimes': ["python3.7"],
                    'created_date': "2022-09-29T10:31:35.977+0000",
                    'layer_version_arn': "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:2",
                    "license_info": "MIT",
                    'version': 2,
                    'compatible_architectures': [
                        'arm64'
                    ]
                },
                {
                    "created_date": "2022-09-29T10:31:26.341+0000",
                    "description": "lambda layer first version",
                    "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:1",
                    "version": 1
                }
            ],
            [],
            {"changed": False, "layer_versions": []}
        ),
        (
            {
                "name": "testlayer",
                "version": 2
            },
            [
                {
                    'compatible_runtimes': ["python3.7"],
                    'created_date': "2022-09-29T10:31:35.977+0000",
                    'layer_version_arn': "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:2",
                    "license_info": "MIT",
                    'version': 2,
                    'compatible_architectures': [
                        'arm64'
                    ]
                },
                {
                    "created_date": "2022-09-29T10:31:26.341+0000",
                    "description": "lambda layer first version",
                    "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:1",
                    "version": 1
                }
            ],
            [
                call(LayerName='testlayer', VersionNumber=2)
            ],
            {
                "changed": True,
                "layer_versions": [
                    {
                        'compatible_runtimes': ["python3.7"],
                        'created_date': "2022-09-29T10:31:35.977+0000",
                        'layer_version_arn': "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:2",
                        "license_info": "MIT",
                        'version': 2,
                        'compatible_architectures': [
                            'arm64'
                        ]
                    }
                ]
            }
        ),
        (
            {
                "name": "testlayer",
                "version": -1
            },
            [
                {
                    'compatible_runtimes': ["python3.7"],
                    'created_date': "2022-09-29T10:31:35.977+0000",
                    'layer_version_arn': "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:2",
                    "license_info": "MIT",
                    'version': 2,
                    'compatible_architectures': [
                        'arm64'
                    ]
                },
                {
                    "created_date": "2022-09-29T10:31:26.341+0000",
                    "description": "lambda layer first version",
                    "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:1",
                    "version": 1
                }
            ],
            [
                call(LayerName='testlayer', VersionNumber=2),
                call(LayerName='testlayer', VersionNumber=1)
            ],
            {
                "changed": True,
                "layer_versions": [
                    {
                        'compatible_runtimes': ["python3.7"],
                        'created_date': "2022-09-29T10:31:35.977+0000",
                        'layer_version_arn': "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:2",
                        "license_info": "MIT",
                        'version': 2,
                        'compatible_architectures': [
                            'arm64'
                        ]
                    },
                    {
                        "created_date": "2022-09-29T10:31:26.341+0000",
                        "description": "lambda layer first version",
                        "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:1",
                        "version": 1
                    }
                ]
            }
        )
    ]
)
def test_delete_layer(params, api_result, calls, ansible_result):

    lambda_client = MagicMock()
    lambda_client.delete_layer_version.return_value = None
    lambda_layer.list_layer_versions = MagicMock()

    lambda_layer.list_layer_versions.return_value = api_result
    result = lambda_layer.delete_layer_version(lambda_client, params)
    assert result == ansible_result

    lambda_layer.list_layer_versions.assert_called_once_with(
        lambda_client, params.get("name")
    )

    if not calls:
        lambda_client.delete_layer_version.assert_not_called()
    else:
        lambda_client.delete_layer_version.assert_has_calls(calls, any_order=True)


def test_delete_layer_check_mode():

    lambda_client = MagicMock()
    lambda_client.delete_layer_version.return_value = None
    lambda_layer.list_layer_versions = MagicMock()

    lambda_layer.list_layer_versions.return_value = [
        {
            'compatible_runtimes': ["python3.7"],
            'created_date': "2022-09-29T10:31:35.977+0000",
            'layer_version_arn': "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:2",
            "license_info": "MIT",
            'version': 2,
            'compatible_architectures': [
                'arm64'
            ]
        },
        {
            "created_date": "2022-09-29T10:31:26.341+0000",
            "description": "lambda layer first version",
            "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:1",
            "version": 1
        }
    ]
    params = {"name": "testlayer", "version": -1}
    result = lambda_layer.delete_layer_version(lambda_client, params, check_mode=True)
    ansible_result = {
        "changed": True,
        "layer_versions": [
            {
                'compatible_runtimes': ["python3.7"],
                'created_date': "2022-09-29T10:31:35.977+0000",
                'layer_version_arn': "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:2",
                "license_info": "MIT",
                'version': 2,
                'compatible_architectures': [
                    'arm64'
                ]
            },
            {
                "created_date": "2022-09-29T10:31:26.341+0000",
                "description": "lambda layer first version",
                "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:1",
                "version": 1
            }
        ]
    }
    assert result == ansible_result

    lambda_layer.list_layer_versions.assert_called_once_with(
        lambda_client, params.get("name")
    )
    lambda_client.delete_layer_version.assert_not_called()


def test_delete_layer_failure():

    lambda_client = MagicMock()
    lambda_client.delete_layer_version.side_effect = raise_lambdalayer_exception()
    lambda_layer.list_layer_versions = MagicMock()

    lambda_layer.list_layer_versions.return_value = [
        {
            "created_date": "2022-09-29T10:31:26.341+0000",
            "description": "lambda layer first version",
            "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:1",
            "version": 1
        }
    ]
    params = {"name": "testlayer", "version": 1}
    with pytest.raises(lambda_layer.LambdaLayerFailure):
        lambda_layer.delete_layer_version(lambda_client, params)


class CreateLayerTestCase(TestCase):
    def setUp(self):
        self.lambda_client = MagicMock()
        lambda_layer.list_layer_versions = MagicMock()

        self.zip_file_data = b"simple lambda layer content"
        self.file_handler = NamedTemporaryFile(delete=False)
        self.file_handler.write(self.zip_file_data)
        self.file_handler.flush()

    def tearDown(self):
        self.file_handler.close()
        os.unlink(self.file_handler.name)

    def test_check_mode(self):
        params = {
            "name": "testlayer",
            "description": "ansible units testing sample layer",
            "content": {
                "s3_bucket": "mybucket",
                "s3_key": "mybucket-key",
                "s3_object_version": "v1"
            },
            "license_info": "MIT"
        }

        result = lambda_layer.create_layer_version(self.lambda_client, params, check_mode=True)
        assert result == {"msg": "Create operation skipped - running in check mode", "changed": True}

        lambda_layer.list_layer_versions.assert_not_called()
        self.lambda_client.publish_layer_version.assert_not_called()

    def test_using_s3_bucket(self):
        params = {
            "name": "testlayer",
            "description": "ansible units testing sample layer",
            "content": {
                "s3_bucket": "mybucket",
                "s3_key": "mybucket-key",
                "s3_object_version": "v1"
            },
            "license_info": "MIT"
        }

        self.lambda_client.publish_layer_version.return_value = {
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

        expected = {
            "changed": True,
            "layer_versions": [
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
        }

        result = lambda_layer.create_layer_version(self.lambda_client, params)
        assert result == expected

        self.lambda_client.publish_layer_version.assert_called_with(
            LayerName="testlayer",
            Description="ansible units testing sample layer",
            LicenseInfo="MIT",
            Content={
                "S3Bucket": "mybucket",
                "S3Key": "mybucket-key",
                "S3ObjectVersion": "v1"
            }
        )

    def test_using_zip_file(self):
        params = {
            "name": "testlayer",
            "description": "ansible units testing sample layer",
            "content": {
                "zip_file": self.file_handler.name,
            },
            "compatible_runtimes": [
                "nodejs",
                "python3.9"
            ],
            "compatible_architectures": [
                'x86_64',
                'arm64'
            ]
        }

        self.lambda_client.publish_layer_version.return_value = {
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

        expected = {
            "changed": True,
            "layer_versions": [
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
        }

        result = lambda_layer.create_layer_version(self.lambda_client, params)
        assert result == expected

        self.lambda_client.publish_layer_version.assert_called_with(
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
            Content={
                "ZipFile": self.zip_file_data
            },
        )

    def test_failure(self):
        params = {
            "name": "testlayer",
            "description": "ansible units testing sample layer",
            "content": {
                "zip_file": self.file_handler.name,
            },
            "compatible_runtimes": [
                "nodejs",
                "python3.9"
            ],
            "compatible_architectures": [
                'x86_64',
                'arm64'
            ]
        }

        self.lambda_client.publish_layer_version.side_effect = raise_lambdalayer_exception()
        with pytest.raises(lambda_layer.LambdaLayerFailure):
            lambda_layer.create_layer_version(self.lambda_client, params)

    def test_using_unexisting_file(self):
        params = {
            "name": "testlayer",
            "description": "ansible units testing sample layer",
            "content": {
                "zip_file": "this_file_does_not_exist",
            },
            "compatible_runtimes": [
                "nodejs",
                "python3.9"
            ],
            "compatible_architectures": [
                'x86_64',
                'arm64'
            ]
        }

        self.lambda_client.publish_layer_version.return_value = {}
        with pytest.raises(FileNotFoundError):
            lambda_layer.create_layer_version(self.lambda_client, params)

        self.lambda_client.publish_layer_version.assert_not_called()


class ExecuteModuleTestCase(TestCase):

    def setUp(self):
        self.module = MagicMock()
        self.module.check_mode = False
        self.module.exit_json.side_effect = SystemExit(1)
        self.module.fail_json_aws.side_effect = SystemExit(2)

        self.lambda_client = MagicMock()

        lambda_layer.create_layer_version = MagicMock()
        lambda_layer.delete_layer_version = MagicMock()

    def test_create_layer(self):
        params = {
            "name": "test-layer"
        }
        self.module.params = params

        result = {"changed": True, "layers_versions": {}}
        lambda_layer.create_layer_version.return_value = result

        with pytest.raises(SystemExit):
            lambda_layer.execute_module(self.module, self.lambda_client)

        self.module.exit_json.assert_called_with(
            **result
        )
        self.module.fail_json_aws.assert_not_called()
        lambda_layer.create_layer_version.assert_called_with(
            self.lambda_client, params, self.module.check_mode
        )
        lambda_layer.delete_layer_version.assert_not_called()

    def test_delete_layer(self):
        params = {
            "name": "test-layer", "state": "absent"
        }
        self.module.params = params

        result = {"changed": True, "layers_versions": []}
        lambda_layer.delete_layer_version.return_value = result

        with pytest.raises(SystemExit):
            lambda_layer.execute_module(self.module, self.lambda_client)

        self.module.exit_json.assert_called_with(
            **result
        )
        self.module.fail_json_aws.assert_not_called()
        lambda_layer.delete_layer_version.assert_called_with(
            self.lambda_client, params, self.module.check_mode
        )
        lambda_layer.create_layer_version.assert_not_called()

    def test_failure(self):
        params = {
            "name": "test-layer", "state": "absent"
        }
        self.module.params = params

        exc = "lambdalayer_execute_module_exception"
        msg = "this_exception_is_used_for_unit_testing"
        lambda_layer.delete_layer_version.side_effect = raise_lambdalayer_exception(exc, msg)

        with pytest.raises(SystemExit):
            lambda_layer.execute_module(self.module, self.lambda_client)

        self.module.exit_json.assert_not_called()
        self.module.fail_json_aws.assert_called_with(
            exc, msg=msg
        )
