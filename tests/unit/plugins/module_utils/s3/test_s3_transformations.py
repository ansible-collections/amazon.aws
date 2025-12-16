# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.amazon.aws.plugins.module_utils._s3.transformations import merge_tags
from ansible_collections.amazon.aws.plugins.module_utils._s3.transformations import normalize_s3_bucket_acls
from ansible_collections.amazon.aws.plugins.module_utils._s3.transformations import normalize_s3_bucket_public_access
from ansible_collections.amazon.aws.plugins.module_utils._s3.transformations import normalize_s3_bucket_versioning


class TestMergeTags:
    def test_none_tags_returns_current(self):
        """Test that None desired_tags returns current tags unchanged."""
        current_tags = {"Environment": "prod", "Owner": "team"}
        result = merge_tags(current_tags, None, purge_tags=True)
        assert result == current_tags

    def test_none_tags_with_purge_false(self):
        """Test that None desired_tags with purge_tags=False returns current tags."""
        current_tags = {"Environment": "prod", "Owner": "team"}
        result = merge_tags(current_tags, None, purge_tags=False)
        assert result == current_tags

    def test_empty_current_tags_adds_new_tags(self):
        """Test adding tags when current is empty."""
        current_tags = {}
        new_tags = {"Environment": "dev", "Application": "webapp"}
        result = merge_tags(current_tags, new_tags, purge_tags=True)
        assert result == {"Environment": "dev", "Application": "webapp"}

    def test_purge_tags_true_replaces_all(self):
        """Test that purge_tags=True replaces all current tags."""
        current_tags = {"Environment": "prod", "Owner": "team", "OldTag": "value"}
        new_tags = {"Environment": "dev", "Application": "webapp"}
        result = merge_tags(current_tags, new_tags, purge_tags=True)
        assert result == {"Environment": "dev", "Application": "webapp"}
        assert "Owner" not in result
        assert "OldTag" not in result

    def test_purge_tags_false_merges_tags(self):
        """Test that purge_tags=False merges new tags with existing."""
        current_tags = {"Environment": "prod", "Owner": "team"}
        new_tags = {"Environment": "dev", "Application": "webapp"}
        result = merge_tags(current_tags, new_tags, purge_tags=False)
        assert result == {"Environment": "dev", "Owner": "team", "Application": "webapp"}

    def test_purge_tags_false_keeps_unmodified_tags(self):
        """Test that purge_tags=False preserves tags not in new_tags."""
        current_tags = {"Tag1": "value1", "Tag2": "value2", "Tag3": "value3"}
        new_tags = {"Tag2": "updated"}
        result = merge_tags(current_tags, new_tags, purge_tags=False)
        assert result == {"Tag1": "value1", "Tag2": "updated", "Tag3": "value3"}

    def test_empty_new_tags_with_purge_true(self):
        """Test that empty new_tags with purge=True removes all tags."""
        current_tags = {"Environment": "prod", "Owner": "team"}
        new_tags = {}
        result = merge_tags(current_tags, new_tags, purge_tags=True)
        assert result == {}

    def test_empty_new_tags_with_purge_false(self):
        """Test that empty new_tags with purge=False keeps current tags."""
        current_tags = {"Environment": "prod", "Owner": "team"}
        new_tags = {}
        result = merge_tags(current_tags, new_tags, purge_tags=False)
        assert result == {"Environment": "prod", "Owner": "team"}

    def test_tag_values_converted_to_text(self):
        """Test that tag values are converted to text."""
        current_tags = {}
        new_tags = {"Count": 123, "Enabled": True, "Name": "test"}
        result = merge_tags(current_tags, new_tags, purge_tags=True)
        # All values should be strings
        assert result == {"Count": "123", "Enabled": "True", "Name": "test"}
        assert all(isinstance(v, str) for v in result.values())

    def test_tag_keys_converted_to_text(self):
        """Test that tag keys are converted to text."""
        current_tags = {}
        new_tags = {123: "numeric", "string": "value"}
        result = merge_tags(current_tags, new_tags, purge_tags=True)
        # All keys should be strings
        assert "123" in result
        assert "string" in result
        assert all(isinstance(k, str) for k in result.keys())

    def test_does_not_modify_original_dicts(self):
        """Test that original dicts are not modified (deep copy behavior)."""
        current_tags = {"Environment": "prod", "Owner": "team"}
        new_tags = {"Environment": "dev"}
        original_current = current_tags.copy()
        original_new = new_tags.copy()

        result = merge_tags(current_tags, new_tags, purge_tags=False)

        # Original dicts should be unchanged
        assert current_tags == original_current
        assert new_tags == original_new
        # Result should have merged values
        assert result == {"Environment": "dev", "Owner": "team"}

    def test_nested_values_are_deep_copied(self):
        """Test that nested structures are deep copied with purge=False."""
        current_tags = {"Config": "value1"}
        new_tags = {"NewTag": "value2"}

        result = merge_tags(current_tags, new_tags, purge_tags=False)

        # Modifying result should not affect current_tags
        result["Config"] = "modified"
        assert current_tags["Config"] == "value1"

    def test_special_characters_in_tags(self):
        """Test tags with special characters."""
        current_tags = {}
        new_tags = {"aws:tag": "value", "custom:tag": "value2", "tag-with-dash": "value3"}
        result = merge_tags(current_tags, new_tags, purge_tags=True)
        assert result == {"aws:tag": "value", "custom:tag": "value2", "tag-with-dash": "value3"}


class TestNormalizeS3BucketVersioning:
    def test_none_input_returns_none(self):
        """Test that None input returns None."""
        result = normalize_s3_bucket_versioning(None)
        assert result is None

    def test_empty_dict_returns_empty_dict(self):
        """Test that empty dict returns empty dict (early return)."""
        result = normalize_s3_bucket_versioning({})
        assert result == {}

    def test_dict_with_other_keys_adds_defaults(self):
        """Test that dict with other keys gets default Status and MFADelete."""
        versioning_status = {"SomeOtherKey": "value"}
        result = normalize_s3_bucket_versioning(versioning_status)

        assert result["Status"] == "Disabled"
        assert result["Versioning"] == "Disabled"
        assert result["MFADelete"] == "Disabled"
        assert result["MfaDelete"] == "Disabled"

    def test_versioning_enabled(self):
        """Test versioning status Enabled."""
        versioning_status = {"Status": "Enabled", "MFADelete": "Disabled"}
        result = normalize_s3_bucket_versioning(versioning_status)

        assert result["Status"] == "Enabled"
        assert result["Versioning"] == "Enabled"
        assert result["MFADelete"] == "Disabled"
        assert result["MfaDelete"] == "Disabled"

    def test_versioning_suspended(self):
        """Test versioning status Suspended."""
        versioning_status = {"Status": "Suspended"}
        result = normalize_s3_bucket_versioning(versioning_status)

        assert result["Status"] == "Suspended"
        assert result["Versioning"] == "Suspended"
        assert result["MFADelete"] == "Disabled"
        assert result["MfaDelete"] == "Disabled"

    def test_mfa_delete_enabled(self):
        """Test MFA delete enabled."""
        versioning_status = {"Status": "Enabled", "MFADelete": "Enabled"}
        result = normalize_s3_bucket_versioning(versioning_status)

        assert result["MFADelete"] == "Enabled"
        assert result["MfaDelete"] == "Enabled"

    def test_missing_mfa_delete_defaults_to_disabled(self):
        """Test that missing MFADelete defaults to Disabled."""
        versioning_status = {"Status": "Enabled"}
        result = normalize_s3_bucket_versioning(versioning_status)

        assert result["MFADelete"] == "Disabled"
        assert result["MfaDelete"] == "Disabled"


class TestNormalizeS3BucketPublicAccess:
    def test_none_input_returns_none(self):
        """Test that None input returns None."""
        result = normalize_s3_bucket_public_access(None)
        assert result is None

    def test_empty_dict_returns_empty_dict(self):
        """Test that empty dict returns empty dict."""
        result = normalize_s3_bucket_public_access({})
        assert result == {}

    def test_normalizes_public_access_config(self):
        """Test that public access configuration is normalized."""
        public_access_status = {
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": False,
            "RestrictPublicBuckets": False,
        }
        result = normalize_s3_bucket_public_access(public_access_status)

        # Should have all original keys
        assert result["BlockPublicAcls"] is True
        assert result["IgnorePublicAcls"] is True
        assert result["BlockPublicPolicy"] is False
        assert result["RestrictPublicBuckets"] is False

        # Should also have PublicAccessBlockConfiguration
        assert "PublicAccessBlockConfiguration" in result
        assert result["PublicAccessBlockConfiguration"] == public_access_status

    def test_deep_copy_does_not_modify_original(self):
        """Test that normalization deep copies and doesn't modify original."""
        public_access_status = {"BlockPublicAcls": True}
        result = normalize_s3_bucket_public_access(public_access_status)

        # Modifying result should not affect original
        result["PublicAccessBlockConfiguration"]["BlockPublicAcls"] = False
        assert public_access_status["BlockPublicAcls"] is True


class TestNormalizeS3BucketAcls:
    def test_none_input_returns_none(self):
        """Test that None input returns None."""
        result = normalize_s3_bucket_acls(None)
        assert result is None

    def test_empty_dict_returns_empty_dict(self):
        """Test that empty dict returns empty dict."""
        result = normalize_s3_bucket_acls({})
        assert result == {}

    def test_extracts_grants_from_acls(self):
        """Test that grants are extracted from ACL dict."""
        acls = {
            "grants": [
                {"grantee": {"type": "CanonicalUser", "id": "abc123"}, "permission": "FULL_CONTROL"},
                {
                    "grantee": {"type": "Group", "uri": "http://acs.amazonaws.com/groups/global/AllUsers"},
                    "permission": "READ",
                },
            ]
        }
        result = normalize_s3_bucket_acls(acls)

        # Result should be the grants array
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["permission"] == "FULL_CONTROL"
        assert result[1]["permission"] == "READ"

    def test_empty_grants_returns_empty_list(self):
        """Test that empty grants returns empty list."""
        acls = {"grants": []}
        result = normalize_s3_bucket_acls(acls)

        assert result == []
