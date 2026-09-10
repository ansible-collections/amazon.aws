# (c) 2026 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.modules.rds_cluster_param_group_info import (
    describe_rds_cluster_parameter_group,
)

mod_name = "ansible_collections.amazon.aws.plugins.modules.rds_cluster_param_group_info"

GROUP = {
    "DBClusterParameterGroupName": "test-pg",
    "DBClusterParameterGroupArn": "arn:aws:rds:us-east-1:123456789012:cluster-pg:test-pg",
    "DBParameterGroupFamily": "postgres16",
}


class ExitJsonException(Exception):
    """Raised by the mocked module.exit_json() so tests can assert on the result."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        super().__init__("exit_json")


def raise_exit_json(**kwargs):
    raise ExitJsonException(**kwargs)


def build_module(**params):
    module = MagicMock()
    module.params = {"name": None, "include_parameters": None}
    module.params.update(params)
    module.exit_json.side_effect = raise_exit_json
    return module


@patch(mod_name + ".describe_db_cluster_parameters")
@patch(mod_name + ".get_tags")
@patch(mod_name + ".describe_db_cluster_parameter_groups")
def test_describe_by_name(m_describe_groups, m_get_tags, m_describe_params):
    client = MagicMock()
    module = build_module(name="test-pg")
    m_describe_groups.return_value = [dict(GROUP)]
    m_get_tags.return_value = {"a": "b"}

    with pytest.raises(ExitJsonException) as exc:
        describe_rds_cluster_parameter_group(client, module)

    m_describe_groups.assert_called_once_with(client, DBClusterParameterGroupName="test-pg")
    m_describe_params.assert_not_called()
    groups = exc.value.kwargs["db_cluster_parameter_groups"]
    assert len(groups) == 1
    assert groups[0]["db_cluster_parameter_group_name"] == "test-pg"
    assert groups[0]["tags"] == {"a": "b"}


@patch(mod_name + ".get_tags")
@patch(mod_name + ".describe_db_cluster_parameter_groups")
def test_describe_all_groups(m_describe_groups, m_get_tags):
    client = MagicMock()
    module = build_module()
    m_describe_groups.return_value = []

    with pytest.raises(ExitJsonException) as exc:
        describe_rds_cluster_parameter_group(client, module)

    m_describe_groups.assert_called_once_with(client)
    assert exc.value.kwargs["db_cluster_parameter_groups"] == []


@patch(mod_name + ".describe_db_cluster_parameters")
@patch(mod_name + ".get_tags")
@patch(mod_name + ".describe_db_cluster_parameter_groups")
def test_include_parameters_all_omits_source_filter(m_describe_groups, m_get_tags, m_describe_params):
    client = MagicMock()
    module = build_module(name="test-pg", include_parameters="all")
    m_describe_groups.return_value = [dict(GROUP)]
    m_describe_params.return_value = [{"ParameterName": "array_nulls"}]

    with pytest.raises(ExitJsonException) as exc:
        describe_rds_cluster_parameter_group(client, module)

    m_describe_params.assert_called_once_with(client, DBClusterParameterGroupName="test-pg")
    assert exc.value.kwargs["db_cluster_parameter_groups"][0]["db_parameters"][0]["parameter_name"] == "array_nulls"


@patch(mod_name + ".describe_db_cluster_parameters")
@patch(mod_name + ".get_tags")
@patch(mod_name + ".describe_db_cluster_parameter_groups")
def test_include_parameters_source_filter(m_describe_groups, m_get_tags, m_describe_params):
    client = MagicMock()
    module = build_module(name="test-pg", include_parameters="user")
    m_describe_groups.return_value = [dict(GROUP)]
    m_describe_params.return_value = []

    with pytest.raises(ExitJsonException):
        describe_rds_cluster_parameter_group(client, module)

    m_describe_params.assert_called_once_with(client, DBClusterParameterGroupName="test-pg", Source="user")
