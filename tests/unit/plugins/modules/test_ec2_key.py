# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import call

import pytest
import botocore
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
import datetime
from dateutil.tz import tzutc

from ansible_collections.amazon.aws.plugins.modules import ec2_key

module_name = "ansible_collections.amazon.aws.plugins.modules.ec2_key"


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


def test_extract_key_data():

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

