# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.s3 import AnsibleS3SupportError
from ansible_collections.amazon.aws.plugins.module_utils.s3 import ensure_s3_object_tags


class TestEnsureS3ObjectTags:
    @patch("ansible_collections.amazon.aws.plugins.module_utils.s3.get_s3_object_tagging")
    def test_none_tags_no_change(self, m_get_tags):
        """Test that None desired_tags returns current tags with no changes."""
        client = MagicMock()
        m_get_tags.return_value = {"Environment": "prod", "Owner": "team"}

        result_tags, changed = ensure_s3_object_tags(
            client, "test-bucket", "test-key", None, purge_tags=True, _max_attempts=1, _sleep_time=0
        )

        assert result_tags == {"Environment": "prod", "Owner": "team"}
        assert changed is False
        m_get_tags.assert_called_once_with(client, "test-bucket", "test-key")

    @patch("ansible_collections.amazon.aws.plugins.module_utils.s3.put_s3_object_tagging")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.s3.get_s3_object_tagging")
    def test_tags_already_match_no_change(self, m_get_tags, m_put_tags):
        """Test that matching tags result in no changes."""
        client = MagicMock()
        current_tags = {"Environment": "prod", "Owner": "team"}
        m_get_tags.return_value = current_tags

        result_tags, changed = ensure_s3_object_tags(
            client,
            "test-bucket",
            "test-key",
            {"Environment": "prod", "Owner": "team"},
            purge_tags=True,
            _max_attempts=1,
            _sleep_time=0,
        )

        assert result_tags == current_tags
        assert changed is False
        m_get_tags.assert_called_once_with(client, "test-bucket", "test-key")
        m_put_tags.assert_not_called()

    @patch("ansible_collections.amazon.aws.plugins.module_utils.s3.put_s3_object_tagging")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.s3.get_s3_object_tagging")
    def test_add_new_tags_success(self, m_get_tags, m_put_tags):
        """Test adding new tags to object."""
        client = MagicMock()
        m_get_tags.side_effect = [
            {"Environment": "prod"},
            {"Environment": "prod", "Application": "webapp"},
        ]

        result_tags, changed = ensure_s3_object_tags(
            client,
            "test-bucket",
            "test-key",
            {"Environment": "prod", "Application": "webapp"},
            purge_tags=False,
            _max_attempts=2,
            _sleep_time=0,
        )

        assert result_tags == {"Environment": "prod", "Application": "webapp"}
        assert changed is True
        m_put_tags.assert_called_once_with(
            client, "test-bucket", "test-key", {"Environment": "prod", "Application": "webapp"}
        )

    @patch("ansible_collections.amazon.aws.plugins.module_utils.s3.put_s3_object_tagging")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.s3.get_s3_object_tagging")
    def test_replace_tags_with_purge(self, m_get_tags, m_put_tags):
        """Test replacing tags with purge_tags=True."""
        client = MagicMock()
        m_get_tags.side_effect = [
            {"Environment": "prod", "Owner": "team", "OldTag": "value"},
            {"Environment": "dev", "Application": "webapp"},
        ]

        result_tags, changed = ensure_s3_object_tags(
            client,
            "test-bucket",
            "test-key",
            {"Environment": "dev", "Application": "webapp"},
            purge_tags=True,
            _max_attempts=2,
            _sleep_time=0,
        )

        assert result_tags == {"Environment": "dev", "Application": "webapp"}
        assert changed is True
        m_put_tags.assert_called_once_with(
            client, "test-bucket", "test-key", {"Environment": "dev", "Application": "webapp"}
        )

    @patch("ansible_collections.amazon.aws.plugins.module_utils.s3.delete_s3_object_tagging")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.s3.get_s3_object_tagging")
    def test_delete_all_tags(self, m_get_tags, m_delete_tags):
        """Test deleting all tags with empty dict."""
        client = MagicMock()
        m_get_tags.side_effect = [{"Environment": "prod", "Owner": "team"}, {}]

        result_tags, changed = ensure_s3_object_tags(
            client, "test-bucket", "test-key", {}, purge_tags=True, _max_attempts=2, _sleep_time=0
        )

        assert result_tags == {}
        assert changed is True
        m_delete_tags.assert_called_once_with(client, "test-bucket", "test-key")

    @patch("ansible_collections.amazon.aws.plugins.module_utils.s3.put_s3_object_tagging")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.s3.get_s3_object_tagging")
    def test_merge_tags_without_purge(self, m_get_tags, m_put_tags):
        """Test merging tags with purge_tags=False."""
        client = MagicMock()
        m_get_tags.side_effect = [
            {"Tag1": "value1", "Tag2": "value2"},
            {"Tag1": "value1", "Tag2": "updated", "Tag3": "value3"},
        ]

        result_tags, changed = ensure_s3_object_tags(
            client,
            "test-bucket",
            "test-key",
            {"Tag2": "updated", "Tag3": "value3"},
            purge_tags=False,
            _max_attempts=2,
            _sleep_time=0,
        )

        assert result_tags == {"Tag1": "value1", "Tag2": "updated", "Tag3": "value3"}
        assert changed is True
        m_put_tags.assert_called_once_with(
            client, "test-bucket", "test-key", {"Tag1": "value1", "Tag2": "updated", "Tag3": "value3"}
        )

    @patch("ansible_collections.amazon.aws.plugins.module_utils.s3.put_s3_object_tagging")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.s3.get_s3_object_tagging")
    def test_eventual_consistency_retry(self, m_get_tags, m_put_tags):
        """Test retry logic for eventual consistency."""
        client = MagicMock()
        # First call: current tags
        # Second call: tags not yet applied
        # Third call: tags applied successfully
        m_get_tags.side_effect = [
            {"Environment": "prod"},
            {"Environment": "prod"},
            {"Environment": "dev"},
        ]

        result_tags, changed = ensure_s3_object_tags(
            client,
            "test-bucket",
            "test-key",
            {"Environment": "dev"},
            purge_tags=True,
            _max_attempts=3,
            _sleep_time=0,
        )

        assert result_tags == {"Environment": "dev"}
        assert changed is True
        assert m_get_tags.call_count == 3
        m_put_tags.assert_called_once_with(client, "test-bucket", "test-key", {"Environment": "dev"})

    @patch("ansible_collections.amazon.aws.plugins.module_utils.s3.put_s3_object_tagging")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.s3.get_s3_object_tagging")
    def test_eventual_consistency_timeout(self, m_get_tags, m_put_tags):
        """Test that function returns after max attempts even if tags don't match."""
        client = MagicMock()
        # Tags never apply within max_attempts
        m_get_tags.side_effect = [
            {"Environment": "prod"},
            {"Environment": "prod"},
            {"Environment": "prod"},
        ]

        result_tags, changed = ensure_s3_object_tags(
            client,
            "test-bucket",
            "test-key",
            {"Environment": "dev"},
            purge_tags=True,
            _max_attempts=2,
            _sleep_time=0,
        )

        # Still returns changed=True even though tags didn't apply
        assert result_tags == {"Environment": "prod"}
        assert changed is True
        assert m_get_tags.call_count == 3  # Initial + 2 retries
        m_put_tags.assert_called_once()

    @patch("ansible_collections.amazon.aws.plugins.module_utils.s3.delete_s3_object_tagging")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.s3.get_s3_object_tagging")
    def test_empty_tags_without_purge_keeps_existing(self, m_get_tags, m_delete_tags):
        """Test that empty desired_tags with purge=False keeps existing tags."""
        client = MagicMock()
        m_get_tags.return_value = {"Environment": "prod", "Owner": "team"}

        result_tags, changed = ensure_s3_object_tags(
            client, "test-bucket", "test-key", {}, purge_tags=False, _max_attempts=1, _sleep_time=0
        )

        assert result_tags == {"Environment": "prod", "Owner": "team"}
        assert changed is False
        m_delete_tags.assert_not_called()

    @patch("ansible_collections.amazon.aws.plugins.module_utils.s3.put_s3_object_tagging")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.s3.get_s3_object_tagging")
    def test_numeric_tag_values_converted_to_text(self, m_get_tags, m_put_tags):
        """Test that numeric tag values are converted to text."""
        client = MagicMock()
        m_get_tags.side_effect = [{}, {"Count": "123", "Enabled": "True"}]

        result_tags, changed = ensure_s3_object_tags(
            client,
            "test-bucket",
            "test-key",
            {"Count": 123, "Enabled": True},
            purge_tags=True,
            _max_attempts=2,
            _sleep_time=0,
        )

        assert result_tags == {"Count": "123", "Enabled": "True"}
        assert changed is True
        # Verify the tags passed to put were converted
        m_put_tags.assert_called_once_with(client, "test-bucket", "test-key", {"Count": "123", "Enabled": "True"})

    @patch("ansible_collections.amazon.aws.plugins.module_utils.s3.get_s3_object_tagging")
    def test_support_error_with_none_tags_returns_empty(self, m_get_tags):
        """Test that AnsibleS3SupportError with None tags returns empty dict."""
        client = MagicMock()
        m_get_tags.side_effect = AnsibleS3SupportError(message="Tagging not supported")

        result_tags, changed = ensure_s3_object_tags(
            client, "test-bucket", "test-key", None, purge_tags=True, _max_attempts=1, _sleep_time=0
        )

        assert result_tags == {}
        assert changed is False
        m_get_tags.assert_called_once_with(client, "test-bucket", "test-key")

    @patch("ansible_collections.amazon.aws.plugins.module_utils.s3.get_s3_object_tagging")
    def test_support_error_with_tags_raises(self, m_get_tags):
        """Test that AnsibleS3SupportError with tags specified raises."""
        client = MagicMock()
        m_get_tags.side_effect = AnsibleS3SupportError(message="Tagging not supported")

        with pytest.raises(AnsibleS3SupportError, match="Tagging not supported"):
            ensure_s3_object_tags(
                client,
                "test-bucket",
                "test-key",
                {"Environment": "test"},
                purge_tags=True,
                _max_attempts=1,
                _sleep_time=0,
            )
