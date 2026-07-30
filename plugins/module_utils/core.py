# -*- coding: utf-8 -*-

#  Copyright 2017 Michael De La Rue | Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Backwards-compatibility module for amazon.aws module_utils.

.. deprecated::
   The re-exports in this module are deprecated and will be removed in a future major release.
   New code should import directly from the appropriate module_utils submodule.

See the developer guidelines for details:
https://ansible-collections.github.io/amazon.aws/branch/main/dev_guidelines.html
"""

# Deprecated backwards-compatibility re-exports
# These imports are maintained for backwards compatibility but their use is deprecated.
# New code should import directly from the appropriate module_utils submodule.
# These re-exports will be removed in a future major release.
# pylint: disable=unused-import,useless-import-alias
from .arn import parse_aws_arn as parse_aws_arn
from .botocore import HAS_BOTO3 as HAS_BOTO3
from .botocore import get_boto3_client_method_parameters as get_boto3_client_method_parameters
from .botocore import is_boto3_error_code as is_boto3_error_code
from .botocore import is_boto3_error_message as is_boto3_error_message
from .botocore import normalize_boto3_result as normalize_boto3_result
from .exceptions import AnsibleAWSError as AnsibleAWSError
from .modules import AnsibleAWSModule as AnsibleAWSModule
from .transformation import scrub_none_parameters as scrub_none_parameters

# pylint: enable=unused-import,useless-import-alias

# We will also export HAS_BOTO3 so end user modules can use it.
__all__ = ("HAS_BOTO3", "AnsibleAWSModule", "is_boto3_error_code", "is_boto3_error_message")
