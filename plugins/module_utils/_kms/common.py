# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from typing import Callable

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.errors import AWSErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError


class AnsibleKMSError(AnsibleAWSError):
    pass


class KMSErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleKMSError

    @classmethod
    def _is_missing(cls) -> Callable:
        # KMS uses service-specific NotFoundException exception
        # Also handle InvalidKeyId for key lookup failures
        return is_boto3_error_code(["NotFoundException", "InvalidKeyId"])
