# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Common ELBv2 error handling."""

from ..botocore import is_boto3_error_code
from ..errors import AWSErrorHandler
from ..exceptions import AnsibleAWSError


class AnsibleELBv2Error(AnsibleAWSError):
    """Custom exception for ELBv2 operations."""

    pass


class ELBv2ErrorHandler(AWSErrorHandler):
    """Error handler for ELBv2 load balancer operations."""

    _CUSTOM_EXCEPTION = AnsibleELBv2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("LoadBalancerNotFound")


class ELBv2ListenerErrorHandler(AWSErrorHandler):
    """Error handler for ELBv2 listener operations."""

    _CUSTOM_EXCEPTION = AnsibleELBv2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("ListenerNotFound")


class ELBv2RuleErrorHandler(AWSErrorHandler):
    """Error handler for ELBv2 rule operations."""

    _CUSTOM_EXCEPTION = AnsibleELBv2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("RuleNotFound")


class ELBv2TargetGroupErrorHandler(AWSErrorHandler):
    """Error handler for ELBv2 target group operations."""

    _CUSTOM_EXCEPTION = AnsibleELBv2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("TargetGroupNotFound")
