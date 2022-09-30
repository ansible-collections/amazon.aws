# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.amazon.aws.plugins.module_utils.cloud import CloudRetry
from ansible_collections.amazon.aws.plugins.module_utils.cloud import BackoffIterator
from ansible_collections.amazon.aws.tests.unit.compat.mock import MagicMock
from ansible_collections.amazon.aws.tests.unit.compat.mock import sentinel


class TestBackoffCreation(object):

    def setup_method(self):
        self.decorator_generator = MagicMock()
        self.decorator_generator.return_value = sentinel.decorator

    def test_create_exponential_backoff(self, monkeypatch):
        decorator_generator = self.decorator_generator
        monkeypatch.setattr(CloudRetry, 'base_decorator', decorator_generator)

        decorator = CloudRetry.exponential_backoff()
        assert decorator_generator.called is True
        assert decorator_generator.call_count == 1
        assert decorator is sentinel.decorator

        kw_args = decorator_generator.call_args.kwargs
        assert kw_args['catch_extra_error_codes'] is None
        assert kw_args['found'] is CloudRetry.found
        assert kw_args['retries'] == 10
        assert isinstance(kw_args['sleep_time_generator'], BackoffIterator)
        assert kw_args['status_code_from_exception'] is CloudRetry.status_code_from_exception

        sleep_time_generator = kw_args['sleep_time_generator']
        assert sleep_time_generator.delay == 3
        assert sleep_time_generator.backoff == 2
        assert sleep_time_generator.max_delay == 60
        assert sleep_time_generator.jitter is False

        decorator_generator.reset_mock()

        decorator = CloudRetry.exponential_backoff(retries=11, delay=4, backoff=3, max_delay=61, catch_extra_error_codes=[42])
        assert decorator_generator.called is True
        assert decorator_generator.call_count == 1
        assert decorator is sentinel.decorator

        kw_args = decorator_generator.call_args.kwargs
        assert kw_args['catch_extra_error_codes'] == [42]
        assert kw_args['found'] is CloudRetry.found
        assert kw_args['retries'] == 11
        assert isinstance(kw_args['sleep_time_generator'], BackoffIterator)
        assert kw_args['status_code_from_exception'] is CloudRetry.status_code_from_exception

        sleep_time_generator = kw_args['sleep_time_generator']
        assert sleep_time_generator.delay == 4
        assert sleep_time_generator.backoff == 3
        assert sleep_time_generator.max_delay == 61
        assert sleep_time_generator.jitter is False

    def test_create_jittered_backoff(self, monkeypatch):
        decorator_generator = self.decorator_generator
        monkeypatch.setattr(CloudRetry, 'base_decorator', decorator_generator)

        decorator = CloudRetry.jittered_backoff()
        assert decorator_generator.called is True
        assert decorator_generator.call_count == 1
        assert decorator is sentinel.decorator

        kw_args = decorator_generator.call_args.kwargs
        assert kw_args['catch_extra_error_codes'] is None
        assert kw_args['found'] is CloudRetry.found
        assert kw_args['retries'] == 10
        assert isinstance(kw_args['sleep_time_generator'], BackoffIterator)
        assert kw_args['status_code_from_exception'] is CloudRetry.status_code_from_exception

        sleep_time_generator = kw_args['sleep_time_generator']
        assert sleep_time_generator.delay == 3
        assert sleep_time_generator.backoff == 2
        assert sleep_time_generator.max_delay == 60
        assert sleep_time_generator.jitter is True

        decorator_generator.reset_mock()

        decorator = CloudRetry.jittered_backoff(retries=11, delay=4, backoff=3, max_delay=61, catch_extra_error_codes=[42])
        assert decorator_generator.called is True
        assert decorator_generator.call_count == 1
        assert decorator is sentinel.decorator

        kw_args = decorator_generator.call_args.kwargs
        assert kw_args['catch_extra_error_codes'] == [42]
        assert kw_args['found'] is CloudRetry.found
        assert kw_args['retries'] == 11
        assert isinstance(kw_args['sleep_time_generator'], BackoffIterator)
        assert kw_args['status_code_from_exception'] is CloudRetry.status_code_from_exception

        sleep_time_generator = kw_args['sleep_time_generator']
        assert sleep_time_generator.delay == 4
        assert sleep_time_generator.backoff == 3
        assert sleep_time_generator.max_delay == 61
        assert sleep_time_generator.jitter is True

    def test_create_legacy_backoff(self, monkeypatch):
        decorator_generator = self.decorator_generator
        monkeypatch.setattr(CloudRetry, 'base_decorator', decorator_generator)

        decorator = CloudRetry.backoff()
        assert decorator_generator.called is True
        assert decorator_generator.call_count == 1
        assert decorator is sentinel.decorator

        kw_args = decorator_generator.call_args.kwargs
        assert kw_args['catch_extra_error_codes'] is None
        assert kw_args['found'] is CloudRetry.found
        assert kw_args['retries'] == 10
        assert isinstance(kw_args['sleep_time_generator'], BackoffIterator)
        assert kw_args['status_code_from_exception'] is CloudRetry.status_code_from_exception

        sleep_time_generator = kw_args['sleep_time_generator']
        assert sleep_time_generator.delay == 3
        assert sleep_time_generator.backoff == 1.1
        assert sleep_time_generator.max_delay is None
        assert sleep_time_generator.jitter is False

        decorator_generator.reset_mock()

        decorator = CloudRetry.backoff(tries=11, delay=4, backoff=3, catch_extra_error_codes=[42])
        assert decorator_generator.called is True
        assert decorator_generator.call_count == 1
        assert decorator is sentinel.decorator

        kw_args = decorator_generator.call_args.kwargs
        assert kw_args['catch_extra_error_codes'] == [42]
        assert kw_args['found'] is CloudRetry.found
        assert kw_args['retries'] == 11
        assert isinstance(kw_args['sleep_time_generator'], BackoffIterator)
        assert kw_args['status_code_from_exception'] is CloudRetry.status_code_from_exception

        sleep_time_generator = kw_args['sleep_time_generator']
        assert sleep_time_generator.delay == 4
        assert sleep_time_generator.backoff == 3
        assert sleep_time_generator.max_delay is None
        assert sleep_time_generator.jitter is False
