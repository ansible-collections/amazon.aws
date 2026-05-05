# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock

import pytest

from ansible.errors import AnsibleLookupError

from ansible_collections.amazon.aws.plugins.lookup.ssm_parameter import LookupModule


@pytest.fixture(name="lookup_plugin")
def fixture_lookup_plugin():
    lookup = LookupModule()
    lookup.params = {}

    lookup.get_option = MagicMock()

    def _get_option(x):
        return lookup.params.get(x)

    lookup.get_option.side_effect = _get_option
    lookup.client = MagicMock()
    lookup._display = MagicMock()

    return lookup


class TestValidateOptions:
    """Unit tests for _validate_options helper method"""

    def test_validate_valid_options(self, lookup_plugin):
        """Test that valid options don't raise errors"""
        # Should not raise
        lookup_plugin.params = {"on_missing": "error", "on_denied": "warn"}
        lookup_plugin._validate_options()
        lookup_plugin.params = {"on_missing": "warn", "on_denied": "skip"}
        lookup_plugin._validate_options()
        lookup_plugin.params = {"on_missing": "skip", "on_denied": "error"}
        lookup_plugin._validate_options()

    @pytest.mark.parametrize(
        "on_missing,expected_error",
        [
            ("invalid", '"on_missing" must be a string and one of "error", "warn" or "skip", not invalid'),
        ],
    )
    def test_validate_invalid_on_missing(self, lookup_plugin, on_missing, expected_error):
        """Test that invalid on_missing values raise errors"""
        lookup_plugin.params = {"on_missing": on_missing, "on_denied": "error"}
        with pytest.raises(AnsibleLookupError) as exc_info:
            lookup_plugin._validate_options()
        assert expected_error == str(exc_info.value)

    @pytest.mark.parametrize(
        "on_denied,expected_error",
        [
            ("invalid", '"on_denied" must be a string and one of "error", "warn" or "skip", not invalid'),
        ],
    )
    def test_validate_invalid_on_denied(self, lookup_plugin, on_denied, expected_error):
        """Test that invalid on_denied values raise errors"""
        lookup_plugin.params = {"on_missing": "error", "on_denied": on_denied}
        with pytest.raises(AnsibleLookupError) as exc_info:
            lookup_plugin._validate_options()
        assert expected_error == str(exc_info.value)

    def test_validate_shortnames_droppath_mutually_exclusive(self, lookup_plugin):
        """Test that shortnames and droppath cannot both be True"""
        lookup_plugin.params = {"shortnames": True, "droppath": True, "on_missing": "error", "on_denied": "error"}

        with pytest.raises(AnsibleLookupError) as exc_info:
            lookup_plugin._validate_options()
        assert "shortnames and droppath are mutually exclusive" in str(exc_info.value)

    def test_validate_shortnames_only(self, lookup_plugin):
        """Test that shortnames=True alone is valid"""
        lookup_plugin.params = {"shortnames": True, "droppath": False, "on_missing": "error", "on_denied": "error"}
        # Should not raise
        lookup_plugin._validate_options()

    def test_validate_droppath_only(self, lookup_plugin):
        """Test that droppath=True alone is valid"""
        lookup_plugin.params = {"shortnames": False, "droppath": True, "on_missing": "error", "on_denied": "error"}
        # Should not raise
        lookup_plugin._validate_options()


class TestProcessParameterNames:
    """Unit tests for _process_parameter_names helper method"""

    def test_process_no_options(self, lookup_plugin):
        """Test that parameters are unchanged when no options are set"""
        lookup_plugin.params = {"shortnames": False, "droppath": False}
        paramlist = [
            {"Name": "/app/prod/database/password", "Value": "secret1"},
            {"Name": "/app/prod/database/username", "Value": "admin"},
        ]

        lookup_plugin._process_parameter_names(paramlist, "/app/prod/")

        assert paramlist[0]["Name"] == "/app/prod/database/password"
        assert paramlist[1]["Name"] == "/app/prod/database/username"

    def test_process_shortnames(self, lookup_plugin):
        """Test that shortnames extracts the final path component"""
        lookup_plugin.params = {"shortnames": True, "droppath": False}
        paramlist = [
            {"Name": "/app/prod/database/password", "Value": "secret1"},
            {"Name": "/app/prod/database/username", "Value": "admin"},
            {"Name": "/app/prod/api/key", "Value": "key123"},
        ]

        lookup_plugin._process_parameter_names(paramlist, "/app/prod/")

        assert paramlist[0]["Name"] == "password"
        assert paramlist[1]["Name"] == "username"
        assert paramlist[2]["Name"] == "key"

    def test_process_shortnames_no_slash(self, lookup_plugin):
        """Test shortnames with parameter name that has no slashes"""
        lookup_plugin.params = {"shortnames": True, "droppath": False}
        paramlist = [{"Name": "simple-name", "Value": "value1"}]

        lookup_plugin._process_parameter_names(paramlist, "/app/")

        # rfind returns -1 when not found, so [-1+1:] gives the whole string
        assert paramlist[0]["Name"] == "simple-name"

    def test_process_droppath(self, lookup_plugin):
        """Test that droppath removes the specified path prefix"""
        lookup_plugin.params = {"shortnames": False, "droppath": True}
        paramlist = [
            {"Name": "/app/prod/database/password", "Value": "secret1"},
            {"Name": "/app/prod/database/username", "Value": "admin"},
            {"Name": "/app/prod/api/key", "Value": "key123"},
        ]

        lookup_plugin._process_parameter_names(paramlist, "/app/prod/")

        assert paramlist[0]["Name"] == "database/password"
        assert paramlist[1]["Name"] == "database/username"
        assert paramlist[2]["Name"] == "api/key"

    def test_process_droppath_no_match(self, lookup_plugin):
        """Test droppath when the path doesn't match"""
        lookup_plugin.params = {"shortnames": False, "droppath": True}
        paramlist = [{"Name": "/other/path/param", "Value": "value1"}]

        lookup_plugin._process_parameter_names(paramlist, "/app/prod/")

        # Path not in name, so it remains unchanged
        assert paramlist[0]["Name"] == "/other/path/param"

    def test_process_empty_paramlist(self, lookup_plugin):
        """Test processing an empty parameter list"""
        lookup_plugin.params = {"shortnames": True, "droppath": False}
        paramlist = []

        # Should not raise
        lookup_plugin._process_parameter_names(paramlist, "/app/prod/")

        assert paramlist == []


class TestGetPathParameters:
    """Unit tests for get_path_parameters method"""

    def test_get_path_parameters_empty_list_error(self, lookup_plugin):
        """Test that empty paramlist with on_missing='error' raises error"""
        lookup_plugin.params = {"on_missing": "error"}
        lookup_plugin._cached_on_missing = "error"

        client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value.build_full_result.return_value = {"Parameters": []}
        client.get_paginator.return_value = paginator
        lookup_plugin._cached_client = client

        with pytest.raises(AnsibleLookupError) as exc_info:
            lookup_plugin.get_path_parameters("/app/missing/", {})

        assert "Failed to find SSM parameter path /app/missing/ (ResourceNotFound)" == str(exc_info.value)

    def test_get_path_parameters_empty_list_warn(self, lookup_plugin):
        """Test that empty paramlist with on_missing='warn' returns empty and warns"""
        lookup_plugin.params = {"on_missing": "warn"}
        lookup_plugin._cached_on_missing = "warn"
        lookup_plugin.warn = MagicMock()

        client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value.build_full_result.return_value = {"Parameters": []}
        client.get_paginator.return_value = paginator
        lookup_plugin._cached_client = client

        result = lookup_plugin.get_path_parameters("/app/missing/", {})

        assert result == []
        lookup_plugin.warn.assert_called_once_with("Skipping, did not find SSM parameter path /app/missing/")

    def test_get_path_parameters_empty_list_skip(self, lookup_plugin):
        """Test that empty paramlist with on_missing='skip' returns empty silently"""
        lookup_plugin.params = {"on_missing": "skip"}
        lookup_plugin._cached_on_missing = "skip"
        lookup_plugin.warn = MagicMock()

        client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value.build_full_result.return_value = {"Parameters": []}
        client.get_paginator.return_value = paginator
        lookup_plugin._cached_client = client

        result = lookup_plugin.get_path_parameters("/app/missing/", {})

        assert result == []
        lookup_plugin.warn.assert_not_called()

    def test_get_path_parameters_with_results(self, lookup_plugin):
        """Test that non-empty paramlist is returned successfully"""
        lookup_plugin.params = {"on_missing": "error"}
        lookup_plugin._cached_on_missing = "error"

        client = MagicMock()
        paginator = MagicMock()
        expected_params = [
            {"Name": "/app/prod/db/password", "Value": "secret1"},
            {"Name": "/app/prod/db/username", "Value": "admin"},
        ]
        paginator.paginate.return_value.build_full_result.return_value = {"Parameters": expected_params}
        client.get_paginator.return_value = paginator
        lookup_plugin._cached_client = client

        result = lookup_plugin.get_path_parameters("/app/prod/", {})

        assert result == expected_params


class TestLookupByName:
    """Unit tests for _lookup_by_name orchestration"""

    def test_lookup_by_name_preserves_none_values(self, lookup_plugin):
        """Test that None values are preserved (on_missing/on_denied='skip')"""
        lookup_plugin.params = {"recursive": False}
        lookup_plugin.get_parameter_value = MagicMock(side_effect=["value-1", None, "value-3"])

        result = lookup_plugin._lookup_by_name({}, ["param-1", "param-2", "param-3"])

        assert result == ["value-1", None, "value-3"]

    def test_lookup_by_name_all_none_returns_empty_list(self, lookup_plugin):
        """Test that all None values returns empty list (all params missing/denied)"""
        lookup_plugin.params = {"recursive": False}
        lookup_plugin.get_parameter_value = MagicMock(return_value=None)

        result = lookup_plugin._lookup_by_name({}, ["param-1", "param-2"])

        assert result == []

    def test_lookup_by_name_successful(self, lookup_plugin):
        """Test successful parameter lookups"""
        lookup_plugin.params = {"recursive": False}
        lookup_plugin.get_parameter_value = MagicMock(side_effect=["value-1", "value-2"])

        result = lookup_plugin._lookup_by_name({}, ["param-1", "param-2"])

        assert result == ["value-1", "value-2"]
