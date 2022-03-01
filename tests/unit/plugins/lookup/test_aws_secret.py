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
from copy import copy

from ansible.errors import AnsibleError
from ansible.plugins.loader import lookup_loader

from ansible_collections.amazon.aws.plugins.lookup import aws_secret

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


simple_variable_success_response = {
    'Name': 'secret',
    'VersionId': 'cafe8168-e6ce-4e59-8830-5b143faf6c52',
    'SecretString': '{"secret":"simplesecret"}',
    'VersionStages': ['AWSCURRENT'],
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


def test_lookup_variable(mocker, dummy_credentials):
    dateutil_tz = pytest.importorskip("dateutil.tz")
    lookup = lookup_loader.get('amazon.aws.aws_secret')
    boto3_double = mocker.MagicMock()
    boto3_double.Session.return_value.client.return_value.get_secret_value.return_value = copy(
        simple_variable_success_response)
    boto3_client_double = boto3_double.Session.return_value.client

    mocker.patch.object(boto3, 'session', boto3_double)
    retval = lookup.run(["simple_variable"], None, **dummy_credentials)
    assert (retval[0] == '{"secret":"simplesecret"}')
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


def test_nested_lookup_variable(mocker, dummy_credentials):
    dateutil_tz = pytest.importorskip("dateutil.tz")
    simple_variable_success_response = {
        'Name': 'simple_variable',
        'VersionId': 'cafe8168-e6ce-4e59-8830-5b143faf6c52',
        'SecretString': '{"key1": {"key2": {"key3": 1 } } }',
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
    dummy_credentials["nested"] = 'true'
    retval = lookup.run(["simple_variable.key1.key2.key3"], None, **dummy_credentials)
    assert(retval[0] == '1')
    boto3_client_double.assert_called_with('secretsmanager', 'eu-west-1', aws_access_key_id='notakey',
                                           aws_secret_access_key="notasecret", aws_session_token=None)


def test_path_lookup_variable(mocker, dummy_credentials, record_property):
    lookup = aws_secret.LookupModule()
    lookup._load_name = "aws_secret"

    path_list_secrets_success_response = {
        'SecretList': [
            {
                'Name': '/testpath/too',
            },
            {
                'Name': '/testpath/won',
            }
        ],
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

    boto3_double = mocker.MagicMock()
    list_secrets_fn = boto3_double.Session.return_value.client.return_value.list_secrets
    list_secrets_fn.return_value = path_list_secrets_success_response

    get_secret_value_fn = boto3_double.Session.return_value.client.return_value.get_secret_value
    first_path = copy(simple_variable_success_response)
    first_path['SecretString'] = 'simple_value_too'
    second_path = copy(simple_variable_success_response)
    second_path['SecretString'] = 'simple_value_won'
    get_secret_value_fn.side_effect = [
        first_path,
        second_path
    ]

    boto3_client_double = boto3_double.Session.return_value.client
    boto3_client_get_paginator_double = boto3_double.Session.return_value.client.return_value.get_paginator
    boto3_paginate_double = boto3_client_get_paginator_double.return_value.paginate
    boto3_paginate_double.return_value = [path_list_secrets_success_response]

    mocker.patch.object(boto3, 'session', boto3_double)
    dummy_credentials["bypath"] = 'true'
    dummy_credentials["boto_profile"] = 'test'
    dummy_credentials["aws_profile"] = 'test'
    retval = lookup.run(["/testpath"], {}, **dummy_credentials)
    boto3_paginate_double.assert_called_once()
    boto3_client_get_paginator_double.assert_called_once()
    boto3_client_get_paginator_double.assert_called_once_with('list_secrets')

    record_property('KEY', retval)
    assert (retval[0]["/testpath/won"] == "simple_value_won")
    assert (retval[0]["/testpath/too"] == "simple_value_too")
    boto3_client_double.assert_called_with('secretsmanager', 'eu-west-1', aws_access_key_id='notakey',
                                           aws_secret_access_key="notasecret", aws_session_token=None)
    boto3_paginate_double.assert_called_with(Filters=[{'Key': 'name', 'Values': ['/testpath']}])


def test_path_lookup_variable_paginated(mocker, dummy_credentials, record_property):
    lookup = aws_secret.LookupModule()
    lookup._load_name = "aws_secret"

    def secret(value):
        return {"Name": f"/testpath_paginated/{value}"}

    def get_secret_list(value):
        return [secret(f"{value}{i}") for i in range(0, 6)]
    path_list_secrets_paginated_success_response = {
        'SecretList': [
            item for pair in zip(get_secret_list("too"), get_secret_list("won")) for item in pair
        ],
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
    boto3_double = mocker.MagicMock()
    list_secrets_fn = boto3_double.Session.return_value.client.return_value.list_secrets
    list_secrets_fn.return_value = path_list_secrets_paginated_success_response
    get_secret_value_fn = boto3_double.Session.return_value.client.return_value.get_secret_value

    def secret_string(val):
        path = copy(simple_variable_success_response)
        path["SecretString"] = f"simple_value_{val}"
        return path

    def _get_secret_list(value):
        return [secret_string(f"{value}{i}") for i in range(0, 6)]
    get_secret_value_fn.side_effect = [
        item for pair in zip(_get_secret_list("too"), _get_secret_list("won")) for item in pair
    ]
    boto3_client_double = boto3_double.Session.return_value.client
    boto3_client_get_paginator_double = boto3_double.Session.return_value.client.return_value.get_paginator
    boto3_paginate_double = boto3_client_get_paginator_double.return_value.paginate
    boto3_paginate_double.return_value = [path_list_secrets_paginated_success_response]
    mocker.patch.object(boto3, 'session', boto3_double)
    dummy_credentials["bypath"] = 'true'
    dummy_credentials["boto_profile"] = 'test'
    dummy_credentials["aws_profile"] = 'test'
    retval = lookup.run(["/testpath_paginated"], {}, **dummy_credentials)
    boto3_paginate_double.assert_called_once()
    boto3_client_get_paginator_double.assert_called_once()
    boto3_client_get_paginator_double.assert_called_once_with('list_secrets')
    record_property('KEY', retval)
    assert (retval[0]["/testpath_paginated/won0"] == "simple_value_won0")
    assert (retval[0]["/testpath_paginated/too0"] == "simple_value_too0")
    assert (len(retval[0]) == 12)
    boto3_client_double.assert_called_with('secretsmanager', 'eu-west-1', aws_access_key_id='notakey',
                                           aws_secret_access_key="notasecret", aws_session_token=None)
    boto3_paginate_double.assert_called_with(Filters=[{'Key': 'name', 'Values': ['/testpath_paginated']}])
