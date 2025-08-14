# (c) 2022 Red Hat Inc.

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

from ansible_collections.amazon.aws.plugins.modules import s3_object

module_name = "ansible_collections.amazon.aws.plugins.modules.s3_object"
utils = "ansible_collections.amazon.aws.plugins.module_utils.ec2"


@patch(module_name + ".delete_key")
def test_s3_object_do_delobj_success(m_delete_key):
    module = MagicMock()
    s3 = MagicMock()
    var_dict = {
        "object": "/usr/local/myfile.txt",
        "bucket": "a987e6b6026ab04e4717",
    }
    s3_object.s3_object_do_delobj(module, s3, s3, var_dict)
    assert m_delete_key.call_count == 1
    module.exit_json.assert_called_with(msg="Object deleted from bucket a987e6b6026ab04e4717.", changed=True)


@patch(module_name + ".delete_key")
def test_s3_object_do_delobj_failure_nobucket(m_delete_key):
    module = MagicMock()
    s3 = MagicMock()

    var_dict = {"object": "/usr/local/myfile.txt", "bucket": ""}
    s3_object.s3_object_do_delobj(module, s3, s3, var_dict)
    assert m_delete_key.call_count == 0
    module.fail_json.assert_called_with(msg="Bucket parameter is required.")


@patch(module_name + ".delete_key")
def test_s3_object_do_delobj_failure_noobj(m_delete_key):
    module = MagicMock()
    s3 = MagicMock()
    var_dict = {"bucket": "a987e6b6026ab04e4717", "object": ""}
    s3_object.s3_object_do_delobj(module, s3, s3, var_dict)
    assert m_delete_key.call_count == 0
    module.fail_json.assert_called_with(msg="object parameter is required")


@patch(utils + ".get_aws_connection_info")
def test_populate_params(m_get_aws_connection_info):
    module = MagicMock()
    m_get_aws_connection_info.return_value = (
        "us-east-1",
        None,
        {
            "aws_access_key_id": "xxxx",
            "aws_secret_access_key": "yyyy",
            "aws_session_token": "zzzz",
            "verify": True,
        },
    )

    module.params = {
        "bucket": "4a6cfe3c17b798613fa77b462e402984",
        "ceph": False,
        "content": None,
        "content_base64": None,
        "copy_src": None,
        "debug_botocore_endpoint_logs": True,
        "dest": None,
        "dualstack": False,
        "encrypt": True,
        "encryption_kms_key_id": None,
        "encryption_mode": "AES256",
        "endpoint_url": None,
        "expiry": 600,
        "headers": None,
        "ignore_nonexistent_bucket": False,
        "marker": "",
        "max_keys": 1000,
        "metadata": None,
        "mode": "create",
        "object": None,
        "overwrite": "latest",
        "permission": ["private"],
        "prefix": "",
        "profile": None,
        "purge_tags": True,
        "region": "us-east-1",
        "retries": 0,
        "sig_v4": True,
        "src": None,
        "tags": None,
        "validate_bucket_name": False,
        "validate_certs": True,
        "version": None,
    }
    result = s3_object.populate_params(module)
    for k, v in module.params.items():
        assert result[k] == v

    module.params.update({"object": "example.txt", "mode": "get"})
    result = s3_object.populate_params(module)
    assert result["object"] == "example.txt"

    module.params.update({"object": "/example.txt", "mode": "get"})
    result = s3_object.populate_params(module)
    assert result["object"] == "example.txt"

    module.params.update({"object": "example.txt", "mode": "delete"})
    result = s3_object.populate_params(module)
    module.fail_json.assert_called_with(msg="Parameter object cannot be used with mode=delete")


def _base_module_mock():
    module = MagicMock()
    module.check_mode = False
    module.params = {
        "permission": ["private"],
        "encryption_mode": "AES256",
        "encryption_kms_key_id": None,
        "tags": None,
    }
    return module


def _headers_fixture():
    return {
        "ContentType": "text/html; charset=utf-8",
        "ContentDisposition": "inline",
        "CacheControl": "max-age=0",
        "X-Custom-Header": "custom",
    }


def test_upload_content_headers_promoted_to_extraargs():
    module = _base_module_mock()
    s3 = MagicMock()

    headers = _headers_fixture()

    s3_object.upload_s3file(
        module,
        s3,
        bucket="my-bucket",
        obj="index.html",
        expiry=600,
        metadata=None,
        encrypt=True,
        headers=headers,
        src=None,
        content=b"<html></html>",
        acl_disabled=False,
    )

    # With in-memory content we now use put_object to ensure headers are honored
    assert s3.put_object.call_count == 1
    # Extract kwargs for verification
    call_args, kwargs = s3.put_object.call_args
    # With put_object, promoted headers are top-level kwargs, not under ExtraArgs
    assert kwargs["ContentType"] == headers["ContentType"]
    assert kwargs["ContentDisposition"] == headers["ContentDisposition"]
    assert kwargs["CacheControl"] == headers["CacheControl"]
    assert kwargs["ServerSideEncryption"] == "AES256"
    assert "Metadata" in kwargs and kwargs["Metadata"]["X-Custom-Header"] == "custom"


def test_upload_src_headers_promoted_to_extraargs():
    module = _base_module_mock()
    s3 = MagicMock()

    headers = _headers_fixture()

    s3_object.upload_s3file(
        module,
        s3,
        bucket="my-bucket",
        obj="index.html",
        expiry=600,
        metadata=None,
        encrypt=True,
        headers=headers,
        src="/tmp/index.html",
        content=None,
        acl_disabled=False,
    )

    assert s3.upload_file.call_count == 1
    call_args, kwargs = s3.upload_file.call_args
    extra = kwargs.get("ExtraArgs")

    assert extra["ContentType"] == headers["ContentType"]
    assert extra["ContentDisposition"] == headers["ContentDisposition"]
    assert extra["CacheControl"] == headers["CacheControl"]
    assert extra["ServerSideEncryption"] == "AES256"
    assert extra.get("Metadata") is not None
    assert extra["Metadata"]["X-Custom-Header"] == "custom"
