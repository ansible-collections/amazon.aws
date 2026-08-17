# (c) 2026 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

from ansible_collections.amazon.aws.plugins.module_utils.rds import AnsibleRDSError
from ansible_collections.amazon.aws.plugins.modules import rds_engine_versions_info
from ansible_collections.amazon.aws.plugins.modules.rds_engine_versions_info import engine_versions_info

mod_name = "ansible_collections.amazon.aws.plugins.modules.rds_engine_versions_info"


@patch(mod_name + "._describe_db_engine_versions")
def test_engine_versions_info_with_engine(m_describe):
    conn = MagicMock()
    module = MagicMock()
    m_describe.return_value = [
        {
            "Engine": "aurora-postgresql",
            "EngineVersion": "16.1",
            "DBParameterGroupFamily": "aurora-postgresql16",
            "DBEngineDescription": "Aurora (PostgreSQL)",
            "TagList": [{"Key": "env", "Value": "test"}],
        }
    ]

    result = engine_versions_info(
        conn, module, engine="aurora-postgresql", engine_version=None,
        db_parameter_group_family=None, default_only=False, filters=None,
    )

    assert result == [
        {
            "engine": "aurora-postgresql",
            "engine_version": "16.1",
            "db_parameter_group_family": "aurora-postgresql16",
            "db_engine_description": "Aurora (PostgreSQL)",
            "tags": {"env": "test"},
        }
    ]
    m_describe.assert_called_with(conn, DefaultOnly=False, Engine="aurora-postgresql")


@patch(mod_name + "._describe_db_engine_versions")
def test_engine_versions_info_default_only(m_describe):
    conn = MagicMock()
    module = MagicMock()
    m_describe.return_value = [
        {
            "Engine": "postgres",
            "EngineVersion": "16.4",
            "DBParameterGroupFamily": "postgres16",
            "TagList": [],
        }
    ]

    result = engine_versions_info(
        conn, module, engine="postgres", engine_version=None,
        db_parameter_group_family="postgres16", default_only=True, filters=None,
    )

    assert len(result) == 1
    assert result[0]["engine"] == "postgres"
    assert result[0]["tags"] == {}
    m_describe.assert_called_with(
        conn, DefaultOnly=True, Engine="postgres", DBParameterGroupFamily="postgres16",
    )


@patch(mod_name + "._describe_db_engine_versions")
def test_engine_versions_info_no_results(m_describe):
    conn = MagicMock()
    module = MagicMock()
    m_describe.return_value = []

    result = engine_versions_info(
        conn, module, engine="mysql", engine_version="99.99",
        db_parameter_group_family=None, default_only=False, filters=None,
    )

    assert result == []


@patch(mod_name + "._describe_db_engine_versions")
def test_engine_versions_info_no_tag_list_key(m_describe):
    conn = MagicMock()
    module = MagicMock()
    m_describe.return_value = [
        {
            "Engine": "mysql",
            "EngineVersion": "8.0",
        }
    ]

    result = engine_versions_info(
        conn, module, engine="mysql", engine_version=None,
        db_parameter_group_family=None, default_only=False, filters=None,
    )

    assert result[0]["tags"] == {}


@patch(mod_name + "._describe_db_engine_versions")
def test_engine_versions_info_with_filters(m_describe):
    conn = MagicMock()
    module = MagicMock()
    m_describe.return_value = []
    filters = {"engine-mode": "provisioned"}

    engine_versions_info(
        conn, module, engine=None, engine_version=None,
        db_parameter_group_family=None, default_only=False, filters=filters,
    )

    m_describe.assert_called_with(conn, DefaultOnly=False, Filters=filters)


@patch(mod_name + ".AnsibleAWSModule")
def test_main_success(m_AnsibleAWSModule):
    m_module = MagicMock()
    m_AnsibleAWSModule.return_value = m_module
    m_module.params = {
        "engine": None,
        "engine_version": None,
        "db_parameter_group_family": None,
        "default_only": False,
        "filters": None,
    }

    rds_engine_versions_info.main()

    m_module.client.assert_called_with("rds")
    m_module.exit_json.assert_called_with(changed=False, db_engine_versions=[])


@patch(mod_name + "._describe_db_engine_versions")
@patch(mod_name + ".AnsibleAWSModule")
def test_main_failure(m_AnsibleAWSModule, m_describe):
    m_module = MagicMock()
    m_AnsibleAWSModule.return_value = m_module
    m_module.params = {
        "engine": None,
        "engine_version": None,
        "db_parameter_group_family": None,
        "default_only": False,
        "filters": None,
    }
    e = AnsibleRDSError()
    m_describe.side_effect = e

    rds_engine_versions_info.main()

    m_module.client.assert_called_with("rds")
    m_module.fail_json_aws.assert_called_with(e, msg="Couldn't get RDS engine versions.")
