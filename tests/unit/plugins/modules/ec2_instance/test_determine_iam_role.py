# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import sys

from ansible_collections.amazon.aws.tests.unit.compat.mock import MagicMock
from ansible_collections.amazon.aws.tests.unit.compat.mock import sentinel
import ansible_collections.amazon.aws.plugins.modules.ec2_instance as ec2_instance_module
import ansible_collections.amazon.aws.plugins.module_utils.arn as utils_arn
from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3

try:
    import botocore
except ImportError:
    pass

pytest.mark.skipif(not HAS_BOTO3, reason="test_determine_iam_role.py requires the python modules 'boto3' and 'botocore'")


def _client_error(code='GenericError'):
    return botocore.exceptions.ClientError(
        {'Error': {'Code': code, 'Message': 'Something went wrong'},
         'ResponseMetadata': {'RequestId': '01234567-89ab-cdef-0123-456789abcdef'}},
        'some_called_method')


@pytest.fixture
def params_object():
    params = {
        'instance_role': None,
        'exact_count': None,
        'count': None,
        'launch_template': None,
        'instance_type': None,
    }
    return params


class FailJsonException(Exception):
    def __init__(self):
        pass


@pytest.fixture
def ec2_instance(monkeypatch):
    monkeypatch.setattr(ec2_instance_module, 'parse_aws_arn', lambda arn: None)
    monkeypatch.setattr(ec2_instance_module, 'module', MagicMock())
    ec2_instance_module.module.fail_json.side_effect = FailJsonException()
    ec2_instance_module.module.fail_json_aws.side_effect = FailJsonException()
    return ec2_instance_module


def test_determine_iam_role_arn(params_object, ec2_instance, monkeypatch):
    # Revert the default monkey patch to make it simple to try passing a valid ARNs
    monkeypatch.setattr(ec2_instance, 'parse_aws_arn', utils_arn.parse_aws_arn)

    # Simplest example, someone passes a valid instance profile ARN
    arn = ec2_instance.determine_iam_role('arn:aws:iam::123456789012:instance-profile/myprofile')
    assert arn == 'arn:aws:iam::123456789012:instance-profile/myprofile'


def test_determine_iam_role_name(params_object, ec2_instance):
    profile_description = {'InstanceProfile': {'Arn': sentinel.IAM_PROFILE_ARN}}
    iam_client = MagicMock(**{"get_instance_profile.return_value": profile_description})
    ec2_instance_module.module.client.return_value = iam_client

    arn = ec2_instance.determine_iam_role(sentinel.IAM_PROFILE_NAME)
    assert arn == sentinel.IAM_PROFILE_ARN


def test_determine_iam_role_missing(params_object, ec2_instance):
    missing_exception = _client_error('NoSuchEntity')
    iam_client = MagicMock(**{"get_instance_profile.side_effect": missing_exception})
    ec2_instance_module.module.client.return_value = iam_client

    with pytest.raises(FailJsonException) as exception:
        arn = ec2_instance.determine_iam_role(sentinel.IAM_PROFILE_NAME)

    assert ec2_instance_module.module.fail_json_aws.call_count == 1
    assert ec2_instance_module.module.fail_json_aws.call_args.args[0] is missing_exception
    assert 'Could not find' in ec2_instance_module.module.fail_json_aws.call_args.kwargs['msg']


@pytest.mark.skipif(sys.version_info < (3, 8), reason='call_args behaviour changed in Python 3.8')
def test_determine_iam_role_missing(params_object, ec2_instance):
    missing_exception = _client_error()
    iam_client = MagicMock(**{"get_instance_profile.side_effect": missing_exception})
    ec2_instance_module.module.client.return_value = iam_client

    with pytest.raises(FailJsonException) as exception:
        arn = ec2_instance.determine_iam_role(sentinel.IAM_PROFILE_NAME)

    assert ec2_instance_module.module.fail_json_aws.call_count == 1
    assert ec2_instance_module.module.fail_json_aws.call_args.args[0] is missing_exception
    assert 'An error occurred while searching' in ec2_instance_module.module.fail_json_aws.call_args.kwargs['msg']
    assert 'Please try supplying the full ARN' in ec2_instance_module.module.fail_json_aws.call_args.kwargs['msg']
