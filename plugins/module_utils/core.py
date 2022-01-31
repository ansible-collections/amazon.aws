#
#  Copyright 2017 Michael De La Rue | Ansible
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

"""This module adds shared support for generic Amazon AWS modules

In order to use this module, include it as part of a custom
module as shown below.

  from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
  module = AnsibleAWSModule(argument_spec=dictionary, supports_check_mode=boolean
                            mutually_exclusive=list1, required_together=list2)

The 'AnsibleAWSModule' module provides similar, but more restricted,
interfaces to the normal Ansible module.  It also includes the
additional methods for connecting to AWS using the standard module arguments

    m.resource('lambda') # - get an AWS connection as a boto3 resource.

or

    m.client('sts') # - get an AWS connection as a boto3 client.

To make use of AWSRetry easier, it can now be wrapped around any call from a
module-created client. To add retries to a client, create a client:

    m.client('ec2', retry_decorator=AWSRetry.jittered_backoff(retries=10))

Any calls from that client can be made to use the decorator passed at call-time
using the `aws_retry` argument. By default, no retries are used.

    ec2 = m.client('ec2', retry_decorator=AWSRetry.jittered_backoff(retries=10))
    ec2.describe_instances(InstanceIds=['i-123456789'], aws_retry=True)

The call will be retried the specified number of times, so the calling functions
don't need to be wrapped in the backoff decorator.
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# Used to live here, moved into ansible_collections.amazon.aws.plugins.module_utils.arn
from .arn import parse_aws_arn  # pylint: disable=unused-import

# Used to live here, moved into ansible_collections.amazon.aws.plugins.module_utils.botocore
from .botocore import HAS_BOTO3  # pylint: disable=unused-import
from .botocore import is_boto3_error_code  # pylint: disable=unused-import
from .botocore import is_boto3_error_message  # pylint: disable=unused-import
from .botocore import get_boto3_client_method_parameters  # pylint: disable=unused-import
from .botocore import normalize_boto3_result  # pylint: disable=unused-import

# Used to live here, moved into ansible_collections.amazon.aws.plugins.module_utils.modules
from .modules import AnsibleAWSModule  # pylint: disable=unused-import

# Used to live here, moved into ansible_collections.amazon.aws.plugins.module_utils.modules
from .transformation import scrub_none_parameters  # pylint: disable=unused-import

# We will also export HAS_BOTO3 so end user modules can use it.
__all__ = ('AnsibleAWSModule', 'HAS_BOTO3', 'is_boto3_error_code', 'is_boto3_error_message')


class AnsibleAWSError(Exception):
    pass
