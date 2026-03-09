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


class AnsibleRoute53Error(AnsibleAWSError):
    pass


class Route53ErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleRoute53Error

    @classmethod
    def _is_missing(cls) -> Callable:
        return is_boto3_error_code(["NoSuchHealthCheck", "NoSuchHostedZone"])
