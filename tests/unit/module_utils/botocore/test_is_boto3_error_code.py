# -*- coding: utf-8 -*-
# (c) 2020 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

try:
    import botocore
except ImportError:
    # Handled by HAS_BOTO3
    pass

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_is_boto3_error_code.py requires the python modules 'boto3' and 'botocore'")


class TestIsBoto3ErrorCode():

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

    ###
    # Test that is_boto3_error_code does what's expected when used in a try/except block
    # (where we don't explicitly pass an exception to the function)
    ###

    def _do_try_code(self, exception, codes):
        try:
            raise exception
        except is_boto3_error_code(codes) as e:
            return e

    def test_is_boto3_error_code_single__raise__client(self):
        # 'AccessDenied' error, should be caught in our try/except in _do_try_code
        thrown_exception = self._make_denied_exception()
        codes_to_catch = 'AccessDenied'

        caught_exception = self._do_try_code(thrown_exception, codes_to_catch)
        assert caught_exception == thrown_exception

    def test_is_boto3_error_code_single__raise__unexpected(self):
        # 'SomeThingWentWrong' error, shouldn't be caught because the Code doesn't match
        thrown_exception = self._make_unexpected_exception()
        codes_to_catch = 'AccessDenied'

        with pytest.raises(botocore.exceptions.ClientError) as context:
            self._do_try_code(thrown_exception, codes_to_catch)
        assert context.value == thrown_exception

    def test_is_boto3_error_code_single__raise__botocore(self):
        # BotoCoreExceptions don't have an error code, so shouldn't be caught (and shouldn't throw
        # some other error due to the missing 'Code' data on the exception)
        thrown_exception = self._make_botocore_exception()
        codes_to_catch = 'AccessDenied'

        with pytest.raises(botocore.exceptions.BotoCoreError) as context:
            self._do_try_code(thrown_exception, codes_to_catch)

        assert context.value == thrown_exception

    def test_is_boto3_error_code_multiple__raise__client(self):
        # 'AccessDenied' error, should be caught in our try/except in _do_try_code
        # test with multiple possible codes to catch
        thrown_exception = self._make_denied_exception()
        codes_to_catch = ['AccessDenied', 'NotAccessDenied']

        caught_exception = self._do_try_code(thrown_exception, codes_to_catch)
        assert caught_exception == thrown_exception

        thrown_exception = self._make_denied_exception()
        codes_to_catch = ['NotAccessDenied', 'AccessDenied']

        caught_exception = self._do_try_code(thrown_exception, codes_to_catch)
        assert caught_exception == thrown_exception

    def test_is_boto3_error_code_multiple__raise__unexpected(self):
        # 'SomeThingWentWrong' error, shouldn't be caught because the Code doesn't match
        # test with multiple possible codes to catch
        thrown_exception = self._make_unexpected_exception()
        codes_to_catch = ['NotAccessDenied', 'AccessDenied']

        with pytest.raises(botocore.exceptions.ClientError) as context:
            self._do_try_code(thrown_exception, codes_to_catch)
        assert context.value == thrown_exception

    def test_is_boto3_error_code_multiple__raise__botocore(self):
        # BotoCoreErrors don't have an error code, so shouldn't be caught (and shouldn't throw
        # some other error due to the missing 'Code' data on the exception)
        # test with multiple possible codes to catch
        thrown_exception = self._make_botocore_exception()
        codes_to_catch = ['NotAccessDenied', 'AccessDenied']

        with pytest.raises(botocore.exceptions.BotoCoreError) as context:
            self._do_try_code(thrown_exception, codes_to_catch)
        assert context.value == thrown_exception

    ###
    # Test that is_boto3_error_code returns what we expect when explicitly passed an exception
    ###

    def test_is_boto3_error_code_single__pass__client(self):
        passed_exception = self._make_denied_exception()
        returned_exception = is_boto3_error_code('AccessDenied', e=passed_exception)
        assert isinstance(passed_exception, returned_exception)
        assert issubclass(returned_exception, botocore.exceptions.ClientError)
        assert not issubclass(returned_exception, botocore.exceptions.BotoCoreError)
        assert issubclass(returned_exception, Exception)
        assert returned_exception.__name__ != "NeverEverRaisedException"

    def test_is_boto3_error_code_single__pass__unexpected(self):
        passed_exception = self._make_unexpected_exception()
        returned_exception = is_boto3_error_code('AccessDenied', e=passed_exception)
        assert not isinstance(passed_exception, returned_exception)
        assert not issubclass(returned_exception, botocore.exceptions.ClientError)
        assert not issubclass(returned_exception, botocore.exceptions.BotoCoreError)
        assert issubclass(returned_exception, Exception)
        assert returned_exception.__name__ == "NeverEverRaisedException"

    def test_is_boto3_error_code_single__pass__botocore(self):
        passed_exception = self._make_botocore_exception()
        returned_exception = is_boto3_error_code('AccessDenied', e=passed_exception)
        assert not isinstance(passed_exception, returned_exception)
        assert not issubclass(returned_exception, botocore.exceptions.ClientError)
        assert not issubclass(returned_exception, botocore.exceptions.BotoCoreError)
        assert issubclass(returned_exception, Exception)
        assert returned_exception.__name__ == "NeverEverRaisedException"

    def test_is_boto3_error_code_multiple__pass__client(self):
        passed_exception = self._make_denied_exception()
        returned_exception = is_boto3_error_code(['NotAccessDenied', 'AccessDenied'], e=passed_exception)
        assert isinstance(passed_exception, returned_exception)
        assert issubclass(returned_exception, botocore.exceptions.ClientError)
        assert not issubclass(returned_exception, botocore.exceptions.BotoCoreError)
        assert issubclass(returned_exception, Exception)
        assert returned_exception.__name__ != "NeverEverRaisedException"

        returned_exception = is_boto3_error_code(['AccessDenied', 'NotAccessDenied'], e=passed_exception)
        assert isinstance(passed_exception, returned_exception)
        assert issubclass(returned_exception, botocore.exceptions.ClientError)
        assert not issubclass(returned_exception, botocore.exceptions.BotoCoreError)
        assert issubclass(returned_exception, Exception)
        assert returned_exception.__name__ != "NeverEverRaisedException"

    def test_is_boto3_error_code_multiple__pass__unexpected(self):
        passed_exception = self._make_unexpected_exception()
        returned_exception = is_boto3_error_code(['NotAccessDenied', 'AccessDenied'], e=passed_exception)
        assert not isinstance(passed_exception, returned_exception)
        assert not issubclass(returned_exception, botocore.exceptions.ClientError)
        assert not issubclass(returned_exception, botocore.exceptions.BotoCoreError)
        assert issubclass(returned_exception, Exception)
        assert returned_exception.__name__ == "NeverEverRaisedException"

    def test_is_boto3_error_code_multiple__pass__botocore(self):
        passed_exception = self._make_botocore_exception()
        returned_exception = is_boto3_error_code(['NotAccessDenied', 'AccessDenied'], e=passed_exception)
        assert not isinstance(passed_exception, returned_exception)
        assert not issubclass(returned_exception, botocore.exceptions.ClientError)
        assert not issubclass(returned_exception, botocore.exceptions.BotoCoreError)
        assert issubclass(returned_exception, Exception)
        assert returned_exception.__name__ == "NeverEverRaisedException"
