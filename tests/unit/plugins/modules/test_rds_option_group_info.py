# (c) 2026 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

from ansible_collections.amazon.aws.plugins.module_utils.rds import AnsibleRDSError
from ansible_collections.amazon.aws.plugins.modules import rds_option_group_info
from ansible_collections.amazon.aws.plugins.modules.rds_option_group_info import option_group_info

mod_name = "ansible_collections.amazon.aws.plugins.modules.rds_option_group_info"


@patch(mod_name + ".get_tags")
@patch(mod_name + ".describe_option_groups")
def test_option_group_info_by_name(m_describe, m_get_tags):
    conn = MagicMock()
    module = MagicMock()
    m_describe.return_value = [
        {
            "OptionGroupName": "test-og",
            "OptionGroupArn": "arn:aws:rds:us-east-1:123456789012:og:test-og",
            "EngineName": "mysql",
            "MajorEngineVersion": "8.0",
            "OptionGroupDescription": "test option group",
            "Options": [],
        }
    ]
    m_get_tags.return_value = {"Name": "test"}

    result = option_group_info(
        conn, module, option_group_name="test-og", engine_name="", major_engine_version="", marker=None, max_records=100
    )

    assert len(result) == 1
    assert result[0]["option_group_name"] == "test-og"
    assert result[0]["engine_name"] == "mysql"
    assert result[0]["tags"] == {"Name": "test"}
    m_describe.assert_called_with(conn, OptionGroupName="test-og", MaxRecords=100)
    m_get_tags.assert_called_once_with(conn, module, "arn:aws:rds:us-east-1:123456789012:og:test-og")


@patch(mod_name + ".get_tags")
@patch(mod_name + ".describe_option_groups")
def test_option_group_info_by_engine(m_describe, m_get_tags):
    conn = MagicMock()
    module = MagicMock()
    m_describe.return_value = [
        {
            "OptionGroupName": "og-1",
            "OptionGroupArn": "arn:aws:rds:us-east-1:123456789012:og:og-1",
            "EngineName": "mysql",
            "MajorEngineVersion": "8.0",
            "OptionGroupDescription": "og 1",
            "Options": [],
        },
        {
            "OptionGroupName": "og-2",
            "OptionGroupArn": "arn:aws:rds:us-east-1:123456789012:og:og-2",
            "EngineName": "mysql",
            "MajorEngineVersion": "8.0",
            "OptionGroupDescription": "og 2",
            "Options": [],
        },
    ]
    m_get_tags.return_value = {}

    result = option_group_info(
        conn, module, option_group_name="", engine_name="mysql", major_engine_version="8.0", marker=None, max_records=100
    )

    assert len(result) == 2
    assert result[0]["option_group_name"] == "og-1"
    assert result[1]["option_group_name"] == "og-2"
    m_describe.assert_called_with(conn, EngineName="mysql", MajorEngineVersion="8.0", MaxRecords=100)
    assert m_get_tags.call_count == 2


@patch(mod_name + ".get_tags")
@patch(mod_name + ".describe_option_groups")
def test_option_group_info_no_results(m_describe, m_get_tags):
    conn = MagicMock()
    module = MagicMock()
    m_describe.return_value = []

    result = option_group_info(
        conn, module, option_group_name="nonexistent", engine_name="", major_engine_version="", marker=None, max_records=100
    )

    assert result == []
    m_get_tags.assert_not_called()


@patch(mod_name + ".describe_option_groups")
def test_option_group_info_max_records_too_high(m_describe):
    conn = MagicMock()
    module = MagicMock()
    module.fail_json.side_effect = SystemExit(1)

    try:
        option_group_info(
            conn, module, option_group_name="", engine_name="", major_engine_version="", marker=None, max_records=101
        )
    except SystemExit:
        pass

    module.fail_json.assert_called_once_with(
        msg="The maximum number of records to include in the response must be between 20 and 100."
    )
    m_describe.assert_not_called()


@patch(mod_name + ".describe_option_groups")
def test_option_group_info_max_records_too_low(m_describe):
    conn = MagicMock()
    module = MagicMock()
    module.fail_json.side_effect = SystemExit(1)

    try:
        option_group_info(
            conn, module, option_group_name="", engine_name="", major_engine_version="", marker=None, max_records=19
        )
    except SystemExit:
        pass

    module.fail_json.assert_called_once_with(
        msg="The maximum number of records to include in the response must be between 20 and 100."
    )
    m_describe.assert_not_called()


@patch(mod_name + ".AnsibleAWSModule")
def test_main_success(m_AnsibleAWSModule):
    m_module = MagicMock()
    m_AnsibleAWSModule.return_value = m_module
    m_module.params = {
        "option_group_name": "",
        "engine_name": "",
        "major_engine_version": "",
        "marker": None,
        "max_records": 100,
    }

    rds_option_group_info.main()

    m_module.client.assert_called_with("rds")
    call_kwargs = m_module.exit_json.call_args[1]
    assert call_kwargs["changed"] is False
    assert "result" in call_kwargs


@patch(mod_name + ".describe_option_groups")
@patch(mod_name + ".AnsibleAWSModule")
def test_main_failure(m_AnsibleAWSModule, m_describe):
    m_module = MagicMock()
    m_AnsibleAWSModule.return_value = m_module
    m_module.params = {
        "option_group_name": "",
        "engine_name": "",
        "major_engine_version": "",
        "marker": None,
        "max_records": 100,
    }
    e = AnsibleRDSError()
    m_describe.side_effect = e

    rds_option_group_info.main()

    m_module.client.assert_called_with("rds")
    m_module.fail_json_aws.assert_called_with(e, msg="Could not describe option groups.")
