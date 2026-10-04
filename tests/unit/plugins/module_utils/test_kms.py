# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.kms import AnsibleKMSError
from ansible_collections.amazon.aws.plugins.module_utils.kms import AnsibleKMSPermissionsError
from ansible_collections.amazon.aws.plugins.module_utils.kms import AnsibleKMSUnsupportedError
from ansible_collections.amazon.aws.plugins.module_utils.kms import get_key_details
from ansible_collections.amazon.aws.plugins.module_utils.kms import get_kms_aliases_lookup
from ansible_collections.amazon.aws.plugins.module_utils.kms import get_kms_policies
from ansible_collections.amazon.aws.plugins.module_utils.kms import get_kms_policy_as_dict
from ansible_collections.amazon.aws.plugins.module_utils.kms import get_kms_tags


class TestKmsCompatibility:
    """Test suite for kms.py re-exports."""

    def test_api_exports_exist(self):
        """Verify all API re-exports are present."""
        from ansible_collections.amazon.aws.plugins.module_utils import kms

        # API functions
        assert hasattr(kms, "cancel_key_deletion")
        assert hasattr(kms, "create_alias")
        assert hasattr(kms, "create_grant")
        assert hasattr(kms, "create_key")
        assert hasattr(kms, "disable_key")
        assert hasattr(kms, "disable_key_rotation")
        assert hasattr(kms, "enable_key")
        assert hasattr(kms, "enable_key_rotation")
        assert hasattr(kms, "get_key_policy")
        assert hasattr(kms, "get_key_rotation_status")
        assert hasattr(kms, "get_kms_aliases")
        assert hasattr(kms, "get_kms_grants")
        assert hasattr(kms, "get_kms_keys")
        assert hasattr(kms, "get_kms_metadata")
        assert hasattr(kms, "get_kms_tags")
        assert hasattr(kms, "list_key_policies")
        assert hasattr(kms, "list_resource_tags")
        assert hasattr(kms, "put_key_policy")
        assert hasattr(kms, "retire_grant")
        assert hasattr(kms, "schedule_key_deletion")
        assert hasattr(kms, "tag_resource")
        assert hasattr(kms, "untag_resource")
        assert hasattr(kms, "update_key_description")

    def test_exception_exports_exist(self):
        """Verify all exception re-exports are present."""
        from ansible_collections.amazon.aws.plugins.module_utils import kms

        assert hasattr(kms, "AnsibleKMSError")
        assert hasattr(kms, "AnsibleKMSPermissionsError")
        assert hasattr(kms, "AnsibleKMSUnsupportedError")
        assert hasattr(kms, "KMSErrorHandler")

    def test_transformation_exports_exist(self):
        """Verify all transformation re-exports are present."""
        from ansible_collections.amazon.aws.plugins.module_utils import kms

        assert hasattr(kms, "canonicalize_alias_name")
        assert hasattr(kms, "normalize_kms_key_details")

    def test_helper_functions_exist(self):
        """Verify helper functions are present."""
        from ansible_collections.amazon.aws.plugins.module_utils import kms

        assert hasattr(kms, "get_kms_aliases_lookup")
        assert hasattr(kms, "get_kms_policy_as_dict")
        assert hasattr(kms, "get_kms_policies")
        assert hasattr(kms, "get_key_details")


class TestGetKmsAliasesLookup:
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_aliases")
    def test_empty_aliases(self, mock_get_aliases):
        mock_get_aliases.return_value = {"Aliases": []}
        client = MagicMock()
        result = get_kms_aliases_lookup(client)
        assert result == {}

    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_aliases")
    def test_aliases_without_target(self, mock_get_aliases):
        # AWS-managed aliases like aws/s3 don't have TargetKeyId
        mock_get_aliases.return_value = {
            "Aliases": [
                {"AliasName": "alias/aws/s3", "AliasArn": "arn:aws:kms:us-east-1:123456789012:alias/aws/s3"},
            ]
        }
        client = MagicMock()
        result = get_kms_aliases_lookup(client)
        assert result == {}

    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_aliases")
    def test_single_alias_per_key(self, mock_get_aliases):
        mock_get_aliases.return_value = {
            "Aliases": [
                {
                    "AliasName": "alias/mykey",
                    "AliasArn": "arn:aws:kms:us-east-1:123456789012:alias/mykey",
                    "TargetKeyId": "key-123",
                },
            ]
        }
        client = MagicMock()
        result = get_kms_aliases_lookup(client)
        assert result == {"key-123": ["mykey"]}

    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_aliases")
    def test_multiple_aliases_per_key(self, mock_get_aliases):
        mock_get_aliases.return_value = {
            "Aliases": [
                {
                    "AliasName": "alias/mykey",
                    "AliasArn": "arn:aws:kms:us-east-1:123456789012:alias/mykey",
                    "TargetKeyId": "key-123",
                },
                {
                    "AliasName": "alias/mykey2",
                    "AliasArn": "arn:aws:kms:us-east-1:123456789012:alias/mykey2",
                    "TargetKeyId": "key-123",
                },
            ]
        }
        client = MagicMock()
        result = get_kms_aliases_lookup(client)
        assert result == {"key-123": ["mykey", "mykey2"]}

    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_aliases")
    def test_alias_prefix_stripping(self, mock_get_aliases):
        mock_get_aliases.return_value = {
            "Aliases": [
                {
                    "AliasName": "alias/test-key",
                    "AliasArn": "arn:aws:kms:us-east-1:123456789012:alias/test-key",
                    "TargetKeyId": "key-456",
                },
            ]
        }
        client = MagicMock()
        result = get_kms_aliases_lookup(client)
        # Verify 'alias/' prefix is stripped
        assert result == {"key-456": ["test-key"]}
        assert "alias/test-key" not in result.get("key-456", [])


class TestGetKmsTags:
    def test_no_tags(self):
        client = MagicMock()
        paginator = MagicMock()
        client.get_paginator.return_value = paginator
        paginator.paginate.return_value.build_full_result.return_value = {"Tags": []}
        result = get_kms_tags(client, "key-123")
        assert result == {"Tags": []}
        client.get_paginator.assert_called_once_with("list_resource_tags")
        paginator.paginate.assert_called_once_with(KeyId="key-123")

    def test_single_page_tags(self):
        client = MagicMock()
        paginator = MagicMock()
        client.get_paginator.return_value = paginator
        paginator.paginate.return_value.build_full_result.return_value = {
            "Tags": [{"TagKey": "Environment", "TagValue": "Production"}]
        }
        result = get_kms_tags(client, "key-123")
        assert result == {"Tags": [{"TagKey": "Environment", "TagValue": "Production"}]}

    def test_paginated_tags(self):
        # build_full_result handles pagination internally
        client = MagicMock()
        paginator = MagicMock()
        client.get_paginator.return_value = paginator
        paginator.paginate.return_value.build_full_result.return_value = {
            "Tags": [{"TagKey": "Tag1", "TagValue": "Value1"}, {"TagKey": "Tag2", "TagValue": "Value2"}]
        }
        result = get_kms_tags(client, "key-123")
        assert len(result["Tags"]) == 2
        assert {"TagKey": "Tag1", "TagValue": "Value1"} in result["Tags"]
        assert {"TagKey": "Tag2", "TagValue": "Value2"} in result["Tags"]

    @patch("ansible_collections.amazon.aws.plugins.module_utils._kms.api.AWSRetry.jittered_backoff")
    def test_permission_denied(self, mock_retry):
        # Permission errors should propagate, not be caught
        mock_retry.return_value = lambda f: f
        client = MagicMock()
        client.get_paginator.side_effect = AnsibleKMSPermissionsError(
            message="Permission denied", exception=Exception("AccessDenied")
        )
        with pytest.raises(AnsibleKMSPermissionsError):
            get_kms_tags(client, "key-123")


class TestGetKmsPolicyAsDict:
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_key_policy")
    def test_policy_found(self, mock_get_policy):
        mock_get_policy.return_value = {"Policy": '{"Version": "2012-10-17", "Statement": []}'}
        client = MagicMock()
        result = get_kms_policy_as_dict(client, "key-123", "default")
        assert result == {"Version": "2012-10-17", "Statement": []}
        mock_get_policy.assert_called_once_with(client, "key-123", "default")

    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_key_policy")
    def test_policy_not_found(self, mock_get_policy):
        mock_get_policy.return_value = None
        client = MagicMock()
        result = get_kms_policy_as_dict(client, "key-123", "default")
        assert result is None

    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_key_policy")
    def test_permission_denied(self, mock_get_policy):
        mock_get_policy.side_effect = AnsibleKMSPermissionsError(
            message="Permission denied", exception=Exception("AccessDenied")
        )
        client = MagicMock()
        with pytest.raises(AnsibleKMSPermissionsError):
            get_kms_policy_as_dict(client, "key-123")

    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_key_policy")
    def test_default_policy_name(self, mock_get_policy):
        mock_get_policy.return_value = {"Policy": '{"Version": "2012-10-17"}'}
        client = MagicMock()
        get_kms_policy_as_dict(client, "key-123")
        # Should use "default" as policy name when not specified
        mock_get_policy.assert_called_once_with(client, "key-123", "default")

    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_key_policy")
    def test_custom_policy_name(self, mock_get_policy):
        mock_get_policy.return_value = {"Policy": '{"Version": "2012-10-17"}'}
        client = MagicMock()
        get_kms_policy_as_dict(client, "key-123", "custom")
        mock_get_policy.assert_called_once_with(client, "key-123", "custom")


class TestGetKmsPolicies:
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_key_policy")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.list_key_policies")
    def test_no_policies(self, mock_list_policies, mock_get_policy):
        mock_list_policies.return_value = {"PolicyNames": []}
        client = MagicMock()
        result = get_kms_policies(client, "key-123")
        assert result == []
        mock_get_policy.assert_not_called()

    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_key_policy")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.list_key_policies")
    def test_single_policy(self, mock_list_policies, mock_get_policy):
        mock_list_policies.return_value = {"PolicyNames": ["default"]}
        mock_get_policy.return_value = {"Policy": '{"Version": "2012-10-17"}'}
        client = MagicMock()
        result = get_kms_policies(client, "key-123")
        assert result == ['{"Version": "2012-10-17"}']
        mock_get_policy.assert_called_once_with(client, "key-123", "default")

    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_key_policy")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.list_key_policies")
    def test_multiple_policies(self, mock_list_policies, mock_get_policy):
        mock_list_policies.return_value = {"PolicyNames": ["default", "custom"]}
        mock_get_policy.side_effect = [
            {"Policy": '{"Version": "2012-10-17", "Id": "default"}'},
            {"Policy": '{"Version": "2012-10-17", "Id": "custom"}'},
        ]
        client = MagicMock()
        result = get_kms_policies(client, "key-123")
        assert len(result) == 2
        assert '{"Version": "2012-10-17", "Id": "default"}' in result
        assert '{"Version": "2012-10-17", "Id": "custom"}' in result


class TestGetKeyDetails:
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_metadata")
    def test_key_not_found(self, mock_metadata):
        mock_metadata.return_value = None
        client = MagicMock()
        result = get_key_details(client, "key-123")
        assert result is None

    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms._transformations.normalize_kms_key_details")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_policies")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_tags")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_grants")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_key_rotation_status")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_aliases_lookup")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_metadata")
    def test_full_key_details(
        self,
        mock_metadata,
        mock_aliases,
        mock_rotation,
        mock_grants,
        mock_tags,
        mock_policies,
        mock_normalize,
    ):
        mock_metadata.return_value = {"Arn": "arn:aws:kms:us-east-1:123456789012:key/abc", "KeyId": "abc"}
        mock_aliases.return_value = {"abc": ["myalias"]}
        mock_rotation.return_value = {"KeyRotationEnabled": True}
        mock_grants.return_value = {"Grants": []}
        mock_tags.return_value = {"Tags": []}
        mock_policies.return_value = []
        mock_normalize.return_value = {"key_id": "abc"}

        client = MagicMock()
        result = get_key_details(client, "key-123")

        mock_metadata.assert_called_once_with(client, "key-123")
        mock_aliases.assert_called_once_with(client)
        mock_rotation.assert_called_once_with(client, "arn:aws:kms:us-east-1:123456789012:key/abc")
        mock_grants.assert_called_once_with(client, "arn:aws:kms:us-east-1:123456789012:key/abc", grant_tokens=None)
        mock_tags.assert_called_once_with(client, "arn:aws:kms:us-east-1:123456789012:key/abc")
        mock_policies.assert_called_once_with(client, "arn:aws:kms:us-east-1:123456789012:key/abc")
        mock_normalize.assert_called_once()
        assert result == {"key_id": "abc"}

    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms._transformations.normalize_kms_key_details")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_key_rotation_status")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_aliases_lookup")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_metadata")
    def test_pending_deletion_skips_grants_tags_policies(
        self, mock_metadata, mock_aliases, mock_rotation, mock_normalize
    ):
        mock_metadata.return_value = {"Arn": "arn:aws:kms:us-east-1:123456789012:key/abc", "KeyId": "abc"}
        mock_aliases.return_value = {"abc": ["myalias"]}
        mock_rotation.return_value = {"KeyRotationEnabled": False}
        mock_normalize.return_value = {"key_id": "abc"}

        client = MagicMock()
        result = get_key_details(client, "key-123", pending_deletion=True)

        mock_normalize.assert_called_once()
        assert result == {"key_id": "abc"}

    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms._transformations.normalize_kms_key_details")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_policies")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_tags")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_grants")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_key_rotation_status")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_aliases_lookup")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_metadata")
    def test_rotation_permission_error_suppressed(
        self,
        mock_metadata,
        mock_aliases,
        mock_rotation,
        mock_grants,
        mock_tags,
        mock_policies,
        mock_normalize,
    ):
        mock_metadata.return_value = {"Arn": "arn:aws:kms:us-east-1:123456789012:key/abc", "KeyId": "abc"}
        mock_aliases.return_value = {}
        mock_rotation.side_effect = AnsibleKMSPermissionsError(message="denied", exception=Exception())
        mock_grants.return_value = {"Grants": []}
        mock_tags.return_value = {"Tags": []}
        mock_policies.return_value = []
        mock_normalize.return_value = {"key_id": "abc"}

        client = MagicMock()
        result = get_key_details(client, "key-123")

        assert result == {"key_id": "abc"}
        # Verify enable_key_rotation was set to None in the data passed to normalize
        call_args = mock_normalize.call_args[0][0]
        assert call_args["enable_key_rotation"] is None

    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms._transformations.normalize_kms_key_details")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_policies")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_tags")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_grants")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_key_rotation_status")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_aliases_lookup")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_metadata")
    def test_rotation_unsupported_error_suppressed(
        self,
        mock_metadata,
        mock_aliases,
        mock_rotation,
        mock_grants,
        mock_tags,
        mock_policies,
        mock_normalize,
    ):
        mock_metadata.return_value = {"Arn": "arn:aws:kms:us-east-1:123456789012:key/abc", "KeyId": "abc"}
        mock_aliases.return_value = {}
        mock_rotation.side_effect = AnsibleKMSUnsupportedError(message="unsupported", exception=Exception())
        mock_grants.return_value = {"Grants": []}
        mock_tags.return_value = {"Tags": []}
        mock_policies.return_value = []
        mock_normalize.return_value = {"key_id": "abc"}

        client = MagicMock()
        result = get_key_details(client, "key-123")

        call_args = mock_normalize.call_args[0][0]
        assert call_args["enable_key_rotation"] is None

    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms._transformations.normalize_kms_key_details")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_policies")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_tags")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_grants")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_key_rotation_status")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_aliases_lookup")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_metadata")
    def test_grants_tags_policies_permission_errors_propagate(
        self,
        mock_metadata,
        mock_aliases,
        mock_rotation,
        mock_grants,
        mock_tags,
        mock_policies,
        mock_normalize,
    ):
        mock_metadata.return_value = {"Arn": "arn:aws:kms:us-east-1:123456789012:key/abc", "KeyId": "abc"}
        mock_aliases.return_value = {}
        mock_rotation.return_value = {"KeyRotationEnabled": True}
        mock_grants.return_value = {"Grants": []}
        mock_tags.side_effect = AnsibleKMSPermissionsError(message="denied", exception=Exception())

        client = MagicMock()
        with pytest.raises(AnsibleKMSPermissionsError):
            get_key_details(client, "key-123")

    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_aliases_lookup")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.kms.get_kms_metadata")
    def test_alias_lookup_error_reraised(self, mock_metadata, mock_aliases):
        mock_metadata.return_value = {"Arn": "arn:aws:kms:us-east-1:123456789012:key/abc", "KeyId": "abc"}
        mock_aliases.side_effect = AnsibleKMSError(message="error", exception=Exception("test"))

        client = MagicMock()
        with pytest.raises(AnsibleKMSError, match="Failed to obtain aliases"):
            get_key_details(client, "key-123")
