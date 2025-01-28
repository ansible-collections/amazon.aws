#
# (c) 2024 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import patch

from ansible_collections.amazon.aws.plugins.module_utils import transformation

filters = {
    "tag:Test_Name": "ansible-test-units",
    "ansible_test_version": "milestone",
}

expected_no_ignore_keys = {
    "tag:Test-Name": "ansible-test-units",
    "ansible-test-version": "milestone",
}

expected_ignore_keys = {
    "tag:Test_Name": "ansible-test-units",
    "ansible-test-version": "milestone",
}


@patch("ansible_collections.amazon.aws.plugins.module_utils.transformation.ansible_dict_to_boto3_filter_list")
def test_sanitize_filters_to_boto3_filter_list_no_ignore_keys(m_ansible_dict_to_boto3_filter_list):
    m_ansible_dict_to_boto3_filter_list.side_effect = lambda x: x
    assert expected_no_ignore_keys == transformation.sanitize_filters_to_boto3_filter_list(filters)


@patch("ansible_collections.amazon.aws.plugins.module_utils.transformation.ansible_dict_to_boto3_filter_list")
def test_sanitize_filters_to_boto3_filter_list_ignore_keys(m_ansible_dict_to_boto3_filter_list):
    m_ansible_dict_to_boto3_filter_list.side_effect = lambda x: x
    assert expected_ignore_keys == transformation.sanitize_filters_to_boto3_filter_list(filters, ignore_keys=["tag:"])
