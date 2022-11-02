# (c) 2022 Red Hat Inc.

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock, patch, ANY
import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_eni_info

module_name = "ansible_collections.amazon.aws.plugins.modules.ec2_eni_info"


@pytest.mark.parametrize("eni_id,filters,expected", [('', {}, {}), ('eni-1234567890', {}, {'NetworkInterfaceIds': ['eni-1234567890']})])
def test_build_request_args(eni_id, filters, expected):
    assert ec2_eni_info.build_request_args(eni_id, filters) == expected


@patch(module_name + ".AnsibleAWSModule")
def test_main_success(m_AnsibleAWSModule):
    m_module = MagicMock()
    m_AnsibleAWSModule.return_value = m_module

    ec2_eni_info.main()

    m_module.client.assert_called_with("ec2", retry_decorator=ANY)
