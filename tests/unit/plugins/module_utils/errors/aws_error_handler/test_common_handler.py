# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

try:
    import botocore
except ImportError:
    pass

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3
from ansible_collections.amazon.aws.plugins.module_utils.errors import AWSErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_common_handler.py requires the python modules 'boto3' and 'botocore'")


class AnsibleAWSExampleError(AnsibleAWSError):
    pass


class AWSExampleErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleAWSExampleError

    @classmethod
    def _is_missing(cls):
        # Shouldn't be called by the 'common' handler
        assert False, "_is_missing() should not be called by common_error_handler"


class TestAwsCommonHandler:
    def test_no_failures(self):
        self.counter = 0

        @AWSErrorHandler.common_error_handler("no error")
        def no_failures():
            self.counter += 1

        no_failures()
        assert self.counter == 1

    def test_no_failures_no_missing(self):
        self.counter = 0

        @AWSExampleErrorHandler.common_error_handler("no error")
        def no_failures():
            self.counter += 1

        no_failures()
        assert self.counter == 1

    def test_client_error(self):
        self.counter = 0
        err_response = {"Error": {"Code": "MalformedPolicyDocument"}}

        @AWSErrorHandler.common_error_handler("do something")
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

    def test_custom_error(self):
        self.counter = 0
        err_response = {"Error": {"Code": "MalformedPolicyDocument"}}

        @AWSExampleErrorHandler.common_error_handler("do something")
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

    def test_format_string_single_param(self):
        self.counter = 0
        err_response = {"Error": {"Code": "MalformedPolicyDocument"}}

        @AWSErrorHandler.common_error_handler("get role {name}")
        def raise_client_error(name):
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleAWSError) as e_info:
            raise_client_error("test-role")
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "get role test-role" in raised.message
        assert "Something bad" in str(raised.exception)

    def test_format_string_multiple_params(self):
        self.counter = 0
        err_response = {"Error": {"Code": "MalformedPolicyDocument"}}

        @AWSErrorHandler.common_error_handler("attach policy {policy} to role {role}")
        def raise_client_error(client, role, policy):
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleAWSError) as e_info:
            raise_client_error(None, "test-role", "test-policy")
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "attach policy test-policy to role test-role" in raised.message

    def test_format_string_kwargs(self):
        self.counter = 0
        err_response = {"Error": {"Code": "MalformedPolicyDocument"}}

        @AWSErrorHandler.common_error_handler("update role {name}")
        def raise_client_error(client, name=None):
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleAWSError) as e_info:
            raise_client_error(None, name="my-role")
        assert self.counter == 1
        raised = e_info.value
        assert "update role my-role" in raised.message

    def test_format_string_fallback_on_invalid_param(self):
        self.counter = 0
        err_response = {"Error": {"Code": "MalformedPolicyDocument"}}

        @AWSErrorHandler.common_error_handler("get role {nonexistent}")
        def raise_client_error(name):
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleAWSError) as e_info:
            raise_client_error("test-role")
        assert self.counter == 1
        raised = e_info.value
        # Should fall back to original description with error note when format fails
        assert "get role {nonexistent}" in raised.message
        assert "error formatting message" in raised.message

    def test_format_string_no_params(self):
        self.counter = 0

        @AWSErrorHandler.common_error_handler("list all roles")
        def no_failures():
            self.counter += 1

        no_failures()
        assert self.counter == 1

    def test_format_string_waiter_error(self):
        self.counter = 0

        @AWSErrorHandler.common_error_handler("wait for role {name}")
        def raise_waiter_error(name):
            self.counter += 1
            raise botocore.exceptions.WaiterError("RoleExists", "Max attempts exceeded", {})

        with pytest.raises(AnsibleAWSError) as e_info:
            raise_waiter_error("test-role")
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.WaiterError)
        assert "Timeout trying to wait for role test-role" in raised.message
