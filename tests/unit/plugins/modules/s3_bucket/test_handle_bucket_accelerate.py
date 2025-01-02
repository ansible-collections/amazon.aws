# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import sentinel

import botocore
import pytest

from ansible_collections.amazon.aws.plugins.modules.s3_bucket import handle_bucket_accelerate

module_name = "ansible_collections.amazon.aws.plugins.modules.s3_bucket"


def a_botocore_exception(message):
    return botocore.exceptions.ClientError({"Error": {"Code": message}}, sentinel.BOTOCORE_ACTION)


@pytest.fixture(name="ansible_module")
def fixure_ansible_module():
    mock = MagicMock()
    mock.params = {"accelerate_enabled": sentinel.ACCELERATE_ENABLED}
    mock.fail_json_aws.side_effect = SystemExit(1)
    return mock


@pytest.mark.parametrize(
    "code,message",
    [
        ("NotImplemented", "Fetching bucket transfer acceleration state is not supported"),
        ("XNotImplemented", "Fetching bucket transfer acceleration state is not supported"),
        ("AccessDenied", "Permission denied fetching transfer acceleration for bucket"),
        (sentinel.BOTO_CLIENT_ERROR, "Failed to fetch bucket transfer acceleration state"),
    ],
)
@patch(module_name + ".get_bucket_accelerate_status")
def test_failure(m_get_bucket_accelerate_status, ansible_module, code, message):
    bucket_name = sentinel.BUCKET_NAME
    client = MagicMock()
    exc = a_botocore_exception(code)
    m_get_bucket_accelerate_status.side_effect = exc
    with pytest.raises(SystemExit):
        handle_bucket_accelerate(client, ansible_module, bucket_name)
    ansible_module.fail_json_aws.assert_called_once_with(exc, msg=message)


@patch(module_name + ".get_bucket_accelerate_status")
def test_unsupported(m_get_bucket_accelerate_status, ansible_module):
    bucket_name = sentinel.BUCKET_NAME
    client = MagicMock()
    m_get_bucket_accelerate_status.side_effect = a_botocore_exception("UnsupportedArgument")
    changed, result = handle_bucket_accelerate(client, ansible_module, bucket_name)
    assert changed is False
    assert result is False
    ansible_module.warn.assert_called_once()


@pytest.mark.parametrize("accelerate_enabled", [True, False])
@patch(module_name + ".delete_bucket_accelerate_configuration")
@patch(module_name + ".get_bucket_accelerate_status")
def test_delete(
    m_get_bucket_accelerate_status, m_delete_bucket_accelerate_configuration, ansible_module, accelerate_enabled
):
    bucket_name = sentinel.BUCKET_NAME
    client = MagicMock()
    ansible_module.params.update({"accelerate_enabled": accelerate_enabled})
    m_get_bucket_accelerate_status.return_value = True
    if not accelerate_enabled:
        assert (True, False) == handle_bucket_accelerate(client, ansible_module, bucket_name)
        m_delete_bucket_accelerate_configuration.assert_called_once_with(client, bucket_name)
    else:
        assert (False, True) == handle_bucket_accelerate(client, ansible_module, bucket_name)
        m_delete_bucket_accelerate_configuration.assert_not_called()


@pytest.mark.parametrize("accelerate_enabled", [True, False])
@patch(module_name + ".put_bucket_accelerate_configuration")
@patch(module_name + ".get_bucket_accelerate_status")
def test_put(m_get_bucket_accelerate_status, m_put_bucket_accelerate_configuration, ansible_module, accelerate_enabled):
    bucket_name = sentinel.BUCKET_NAME
    client = MagicMock()
    ansible_module.params.update({"accelerate_enabled": accelerate_enabled})
    m_get_bucket_accelerate_status.return_value = False
    if accelerate_enabled:
        assert (True, True) == handle_bucket_accelerate(client, ansible_module, bucket_name)
        m_put_bucket_accelerate_configuration.assert_called_once_with(client, bucket_name)
    else:
        assert (False, False) == handle_bucket_accelerate(client, ansible_module, bucket_name)
        m_put_bucket_accelerate_configuration.assert_not_called()
