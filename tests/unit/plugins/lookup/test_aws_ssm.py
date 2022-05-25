#
# (c) 2017 Michael De La Rue
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
from unittest.mock import ANY
from copy import copy

from ansible.errors import AnsibleError

from ansible_collections.amazon.aws.plugins.lookup import aws_ssm

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    pytestmark = pytest.mark.skip("This test requires the boto3 and botocore Python libraries")

simple_variable_success_response = {
    'Parameter': {
        'Name': 'simple_variable',
        'Type': 'String',
        'Value': 'simplevalue',
        'Version': 1
    },
    'ResponseMetadata': {
        'RequestId': '12121212-3434-5656-7878-9a9a9a9a9a9a',
        'HTTPStatusCode': 200,
        'HTTPHeaders': {
            'x-amzn-requestid': '12121212-3434-5656-7878-9a9a9a9a9a9a',
            'content-type': 'application/x-amz-json-1.1',
            'content-length': '116',
            'date': 'Tue, 23 Jan 2018 11:04:27 GMT'
        },
        'RetryAttempts': 0
    }
}

path_success_response = copy(simple_variable_success_response)
path_success_response['Parameters'] = [
    {'Name': '/testpath/too', 'Type': 'String', 'Value': 'simple_value_too', 'Version': 1},
    {'Name': '/testpath/won', 'Type': 'String', 'Value': 'simple_value_won', 'Version': 1}
]

simple_response = copy(simple_variable_success_response)
simple_response['Parameter'] = {
    'Name': 'simple',
    'Type': 'String',
    'Value': 'simple_value',
    'Version': 1
}

simple_won_response = copy(simple_variable_success_response)
simple_won_response['Parameter'] = {
    'Name': '/testpath/won',
    'Type': 'String',
    'Value': 'simple_value_won',
    'Version': 1
}

dummy_credentials = {}
dummy_credentials['boto_profile'] = None
dummy_credentials['aws_secret_key'] = "notasecret"
dummy_credentials['aws_access_key'] = "notakey"
dummy_credentials['aws_security_token'] = None
dummy_credentials['region'] = 'eu-west-1'


def mock_get_parameter(**kwargs):
    if kwargs.get('Name') == 'simple':
        return simple_response
    elif kwargs.get('Name') == '/testpath/won':
        return simple_won_response
    elif kwargs.get('Name') == 'missing_variable':
        warn_response = {'Error': {'Code': 'ParameterNotFound', 'Message': 'Parameter not found'}}
        operation_name = 'FakeOperation'
        raise ClientError(warn_response, operation_name)
    elif kwargs.get('Name') == 'denied_variable':
        error_response = {'Error': {'Code': 'AccessDeniedException', 'Message': 'Fake Testing Error'}}
        operation_name = 'FakeOperation'
        raise ClientError(error_response, operation_name)
    elif kwargs.get('Name') == 'notfound_variable':
        error_response = {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Fake Testing Error'}}
        operation_name = 'FakeOperation'
        raise ClientError(error_response, operation_name)
    else:
        warn_response = {'Error': {'Code': 'ParameterNotFound', 'Message': 'Parameter not found'}}
        operation_name = 'FakeOperation'
        raise ClientError(warn_response, operation_name)


def test_lookup_variable(mocker):
    lookup = aws_ssm.LookupModule()
    lookup._load_name = "aws_ssm"

    boto3_double = mocker.MagicMock()
    boto3_double.Session.return_value.client.return_value.get_parameter.return_value = simple_variable_success_response
    boto3_client_double = boto3_double.Session.return_value.client

    mocker.patch.object(boto3, 'session', boto3_double)
    retval = lookup.run(["simple_variable"], {}, **dummy_credentials)
    assert(isinstance(retval, list))
    assert(len(retval) == 1)
    assert(retval[0] == "simplevalue")
    boto3_client_double.assert_called_with(
        'ssm',
        region_name='eu-west-1',
        aws_access_key_id='notakey',
        aws_secret_access_key="notasecret",
        aws_session_token=None,
        endpoint_url=None,
        config=ANY,
        verify=None,
    )


def test_path_lookup_variable(mocker):
    lookup = aws_ssm.LookupModule()
    lookup._load_name = "aws_ssm"

    boto3_double = mocker.MagicMock()
    get_paginator_fn = boto3_double.Session.return_value.client.return_value.get_paginator
    paginator = get_paginator_fn.return_value
    paginator.paginate.return_value.build_full_result.return_value = path_success_response
    boto3_client_double = boto3_double.Session.return_value.client

    mocker.patch.object(boto3, 'session', boto3_double)
    args = copy(dummy_credentials)
    args["bypath"] = True
    args["recursive"] = True
    retval = lookup.run(["/testpath"], {}, **args)
    assert(retval[0]["/testpath/won"] == "simple_value_won")
    assert(retval[0]["/testpath/too"] == "simple_value_too")
    boto3_client_double.assert_called_with(
        'ssm',
        region_name='eu-west-1',
        aws_access_key_id='notakey',
        aws_secret_access_key="notasecret",
        aws_session_token=None,
        endpoint_url=None,
        config=ANY,
        verify=None,
    )
    get_paginator_fn.assert_called_with('get_parameters_by_path')
    paginator.paginate.assert_called_with(Path="/testpath", Recursive=True, WithDecryption=True)
    paginator.paginate.return_value.build_full_result.assert_called_with()


def test_warn_on_missing_match_retvals_to_call_params_with_some_missing_variables(mocker):
    """If we get a complex list of variables with some missing and some
    not, and on_missing is warn, we still have to return a list which
    matches with the original variable list.

    """
    lookup = aws_ssm.LookupModule()
    lookup._load_name = "aws_ssm"

    boto3_double = mocker.MagicMock()

    boto3_double.Session.return_value.client.return_value.get_parameter.side_effect = mock_get_parameter

    mocker.patch.object(boto3, 'session', boto3_double)
    args = copy(dummy_credentials)
    args["on_missing"] = 'warn'
    retval = lookup.run(["simple", "missing_variable", "/testpath/won", "simple"], {}, **args)
    assert(isinstance(retval, list))
    assert(retval == ["simple_value", None, "simple_value_won", "simple_value"])


def test_skip_on_missing_match_retvals_to_call_params_with_some_missing_variables(mocker):
    """If we get a complex list of variables with some missing and some
    not, and on_missing is skip, we still have to return a list which
    matches with the original variable list.

    """
    lookup = aws_ssm.LookupModule()
    lookup._load_name = "aws_ssm"

    boto3_double = mocker.MagicMock()

    boto3_double.Session.return_value.client.return_value.get_parameter.side_effect = mock_get_parameter

    mocker.patch.object(boto3, 'session', boto3_double)
    args = copy(dummy_credentials)
    args["on_missing"] = 'skip'
    retval = lookup.run(["simple", "missing_variable", "/testpath/won", "simple"], {}, **args)
    assert(isinstance(retval, list))
    assert(retval == ["simple_value", None, "simple_value_won", "simple_value"])


def test_warn_notfound_resource(mocker):
    lookup = aws_ssm.LookupModule()
    lookup._load_name = "aws_ssm"

    boto3_double = mocker.MagicMock()
    boto3_double.Session.return_value.client.return_value.get_parameter.side_effect = mock_get_parameter

    with pytest.raises(AnsibleError):
        mocker.patch.object(boto3, 'session', boto3_double)
        lookup.run(["notfound_variable"], {}, **dummy_credentials)


def test_on_missing_wrong_value(mocker):
    lookup = aws_ssm.LookupModule()
    lookup._load_name = "aws_ssm"

    boto3_double = mocker.MagicMock()
    boto3_double.Session.return_value.client.return_value.get_parameter.side_effect = mock_get_parameter

    with pytest.raises(AnsibleError) as exc:
        missing_credentials = copy(dummy_credentials)
        missing_credentials['on_missing'] = "fake_value_on_missing"
        mocker.patch.object(boto3, 'session', boto3_double)
        lookup.run(["simple"], {}, **missing_credentials)

    assert exc.match('"on_missing" must be a string and one of "error", "warn" or "skip"')


def test_error_on_missing_variable(mocker):
    lookup = aws_ssm.LookupModule()
    lookup._load_name = "aws_ssm"

    boto3_double = mocker.MagicMock()
    boto3_double.Session.return_value.client.return_value.get_parameter.side_effect = mock_get_parameter

    with pytest.raises(AnsibleError) as exc:
        missing_credentials = copy(dummy_credentials)
        missing_credentials['on_missing'] = "error"
        mocker.patch.object(boto3, 'session', boto3_double)
        lookup.run(["missing_variable"], {}, **missing_credentials)

    assert exc.match(r"Failed to find SSM parameter missing_variable \(ResourceNotFound\)")


def test_warn_on_missing_variable(mocker):
    lookup = aws_ssm.LookupModule()
    lookup._load_name = "aws_ssm"

    boto3_double = mocker.MagicMock()
    boto3_double.Session.return_value.client.return_value.get_parameter.side_effect = mock_get_parameter

    missing_credentials = copy(dummy_credentials)
    missing_credentials['on_missing'] = "warn"
    mocker.patch.object(boto3, 'session', boto3_double)
    retval = lookup.run(["missing_variable"], {}, **missing_credentials)
    assert(isinstance(retval, list))
    assert(retval[0] is None)


def test_skip_on_missing_variable(mocker):
    lookup = aws_ssm.LookupModule()
    lookup._load_name = "aws_ssm"

    boto3_double = mocker.MagicMock()
    boto3_double.Session.return_value.client.return_value.get_parameter.side_effect = mock_get_parameter

    missing_credentials = copy(dummy_credentials)
    missing_credentials['on_missing'] = "skip"
    mocker.patch.object(boto3, 'session', boto3_double)
    retval = lookup.run(["missing_variable"], {}, **missing_credentials)
    assert(isinstance(retval, list))
    assert(retval[0] is None)


def test_on_denied_wrong_value(mocker):
    lookup = aws_ssm.LookupModule()
    lookup._load_name = "aws_ssm"

    boto3_double = mocker.MagicMock()
    boto3_double.Session.return_value.client.return_value.get_parameter.side_effect = mock_get_parameter

    with pytest.raises(AnsibleError) as exc:
        denied_credentials = copy(dummy_credentials)
        denied_credentials['on_denied'] = "fake_value_on_denied"
        mocker.patch.object(boto3, 'session', boto3_double)
        lookup.run(["simple"], {}, **denied_credentials)

    assert exc.match('"on_denied" must be a string and one of "error", "warn" or "skip"')


def test_error_on_denied_variable(mocker):
    lookup = aws_ssm.LookupModule()
    lookup._load_name = "aws_ssm"

    boto3_double = mocker.MagicMock()
    boto3_double.Session.return_value.client.return_value.get_parameter.side_effect = mock_get_parameter

    with pytest.raises(AnsibleError) as exc:
        denied_credentials = copy(dummy_credentials)
        denied_credentials['on_denied'] = "error"
        mocker.patch.object(boto3, 'session', boto3_double)
        lookup.run(["denied_variable"], {}, **denied_credentials)
    assert exc.match(r"Failed to access SSM parameter denied_variable \(AccessDenied\)")


def test_warn_on_denied_variable(mocker):
    lookup = aws_ssm.LookupModule()
    lookup._load_name = "aws_ssm"

    boto3_double = mocker.MagicMock()
    boto3_double.Session.return_value.client.return_value.get_parameter.side_effect = mock_get_parameter

    denied_credentials = copy(dummy_credentials)
    denied_credentials['on_denied'] = "warn"
    mocker.patch.object(boto3, 'session', boto3_double)
    retval = lookup.run(["denied_variable"], {}, **denied_credentials)
    assert(isinstance(retval, list))
    assert(retval[0] is None)


def test_skip_on_denied_variable(mocker):
    lookup = aws_ssm.LookupModule()
    lookup._load_name = "aws_ssm"

    boto3_double = mocker.MagicMock()
    boto3_double.Session.return_value.client.return_value.get_parameter.side_effect = mock_get_parameter

    denied_credentials = copy(dummy_credentials)
    denied_credentials['on_denied'] = "skip"
    mocker.patch.object(boto3, 'session', boto3_double)
    retval = lookup.run(["denied_variable"], {}, **denied_credentials)
    assert(isinstance(retval, list))
    assert(retval[0] is None)
