# -*- coding: utf-8 -*-
# Copyright: Ansible Project
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import os

import pytest

try:
    import boto3

    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible_collections.amazon.aws.plugins.module_utils.botocore import get_boto3_client_method_parameters

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_get_boto3_client_method_parameters.py requires boto3")


class TestGetBoto3ClientMethodParameters:
    """Test suite for get_boto3_client_method_parameters() function."""

    def setup_method(self):
        """Set AWS credentials to prevent metadata service calls."""
        os.environ["AWS_ACCESS_KEY_ID"] = "EXAMPLE_ID"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "EXAMPLE_SECRET"

    def teardown_method(self):
        """Clean up environment variables."""
        os.environ.pop("AWS_ACCESS_KEY_ID", None)
        os.environ.pop("AWS_SECRET_ACCESS_KEY", None)

    def test_get_all_parameters(self):
        """Test getting all parameters for a method."""
        client = boto3.client("ec2", region_name="us-east-1")

        parameters = get_boto3_client_method_parameters(client, "describe_instances", required=False)

        assert isinstance(parameters, list)
        assert "InstanceIds" in parameters
        assert "Filters" in parameters

    def test_get_required_parameters_only(self):
        """Test getting only required parameters for a method."""
        client = boto3.client("s3", region_name="us-east-1")

        parameters = get_boto3_client_method_parameters(client, "put_object", required=True)

        assert isinstance(parameters, list)
        assert "Bucket" in parameters
        assert "Key" in parameters

    def test_method_with_optional_parameters(self):
        """Test method that has optional parameters."""
        client = boto3.client("s3", region_name="us-east-1")

        parameters = get_boto3_client_method_parameters(client, "list_buckets", required=False)

        assert isinstance(parameters, list)
        assert len(parameters) > 0
