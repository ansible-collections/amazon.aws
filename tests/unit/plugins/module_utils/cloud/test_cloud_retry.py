# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import random
from datetime import datetime

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.cloud import CloudRetry


class TestCloudRetry:
    error_codes = [400, 500, 600]
    custom_error_codes = [100, 200, 300]

    class OurTestException(Exception):
        """
        custom exception class for testing
        """

        def __init__(self, status):
            self.status = status

        def __str__(self):
            return f"TestException with status: {self.status}"

    class UnitTestsRetry(CloudRetry):
        base_class = Exception

        @staticmethod
        def status_code_from_exception(error):
            return getattr(error, "status") if hasattr(error, "status") else None

    class CustomRetry(CloudRetry):
        base_class = Exception

        @staticmethod
        def status_code_from_exception(error):
            return error.status["response"]["status"]

        @staticmethod
        def found(response_code, catch_extra_error_codes=None):
            if catch_extra_error_codes:
                return response_code in catch_extra_error_codes + TestCloudRetry.custom_error_codes
            else:
                return response_code in TestCloudRetry.custom_error_codes

    class KeyRetry(CloudRetry):
        base_class = KeyError

        @staticmethod
        def status_code_from_exception(error):
            return True

        @staticmethod
        def found(response_code, catch_extra_error_codes=None):
            return True

    class KeyAndIndexRetry(CloudRetry):
        base_class = (KeyError, IndexError)

        @staticmethod
        def status_code_from_exception(error):
            return True

        @staticmethod
        def found(response_code, catch_extra_error_codes=None):
            return True

    # ========================================================
    #   retry exponential backoff
    # ========================================================
    def test_retry_exponential_backoff(self):
        @TestCloudRetry.UnitTestsRetry.exponential_backoff(
            retries=3, delay=1, backoff=1.1, max_delay=3, catch_extra_error_codes=TestCloudRetry.error_codes
        )
        def test_retry_func():
            if test_retry_func.counter < 2:
                test_retry_func.counter += 1
                raise self.OurTestException(status=random.choice(TestCloudRetry.error_codes))
            else:
                return True

        test_retry_func.counter = 0
        ret = test_retry_func()
        assert ret is True

    def test_retry_exponential_backoff_with_unexpected_exception(self):
        unexpected_except = self.OurTestException(status=100)

        @TestCloudRetry.UnitTestsRetry.exponential_backoff(
            retries=3, delay=1, backoff=1.1, max_delay=3, catch_extra_error_codes=TestCloudRetry.error_codes
        )
        def test_retry_func():
            if test_retry_func.counter == 0:
                test_retry_func.counter += 1
                raise self.OurTestException(status=random.choice(TestCloudRetry.error_codes))
            else:
                raise unexpected_except

        test_retry_func.counter = 0
        with pytest.raises(self.OurTestException) as context:
            test_retry_func()

        assert context.value.status == unexpected_except.status

    # ========================================================
    #   retry jittered backoff
    # ========================================================
    def test_retry_jitter_backoff(self):
        @TestCloudRetry.UnitTestsRetry.jittered_backoff(
            retries=3, delay=1, max_delay=3, catch_extra_error_codes=TestCloudRetry.error_codes
        )
        def test_retry_func():
            if test_retry_func.counter < 2:
                test_retry_func.counter += 1
                raise self.OurTestException(status=random.choice(TestCloudRetry.error_codes))
            else:
                return True

        test_retry_func.counter = 0
        ret = test_retry_func()
        assert ret is True

    def test_retry_jittered_backoff_with_unexpected_exception(self):
        unexpected_except = self.OurTestException(status=100)

        @TestCloudRetry.UnitTestsRetry.jittered_backoff(
            retries=3, delay=1, max_delay=3, catch_extra_error_codes=TestCloudRetry.error_codes
        )
        def test_retry_func():
            if test_retry_func.counter == 0:
                test_retry_func.counter += 1
                raise self.OurTestException(status=random.choice(TestCloudRetry.error_codes))
            else:
                raise unexpected_except

        test_retry_func.counter = 0
        with pytest.raises(self.OurTestException) as context:
            test_retry_func()

        assert context.value.status == unexpected_except.status

    # ========================================================
    #   retry with custom class
    # ========================================================
    def test_retry_exponential_backoff_custom_class(self):
        def build_response():
            return dict(response=dict(status=random.choice(TestCloudRetry.custom_error_codes)))

        @self.CustomRetry.exponential_backoff(
            retries=3, delay=1, backoff=1.1, max_delay=3, catch_extra_error_codes=TestCloudRetry.error_codes
        )
        def test_retry_func():
            if test_retry_func.counter < 2:
                test_retry_func.counter += 1
                raise self.OurTestException(build_response())
            else:
                return True

        test_retry_func.counter = 0

        ret = test_retry_func()
        assert ret is True

    # =============================================================
    #   Test wrapped function multiple times will restart the sleep
    # =============================================================
    def test_wrapped_function_called_several_times(self):
        @TestCloudRetry.UnitTestsRetry.exponential_backoff(
            retries=2, delay=2, backoff=4, max_delay=100, catch_extra_error_codes=TestCloudRetry.error_codes
        )
        def _fail():
            raise self.OurTestException(status=random.choice(TestCloudRetry.error_codes))

        # run the method 3 times and assert that each it is retrying after 2secs
        # the elapsed execution time should be closed to 2sec
        for _i in range(3):
            start = datetime.now()
            with pytest.raises(self.OurTestException):
                _fail()
            duration = (datetime.now() - start).seconds
            assert duration == 2

    def test_only_base_exception(self):
        def _fail_index():
            my_list = list()
            return my_list[5]

        def _fail_key():
            my_dict = dict()
            return my_dict["invalid_key"]

        def _fail_exception():
            raise Exception("bang")

        key_retry_decorator = TestCloudRetry.KeyRetry.exponential_backoff(retries=2, delay=2, backoff=4, max_delay=100)
        key_and_index_retry_decorator = TestCloudRetry.KeyAndIndexRetry.exponential_backoff(
            retries=2, delay=2, backoff=4, max_delay=100
        )

        expectations = [
            [key_retry_decorator, _fail_exception, 0, Exception],
            [key_retry_decorator, _fail_index, 0, IndexError],
            [key_retry_decorator, _fail_key, 2, KeyError],
            [key_and_index_retry_decorator, _fail_exception, 0, Exception],
            [key_and_index_retry_decorator, _fail_index, 2, IndexError],
            [key_and_index_retry_decorator, _fail_key, 2, KeyError],
        ]

        for expectation in expectations:
            decorator = expectation[0]
            function = expectation[1]
            duration = expectation[2]
            exception = expectation[3]

            start = datetime.now()
            with pytest.raises(exception):
                decorator(function)()
            _duration = (datetime.now() - start).seconds
            assert duration == _duration
