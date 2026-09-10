# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.amazon.aws.plugins.module_utils._kms.transformations import camel_to_snake_grant
from ansible_collections.amazon.aws.plugins.module_utils._kms.transformations import canonicalize_alias_name
from ansible_collections.amazon.aws.plugins.module_utils._kms.transformations import normalize_kms_key_details


class TestCanonicalizeAliasName:
    def test_none_input(self):
        assert canonicalize_alias_name(None) is None

    def test_already_prefixed(self):
        assert canonicalize_alias_name("alias/myalias") == "alias/myalias"

    def test_add_prefix(self):
        assert canonicalize_alias_name("myalias") == "alias/myalias"

    def test_empty_string(self):
        assert canonicalize_alias_name("") == "alias/"

    def test_with_slashes(self):
        assert canonicalize_alias_name("my/complex/alias") == "alias/my/complex/alias"


class TestCamelToSnakeGrant:
    def test_basic_grant(self):
        grant = {
            "GrantId": "abc123",
            "GranteePrincipal": "arn:aws:iam::123456789012:role/test",
            "Operations": ["Decrypt", "Encrypt"],
        }
        result = camel_to_snake_grant(grant)
        assert result["grant_id"] == "abc123"
        assert result["grantee_principal"] == "arn:aws:iam::123456789012:role/test"
        assert result["operations"] == ["Decrypt", "Encrypt"]

    def test_grant_with_encryption_context_equals(self):
        grant = {
            "GrantId": "abc123",
            "GranteePrincipal": "arn:aws:iam::123456789012:role/test",
            "Constraints": {"EncryptionContextEquals": {"Department": "Finance"}},
        }
        result = camel_to_snake_grant(grant)
        assert result["grant_id"] == "abc123"
        assert result["constraints"]["encryption_context_equals"] == {"Department": "Finance"}

    def test_grant_with_encryption_context_subset(self):
        grant = {
            "GrantId": "abc123",
            "GranteePrincipal": "arn:aws:iam::123456789012:role/test",
            "Constraints": {"EncryptionContextSubset": {"Project": "Alpha"}},
        }
        result = camel_to_snake_grant(grant)
        assert result["grant_id"] == "abc123"
        assert result["constraints"]["encryption_context_subset"] == {"Project": "Alpha"}

    def test_grant_with_both_encryption_contexts(self):
        grant = {
            "GrantId": "abc123",
            "GranteePrincipal": "arn:aws:iam::123456789012:role/test",
            "Constraints": {
                "EncryptionContextEquals": {"Department": "Finance"},
                "EncryptionContextSubset": {"Project": "Alpha"},
            },
        }
        result = camel_to_snake_grant(grant)
        assert result["constraints"]["encryption_context_equals"] == {"Department": "Finance"}
        assert result["constraints"]["encryption_context_subset"] == {"Project": "Alpha"}

    def test_grant_without_constraints(self):
        grant = {
            "GrantId": "abc123",
            "GranteePrincipal": "arn:aws:iam::123456789012:role/test",
        }
        result = camel_to_snake_grant(grant)
        assert result["grant_id"] == "abc123"
        assert result["grantee_principal"] == "arn:aws:iam::123456789012:role/test"
        # Should have empty constraints dict from camel_dict_to_snake_dict
        assert "constraints" not in result or result.get("constraints") == {}


class TestNormalizeKmsKeyDetails:
    def test_tags_transformation(self):
        """Verify KMS tags with TagKey/TagValue are transformed to Ansible format."""
        key_details = {
            "KeyId": "abc123",
            "Arn": "arn:aws:kms:us-east-1:123456789012:key/abc123",
            "Tags": [{"TagKey": "Hello", "TagValue": "World"}, {"TagKey": "Environment", "TagValue": "Test"}],
        }
        result = normalize_kms_key_details(key_details)
        assert result["tags"] == {"Hello": "World", "Environment": "Test"}
        assert result["key_id"] == "abc123"

    def test_empty_tags(self):
        """Verify empty tags list is handled correctly."""
        key_details = {
            "KeyId": "abc123",
            "Arn": "arn:aws:kms:us-east-1:123456789012:key/abc123",
            "Tags": [],
        }
        result = normalize_kms_key_details(key_details)
        assert result["tags"] == {}

    def test_no_tags(self):
        """Verify missing Tags key doesn't add tags field when force_tags=False."""
        key_details = {
            "KeyId": "abc123",
            "Arn": "arn:aws:kms:us-east-1:123456789012:key/abc123",
        }
        result = normalize_kms_key_details(key_details)
        assert "tags" not in result

    def test_grants_transformation(self):
        """Verify grants list is transformed correctly."""
        key_details = {
            "KeyId": "abc123",
            "Arn": "arn:aws:kms:us-east-1:123456789012:key/abc123",
            "Grants": [
                {
                    "GrantId": "grant123",
                    "GranteePrincipal": "arn:aws:iam::123456789012:role/test",
                    "Operations": ["Decrypt"],
                }
            ],
        }
        result = normalize_kms_key_details(key_details)
        assert len(result["grants"]) == 1
        assert result["grants"][0]["grant_id"] == "grant123"
        assert result["grants"][0]["grantee_principal"] == "arn:aws:iam::123456789012:role/test"

    def test_grants_with_constraints(self):
        """Verify grants with constraints preserve encryption context."""
        key_details = {
            "KeyId": "abc123",
            "Arn": "arn:aws:kms:us-east-1:123456789012:key/abc123",
            "Grants": [
                {
                    "GrantId": "grant123",
                    "GranteePrincipal": "arn:aws:iam::123456789012:role/test",
                    "Constraints": {"EncryptionContextEquals": {"Department": "Finance"}},
                }
            ],
        }
        result = normalize_kms_key_details(key_details)
        assert result["grants"][0]["constraints"]["encryption_context_equals"] == {"Department": "Finance"}

    def test_key_policies_transformation(self):
        """Verify policy JSON strings are parsed to dicts."""
        key_details = {
            "KeyId": "abc123",
            "Arn": "arn:aws:kms:us-east-1:123456789012:key/abc123",
            "KeyPolicies": ['{"Version": "2012-10-17", "Statement": []}', '{"Version": "2012-10-17", "Id": "custom"}'],
        }
        result = normalize_kms_key_details(key_details)
        assert len(result["key_policies"]) == 2
        assert result["key_policies"][0] == {"Version": "2012-10-17", "Statement": []}
        assert result["key_policies"][1] == {"Version": "2012-10-17", "Id": "custom"}

    def test_complete_key_details(self):
        """Verify complete key with all fields transforms correctly."""
        key_details = {
            "KeyId": "abc123",
            "Arn": "arn:aws:kms:us-east-1:123456789012:key/abc123",
            "Description": "Test key",
            "Tags": [{"TagKey": "Environment", "TagValue": "Test"}],
            "Grants": [{"GrantId": "grant123", "GranteePrincipal": "arn:aws:iam::123456789012:role/test"}],
            "KeyPolicies": ['{"Version": "2012-10-17"}'],
        }
        result = normalize_kms_key_details(key_details)
        assert result["key_id"] == "abc123"
        assert result["arn"] == "arn:aws:kms:us-east-1:123456789012:key/abc123"
        assert result["description"] == "Test key"
        assert result["tags"] == {"Environment": "Test"}
        assert len(result["grants"]) == 1
        assert len(result["key_policies"]) == 1
