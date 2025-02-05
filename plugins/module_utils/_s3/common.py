# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import functools
from typing import cast

try:
    # Beware, S3 is a "special" case, it sometimes catches botocore exceptions and
    # re-raises them as boto3 exceptions.
    import boto3
    import botocore
except ImportError:
    pass  # Handled by the calling module


from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_message
from ansible_collections.amazon.aws.plugins.module_utils.errors import AWSErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError

IGNORE_S3_DROP_IN_EXCEPTIONS = ["XNotImplemented", "NotImplemented", "AccessControlListNotSupported", "501"]


class AnsibleS3Error(AnsibleAWSError):
    pass


class AnsibleS3Sigv4RequiredError(AnsibleS3Error):
    pass


class AnsibleS3PermissionsError(AnsibleS3Error):
    pass


class AnsibleS3SupportError(AnsibleS3Error):
    pass


class AnsibleS3RegionSupportError(AnsibleS3SupportError):
    pass


class S3ErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleS3Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code(
            [
                "404",
                "NoSuchTagSet",
                "NoSuchTagSetError",
                "ObjectLockConfigurationNotFoundError",
                "NoSuchBucketPolicy",
                "ServerSideEncryptionConfigurationNotFoundError",
                "NoSuchBucket",
                "NoSuchPublicAccessBlockConfiguration",
                "OwnershipControlsNotFoundError",
                "NoSuchOwnershipControls",
            ]
        )

    @classmethod
    def common_error_handler(cls, description):
        def wrapper(func):
            parent_class = cast(AWSErrorHandler, super(S3ErrorHandler, cls))

            @parent_class.common_error_handler(description)
            @functools.wraps(func)
            def handler(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except is_boto3_error_code(["403", "AccessDenied"]) as e:
                    # FUTURE: there's a case to be made that this moves up into AWSErrorHandler
                    # for now, we'll handle this just for S3, but wait and see if it pops up in too
                    # many other places
                    raise AnsibleS3PermissionsError(
                        message=f"Failed to {description} (permission denied)", exception=e
                    ) from e
                except is_boto3_error_message(  # pylint: disable=duplicate-except
                    "require AWS Signature Version 4"
                ) as e:
                    raise AnsibleS3Sigv4RequiredError(
                        message=f"Failed to {description} (not supported by cloud)", exception=e
                    ) from e
                except is_boto3_error_code(IGNORE_S3_DROP_IN_EXCEPTIONS) as e:  # pylint: disable=duplicate-except
                    # Unlike most of our modules, we attempt to handle non-AWS clouds.  For read-only
                    # actions we sometimes need the ability to ignore unsupported features.
                    raise AnsibleS3SupportError(
                        message=f"Failed to {description} (not supported by cloud)", exception=e
                    ) from e
                except botocore.exceptions.EndpointConnectionError as e:
                    raise cls._CUSTOM_EXCEPTION(
                        message=f"Failed to {description} - Invalid endpoint provided", exception=e
                    ) from e
                except boto3.exceptions.Boto3Error as e:
                    raise cls._CUSTOM_EXCEPTION(message=f"Failed to {description}", exception=e) from e

            return handler

        return wrapper
