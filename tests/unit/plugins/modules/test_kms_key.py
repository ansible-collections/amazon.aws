#
# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

from ansible_collections.amazon.aws.plugins.modules import kms_key


module_name = "ansible_collections.amazon.aws.plugins.modules.kms_key"
key_details = {
    "KeyMetadata": {
        "aliases": ["mykey"],
        "Arn": "arn:aws:kms:us-east-1:12345678:key/mrk-12345678",
        "customer_master_key_spec": "SYMMETRIC_DEFAULT",
        "description": "",
        "enable_key_rotation": False,
        "enabled": True,
        "encryption_algorithms": ["SYMMETRIC_DEFAULT"],
        "grants": [],
        "key_arn": "arn:aws:kms:us-east-1:12345678:key/mrk-12345678",
        "key_id": "mrk-12345678",
        "key_manager": "CUSTOMER",
        "key_policies": [
            {
                "Id": "key-default-1",
                "Statement": [
                    {
                        "Action": "kms:*",
                        "Effect": "Allow",
                        "Principal": {"AWS": "arn:aws:iam::12345678:root"},
                        "Resource": "*",
                        "Sid": "Enable IAM User Permissions",
                    }
                ],
                "Version": "2012-10-17",
            }
        ],
        "key_spec": "SYMMETRIC_DEFAULT",
        "key_state": "Enabled",
        "key_usage": "ENCRYPT_DECRYPT",
        "multi_region": True,
        "multi_region_configuration": {
            "multi_region_key_type": "PRIM   ARY",
            "primary_key": {
                "arn": "arn:aws:kms:us-east-1:12345678:key/mrk-12345678",
                "region": "us-east-1",
            },
            "replica_keys": [],
        },
        "origin": "AWS_KMS",
        "tags": {"Hello": "World2"},
    }
}


@patch(module_name + ".get_kms_metadata_with_backoff")
def test_fetch_key_metadata(m_get_kms_metadata_with_backoff):
    module = MagicMock()
    kms_client = MagicMock()

    m_get_kms_metadata_with_backoff.return_value = key_details
    kms_key.fetch_key_metadata(kms_client, module, "mrk-12345678", "mykey")
    assert m_get_kms_metadata_with_backoff.call_count == 1


def test_validate_params():
    module = MagicMock()
    module.params = {"state": "present", "multi_region": True}

    result = kms_key.validate_params(module, key_details["KeyMetadata"])
    module.fail_json.assert_called_with(msg="You cannot change the multi-region property on an existing key.")
