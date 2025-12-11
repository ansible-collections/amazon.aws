# -*- coding: utf-8 -*-
# Copyright: Contributors to the Ansible project
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

try:
    import botocore
except ImportError:
    # Handled by HAS_BOTO3
    pass

from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_httpstatus

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip(
        "test_is_boto3_error_httpstatus.py requires the python modules 'boto3' and 'botocore'"
    )


class TestIsBoto3ErrorHttpStatus:
    def _make_403_exception(self):
        return botocore.exceptions.ClientError(
            {
                "Error": {
                    "Code": "AccessDenied",
                    "Message": (
                        "User: arn:aws:iam::123456789012:user/ExampleUser "
                        + "is not authorized to perform: iam:GetUser on resource: user ExampleUser"
                    ),
                },
                "ResponseMetadata": {
                    "RequestId": "01234567-89ab-cdef-0123-456789abcdef",
                    "HTTPStatusCode": 403,
                },
            },
            "getUser",
        )

    def _make_404_exception(self):
        return botocore.exceptions.ClientError(
            {
                "Error": {"Code": "NoSuchEntity", "Message": "The user with name ExampleUser cannot be found."},
                "ResponseMetadata": {
                    "RequestId": "01234567-89ab-cdef-0123-456789abcdef",
                    "HTTPStatusCode": 404,
                },
            },
            "getUser",
        )

    def _make_500_exception(self):
        return botocore.exceptions.ClientError(
            {
                "Error": {"Code": "InternalError", "Message": "An internal error occurred."},
                "ResponseMetadata": {
                    "RequestId": "01234567-89ab-cdef-0123-456789abcdef",
                    "HTTPStatusCode": 500,
                },
            },
            "someCall",
        )

    def _make_botocore_exception(self):
        return botocore.exceptions.EndpointConnectionError(endpoint_url="junk.endpoint")

    ###
    # Test that is_boto3_error_httpstatus does what's expected when used in a try/except block
    # (where we don't explicitly pass an exception to the function)
    ###

    def _do_try_status(self, exception, statuses):
        try:
            raise exception
        except is_boto3_error_httpstatus(statuses) as e:
            return e

    def test_is_boto3_error_httpstatus_single__raise__client(self):
        # 403 error, should be caught in our try/except in _do_try_status
        thrown_exception = self._make_403_exception()
        statuses_to_catch = 403

        caught_exception = self._do_try_status(thrown_exception, statuses_to_catch)
        assert caught_exception == thrown_exception

    def test_is_boto3_error_httpstatus_single__raise__unexpected(self):
        # 500 error, shouldn't be caught because the status code doesn't match
        thrown_exception = self._make_500_exception()
        statuses_to_catch = 403

        with pytest.raises(botocore.exceptions.ClientError) as context:
            self._do_try_status(thrown_exception, statuses_to_catch)
        assert context.value == thrown_exception

    def test_is_boto3_error_httpstatus_single__raise__botocore(self):
        # BotoCoreExceptions don't have an HTTP status code, so shouldn't be caught (and shouldn't throw
        # some other error due to the missing 'HTTPStatusCode' data on the exception)
        thrown_exception = self._make_botocore_exception()
        statuses_to_catch = 403

        with pytest.raises(botocore.exceptions.BotoCoreError) as context:
            self._do_try_status(thrown_exception, statuses_to_catch)

        assert context.value == thrown_exception

    def test_is_boto3_error_httpstatus_multiple__raise__client(self):
        # 403 error, should be caught in our try/except in _do_try_status
        # test with multiple possible status codes to catch
        thrown_exception = self._make_403_exception()
        statuses_to_catch = [403, 404]

        caught_exception = self._do_try_status(thrown_exception, statuses_to_catch)
        assert caught_exception == thrown_exception

        thrown_exception = self._make_403_exception()
        statuses_to_catch = [404, 403]

        caught_exception = self._do_try_status(thrown_exception, statuses_to_catch)
        assert caught_exception == thrown_exception

    def test_is_boto3_error_httpstatus_multiple__raise__unexpected(self):
        # 500 error, shouldn't be caught because the status code doesn't match
        # test with multiple possible status codes to catch
        thrown_exception = self._make_500_exception()
        statuses_to_catch = [403, 404]

        with pytest.raises(botocore.exceptions.ClientError) as context:
            self._do_try_status(thrown_exception, statuses_to_catch)
        assert context.value == thrown_exception

    def test_is_boto3_error_httpstatus_multiple__raise__botocore(self):
        # BotoCoreErrors don't have an HTTP status code, so shouldn't be caught (and shouldn't throw
        # some other error due to the missing 'HTTPStatusCode' data on the exception)
        # test with multiple possible status codes to catch
        thrown_exception = self._make_botocore_exception()
        statuses_to_catch = [403, 404]

        with pytest.raises(botocore.exceptions.BotoCoreError) as context:
            self._do_try_status(thrown_exception, statuses_to_catch)
        assert context.value == thrown_exception

    ###
    # Test that is_boto3_error_httpstatus returns what we expect when explicitly passed an exception
    ###

    def test_is_boto3_error_httpstatus_single__pass__client(self):
        passed_exception = self._make_403_exception()
        returned_exception = is_boto3_error_httpstatus(403, e=passed_exception)
        assert isinstance(passed_exception, returned_exception)
        assert issubclass(returned_exception, botocore.exceptions.ClientError)
        assert not issubclass(returned_exception, botocore.exceptions.BotoCoreError)
        assert issubclass(returned_exception, Exception)
        assert returned_exception.__name__ != "NeverEverRaisedException"

    def test_is_boto3_error_httpstatus_single__pass__unexpected(self):
        passed_exception = self._make_500_exception()
        returned_exception = is_boto3_error_httpstatus(403, e=passed_exception)
        assert not isinstance(passed_exception, returned_exception)
        assert not issubclass(returned_exception, botocore.exceptions.ClientError)
        assert not issubclass(returned_exception, botocore.exceptions.BotoCoreError)
        assert issubclass(returned_exception, Exception)
        assert returned_exception.__name__ == "NeverEverRaisedException"

    def test_is_boto3_error_httpstatus_single__pass__botocore(self):
        passed_exception = self._make_botocore_exception()
        returned_exception = is_boto3_error_httpstatus(403, e=passed_exception)
        assert not isinstance(passed_exception, returned_exception)
        assert not issubclass(returned_exception, botocore.exceptions.ClientError)
        assert not issubclass(returned_exception, botocore.exceptions.BotoCoreError)
        assert issubclass(returned_exception, Exception)
        assert returned_exception.__name__ == "NeverEverRaisedException"

    def test_is_boto3_error_httpstatus_multiple__pass__client(self):
        passed_exception = self._make_403_exception()
        returned_exception = is_boto3_error_httpstatus([404, 403], e=passed_exception)
        assert isinstance(passed_exception, returned_exception)
        assert issubclass(returned_exception, botocore.exceptions.ClientError)
        assert not issubclass(returned_exception, botocore.exceptions.BotoCoreError)
        assert issubclass(returned_exception, Exception)
        assert returned_exception.__name__ != "NeverEverRaisedException"

        returned_exception = is_boto3_error_httpstatus([403, 404], e=passed_exception)
        assert isinstance(passed_exception, returned_exception)
        assert issubclass(returned_exception, botocore.exceptions.ClientError)
        assert not issubclass(returned_exception, botocore.exceptions.BotoCoreError)
        assert issubclass(returned_exception, Exception)
        assert returned_exception.__name__ != "NeverEverRaisedException"

    def test_is_boto3_error_httpstatus_multiple__pass__unexpected(self):
        passed_exception = self._make_500_exception()
        returned_exception = is_boto3_error_httpstatus([404, 403], e=passed_exception)
        assert not isinstance(passed_exception, returned_exception)
        assert not issubclass(returned_exception, botocore.exceptions.ClientError)
        assert not issubclass(returned_exception, botocore.exceptions.BotoCoreError)
        assert issubclass(returned_exception, Exception)
        assert returned_exception.__name__ == "NeverEverRaisedException"

    def test_is_boto3_error_httpstatus_multiple__pass__botocore(self):
        passed_exception = self._make_botocore_exception()
        returned_exception = is_boto3_error_httpstatus([404, 403], e=passed_exception)
        assert not isinstance(passed_exception, returned_exception)
        assert not issubclass(returned_exception, botocore.exceptions.ClientError)
        assert not issubclass(returned_exception, botocore.exceptions.BotoCoreError)
        assert issubclass(returned_exception, Exception)
        assert returned_exception.__name__ == "NeverEverRaisedException"

    def test_is_boto3_error_httpstatus_tuple__pass__client(self):
        passed_exception = self._make_403_exception()
        returned_exception = is_boto3_error_httpstatus((404, 403), e=passed_exception)
        assert isinstance(passed_exception, returned_exception)
        assert issubclass(returned_exception, botocore.exceptions.ClientError)
        assert not issubclass(returned_exception, botocore.exceptions.BotoCoreError)
        assert issubclass(returned_exception, Exception)
        assert returned_exception.__name__ != "NeverEverRaisedException"

        returned_exception = is_boto3_error_httpstatus((403, 404), e=passed_exception)
        assert isinstance(passed_exception, returned_exception)
        assert issubclass(returned_exception, botocore.exceptions.ClientError)
        assert not issubclass(returned_exception, botocore.exceptions.BotoCoreError)
        assert issubclass(returned_exception, Exception)
        assert returned_exception.__name__ != "NeverEverRaisedException"

    def test_is_boto3_error_httpstatus_tuple__pass__unexpected(self):
        passed_exception = self._make_500_exception()
        returned_exception = is_boto3_error_httpstatus((404, 403), e=passed_exception)
        assert not isinstance(passed_exception, returned_exception)
        assert not issubclass(returned_exception, botocore.exceptions.ClientError)
        assert not issubclass(returned_exception, botocore.exceptions.BotoCoreError)
        assert issubclass(returned_exception, Exception)
        assert returned_exception.__name__ == "NeverEverRaisedException"

    def test_is_boto3_error_httpstatus_tuple__pass__botocore(self):
        passed_exception = self._make_botocore_exception()
        returned_exception = is_boto3_error_httpstatus((404, 403), e=passed_exception)
        assert not isinstance(passed_exception, returned_exception)
        assert not issubclass(returned_exception, botocore.exceptions.ClientError)
        assert not issubclass(returned_exception, botocore.exceptions.BotoCoreError)
        assert issubclass(returned_exception, Exception)
        assert returned_exception.__name__ == "NeverEverRaisedException"

    def test_is_boto3_error_httpstatus_set__pass__client(self):
        passed_exception = self._make_403_exception()
        returned_exception = is_boto3_error_httpstatus({404, 403}, e=passed_exception)
        assert isinstance(passed_exception, returned_exception)
        assert issubclass(returned_exception, botocore.exceptions.ClientError)
        assert not issubclass(returned_exception, botocore.exceptions.BotoCoreError)
        assert issubclass(returned_exception, Exception)
        assert returned_exception.__name__ != "NeverEverRaisedException"

        returned_exception = is_boto3_error_httpstatus({403, 404}, e=passed_exception)
        assert isinstance(passed_exception, returned_exception)
        assert issubclass(returned_exception, botocore.exceptions.ClientError)
        assert not issubclass(returned_exception, botocore.exceptions.BotoCoreError)
        assert issubclass(returned_exception, Exception)
        assert returned_exception.__name__ != "NeverEverRaisedException"

    def test_is_boto3_error_httpstatus_set__pass__unexpected(self):
        passed_exception = self._make_500_exception()
        returned_exception = is_boto3_error_httpstatus({404, 403}, e=passed_exception)
        assert not isinstance(passed_exception, returned_exception)
        assert not issubclass(returned_exception, botocore.exceptions.ClientError)
        assert not issubclass(returned_exception, botocore.exceptions.BotoCoreError)
        assert issubclass(returned_exception, Exception)
        assert returned_exception.__name__ == "NeverEverRaisedException"

    def test_is_boto3_error_httpstatus_set__pass__botocore(self):
        passed_exception = self._make_botocore_exception()
        returned_exception = is_boto3_error_httpstatus({404, 403}, e=passed_exception)
        assert not isinstance(passed_exception, returned_exception)
        assert not issubclass(returned_exception, botocore.exceptions.ClientError)
        assert not issubclass(returned_exception, botocore.exceptions.BotoCoreError)
        assert issubclass(returned_exception, Exception)
        assert returned_exception.__name__ == "NeverEverRaisedException"
