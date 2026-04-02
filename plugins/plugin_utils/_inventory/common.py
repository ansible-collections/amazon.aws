# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import functools
import typing
from typing import cast

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Callable

from ansible.errors import AnsibleError

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_httpstatus
from ansible_collections.amazon.aws.plugins.module_utils.errors import AWSErrorHandler


class AnsibleInventoryAWSError(AnsibleError):
    """
    Exception for AWS inventory plugins that supports structured exception handling.

    Extends AnsibleError to be compatible with inventory plugin exception handling
    while supporting the same message/exception pattern as AnsibleAWSError.
    """

    def __init__(self, message=None, exception=None, **kwargs):
        if not message and not exception:
            super().__init__()
        elif not message:
            super().__init__(exception)
        else:
            super().__init__(message)

        self.exception = exception
        self.message = message


class AnsibleInventoryPermissionsError(AnsibleInventoryAWSError):
    """Exception raised for inventory permission/authorization errors."""

    pass


class InventoryErrorHandler(AWSErrorHandler):
    """
    Error handler for AWS inventory plugins.

    Provides decorators for handling common AWS inventory error patterns,
    converting boto3 exceptions to AnsibleError exceptions.
    """

    _CUSTOM_EXCEPTION = AnsibleInventoryAWSError

    @classmethod
    def _is_missing(cls) -> Callable:
        """
        Check if a boto3 exception indicates a missing/not found resource.

        Returns:
            A matcher function for boto3 error codes indicating missing resources.
        """
        return is_boto3_error_code(
            [
                "ResourceNotFoundException",
                "NoSuchEntity",
                "InvalidParameterValue",
            ]
        )

    @classmethod
    def common_error_handler(cls, description: str) -> Callable:
        """
        Decorator for inventory operations that provides error handling.

        Catches boto3 exceptions and converts them to AnsibleInventoryAWSError exceptions.
        Permission-related errors (UnauthorizedOperation, AccessDenied, 403) are converted to
        AnsibleInventoryPermissionsError to allow graceful handling with strict_permissions.

        Parameters:
            description: Human-readable description of the operation for error messages.

        Returns:
            Decorated function with error handling.
        """

        def wrapper(func: Callable) -> Callable:
            parent_class = cast(AWSErrorHandler, super(InventoryErrorHandler, cls))

            @parent_class.common_error_handler(description)
            @functools.wraps(func)
            def handler(*args: Any, **kwargs: Any) -> Any:
                try:
                    return func(*args, **kwargs)
                except is_boto3_error_code(["UnauthorizedOperation", "AccessDenied"]) as e:
                    raise AnsibleInventoryPermissionsError(
                        message=f"Failed to {description} (permission denied)", exception=e
                    ) from e
                except is_boto3_error_httpstatus(403) as e:  # pylint: disable=duplicate-except
                    raise AnsibleInventoryPermissionsError(
                        message=f"Failed to {description} (permission denied)", exception=e
                    ) from e

            return handler

        return wrapper
