# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

import ansible_collections.amazon.aws.plugins.module_utils.cloud as cloud_utils
from ansible_collections.amazon.aws.tests.unit.compat.mock import MagicMock
from ansible_collections.amazon.aws.tests.unit.compat.mock import sentinel


class TestRetryFunc:

    class ExceptionA(Exception):
        def __init__(self):
            pass

    class ExceptionB(Exception):
        def __init__(self):
            pass

    def setup_method(self):
        self.sleep_generator = cloud_utils.BackoffIterator(0, 0)
        self.test_function = MagicMock()
        self.test_function.return_value = sentinel.successful_run
        self.found_function = MagicMock()
        self.found_function.return_value = False
        self.extract_code = MagicMock()
        self.extract_code.return_value = sentinel.extracted_code

        self.common_params = [self.test_function, self.sleep_generator, 4, None,
                              self.found_function, self.extract_code, TestRetryFunc.ExceptionA]

    def test_success(self):
        result = cloud_utils._retry_func(*self.common_params)
        assert result is sentinel.successful_run
        assert self.test_function.called is True
        assert self.test_function.call_count == 1

    def test_not_base(self):
        self.test_function.side_effect = TestRetryFunc.ExceptionB()
        with pytest.raises(TestRetryFunc.ExceptionB):
            cloud_utils._retry_func(*self.common_params)
        assert self.test_function.called is True
        assert self.test_function.call_count == 1

    def test_no_match(self):
        self.found_function.return_value = False
        self.test_function.side_effect = TestRetryFunc.ExceptionA()

        with pytest.raises(TestRetryFunc.ExceptionA):
            cloud_utils._retry_func(*self.common_params)
        assert self.test_function.called is True
        assert self.test_function.call_count == 1
        assert self.found_function.called is True
        assert self.found_function.call_count == 1
        assert self.found_function.call_args.args[0] is sentinel.extracted_code
        assert self.found_function.call_args.args[1] is None

        self.test_function.reset_mock()
        self.found_function.reset_mock()

        self.common_params[3] = sentinel.extra_codes

        with pytest.raises(TestRetryFunc.ExceptionA):
            cloud_utils._retry_func(*self.common_params)
        assert self.test_function.called is True
        assert self.test_function.call_count == 1
        assert self.found_function.called is True
        assert self.found_function.call_count == 1
        assert self.found_function.call_args.args[0] is sentinel.extracted_code
        assert self.found_function.call_args.args[1] is sentinel.extra_codes

    def test_simple_retries(self):
        self.found_function.return_value = True
        self.test_function.side_effect = TestRetryFunc.ExceptionA()

        with pytest.raises(TestRetryFunc.ExceptionA):
            cloud_utils._retry_func(*self.common_params)
        assert self.test_function.called is True
        assert self.test_function.call_count == 4

        self.test_function.reset_mock()
        self.common_params[2] = 2

        with pytest.raises(TestRetryFunc.ExceptionA):
            cloud_utils._retry_func(*self.common_params)
        assert self.test_function.called is True
        assert self.test_function.call_count == 2
