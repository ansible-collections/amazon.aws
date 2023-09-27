# (c) 2022 Red Hat Inc.

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import botocore.exceptions
import pytest

from ansible_collections.amazon.aws.plugins.modules import s3_object

module_name = "ansible_collections.amazon.aws.plugins.modules.s3_object"
utils = "ansible_collections.amazon.aws.plugins.module_utils.ec2"


@patch(module_name + ".paginated_list")
def test_list_keys_success(m_paginated_list):
    s3 = MagicMock()

    m_paginated_list.return_value = ["delete.txt"]

    assert ["delete.txt"] == s3_object.list_keys(s3, "a987e6b6026ab04e4717", "", "", 1000)
    m_paginated_list.assert_called_once()


@patch(module_name + ".paginated_list")
def test_list_keys_failure(m_paginated_list):
    s3 = MagicMock()

    m_paginated_list.side_effect = botocore.exceptions.BotoCoreError

    with pytest.raises(s3_object.S3ObjectFailure):
        s3_object.list_keys(s3, "a987e6b6026ab04e4717", "", "", 1000)


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


@patch(module_name + ".paginated_list")
@patch(module_name + ".list_keys")
def test_s3_object_do_list_success(m_paginated_list, m_list_keys):
    module = MagicMock()
    s3 = MagicMock()

    m_paginated_list.return_value = ["delete.txt"]
    var_dict = {
        "bucket": "a987e6b6026ab04e4717",
        "prefix": "",
        "marker": "",
        "max_keys": 1000,
        "bucketrtn": True,
    }

    s3_object.s3_object_do_list(module, s3, s3, var_dict)
    assert m_paginated_list.call_count == 1
    # assert m_list_keys.call_count == 1
    # module.exit_json.assert_called_with(msg="LIST operation complete", s3_keys=['delete.txt'])


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
