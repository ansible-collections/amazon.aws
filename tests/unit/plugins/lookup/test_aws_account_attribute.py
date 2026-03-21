# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible.errors import AnsibleLookupError

from ansible_collections.amazon.aws.plugins.lookup.aws_account_attribute import LookupModule


@pytest.fixture(name="lookup_plugin")
def fixture_lookup_plugin():
    lookup = LookupModule()
    lookup._display = MagicMock()
    lookup.set_options = MagicMock()
    # Mock the cached client instead of the property
    lookup._cached_client = MagicMock()
    return lookup


class TestBuildApiParams:
    """Unit tests for _build_api_params method"""

    def test_build_params_has_ec2_classic(self, lookup_plugin):
        """Test building parameters for has-ec2-classic attribute"""
        params, check_ec2_classic = lookup_plugin._build_api_params("has-ec2-classic")
        assert params == {"AttributeNames": ["supported-platforms"]}
        assert check_ec2_classic is True

    def test_build_params_specific_attribute(self, lookup_plugin):
        """Test building parameters for a specific attribute"""
        params, check_ec2_classic = lookup_plugin._build_api_params("default-vpc")
        assert params == {"AttributeNames": ["default-vpc"]}
        assert check_ec2_classic is False

    def test_build_params_all_attributes(self, lookup_plugin):
        """Test building parameters for all attributes (None)"""
        params, check_ec2_classic = lookup_plugin._build_api_params(None)
        assert params == {"AttributeNames": []}
        assert check_ec2_classic is False

    def test_build_params_max_instances(self, lookup_plugin):
        """Test building parameters for max-instances attribute"""
        params, check_ec2_classic = lookup_plugin._build_api_params("max-instances")
        assert params == {"AttributeNames": ["max-instances"]}
        assert check_ec2_classic is False

    def test_build_params_returns_tuple(self, lookup_plugin):
        """Test that the method returns a tuple"""
        result = lookup_plugin._build_api_params("default-vpc")
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestProcessResponseForEc2Classic:
    """Unit tests for _process_response_for_ec2_classic method"""

    def test_ec2_classic_supported(self, lookup_plugin):
        """Test when EC2-Classic is supported"""
        response = [
            {
                "AttributeName": "supported-platforms",
                "AttributeValues": [{"AttributeValue": "EC2"}, {"AttributeValue": "VPC"}],
            }
        ]
        result = lookup_plugin._process_response_for_ec2_classic(response)
        assert result is True

    def test_ec2_classic_not_supported(self, lookup_plugin):
        """Test when EC2-Classic is not supported"""
        response = [{"AttributeName": "supported-platforms", "AttributeValues": [{"AttributeValue": "VPC"}]}]
        result = lookup_plugin._process_response_for_ec2_classic(response)
        assert result is False

    def test_ec2_classic_only_ec2(self, lookup_plugin):
        """Test when only EC2 is supported (unlikely but valid)"""
        response = [{"AttributeName": "supported-platforms", "AttributeValues": [{"AttributeValue": "EC2"}]}]
        result = lookup_plugin._process_response_for_ec2_classic(response)
        assert result is True

    def test_ec2_classic_empty_values(self, lookup_plugin):
        """Test when no platforms are returned"""
        response = [{"AttributeName": "supported-platforms", "AttributeValues": []}]
        result = lookup_plugin._process_response_for_ec2_classic(response)
        assert result is False


class TestProcessResponseForAttribute:
    """Unit tests for _process_response_for_attribute method"""

    def test_single_value(self, lookup_plugin):
        """Test extracting a single attribute value"""
        response = [{"AttributeName": "default-vpc", "AttributeValues": [{"AttributeValue": "vpc-12345678"}]}]
        result = lookup_plugin._process_response_for_attribute(response)
        assert result == ["vpc-12345678"]

    def test_multiple_values(self, lookup_plugin):
        """Test extracting multiple attribute values"""
        response = [
            {
                "AttributeName": "supported-platforms",
                "AttributeValues": [{"AttributeValue": "EC2"}, {"AttributeValue": "VPC"}],
            }
        ]
        result = lookup_plugin._process_response_for_attribute(response)
        assert result == ["EC2", "VPC"]

    def test_numeric_value(self, lookup_plugin):
        """Test extracting numeric attribute values"""
        response = [{"AttributeName": "max-instances", "AttributeValues": [{"AttributeValue": "20"}]}]
        result = lookup_plugin._process_response_for_attribute(response)
        assert result == ["20"]

    def test_empty_values(self, lookup_plugin):
        """Test extracting from empty attribute values"""
        response = [{"AttributeName": "default-vpc", "AttributeValues": []}]
        result = lookup_plugin._process_response_for_attribute(response)
        assert result == []


class TestProcessResponseForAllAttributes:
    """Unit tests for _process_response_for_all_attributes method"""

    def test_multiple_attributes(self, lookup_plugin):
        """Test flattening multiple attributes"""
        response = [
            {"AttributeName": "default-vpc", "AttributeValues": [{"AttributeValue": "vpc-12345678"}]},
            {"AttributeName": "max-instances", "AttributeValues": [{"AttributeValue": "20"}]},
            {
                "AttributeName": "supported-platforms",
                "AttributeValues": [{"AttributeValue": "EC2"}, {"AttributeValue": "VPC"}],
            },
        ]
        result = lookup_plugin._process_response_for_all_attributes(response)
        assert result == {
            "default-vpc": ["vpc-12345678"],
            "max-instances": ["20"],
            "supported-platforms": ["EC2", "VPC"],
        }

    def test_single_attribute(self, lookup_plugin):
        """Test flattening a single attribute"""
        response = [{"AttributeName": "default-vpc", "AttributeValues": [{"AttributeValue": "vpc-12345678"}]}]
        result = lookup_plugin._process_response_for_all_attributes(response)
        assert result == {"default-vpc": ["vpc-12345678"]}

    def test_empty_response(self, lookup_plugin):
        """Test flattening empty response"""
        response = []
        result = lookup_plugin._process_response_for_all_attributes(response)
        assert result == {}

    def test_attribute_with_multiple_values(self, lookup_plugin):
        """Test flattening attribute with multiple values"""
        response = [
            {"AttributeName": "max-elastic-ips", "AttributeValues": [{"AttributeValue": "5"}]},
            {"AttributeName": "vpc-max-elastic-ips", "AttributeValues": [{"AttributeValue": "5"}]},
        ]
        result = lookup_plugin._process_response_for_all_attributes(response)
        assert result == {"max-elastic-ips": ["5"], "vpc-max-elastic-ips": ["5"]}


class TestRun:
    """Unit tests for run method integration"""

    def test_run_has_ec2_classic_true(self, lookup_plugin):
        """Test run with has-ec2-classic attribute returning true"""
        lookup_plugin._cached_client.describe_account_attributes.return_value = {
            "AccountAttributes": [
                {
                    "AttributeName": "supported-platforms",
                    "AttributeValues": [{"AttributeValue": "EC2"}, {"AttributeValue": "VPC"}],
                }
            ]
        }

        with patch.object(lookup_plugin, "run", wraps=lookup_plugin.run):
            result = lookup_plugin.run([], {}, attribute="has-ec2-classic")

        assert result == [True]

    def test_run_has_ec2_classic_false(self, lookup_plugin):
        """Test run with has-ec2-classic attribute returning false"""
        lookup_plugin._cached_client.describe_account_attributes.return_value = {
            "AccountAttributes": [
                {"AttributeName": "supported-platforms", "AttributeValues": [{"AttributeValue": "VPC"}]}
            ]
        }

        with patch.object(lookup_plugin, "run", wraps=lookup_plugin.run):
            result = lookup_plugin.run([], {}, attribute="has-ec2-classic")

        assert result == [False]

    def test_run_specific_attribute(self, lookup_plugin):
        """Test run with a specific attribute"""
        lookup_plugin._cached_client.describe_account_attributes.return_value = {
            "AccountAttributes": [
                {"AttributeName": "default-vpc", "AttributeValues": [{"AttributeValue": "vpc-12345678"}]}
            ]
        }

        with patch.object(lookup_plugin, "run", wraps=lookup_plugin.run):
            result = lookup_plugin.run([], {}, attribute="default-vpc")

        assert result == ["vpc-12345678"]

    def test_run_all_attributes(self, lookup_plugin):
        """Test run with no attribute specified (all attributes)"""
        lookup_plugin._cached_client.describe_account_attributes.return_value = {
            "AccountAttributes": [
                {"AttributeName": "default-vpc", "AttributeValues": [{"AttributeValue": "vpc-12345678"}]},
                {"AttributeName": "max-instances", "AttributeValues": [{"AttributeValue": "20"}]},
            ]
        }

        with patch.object(lookup_plugin, "run", wraps=lookup_plugin.run):
            result = lookup_plugin.run([], {})

        assert result == [{"default-vpc": ["vpc-12345678"], "max-instances": ["20"]}]

    def test_run_client_error(self, lookup_plugin):
        """Test run with ClientError from AWS"""
        import botocore.exceptions

        error = botocore.exceptions.ClientError(
            {"Error": {"Code": "UnauthorizedOperation", "Message": "Not authorized"}}, "DescribeAccountAttributes"
        )
        lookup_plugin._cached_client.describe_account_attributes.side_effect = error

        with patch.object(lookup_plugin, "run", wraps=lookup_plugin.run):
            with pytest.raises(AnsibleLookupError) as exc_info:
                lookup_plugin.run([], {}, attribute="default-vpc")

        assert "Failed to describe account attributes" in str(exc_info.value)

    def test_run_botocore_error(self, lookup_plugin):
        """Test run with BotoCoreError from AWS"""
        import botocore.exceptions

        error = botocore.exceptions.BotoCoreError()
        lookup_plugin._cached_client.describe_account_attributes.side_effect = error

        with patch.object(lookup_plugin, "run", wraps=lookup_plugin.run):
            with pytest.raises(AnsibleLookupError) as exc_info:
                lookup_plugin.run([], {}, attribute="default-vpc")

        assert "Failed to describe account attributes" in str(exc_info.value)

    def test_run_calls_describe_with_correct_params(self, lookup_plugin):
        """Test that run calls describe_account_attributes with correct parameters"""
        lookup_plugin._cached_client.describe_account_attributes.return_value = {
            "AccountAttributes": [{"AttributeName": "max-instances", "AttributeValues": [{"AttributeValue": "20"}]}]
        }

        with patch.object(lookup_plugin, "run", wraps=lookup_plugin.run):
            lookup_plugin.run([], {}, attribute="max-instances")

        lookup_plugin._cached_client.describe_account_attributes.assert_called_once_with(
            aws_retry=True, AttributeNames=["max-instances"]
        )

    def test_run_all_attributes_empty_params(self, lookup_plugin):
        """Test that run calls describe_account_attributes with empty AttributeNames for all attributes"""
        lookup_plugin._cached_client.describe_account_attributes.return_value = {"AccountAttributes": []}

        with patch.object(lookup_plugin, "run", wraps=lookup_plugin.run):
            lookup_plugin.run([], {})

        lookup_plugin._cached_client.describe_account_attributes.assert_called_once_with(aws_retry=True, AttributeNames=[])
