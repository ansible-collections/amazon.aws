# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import sentinel

import botocore
import pytest

import ansible_collections.amazon.aws.plugins.module_utils.s3 as s3_utils
from ansible_collections.amazon.aws.plugins.modules.s3_bucket import handle_bucket_accelerate

SKIPABLE_ERRORS = [
    ("NotImplemented", "Fetching bucket transfer acceleration state is not supported", s3_utils.AnsibleS3SupportError),
    ("XNotImplemented", "Fetching bucket transfer acceleration state is not supported", s3_utils.AnsibleS3SupportError),
    ("UnsupportedArgument", "Argument not supported in the current Region", s3_utils.AnsibleS3RegionSupportError),
    ("AccessDenied", "Permission denied fetching transfer acceleration for bucket", s3_utils.AnsibleS3PermissionsError),
]

BAD_ERRORS = [
    ("GenericBadClientError", "Failed to fetch bucket transfer acceleration state", s3_utils.AnsibleS3Error),
]


def a_botocore_exception(code, message):
    return botocore.exceptions.ClientError({"Error": {"Code": code, "Message": message}}, sentinel.BOTOCORE_ACTION)


@pytest.fixture(name="ansible_module")
def fixure_ansible_module():
    mock = MagicMock()
    mock.params = {"accelerate_enabled": sentinel.ACCELERATE_ENABLED}
    mock.fail_json_aws.side_effect = SystemExit(1)
    mock.fail_json.side_effect = SystemExit(1)
    return mock


# Test that we fail "gracefully" if we don't support bucket acceleration
@pytest.mark.parametrize("code,message,exception", [*BAD_ERRORS, *SKIPABLE_ERRORS])
def test_failure(ansible_module, code, message, exception):
    bucket_name = sentinel.BUCKET_NAME
    exc = a_botocore_exception(code, message)
    client = MagicMock()
    client.get_bucket_accelerate_configuration.side_effect = exc
    with pytest.raises(exception):
        handle_bucket_accelerate(client, ansible_module, bucket_name)


# Test that we only emit a warning if we don't support bucket acceleration but aren't trying to
# manage the acceleration configuration
@pytest.mark.parametrize("code,message,exception", SKIPABLE_ERRORS)
def test_no_argument(ansible_module, code, message, exception):
    bucket_name = sentinel.BUCKET_NAME
    exc = a_botocore_exception(code, message)
    client = MagicMock()
    client.get_bucket_accelerate_configuration.side_effect = exc

    ansible_module.params["accelerate_enabled"] = None
    changed, result = handle_bucket_accelerate(client, ansible_module, bucket_name)
    assert changed is False
    assert result is None
    ansible_module.warn.assert_called_once()


# Test that we're not being "too" relaxed with our handling, we should only be ignoring errors
# caused by a total lack of support from the platform
@pytest.mark.parametrize("code,message,exception", BAD_ERRORS)
def test_no_argument_fatal(ansible_module, code, message, exception):
    bucket_name = sentinel.BUCKET_NAME
    exc = a_botocore_exception(code, message)
    client = MagicMock()
    client.get_bucket_accelerate_configuration.side_effect = exc

    ansible_module.params["accelerate_enabled"] = None
    with pytest.raises(exception):
        handle_bucket_accelerate(client, ansible_module, bucket_name)
