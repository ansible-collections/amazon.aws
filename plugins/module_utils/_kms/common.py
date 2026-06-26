# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Error handling infrastructure for KMS operations.

This module defines KMS-specific exception classes and error handlers that
provide consistent error handling across all KMS operations.

Exception hierarchy:
- AnsibleKMSError (base)
  - AnsibleKMSPermissionsError (AccessDeniedException)
  - AnsibleKMSUnsupportedError (UnsupportedOperationException)

The KMSErrorHandler decorator automatically converts boto3 exceptions to
these typed exceptions with helpful error messages.
"""

from __future__ import annotations

import functools
import typing

if typing.TYPE_CHECKING:
    from typing import Callable

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.errors import AWSErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError


class AnsibleKMSError(AnsibleAWSError):
    pass


class AnsibleKMSPermissionsError(AnsibleKMSError):
    """Exception raised for KMS permission/authorization errors."""

    pass


class AnsibleKMSUnsupportedError(AnsibleKMSError):
    """Exception raised when a KMS operation is not supported (e.g., key rotation on asymmetric keys)."""

    pass


class KMSErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleKMSError

    @classmethod
    def _is_missing(cls) -> Callable:
        # KMS uses service-specific NotFoundException exception
        # Also handle InvalidKeyId for key lookup failures
        return is_boto3_error_code(["NotFoundException", "InvalidKeyId"])

    @classmethod
    def common_error_handler(cls, description: str):
        """
        Decorator for common error handling, including permissions and unsupported operation errors.

        Catches and converts boto3 exceptions to appropriate AnsibleKMS exceptions:
        - AccessDeniedException -> raises AnsibleKMSPermissionsError
        - UnsupportedOperationException -> raises AnsibleKMSUnsupportedError
        """

        def wrapper(func: Callable) -> Callable:
            parent_decorator = super(KMSErrorHandler, cls).common_error_handler(description)

            @parent_decorator
            @functools.wraps(func)
            def handler(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except is_boto3_error_code("AccessDeniedException") as e:
                    raise AnsibleKMSPermissionsError(
                        message=f"Failed to {description} (permission denied)", exception=e
                    ) from e
                except is_boto3_error_code("UnsupportedOperationException") as e:  # pylint: disable=duplicate-except
                    raise AnsibleKMSUnsupportedError(
                        message=f"Failed to {description} (operation not supported)", exception=e
                    ) from e

            return handler

        return wrapper
