# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import patch

from ansible_collections.amazon.aws.plugins.module_utils.botocore import _get_user_agent_string


class TestGetUserAgentString:
    """Test suite for _get_user_agent_string() function."""

    def setup_method(self):
        """Import and reset common module before each test."""
        # Import here to ensure fresh state
        from ansible_collections.amazon.aws.plugins.module_utils import common

        # Reset to defaults
        common.set_collection_info(
            collection_name=common.AMAZON_AWS_COLLECTION_NAME,
            collection_version=common.AMAZON_AWS_COLLECTION_VERSION,
        )

    def teardown_method(self):
        """Reset collection info to defaults after each test."""
        from ansible_collections.amazon.aws.plugins.module_utils import common

        common.set_collection_info(
            collection_name=common.AMAZON_AWS_COLLECTION_NAME,
            collection_version=common.AMAZON_AWS_COLLECTION_VERSION,
        )

    @patch("ansible_collections.amazon.aws.plugins.module_utils.botocore.__version__", "2.15.0")
    def test_user_agent_with_ansible_version(self):
        """Test user agent string includes Ansible version."""
        user_agent = _get_user_agent_string()

        assert "APN/1.0 Ansible/2.15.0" in user_agent

    def test_user_agent_with_community_aws(self):
        """Test user agent string when called from community.aws collection."""
        from ansible_collections.amazon.aws.plugins.module_utils import common

        # Simulate community.aws setting its collection info
        common.set_collection_info(collection_name="community.aws", collection_version="12.0.0-dev0")

        user_agent = _get_user_agent_string()

        assert "APN/1.0 Ansible/" in user_agent
        assert "community.aws/12.0.0-dev0" in user_agent
        assert "amazon.aws" not in user_agent

    def test_user_agent_with_custom_collection(self):
        """Test user agent string with custom collection."""
        from ansible_collections.amazon.aws.plugins.module_utils import common

        common.set_collection_info(collection_name="my.custom", collection_version="1.2.3")

        user_agent = _get_user_agent_string()

        assert "APN/1.0 Ansible/" in user_agent
        assert "my.custom/1.2.3" in user_agent

    def test_user_agent_with_name_only(self):
        """Test user agent string when collection has name but no version.

        Note: Due to how set_collection_info works (only updates if truthy),
        we need to directly manipulate the module state for this test.
        """
        from ansible_collections.amazon.aws.plugins.module_utils import common

        # Directly set the internal state since set_collection_info won't accept None
        common._collection_info_context["name"] = "test.collection"
        common._collection_info_context["version"] = None

        user_agent = _get_user_agent_string()

        assert "APN/1.0 Ansible/" in user_agent
        assert "test.collection" in user_agent
        # Should not have a slash after collection name since no version
        assert "test.collection/" not in user_agent

    def test_user_agent_with_empty_name(self):
        """Test user agent string when collection name is empty.

        Note: Due to how set_collection_info works (only updates if truthy),
        setting to empty string doesn't actually change the value.
        Testing actual behavior: defaults remain when empty string is passed.
        """
        from ansible_collections.amazon.aws.plugins.module_utils import common

        # Empty string is falsy, so set_collection_info won't update it
        # This tests that the default values are used
        common.set_collection_info(collection_name="", collection_version="1.0.0")

        user_agent = _get_user_agent_string()

        # Empty string doesn't update, so we still get default amazon.aws
        assert user_agent.startswith("APN/1.0 Ansible/")
        assert "amazon.aws/1.0.0" in user_agent

    def test_user_agent_with_none_name(self):
        """Test user agent string when collection name is None.

        Note: Due to how set_collection_info works (only updates if truthy),
        setting to None doesn't actually change the value.
        Testing actual behavior: defaults remain when None is passed.
        """
        from ansible_collections.amazon.aws.plugins.module_utils import common

        # None is falsy, so set_collection_info won't update it
        # This tests that the default values are used
        common.set_collection_info(collection_name=None, collection_version="1.0.0")

        user_agent = _get_user_agent_string()

        # None doesn't update, so we still get default amazon.aws
        assert user_agent.startswith("APN/1.0 Ansible/")
        assert "amazon.aws/1.0.0" in user_agent

    def test_user_agent_format(self):
        """Test that user agent string follows expected format."""
        from ansible_collections.amazon.aws.plugins.module_utils import common

        common.set_collection_info(collection_name="example.test", collection_version="2.3.4")

        user_agent = _get_user_agent_string()

        # Format should be: APN/1.0 Ansible/<version> <collection>/<version>
        parts = user_agent.split()
        assert parts[0] == "APN/1.0"
        assert parts[1].startswith("Ansible/")
        assert parts[2] == "example.test/2.3.4"

    @patch("ansible_collections.amazon.aws.plugins.module_utils.botocore.__version__", "2.16.1")
    def test_user_agent_real_world_scenario(self):
        """Test user agent string in a real-world scenario."""
        from ansible_collections.amazon.aws.plugins.module_utils import common

        # Scenario: Running from amazon.aws collection
        common.set_collection_info(collection_name="amazon.aws", collection_version="9.0.0")

        user_agent = _get_user_agent_string()

        expected = "APN/1.0 Ansible/2.16.1 amazon.aws/9.0.0"
        assert user_agent == expected
