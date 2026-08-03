# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3
from ansible_collections.amazon.aws.plugins.module_utils.rds import Boto3ClientMethod
from ansible_collections.amazon.aws.plugins.module_utils.rds import arg_spec_to_rds_params
from ansible_collections.amazon.aws.plugins.module_utils.rds import compare_iam_roles
from ansible_collections.amazon.aws.plugins.module_utils.rds import format_rds_client_method_parameters

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_rds_transformations.py requires the python modules 'boto3' and 'botocore'")

mod_transformations = "ansible_collections.amazon.aws.plugins.module_utils._rds.transformations"


# =============================================================================
# arg_spec_to_rds_params
# =============================================================================


def test__arg_spec_to_rds_params_basic():
    options = {"db_instance_identifier": "mydb", "master_username": "admin", "tags": {"Name": "mydb"}}
    result = arg_spec_to_rds_params(options)

    assert result["DBInstanceIdentifier"] == "mydb"
    assert result["MasterUsername"] == "admin"
    assert result["Tags"] == {"Name": "mydb"}
    assert "db_instance_identifier" not in result


def test__arg_spec_to_rds_params_iam_replacement():
    options = {"iam_database_authentication_enabled": True, "tags": {}}
    result = arg_spec_to_rds_params(options)

    assert "IAMDatabaseAuthenticationEnabled" in result
    assert "IamDatabaseAuthenticationEnabled" not in result


def test__arg_spec_to_rds_params_db_replacement():
    options = {"db_name": "mydb", "db_cluster_identifier": "mycluster", "tags": {}}
    result = arg_spec_to_rds_params(options)

    assert "DBName" in result
    assert "DBClusterIdentifier" in result
    assert "DbName" not in result


def test__arg_spec_to_rds_params_az_replacement():
    options = {"multi_az": True, "tags": {}}
    result = arg_spec_to_rds_params(options)

    assert "MultiAZ" in result
    assert "MultiAz" not in result


def test__arg_spec_to_rds_params_ca_replacement():
    options = {"ca_certificate_identifier": "rds-ca-2019", "tags": {}}
    result = arg_spec_to_rds_params(options)

    assert "CACertificateIdentifier" in result
    assert "CaCertificateIdentifier" not in result


def test__arg_spec_to_rds_params_kms_key_replacement():
    options = {"performance_insights_kms_key_id": "arn:aws:kms:us-east-1:123456:key/abc", "tags": {}}
    result = arg_spec_to_rds_params(options)

    assert "PerformanceInsightsKMSKeyId" in result
    assert "PerformanceInsightsKmsKeyId" not in result


def test__arg_spec_to_rds_params_processor_features_preserved():
    proc_features = [{"Name": "coreCount", "Value": "4"}]
    options = {"db_instance_class": "db.m5.large", "processor_features": proc_features, "tags": {"Env": "dev"}}
    result = arg_spec_to_rds_params(options)

    assert result["ProcessorFeatures"] == proc_features
    assert result["Tags"] == {"Env": "dev"}
    assert result["DBInstanceClass"] == "db.m5.large"


def test__arg_spec_to_rds_params_tags_none():
    options = {"db_instance_identifier": "mydb", "tags": None}
    result = arg_spec_to_rds_params(options)

    assert result["Tags"] is None


def test__arg_spec_to_rds_params_empty_options():
    options = {"tags": {}}
    result = arg_spec_to_rds_params(options)

    assert result == {"Tags": {}}


# =============================================================================
# format_rds_client_method_parameters
# =============================================================================


@pytest.mark.parametrize(
    "provided_params, format_tags, expected",
    [
        (
            {"RequiredParameter": "Present"},
            False,
            {"RequiredParameter": "Present"},
        ),
        (
            {"RequiredParameter": "Present", "OptionalParameter": None},
            False,
            {"RequiredParameter": "Present"},
        ),
        (
            {"RequiredParameter": "Present", "IrrelevantParameter": "Not used by this method"},
            False,
            {"RequiredParameter": "Present"},
        ),
        (
            {
                "RequiredParameter": "Present",
                "OptionalParameter": "Present",
                "Tags": {"still_in": "ansible_dict_format"},
            },
            False,
            {
                "RequiredParameter": "Present",
                "OptionalParameter": "Present",
                "Tags": {"still_in": "ansible_dict_format"},
            },
        ),
        (
            {"RequiredParameter": "Present"},
            True,
            {"RequiredParameter": "Present"},
        ),
        (
            {"RequiredParameter": "Present", "Tags": None},
            True,
            {"RequiredParameter": "Present"},
        ),
        (
            {"RequiredParameter": "Present", "Tags": {}},
            True,
            {"RequiredParameter": "Present", "Tags": {}},
        ),
        (
            {"RequiredParameter": "Present", "Tags": {"Now in": "boto3_list_format"}},
            True,
            {"RequiredParameter": "Present", "Tags": [{"Key": "Now in", "Value": "boto3_list_format"}]},
        ),
    ],
)
@patch(mod_transformations + ".get_boto3_client_method_parameters")
def test_format_rds_client_method_parameters_success(
    m_get_boto3_client_method_parameters, provided_params, format_tags, expected
):
    module = MagicMock()
    module.fail_json_aws = MagicMock()
    client = MagicMock()
    m_get_boto3_client_method_parameters.side_effect = [
        ["RequiredParameter"],
        ["RequiredParameter", "OptionalParameter", "Tags"],
    ]

    assert format_rds_client_method_parameters(client, module, provided_params, "mock_method", format_tags) == expected


@pytest.mark.parametrize(
    "provided_params",
    [
        ({"RequiredParameter": None}),
        ({"OptionalParameter": "present"}),
        ({}),
    ],
)
@patch(mod_transformations + ".get_boto3_client_method_parameters")
@patch(mod_transformations + ".get_rds_method_attribute")
def test_format_rds_client_method_parameters_failure(
    m_get_rds_method_attribute, m_get_boto3_client_method_parameters, provided_params
):
    module = MagicMock()
    client = MagicMock()
    m_get_boto3_client_method_parameters.return_value = ["RequiredParameter"]
    m_get_rds_method_attribute.return_value = Boto3ClientMethod("mock_method", None, "mock method", None, None)

    format_rds_client_method_parameters(client, module, provided_params, "mock_method", False)
    module.fail_json.assert_called_with(msg="To mock method requires the parameters: ['RequiredParameter']")


class TestRdsUtils:
    def setup_method(self):
        self.target_role_list = [
            {"role_arn": "role_won", "feature_name": "s3Export"},
            {"role_arn": "role_too", "feature_name": "Lambda"},
            {"role_arn": "role_thrie", "feature_name": "s3Import"},
        ]

    def test_compare_iam_roles_equal(self):
        existing_list = self.target_role_list
        roles_to_add, roles_to_delete = compare_iam_roles(existing_list, self.target_role_list, purge_roles=False)
        assert roles_to_add == []
        assert roles_to_delete == []
        roles_to_add, roles_to_delete = compare_iam_roles(existing_list, self.target_role_list, purge_roles=True)
        assert roles_to_add == []
        assert roles_to_delete == []

    def test_compare_iam_roles_empty_arr_existing(self):
        roles_to_add, roles_to_delete = compare_iam_roles([], self.target_role_list, purge_roles=False)
        assert roles_to_add == self.target_role_list
        assert roles_to_delete == []
        roles_to_add, roles_to_delete = compare_iam_roles([], self.target_role_list, purge_roles=True)
        assert roles_to_add == self.target_role_list
        assert roles_to_delete == []

    def test_compare_iam_roles_empty_arr_target(self):
        existing_list = self.target_role_list
        roles_to_add, roles_to_delete = compare_iam_roles(existing_list, [], purge_roles=False)
        assert roles_to_add == []
        assert roles_to_delete == []
        roles_to_add, roles_to_delete = compare_iam_roles(existing_list, [], purge_roles=True)
        assert roles_to_add == []
        assert roles_to_delete == self.target_role_list

    def test_compare_iam_roles_different(self):
        existing_list = [{"role_arn": "role_wonn", "feature_name": "s3Export"}]
        roles_to_add, roles_to_delete = compare_iam_roles(existing_list, self.target_role_list, purge_roles=False)
        assert roles_to_add == self.target_role_list
        assert roles_to_delete == []
        roles_to_add, roles_to_delete = compare_iam_roles(existing_list, self.target_role_list, purge_roles=True)
        assert roles_to_add == self.target_role_list
        assert roles_to_delete == existing_list

        existing_list = self.target_role_list.copy()
        self.target_role_list = [{"role_arn": "role_wonn", "feature_name": "s3Export"}]
        roles_to_add, roles_to_delete = compare_iam_roles(existing_list, self.target_role_list, purge_roles=False)
        assert roles_to_add == self.target_role_list
        assert roles_to_delete == []
        roles_to_add, roles_to_delete = compare_iam_roles(existing_list, self.target_role_list, purge_roles=True)
        assert roles_to_add == self.target_role_list
        assert roles_to_delete == existing_list
