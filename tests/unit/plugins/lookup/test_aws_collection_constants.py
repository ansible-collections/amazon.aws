# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible.errors import AnsibleLookupError

from ansible_collections.amazon.aws.plugins.lookup.aws_collection_constants import LookupModule


@pytest.fixture(name="lookup_plugin")
def fixture_lookup_plugin():
    lookup = LookupModule()
    lookup._display = MagicMock()
    return lookup


class TestValidateTerms:
    """Unit tests for _validate_terms helper method"""

    def test_validate_single_term(self, lookup_plugin):
        """Test that single term is valid"""
        # Should not raise
        lookup_plugin._validate_terms(["MINIMUM_BOTOCORE_VERSION"])

    def test_validate_empty_terms(self, lookup_plugin):
        """Test that empty terms raises error"""
        with pytest.raises(AnsibleLookupError) as exc_info:
            lookup_plugin._validate_terms([])
        assert "Constant name not provided" in str(exc_info.value)

    def test_validate_multiple_terms(self, lookup_plugin):
        """Test that multiple terms raises error"""
        with pytest.raises(AnsibleLookupError) as exc_info:
            lookup_plugin._validate_terms(["MINIMUM_BOTOCORE_VERSION", "HAS_BOTO3"])
        assert "Multiple constant names provided" in str(exc_info.value)


class TestLookupConstant:
    """Unit tests for lookup_constant method"""

    def test_lookup_minimum_botocore_version(self, lookup_plugin):
        """Test looking up MINIMUM_BOTOCORE_VERSION"""
        result = lookup_plugin.lookup_constant("MINIMUM_BOTOCORE_VERSION")
        assert result is not None
        assert isinstance(result, str)

    def test_lookup_minimum_boto3_version(self, lookup_plugin):
        """Test looking up MINIMUM_BOTO3_VERSION"""
        result = lookup_plugin.lookup_constant("MINIMUM_BOTO3_VERSION")
        assert result is not None
        assert isinstance(result, str)

    def test_lookup_has_boto3(self, lookup_plugin):
        """Test looking up HAS_BOTO3"""
        result = lookup_plugin.lookup_constant("HAS_BOTO3")
        assert result is not None
        assert isinstance(result, bool)

    def test_lookup_amazon_aws_collection_version(self, lookup_plugin):
        """Test looking up AMAZON_AWS_COLLECTION_VERSION"""
        result = lookup_plugin.lookup_constant("AMAZON_AWS_COLLECTION_VERSION")
        assert result is not None
        assert isinstance(result, str)

    def test_lookup_amazon_aws_collection_name(self, lookup_plugin):
        """Test looking up AMAZON_AWS_COLLECTION_NAME"""
        result = lookup_plugin.lookup_constant("AMAZON_AWS_COLLECTION_NAME")
        assert result is not None
        assert isinstance(result, str)

    def test_lookup_community_aws_collection_version_when_available(self, lookup_plugin):
        """Test looking up COMMUNITY_AWS_COLLECTION_VERSION when community collection is available"""
        import ansible_collections.amazon.aws.plugins.lookup.aws_collection_constants as constants_module

        mock_utils = MagicMock()
        mock_utils.COMMUNITY_AWS_COLLECTION_VERSION = "1.0.0"

        # Set the attribute before patching since it may not exist
        setattr(constants_module, "community_utils", mock_utils)
        try:
            with patch.object(constants_module, "HAS_COMMUNITY", True):
                result = lookup_plugin.lookup_constant("COMMUNITY_AWS_COLLECTION_VERSION")
                assert result == "1.0.0"
        finally:
            # Clean up the attribute
            if hasattr(constants_module, "community_utils"):
                delattr(constants_module, "community_utils")

    @patch("ansible_collections.amazon.aws.plugins.lookup.aws_collection_constants.HAS_COMMUNITY", False)
    def test_lookup_community_aws_collection_version_when_unavailable(self, lookup_plugin):
        """Test looking up COMMUNITY_AWS_COLLECTION_VERSION when community collection is not available"""
        with pytest.raises(AnsibleLookupError) as exc_info:
            lookup_plugin.lookup_constant("COMMUNITY_AWS_COLLECTION_VERSION")
        assert "Unable to load ansible_collections.community.aws" in str(exc_info.value)

    def test_lookup_community_aws_collection_name_when_available(self, lookup_plugin):
        """Test looking up COMMUNITY_AWS_COLLECTION_NAME when community collection is available"""
        import ansible_collections.amazon.aws.plugins.lookup.aws_collection_constants as constants_module

        mock_utils = MagicMock()
        mock_utils.COMMUNITY_AWS_COLLECTION_NAME = "community.aws"

        # Set the attribute before patching since it may not exist
        setattr(constants_module, "community_utils", mock_utils)
        try:
            with patch.object(constants_module, "HAS_COMMUNITY", True):
                result = lookup_plugin.lookup_constant("COMMUNITY_AWS_COLLECTION_NAME")
                assert result == "community.aws"
        finally:
            # Clean up the attribute
            if hasattr(constants_module, "community_utils"):
                delattr(constants_module, "community_utils")

    @patch("ansible_collections.amazon.aws.plugins.lookup.aws_collection_constants.HAS_COMMUNITY", False)
    def test_lookup_community_aws_collection_name_when_unavailable(self, lookup_plugin):
        """Test looking up COMMUNITY_AWS_COLLECTION_NAME when community collection is not available"""
        with pytest.raises(AnsibleLookupError) as exc_info:
            lookup_plugin.lookup_constant("COMMUNITY_AWS_COLLECTION_NAME")
        assert "Unable to load ansible_collections.community.aws" in str(exc_info.value)

    def test_lookup_invalid_constant(self, lookup_plugin):
        """Test that looking up an invalid constant returns None"""
        result = lookup_plugin.lookup_constant("INVALID_CONSTANT")
        assert result is None


class TestRun:
    """Unit tests for run method"""

    def test_run_with_valid_constant(self, lookup_plugin):
        """Test run with a valid constant name"""
        lookup_plugin.set_options = MagicMock()
        result = lookup_plugin.run(["MINIMUM_BOTOCORE_VERSION"], {})
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] is not None

    def test_run_normalizes_case(self, lookup_plugin):
        """Test that run normalizes constant name to uppercase"""
        lookup_plugin.set_options = MagicMock()
        result = lookup_plugin.run(["minimum_botocore_version"], {})
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] is not None

    def test_run_with_no_terms(self, lookup_plugin):
        """Test that run raises error when no terms provided"""
        lookup_plugin.set_options = MagicMock()
        with pytest.raises(AnsibleLookupError) as exc_info:
            lookup_plugin.run([], {})
        assert "Constant name not provided" in str(exc_info.value)

    def test_run_with_multiple_terms(self, lookup_plugin):
        """Test that run raises error when multiple terms provided"""
        lookup_plugin.set_options = MagicMock()
        with pytest.raises(AnsibleLookupError) as exc_info:
            lookup_plugin.run(["MINIMUM_BOTOCORE_VERSION", "MINIMUM_BOTO3_VERSION"], {})
        assert "Multiple constant names provided" in str(exc_info.value)

    def test_run_calls_set_options(self, lookup_plugin):
        """Test that run calls set_options with correct parameters"""
        lookup_plugin.set_options = MagicMock()
        variables = {"var1": "value1"}
        kwargs = {"key1": "value1"}
        lookup_plugin.run(["HAS_BOTO3"], variables, **kwargs)
        lookup_plugin.set_options.assert_called_once_with(var_options=variables, direct=kwargs)
