# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest
import sys
from unittest.mock import MagicMock
from unittest.mock import sentinel

from ansible_collections.amazon.aws.plugins.module_utils.cloud import CloudRetry
from ansible_collections.amazon.aws.plugins.module_utils.cloud import BackoffIterator

if sys.version_info < (3, 8):
    pytest.skip(
        "accessing call_args.kwargs by keyword (instead of index) was introduced in Python 3.8", allow_module_level=True
    )


@pytest.fixture
def patch_cloud_retry(monkeypatch):
    """
    replaces CloudRetry.base_decorator with a MagicMock so that we can exercise the generation of
    the various "public" decorators.  We can then check that base_decorator was called as expected.
    Note: this doesn't test the operation of CloudRetry.base_decorator itself, but does make sure
    we can fully exercise the various wrapper functions built over the top of it.
    """

    def perform_patch():
        decorator_generator = MagicMock()
        decorator_generator.return_value = sentinel.decorator
        monkeypatch.setattr(CloudRetry, "base_decorator", decorator_generator)
        return CloudRetry, decorator_generator

    return perform_patch


def check_common_side_effects(decorator_generator):
    """
    By invoking CloudRetry.(exponential_backoff|jittered_backoff|backoff) we expect certain things
    to have happend, specifically CloudRetry.base_decorator should have been called *once* with a
    number of keyword arguments.
    "found" should be CloudRetry.found
    "status_code_from_exception"  should be CloudRetry.status_code_from_exception (this is replaced when the abstract class is realised)
    "sleep_time_generator" should be an instance of CloudRetry.BackoffIterator
    """

    assert decorator_generator.called is True
    assert decorator_generator.call_count == 1

    gen_kw_args = decorator_generator.call_args.kwargs
    assert gen_kw_args["found"] is CloudRetry.found
    assert gen_kw_args["status_code_from_exception"] is CloudRetry.status_code_from_exception

    sleep_time_generator = gen_kw_args["sleep_time_generator"]
    assert isinstance(sleep_time_generator, BackoffIterator)

    # Return the KW args used when CloudRetry.base_decorator was called and the sleep_time_generator
    # passed, these are what should change between the different decorators
    return gen_kw_args, sleep_time_generator


def test_create_exponential_backoff_with_defaults(patch_cloud_retry):
    cloud_retry, decorator_generator = patch_cloud_retry()

    decorator = cloud_retry.exponential_backoff()

    assert decorator is sentinel.decorator

    gen_kw_args, sleep_time_generator = check_common_side_effects(decorator_generator)

    assert gen_kw_args["retries"] == 10
    assert gen_kw_args["catch_extra_error_codes"] is None
    assert sleep_time_generator.delay == 3
    assert sleep_time_generator.backoff == 2
    assert sleep_time_generator.max_delay == 60
    assert sleep_time_generator.jitter is False


def test_create_exponential_backoff_with_args(patch_cloud_retry):
    cloud_retry, decorator_generator = patch_cloud_retry()

    decorator = cloud_retry.exponential_backoff(
        retries=11, delay=4, backoff=3, max_delay=61, catch_extra_error_codes=[42]
    )
    assert decorator is sentinel.decorator

    gen_kw_args, sleep_time_generator = check_common_side_effects(decorator_generator)

    assert gen_kw_args["catch_extra_error_codes"] == [42]
    assert gen_kw_args["retries"] == 11
    assert sleep_time_generator.delay == 4
    assert sleep_time_generator.backoff == 3
    assert sleep_time_generator.max_delay == 61
    assert sleep_time_generator.jitter is False


def test_create_jittered_backoff_with_defaults(patch_cloud_retry):
    cloud_retry, decorator_generator = patch_cloud_retry()

    decorator = cloud_retry.jittered_backoff()
    assert decorator is sentinel.decorator

    gen_kw_args, sleep_time_generator = check_common_side_effects(decorator_generator)

    assert gen_kw_args["catch_extra_error_codes"] is None
    assert gen_kw_args["retries"] == 10
    assert sleep_time_generator.delay == 3
    assert sleep_time_generator.backoff == 2
    assert sleep_time_generator.max_delay == 60
    assert sleep_time_generator.jitter is True


def test_create_jittered_backoff_with_args(patch_cloud_retry):
    cloud_retry, decorator_generator = patch_cloud_retry()

    decorator = cloud_retry.jittered_backoff(retries=11, delay=4, backoff=3, max_delay=61, catch_extra_error_codes=[42])
    assert decorator is sentinel.decorator

    gen_kw_args, sleep_time_generator = check_common_side_effects(decorator_generator)

    assert gen_kw_args["catch_extra_error_codes"] == [42]
    assert gen_kw_args["retries"] == 11
    assert sleep_time_generator.delay == 4
    assert sleep_time_generator.backoff == 3
    assert sleep_time_generator.max_delay == 61
    assert sleep_time_generator.jitter is True
