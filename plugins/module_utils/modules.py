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

  from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
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

from functools import wraps
import logging
import os
import re
import traceback


try:
    from cStringIO import StringIO
except ImportError:
    # Python 3
    from io import StringIO

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils._text import to_native

from .botocore import HAS_BOTO3
from .botocore import boto3_conn
from .botocore import get_aws_connection_info
from .botocore import get_aws_region
from .botocore import gather_sdk_versions

from .version import LooseVersion

# Currently only AnsibleAWSModule.  However we have a lot of Copy and Paste code
# for Inventory and Lookup modules which we should refactor


class AnsibleAWSModule(object):
    """An ansible module class for AWS modules

    AnsibleAWSModule provides an a class for building modules which
    connect to Amazon Web Services.  The interface is currently more
    restricted than the basic module class with the aim that later the
    basic module class can be reduced.  If you find that any key
    feature is missing please contact the author/Ansible AWS team
    (available on #ansible-aws on IRC) to request the additional
    features needed.
    """
    default_settings = {
        "default_args": True,
        "check_boto3": True,
        "auto_retry": True,
        "module_class": AnsibleModule
    }

    def __init__(self, **kwargs):
        local_settings = {}
        for key in AnsibleAWSModule.default_settings:
            try:
                local_settings[key] = kwargs.pop(key)
            except KeyError:
                local_settings[key] = AnsibleAWSModule.default_settings[key]
        self.settings = local_settings

        if local_settings["default_args"]:
            argument_spec_full = aws_argument_spec()
            try:
                argument_spec_full.update(kwargs["argument_spec"])
            except (TypeError, NameError):
                pass
            kwargs["argument_spec"] = argument_spec_full

        self._module = AnsibleAWSModule.default_settings["module_class"](**kwargs)

        if local_settings["check_boto3"]:
            if not HAS_BOTO3:
                self._module.fail_json(
                    msg=missing_required_lib('botocore and boto3'))
            if not self.botocore_at_least('1.21.0'):
                self.warn('botocore < 1.21.0 is not supported or tested.'
                          '  Some features may not work.')
            if not self.boto3_at_least("1.18.0"):
                self.warn('boto3 < 1.18.0 is not supported or tested.'
                          '  Some features may not work.')

        deprecated_vars = {'EC2_REGION', 'EC2_SECURITY_TOKEN', 'EC2_SECRET_KEY', 'EC2_ACCESS_KEY',
                           'EC2_URL', 'S3_URL'}
        if deprecated_vars.intersection(set(os.environ.keys())):
            self._module.deprecate(
                "Support for the 'EC2_REGION', 'EC2_ACCESS_KEY', 'EC2_SECRET_KEY', "
                "'EC2_SECURITY_TOKEN', 'EC2_URL', and 'S3_URL' environment "
                "variables has been deprecated.  "
                "These variables are currently used for all AWS services which can "
                "cause confusion.  We recomend using the relevant module "
                "parameters or alternatively the 'AWS_REGION', 'AWS_ACCESS_KEY_ID', "
                "'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN', and 'AWS_URL' "
                "environment variables can be used instead.",
                date='2024-12-01', collection_name='amazon.aws',
            )

        if 'AWS_SECURITY_TOKEN' in os.environ.keys():
            self._module.deprecate(
                "Support for the 'AWS_SECURITY_TOKEN' environment variable "
                "has been deprecated.  This variable was based on the original "
                "boto SDK, support for which has now been dropped.  "
                "We recommend using the 'session_token' module parameter "
                "or alternatively the 'AWS_SESSION_TOKEN' environment variable "
                "can be used instead.",
                date='2024-12-01', collection_name='amazon.aws',
            )

        self.check_mode = self._module.check_mode
        self._diff = self._module._diff
        self._name = self._module._name

        self._botocore_endpoint_log_stream = StringIO()
        self.logger = None
        if self.params.get('debug_botocore_endpoint_logs'):
            self.logger = logging.getLogger('botocore.endpoint')
            self.logger.setLevel(logging.DEBUG)
            self.logger.addHandler(logging.StreamHandler(self._botocore_endpoint_log_stream))

    @property
    def params(self):
        return self._module.params

    def _get_resource_action_list(self):
        actions = []
        for ln in self._botocore_endpoint_log_stream.getvalue().split('\n'):
            ln = ln.strip()
            if not ln:
                continue
            found_operational_request = re.search(r"OperationModel\(name=.*?\)", ln)
            if found_operational_request:
                operation_request = found_operational_request.group(0)[20:-1]
                resource = re.search(r"https://.*?\.", ln).group(0)[8:-1]
                actions.append("{0}:{1}".format(resource, operation_request))
        return list(set(actions))

    def exit_json(self, *args, **kwargs):
        if self.params.get('debug_botocore_endpoint_logs'):
            kwargs['resource_actions'] = self._get_resource_action_list()
        return self._module.exit_json(*args, **kwargs)

    def fail_json(self, *args, **kwargs):
        if self.params.get('debug_botocore_endpoint_logs'):
            kwargs['resource_actions'] = self._get_resource_action_list()
        return self._module.fail_json(*args, **kwargs)

    def debug(self, *args, **kwargs):
        return self._module.debug(*args, **kwargs)

    def warn(self, *args, **kwargs):
        return self._module.warn(*args, **kwargs)

    def deprecate(self, *args, **kwargs):
        return self._module.deprecate(*args, **kwargs)

    def boolean(self, *args, **kwargs):
        return self._module.boolean(*args, **kwargs)

    def md5(self, *args, **kwargs):
        return self._module.md5(*args, **kwargs)

    def client(self, service, retry_decorator=None):
        region, endpoint_url, aws_connect_kwargs = get_aws_connection_info(self, boto3=True)
        conn = boto3_conn(self, conn_type='client', resource=service,
                          region=region, endpoint=endpoint_url, **aws_connect_kwargs)
        return conn if retry_decorator is None else _RetryingBotoClientWrapper(conn, retry_decorator)

    def resource(self, service):
        region, endpoint_url, aws_connect_kwargs = get_aws_connection_info(self, boto3=True)
        return boto3_conn(self, conn_type='resource', resource=service,
                          region=region, endpoint=endpoint_url, **aws_connect_kwargs)

    @property
    def region(self):
        return get_aws_region(self, True)

    def fail_json_aws(self, exception, msg=None, **kwargs):
        """call fail_json with processed exception

        function for converting exceptions thrown by AWS SDK modules,
        botocore, boto3 and boto, into nice error messages.
        """
        last_traceback = traceback.format_exc()

        # to_native is trusted to handle exceptions that str() could
        # convert to text.
        try:
            except_msg = to_native(exception.message)
        except AttributeError:
            except_msg = to_native(exception)

        if msg is not None:
            message = '{0}: {1}'.format(msg, except_msg)
        else:
            message = except_msg

        try:
            response = exception.response
        except AttributeError:
            response = None

        failure = dict(
            msg=message,
            exception=last_traceback,
            **self._gather_versions()
        )

        failure.update(kwargs)

        if response is not None:
            failure.update(**camel_dict_to_snake_dict(response))

        self.fail_json(**failure)

    def _gather_versions(self):
        """Gather AWS SDK (boto3 and botocore) dependency versions

        Returns {'boto3_version': str, 'botocore_version': str}
        Returns {} if either is not installed
        """
        return gather_sdk_versions()

    def require_boto3_at_least(self, desired, **kwargs):
        """Check if the available boto3 version is greater than or equal to a desired version.

        calls fail_json() when the boto3 version is less than the desired
        version

        Usage:
            module.require_boto3_at_least("1.2.3", reason="to update tags")
            module.require_boto3_at_least("1.1.1")

        :param desired the minimum desired version
        :param reason why the version is required (optional)
        """
        if not self.boto3_at_least(desired):
            self._module.fail_json(
                msg=missing_required_lib('boto3>={0}'.format(desired), **kwargs),
                **self._gather_versions()
            )

    def boto3_at_least(self, desired):
        """Check if the available boto3 version is greater than or equal to a desired version.

        Usage:
            if module.params.get('assign_ipv6_address') and not module.boto3_at_least('1.4.4'):
                # conditionally fail on old boto3 versions if a specific feature is not supported
                module.fail_json(msg="Boto3 can't deal with EC2 IPv6 addresses before version 1.4.4.")
        """
        existing = self._gather_versions()
        return LooseVersion(existing['boto3_version']) >= LooseVersion(desired)

    def require_botocore_at_least(self, desired, **kwargs):
        """Check if the available botocore version is greater than or equal to a desired version.

        calls fail_json() when the botocore version is less than the desired
        version

        Usage:
            module.require_botocore_at_least("1.2.3", reason="to update tags")
            module.require_botocore_at_least("1.1.1")

        :param desired the minimum desired version
        :param reason why the version is required (optional)
        """
        if not self.botocore_at_least(desired):
            self._module.fail_json(
                msg=missing_required_lib('botocore>={0}'.format(desired), **kwargs),
                **self._gather_versions()
            )

    def botocore_at_least(self, desired):
        """Check if the available botocore version is greater than or equal to a desired version.

        Usage:
            if not module.botocore_at_least('1.2.3'):
                module.fail_json(msg='The Serverless Elastic Load Compute Service is not in botocore before v1.2.3')
            if not module.botocore_at_least('1.5.3'):
                module.warn('Botocore did not include waiters for Service X before 1.5.3. '
                            'To wait until Service X resources are fully available, update botocore.')
        """
        existing = self._gather_versions()
        return LooseVersion(existing['botocore_version']) >= LooseVersion(desired)


class _RetryingBotoClientWrapper(object):
    __never_wait = (
        'get_paginator', 'can_paginate',
        'get_waiter', 'generate_presigned_url',
    )

    def __init__(self, client, retry):
        self.client = client
        self.retry = retry

    def _create_optional_retry_wrapper_function(self, unwrapped):
        retrying_wrapper = self.retry(unwrapped)

        @wraps(unwrapped)
        def deciding_wrapper(aws_retry=False, *args, **kwargs):
            if aws_retry:
                return retrying_wrapper(*args, **kwargs)
            else:
                return unwrapped(*args, **kwargs)
        return deciding_wrapper

    def __getattr__(self, name):
        unwrapped = getattr(self.client, name)
        if name in self.__never_wait:
            return unwrapped
        elif callable(unwrapped):
            wrapped = self._create_optional_retry_wrapper_function(unwrapped)
            setattr(self, name, wrapped)
            return wrapped
        else:
            return unwrapped


def _aws_common_argument_spec():
    """
    This does not include 'region' as some AWS APIs don't require a
    region.  However, it's not recommended to do this as it means module_defaults
    can't include the region parameter.
    """
    return dict(
        access_key=dict(
            aliases=['aws_access_key_id', 'aws_access_key', 'ec2_access_key'],
            deprecated_aliases=[
                dict(name='ec2_access_key', date='2024-12-01', collection_name='amazon.aws'),
            ],
            no_log=False,
        ),
        secret_key=dict(
            aliases=['aws_secret_access_key', 'aws_secret_key', 'ec2_secret_key'],
            deprecated_aliases=[
                dict(name='ec2_secret_key', date='2024-12-01', collection_name='amazon.aws'),
            ],
            no_log=True,
        ),
        session_token=dict(
            aliases=['aws_session_token', 'security_token', 'access_token', 'aws_security_token'],
            deprecated_aliases=[
                dict(name='access_token', date='2024-12-01', collection_name='amazon.aws'),
                dict(name='security_token', date='2024-12-01', collection_name='amazon.aws'),
                dict(name='aws_security_token', date='2024-12-01', collection_name='amazon.aws'),
            ],
            no_log=True,
        ),
        profile=dict(
            aliases=['aws_profile'],
        ),

        endpoint_url=dict(
            aliases=['aws_endpoint_url', 'ec2_url', 's3_url'],
            deprecated_aliases=[
                dict(name='ec2_url', date='2024-12-01', collection_name='amazon.aws'),
                dict(name='s3_url', date='2024-12-01', collection_name='amazon.aws'),
            ],
        ),
        validate_certs=dict(
            type='bool',
            default=True,
        ),
        aws_ca_bundle=dict(
            type='path'
        ),
        aws_config=dict(
            type='dict'
        ),
        debug_botocore_endpoint_logs=dict(
            type='bool',
            default=False,
            fallback=(env_fallback, ['ANSIBLE_DEBUG_BOTOCORE_LOGS']),
        ),
    )


def aws_argument_spec():
    """
    Returns a dictionary containing the argument_spec common to all AWS modules.
    """
    region_spec = dict(
        region=dict(
            aliases=['aws_region', 'ec2_region'],
            deprecated_aliases=[
                dict(name='ec2_region', date='2024-12-01', collection_name='amazon.aws'),
            ],
        ),
    )
    spec = _aws_common_argument_spec()
    spec.update(region_spec)
    return spec
