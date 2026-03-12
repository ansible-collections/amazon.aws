# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.amazon.aws.plugins.module_utils.common import AMAZON_AWS_COLLECTION_NAME
from ansible_collections.amazon.aws.plugins.module_utils.common import AMAZON_AWS_COLLECTION_VERSION
from ansible_collections.amazon.aws.plugins.module_utils.common import get_collection_info
from ansible_collections.amazon.aws.plugins.module_utils.common import set_collection_info


class TestCommon:
    """Test suite for common.py module utilities."""

    def setup_method(self):
        """Reset collection info to defaults before each test."""
        set_collection_info(
            collection_name=AMAZON_AWS_COLLECTION_NAME,
            collection_version=AMAZON_AWS_COLLECTION_VERSION,
        )

    def teardown_method(self):
        """Reset collection info to defaults after each test to prevent pollution."""
        set_collection_info(
            collection_name=AMAZON_AWS_COLLECTION_NAME,
            collection_version=AMAZON_AWS_COLLECTION_VERSION,
        )

    def test_default_collection_name(self):
        """Test that AMAZON_AWS_COLLECTION_NAME has the expected value."""
        assert AMAZON_AWS_COLLECTION_NAME == "amazon.aws"

    def test_get_collection_info_default(self):
        """Test get_collection_info returns default values."""
        info = get_collection_info()
        assert info["name"] == AMAZON_AWS_COLLECTION_NAME
        assert info["version"] == AMAZON_AWS_COLLECTION_VERSION

    def test_get_collection_info_returns_dict(self):
        """Test get_collection_info returns a dictionary."""
        info = get_collection_info()
        assert isinstance(info, dict)
        assert "name" in info
        assert "version" in info

    def test_set_collection_info_name_only(self):
        """Test set_collection_info with collection_name parameter only."""
        set_collection_info(collection_name="custom.collection")
        info = get_collection_info()
        assert info["name"] == "custom.collection"
        # Version should remain unchanged from default
        assert info["version"] == AMAZON_AWS_COLLECTION_VERSION

    def test_set_collection_info_version_only(self):
        """Test set_collection_info with collection_version parameter only."""
        set_collection_info(collection_version="1.2.3")
        info = get_collection_info()
        # Name should remain unchanged from default
        assert info["name"] == AMAZON_AWS_COLLECTION_NAME
        assert info["version"] == "1.2.3"

    def test_set_collection_info_both_parameters(self):
        """Test set_collection_info with both parameters."""
        set_collection_info(collection_name="community.aws", collection_version="2.0.0")
        info = get_collection_info()
        assert info["name"] == "community.aws"
        assert info["version"] == "2.0.0"

    def test_set_collection_info_none_parameters(self):
        """Test set_collection_info with None parameters doesn't change values."""
        # Set to known values first
        set_collection_info(collection_name="test.collection", collection_version="1.0.0")

        # Call with None parameters
        set_collection_info(collection_name=None, collection_version=None)

        # Values should remain unchanged
        info = get_collection_info()
        assert info["name"] == "test.collection"
        assert info["version"] == "1.0.0"

    def test_set_collection_info_no_parameters(self):
        """Test set_collection_info with no parameters doesn't change values."""
        # Set to known values first
        set_collection_info(collection_name="test.collection", collection_version="1.0.0")

        # Call with no parameters
        set_collection_info()

        # Values should remain unchanged
        info = get_collection_info()
        assert info["name"] == "test.collection"
        assert info["version"] == "1.0.0"

    def test_collection_info_persistence(self):
        """Test that collection info persists between get_collection_info calls."""
        set_collection_info(collection_name="persistent.test", collection_version="3.0.0")

        # Call get_collection_info multiple times
        info1 = get_collection_info()
        info2 = get_collection_info()

        # Both calls should return the same values
        assert info1["name"] == "persistent.test"
        assert info1["version"] == "3.0.0"
        assert info2["name"] == "persistent.test"
        assert info2["version"] == "3.0.0"

    def test_collection_info_successive_updates(self):
        """Test that successive set_collection_info calls update the context."""
        # First update
        set_collection_info(collection_name="first.collection")
        info = get_collection_info()
        assert info["name"] == "first.collection"

        # Second update
        set_collection_info(collection_name="second.collection")
        info = get_collection_info()
        assert info["name"] == "second.collection"

        # Third update with version
        set_collection_info(collection_version="5.0.0")
        info = get_collection_info()
        assert info["name"] == "second.collection"  # Name unchanged
        assert info["version"] == "5.0.0"

    def test_collection_info_empty_string(self):
        """Test set_collection_info with empty strings (should not update)."""
        # Set to known values
        set_collection_info(collection_name="test.collection", collection_version="1.0.0")

        # Empty strings are falsy in Python, so they shouldn't update
        set_collection_info(collection_name="", collection_version="")

        info = get_collection_info()
        # Values should remain unchanged (empty strings are falsy)
        assert info["name"] == "test.collection"
        assert info["version"] == "1.0.0"

    def test_community_aws_use_case(self):
        """Test the actual use case from community.aws collection.

        This simulates how community.aws uses set_collection_info to override
        the collection name and version for user agent tracking.
        """
        # Simulate community.aws setting its own collection info
        set_collection_info(collection_name="community.aws", collection_version="12.0.0-dev0")

        info = get_collection_info()
        assert info["name"] == "community.aws"
        assert info["version"] == "12.0.0-dev0"

        # This would then be used in botocore._get_user_agent_string()
        # to build a user agent like: "APN/1.0 Ansible/2.15.0 community.aws/12.0.0-dev0"
