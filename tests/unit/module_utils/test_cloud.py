# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.amazon.aws.plugins.module_utils.cloud import CloudRetry, BackoffIterator
import unittest
import random
from datetime import datetime


def test_backoff_value_generator():
    max_delay = 60
    initial = 3
    backoff = 2

    min_sleep = initial
    counter = 0
    for sleep in BackoffIterator(delay=initial, backoff=backoff, max_delay=max_delay):
        if counter > 4:
            assert sleep == max_delay
        else:
            assert sleep == min_sleep
            min_sleep *= backoff
        counter += 1
        if counter == 10:
            break


def test_backoff_value_generator_with_jitter():
    max_delay = 60
    initial = 3
    backoff = 2

    min_sleep = initial
    counter = 0
    for sleep in BackoffIterator(delay=initial, backoff=backoff, max_delay=max_delay, jitter=True):
        if counter > 4:
            assert sleep <= max_delay
        else:
            assert sleep <= min_sleep
            min_sleep *= backoff
        counter += 1
        if counter == 10:
            break


class CloudRetryUtils(unittest.TestCase):

    error_codes = [400, 500, 600]
    custom_error_codes = [100, 200, 300]

    class TestException(Exception):
        """
        custom exception class for testing
        """
        def __init__(self, status):
            self.status = status

        def __str__(self):
            return "TestException with status: {0}".format(self.status)

    class UnitTestsRetry(CloudRetry):
        base_class = Exception

        @staticmethod
        def status_code_from_exception(error):
            return getattr(error, "status") if hasattr(error, "status") else None

    class CustomRetry(CloudRetry):
        base_class = Exception

        @staticmethod
        def status_code_from_exception(error):
            return error.status['response']['status']

        @staticmethod
        def found(response_code, catch_extra_error_codes=None):
            if catch_extra_error_codes:
                return response_code in catch_extra_error_codes + CloudRetryUtils.custom_error_codes
            else:
                return response_code in CloudRetryUtils.custom_error_codes

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
    # Setup some initial data that we can use within our tests
    # ========================================================
    def setUp(self):
        # nothing to do on setup stage
        pass

    # ========================================================
    #   retry exponential backoff
    # ========================================================
    def test_retry_exponential_backoff(self):

        @CloudRetryUtils.UnitTestsRetry.exponential_backoff(retries=3, delay=1, backoff=1.1, max_delay=3, catch_extra_error_codes=CloudRetryUtils.error_codes)
        def test_retry_func():
            if test_retry_func.counter < 2:
                test_retry_func.counter += 1
                raise self.TestException(status=random.choice(CloudRetryUtils.error_codes))
            else:
                return True

        test_retry_func.counter = 0
        ret = test_retry_func()
        assert ret is True

    def test_retry_exponential_backoff_with_unexpected_exception(self):
        unexpected_except = self.TestException(status=100)

        @CloudRetryUtils.UnitTestsRetry.exponential_backoff(retries=3, delay=1, backoff=1.1, max_delay=3, catch_extra_error_codes=CloudRetryUtils.error_codes)
        def test_retry_func():
            if test_retry_func.counter == 0:
                test_retry_func.counter += 1
                raise self.TestException(status=random.choice(CloudRetryUtils.error_codes))
            else:
                raise unexpected_except

        test_retry_func.counter = 0
        try:
            ret = test_retry_func()
        except self.TestException as exc:
            assert exc.status == unexpected_except.status

    # ========================================================
    #   retry jittered backoff
    # ========================================================
    def test_retry_jitter_backoff(self):
        @CloudRetryUtils.UnitTestsRetry.jittered_backoff(retries=3, delay=1, max_delay=3, catch_extra_error_codes=CloudRetryUtils.error_codes)
        def test_retry_func():
            if test_retry_func.counter < 2:
                test_retry_func.counter += 1
                raise self.TestException(status=random.choice(CloudRetryUtils.error_codes))
            else:
                return True

        test_retry_func.counter = 0
        ret = test_retry_func()
        assert ret is True

    def test_retry_jittered_backoff_with_unexpected_exception(self):
        unexpected_except = self.TestException(status=100)

        @CloudRetryUtils.UnitTestsRetry.jittered_backoff(retries=3, delay=1, max_delay=3, catch_extra_error_codes=CloudRetryUtils.error_codes)
        def test_retry_func():
            if test_retry_func.counter == 0:
                test_retry_func.counter += 1
                raise self.TestException(status=random.choice(CloudRetryUtils.error_codes))
            else:
                raise unexpected_except

        test_retry_func.counter = 0
        try:
            ret = test_retry_func()
        except self.TestException as exc:
            assert exc.status == unexpected_except.status

    # ========================================================
    #   retry with custom class
    # ========================================================
    def test_retry_exponential_backoff_custom_class(self):
        def build_response():
            return dict(response=dict(status=random.choice(CloudRetryUtils.custom_error_codes)))

        @self.CustomRetry.exponential_backoff(retries=3, delay=1, backoff=1.1, max_delay=3, catch_extra_error_codes=CloudRetryUtils.error_codes)
        def test_retry_func():
            if test_retry_func.counter < 2:
                test_retry_func.counter += 1
                raise self.TestException(build_response())
            else:
                return True

        test_retry_func.counter = 0

        ret = test_retry_func()
        assert ret is True

    # =============================================================
    #   Test wrapped function multiple times will restart the sleep
    # =============================================================
    def test_wrapped_function_called_several_times(self):
        @CloudRetryUtils.UnitTestsRetry.exponential_backoff(retries=2, delay=2, backoff=4, max_delay=100, catch_extra_error_codes=CloudRetryUtils.error_codes)
        def _fail():
            raise self.TestException(status=random.choice(CloudRetryUtils.error_codes))

        # run the method 3 times and assert that each it is retrying after 2secs
        # the elapsed execution time should be closed to 2sec
        for u in range(3):
            start = datetime.now()
            raised = False
            try:
                _fail()
            except self.TestException:
                raised = True
                duration = (datetime.now() - start).seconds
                assert duration == 2
            finally:
                assert raised

    def test_only_base_exception(self):
        def _fail_index():
            my_list = list()
            return my_list[5]

        def _fail_key():
            my_dict = dict()
            return my_dict['invalid_key']

        def _fail_exception():
            raise Exception('bang')

        key_retry_decorator = CloudRetryUtils.KeyRetry.exponential_backoff(retries=2, delay=2, backoff=4, max_delay=100)
        key_and_index_retry_decorator = CloudRetryUtils.KeyAndIndexRetry.exponential_backoff(retries=2, delay=2, backoff=4, max_delay=100)

        expectations = [
            [key_retry_decorator, _fail_exception, 0],
            [key_retry_decorator, _fail_index, 0],
            [key_retry_decorator, _fail_key, 2],
            [key_and_index_retry_decorator, _fail_exception, 0],
            [key_and_index_retry_decorator, _fail_index, 2],
            [key_and_index_retry_decorator, _fail_key, 2],
        ]

        for expection in expectations:
            decorator = expection[0]
            function = expection[1]
            duration = expection[2]

            start = datetime.now()
            raised = False
            try:
                decorator(function)()
            except Exception:
                raised = True
                _duration = (datetime.now() - start).seconds
                assert duration == _duration
            finally:
                assert raised
