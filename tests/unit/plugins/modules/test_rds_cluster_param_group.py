# (c) 2026 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.modules.rds_cluster_param_group import ensure_absent
from ansible_collections.amazon.aws.plugins.modules.rds_cluster_param_group import ensure_present
from ansible_collections.amazon.aws.plugins.modules.rds_cluster_param_group import get_parameter_group
from ansible_collections.amazon.aws.plugins.modules.rds_cluster_param_group import has_changed_parameters
from ansible_collections.amazon.aws.plugins.modules.rds_cluster_param_group import modify_parameters
from ansible_collections.amazon.aws.plugins.modules.rds_cluster_param_group import update_parameter_group

mod_name = "ansible_collections.amazon.aws.plugins.modules.rds_cluster_param_group"

GROUP_ARN = "arn:aws:rds:us-east-1:123456789012:cluster-pg:test-pg"
GROUP = {
    "DBClusterParameterGroupName": "test-pg",
    "DBClusterParameterGroupArn": GROUP_ARN,
    "DBParameterGroupFamily": "postgres16",
    "Description": "test cluster param group",
}


class ExitJsonException(Exception):
    """Raised by the mocked module.exit_json() so tests can assert on the result."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        super().__init__("exit_json")


class FailJsonException(Exception):
    """Raised by the mocked module.fail_json() so tests can assert on the failure."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        super().__init__(kwargs.get("msg", "fail_json"))


def raise_exit_json(**kwargs):
    raise ExitJsonException(**kwargs)


def raise_fail_json(**kwargs):
    raise FailJsonException(**kwargs)


def build_module(**params):
    module = MagicMock()
    module.check_mode = False
    module.params = {
        "state": "present",
        "name": "test-pg",
        "description": "test cluster param group",
        "db_parameter_group_family": "postgres16",
        "parameters": None,
        "tags": None,
        "purge_tags": True,
    }
    module.params.update(params)
    module.exit_json.side_effect = raise_exit_json
    module.fail_json.side_effect = raise_fail_json
    return module


# =============================================================================
# get_parameter_group
# =============================================================================


@patch(mod_name + ".describe_db_cluster_parameter_groups")
def test_get_parameter_group_found(m_describe):
    client = MagicMock()
    m_describe.return_value = [GROUP]

    assert get_parameter_group(client, "test-pg") == GROUP
    m_describe.assert_called_once_with(client, DBClusterParameterGroupName="test-pg")


@patch(mod_name + ".describe_db_cluster_parameter_groups")
def test_get_parameter_group_not_found(m_describe):
    m_describe.return_value = []

    assert get_parameter_group(MagicMock(), "test-pg") is None


# =============================================================================
# has_changed_parameters
# =============================================================================


def test_has_changed_parameters_detects_change():
    current_params = [
        {"ParameterName": "array_nulls", "ParameterValue": "1", "ApplyMethod": "immediate", "IsModifiable": True},
        {
            "ParameterName": "authentication_timeout",
            "ParameterValue": "50",
            "ApplyMethod": "immediate",
            "IsModifiable": True,
        },
    ]
    desired_params = [
        {"ParameterName": "array_nulls", "ParameterValue": "0", "ApplyMethod": "immediate"},
        {"ParameterName": "authentication_timeout", "ParameterValue": "50", "ApplyMethod": "immediate"},
    ]

    assert has_changed_parameters(build_module(), current_params, desired_params) is True


def test_has_changed_parameters_no_change():
    current_params = [
        {"ParameterName": "array_nulls", "ParameterValue": "0", "ApplyMethod": "immediate", "IsModifiable": True}
    ]
    desired_params = [{"ParameterName": "array_nulls", "ParameterValue": "0", "ApplyMethod": "immediate"}]

    assert has_changed_parameters(build_module(), current_params, desired_params) is False


def test_has_changed_parameters_unset_current_value():
    """A parameter that has never been set has no ParameterValue key."""
    current_params = [{"ParameterName": "array_nulls", "ApplyMethod": "immediate", "IsModifiable": True}]
    desired_params = [{"ParameterName": "array_nulls", "ParameterValue": "0", "ApplyMethod": "immediate"}]

    assert has_changed_parameters(build_module(), current_params, desired_params) is True


def test_has_changed_parameters_unknown_parameter():
    module = build_module()

    with pytest.raises(FailJsonException) as exc:
        has_changed_parameters(module, [], [{"ParameterName": "invalid_fake", "ParameterValue": "test"}])

    assert exc.value.kwargs["msg"] == "Could not find parameter with name: invalid_fake"


def test_has_changed_parameters_not_modifiable():
    module = build_module()
    current_params = [
        {"ParameterName": "archive_library", "ParameterValue": "test", "IsModifiable": False},
    ]

    with pytest.raises(FailJsonException) as exc:
        has_changed_parameters(module, current_params, [{"ParameterName": "archive_library", "ParameterValue": "test"}])

    assert exc.value.kwargs["msg"] == "The parameter archive_library cannot be modified"


# =============================================================================
# modify_parameters
# =============================================================================


@patch(mod_name + ".modify_db_cluster_parameter_group")
@patch(mod_name + ".describe_db_cluster_parameters")
def test_modify_parameters_applies_changes(m_describe, m_modify):
    """All requested parameters are sent, not just the ones that differ."""
    client = MagicMock()
    module = build_module()
    m_describe.return_value = [
        {"ParameterName": "array_nulls", "ParameterValue": "1", "ApplyMethod": "immediate", "IsModifiable": True},
        {
            "ParameterName": "authentication_timeout",
            "ParameterValue": "50",
            "ApplyMethod": "immediate",
            "IsModifiable": True,
        },
    ]
    parameters = [
        {"parameter_name": "array_nulls", "parameter_value": "0", "apply_method": "immediate"},
        {"parameter_name": "authentication_timeout", "parameter_value": "50", "apply_method": "immediate"},
    ]

    assert modify_parameters(client, module, "test-pg", parameters) is True

    m_describe.assert_called_once_with(client, DBClusterParameterGroupName="test-pg")
    m_modify.assert_called_once_with(
        client,
        "test-pg",
        [
            {"ParameterName": "array_nulls", "ParameterValue": "0", "ApplyMethod": "immediate"},
            {"ParameterName": "authentication_timeout", "ParameterValue": "50", "ApplyMethod": "immediate"},
        ],
    )


@patch(mod_name + ".modify_db_cluster_parameter_group")
@patch(mod_name + ".describe_db_cluster_parameters")
def test_modify_parameters_idempotent(m_describe, m_modify):
    module = build_module()
    m_describe.return_value = [
        {"ParameterName": "array_nulls", "ParameterValue": "0", "ApplyMethod": "immediate", "IsModifiable": True}
    ]
    parameters = [{"parameter_name": "array_nulls", "parameter_value": "0", "apply_method": "immediate"}]

    assert modify_parameters(MagicMock(), module, "test-pg", parameters) is False
    m_modify.assert_not_called()


@patch(mod_name + ".modify_db_cluster_parameter_group")
@patch(mod_name + ".describe_db_cluster_parameters")
def test_modify_parameters_check_mode(m_describe, m_modify):
    module = build_module()
    module.check_mode = True
    m_describe.return_value = [
        {"ParameterName": "array_nulls", "ParameterValue": "1", "ApplyMethod": "immediate", "IsModifiable": True}
    ]
    parameters = [{"parameter_name": "array_nulls", "parameter_value": "0", "apply_method": "immediate"}]

    assert modify_parameters(MagicMock(), module, "test-pg", parameters) is True
    m_modify.assert_not_called()


# =============================================================================
# update_parameter_group
# =============================================================================


@patch(mod_name + ".ensure_tags")
@patch(mod_name + ".get_tags")
def test_update_parameter_group_no_tags_requested(m_get_tags, m_ensure_tags):
    module = build_module(tags=None)

    assert update_parameter_group(MagicMock(), module, GROUP) is False
    m_get_tags.assert_not_called()
    m_ensure_tags.assert_not_called()


@patch(mod_name + ".ensure_tags")
@patch(mod_name + ".get_tags")
def test_update_parameter_group_updates_tags(m_get_tags, m_ensure_tags):
    client = MagicMock()
    module = build_module(tags={"a": "b"})
    m_get_tags.return_value = {}
    m_ensure_tags.return_value = True

    assert update_parameter_group(client, module, GROUP) is True
    m_ensure_tags.assert_called_once_with(client, module, GROUP_ARN, {}, {"a": "b"}, True)


@patch(mod_name + ".ensure_tags")
@patch(mod_name + ".get_tags")
def test_update_parameter_group_empty_tags_dict_is_a_no_op(m_get_tags, m_ensure_tags):
    """An empty tags dict leaves existing tags alone, even with purge_tags enabled."""
    module = build_module(tags={})

    assert update_parameter_group(MagicMock(), module, GROUP) is False
    m_get_tags.assert_not_called()
    m_ensure_tags.assert_not_called()


@patch(mod_name + ".ensure_tags")
@patch(mod_name + ".get_tags")
def test_update_parameter_group_warns_on_family_change(m_get_tags, m_ensure_tags):
    module = build_module(db_parameter_group_family="postgres15")
    m_ensure_tags.return_value = False

    update_parameter_group(MagicMock(), module, GROUP)

    module.warn.assert_called_once()
    assert "immutable" in module.warn.call_args.args[0]


# =============================================================================
# ensure_present
# =============================================================================


@patch(mod_name + ".get_tags")
@patch(mod_name + ".create_db_cluster_parameter_group")
@patch(mod_name + ".describe_db_cluster_parameter_groups")
def test_ensure_present_creates(m_describe, m_create, m_get_tags):
    client = MagicMock()
    module = build_module(tags={"a": "b"})
    m_describe.return_value = []
    m_create.return_value = {"DBClusterParameterGroup": GROUP}
    m_get_tags.return_value = {"a": "b"}

    with pytest.raises(ExitJsonException) as exc:
        ensure_present(client, module)

    assert exc.value.kwargs["changed"] is True
    assert exc.value.kwargs["db_cluster_parameter_group"]["db_cluster_parameter_group_name"] == "test-pg"
    assert exc.value.kwargs["db_cluster_parameter_group"]["tags"] == {"a": "b"}
    m_create.assert_called_once_with(
        client,
        DBClusterParameterGroupName="test-pg",
        DBParameterGroupFamily="postgres16",
        Description="test cluster param group",
        Tags=[{"Key": "a", "Value": "b"}],
    )
    # The group returned by the create call is reused instead of describing it again.
    m_describe.assert_called_once()


@patch(mod_name + ".create_db_cluster_parameter_group")
@patch(mod_name + ".describe_db_cluster_parameter_groups")
def test_ensure_present_create_check_mode(m_describe, m_create):
    module = build_module()
    module.check_mode = True
    m_describe.return_value = []

    with pytest.raises(ExitJsonException) as exc:
        ensure_present(MagicMock(), module)

    assert exc.value.kwargs["changed"] is True
    m_create.assert_not_called()


@patch(mod_name + ".get_tags")
@patch(mod_name + ".update_parameter_group")
@patch(mod_name + ".describe_db_cluster_parameter_groups")
def test_ensure_present_idempotent(m_describe, m_update, m_get_tags):
    module = build_module()
    m_describe.return_value = [GROUP]
    m_update.return_value = False
    m_get_tags.return_value = {}

    with pytest.raises(ExitJsonException) as exc:
        ensure_present(MagicMock(), module)

    assert exc.value.kwargs["changed"] is False


@patch(mod_name + ".get_tags")
@patch(mod_name + ".modify_parameters")
@patch(mod_name + ".update_parameter_group")
@patch(mod_name + ".describe_db_cluster_parameter_groups")
def test_ensure_present_modifies_parameters(m_describe, m_update, m_modify, m_get_tags):
    parameters = [{"parameter_name": "array_nulls", "parameter_value": "0", "apply_method": "immediate"}]
    module = build_module(parameters=parameters)
    m_describe.return_value = [GROUP]
    m_update.return_value = False
    m_modify.return_value = True
    m_get_tags.return_value = {}

    with pytest.raises(ExitJsonException) as exc:
        ensure_present(MagicMock(), module)

    assert exc.value.kwargs["changed"] is True
    m_modify.assert_called_once()


# =============================================================================
# ensure_absent
# =============================================================================


@patch(mod_name + ".delete_db_cluster_parameter_group")
@patch(mod_name + ".describe_db_cluster_parameter_groups")
def test_ensure_absent_deletes(m_describe, m_delete):
    client = MagicMock()
    module = build_module(state="absent")
    m_describe.return_value = [GROUP]

    with pytest.raises(ExitJsonException) as exc:
        ensure_absent(client, module)

    assert exc.value.kwargs["changed"] is True
    m_delete.assert_called_once_with(client, "test-pg")


@patch(mod_name + ".delete_db_cluster_parameter_group")
@patch(mod_name + ".describe_db_cluster_parameter_groups")
def test_ensure_absent_check_mode(m_describe, m_delete):
    module = build_module(state="absent")
    module.check_mode = True
    m_describe.return_value = [GROUP]

    with pytest.raises(ExitJsonException) as exc:
        ensure_absent(MagicMock(), module)

    assert exc.value.kwargs["changed"] is True
    m_delete.assert_not_called()


@patch(mod_name + ".delete_db_cluster_parameter_group")
@patch(mod_name + ".describe_db_cluster_parameter_groups")
def test_ensure_absent_already_gone(m_describe, m_delete):
    module = build_module(state="absent")
    m_describe.return_value = []

    with pytest.raises(ExitJsonException) as exc:
        ensure_absent(MagicMock(), module)

    assert exc.value.kwargs["changed"] is False
    m_delete.assert_not_called()
