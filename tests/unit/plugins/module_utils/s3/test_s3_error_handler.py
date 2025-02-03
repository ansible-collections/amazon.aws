# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

try:
    import botocore
except ImportError:
    pass

import pytest

pytest.skip("skipping tests for s3 code that hasn't been backported yet", allow_module_level=True)

from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3
from ansible_collections.amazon.aws.plugins.module_utils.s3 import AnsibleS3Error
from ansible_collections.amazon.aws.plugins.module_utils.s3 import AnsibleS3PermissionsError
from ansible_collections.amazon.aws.plugins.module_utils.s3 import AnsibleS3Sigv4RequiredError
from ansible_collections.amazon.aws.plugins.module_utils.s3 import AnsibleS3SupportError
from ansible_collections.amazon.aws.plugins.module_utils.s3 import S3ErrorHandler

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_s3_error_handler.py requires the python modules 'boto3' and 'botocore'")


class TestS3DeletionHandler:
    def test_no_failures(self):
        self.counter = 0

        @S3ErrorHandler.deletion_error_handler("no error")
        def no_failures():
            self.counter += 1

        no_failures()
        assert self.counter == 1

    def test_client_error(self):
        self.counter = 0
        err_response = {
            "Error": {
                "Code": "MalformedPolicyDocument",
                "Message": "Policy document should not specify a principal",
            }
        }

        @S3ErrorHandler.deletion_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleS3Error) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "do something" in raised.message
        assert "Something bad" in str(raised.exception)

    def test_ignore_error(self):
        self.counter = 0
        err_response = {
            "Error": {
                "Code": "404",
                "Message": "Not found",
            }
        }

        @S3ErrorHandler.deletion_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "I couldn't find it")

        ret_val = raise_client_error()
        assert self.counter == 1
        assert ret_val is False


class TestS3ListHandler:
    def test_no_failures(self):
        self.counter = 0

        @S3ErrorHandler.list_error_handler("no error")
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

        @S3ErrorHandler.list_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleS3Error) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "do something" in raised.message
        assert "Something bad" in str(raised.exception)

    def test_list_error(self):
        self.counter = 0
        err_response = {
            "Error": {
                "Code": "404",
                "Message": "Not found",
            }
        }

        @S3ErrorHandler.list_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "I couldn't find it")

        ret_val = raise_client_error()
        assert self.counter == 1
        assert ret_val is None


class TestS3CommonHandler:
    def test_no_failures(self):
        self.counter = 0

        @S3ErrorHandler.common_error_handler("no error")
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

        @S3ErrorHandler.common_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleS3Error) as e_info:
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
                "Code": "AccessDenied",
                "Message": "Forbidden",
            }
        }

        @S3ErrorHandler.common_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleS3PermissionsError) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "do something" in raised.message
        assert "Something bad" in str(raised.exception)

    def test_not_implemented_error(self):
        self.counter = 0
        err_response = {
            "Error": {
                "Code": "XNotImplemented",
                "Message": "The request you provided implies functionality that is not implemented.",
            }
        }

        @S3ErrorHandler.common_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleS3SupportError) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "do something" in raised.message
        assert "Something bad" in str(raised.exception)

    def test_endpoint_error(self):
        self.counter = 0

        @S3ErrorHandler.common_error_handler("do something")
        def raise_connection_error():
            self.counter += 1
            raise botocore.exceptions.EndpointConnectionError(endpoint_url="junk.endpoint")

        with pytest.raises(AnsibleS3Error) as e_info:
            raise_connection_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.BotoCoreError)
        assert "do something" in raised.message
        assert "junk.endpoint" in str(raised.exception)

    def test_sigv4_error(self):
        self.counter = 0
        err_response = {
            "Error": {
                "Code": "InvalidArgument",
                "Message": "Requests specifying Server Side Encryption with AWS KMS managed keys require AWS Signature Version 4",
            }
        }

        @S3ErrorHandler.common_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleS3Sigv4RequiredError) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "do something" in raised.message
        assert "Something bad" in str(raised.exception)

    def test_boto3_error(self):
        self.counter = 0
        err_response = {
            "Error": {
                "Code": "MalformedPolicyDocument",
                "Message": "Policy document should not specify a principal.",
            }
        }

        @S3ErrorHandler.common_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleS3Error) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "do something" in raised.message
        assert "Something bad" in str(raised.exception)
