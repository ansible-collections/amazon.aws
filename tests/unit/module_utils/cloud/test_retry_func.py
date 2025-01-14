# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import sys
from unittest.mock import Mock
from unittest.mock import sentinel

import pytest

import ansible_collections.amazon.aws.plugins.module_utils.cloud as cloud_utils

if sys.version_info < (3, 8):
    pytest.skip(
        "accessing call_args.kwargs by keyword (instead of index) was introduced in Python 3.8", allow_module_level=True
    )


class ExceptionA(Exception):
    def __init__(self):
        pass


class ExceptionB(Exception):
    def __init__(self):
        pass


@pytest.fixture(name="retrier")
def fixture_retrier():
    def do_retry(
        func=None,
        sleep_generator=None,
        retries=4,
        catch_extra_error_codes=None,
        found_f=None,
        extract_code=None,
        base_class=None,
    ):
        if not func:
            func = Mock(return_value=sentinel.successful_run)
        if not sleep_generator:
            sleep_generator = cloud_utils.BackoffIterator(0, 0)
        if not found_f:
            found_f = Mock(return_value=False)
        if not extract_code:
            extract_code = Mock(return_value=sentinel.extracted_code)
        if not base_class:
            base_class = ExceptionA

        result = cloud_utils._retry_func(
            func,
            sleep_generator,
            retries,
            catch_extra_error_codes,
            found_f,
            extract_code,
            base_class,
        )
        return func, result

    return do_retry


def test_success(retrier):
    func, result = retrier()
    assert result is sentinel.successful_run
    assert func.called is True
    assert func.call_count == 1


def test_not_base(retrier):
    func = Mock(side_effect=ExceptionB)
    with pytest.raises(ExceptionB):
        _f, _result = retrier(func=func)
    assert func.called is True
    assert func.call_count == 1


def test_no_match(retrier):
    found_f = Mock(return_value=False)
    func = Mock(side_effect=ExceptionA)

    with pytest.raises(ExceptionA):
        _f, _result = retrier(func=func, found_f=found_f)
    assert func.called is True
    assert func.call_count == 1
    assert found_f.called is True
    assert found_f.call_count == 1
    assert found_f.call_args.args[0] is sentinel.extracted_code
    assert found_f.call_args.args[1] is None


def test_no_match_with_extra_error_codes(retrier):
    found_f = Mock(return_value=False)
    func = Mock(side_effect=ExceptionA)
    catch_extra_error_codes = sentinel.extra_codes

    with pytest.raises(ExceptionA):
        _f, _result = retrier(func=func, found_f=found_f, catch_extra_error_codes=catch_extra_error_codes)
    assert func.called is True
    assert func.call_count == 1
    assert found_f.called is True
    assert found_f.call_count == 1
    assert found_f.call_args.args[0] is sentinel.extracted_code
    assert found_f.call_args.args[1] is sentinel.extra_codes


def test_simple_retries_4_times(retrier):
    found_f = Mock(return_value=True)
    func = Mock(side_effect=ExceptionA)

    with pytest.raises(ExceptionA):
        _f, _result = retrier(func=func, found_f=found_f)
    assert func.called is True
    assert func.call_count == 4


def test_simple_retries_2_times(retrier):
    found_f = Mock(return_value=True)
    func = Mock(side_effect=ExceptionA)

    with pytest.raises(ExceptionA):
        _f, _result = retrier(func=func, found_f=found_f, retries=2)
    assert func.called is True
    assert func.call_count == 2
