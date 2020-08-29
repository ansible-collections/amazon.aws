# -*- coding: utf-8 -*-
# (c) 2020 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import boto3
import botocore

from ansible_collections.amazon.aws.tests.unit.compat import unittest
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code


class Boto3ErrorTestCase(unittest.TestCase):

    def setUp(self):
        # Basic information that ClientError needs to spawn off an error
        self.EXAMPLE_EXCEPTION_DATA = {
            "Error": {
                "Code": "InvalidParameterValue",
                "Message": "The filter 'exampleFilter' is invalid"
            },
            "ResponseMetadata": {
                "RequestId": "01234567-89ab-cdef-0123-456789abcdef",
                "HTTPStatusCode": 400,
                "HTTPHeaders": {
                    "transfer-encoding": "chunked",
                    "date": "Fri, 13 Nov 2020 00:00:00 GMT",
                    "connection": "close",
                    "server": "AmazonEC2"
                },
                "RetryAttempts": 0
            }
        }

    def test_client_error_match_single(self):
        error_caught = 0
        try:
            raise botocore.exceptions.ClientError(self.EXAMPLE_EXCEPTION_DATA, "testCall")
        except is_boto3_error_code('InvalidParameterValue'):
            error_caught = 1
        except botocore.exceptions.ClientError:  # pylint: disable=duplicate-except
            error_caught = 2
        except Exception:
            error_caught = 3
        assert error_caught == 1

        try:
            raise botocore.exceptions.ClientError(self.EXAMPLE_EXCEPTION_DATA, "testCall")
        except is_boto3_error_code('SomeError'):
            error_caught = 4
        except botocore.exceptions.ClientError:  # pylint: disable=duplicate-except
            error_caught = 5
        except Exception:
            error_caught = 6
        assert error_caught == 5

    def test_client_error_match_list(self):
        error_caught = 0
        try:
            raise botocore.exceptions.ClientError(self.EXAMPLE_EXCEPTION_DATA, "testCall")
        except is_boto3_error_code(['SomeError', 'InvalidParameterValue']):
            error_caught = 1
        except botocore.exceptions.ClientError:  # pylint: disable=duplicate-except
            error_caught = 2
        except Exception:
            error_caught = 3
        assert error_caught == 1

        try:
            raise botocore.exceptions.ClientError(self.EXAMPLE_EXCEPTION_DATA, "testCall")
        except is_boto3_error_code(['InvalidParameterValue', 'SomeError']):
            error_caught = 4
        except botocore.exceptions.ClientError:  # pylint: disable=duplicate-except
            error_caught = 5
        except Exception:
            error_caught = 6
        assert error_caught == 4

        try:
            raise botocore.exceptions.ClientError(self.EXAMPLE_EXCEPTION_DATA, "testCall")
        except is_boto3_error_code(['SomeError', 'AnotherError']):
            error_caught = 7
        except botocore.exceptions.ClientError:  # pylint: disable=duplicate-except
            error_caught = 8
        except Exception:
            error_caught = 9
        assert error_caught == 8

        try:
            raise botocore.exceptions.ClientError(self.EXAMPLE_EXCEPTION_DATA, "testCall")
        except is_boto3_error_code(['AnotherError', 'SomeError']):
            error_caught = 10
        except botocore.exceptions.ClientError:  # pylint: disable=duplicate-except
            error_caught = 11
        except Exception:
            error_caught = 12
        assert error_caught == 11

    def test_botocore_error(self):
        # Tests that we cope with a non-ClientError and don't match
        error_caught = 0
        try:
            raise botocore.exceptions.BotoCoreError()
        except is_boto3_error_code('InvalidParameterValue'):
            error_caught = 1
        except botocore.exceptions.BotoCoreError:
            error_caught = 2
        except Exception:
            error_caught = 3
        assert error_caught == 2

        try:
            raise botocore.exceptions.BotoCoreError()
        # This is the error *Message*, but we shouldn't catch it.
        except is_boto3_error_code('An unspecified error occurred'):
            error_caught = 4
        except botocore.exceptions.BotoCoreError:
            error_caught = 5
        except Exception:
            error_caught = 6
        assert error_caught == 5

    def test_botocore_error_list(self):
        error_caught = 0

        try:
            raise botocore.exceptions.BotoCoreError()
        except is_boto3_error_code(['An unspecified error occurred', 'InvalidParameterValue']):
            error_caught = 1
        except botocore.exceptions.BotoCoreError:
            error_caught = 2
        except Exception:
            error_caught = 3
        assert error_caught == 2

        try:
            raise botocore.exceptions.BotoCoreError()
        # This is the error *Message*, but we shouldn't catch it.
        except is_boto3_error_code(['InvalidParameterValue', 'An unspecified error occurred']):
            error_caught = 4
        except botocore.exceptions.BotoCoreError:
            error_caught = 5
        except Exception:
            error_caught = 6
        assert error_caught == 5
