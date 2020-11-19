# (c) 2019 Robert Williams
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import datetime
import sys
from copy import copy

from ansible.errors import AnsibleError
from ansible.plugins.loader import lookup_loader

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    pytestmark = pytest.mark.skip("This test requires the boto3 and botocore Python libraries")


@pytest.fixture
def dummy_credentials():
    dummy_credentials = {}
    dummy_credentials['boto_profile'] = None
    dummy_credentials['aws_secret_key'] = "notasecret"
    dummy_credentials['aws_access_key'] = "notakey"
    dummy_credentials['aws_security_token'] = None
    dummy_credentials['region'] = 'eu-west-1'
    return dummy_credentials


def test_lookup_variable(mocker, dummy_credentials):
    dateutil_tz = pytest.importorskip("dateutil.tz")
    simple_variable_success_response = {
        'Name': 'secret',
        'VersionId': 'cafe8168-e6ce-4e59-8830-5b143faf6c52',
        'SecretString': '{"secret":"simplesecret"}',
        'VersionStages': ['AWSCURRENT'],
        'CreatedDate': datetime.datetime(2019, 4, 4, 11, 41, 0, 878000, tzinfo=dateutil_tz.tzlocal()),
        'ResponseMetadata': {
            'RequestId': '21099462-597c-490a-800f-8b7a41e5151c',
            'HTTPStatusCode': 200,
            'HTTPHeaders': {
                'date': 'Thu, 04 Apr 2019 10:43:12 GMT',
                'content-type': 'application/x-amz-json-1.1',
                'content-length': '252',
                'connection': 'keep-alive',
                'x-amzn-requestid': '21099462-597c-490a-800f-8b7a41e5151c'
            },
            'RetryAttempts': 0
        }
    }
    lookup = lookup_loader.get('amazon.aws.aws_secret')
    boto3_double = mocker.MagicMock()
    boto3_double.Session.return_value.client.return_value.get_secret_value.return_value = simple_variable_success_response
    boto3_client_double = boto3_double.Session.return_value.client

    mocker.patch.object(boto3, 'session', boto3_double)
    retval = lookup.run(["simple_variable"], None, **dummy_credentials)
    assert(retval[0] == '{"secret":"simplesecret"}')
    boto3_client_double.assert_called_with('secretsmanager', 'eu-west-1', aws_access_key_id='notakey',
                                           aws_secret_access_key="notasecret", aws_session_token=None)


error_response_missing = {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Fake Not Found Error'}}
error_response_denied = {'Error': {'Code': 'AccessDeniedException', 'Message': 'Fake Denied Error'}}
operation_name = 'FakeOperation'


def test_on_missing_option(mocker, dummy_credentials):
    boto3_double = mocker.MagicMock()
    boto3_double.Session.return_value.client.return_value.get_secret_value.side_effect = ClientError(error_response_missing, operation_name)

    with pytest.raises(AnsibleError, match="ResourceNotFound"):
        mocker.patch.object(boto3, 'session', boto3_double)
        lookup_loader.get('amazon.aws.aws_secret').run(["missing_secret"], None, **dummy_credentials)

    mocker.patch.object(boto3, 'session', boto3_double)
    args = copy(dummy_credentials)
    args["on_missing"] = 'skip'
    retval = lookup_loader.get('amazon.aws.aws_secret').run(["missing_secret"], None, **args)
    assert(retval == [])

    mocker.patch.object(boto3, 'session', boto3_double)
    args = copy(dummy_credentials)
    args["on_missing"] = 'warn'
    retval = lookup_loader.get('amazon.aws.aws_secret').run(["missing_secret"], None, **args)
    assert(retval == [])


def test_on_denied_option(mocker, dummy_credentials):
    boto3_double = mocker.MagicMock()
    boto3_double.Session.return_value.client.return_value.get_secret_value.side_effect = ClientError(error_response_denied, operation_name)

    with pytest.raises(AnsibleError, match="AccessDenied"):
        mocker.patch.object(boto3, 'session', boto3_double)
        lookup_loader.get('amazon.aws.aws_secret').run(["denied_secret"], None, **dummy_credentials)

    mocker.patch.object(boto3, 'session', boto3_double)
    args = copy(dummy_credentials)
    args["on_denied"] = 'skip'
    retval = lookup_loader.get('amazon.aws.aws_secret').run(["denied_secret"], None, **args)
    assert(retval == [])

    mocker.patch.object(boto3, 'session', boto3_double)
    args = copy(dummy_credentials)
    args["on_denied"] = 'warn'
    retval = lookup_loader.get('amazon.aws.aws_secret').run(["denied_secret"], None, **args)
    assert(retval == [])
