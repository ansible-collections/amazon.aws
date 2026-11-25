# (c) 2024 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible.module_utils.common.arg_spec import ArgumentSpecValidator

from ansible_collections.amazon.aws.plugins.module_utils.rds import AnsibleRDSError
from ansible_collections.amazon.aws.plugins.modules import rds_instance
from ansible_collections.amazon.aws.plugins.modules.rds_instance import get_instance

mod_name = "ansible_collections.amazon.aws.plugins.modules.rds_instance"


@pytest.mark.parametrize(
    "instances, expected",
    [
        ([], {}),
        (
            [
                {
                    "DBInstanceIdentifier": "my-instance",
                    "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:og:my-instance",
                    "TagList": [],
                }
            ],
            {
                "DBInstanceIdentifier": "my-instance",
                "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:og:my-instance",
                "Tags": {},
            },
        ),
        (
            [
                {
                    "DBInstanceIdentifier": "my-instance",
                    "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:og:my-instance",
                    "TagList": [{"Key": "My Tag", "Value": "My Value"}],
                    "ProcessorFeatures": [{"Name": "coreCount", "Value": "1"}],
                    "PendingModifiedValues": {
                        "ProcessorFeatures": [{"Name": "coreCount", "Value": "2"}],
                    },
                }
            ],
            {
                "DBInstanceIdentifier": "my-instance",
                "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:og:my-instance",
                "Tags": {"My Tag": "My Value"},
                "ProcessorFeatures": {"coreCount": "1"},
                "PendingModifiedValues": {"ProcessorFeatures": {"coreCount": "2"}},
            },
        ),
        (
            [
                {
                    "DBInstanceIdentifier": "my-instance",
                    "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:og:my-instance",
                    "TagList": [{"Key": "My Tag", "Value": "My Value"}],
                    "Engine": "oracle-ee-cdb",
                    "MultiTenant": "True",
                }
            ],
            {
                "DBInstanceIdentifier": "my-instance",
                "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:og:my-instance",
                "Tags": {"My Tag": "My Value"},
                "Engine": "oracle-ee-cdb",
                "MultiTenant": "True",
            },
        ),
    ],
)
@patch(mod_name + ".describe_db_instances")
def test_get_instance_success(m_describe_db_instances, instances, expected):
    client = MagicMock()
    module = MagicMock()
    m_describe_db_instances.return_value = instances
    assert get_instance(client, module, "my-instance") == expected


@patch(mod_name + ".describe_db_instances")
def test_get_instance_failure(m_describe_db_instances):
    client = MagicMock()
    module = MagicMock()
    e = AnsibleRDSError()
    m_describe_db_instances.side_effect = e
    get_instance(client, module, "my-instance")
    module.fail_json_aws.assert_called_once_with(e, msg="Failed to get DB instance my-instance")


@patch(mod_name + ".describe_db_instances")
@patch(mod_name + ".get_changing_options_with_inconsistent_keys")
def test_get_options_with_changing_values(m_get_changing_options_with_inconsistent_keys, m_describe_db_instances):
    module = MagicMock()
    client = MagicMock()
    instance = {}

    m_describe_db_instances.return_value = [
        {
            "DBInstanceIdentifier": "my-instance",
            "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:og:my-instance",
            "TagList": [{"Key": "My Tag", "Value": "My Value"}],
            "Engine": "oracle-ee-cdb",
            "MultiTenant": True,
            "Endpoint": {"Port": "3000"},
            "DBSubnetGroup": {
                "DBSubnetGroupDescription": "default",
                "DBSubnetGroupName": "default",
            },
        }
    ]

    module.params = {
        "db_instance_identifier": "my-instance",
        "purge_cloudwatch_logs_exports": None,
        "force_update_password": None,
        "port": None,
        "enable_cloudwatch_logs_exports": None,
        "storage_type": None,
        "purge_security_groups": None,
        "ca_certificate_identifier": None,
        "db_instance_arn": "arn:aws:rds:us-east-1:123456789012:og:my-instance",
        "engine": "oracle-ee-cdb",
        "multi_tenant": False,
        "db_subnet_group": {
            "db_subnet_group_description": "default",
            "db_subnet_group_name": "default",
            "subnet_group_status": "Complete",
        },
    }
    m_get_changing_options_with_inconsistent_keys.return_value = {}
    rds_instance.get_options_with_changing_values(client, module, instance)
    assert module.require_botocore_at_least.call_count == 0
    module.fail_json.assert_called_with(
        msg="A DB which is configured to be a multi tenant cannot be modified to use single tenant configuration."
    )


def test_validate_options():
    module = MagicMock()
    client = MagicMock()
    instance = ""

    module.params = {
        "skip_final_snapshot": None,
        "final_db_snapshot_identifier": None,
        "new_db_instance_identifier": None,
        "tde_credential_password": False,
        "tde_credential_arn": False,
        "read_replica": None,
        "creation_source": None,
        "source_db_instance_identifier": None,
        "engine": "Aurora",
        "multi_tenant": True,
        "state": "present",
    }
    rds_instance.validate_options(client, module, instance)
    assert module.require_botocore_at_least.call_count == 0
    module.fail_json.assert_called_with(
        msg="Multi Tenant parameter only applies to RDS for Oracle container database (CDB) engines and not to Aurora."
    )


class TestGetParametersSelfManagedAD:
    @patch(mod_name + ".format_rds_client_method_parameters")
    def test_create_includes_self_managed_ad_params(self, m_format_params):
        client = MagicMock()
        module = MagicMock()

        raw_parameters = {
            "DBInstanceIdentifier": "test-selfmanaged-ad",
            "Engine": "postgres",
            "DBInstanceClass": "db.t3.micro",
            "MasterUsername": "admin",
            "MasterUserPassword": "secret",
            "AllocatedStorage": 20,
            "Domain": "d-1234567890",
            "DomainIAMRoleName": "rds-ad-role",
            "DomainFqdn": "corp.example.com",
            "DomainOu": "OU=RDS,DC=corp,DC=example,DC=com",
            "DomainAuthSecretArn": "arn:aws:secretsmanager:us-east-1:123456789012:secret:ad-join-creds",
            "DomainDnsIps": ["10.0.1.10", "10.0.2.10"],
            "Tags": {},
        }

        m_format_params.return_value = raw_parameters.copy()

        rds_instance.get_parameters(client, module, raw_parameters, "create_db_instance")

        m_format_params.assert_called_once_with(client, module, raw_parameters, "create_db_instance", format_tags=False)

    @patch(mod_name + ".get_changing_options_with_inconsistent_keys")
    @patch(mod_name + ".get_instance")
    @patch(mod_name + ".format_rds_client_method_parameters")
    def test_modify_includes_self_managed_ad_params(self, m_format_params, m_get_instance, m_get_changing):
        client = MagicMock()
        module = MagicMock()
        module.params = {
            "db_instance_identifier": "test-selfmanaged-ad",
            "purge_cloudwatch_logs_exports": None,
            "force_update_password": None,
            "port": None,
            "enable_cloudwatch_logs_exports": None,
            "storage_type": None,
            "purge_security_groups": None,
            "ca_certificate_identifier": None,
        }

        raw_parameters = {
            "DBInstanceIdentifier": "test-selfmanaged-ad",
            "Domain": "d-1234567890",
            "DomainIAMRoleName": "rds-ad-role",
            "DomainFqdn": "corp.example.com",
            "DomainOu": "OU=RDS,DC=corp,DC=example,DC=com",
            "DomainAuthSecretArn": "arn:aws:secretsmanager:us-east-1:123456789012:secret:ad-join-creds",
            "DomainDnsIps": ["10.0.1.10", "10.0.2.10"],
            "Tags": {},
        }

        m_format_params.return_value = raw_parameters.copy()
        m_get_instance.return_value = {
            "DBInstanceIdentifier": "test-selfmanaged-ad",
            "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:db:test-selfmanaged-ad",
            "Tags": {},
            "Endpoint": {"Port": 5432},
            "DBSubnetGroup": {"DBSubnetGroupName": "default"},
        }
        m_get_changing.return_value = {}

        rds_instance.get_parameters(client, module, raw_parameters, "modify_db_instance")

        m_format_params.assert_called_once_with(client, module, raw_parameters, "modify_db_instance", format_tags=False)

    @patch(mod_name + ".format_rds_client_method_parameters")
    def test_create_without_self_managed_ad_params(self, m_format_params):
        client = MagicMock()
        module = MagicMock()

        raw_parameters = {
            "DBInstanceIdentifier": "test-managed-ad",
            "Engine": "postgres",
            "DBInstanceClass": "db.t3.micro",
            "MasterUsername": "admin",
            "MasterUserPassword": "secret",
            "AllocatedStorage": 20,
            "Domain": "d-1234567890",
            "DomainIAMRoleName": "rds-ad-role",
            "Tags": {},
        }

        m_format_params.return_value = raw_parameters.copy()

        rds_instance.get_parameters(client, module, raw_parameters, "create_db_instance")
        m_format_params.assert_called_once_with(client, module, raw_parameters, "create_db_instance", format_tags=False)


DB_INSTANCE_ARN = "arn:aws:rds:us-east-1:123456789012:db:my-instance"


INSTANCE = {"DBInstanceArn": DB_INSTANCE_ARN}


def _pending(action="system-update", opt_in_status=""):
    detail = {"Action": action}
    if opt_in_status is not None:
        detail["OptInStatus"] = opt_in_status
    return [{"ResourceIdentifier": DB_INSTANCE_ARN, "PendingMaintenanceActionDetails": [detail]}]


@patch(mod_name + ".call_method")
@patch(mod_name + ".describe_pending_maintenance_actions")
def test_ensure_pending_maintenance_action_applied(m_describe, m_call_method):
    client = MagicMock()
    module = MagicMock()
    module.check_mode = False
    module.params = {
        "apply_pending_maintenance_action": {"apply_action": "system-update", "opt_in_type": "immediate"},
    }
    m_describe.return_value = _pending(action="system-update", opt_in_status="")
    m_call_method.return_value = ({}, True)

    changed = rds_instance.ensure_pending_maintenance_action(client, module, INSTANCE)

    assert changed is True
    m_describe.assert_called_once_with(client, ResourceIdentifier=DB_INSTANCE_ARN)
    m_call_method.assert_called_once_with(
        client,
        module,
        method_name="apply_pending_maintenance_action",
        parameters={
            "ResourceIdentifier": DB_INSTANCE_ARN,
            "ApplyAction": "system-update",
            "OptInType": "immediate",
        },
    )


@patch(mod_name + ".call_method")
@patch(mod_name + ".describe_pending_maintenance_actions")
def test_ensure_pending_maintenance_action_no_pending(m_describe, m_call_method):
    client = MagicMock()
    module = MagicMock()
    module.check_mode = False
    module.params = {
        "apply_pending_maintenance_action": {"apply_action": "db-upgrade", "opt_in_type": "immediate"},
    }
    # A pending action exists, but it does not match the requested apply_action
    m_describe.return_value = _pending(action="system-update")

    changed = rds_instance.ensure_pending_maintenance_action(client, module, INSTANCE)

    assert changed is False
    m_call_method.assert_not_called()


@patch(mod_name + ".call_method")
@patch(mod_name + ".describe_pending_maintenance_actions")
def test_ensure_pending_maintenance_action_already_opted_in(m_describe, m_call_method):
    client = MagicMock()
    module = MagicMock()
    module.check_mode = False
    module.params = {
        "apply_pending_maintenance_action": {"apply_action": "system-update", "opt_in_type": "next-maintenance"},
    }
    # The action is already opted-in to the requested type: idempotent no-op
    m_describe.return_value = _pending(action="system-update", opt_in_status="next-maintenance")

    changed = rds_instance.ensure_pending_maintenance_action(client, module, INSTANCE)

    assert changed is False
    m_call_method.assert_not_called()


@patch(mod_name + ".call_method")
@patch(mod_name + ".describe_pending_maintenance_actions")
def test_ensure_pending_maintenance_action_undo_without_opt_in(m_describe, m_call_method):
    client = MagicMock()
    module = MagicMock()
    module.check_mode = False
    module.params = {
        "apply_pending_maintenance_action": {"apply_action": "system-update", "opt_in_type": "undo-opt-in"},
    }
    # Nothing has been opted-in, so there is nothing to undo
    m_describe.return_value = _pending(action="system-update", opt_in_status="")

    changed = rds_instance.ensure_pending_maintenance_action(client, module, INSTANCE)

    assert changed is False
    m_call_method.assert_not_called()


@patch(mod_name + ".call_method")
@patch(mod_name + ".describe_pending_maintenance_actions")
def test_ensure_pending_maintenance_action_check_mode(m_describe, m_call_method):
    client = MagicMock()
    module = MagicMock()
    module.check_mode = True
    module.params = {
        "apply_pending_maintenance_action": {"apply_action": "system-update", "opt_in_type": "immediate"},
    }
    m_describe.return_value = _pending(action="system-update", opt_in_status="")

    changed = rds_instance.ensure_pending_maintenance_action(client, module, INSTANCE)

    # check_mode reports the change without calling the API
    assert changed is True
    m_call_method.assert_not_called()


class _StopMain(Exception):
    """Sentinel used to stop rds_instance.main() once the argument spec is built."""


def test_apply_pending_maintenance_action_argument_spec_validation():
    captured = {}

    def capture(**kwargs):
        captured["argument_spec"] = kwargs["argument_spec"]
        raise _StopMain

    with patch(mod_name + ".AnsibleAWSModule", side_effect=capture):
        with pytest.raises(_StopMain):
            rds_instance.main()

    argument_spec = captured["argument_spec"]

    valid = {
        "db_instance_identifier": "my-instance",
        "apply_pending_maintenance_action": {"apply_action": "system-update", "opt_in_type": "immediate"},
    }
    invalid = {
        "db_instance_identifier": "my-instance",
        "apply_pending_maintenance_action": {"apply_action": "not-a-real-action", "opt_in_type": "immediate"},
    }

    assert not ArgumentSpecValidator(argument_spec).validate(valid).error_messages
    assert ArgumentSpecValidator(argument_spec).validate(invalid).error_messages
