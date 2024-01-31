# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

try:
    import botocore
except ImportError:
    pass

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.errors import AWSErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_list_handler.py requires the python modules 'boto3' and 'botocore'")


class AnsibleAWSExampleError(AnsibleAWSError):
    pass


class AWSExampleErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleAWSExampleError

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("NoSuchEntity")


class AWSCleanErrorHandler(AWSErrorHandler):
    @classmethod
    def _is_missing(cls):
        # Shouldn't be called if there's no error
        assert False, "_is_missing() should not be called when no errors occurred"


class TestAWSListHandler:
    def test_no_failures(self):
        self.counter = 0

        @AWSErrorHandler.list_error_handler("no error")
        def no_failures():
            self.counter += 1

        no_failures()
        assert self.counter == 1

    def test_client_error(self):
        self.counter = 0
        err_response = {"Error": {"Code": "MalformedPolicyDocument"}}

        @AWSErrorHandler.list_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleAWSError) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "do something" in raised.message
        assert "Something bad" in str(raised.exception)

    def test_no_missing_client_error(self):
        # If _is_missing() hasn't been overridden we do nothing interesting
        self.counter = 0
        err_response = {"Error": {"Code": "NoSuchEntity"}}

        @AWSErrorHandler.list_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleAWSError) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "do something" in raised.message
        assert "Something bad" in str(raised.exception)

    def test_list_error(self):
        self.counter = 0
        err_response = {"Error": {"Code": "NoSuchEntity"}}

        @AWSExampleErrorHandler.list_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "I couldn't find it")

        ret_val = raise_client_error()
        assert self.counter == 1
        assert ret_val is None

    def test_list_error_custom_return(self):
        self.counter = 0
        err_response = {"Error": {"Code": "NoSuchEntity"}}

        @AWSExampleErrorHandler.list_error_handler("do something", [])
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "I couldn't find it")

        ret_val = raise_client_error()
        assert self.counter == 1
        assert ret_val == []

    def test_custom_error(self):
        self.counter = 0
        err_response = {"Error": {"Code": "MalformedPolicyDocument"}}

        @AWSExampleErrorHandler.list_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleAWSExampleError) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "do something" in raised.message
        assert "Something bad" in str(raised.exception)
