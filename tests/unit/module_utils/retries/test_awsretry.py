# -*- coding: utf-8 -*-
# (c) 2015, Allen Sanabria <asanabria@linuxdynasty.org>
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

try:
    import botocore
except ImportError:
    pass

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_awsretry.py requires the python modules 'boto3' and 'botocore'")


class TestAWSRetry:
    def test_no_failures(self):
        self.counter = 0

        @AWSRetry.exponential_backoff(retries=2, delay=0.1)
        def no_failures():
            self.counter += 1

        no_failures()
        assert self.counter == 1

    def test_extend_boto3_failures(self):
        self.counter = 0
        err_response = {"Error": {"Code": "MalformedPolicyDocument"}}

        @AWSRetry.exponential_backoff(retries=2, delay=0.1, catch_extra_error_codes=["MalformedPolicyDocument"])
        def extend_failures():
            self.counter += 1
            if self.counter < 2:
                raise botocore.exceptions.ClientError(err_response, "You did something wrong.")
            else:
                return "success"

        result = extend_failures()
        assert result == "success"
        assert self.counter == 2

    def test_retry_once(self):
        self.counter = 0
        err_response = {"Error": {"Code": "InternalFailure"}}

        @AWSRetry.exponential_backoff(retries=2, delay=0.1)
        def retry_once():
            self.counter += 1
            if self.counter < 2:
                raise botocore.exceptions.ClientError(err_response, "Something went wrong!")
            else:
                return "success"

        result = retry_once()
        assert result == "success"
        assert self.counter == 2

    def test_reached_limit(self):
        self.counter = 0
        err_response = {"Error": {"Code": "RequestLimitExceeded"}}

        @AWSRetry.exponential_backoff(retries=4, delay=0.1)
        def fail():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "toooo fast!!")

        with pytest.raises(botocore.exceptions.ClientError) as context:
            fail()
        response = context.value.response
        assert response["Error"]["Code"] == "RequestLimitExceeded"
        assert self.counter == 4

    def test_unexpected_exception_does_not_retry(self):
        self.counter = 0
        err_response = {"Error": {"Code": "AuthFailure"}}

        @AWSRetry.exponential_backoff(retries=4, delay=0.1)
        def raise_unexpected_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_response, "unexpected error")

        with pytest.raises(botocore.exceptions.ClientError) as context:
            raise_unexpected_error()
        response = context.value.response
        assert response["Error"]["Code"] == "AuthFailure"
        assert self.counter == 1
