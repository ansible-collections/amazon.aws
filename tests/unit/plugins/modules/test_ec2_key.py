# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import datetime
from dateutil.tz import tzutc
import pytest
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import ANY

import botocore

from ansible.module_utils._text import to_bytes

from ansible_collections.amazon.aws.plugins.modules import ec2_key

module_name = "ansible_collections.amazon.aws.plugins.modules.ec2_key"


def raise_botocore_exception_clienterror(action):
    params = {
        "Error": {"Code": 1, "Message": "error creating key"},
        "ResponseMetadata": {"RequestId": "01234567-89ab-cdef-0123-456789abcdef"},
    }

    if action == "create_key_pair":
        params["Error"]["Message"] = "error creating key"

    elif action == "describe_key_pair":
        params["Error"]["Code"] = "InvalidKeyPair.NotFound"
        params["Error"]["Message"] = "The key pair does not exist"

    elif action == "import_key_pair":
        params["Error"]["Message"] = "error importing key"

    elif action == "delete_key_pair":
        params["Error"]["Message"] = "error deleting key"

    return botocore.exceptions.ClientError(params, action)


def test__import_key_pair():
    ec2_client = MagicMock()
    name = "my_keypair"
    key_material = "ssh-rsa AAAAB3NzaC1yc2EAA email@example.com"

    expected_params = {
        "KeyName": name,
        "PublicKeyMaterial": to_bytes(key_material),
    }

    ec2_client.import_key_pair.return_value = {
        "KeyFingerprint": "d7:ff:a6:63:18:64:9c:57:a1:ee:ca:a4:ad:c2:81:62",
        "KeyName": "my_keypair",
        "KeyPairId": "key-012345678905a208d",
    }

    result = ec2_key._import_key_pair(ec2_client, name, key_material)

    assert result == ec2_client.import_key_pair.return_value
    assert ec2_client.import_key_pair.call_count == 1
    ec2_client.import_key_pair.assert_called_with(aws_retry=True, **expected_params)


def test_api_failure__import_key_pair():
    ec2_client = MagicMock()
    name = "my_keypair"
    key_material = "ssh-rsa AAAAB3NzaC1yc2EAA email@example.com"

    expected_params = {
        "KeyName": name,
        "PublicKeyMaterial": to_bytes(key_material),
    }

    ec2_client.import_key_pair.side_effect = raise_botocore_exception_clienterror("import_key_pair")

    with pytest.raises(ec2_key.Ec2KeyFailure):
        ec2_key._import_key_pair(ec2_client, name, key_material)


def test_extract_key_data_describe_key_pairs():
    key = {
        "CreateTime": datetime.datetime(2022, 9, 15, 20, 10, 15, tzinfo=tzutc()),
        "KeyFingerprint": "11:12:13:14:bb:26:85:b2:e8:39:27:bc:ee:aa:ff:ee:dd:cc:bb:aa",
        "KeyName": "my_keypair",
        "KeyPairId": "key-043046ef2a9a80b56",
        "Tags": [],
    }

    key_type = "rsa"

    expected_result = {
        "name": "my_keypair",
        "fingerprint": "11:12:13:14:bb:26:85:b2:e8:39:27:bc:ee:aa:ff:ee:dd:cc:bb:aa",
        "id": "key-043046ef2a9a80b56",
        "tags": {},
        "type": "rsa",
    }

    result = ec2_key.extract_key_data(key, key_type)

    assert result == expected_result


def test_extract_key_data_create_key_pair():
    key = {
        "KeyFingerprint": "11:12:13:14:bb:26:85:b2:e8:39:27:bc:ee:aa:ff:ee:dd:cc:bb:aa",
        "KeyName": "my_keypair",
        "KeyPairId": "key-043046ef2a9a80b56",
    }

    key_type = "rsa"

    expected_result = {
        "name": "my_keypair",
        "fingerprint": "11:12:13:14:bb:26:85:b2:e8:39:27:bc:ee:aa:ff:ee:dd:cc:bb:aa",
        "id": "key-043046ef2a9a80b56",
        "tags": {},
        "type": "rsa",
    }

    result = ec2_key.extract_key_data(key, key_type)

    assert result == expected_result


@patch(module_name + ".delete_key_pair")
@patch(module_name + "._import_key_pair")
@patch(module_name + ".find_key_pair")
def test_get_key_fingerprint(m_find_key_pair, m_import_key_pair, m_delete_key_pair):
    module = MagicMock()
    ec2_client = MagicMock()

    m_find_key_pair.return_value = None

    m_import_key_pair.return_value = {
        "KeyFingerprint": "d7:ff:a6:63:18:64:9c:57:a1:ee:ca:a4:ad:c2:81:62",
        "KeyName": "my_keypair",
        "KeyPairId": "key-043046ef2a9a80b56",
    }

    m_delete_key_pair.return_value = {"changed": True, "key": None, "msg": "key deleted"}

    expected_result = "d7:ff:a6:63:18:64:9c:57:a1:ee:ca:a4:ad:c2:81:62"

    key_material = "ssh-rsa AAAAB3NzaC1yc2EAA email@example.com"

    result = ec2_key.get_key_fingerprint(module, ec2_client, key_material)

    assert result == expected_result
    assert m_find_key_pair.call_count == 1
    assert m_import_key_pair.call_count == 1
    assert m_delete_key_pair.call_count == 1


def test_find_key_pair():
    ec2_client = MagicMock()
    name = "my_keypair"

    ec2_client.describe_key_pairs.return_value = {
        "KeyPairs": [
            {
                "CreateTime": datetime.datetime(2022, 9, 15, 20, 10, 15, tzinfo=tzutc()),
                "KeyFingerprint": "11:12:13:14:bb:26:85:b2:e8:39:27:bc:ee:aa:ff:ee:dd:cc:bb:aa",
                "KeyName": "my_keypair",
                "KeyPairId": "key-043046ef2a9a80b56",
                "KeyType": "rsa",
                "Tags": [],
            }
        ],
    }

    ec2_key.find_key_pair(ec2_client, name)

    assert ec2_client.describe_key_pairs.call_count == 1
    ec2_client.describe_key_pairs.assert_called_with(aws_retry=True, KeyNames=[name])


def test_api_failure_find_key_pair():
    ec2_client = MagicMock()
    name = "non_existing_keypair"

    ec2_client.describe_key_pairs.side_effect = botocore.exceptions.BotoCoreError

    with pytest.raises(ec2_key.Ec2KeyFailure):
        ec2_key.find_key_pair(ec2_client, name)


def test_invalid_key_pair_find_key_pair():
    ec2_client = MagicMock()
    name = "non_existing_keypair"

    ec2_client.describe_key_pairs.side_effect = raise_botocore_exception_clienterror("describe_key_pair")

    result = ec2_key.find_key_pair(ec2_client, name)

    assert result is None


def test__create_key_pair():
    ec2_client = MagicMock()
    name = "my_keypair"
    tag_spec = None
    key_type = None

    expected_params = {"KeyName": name}

    ec2_client.create_key_pair.return_value = {
        "KeyFingerprint": "d7:ff:a6:63:18:64:9c:57:a1:ee:ca:a4:ad:c2:81:62",
        "KeyMaterial": (
            "-----BEGIN RSA PRIVATE KEY-----\n"  # gitleaks:allow
            "MIIEXm7/Bi9wba2m0Qtclu\nCXQw2paSIZb\n"
            "-----END RSA PRIVATE KEY-----"
        ),
        "KeyName": "my_keypair",
        "KeyPairId": "key-012345678905a208d",
    }

    result = ec2_key._create_key_pair(ec2_client, name, tag_spec, key_type)

    assert result == ec2_client.create_key_pair.return_value
    assert ec2_client.create_key_pair.call_count == 1
    ec2_client.create_key_pair.assert_called_with(aws_retry=True, **expected_params)


def test_api_failure__create_key_pair():
    ec2_client = MagicMock()
    name = "my_keypair"
    tag_spec = None
    key_type = None

    ec2_client.create_key_pair.side_effect = raise_botocore_exception_clienterror("create_key_pair")

    with pytest.raises(ec2_key.Ec2KeyFailure):
        ec2_key._create_key_pair(ec2_client, name, tag_spec, key_type)


@patch(module_name + ".extract_key_data")
@patch(module_name + "._import_key_pair")
def test_create_new_key_pair_key_material(m_import_key_pair, m_extract_key_data):
    module = MagicMock()
    ec2_client = MagicMock()

    name = "my_keypair"
    key_material = "ssh-rsa AAAAB3NzaC1yc2EAA email@example.com"
    key_type = "rsa"
    tags = None

    module.check_mode = False

    m_import_key_pair.return_value = {
        "KeyFingerprint": "d7:ff:a6:63:18:64:9c:57:a1:ee:ca:a4:ad:c2:81:62",
        "KeyName": "my_keypair",
        "KeyPairId": "key-012345678905a208d",
    }

    m_extract_key_data.return_value = {
        "name": "my_keypair",
        "fingerprint": "11:12:13:14:bb:26:85:b2:e8:39:27:bc:ee:aa:ff:ee:dd:cc:bb:aa",
        "id": "key-043046ef2a9a80b56",
        "tags": {},
        "type": "rsa",
    }

    expected_result = {"changed": True, "key": m_extract_key_data.return_value, "msg": "key pair created"}

    result = ec2_key.create_new_key_pair(ec2_client, name, key_material, key_type, tags, module.check_mode)

    assert result == expected_result
    assert m_import_key_pair.call_count == 1
    assert m_extract_key_data.call_count == 1


@patch(module_name + ".extract_key_data")
@patch(module_name + "._create_key_pair")
def test_create_new_key_pair_no_key_material(m_create_key_pair, m_extract_key_data):
    module = MagicMock()
    ec2_client = MagicMock()

    name = "my_keypair"
    key_type = "rsa"
    key_material = None
    tags = None

    module.check_mode = False

    m_create_key_pair.return_value = {
        "KeyFingerprint": "d7:ff:a6:63:18:64:9c:57:a1:ee:ca:a4:ad:c2:81:62",
        "KeyName": "my_keypair",
        "KeyPairId": "key-012345678905a208d",
    }

    m_extract_key_data.return_value = {
        "name": "my_keypair",
        "fingerprint": "11:12:13:14:bb:26:85:b2:e8:39:27:bc:ee:aa:ff:ee:dd:cc:bb:aa",
        "id": "key-043046ef2a9a80b56",
        "tags": {},
        "type": "rsa",
    }

    expected_result = {"changed": True, "key": m_extract_key_data.return_value, "msg": "key pair created"}

    result = ec2_key.create_new_key_pair(ec2_client, name, key_material, key_type, tags, module.check_mode)

    assert result == expected_result
    assert m_create_key_pair.call_count == 1
    assert m_extract_key_data.call_count == 1


def test__delete_key_pair():
    ec2_client = MagicMock()

    key_name = "my_keypair"
    ec2_key._delete_key_pair(ec2_client, key_name)

    assert ec2_client.delete_key_pair.call_count == 1
    ec2_client.delete_key_pair.assert_called_with(aws_retry=True, KeyName=key_name)


def test_api_failure__delete_key_pair():
    ec2_client = MagicMock()
    name = "my_keypair"

    ec2_client.delete_key_pair.side_effect = raise_botocore_exception_clienterror("delete_key_pair")

    with pytest.raises(ec2_key.Ec2KeyFailure):
        ec2_key._delete_key_pair(ec2_client, name)


@patch(module_name + ".extract_key_data")
@patch(module_name + "._import_key_pair")
@patch(module_name + ".delete_key_pair")
@patch(module_name + ".get_key_fingerprint")
def test_update_key_pair_by_key_material_update_needed(
    m_get_key_fingerprint, m_delete_key_pair, m__import_key_pair, m_extract_key_data
):
    module = MagicMock()
    ec2_client = MagicMock()

    name = "my_keypair"
    key_material = "ssh-rsa AAAAB3NzaC1yc2EAA email@example.com"
    tag_spec = None
    key = {
        "KeyName": "my_keypair",
        "KeyFingerprint": "11:12:13:14:bb:26:85:b2:e8:39:27:bc:ee:aa:ff:ee:dd:cc:bb:aa",
        "KeyPairId": "key-043046ef2a9a80b56",
        "Tags": {},
    }

    module.check_mode = False

    m_get_key_fingerprint.return_value = "d7:ff:a6:63:18:64:9c:57:a1:ee:ca:a4:ad:c2:81:62"
    m_delete_key_pair.return_value = None
    m__import_key_pair.return_value = {
        "KeyFingerprint": "11:12:13:14:bb:26:85:b2:e8:39:27:bc:ee:aa:ff:ee:dd:cc:bb:aa",
        "KeyName": "my_keypair",
        "KeyPairId": "key-043046ef2a9a80b56",
        "Tags": {},
    }
    m_extract_key_data.return_value = {
        "name": "my_keypair",
        "fingerprint": "d7:ff:a6:63:18:64:9c:57:a1:ee:ca:a4:ad:c2:81:62",
        "id": "key-012345678905a208d",
        "tags": {},
    }

    expected_result = {"changed": True, "key": m_extract_key_data.return_value, "msg": "key pair updated"}

    result = ec2_key.update_key_pair_by_key_material(module.check_mode, ec2_client, name, key, key_material, tag_spec)

    assert result == expected_result
    assert m_get_key_fingerprint.call_count == 1
    assert m_delete_key_pair.call_count == 1
    assert m__import_key_pair.call_count == 1
    assert m_extract_key_data.call_count == 1
    m_get_key_fingerprint.assert_called_with(module.check_mode, ec2_client, key_material)
    m_delete_key_pair.assert_called_with(module.check_mode, ec2_client, name, finish_task=False)
    m__import_key_pair.assert_called_with(ec2_client, name, key_material, tag_spec)
    m_extract_key_data.assert_called_with(key)


@patch(module_name + ".extract_key_data")
@patch(module_name + ".get_key_fingerprint")
def test_update_key_pair_by_key_material_key_exists(m_get_key_fingerprint, m_extract_key_data):
    ec2_client = MagicMock()

    key_material = MagicMock()
    key_fingerprint = MagicMock()
    tag_spec = MagicMock()
    key_id = MagicMock()
    key_name = MagicMock()
    key = {
        "KeyName": key_name,
        "KeyFingerprint": key_fingerprint,
        "KeyPairId": key_id,
        "Tags": {},
    }

    check_mode = False
    m_get_key_fingerprint.return_value = key_fingerprint
    m_extract_key_data.return_value = {
        "name": key_name,
        "fingerprint": key_fingerprint,
        "id": key_id,
        "tags": {},
    }

    expected_result = {"changed": False, "key": m_extract_key_data.return_value, "msg": "key pair already exists"}

    assert expected_result == ec2_key.update_key_pair_by_key_material(
        check_mode, ec2_client, key_name, key, key_material, tag_spec
    )

    m_get_key_fingerprint.assert_called_once_with(check_mode, ec2_client, key_material)
    m_extract_key_data.assert_called_once_with(key)


@patch(module_name + ".extract_key_data")
@patch(module_name + "._create_key_pair")
@patch(module_name + ".delete_key_pair")
def test_update_key_pair_by_key_type_update_needed(m_delete_key_pair, m__create_key_pair, m_extract_key_data):
    module = MagicMock()
    ec2_client = MagicMock()

    name = "my_keypair"
    key_type = "rsa"
    tag_spec = None

    module.check_mode = False

    m_delete_key_pair.return_value = None
    m__create_key_pair.return_value = {
        "KeyFingerprint": "11:12:13:14:bb:26:85:b2:e8:39:27:bc:ee:aa:ff:ee:dd:cc:bb:aa",
        "Name": "my_keypair",
        "Id": "key-043046ef2a9a80b56",
        "Tags": {},
        "Type": "rsa",
    }
    m_extract_key_data.return_value = {
        "name": "my_keypair",
        "fingerprint": "11:12:13:14:bb:26:85:b2:e8:39:27:bc:ee:aa:ff:ee:dd:cc:bb:aa",
        "id": "key-043046ef2a9a80b56",
        "tags": {},
        "type": "rsa",
    }

    expected_result = {"changed": True, "key": m_extract_key_data.return_value, "msg": "key pair updated"}

    result = ec2_key.update_key_pair_by_key_type(module.check_mode, ec2_client, name, key_type, tag_spec)

    assert result == expected_result
    assert m_delete_key_pair.call_count == 1
    assert m__create_key_pair.call_count == 1
    assert m_extract_key_data.call_count == 1
    m_delete_key_pair.assert_called_with(module.check_mode, ec2_client, name, finish_task=False)
    m__create_key_pair.assert_called_with(ec2_client, name, tag_spec, key_type)
    m_extract_key_data.assert_called_with(m__create_key_pair.return_value, key_type)


@patch(module_name + ".update_key_pair_by_key_material")
def test_handle_existing_key_pair_update_key_matrial_with_force(m_update_key_pair_by_key_material):
    module = MagicMock()
    ec2_client = MagicMock()

    name = "my_keypair"
    key = {
        "KeyName": "my_keypair",
        "KeyFingerprint": "11:12:13:14:bb:26:85:b2:e8:39:27:bc:ee:aa:ff:ee:dd:cc:bb:aa",
        "KeyPairId": "key-043046ef2a9a80b56",
        "Tags": {},
        "KeyType": "rsa",
    }

    module.params = {
        "key_material": "ssh-rsa AAAAB3NzaC1yc2EAA email@example.com",
        "force": True,
        "key_type": "rsa",
        "tags": None,
        "purge_tags": True,
        "tag_spec": None,
    }

    key_data = {
        "name": "my_keypair",
        "fingerprint": "d7:ff:a6:63:18:64:9c:57:a1:ee:ca:a4:ad:c2:81:62",
        "id": "key-012345678905a208d",
        "tags": {},
    }

    m_update_key_pair_by_key_material.return_value = {"changed": True, "key": key_data, "msg": "key pair updated"}

    expected_result = {"changed": True, "key": key_data, "msg": "key pair updated"}

    result = ec2_key.handle_existing_key_pair_update(module, ec2_client, name, key)

    assert result == expected_result
    assert m_update_key_pair_by_key_material.call_count == 1


@patch(module_name + ".update_key_pair_by_key_type")
def test_handle_existing_key_pair_update_key_type(m_update_key_pair_by_key_type):
    module = MagicMock()
    ec2_client = MagicMock()

    name = "my_keypair"
    key = {
        "KeyName": "my_keypair",
        "KeyFingerprint": "11:12:13:14:bb:26:85:b2:e8:39:27:bc:ee:aa:ff:ee:dd:cc:bb:aa",
        "KeyPairId": "key-043046ef2a9a80b56",
        "Tags": {},
        "KeyType": "ed25519",
    }

    module.params = {
        "key_material": "ssh-rsa AAAAB3NzaC1yc2EAA email@example.com",
        "force": False,
        "key_type": "rsa",
        "tags": None,
        "purge_tags": True,
        "tag_spec": None,
    }

    key_data = {
        "name": "my_keypair",
        "fingerprint": "d7:ff:a6:63:18:64:9c:57:a1:ee:ca:a4:ad:c2:81:62",
        "id": "key-012345678905a208d",
        "tags": {},
    }

    m_update_key_pair_by_key_type.return_value = {"changed": True, "key": key_data, "msg": "key pair updated"}

    expected_result = {"changed": True, "key": key_data, "msg": "key pair updated"}

    result = ec2_key.handle_existing_key_pair_update(module, ec2_client, name, key)

    assert result == expected_result
    assert m_update_key_pair_by_key_type.call_count == 1


@patch(module_name + ".extract_key_data")
def test_handle_existing_key_pair_else(m_extract_key_data):
    module = MagicMock()
    ec2_client = MagicMock()

    name = "my_keypair"
    key = {
        "KeyName": "my_keypair",
        "KeyFingerprint": "11:12:13:14:bb:26:85:b2:e8:39:27:bc:ee:aa:ff:ee:dd:cc:bb:aa",
        "KeyPairId": "key-043046ef2a9a80b56",
        "Tags": {},
        "KeyType": "rsa",
    }

    module.params = {
        "key_material": "ssh-rsa AAAAB3NzaC1yc2EAA email@example.com",
        "force": False,
        "key_type": "rsa",
        "tags": None,
        "purge_tags": True,
        "tag_spec": None,
    }

    m_extract_key_data.return_value = {
        "name": "my_keypair",
        "fingerprint": "11:12:13:14:bb:26:85:b2:e8:39:27:bc:ee:aa:ff:ee:dd:cc:bb:aa",
        "id": "key-043046ef2a9a80b56",
        "tags": {},
        "type": "rsa",
    }

    expected_result = {"changed": False, "key": m_extract_key_data.return_value, "msg": "key pair already exists"}

    result = ec2_key.handle_existing_key_pair_update(module, ec2_client, name, key)

    assert result == expected_result
    assert m_extract_key_data.call_count == 1


@patch(module_name + "._delete_key_pair")
@patch(module_name + ".find_key_pair")
def test_delete_key_pair_key_exists(m_find_key_pair, m_delete_key_pair):
    module = MagicMock()
    ec2_client = MagicMock()

    name = "my_keypair"

    module.check_mode = False

    m_find_key_pair.return_value = {
        "KeyPairs": [
            {
                "CreateTime": datetime.datetime(2022, 9, 15, 20, 10, 15, tzinfo=tzutc()),
                "KeyFingerprint": "11:12:13:14:bb:26:85:b2:e8:39:27:bc:ee:aa:ff:ee:dd:cc:bb:aa",
                "KeyName": "my_keypair",
                "KeyPairId": "key-043046ef2a9a80b56",
                "KeyType": "rsa",
                "Tags": [],
            }
        ],
    }

    expected_result = {"changed": True, "key": None, "msg": "key deleted"}

    result = ec2_key.delete_key_pair(module.check_mode, ec2_client, name)

    assert m_find_key_pair.call_count == 1
    m_find_key_pair.assert_called_with(ec2_client, name)
    assert m_delete_key_pair.call_count == 1
    m_delete_key_pair.assert_called_with(ec2_client, name)
    assert result == expected_result


@patch(module_name + "._delete_key_pair")
@patch(module_name + ".find_key_pair")
def test_delete_key_pair_key_not_exist(m_find_key_pair, m_delete_key_pair):
    module = MagicMock()
    ec2_client = MagicMock()

    name = "my_keypair"

    module.check_mode = False

    m_find_key_pair.return_value = None

    expected_result = {"key": None, "msg": "key did not exist"}

    result = ec2_key.delete_key_pair(module.check_mode, ec2_client, name)

    assert m_find_key_pair.call_count == 1
    m_find_key_pair.assert_called_with(ec2_client, name)
    assert m_delete_key_pair.call_count == 0
    assert result == expected_result


@patch(module_name + ".AnsibleAWSModule")
def test_main_success(m_AnsibleAWSModule):
    m_module = MagicMock()
    m_AnsibleAWSModule.return_value = m_module

    ec2_key.main()

    m_module.client.assert_called_with("ec2", retry_decorator=ANY)
