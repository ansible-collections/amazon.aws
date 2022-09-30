# Copyright (c) 2021 Ansible Project
#
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import time
import functools
import random
import ansible.module_utils.common.warnings as ansible_warnings


class BackoffIterator:
    """iterate sleep value based on the exponential or jitter back-off algorithm.
    Args:
        delay (int or float): initial delay.
        backoff (int or float): backoff multiplier e.g. value of 2 will  double the delay each retry.
        max_delay (int or None): maximum amount of time to wait between retries.
        jitter (bool): if set to true, add jitter to the generate value.
    """

    def __init__(self, delay, backoff, max_delay=None, jitter=False):
        self.delay = delay
        self.backoff = backoff
        self.max_delay = max_delay
        self.jitter = jitter

    def __iter__(self):
        self.current_delay = self.delay
        return self

    def __next__(self):
        return_value = self.current_delay if self.max_delay is None else min(self.current_delay, self.max_delay)
        if self.jitter:
            return_value = random.uniform(0.0, return_value)
        self.current_delay *= self.backoff
        return return_value


def _retry_func(func, sleep_time_generator, retries, catch_extra_error_codes, found_f, status_code_from_except_f, base_class):
    counter = 0
    for sleep_time in sleep_time_generator:
        try:
            return func()
        except Exception as exc:  # pylint: disable=broad-except
            counter += 1
            if counter == retries:
                raise
            if base_class and not isinstance(exc, base_class):
                raise
            status_code = status_code_from_except_f(exc)
            if found_f(status_code, catch_extra_error_codes):
                time.sleep(sleep_time)
            else:
                raise


class CloudRetry:
    """
    The base class to be used by other cloud providers to provide a backoff/retry decorator based on status codes.
    """

    base_class = type(None)

    @staticmethod
    def status_code_from_exception(error):
        """
        Returns the Error 'code' from an exception.
        Args:
          error: The Exception from which the error code is to be extracted.
            error will be an instance of class.base_class.
        """
        raise NotImplementedError()

    @staticmethod
    def found(response_code, catch_extra_error_codes=None):
        def _is_iterable():
            try:
                iter(catch_extra_error_codes)
            except TypeError:
                # not iterable
                return False
            else:
                # iterable
                return True
        return _is_iterable() and response_code in catch_extra_error_codes

    @classmethod
    def base_decorator(cls, retries, found, status_code_from_exception, catch_extra_error_codes, sleep_time_generator):
        def retry_decorator(func):
            @functools.wraps(func)
            def _retry_wrapper(*args, **kwargs):
                partial_func = functools.partial(func, *args, **kwargs)
                return _retry_func(
                    func=partial_func,
                    sleep_time_generator=sleep_time_generator,
                    retries=retries,
                    catch_extra_error_codes=catch_extra_error_codes,
                    found_f=found,
                    status_code_from_except_f=status_code_from_exception,
                    base_class=cls.base_class,
                )
            return _retry_wrapper
        return retry_decorator

    @classmethod
    def exponential_backoff(cls, retries=10, delay=3, backoff=2, max_delay=60, catch_extra_error_codes=None):
        """Wrap a callable with retry behavior.
        Args:
            retries (int): Number of times to retry a failed request before giving up
                default=10
            delay (int or float): Initial delay between retries in seconds
                default=3
            backoff (int or float): backoff multiplier e.g. value of 2 will  double the delay each retry
                default=2
            max_delay (int or None): maximum amount of time to wait between retries.
                default=60
            catch_extra_error_codes: Additional error messages to catch, in addition to those which may be defined by a subclass of CloudRetry
                default=None
        Returns:
            Callable: A generator that calls the decorated function using an exponential backoff.
        """
        sleep_time_generator = BackoffIterator(delay=delay, backoff=backoff, max_delay=max_delay)
        return cls.base_decorator(
            retries=retries,
            found=cls.found,
            status_code_from_exception=cls.status_code_from_exception,
            catch_extra_error_codes=catch_extra_error_codes,
            sleep_time_generator=sleep_time_generator,
        )

    @classmethod
    def jittered_backoff(cls, retries=10, delay=3, backoff=2.0, max_delay=60, catch_extra_error_codes=None):
        """Wrap a callable with retry behavior.
        Args:
            retries (int): Number of times to retry a failed request before giving up
                default=10
            delay (int or float): Initial delay between retries in seconds
                default=3
            backoff (int or float): backoff multiplier e.g. value of 2 will  double the delay each retry
                default=2.0
            max_delay (int or None): maximum amount of time to wait between retries.
                default=60
            catch_extra_error_codes: Additional error messages to catch, in addition to those which may be defined by a subclass of CloudRetry
                default=None
        Returns:
            Callable: A generator that calls the decorated function using using a jittered backoff strategy.
        """
        sleep_time_generator = BackoffIterator(delay=delay, backoff=backoff, max_delay=max_delay, jitter=True)
        return cls.base_decorator(
            retries=retries,
            found=cls.found,
            status_code_from_exception=cls.status_code_from_exception,
            catch_extra_error_codes=catch_extra_error_codes,
            sleep_time_generator=sleep_time_generator,
        )

    @classmethod
    def backoff(cls, tries=10, delay=3, backoff=1.1, catch_extra_error_codes=None):
        """
        Wrap a callable with retry behavior.
        Developers should use CloudRetry.exponential_backoff instead.
        This method has been deprecated and will be removed in release 6.0.0, consider using exponential_backoff method instead.
        Args:
            retries (int): Number of times to retry a failed request before giving up
                default=10
            delay (int or float): Initial delay between retries in seconds
                default=3
            backoff (int or float): backoff multiplier e.g. value of 2 will  double the delay each retry
                default=1.1
            catch_extra_error_codes: Additional error messages to catch, in addition to those which may be defined by a subclass of CloudRetry
                default=None
        Returns:
            Callable: A generator that calls the decorated function using an exponential backoff.
        """
        # This won't emit a warning (we don't have the context available to us), but will trigger
        # sanity failures as we prepare for 6.0.0
        ansible_warnings.deprecate(
            'CloudRetry.backoff has been deprecated, please use CloudRetry.exponential_backoff instead',
            version='6.0.0', collection_name='amazon.aws')

        return cls.exponential_backoff(
            retries=tries,
            delay=delay,
            backoff=backoff,
            max_delay=None,
            catch_extra_error_codes=catch_extra_error_codes,
        )
