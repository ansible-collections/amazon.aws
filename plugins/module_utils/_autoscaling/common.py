# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# try:
#     import botocore
# except ImportError:
#     pass  # Modules are responsible for handling this.

from ..botocore import is_boto3_error_code
from ..errors import AWSErrorHandler
from ..exceptions import AnsibleAWSError


class AnsibleAutoScalingError(AnsibleAWSError):
    pass


class AutoScalingErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleAutoScalingError

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("NoSuchEntity")
