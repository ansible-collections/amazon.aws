# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

try:
    import botocore
except ImportError:
    pass

from ansible_collections.amazon.aws.plugins.module_utils.autoscaling import AnsibleAutoScalingError
from ansible_collections.amazon.aws.plugins.module_utils.autoscaling import AutoScalingErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_iam_error_handler.py requires the python modules 'boto3' and 'botocore'")


class TestAutoScalingDeletionHandler:
    def test_no_failures(self):
        self.counter = 0

        @AutoScalingErrorHandler.deletion_error_handler("no error")
        def no_failures():
            self.counter += 1

        no_failures()
        assert self.counter == 1

    def test_client_error(self):
        self.counter = 0
        err_response = {"Error": {"Code": "MalformedPolicyDocument"}}

        @AutoScalingErrorHandler.deletion_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleAutoScalingError) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "do something" in raised.message
        assert "Something bad" in str(raised.exception)

    def test_ignore_error(self):
        self.counter = 0
        err_response = {"Error": {"Code": "NoSuchEntity"}}

        @AutoScalingErrorHandler.deletion_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "I couldn't find it")

        ret_val = raise_client_error()
        assert self.counter == 1
        assert ret_val is False


class TestIamListHandler:
    def test_no_failures(self):
        self.counter = 0

        @AutoScalingErrorHandler.list_error_handler("no error")
        def no_failures():
            self.counter += 1

        no_failures()
        assert self.counter == 1

    def test_client_error(self):
        self.counter = 0
        err_response = {"Error": {"Code": "MalformedPolicyDocument"}}

        @AutoScalingErrorHandler.list_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleAutoScalingError) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "do something" in raised.message
        assert "Something bad" in str(raised.exception)

    def test_list_error(self):
        self.counter = 0
        err_response = {"Error": {"Code": "NoSuchEntity"}}

        @AutoScalingErrorHandler.list_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "I couldn't find it")

        ret_val = raise_client_error()
        assert self.counter == 1
        assert ret_val is None


class TestIamCommonHandler:
    def test_no_failures(self):
        self.counter = 0

        @AutoScalingErrorHandler.common_error_handler("no error")
        def no_failures():
            self.counter += 1

        no_failures()
        assert self.counter == 1

    def test_client_error(self):
        self.counter = 0
        err_response = {"Error": {"Code": "MalformedPolicyDocument"}}

        @AutoScalingErrorHandler.common_error_handler("do something")
        def raise_client_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "Something bad")

        with pytest.raises(AnsibleAutoScalingError) as e_info:
            raise_client_error()
        assert self.counter == 1
        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "do something" in raised.message
        assert "Something bad" in str(raised.exception)
