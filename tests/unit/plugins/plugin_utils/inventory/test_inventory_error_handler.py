# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

try:
    import botocore
except ImportError:
    pass

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3
from ansible_collections.amazon.aws.plugins.plugin_utils.inventory import AnsibleInventoryAWSError
from ansible_collections.amazon.aws.plugins.plugin_utils.inventory import AnsibleInventoryPermissionsError
from ansible_collections.amazon.aws.plugins.plugin_utils.inventory import InventoryErrorHandler

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_inventory_error_handler.py requires the python modules 'boto3' and 'botocore'")


class TestInventoryCommonHandler:
    def test_no_failures(self):
        self.counter = 0

        @InventoryErrorHandler.common_error_handler("no error")
        def no_failures():
            self.counter += 1

        no_failures()
        assert self.counter == 1

    def test_client_error(self):
        self.counter = 0
        err_response = {
            "Error": {
                "Code": "InvalidParameterValue",
                "Message": "Invalid parameter value",
            }
        }

        @InventoryErrorHandler.common_error_handler("describe instances")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "DescribeInstances")

        with pytest.raises(AnsibleInventoryAWSError) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "describe instances" in raised.message
        assert "DescribeInstances" in str(raised.exception)

    def test_waiter_error(self):
        self.counter = 0

        @InventoryErrorHandler.common_error_handler("wait for instances")
        def raise_waiter_error():
            self.counter += 1
            raise botocore.exceptions.WaiterError(
                name="InstanceRunning",
                reason="Max attempts exceeded",
                last_response={},
            )

        with pytest.raises(AnsibleInventoryAWSError) as e_info:
            raise_waiter_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.WaiterError)
        assert "Timeout trying to wait for instances" in raised.message

    def test_permissions_error_unauthorized(self):
        self.counter = 0
        err_response = {
            "Error": {
                "Code": "UnauthorizedOperation",
                "Message": "You are not authorized to perform this operation",
            },
            "ResponseMetadata": {"HTTPStatusCode": 403},
        }

        @InventoryErrorHandler.common_error_handler("describe instances")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "DescribeInstances")

        with pytest.raises(AnsibleInventoryPermissionsError) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "describe instances" in raised.message
        assert "permission denied" in raised.message
        assert "DescribeInstances" in str(raised.exception)

    def test_permissions_error_http_403(self):
        """Test that HTTP 403 status code raises AnsibleInventoryPermissionsError"""
        self.counter = 0
        err_response = {
            "Error": {
                "Code": "AccessDenied",
                "Message": "Access Denied",
            },
            "ResponseMetadata": {"HTTPStatusCode": 403},
        }

        @InventoryErrorHandler.common_error_handler("list hosted zones")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "ListHostedZones")

        with pytest.raises(AnsibleInventoryPermissionsError) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "list hosted zones" in raised.message
        assert "permission denied" in raised.message
        assert "ListHostedZones" in str(raised.exception)

    def test_botocore_error(self):
        self.counter = 0

        @InventoryErrorHandler.common_error_handler("connect to endpoint")
        def raise_connection_error():
            self.counter += 1
            raise botocore.exceptions.EndpointConnectionError(endpoint_url="https://ec2.us-east-1.amazonaws.com")

        with pytest.raises(AnsibleInventoryAWSError) as e_info:
            raise_connection_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.BotoCoreError)
        assert "connect to endpoint" in raised.message
        assert "ec2.us-east-1.amazonaws.com" in str(raised.exception)


class TestInventoryListHandler:
    def test_no_failures(self):
        self.counter = 0

        @InventoryErrorHandler.list_error_handler("no error")
        def no_failures():
            self.counter += 1

        no_failures()
        assert self.counter == 1

    def test_client_error(self):
        self.counter = 0
        err_response = {
            "Error": {
                "Code": "ValidationException",
                "Message": "Validation failed",
            }
        }

        @InventoryErrorHandler.list_error_handler("get inventory")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "GetInventory")

        with pytest.raises(AnsibleInventoryAWSError) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "get inventory" in raised.message
        assert "GetInventory" in str(raised.exception)

    def test_list_error(self):
        self.counter = 0
        err_response = {
            "Error": {
                "Code": "ResourceNotFoundException",
                "Message": "Resource not found",
            }
        }

        @InventoryErrorHandler.list_error_handler("get hosted zone")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "GetHostedZone")

        ret_val = raise_client_error()
        assert self.counter == 1
        assert ret_val is None

    def test_list_error_with_default(self):
        self.counter = 0
        err_response = {
            "Error": {
                "Code": "NoSuchEntity",
                "Message": "Entity not found",
            }
        }

        @InventoryErrorHandler.list_error_handler("list records", default_value=[])
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "ListResourceRecordSets")

        ret_val = raise_client_error()
        assert self.counter == 1
        assert ret_val == []

    def test_permissions_error_not_silenced(self):
        """Test that permission errors are NOT silenced by list_error_handler"""
        self.counter = 0
        err_response = {
            "Error": {
                "Code": "UnauthorizedOperation",
                "Message": "You are not authorized",
            },
            "ResponseMetadata": {"HTTPStatusCode": 403},
        }

        @InventoryErrorHandler.list_error_handler("describe instances")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "DescribeInstances")

        with pytest.raises(AnsibleInventoryPermissionsError) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "permission denied" in raised.message
