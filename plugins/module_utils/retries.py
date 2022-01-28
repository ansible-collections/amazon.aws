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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

try:
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from .cloud import CloudRetry


def _botocore_exception_maybe():
    """
    Allow for boto3 not being installed when using these utils by wrapping
    botocore.exceptions instead of assigning from it directly.
    """
    if HAS_BOTO3:
        return ClientError
    return type(None)


class AWSRetry(CloudRetry):
    base_class = _botocore_exception_maybe()

    @staticmethod
    def status_code_from_exception(error):
        return error.response['Error']['Code']

    @staticmethod
    def found(response_code, catch_extra_error_codes=None):
        # This list of failures is based on this API Reference
        # http://docs.aws.amazon.com/AWSEC2/latest/APIReference/errors-overview.html
        #
        # TooManyRequestsException comes from inside botocore when it
        # does retrys, unfortunately however it does not try long
        # enough to allow some services such as API Gateway to
        # complete configuration.  At the moment of writing there is a
        # botocore/boto3 bug open to fix this.
        #
        # https://github.com/boto/boto3/issues/876 (and linked PRs etc)
        retry_on = [
            'RequestLimitExceeded', 'Unavailable', 'ServiceUnavailable',
            'InternalFailure', 'InternalError', 'TooManyRequestsException',
            'Throttling'
        ]
        if catch_extra_error_codes:
            retry_on.extend(catch_extra_error_codes)

        return response_code in retry_on
