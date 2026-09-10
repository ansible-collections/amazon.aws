# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

try:
    import botocore
except ImportError:
    pass

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3
from ansible_collections.amazon.aws.plugins.module_utils.kms import AnsibleKMSError
from ansible_collections.amazon.aws.plugins.module_utils.kms import AnsibleKMSPermissionsError
from ansible_collections.amazon.aws.plugins.module_utils.kms import AnsibleKMSUnsupportedError
from ansible_collections.amazon.aws.plugins.module_utils.kms import KMSErrorHandler

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_common.py requires the python modules 'boto3' and 'botocore'")


class TestKMSCommonHandler:
    def test_no_failures(self):
        self.counter = 0

        @KMSErrorHandler.common_error_handler("no error")
        def no_failures():
            self.counter += 1

        no_failures()
        assert self.counter == 1

    def test_client_error(self):
        self.counter = 0
        err_response = {
            "Error": {
                "Code": "MalformedPolicyDocument",
                "Message": "Policy document should not specify a principal.",
            }
        }

        @KMSErrorHandler.common_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleKMSError) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "do something" in raised.message
        assert "Something bad" in str(raised.exception)

    def test_permissions_error(self):
        self.counter = 0
        err_response = {
            "Error": {
                "Code": "AccessDeniedException",
                "Message": "User is not authorized to perform kms:GetKeyRotationStatus",
            }
        }

        @KMSErrorHandler.common_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleKMSPermissionsError) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "do something" in raised.message
        assert "permission denied" in raised.message
        assert "Something bad" in str(raised.exception)

    def test_unsupported_operation_error(self):
        self.counter = 0
        err_response = {
            "Error": {
                "Code": "UnsupportedOperationException",
                "Message": "The request is not supported for the specified key",
            }
        }

        @KMSErrorHandler.common_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleKMSUnsupportedError) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "do something" in raised.message
        assert "operation not supported" in raised.message
        assert "Something bad" in str(raised.exception)

    def test_not_found_error(self):
        self.counter = 0
        err_response = {
            "Error": {
                "Code": "NotFoundException",
                "Message": "Key not found",
            }
        }

        @KMSErrorHandler.common_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleKMSError) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "do something" in raised.message
        assert "Something bad" in str(raised.exception)

    def test_invalid_key_id_error(self):
        self.counter = 0
        err_response = {
            "Error": {
                "Code": "InvalidKeyId",
                "Message": "Invalid key id",
            }
        }

        @KMSErrorHandler.common_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleKMSError) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "do something" in raised.message
        assert "Something bad" in str(raised.exception)

    def test_endpoint_error(self):
        self.counter = 0

        @KMSErrorHandler.common_error_handler("do something")
        def raise_connection_error():
            self.counter += 1
            raise botocore.exceptions.EndpointConnectionError(endpoint_url="junk.endpoint")

        with pytest.raises(AnsibleKMSError) as e_info:
            raise_connection_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.BotoCoreError)
        assert "do something" in raised.message
        assert "junk.endpoint" in str(raised.exception)

    def test_boto3_error(self):
        self.counter = 0
        err_response = {
            "Error": {
                "Code": "MalformedPolicyDocument",
                "Message": "Policy document should not specify a principal.",
            }
        }

        @KMSErrorHandler.common_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleKMSError) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "do something" in raised.message
        assert "Something bad" in str(raised.exception)
