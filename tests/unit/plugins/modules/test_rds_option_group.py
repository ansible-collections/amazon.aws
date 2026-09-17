# (c) 2026 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

from ansible_collections.amazon.aws.plugins.module_utils.rds import AnsibleRDSError
from ansible_collections.amazon.aws.plugins.modules import rds_option_group
from ansible_collections.amazon.aws.plugins.modules.rds_option_group import get_option_group
from ansible_collections.amazon.aws.plugins.modules.rds_option_group import update_tags

mod_name = "ansible_collections.amazon.aws.plugins.modules.rds_option_group"


@patch(mod_name + ".get_tags")
@patch(mod_name + ".describe_option_groups")
def test_get_option_group_found(m_describe, m_get_tags):
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

    result = get_option_group(conn, module, "test-og")

    assert result["option_group_name"] == "test-og"
    assert result["engine_name"] == "mysql"
    assert result["tags"] == {"Name": "test"}
    m_describe.assert_called_with(conn, OptionGroupName="test-og")
    m_get_tags.assert_called_once_with(conn, module, "arn:aws:rds:us-east-1:123456789012:og:test-og")


@patch(mod_name + ".get_tags")
@patch(mod_name + ".describe_option_groups")
def test_get_option_group_not_found(m_describe, m_get_tags):
    conn = MagicMock()
    module = MagicMock()
    m_describe.return_value = []

    result = get_option_group(conn, module, "nonexistent")

    assert result == {}
    m_get_tags.assert_not_called()


@patch(mod_name + ".get_tags")
@patch(mod_name + ".compare_aws_tags")
def test_update_tags_adds_and_removes(m_compare, m_get_tags):
    conn = MagicMock()
    module = MagicMock()
    module.params = {"tags": {"New": "tag"}, "purge_tags": True}
    module.check_mode = False
    m_get_tags.return_value = {"Old": "tag"}
    m_compare.return_value = ({"New": "tag"}, ["Old"])

    option_group = {"option_group_arn": "arn:aws:rds:us-east-1:123456789012:og:test-og"}

    result = update_tags(conn, module, option_group)

    assert result is True
    conn.add_tags_to_resource.assert_called_once()
    conn.remove_tags_from_resource.assert_called_once()


@patch(mod_name + ".get_tags")
@patch(mod_name + ".compare_aws_tags")
def test_update_tags_no_change(m_compare, m_get_tags):
    conn = MagicMock()
    module = MagicMock()
    module.params = {"tags": {"Same": "tag"}, "purge_tags": True}
    module.check_mode = False
    m_get_tags.return_value = {"Same": "tag"}
    m_compare.return_value = ({}, [])

    option_group = {"option_group_arn": "arn:aws:rds:us-east-1:123456789012:og:test-og"}

    result = update_tags(conn, module, option_group)

    assert result is False
    conn.add_tags_to_resource.assert_not_called()
    conn.remove_tags_from_resource.assert_not_called()


def test_update_tags_none():
    conn = MagicMock()
    module = MagicMock()
    module.params = {"tags": None}

    result = update_tags(conn, module, {"option_group_arn": "arn"})

    assert result is False


@patch(mod_name + ".get_tags")
@patch(mod_name + ".compare_aws_tags")
def test_update_tags_check_mode(m_compare, m_get_tags):
    conn = MagicMock()
    module = MagicMock()
    module.params = {"tags": {"New": "tag"}, "purge_tags": True}
    module.check_mode = True
    m_get_tags.return_value = {"Old": "tag"}
    m_compare.return_value = ({"New": "tag"}, ["Old"])

    option_group = {"option_group_arn": "arn:aws:rds:us-east-1:123456789012:og:test-og"}

    result = update_tags(conn, module, option_group)

    assert result is True
    conn.add_tags_to_resource.assert_not_called()
    conn.remove_tags_from_resource.assert_not_called()


@patch(mod_name + ".get_tags")
@patch(mod_name + ".describe_option_groups")
@patch(mod_name + ".AnsibleAWSModule")
def test_main_present_creates(m_AnsibleAWSModule, m_describe, m_get_tags):
    m_module = MagicMock()
    m_AnsibleAWSModule.return_value = m_module
    m_module.params = {
        "state": "present",
        "option_group_name": "test-og",
        "engine_name": "mysql",
        "major_engine_version": "8.0",
        "option_group_description": "test",
        "options": None,
        "apply_immediately": False,
        "tags": None,
        "purge_tags": True,
        "wait": True,
    }
    m_module.check_mode = False
    m_describe.return_value = []
    m_get_tags.return_value = {}

    rds_option_group.main()

    assert m_module.client.call_args[0] == ("rds",)


@patch(mod_name + ".describe_option_groups")
@patch(mod_name + ".AnsibleAWSModule")
def test_main_failure(m_AnsibleAWSModule, m_describe):
    m_module = MagicMock()
    m_AnsibleAWSModule.return_value = m_module
    m_module.params = {
        "state": "present",
        "option_group_name": "test-og",
        "engine_name": "mysql",
        "major_engine_version": "8.0",
        "option_group_description": "test",
        "options": None,
        "apply_immediately": False,
        "tags": None,
        "purge_tags": True,
        "wait": True,
    }
    e = AnsibleRDSError()
    m_describe.side_effect = e
    m_module.fail_json_aws.side_effect = SystemExit(1)

    try:
        rds_option_group.main()
    except SystemExit:
        pass

    assert m_module.client.call_args[0] == ("rds",)
    m_module.fail_json_aws.assert_called_with(e, msg="Couldn't manage option group.")


@patch(mod_name + ".describe_option_groups")
def test_create_option_group_check_mode_with_tags(m_describe):
    """Verify check_mode is respected when creating an option group with tags (bug fix)."""
    conn = MagicMock()
    module = MagicMock()
    module.params = {
        "option_group_name": "test-og",
        "engine_name": "mysql",
        "major_engine_version": "8.0",
        "option_group_description": "test",
        "tags": {"Key": "Value"},
    }
    module.check_mode = True

    result = rds_option_group.create_option_group(conn, module)

    assert result is True
    conn.create_option_group.assert_not_called()
