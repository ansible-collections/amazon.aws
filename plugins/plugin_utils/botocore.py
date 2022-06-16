# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
A set of helper functions designed to help with initializing boto3/botocore
connections.
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from functools import wraps

try:
    import botocore
except ImportError:
    pass

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.six import binary_type
from ansible.module_utils.six import text_type

from ansible_collections.amazon.aws.plugins.module_utils.botocore import _boto3_conn
from ansible_collections.amazon.aws.plugins.module_utils.botocore import BotocoreBaseMixin


class BotocorePluginMixin(BotocoreBaseMixin):
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
            self.fail(missing_required_lib('boto3>={0}'.format(desired), **kwargs))

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
            self.fail(missing_required_lib('botocore>={0}'.format(desired), **kwargs))

    def check_required_libraries(self):
        msg = self._test_required_libraries()
        if msg:
            self.fail(msg)

    def client(self, service):
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(self)
        return boto3_conn(self, conn_type='client', resource=service,
                          region=region, endpoint=ec2_url, **aws_connect_kwargs)

    def resource(self, service):
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(self)
        return boto3_conn(self, conn_type='resource', resource=service,
                          region=region, endpoint=ec2_url, **aws_connect_kwargs)

    @staticmethod
    def aws_error_handler(description):
        def wrapper(func):
            @wraps(func)
            def handler(_self, *args, **kwargs):
                try:
                    return func(_self, *args, **kwargs)
                except (botocore.exceptions.WaiterError) as e:
                    _self.fail_aws(e, msg='Failed waiting for {DESC}'.format(DESC=description))
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    _self.fail_aws(e, msg='Failed to {DESC}'.format(DESC=description))
            return handler
        return wrapper


def boto3_conn(module, conn_type=None, resource=None, region=None, endpoint=None, **params):
    """
    Builds a boto3 resource/client connection cleanly wrapping the most common failures.
    Handles:
        ValueError,
        botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError,
        botocore.exceptions.NoCredentialsError, botocore.exceptions.ConfigParseError,
        botocore.exceptions.NoRegionError
    """
    try:
        return _boto3_conn(conn_type=conn_type, resource=resource, region=region, endpoint=endpoint, **params)
    except ValueError as e:
        module.fail("Couldn't connect to AWS: {0}".format(to_native(e)))
    except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError,
            botocore.exceptions.NoCredentialsError, botocore.exceptions.ConfigParseError) as e:
        module.fail(to_native(e))
    except botocore.exceptions.NoRegionError as e:
        module.fail("The {0} requires a region and none was found in configuration, "
                    "environment variables or module parameters".format(module.module_description))


def get_aws_connection_info(module):
    aws_url = None
    region = None

    boto3_params = {}
    if module.has_option('region') and module.get_option('region') is not None:
        region = module.get_option('region')
    elif module.has_option('aws_region') and module.get_option('aws_region') is not None:
        region = module.get_option('aws_region')

    if module.has_option('aws_secret_key') and module.get_option('aws_secret_key') is not None:
        boto3_params['aws_secret_access_key'] = module.get_option('aws_secret_key')
    if module.has_option('aws_access_key') and module.get_option('aws_access_key') is not None:
        boto3_params['aws_access_key_id'] = module.get_option('aws_access_key')

    if module.has_option('aws_security_token') and module.get_option('aws_security_token') is not None:
        boto3_params['aws_session_token'] = module.get_option('aws_security_token')
    elif module.has_option('aws_session_token') and module.get_option('aws_session_token') is not None:
        boto3_params['aws_session_token'] = module.get_option('aws_session_token')

    if module.has_option('aws_profile') and module.get_option('aws_profile') is not None:
        boto3_params = {}
        boto3_params['profile_name'] = module.get_option('aws_profile')

    if module.has_option('validate_certs') and module.get_option('validate_certs') is not None:
        validate_certs = module.get_option('validate_certs')
    else:
        validate_certs = True

    if validate_certs and module.has_option('aws_ca_bundle') and module.get_option('aws_ca_bundle') is not None:
        boto3_params['verify'] = module.get_option('aws_ca_bundle')
    else:
        boto3_params['verify'] = validate_certs

    if module.has_option('aws_config') and module.get_option('aws_config') is not None:
        config = module.get_option('aws_config')
        boto3_params['aws_config'] = botocore.config.Config(**config)

    for param, value in boto3_params.items():
        if isinstance(value, binary_type):
            boto3_params[param] = text_type(value, 'utf-8', 'strict')

    if module.has_option('aws_endpoint_url') and module.get_option('aws_endpoint_url') is not None:
        aws_url = module.get_option('aws_endpoint_url')
    elif module.has_option('endpoint_url') and module.get_option('endpoint_url') is not None:
        aws_url = module.get_option('endpoint_url')
    elif module.has_option('endpoint') and module.get_option('endpoint') is not None:
        aws_url = module.get_option('endpoint')

    return region, aws_url, boto3_params
