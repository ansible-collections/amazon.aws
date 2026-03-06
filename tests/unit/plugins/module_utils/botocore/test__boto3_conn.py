# -*- coding: utf-8 -*-
# Copyright: Ansible Project
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

try:
    import botocore
    import botocore.config

    HAS_BOTOCORE = True
except ImportError:
    HAS_BOTOCORE = False

from ansible_collections.amazon.aws.plugins.module_utils.botocore import _boto3_conn

if not HAS_BOTOCORE:
    pytestmark = pytest.mark.skip("test__boto3_conn.py requires botocore")


class TestBoto3ConnInvalidConnType:
    """Test _boto3_conn with invalid conn_type parameter."""

    def test_invalid_conn_type_raises_value_error(self):
        """Test that invalid conn_type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            _boto3_conn(conn_type="invalid", resource="ec2", region="us-east-1")

        assert "must specify either both, resource, or client" in str(exc_info.value)


class TestBoto3ConnResourceType:
    """Test _boto3_conn with conn_type='resource'."""

    @patch("ansible_collections.amazon.aws.plugins.module_utils.botocore.enable_placebo")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.botocore.boto3.session.Session")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.botocore._get_user_agent_string")
    def test_resource_conn_type(self, mock_user_agent, mock_session_class, mock_enable_placebo):
        """Test creating a resource connection."""
        mock_user_agent.return_value = "test-agent"
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_resource = MagicMock()
        mock_session.resource.return_value = mock_resource

        result = _boto3_conn(conn_type="resource", resource="s3", region="us-west-2")

        assert result == mock_resource
        mock_session.resource.assert_called_once()
        call_kwargs = mock_session.resource.call_args[1]
        assert call_kwargs["region_name"] == "us-west-2"
        mock_enable_placebo.assert_called_once_with(mock_session)


class TestBoto3ConnClientType:
    """Test _boto3_conn with conn_type='client'."""

    @patch("ansible_collections.amazon.aws.plugins.module_utils.botocore.enable_placebo")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.botocore.boto3.session.Session")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.botocore._get_user_agent_string")
    def test_client_conn_type(self, mock_user_agent, mock_session_class, mock_enable_placebo):
        """Test creating a client connection."""
        mock_user_agent.return_value = "test-agent"
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client

        result = _boto3_conn(conn_type="client", resource="ec2", region="eu-west-1", endpoint="https://example.com")

        assert result == mock_client
        mock_session.client.assert_called_once()
        call_kwargs = mock_session.client.call_args[1]
        assert call_kwargs["region_name"] == "eu-west-1"
        assert call_kwargs["endpoint_url"] == "https://example.com"


class TestBoto3ConnBothType:
    """Test _boto3_conn with conn_type='both'."""

    @patch("ansible_collections.amazon.aws.plugins.module_utils.botocore.enable_placebo")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.botocore.boto3.session.Session")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.botocore._get_user_agent_string")
    def test_both_conn_type(self, mock_user_agent, mock_session_class, mock_enable_placebo):
        """Test creating both client and resource connections."""
        mock_user_agent.return_value = "test-agent"
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_client = MagicMock()
        mock_resource = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session.resource.return_value = mock_resource

        result = _boto3_conn(conn_type="both", resource="s3", region="ap-southeast-1")

        assert isinstance(result, tuple)
        assert result[0] == mock_client
        assert result[1] == mock_resource
        assert mock_session.client.call_count == 1
        assert mock_session.resource.call_count == 1


class TestBoto3ConnConfigMerging:
    """Test _boto3_conn config parameter merging."""

    @patch("ansible_collections.amazon.aws.plugins.module_utils.botocore.enable_placebo")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.botocore.boto3.session.Session")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.botocore._get_user_agent_string")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.botocore._merge_botocore_config")
    def test_config_parameter_merged(self, mock_merge_config, mock_user_agent, mock_session_class, mock_enable_placebo):
        """Test that config parameter is merged."""
        mock_user_agent.return_value = "test-agent"
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client

        custom_config = botocore.config.Config(retries={"max_attempts": 5})
        mock_merge_config.side_effect = lambda base, custom: custom if custom else base

        _boto3_conn(conn_type="client", resource="ec2", region="us-east-1", config=custom_config)

        assert mock_merge_config.call_count == 2
        first_call = mock_merge_config.call_args_list[0]
        assert first_call[0][1] == custom_config

    @patch("ansible_collections.amazon.aws.plugins.module_utils.botocore.enable_placebo")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.botocore.boto3.session.Session")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.botocore._get_user_agent_string")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.botocore._merge_botocore_config")
    def test_aws_config_parameter_merged(
        self, mock_merge_config, mock_user_agent, mock_session_class, mock_enable_placebo
    ):
        """Test that aws_config parameter is merged."""
        mock_user_agent.return_value = "test-agent"
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client

        custom_config = botocore.config.Config(retries={"max_attempts": 3})
        mock_merge_config.side_effect = lambda base, custom: custom if custom else base

        _boto3_conn(conn_type="client", resource="ec2", region="us-east-1", aws_config=custom_config)

        assert mock_merge_config.call_count == 2
        second_call = mock_merge_config.call_args_list[1]
        assert second_call[0][1] == custom_config


class TestBoto3ConnProfileName:
    """Test _boto3_conn with profile_name parameter."""

    @patch("ansible_collections.amazon.aws.plugins.module_utils.botocore.enable_placebo")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.botocore.boto3.session.Session")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.botocore._get_user_agent_string")
    def test_profile_name_passed_to_session(self, mock_user_agent, mock_session_class, mock_enable_placebo):
        """Test that profile_name is passed to Session."""
        mock_user_agent.return_value = "test-agent"
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client

        _boto3_conn(conn_type="client", resource="ec2", region="us-east-1", profile_name="my-profile")

        mock_session_class.assert_called_once_with(profile_name="my-profile")
