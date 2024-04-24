# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import functools

try:
    import botocore
except ImportError:
    pass  # Modules are responsible for handling this.

from .exceptions import AnsibleAWSError


class AWSErrorHandler:
    """_CUSTOM_EXCEPTION can be overridden by subclasses to customize the exception raised"""

    _CUSTOM_EXCEPTION = AnsibleAWSError

    @classmethod
    def _is_missing(cls):
        """Should be overridden with a class method that returns the value from is_boto3_error_code (or similar)"""
        return type("NeverEverRaisedException", (Exception,), {})

    @classmethod
    def common_error_handler(cls, description):
        """A simple error handler that catches the standard Boto3 exceptions and raises
        an AnsibleAWSError exception.

        param: description: a description of the action being taken.
                            Exception raised will include a message of
                            f"Timeout trying to {description}" or
                            f"Failed to {description}"
        """

        def wrapper(func):
            @functools.wraps(func)
            def handler(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except botocore.exceptions.WaiterError as e:
                    raise cls._CUSTOM_EXCEPTION(message=f"Timeout trying to {description}", exception=e) from e
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    raise cls._CUSTOM_EXCEPTION(message=f"Failed to {description}", exception=e) from e

            return handler

        return wrapper

    @classmethod
    def list_error_handler(cls, description, default_value=None):
        """A simple error handler that catches the standard Boto3 exceptions and raises
        an AnsibleAWSError exception.
        Error codes representing a non-existent entity will result in None being returned
        Generally used for Get/List calls where the exception just means the resource isn't there

        param: description: a description of the action being taken.
                            Exception raised will include a message of
                            f"Timeout trying to {description}" or
                            f"Failed to {description}"
        param: default_value: the value to return if no matching
                            resources are returned.  Defaults to None
        """

        def wrapper(func):
            @functools.wraps(func)
            @cls.common_error_handler(description)
            def handler(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except cls._is_missing():
                    return default_value

            return handler

        return wrapper

    @classmethod
    def deletion_error_handler(cls, description):
        """A simple error handler that catches the standard Boto3 exceptions and raises
        an AnsibleAWSError exception.
        Error codes representing a non-existent entity will result in None being returned
        Generally used in deletion calls where NoSuchEntity means it's already gone

        param: description: a description of the action being taken.
                            Exception raised will include a message of
                            f"Timeout trying to {description}" or
                            f"Failed to {description}"
        """

        def wrapper(func):
            @functools.wraps(func)
            @cls.common_error_handler(description)
            def handler(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except cls._is_missing():
                    return False

            return handler

        return wrapper
