# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import call

import pytest
import botocore
import datetime
from dateutil.tz import tzutc
from ansible.module_utils._text import to_bytes

from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code

from ansible_collections.amazon.aws.plugins.modules import ec2_key

module_name = "ansible_collections.amazon.aws.plugins.modules.ec2_key"


def raise_botocore_exception_clienterror(action):

    params = {
            'Error': {
                'Code': 1,
                'Message': 'error creating key'
            },
            'ResponseMetadata': {
                'RequestId': '01234567-89ab-cdef-0123-456789abcdef'
            }
        }

    if action == 'create_key_pair':
        params['Error']['Message'] = 'error creating key'

    elif action == 'describe_key_pair':
        params['Error']['Code'] = 'InvalidKeyPair.NotFound'
        params['Error']['Message'] = 'The key pair does not exist'

    elif action == 'import_key_pair':
        params['Error']['Message'] = 'error importing key'

    return botocore.exceptions.ClientError(params, action)


def test__import_key_pair():
    ec2_client = MagicMock()
    name = 'my_keypair'
    key_material = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQD3F6tyPEFEzV0LX3X8BsXdMsQz1x2cEikKDEY0aIj41qgxMCP/iteneqXSIFZBp5vizPvaoIR3Um9xK7PGoW8giupGn+EPuxIA4cDM4vzOqOkiMPhz5XK0whEjkVzTo4+S0puvDZuwIsdiW9mxhJc7tgBNL0cYlWSYVkz4G/fslNfRPW5mYAM49f4fhtxPb5ok4Q2Lg9dPKVHO/Bgeu5woMc7RY0p1ej6D4CKFE6lymSDJpW0YHX/wqE9+cfEauh7xZcG0q9t2ta6F6fmX0agvpFyZo8aFbXeUBr7osSCJNgvavWbM/06niWrOvYX2xwWdhXmXSrbX8ZbabVohBK41 email@example.com"

    expected_params = {
        'KeyName': name,
        'PublicKeyMaterial': to_bytes(key_material),
    }

    ec2_client.import_key_pair.return_value = {
        'KeyFingerprint': 'd7:ff:a6:63:18:64:9c:57:a1:ee:ca:a4:ad:c2:81:62',
        'KeyName': 'my_keypair',
        'KeyPairId': 'key-012345678905a208d'
    }

    result = ec2_key._import_key_pair(ec2_client, name, key_material)

    assert result == ec2_client.import_key_pair.return_value
    assert ec2_client.import_key_pair.call_count == 1
    assert ec2_client.import_key_pair.called_with(aws_retry=True, **expected_params)


def test_api_failure__import_key_pair():
    ec2_client = MagicMock()
    name = 'my_keypair'
    key_material = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQD3F6tyPEFEzV0LX3X8BsXdMsQz1x2cEikKDEY0aIj41qgxMCP/iteneqXSIFZBp5vizPvaoIR3Um9xK7PGoW8giupGn+EPuxIA4cDM4vzOqOkiMPhz5XK0whEjkVzTo4+S0puvDZuwIsdiW9mxhJc7tgBNL0cYlWSYVkz4G/fslNfRPW5mYAM49f4fhtxPb5ok4Q2Lg9dPKVHO/Bgeu5woMc7RY0p1ej6D4CKFE6lymSDJpW0YHX/wqE9+cfEauh7xZcG0q9t2ta6F6fmX0agvpFyZo8aFbXeUBr7osSCJNgvavWbM/06niWrOvYX2xwWdhXmXSrbX8ZbabVohBK41 email@example.com"

    expected_params = {
        'KeyName': name,
        'PublicKeyMaterial': to_bytes(key_material),
    }

    ec2_client.import_key_pair.side_effect = raise_botocore_exception_clienterror('import_key_pair')

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
        "type": "rsa"
    }

    result = ec2_key.extract_key_data(key, key_type)

    assert result == expected_result


def test_extract_key_data_create_key_pair():

    key = {
    'KeyFingerprint': '11:12:13:14:bb:26:85:b2:e8:39:27:bc:ee:aa:ff:ee:dd:cc:bb:aa',
    'KeyName': 'my_keypair',
    'KeyPairId': 'key-043046ef2a9a80b56'
    }

    key_type = "rsa"

    expected_result = {
        "name": "my_keypair",
        "fingerprint": "11:12:13:14:bb:26:85:b2:e8:39:27:bc:ee:aa:ff:ee:dd:cc:bb:aa",
        "id": "key-043046ef2a9a80b56",
        "tags": {},
        "type": "rsa"
    }

    result = ec2_key.extract_key_data(key, key_type)

    assert result == expected_result


@patch(module_name + '.delete_key_pair')
@patch(module_name + '._import_key_pair')
@patch(module_name + '.find_key_pair')
def test_get_key_fingerprint(m_find_key_pair, m_import_key_pair, m_delete_key_pair):

    module = MagicMock()
    ec2_client = MagicMock()

    m_find_key_pair.return_value = None

    m_import_key_pair.return_value = {
        'KeyFingerprint': 'd7:ff:a6:63:18:64:9c:57:a1:ee:ca:a4:ad:c2:81:62',
        'KeyName': 'my_keypair',
        'KeyPairId': 'key-043046ef2a9a80b56'
    }

    m_delete_key_pair.return_value = {
        'changed': True,
        'key': None,
        'msg': 'key deleted'
    }

    expected_result = 'd7:ff:a6:63:18:64:9c:57:a1:ee:ca:a4:ad:c2:81:62'

    key_material = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQD3F6tyPEFEzV0LX3X8BsXdMsQz1x2cEikKDEY0aIj41qgxMCP/iteneqXSIFZBp5vizPvaoIR3Um9xK7PGoW8giupGn+EPuxIA4cDM4vzOqOkiMPhz5XK0whEjkVzTo4+S0puvDZuwIsdiW9mxhJc7tgBNL0cYlWSYVkz4G/fslNfRPW5mYAM49f4fhtxPb5ok4Q2Lg9dPKVHO/Bgeu5woMc7RY0p1ej6D4CKFE6lymSDJpW0YHX/wqE9+cfEauh7xZcG0q9t2ta6F6fmX0agvpFyZo8aFbXeUBr7osSCJNgvavWbM/06niWrOvYX2xwWdhXmXSrbX8ZbabVohBK41 email@example.com"

    result = ec2_key.get_key_fingerprint(module, ec2_client, key_material)

    assert result == expected_result
    assert m_find_key_pair.call_count == 1
    assert m_import_key_pair.call_count == 1
    assert m_delete_key_pair.call_count == 1


def test_find_key_pair():
    ec2_client = MagicMock()
    name = 'my_keypair'

    ec2_client.describe_key_pairs.return_value = {
        'KeyPairs': [
            {
                'CreateTime': datetime.datetime(2022, 9, 15, 20, 10, 15, tzinfo=tzutc()),
                'KeyFingerprint': '11:12:13:14:bb:26:85:b2:e8:39:27:bc:ee:aa:ff:ee:dd:cc:bb:aa',
                'KeyName': 'my_keypair',
                'KeyPairId': 'key-043046ef2a9a80b56',
                'KeyType': 'rsa',
                'Tags': []
            }
        ],
    }

    ec2_key.find_key_pair(ec2_client, name)

    assert ec2_client.describe_key_pairs.call_count == 1
    ec2_client.describe_key_pairs.assert_called_with(aws_retry=True, KeyNames=[name])


def test_api_failure_find_key_pair():
    ec2_client = MagicMock()
    name = 'non_existing_keypair'

    ec2_client.describe_key_pairs.side_effect = botocore.exceptions.BotoCoreError

    with pytest.raises(ec2_key.Ec2KeyFailure):
        ec2_key.find_key_pair(ec2_client, name)


def test_invalid_key_pair_find_key_pair():
    ec2_client = MagicMock()
    name = 'non_existing_keypair'

    ec2_client.describe_key_pairs.side_effect = raise_botocore_exception_clienterror('describe_key_pair')

    result = ec2_key.find_key_pair(ec2_client, name)

    assert result == None


def test__create_key_pair():
    ec2_client = MagicMock()
    name = 'my_keypair'
    tag_spec = None
    key_type = None

    expected_params = { 'KeyName': name }

    ec2_client.create_key_pair.return_value = {
        'KeyFingerprint': 'd7:ff:a6:63:18:64:9c:57:a1:ee:ca:a4:ad:c2:81:62',
        'KeyMaterial': '-----BEGIN RSA PRIVATE KEY-----\nMIIEXm7/Bi9wba2m0Qtclu\nCXQw2paSIZb\n-----END RSA PRIVATE KEY-----',
        'KeyName': 'my_keypair',
        'KeyPairId': 'key-012345678905a208d'
    }

    result = ec2_key._create_key_pair(ec2_client, name, tag_spec, key_type)

    assert result == ec2_client.create_key_pair.return_value
    assert ec2_client.create_key_pair.call_count == 1
    assert ec2_client.create_key_pair.called_with(aws_retry=True, **expected_params)


def test_api_failure__create_key_pair():
    ec2_client = MagicMock()
    name = 'my_keypair'
    tag_spec = None
    key_type = None

    ec2_client.create_key_pair.side_effect = raise_botocore_exception_clienterror('create_key_pair')

    with pytest.raises(ec2_key.Ec2KeyFailure):
        ec2_key._create_key_pair(ec2_client, name, tag_spec, key_type)
