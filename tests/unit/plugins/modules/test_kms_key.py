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


@patch(module_name + ".get_kms_metadata")
def test_fetch_key_metadata(m_get_kms_metadata):
    module = MagicMock()
    kms_client = MagicMock()

    m_get_kms_metadata.return_value = key_details["KeyMetadata"]
    kms_key.fetch_key_metadata(kms_client, module, "mrk-12345678", "mykey")
    assert m_get_kms_metadata.call_count == 1


def test_validate_params():
    module = MagicMock()
    module.params = {"state": "present", "multi_region": True}

    kms_key.validate_params(module, key_details["KeyMetadata"])
    module.fail_json.assert_called_with(msg="You cannot change the multi-region property on an existing key.")


class TestConvertGrantParams:
    def test_basic_grant(self):
        grant = {"grantee_principal": "arn:aws:iam::123456789012:role/test"}
        key = {"key_arn": "arn:aws:kms:us-east-1:123456789012:key/abc123"}
        result = kms_key.convert_grant_params(grant, key)
        assert result["KeyId"] == "arn:aws:kms:us-east-1:123456789012:key/abc123"
        assert result["GranteePrincipal"] == "arn:aws:iam::123456789012:role/test"
        assert "Operations" not in result
        assert "Name" not in result

    def test_grant_with_operations(self):
        grant = {"grantee_principal": "arn:aws:iam::123456789012:role/test", "operations": ["Decrypt", "Encrypt"]}
        key = {"key_arn": "arn:aws:kms:us-east-1:123456789012:key/abc123"}
        result = kms_key.convert_grant_params(grant, key)
        assert result["Operations"] == ["Decrypt", "Encrypt"]

    def test_grant_with_name(self):
        grant = {"grantee_principal": "arn:aws:iam::123456789012:role/test", "name": "MyGrant"}
        key = {"key_arn": "arn:aws:kms:us-east-1:123456789012:key/abc123"}
        result = kms_key.convert_grant_params(grant, key)
        assert result["Name"] == "MyGrant"

    def test_grant_with_retiring_principal(self):
        grant = {
            "grantee_principal": "arn:aws:iam::123456789012:role/test",
            "retiring_principal": "arn:aws:iam::123456789012:role/retire",
        }
        key = {"key_arn": "arn:aws:kms:us-east-1:123456789012:key/abc123"}
        result = kms_key.convert_grant_params(grant, key)
        assert result["RetiringPrincipal"] == "arn:aws:iam::123456789012:role/retire"

    def test_grant_with_encryption_context_subset(self):
        grant = {
            "grantee_principal": "arn:aws:iam::123456789012:role/test",
            "constraints": {"encryption_context_subset": {"Department": "Finance"}},
        }
        key = {"key_arn": "arn:aws:kms:us-east-1:123456789012:key/abc123"}
        result = kms_key.convert_grant_params(grant, key)
        assert result["Constraints"]["EncryptionContextSubset"] == {"Department": "Finance"}

    def test_grant_with_encryption_context_equals(self):
        grant = {
            "grantee_principal": "arn:aws:iam::123456789012:role/test",
            "constraints": {"encryption_context_equals": {"Project": "Alpha"}},
        }
        key = {"key_arn": "arn:aws:kms:us-east-1:123456789012:key/abc123"}
        result = kms_key.convert_grant_params(grant, key)
        assert result["Constraints"]["EncryptionContextEquals"] == {"Project": "Alpha"}

    def test_grant_with_both_constraints(self):
        grant = {
            "grantee_principal": "arn:aws:iam::123456789012:role/test",
            "constraints": {
                "encryption_context_subset": {"Department": "Finance"},
                "encryption_context_equals": {"Project": "Alpha"},
            },
        }
        key = {"key_arn": "arn:aws:kms:us-east-1:123456789012:key/abc123"}
        result = kms_key.convert_grant_params(grant, key)
        assert result["Constraints"]["EncryptionContextSubset"] == {"Department": "Finance"}
        assert result["Constraints"]["EncryptionContextEquals"] == {"Project": "Alpha"}

    def test_complete_grant(self):
        grant = {
            "grantee_principal": "arn:aws:iam::123456789012:role/test",
            "retiring_principal": "arn:aws:iam::123456789012:role/retire",
            "operations": ["Decrypt", "Encrypt", "GenerateDataKey"],
            "name": "CompleteGrant",
            "constraints": {"encryption_context_equals": {"Environment": "Production"}},
        }
        key = {"key_arn": "arn:aws:kms:us-east-1:123456789012:key/abc123"}
        result = kms_key.convert_grant_params(grant, key)
        assert result["KeyId"] == "arn:aws:kms:us-east-1:123456789012:key/abc123"
        assert result["GranteePrincipal"] == "arn:aws:iam::123456789012:role/test"
        assert result["RetiringPrincipal"] == "arn:aws:iam::123456789012:role/retire"
        assert result["Operations"] == ["Decrypt", "Encrypt", "GenerateDataKey"]
        assert result["Name"] == "CompleteGrant"
        assert result["Constraints"]["EncryptionContextEquals"] == {"Environment": "Production"}
