#
# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from unittest.mock import MagicMock, call, patch
from ansible_collections.amazon.aws.plugins.modules import lambda_layer


def raise_lambdalayer_exception(e=None, m=None):
    e = e or "lambda layer exc"
    m = m or "unit testing"
    return lambda_layer.LambdaLayerFailure(exc=e, msg=m)


mod_list_layer = "ansible_collections.amazon.aws.plugins.modules.lambda_layer.list_layer_versions"
mod_create_layer = "ansible_collections.amazon.aws.plugins.modules.lambda_layer.create_layer_version"
mod_delete_layer = "ansible_collections.amazon.aws.plugins.modules.lambda_layer.delete_layer_version"


@pytest.mark.parametrize(
    "params,api_result,calls,ansible_result",
    [
        ({"name": "testlayer", "version": 4}, [], [], {"changed": False, "layer_versions": []}),
        (
            {"name": "testlayer", "version": 4},
            [
                {
                    "compatible_runtimes": ["python3.7"],
                    "created_date": "2022-09-29T10:31:35.977+0000",
                    "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:2",
                    "license_info": "MIT",
                    "version": 2,
                    "compatible_architectures": ["arm64"],
                },
                {
                    "created_date": "2022-09-29T10:31:26.341+0000",
                    "description": "lambda layer first version",
                    "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:1",
                    "version": 1,
                },
            ],
            [],
            {"changed": False, "layer_versions": []},
        ),
        (
            {"name": "testlayer", "version": 2},
            [
                {
                    "compatible_runtimes": ["python3.7"],
                    "created_date": "2022-09-29T10:31:35.977+0000",
                    "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:2",
                    "license_info": "MIT",
                    "version": 2,
                    "compatible_architectures": ["arm64"],
                },
                {
                    "created_date": "2022-09-29T10:31:26.341+0000",
                    "description": "lambda layer first version",
                    "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:1",
                    "version": 1,
                },
            ],
            [call(LayerName="testlayer", VersionNumber=2)],
            {
                "changed": True,
                "layer_versions": [
                    {
                        "compatible_runtimes": ["python3.7"],
                        "created_date": "2022-09-29T10:31:35.977+0000",
                        "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:2",
                        "license_info": "MIT",
                        "version": 2,
                        "compatible_architectures": ["arm64"],
                    }
                ],
            },
        ),
        (
            {"name": "testlayer", "version": -1},
            [
                {
                    "compatible_runtimes": ["python3.7"],
                    "created_date": "2022-09-29T10:31:35.977+0000",
                    "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:2",
                    "license_info": "MIT",
                    "version": 2,
                    "compatible_architectures": ["arm64"],
                },
                {
                    "created_date": "2022-09-29T10:31:26.341+0000",
                    "description": "lambda layer first version",
                    "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:1",
                    "version": 1,
                },
            ],
            [call(LayerName="testlayer", VersionNumber=2), call(LayerName="testlayer", VersionNumber=1)],
            {
                "changed": True,
                "layer_versions": [
                    {
                        "compatible_runtimes": ["python3.7"],
                        "created_date": "2022-09-29T10:31:35.977+0000",
                        "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:2",
                        "license_info": "MIT",
                        "version": 2,
                        "compatible_architectures": ["arm64"],
                    },
                    {
                        "created_date": "2022-09-29T10:31:26.341+0000",
                        "description": "lambda layer first version",
                        "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:1",
                        "version": 1,
                    },
                ],
            },
        ),
    ],
)
@patch(mod_list_layer)
def test_delete_layer(m_list_layer, params, api_result, calls, ansible_result):
    lambda_client = MagicMock()
    lambda_client.delete_layer_version.return_value = None

    m_list_layer.return_value = api_result
    result = lambda_layer.delete_layer_version(lambda_client, params)
    assert result == ansible_result

    m_list_layer.assert_called_once_with(lambda_client, params.get("name"))

    if not calls:
        lambda_client.delete_layer_version.assert_not_called()
    else:
        lambda_client.delete_layer_version.assert_has_calls(calls, any_order=True)


@patch(mod_list_layer)
def test_delete_layer_check_mode(m_list_layer):
    lambda_client = MagicMock()
    lambda_client.delete_layer_version.return_value = None

    m_list_layer.return_value = [
        {
            "compatible_runtimes": ["python3.7"],
            "created_date": "2022-09-29T10:31:35.977+0000",
            "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:2",
            "license_info": "MIT",
            "version": 2,
            "compatible_architectures": ["arm64"],
        },
        {
            "created_date": "2022-09-29T10:31:26.341+0000",
            "description": "lambda layer first version",
            "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:1",
            "version": 1,
        },
    ]
    params = {"name": "testlayer", "version": -1}
    result = lambda_layer.delete_layer_version(lambda_client, params, check_mode=True)
    ansible_result = {
        "changed": True,
        "layer_versions": [
            {
                "compatible_runtimes": ["python3.7"],
                "created_date": "2022-09-29T10:31:35.977+0000",
                "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:2",
                "license_info": "MIT",
                "version": 2,
                "compatible_architectures": ["arm64"],
            },
            {
                "created_date": "2022-09-29T10:31:26.341+0000",
                "description": "lambda layer first version",
                "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:1",
                "version": 1,
            },
        ],
    }
    assert result == ansible_result

    m_list_layer.assert_called_once_with(lambda_client, params.get("name"))
    lambda_client.delete_layer_version.assert_not_called()


@patch(mod_list_layer)
def test_delete_layer_failure(m_list_layer):
    lambda_client = MagicMock()
    lambda_client.delete_layer_version.side_effect = raise_lambdalayer_exception()

    m_list_layer.return_value = [
        {
            "created_date": "2022-09-29T10:31:26.341+0000",
            "description": "lambda layer first version",
            "layer_version_arn": "arn:aws:lambda:eu-west-2:123456789012:layer:testlayer:1",
            "version": 1,
        }
    ]
    params = {"name": "testlayer", "version": 1}
    with pytest.raises(lambda_layer.LambdaLayerFailure):
        lambda_layer.delete_layer_version(lambda_client, params)


@pytest.mark.parametrize("b_s3content", [(True), (False)])
@patch(mod_list_layer)
def test_create_layer(m_list_layer, b_s3content, tmp_path):
    params = {
        "name": "testlayer",
        "description": "ansible units testing sample layer",
        "content": {},
        "license_info": "MIT",
    }

    lambda_client = MagicMock()

    lambda_client.publish_layer_version.return_value = {
        "CompatibleRuntimes": [
            "python3.6",
            "python3.7",
        ],
        "Content": {
            "CodeSha256": "tv9jJO+rPbXUUXuRKi7CwHzKtLDkDRJLB3cC3Z/ouXo=",
            "CodeSize": 169,
            "Location": (
                "https://awslambda-us-west-2-layers.s3.us-west-2.amazonaws.com/snapshots/123456789012/my-layer-4aaa2fbb"
            ),
        },
        "CreatedDate": "2018-11-14T23:03:52.894+0000",
        "Description": "ansible units testing sample layer",
        "LayerArn": "arn:aws:lambda:us-west-2:123456789012:layer:my-layer",
        "LayerVersionArn": "arn:aws:lambda:us-west-2:123456789012:layer:testlayer:1",
        "LicenseInfo": "MIT",
        "Version": 1,
        "ResponseMetadata": {
            "http_header": "true",
        },
    }

    expected = {
        "changed": True,
        "layer_versions": [
            {
                "compatible_runtimes": ["python3.6", "python3.7"],
                "content": {
                    "code_sha256": "tv9jJO+rPbXUUXuRKi7CwHzKtLDkDRJLB3cC3Z/ouXo=",
                    "code_size": 169,
                    "location": "https://awslambda-us-west-2-layers.s3.us-west-2.amazonaws.com/snapshots/123456789012/my-layer-4aaa2fbb",
                },
                "created_date": "2018-11-14T23:03:52.894+0000",
                "description": "ansible units testing sample layer",
                "layer_arn": "arn:aws:lambda:us-west-2:123456789012:layer:my-layer",
                "layer_version_arn": "arn:aws:lambda:us-west-2:123456789012:layer:testlayer:1",
                "license_info": "MIT",
                "version": 1,
            }
        ],
    }

    if b_s3content:
        params["content"] = {"s3_bucket": "mybucket", "s3_key": "mybucket-key", "s3_object_version": "v1"}
        content_arg = {"S3Bucket": "mybucket", "S3Key": "mybucket-key", "S3ObjectVersion": "v1"}
    else:
        binary_data = b"simple lambda layer content"
        test_dir = tmp_path / "lambda_layer"
        test_dir.mkdir()
        zipfile = test_dir / "lambda.zip"
        zipfile.write_bytes(binary_data)

        params["content"] = {"zip_file": str(zipfile)}
        content_arg = {
            "ZipFile": binary_data,
        }

    result = lambda_layer.create_layer_version(lambda_client, params)

    assert result == expected

    lambda_client.publish_layer_version.assert_called_with(
        LayerName="testlayer",
        Description="ansible units testing sample layer",
        LicenseInfo="MIT",
        Content=content_arg,
    )

    m_list_layer.assert_not_called()


@patch(mod_list_layer)
def test_create_layer_check_mode(m_list_layer):
    params = {
        "name": "testlayer",
        "description": "ansible units testing sample layer",
        "content": {"s3_bucket": "mybucket", "s3_key": "mybucket-key", "s3_object_version": "v1"},
        "license_info": "MIT",
    }

    lambda_client = MagicMock()

    result = lambda_layer.create_layer_version(lambda_client, params, check_mode=True)
    assert result == {"msg": "Create operation skipped - running in check mode", "changed": True}

    m_list_layer.assert_not_called()
    lambda_client.publish_layer_version.assert_not_called()


def test_create_layer_failure():
    params = {
        "name": "testlayer",
        "description": "ansible units testing sample layer",
        "content": {"s3_bucket": "mybucket", "s3_key": "mybucket-key", "s3_object_version": "v1"},
        "compatible_runtimes": ["nodejs", "python3.9"],
        "compatible_architectures": ["x86_64", "arm64"],
    }
    lambda_client = MagicMock()
    lambda_client.publish_layer_version.side_effect = raise_lambdalayer_exception()

    with pytest.raises(lambda_layer.LambdaLayerFailure):
        lambda_layer.create_layer_version(lambda_client, params)


def test_create_layer_using_unexisting_file():
    params = {
        "name": "testlayer",
        "description": "ansible units testing sample layer",
        "content": {
            "zip_file": "this_file_does_not_exist",
        },
        "compatible_runtimes": ["nodejs", "python3.9"],
        "compatible_architectures": ["x86_64", "arm64"],
    }

    lambda_client = MagicMock()

    lambda_client.publish_layer_version.return_value = {}
    with pytest.raises(FileNotFoundError):
        lambda_layer.create_layer_version(lambda_client, params)

    lambda_client.publish_layer_version.assert_not_called()


@pytest.mark.parametrize(
    "params,failure",
    [
        ({"name": "test-layer"}, False),
        ({"name": "test-layer", "state": "absent"}, False),
        ({"name": "test-layer"}, True),
        ({"name": "test-layer", "state": "absent"}, True),
    ],
)
@patch(mod_create_layer)
@patch(mod_delete_layer)
def test_execute_module(m_delete_layer, m_create_layer, params, failure):
    module = MagicMock()
    module.params = params
    module.check_mode = False
    module.exit_json.side_effect = SystemExit(1)
    module.fail_json_aws.side_effect = SystemExit(2)

    lambda_client = MagicMock()

    state = params.get("state", "present")
    result = {"changed": True, "layers_versions": {}}

    if not failure:
        if state == "present":
            m_create_layer.return_value = result
            with pytest.raises(SystemExit):
                lambda_layer.execute_module(module, lambda_client)

            module.exit_json.assert_called_with(**result)
            module.fail_json_aws.assert_not_called()
            m_create_layer.assert_called_with(lambda_client, params, module.check_mode)
            m_delete_layer.assert_not_called()

        elif state == "absent":
            m_delete_layer.return_value = result
            with pytest.raises(SystemExit):
                lambda_layer.execute_module(module, lambda_client)

            module.exit_json.assert_called_with(**result)
            module.fail_json_aws.assert_not_called()
            m_delete_layer.assert_called_with(lambda_client, params, module.check_mode)
            m_create_layer.assert_not_called()
    else:
        exc = "lambdalayer_execute_module_exception"
        msg = "this_exception_is_used_for_unit_testing"
        m_create_layer.side_effect = raise_lambdalayer_exception(exc, msg)
        m_delete_layer.side_effect = raise_lambdalayer_exception(exc, msg)

        with pytest.raises(SystemExit):
            lambda_layer.execute_module(module, lambda_client)

        module.exit_json.assert_not_called()
        module.fail_json_aws.assert_called_with(exc, msg=msg)
