# (c) 2024 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import copy
from unittest.mock import MagicMock

import pytest

from ansible_collections.amazon.aws.plugins.modules import rds_cluster


@pytest.fixture(name="ansible_module")
def fixture_ansible_module():
    module = MagicMock()
    module.check_mode = False
    module.params = {}
    module.fail_json.side_effect = SystemExit(1)
    module.fail_json_aws.side_effect = SystemExit(1)

    return module


class TestChangingClusterOptions:
    def test_module_state(self, ansible_module):
        apply_immediately = MagicMock()
        db_cluster_id = MagicMock()
        master_user_passwd = MagicMock()

        modify_params = {
            "ApplyImmediately": apply_immediately,
            "DBClusterIdentifier": db_cluster_id,
            "MasterUserPassword": master_user_passwd,
        }
        current_cluster = {
            "DBClusterIdentifier": db_cluster_id,
        }

        # 'present' or 'absent'
        rds_cluster.module = ansible_module
        for state in ("present", "absent"):
            rds_cluster.module.params.update({"state": state})
            assert modify_params == rds_cluster.changing_cluster_options(copy.deepcopy(modify_params), current_cluster)

        # 'stopped'/'started'
        for state in ("started", "stopped"):
            rds_cluster.module.params.update({"state": state})
            # 'mysql' or 'postgres' engine
            for engine in ("mysql", "postgres"):
                current_cluster.update({"Engine": engine})
                with pytest.raises(SystemExit):
                    rds_cluster.changing_cluster_options(copy.deepcopy(modify_params), current_cluster)
                rds_cluster.module.fail_json.assert_called_once_with(f"Only aurora clusters can use the state {state}")
                rds_cluster.module.fail_json.reset_mock()
            # 'aurora' engine
            current_cluster.update({"Engine": "aurora"})
            assert {"DBClusterIdentifier": db_cluster_id} == rds_cluster.changing_cluster_options(
                copy.deepcopy(modify_params), current_cluster
            )

    @pytest.mark.parametrize(
        "params,expected",
        [
            ({"StorageType": "10B"}, {"StorageType": "10B"}),
            ({"StorageType": "10B", "DeletionProtection": True}, {"StorageType": "10B", "DeletionProtection": True}),
            ({"DeletionProtection": True}, {"DeletionProtection": True}),
            ({"DeletionProtection": False}, {}),
            ({"Domain": "domain-2"}, {"Domain": "domain-2"}),
            ({"Domain": "domain-1", "DomainIAMRoleName": "ansible-test-units-001"}, {}),
            (
                {"Domain": "domain-2", "DomainIAMRoleName": "ansible-test-units-001"},
                {"Domain": "domain-2", "DomainIAMRoleName": "ansible-test-units-001"},
            ),
            (
                {"Domain": "domain-2", "DomainIAMRoleName": "ansible-test-units-002"},
                {"Domain": "domain-2", "DomainIAMRoleName": "ansible-test-units-002"},
            ),
        ],
    )
    def test_modify_params(self, ansible_module, params, expected):
        apply_immediately = MagicMock()
        db_cluster_id = MagicMock()

        modify_params = {
            "ApplyImmediately": apply_immediately,
            "DBClusterIdentifier": db_cluster_id,
        }
        if expected:
            expected.update(modify_params)
        modify_params.update(params)

        current_cluster = {
            "DBClusterIdentifier": db_cluster_id,
            "DeletionProtection": False,
            "DomainMemberships": [
                {
                    "Domain": "domain-1",
                    "Status": "joined",
                    "FQDN": "testing.ansible.units",
                    "IAMRoleName": "ansible-test-units-001",
                },
            ],
        }

        # state is set to 'present'
        ansible_module.params.update({"state": "present"})
        rds_cluster.module = ansible_module
        assert expected == rds_cluster.changing_cluster_options(modify_params, current_cluster)

    @pytest.mark.parametrize(
        "modify_vpc_security_group_ids, current_vpc_security_group_ids, expected_vpc_security_group_ids",
        [
            (["id-1", "id-1", "id-2"], ["id-3"], ["id-1", "id-2"]),
            (["id-1", "id-2"], ["id-1", "id-2"], ["id-1", "id-2"]),
        ],
    )
    def test_vpc_security_group_ids_purge_true(
        self,
        ansible_module,
        modify_vpc_security_group_ids,
        current_vpc_security_group_ids,
        expected_vpc_security_group_ids,
    ):
        db_cluster_id = MagicMock()
        apply_immediately = MagicMock()
        modify_params = {
            "DBClusterIdentifier": db_cluster_id,
            "ApplyImmediately": apply_immediately,
        }
        expected = {}
        if expected_vpc_security_group_ids:
            expected.update(modify_params)
            expected["VpcSecurityGroupIds"] = expected_vpc_security_group_ids
        modify_params.update({"VpcSecurityGroupIds": modify_vpc_security_group_ids})

        current_cluster = {"VpcSecurityGroups": [{"VpcSecurityGroupId": x} for x in current_vpc_security_group_ids]}

        # state is set to 'present'
        ansible_module.params.update({"state": "present", "purge_security_groups": True})
        rds_cluster.module = ansible_module
        assert expected == rds_cluster.changing_cluster_options(modify_params, current_cluster)

    @pytest.mark.parametrize(
        "modify_vpc_security_group_ids, current_vpc_security_group_ids, expected_vpc_security_group_ids",
        [
            (["id-1", "id-1", "id-2"], ["id-3"], ["id-1", "id-2", "id-3"]),
            (["id-1", "id-2"], ["id-2", "id-1"], []),
            (["id-1", "id-2"], ["id-2", "id-1", "id-3"], []),
            (["id-1", "id-1", "id-2"], [], ["id-1", "id-2"]),
        ],
    )
    def test_vpc_security_group_ids_purge_false(
        self,
        ansible_module,
        modify_vpc_security_group_ids,
        current_vpc_security_group_ids,
        expected_vpc_security_group_ids,
    ):
        db_cluster_id = MagicMock()
        apply_immediately = MagicMock()
        modify_params = {
            "DBClusterIdentifier": db_cluster_id,
            "ApplyImmediately": apply_immediately,
        }
        expected = {}
        if expected_vpc_security_group_ids:
            expected.update(modify_params)
            expected["VpcSecurityGroupIds"] = expected_vpc_security_group_ids
        modify_params.update({"VpcSecurityGroupIds": modify_vpc_security_group_ids})

        current_cluster = {"VpcSecurityGroups": [{"VpcSecurityGroupId": x} for x in current_vpc_security_group_ids]}

        # state is set to 'present'
        ansible_module.params.update({"state": "present", "purge_security_groups": False})
        rds_cluster.module = ansible_module
        assert expected == rds_cluster.changing_cluster_options(modify_params, current_cluster)

    @pytest.mark.parametrize(
        "purge_cloudwatch_logs_exports, modify_enable_cloudwatch_logs_exports, current_enabled_cloudwatch_logs_exports, enable_log_types, disable_log_types",
        [
            (True, ["log-3", "log-2"], ["log-1"], ["log-2", "log-3"], ["log-1"]),
            (False, ["log-3", "log-2"], ["log-1"], ["log-2", "log-3"], []),
            (True, ["log-1", "log-2"], ["log-1", "log-2", "log-3"], [], ["log-3"]),
            (False, ["log-1", "log-2"], ["log-1", "log-2", "log-3"], [], []),
        ],
    )
    def test_enable_cloudwatch_logs_export(
        self,
        ansible_module,
        purge_cloudwatch_logs_exports,
        modify_enable_cloudwatch_logs_exports,
        current_enabled_cloudwatch_logs_exports,
        enable_log_types,
        disable_log_types,
    ):
        db_cluster_id = MagicMock()
        apply_immediately = MagicMock()
        modify_params = {
            "DBClusterIdentifier": db_cluster_id,
            "ApplyImmediately": apply_immediately,
            "EnableCloudwatchLogsExports": modify_enable_cloudwatch_logs_exports,
        }
        expected = None
        if enable_log_types or disable_log_types:
            expected = {"EnableLogTypes": enable_log_types, "DisableLogTypes": disable_log_types}

        current_cluster = {"EnabledCloudwatchLogsExports": current_enabled_cloudwatch_logs_exports}

        # state is set to 'present'
        ansible_module.params.update(
            {"state": "present", "purge_cloudwatch_logs_exports": purge_cloudwatch_logs_exports}
        )
        rds_cluster.module = ansible_module
        assert expected == rds_cluster.changing_cluster_options(modify_params, current_cluster).get(
            "CloudwatchLogsExportConfiguration"
        )

    @pytest.mark.parametrize(
        "new_cluster_id, current_cluster_id, expected_change",
        [
            ("", "cluster-id-1", False),
            (None, "cluster-id-1", False),
            ("cluster-id-1", "cluster-id-1", False),
            ("cluster-id-2", "cluster-id-1", True),
        ],
    )
    def test_modify_cluster_id(self, ansible_module, new_cluster_id, current_cluster_id, expected_change):
        db_cluster_id = MagicMock()
        apply_immediately = MagicMock()
        modify_params = {
            "DBClusterIdentifier": db_cluster_id,
            "NewDBClusterIdentifier": new_cluster_id,
            "ApplyImmediately": apply_immediately,
        }
        expected = {}
        if expected_change:
            expected.update(modify_params)

        current_cluster = {"DBClusterIdentifier": current_cluster_id}

        # state is set to 'present'
        ansible_module.params.update({"state": "present"})
        rds_cluster.module = ansible_module
        assert expected == rds_cluster.changing_cluster_options(modify_params, current_cluster)

    @pytest.mark.parametrize(
        "new_option_group_name, cluster_option_group_memberships, expected_change",
        [
            ("", [], False),
            (None, [], False),
            ("opt-3", ["opt-1", "opt-2", "opt-3"], False),
            ("opt-3", ["opt-1", "opt-2"], True),
        ],
    )
    def test_option_group_name(
        self, ansible_module, new_option_group_name, cluster_option_group_memberships, expected_change
    ):
        db_cluster_id = MagicMock()
        apply_immediately = MagicMock()
        modify_params = {
            "DBClusterIdentifier": db_cluster_id,
            "OptionGroupName": new_option_group_name,
            "ApplyImmediately": apply_immediately,
        }
        expected = {}
        if expected_change:
            expected.update(modify_params)

        current_cluster = {
            "DBClusterOptionGroupMemberships": [
                {"DBClusterOptionGroupName": x} for x in cluster_option_group_memberships
            ]
        }

        # state is set to 'present'
        ansible_module.params.update({"state": "present"})
        rds_cluster.module = ansible_module
        assert expected == rds_cluster.changing_cluster_options(modify_params, current_cluster)

    @pytest.mark.parametrize(
        "new_db_cluster_parameter_group_name, current_db_cluster_parameter_group_name, expected_change",
        [
            ("", "param-group-0", False),
            (None, "param-group-0", False),
            ("param-group-0", "param-group-0", False),
            ("param-group-1", "param-group-0", True),
        ],
    )
    def test_db_cluster_parameter_group_name(
        self,
        ansible_module,
        new_db_cluster_parameter_group_name,
        current_db_cluster_parameter_group_name,
        expected_change,
    ):
        db_cluster_id = MagicMock()
        apply_immediately = MagicMock()
        modify_params = {
            "DBClusterIdentifier": db_cluster_id,
            "DBClusterParameterGroupName": new_db_cluster_parameter_group_name,
            "ApplyImmediately": apply_immediately,
        }
        expected = {}
        if expected_change:
            expected.update(modify_params)

        current_cluster = {"DBClusterParameterGroup": current_db_cluster_parameter_group_name}

        # state is set to 'present'
        ansible_module.params.update({"state": "present"})
        rds_cluster.module = ansible_module
        assert expected == rds_cluster.changing_cluster_options(modify_params, current_cluster)
