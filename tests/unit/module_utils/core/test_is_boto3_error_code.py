# -*- coding: utf-8 -*-
# (c) 2020 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import botocore

from ansible_collections.amazon.aws.tests.unit.compat import unittest

from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import HAS_BOTO3

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_iam.py requires the python modules 'boto3' and 'botocore'")


class Boto3ErrorCodeTestSuite(unittest.TestCase):

    def _make_denied_exception(self):
        return botocore.exceptions.ClientError(
            {
                "Error": {
                    "Code": "AccessDenied",
                    "Message": "User: arn:aws:iam::123456789012:user/ExampleUser "
                               + "is not authorized to perform: iam:GetUser on resource: user ExampleUser"
                },
                "ResponseMetadata": {
                    "RequestId": "01234567-89ab-cdef-0123-456789abcdef"
                }
            }, 'getUser')

    def _make_unexpected_exception(self):
        return botocore.exceptions.ClientError(
            {
                "Error": {
                    "Code": "SomeThingWentWrong",
                    "Message": "Boom!"
                },
                "ResponseMetadata": {
                    "RequestId": "01234567-89ab-cdef-0123-456789abcdef"
                }
            }, 'someCall')

    def _make_encoded_exception(self):
        return botocore.exceptions.ClientError(
            {
                "Error": {
                    "Code": "PermissionDenied",
                    "Message": "You are not authorized to perform this operation. Encoded authorization failure message: " +
                               "fEwXX6llx3cClm9J4pURgz1XPnJPrYexEbrJcLhFkwygMdOgx_-aEsj0LqRM6Kxt2HVI6prUhDwbJqBo9U2V7iRKZ" +
                               "T6ZdJvHH02cXmD0Jwl5vrTsf0PhBcWYlH5wl2qME7xTfdolEUr4CzumCiti7ETiO-RDdHqWlasBOW5bWsZ4GSpPdU" +
                               "06YAX0TfwVBs48uU5RpCHfz1uhSzez-3elbtp9CmTOHLt5pzJodiovccO55BQKYLPtmJcs6S9YLEEogmpI4Cb1D26" +
                               "fYahDh51jEmaohPnW5pb1nQe2yPEtuIhtRzNjhFCOOMwY5DBzNsymK-Gj6eJLm7FSGHee4AHLU_XmZMe_6bcLAiOx" +
                               "6Zdl65Kdd0hLcpwVxyZMi27HnYjAdqRlV3wuCW2PkhAW14qZQLfiuHZDEwnPe2PBGSlFcCmkQvJvX-YLoA7Uyc2wf" +
                               "NX5RJm38STwfiJSkQaNDhHKTWKiLOsgY4Gze6uZoG7zOcFXFRyaA4cbMmI76uyBO7j-9uQUCtBYqYto8x_9CUJcxI" +
                               "VC5SPG_C1mk-WoDMew01f0qy-bNaCgmJ9TOQGd08FyuT1SaMpCC0gX6mHuOnEgkFw3veBIowMpp9XcM-yc42fmIOp" +
                               "FOdvQO6uE9p55Qc-uXvsDTTvT3A7EeFU8a_YoAIt9UgNYM6VTvoprLz7dBI_P6C-bdPPZCY2amm-dJNVZelT6TbJB" +
                               "H_Vxh0fzeiSUBersy_QzB0moc-vPWgnB-IkgnYLV-4L3K0L2"
                },
                "ResponseMetadata": {
                    "RequestId": "01234567-89ab-cdef-0123-456789abcdef"
                }
            }, 'someCall')

    def _make_botocore_exception(self):
        return botocore.exceptions.EndpointConnectionError(endpoint_url='junk.endpoint')

    def setUp(self):
        pass

    def test_is_boto3_error_code_single__raise__client(self):
        thrown_exception = self._make_denied_exception()
        caught_exception = None
        try:
            raise thrown_exception
        except is_boto3_error_code('AccessDenied') as e:
            caught_exception = e
            caught = 'Code'
        except botocore.exceptions.ClientError as e:  # pylint: disable=duplicate-except
            caught_exception = e
            caught = 'ClientError'
        except botocore.exceptions.BotoCoreError as e:
            caught_exception = e
            caught = 'BotoCoreError'
        except Exception as e:
            caught_exception = e
            caught = 'Exception'
        self.assertEqual(caught_exception, thrown_exception)
        self.assertEqual(caught, 'Code')

    def test_is_boto3_error_code_single__raise__unexpected(self):
        thrown_exception = self._make_unexpected_exception()
        caught_exception = None
        try:
            raise thrown_exception
        except is_boto3_error_code('AccessDenied') as e:
            caught_exception = e
            caught = 'Code'
        except botocore.exceptions.ClientError as e:  # pylint: disable=duplicate-except
            caught_exception = e
            caught = 'ClientError'
        except botocore.exceptions.BotoCoreError as e:
            caught_exception = e
            caught = 'BotoCoreError'
        except Exception as e:
            caught_exception = e
            caught = 'Exception'
        self.assertEqual(caught_exception, thrown_exception)
        self.assertEqual(caught, 'ClientError')

    def test_is_boto3_error_code_single__raise__botocore(self):
        thrown_exception = self._make_botocore_exception()
        caught_exception = None
        try:
            raise thrown_exception
        except is_boto3_error_code('AccessDenied') as e:
            caught_exception = e
            caught = 'Code'
        except botocore.exceptions.ClientError as e:  # pylint: disable=duplicate-except
            caught_exception = e
            caught = 'ClientError'
        except botocore.exceptions.BotoCoreError as e:
            caught_exception = e
            caught = 'BotoCoreError'
        except Exception as e:
            caught_exception = e
            caught = 'Exception'
        self.assertEqual(caught_exception, thrown_exception)
        self.assertEqual(caught, 'BotoCoreError')

    def test_is_boto3_error_code_multiple__raise__client(self):
        thrown_exception = self._make_denied_exception()
        caught_exception = None
        try:
            raise thrown_exception
        except is_boto3_error_code(['NotAccessDenied', 'AccessDenied']) as e:
            caught_exception = e
            caught = 'Code'
        except botocore.exceptions.ClientError as e:  # pylint: disable=duplicate-except
            caught_exception = e
            caught = 'ClientError'
        except botocore.exceptions.BotoCoreError as e:
            caught_exception = e
            caught = 'BotoCoreError'
        except Exception as e:
            caught_exception = e
            caught = 'Exception'
        self.assertEqual(caught_exception, thrown_exception)
        self.assertEqual(caught, 'Code')
        caught_exception = None
        try:
            raise thrown_exception
        except is_boto3_error_code(['AccessDenied', 'NotAccessDenied']) as e:
            caught_exception = e
            caught = 'Code'
        except botocore.exceptions.ClientError as e:  # pylint: disable=duplicate-except
            caught_exception = e
            caught = 'ClientError'
        except botocore.exceptions.BotoCoreError as e:
            caught_exception = e
            caught = 'BotoCoreError'
        except Exception as e:
            caught_exception = e
            caught = 'Exception'
        self.assertEqual(caught_exception, thrown_exception)
        self.assertEqual(caught, 'Code')

    def test_is_boto3_error_code_multiple__raise__unexpected(self):
        thrown_exception = self._make_unexpected_exception()
        caught_exception = None
        try:
            raise thrown_exception
        except is_boto3_error_code(['NotAccessDenied', 'AccessDenied']) as e:
            caught_exception = e
            caught = 'Code'
        except botocore.exceptions.ClientError as e:  # pylint: disable=duplicate-except
            caught_exception = e
            caught = 'ClientError'
        except botocore.exceptions.BotoCoreError as e:
            caught_exception = e
            caught = 'BotoCoreError'
        except Exception as e:
            caught_exception = e
            caught = 'Exception'
        self.assertEqual(caught_exception, thrown_exception)
        self.assertEqual(caught, 'ClientError')

    def test_is_boto3_error_code_multiple__raise__botocore(self):
        thrown_exception = self._make_botocore_exception()
        caught_exception = None
        try:
            raise thrown_exception
        except is_boto3_error_code(['NotAccessDenied', 'AccessDenied']) as e:
            caught_exception = e
            caught = 'Code'
        except botocore.exceptions.ClientError as e:  # pylint: disable=duplicate-except
            caught_exception = e
            caught = 'ClientError'
        except botocore.exceptions.BotoCoreError as e:
            caught_exception = e
            caught = 'BotoCoreError'
        except Exception as e:
            caught_exception = e
            caught = 'Exception'
        self.assertEqual(caught_exception, thrown_exception)
        self.assertEqual(caught, 'BotoCoreError')

    def test_is_boto3_error_code_single__pass__client(self):
        passed_exception = self._make_denied_exception()
        returned_exception = is_boto3_error_code('AccessDenied', e=passed_exception)
        self.assertTrue(isinstance(passed_exception, returned_exception))
        self.assertTrue(issubclass(returned_exception, botocore.exceptions.ClientError))
        self.assertFalse(issubclass(returned_exception, botocore.exceptions.BotoCoreError))
        self.assertTrue(issubclass(returned_exception, Exception))
        self.assertNotEqual(returned_exception.__name__, "NeverEverRaisedException")

    def test_is_boto3_error_code_single__pass__unexpected(self):
        passed_exception = self._make_unexpected_exception()
        returned_exception = is_boto3_error_code('AccessDenied', e=passed_exception)
        self.assertFalse(isinstance(passed_exception, returned_exception))
        self.assertFalse(issubclass(returned_exception, botocore.exceptions.ClientError))
        self.assertFalse(issubclass(returned_exception, botocore.exceptions.BotoCoreError))
        self.assertTrue(issubclass(returned_exception, Exception))
        self.assertEqual(returned_exception.__name__, "NeverEverRaisedException")

    def test_is_boto3_error_code_single__pass__botocore(self):
        passed_exception = self._make_botocore_exception()
        returned_exception = is_boto3_error_code('AccessDenied', e=passed_exception)
        self.assertFalse(isinstance(passed_exception, returned_exception))
        self.assertFalse(issubclass(returned_exception, botocore.exceptions.ClientError))
        self.assertFalse(issubclass(returned_exception, botocore.exceptions.BotoCoreError))
        self.assertTrue(issubclass(returned_exception, Exception))
        self.assertEqual(returned_exception.__name__, "NeverEverRaisedException")

    def test_is_boto3_error_code_multiple__pass__client(self):
        passed_exception = self._make_denied_exception()
        returned_exception = is_boto3_error_code(['NotAccessDenied', 'AccessDenied'], e=passed_exception)
        self.assertTrue(isinstance(passed_exception, returned_exception))
        self.assertTrue(issubclass(returned_exception, botocore.exceptions.ClientError))
        self.assertFalse(issubclass(returned_exception, botocore.exceptions.BotoCoreError))
        self.assertTrue(issubclass(returned_exception, Exception))
        self.assertNotEqual(returned_exception.__name__, "NeverEverRaisedException")
        returned_exception = is_boto3_error_code(['AccessDenied', 'NotAccessDenied'], e=passed_exception)
        self.assertTrue(isinstance(passed_exception, returned_exception))
        self.assertTrue(issubclass(returned_exception, botocore.exceptions.ClientError))
        self.assertFalse(issubclass(returned_exception, botocore.exceptions.BotoCoreError))
        self.assertTrue(issubclass(returned_exception, Exception))
        self.assertNotEqual(returned_exception.__name__, "NeverEverRaisedException")

    def test_is_boto3_error_code_multiple__pass__unexpected(self):
        passed_exception = self._make_unexpected_exception()
        returned_exception = is_boto3_error_code(['NotAccessDenied', 'AccessDenied'], e=passed_exception)
        self.assertFalse(isinstance(passed_exception, returned_exception))
        self.assertFalse(issubclass(returned_exception, botocore.exceptions.ClientError))
        self.assertFalse(issubclass(returned_exception, botocore.exceptions.BotoCoreError))
        self.assertTrue(issubclass(returned_exception, Exception))
        self.assertEqual(returned_exception.__name__, "NeverEverRaisedException")

    def test_is_boto3_error_code_multiple__pass__botocore(self):
        passed_exception = self._make_botocore_exception()
        returned_exception = is_boto3_error_code(['NotAccessDenied', 'AccessDenied'], e=passed_exception)
        self.assertFalse(isinstance(passed_exception, returned_exception))
        self.assertFalse(issubclass(returned_exception, botocore.exceptions.ClientError))
        self.assertFalse(issubclass(returned_exception, botocore.exceptions.BotoCoreError))
        self.assertTrue(issubclass(returned_exception, Exception))
        self.assertEqual(returned_exception.__name__, "NeverEverRaisedException")
