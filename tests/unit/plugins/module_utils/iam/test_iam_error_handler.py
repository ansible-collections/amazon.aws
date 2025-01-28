# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

try:
    import botocore
except ImportError:
    pass

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3
from ansible_collections.amazon.aws.plugins.module_utils.iam import AnsibleIAMError
from ansible_collections.amazon.aws.plugins.module_utils.iam import IAMErrorHandler

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_iam_error_handler.py requires the python modules 'boto3' and 'botocore'")


class TestIamDeletionHandler:
    def test_no_failures(self):
        self.counter = 0

        @IAMErrorHandler.deletion_error_handler("no error")
        def no_failures():
            self.counter += 1

        no_failures()
        assert self.counter == 1

    def test_client_error(self):
        self.counter = 0
        err_response = {"Error": {"Code": "MalformedPolicyDocument"}}

        @IAMErrorHandler.deletion_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleIAMError) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "do something" in raised.message
        assert "Something bad" in str(raised.exception)

    def test_ignore_error(self):
        self.counter = 0
        err_response = {"Error": {"Code": "NoSuchEntity"}}

        @IAMErrorHandler.deletion_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "I couldn't find it")

        ret_val = raise_client_error()
        assert self.counter == 1
        assert ret_val is False


class TestIamListHandler:
    def test_no_failures(self):
        self.counter = 0

        @IAMErrorHandler.list_error_handler("no error")
        def no_failures():
            self.counter += 1

        no_failures()
        assert self.counter == 1

    def test_client_error(self):
        self.counter = 0
        err_response = {"Error": {"Code": "MalformedPolicyDocument"}}

        @IAMErrorHandler.list_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleIAMError) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "do something" in raised.message
        assert "Something bad" in str(raised.exception)

    def test_list_error(self):
        self.counter = 0
        err_response = {"Error": {"Code": "NoSuchEntity"}}

        @IAMErrorHandler.list_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "I couldn't find it")

        ret_val = raise_client_error()
        assert self.counter == 1
        assert ret_val is None


class TestIamCommonHandler:
    def test_no_failures(self):
        self.counter = 0

        @IAMErrorHandler.common_error_handler("no error")
        def no_failures():
            self.counter += 1

        no_failures()
        assert self.counter == 1

    def test_client_error(self):
        self.counter = 0
        err_response = {"Error": {"Code": "MalformedPolicyDocument"}}

        @IAMErrorHandler.common_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleIAMError) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "do something" in raised.message
        assert "Something bad" in str(raised.exception)
