#
# (c) 2024 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from ansible.errors import AnsibleLookupError

from ansible_collections.amazon.aws.plugins.lookup.secretsmanager_secret import LookupModule


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


def _raise_boto_clienterror(code, msg):
    params = {
        "Error": {"Code": code, "Message": msg},
        "ResponseMetadata": {"RequestId": "01234567-89ab-cdef-0123-456789abcdef"},
    }
    return ClientError(params, "get_secret_value")


class TestValidateOptions:
    """Unit tests for _validate_options helper method"""

    @pytest.mark.parametrize(
        "on_missing,expected_error",
        [
            ("invalid", '"on_missing" must be a string and one of "error", "warn" or "skip", not invalid'),
        ],
    )
    def test_validate_invalid_on_missing(self, lookup_plugin, on_missing, expected_error):
        """Test that invalid on_missing values raise errors"""
        lookup_plugin.params = {"on_missing": on_missing, "on_denied": "error", "on_deleted": "error"}
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
        lookup_plugin.params = {"on_missing": "error", "on_denied": on_denied, "on_deleted": "error"}
        with pytest.raises(AnsibleLookupError) as exc_info:
            lookup_plugin._validate_options()
        assert expected_error == str(exc_info.value)

    @pytest.mark.parametrize(
        "on_deleted,expected_error",
        [
            ("delete", '"on_deleted" must be a string and one of "error", "warn" or "skip", not delete'),
        ],
    )
    def test_validate_invalid_on_deleted(self, lookup_plugin, on_deleted, expected_error):
        """Test that invalid on_deleted values raise errors"""
        lookup_plugin.params = {"on_missing": "error", "on_denied": "error", "on_deleted": on_deleted}
        with pytest.raises(AnsibleLookupError) as exc_info:
            lookup_plugin._validate_options()
        assert expected_error == str(exc_info.value)

    def test_validate_valid_options(self, lookup_plugin):
        """Test that valid options don't raise errors"""
        # Should not raise
        lookup_plugin.params = {"on_missing": "error", "on_denied": "warn", "on_deleted": "skip"}
        lookup_plugin._validate_options()
        lookup_plugin.params = {"on_missing": "warn", "on_denied": "skip", "on_deleted": "error"}
        lookup_plugin._validate_options()
        lookup_plugin.params = {"on_missing": "skip", "on_denied": "error", "on_deleted": "warn"}
        lookup_plugin._validate_options()


class TestLookupModuleGetSecretValue:
    """Integration tests for get_secret_value - tests full flow with decorator"""

    def test_get_secret_value_integration(self, lookup_plugin):
        """Test complete get_secret_value flow"""
        client = MagicMock()
        client.get_secret_value = MagicMock()
        client.get_secret_value.return_value = {"SecretString": "my-secret-value"}
        lookup_plugin._cached_client = client

        result = lookup_plugin.get_secret_value("my-secret", version_stage="AWSCURRENT", version_id="v123")

        assert result == "my-secret-value"
        client.get_secret_value.assert_called_once_with(
            aws_retry=True, SecretId="my-secret", VersionStage="AWSCURRENT", VersionId="v123"
        )

    def test_get_secret_value_nested_integration(self, lookup_plugin):
        """Test nested value extraction integration"""
        client = MagicMock()
        client.get_secret_value = MagicMock()
        json_secret = '{"db": {"password": "secret123"}}'
        client.get_secret_value.return_value = {"SecretString": json_secret}
        lookup_plugin._cached_client = client

        result = lookup_plugin.get_secret_value("my-secret.db.password", nested=True)

        assert result == "secret123"
        # Nested=True extracts just the secret name for the API call
        client.get_secret_value.assert_called_once_with(aws_retry=True, SecretId="my-secret")


class TestBuildSecretParams:
    """Unit tests for _build_secret_params helper method"""

    def test_build_params_simple_term(self, lookup_plugin):
        """Test building params with just a term"""
        params = lookup_plugin._build_secret_params("my-secret", None, None, False)
        assert params == {"SecretId": "my-secret"}

    def test_build_params_with_version_id(self, lookup_plugin):
        """Test building params with version_id"""
        params = lookup_plugin._build_secret_params("my-secret", "version-123", None, False)
        assert params == {"SecretId": "my-secret", "VersionId": "version-123"}

    def test_build_params_with_version_stage(self, lookup_plugin):
        """Test building params with version_stage"""
        params = lookup_plugin._build_secret_params("my-secret", None, "AWSCURRENT", False)
        assert params == {"SecretId": "my-secret", "VersionStage": "AWSCURRENT"}

    def test_build_params_with_both_versions(self, lookup_plugin):
        """Test building params with both version_id and version_stage"""
        params = lookup_plugin._build_secret_params("my-secret", "version-123", "AWSCURRENT", False)
        assert params == {"SecretId": "my-secret", "VersionId": "version-123", "VersionStage": "AWSCURRENT"}

    def test_build_params_nested_extracts_secret_name(self, lookup_plugin):
        """Test that nested=True extracts secret name from dotted path"""
        params = lookup_plugin._build_secret_params("my-secret.root.child", None, None, True)
        assert params == {"SecretId": "my-secret"}

    def test_build_params_nested_with_versions(self, lookup_plugin):
        """Test nested with version parameters"""
        params = lookup_plugin._build_secret_params("my-secret.root.child", "version-123", "AWSCURRENT", True)
        assert params == {"SecretId": "my-secret", "VersionId": "version-123", "VersionStage": "AWSCURRENT"}

    def test_build_params_nested_invalid_raises_error(self, lookup_plugin):
        """Test that nested=True with no dots raises error"""
        with pytest.raises(AnsibleLookupError) as exc_info:
            lookup_plugin._build_secret_params("my-secret", None, None, True)
        assert "Nested query must use the following syntax" in str(exc_info.value)


class TestProcessSecretResponse:
    """Unit tests for _process_secret_response helper method"""

    def test_process_binary_response(self, lookup_plugin):
        """Test processing response with SecretBinary"""
        response = {"SecretBinary": b"binary-data"}
        result = lookup_plugin._process_secret_response(response, "my-secret", False)
        assert result == b"binary-data"

    def test_process_string_response_non_nested(self, lookup_plugin):
        """Test processing response with SecretString (non-nested)"""
        response = {"SecretString": "my-secret-value"}
        result = lookup_plugin._process_secret_response(response, "my-secret", False)
        assert result == "my-secret-value"

    def test_process_string_response_nested(self, lookup_plugin, mocker):
        """Test processing response with SecretString (nested)"""
        response = {"SecretString": '{"key": "value"}'}
        mock_extract = mocker.patch.object(lookup_plugin, "_extract_nested_value", return_value="extracted-value")

        result = lookup_plugin._process_secret_response(response, "my-secret.key", True)

        assert result == "extracted-value"
        mock_extract.assert_called_once_with('{"key": "value"}', "my-secret.key")

    def test_process_empty_response(self, lookup_plugin):
        """Test processing response with neither SecretBinary nor SecretString"""
        response = {"ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:my-secret"}
        result = lookup_plugin._process_secret_response(response, "my-secret", False)
        assert result is None


class TestExtractNestedValue:
    """Unit tests for _extract_nested_value helper method"""

    def test_extract_single_key(self, lookup_plugin):
        """Test extracting a single nested key"""
        secret_string = '{"password": "secret123"}'
        result = lookup_plugin._extract_nested_value(secret_string, "my-secret.password")
        assert result == "secret123"

    def test_extract_nested_keys(self, lookup_plugin):
        """Test extracting deeply nested keys"""
        secret_string = '{"db": {"prod": {"password": "secret123"}}}'
        result = lookup_plugin._extract_nested_value(secret_string, "my-secret.db.prod.password")
        assert result == "secret123"

    def test_extract_number_converts_to_string(self, lookup_plugin):
        """Test that numeric values are converted to strings"""
        secret_string = '{"port": 5432}'
        result = lookup_plugin._extract_nested_value(secret_string, "my-secret.port")
        assert result == "5432"
        assert isinstance(result, str)

    def test_extract_boolean_converts_to_string(self, lookup_plugin):
        """Test that boolean values are converted to strings"""
        secret_string = '{"enabled": true}'
        result = lookup_plugin._extract_nested_value(secret_string, "my-secret.enabled")
        assert result == "True"
        assert isinstance(result, str)

    def test_extract_object_converts_to_string(self, lookup_plugin):
        """Test that object values are converted to strings"""
        secret_string = '{"config": {"host": "localhost", "port": 5432}}'
        result = lookup_plugin._extract_nested_value(secret_string, "my-secret.config")
        # Python dict str representation
        assert "host" in result
        assert "localhost" in result

    def test_extract_missing_key_raises_nested_error(self, lookup_plugin):
        """Test that missing keys raise LookupResourceNotFoundError"""
        from ansible_collections.amazon.aws.plugins.plugin_utils.lookup import LookupResourceNotFoundError

        secret_string = '{"db": {"prod": {"password": "secret123"}}}'

        with pytest.raises(LookupResourceNotFoundError) as exc_info:
            lookup_plugin._extract_nested_value(secret_string, "my-secret.db.staging.password")

        assert exc_info.value.path == "db.staging"

    def test_extract_key_from_non_dict_raises_nested_error(self, lookup_plugin):
        """Test that trying to traverse a non-dict raises LookupResourceNotFoundError"""
        from ansible_collections.amazon.aws.plugins.plugin_utils.lookup import LookupResourceNotFoundError

        secret_string = '{"password": "secret123"}'

        # Trying to access password.nested when password is a string, not a dict
        with pytest.raises(LookupResourceNotFoundError) as exc_info:
            lookup_plugin._extract_nested_value(secret_string, "my-secret.password.nested")

        assert exc_info.value.path == "password.nested"


class TestFetchSecretList:
    """Unit tests for _fetch_secret_list helper method"""

    def test_fetch_single_page(self, lookup_plugin):
        """Test fetching secrets from a single page"""
        client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = [
            {"SecretList": [{"Name": "secret-1", "ARN": "arn:1"}, {"Name": "secret-2", "ARN": "arn:2"}]}
        ]
        client.get_paginator.return_value = paginator
        lookup_plugin._cached_client = client

        result = lookup_plugin._fetch_secret_list("/app/prod/*")

        assert len(result) == 2
        assert result[0]["Name"] == "secret-1"
        assert result[1]["Name"] == "secret-2"
        client.get_paginator.assert_called_once_with("list_secrets")
        paginator.paginate.assert_called_once_with(Filters=[{"Key": "name", "Values": ["/app/prod/*"]}])

    def test_fetch_multiple_pages(self, lookup_plugin):
        """Test fetching secrets across multiple pages"""
        client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = [
            {"SecretList": [{"Name": "secret-1"}, {"Name": "secret-2"}]},
            {"SecretList": [{"Name": "secret-3"}]},
            {"SecretList": [{"Name": "secret-4"}, {"Name": "secret-5"}]},
        ]
        client.get_paginator.return_value = paginator
        lookup_plugin._cached_client = client

        result = lookup_plugin._fetch_secret_list("/app/*")

        assert len(result) == 5
        assert [s["Name"] for s in result] == ["secret-1", "secret-2", "secret-3", "secret-4", "secret-5"]

    def test_fetch_empty_results(self, lookup_plugin):
        """Test fetching when no secrets match"""
        client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = [{"SecretList": []}]
        client.get_paginator.return_value = paginator
        lookup_plugin._cached_client = client
        lookup_plugin._cached_on_missing = "skip"

        result = lookup_plugin._fetch_secret_list("/nonexistent/*")

        assert result == []

    def test_fetch_page_without_secret_list(self, lookup_plugin):
        """Test handling pages without SecretList key"""
        client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = [
            {"SecretList": [{"Name": "secret-1"}]},
            {"NextToken": "token123"},  # Page without SecretList
            {"SecretList": [{"Name": "secret-2"}]},
        ]
        client.get_paginator.return_value = paginator
        lookup_plugin._cached_client = client

        result = lookup_plugin._fetch_secret_list("/app/*")

        assert len(result) == 2
        assert result[0]["Name"] == "secret-1"
        assert result[1]["Name"] == "secret-2"


class TestLookupByPath:
    """Unit tests for _lookup_by_path orchestration"""

    def test_lookup_by_path_single_term(self, lookup_plugin):
        """Test path lookup with single term"""
        lookup_plugin._fetch_secret_list = MagicMock(return_value=[{"Name": "secret-1"}, {"Name": "secret-2"}])
        lookup_plugin.get_secret_value = MagicMock(side_effect=lambda name: f"value-{name}")

        result = lookup_plugin._lookup_by_path(["/app/prod/*"])

        assert result == [{"secret-1": "value-secret-1", "secret-2": "value-secret-2"}]
        lookup_plugin._fetch_secret_list.assert_called_once_with("/app/prod/*")

    def test_lookup_by_path_multiple_terms(self, lookup_plugin):
        """Test path lookup with multiple terms"""
        lookup_plugin._fetch_secret_list = MagicMock(
            side_effect=[
                [{"Name": "secret-1"}],
                [{"Name": "secret-2"}],
            ]
        )
        lookup_plugin.get_secret_value = MagicMock(side_effect=lambda name: f"value-{name}")

        result = lookup_plugin._lookup_by_path(["/app/prod/*", "/app/staging/*"])

        assert result == [{"secret-1": "value-secret-1", "secret-2": "value-secret-2"}]

    def test_lookup_by_path_skips_none_values(self, lookup_plugin):
        """Test that None values are skipped (on_missing/on_denied='skip')"""
        lookup_plugin._fetch_secret_list = MagicMock(
            return_value=[{"Name": "secret-1"}, {"Name": "secret-2"}, {"Name": "secret-3"}]
        )
        # Simulate skip behavior: some return None
        lookup_plugin.get_secret_value = MagicMock(side_effect=["value-1", None, "value-3"])

        result = lookup_plugin._lookup_by_path(["/app/*"])

        assert result == [{"secret-1": "value-1", "secret-3": "value-3"}]

    def test_lookup_by_path_all_none_returns_empty(self, lookup_plugin):
        """Test that all None values returns empty list"""
        lookup_plugin._fetch_secret_list = MagicMock(return_value=[{"Name": "secret-1"}, {"Name": "secret-2"}])
        lookup_plugin.get_secret_value = MagicMock(return_value=None)

        result = lookup_plugin._lookup_by_path(["/app/*"])

        assert result == []

    def test_lookup_by_path_empty_secret_list(self, lookup_plugin):
        """Test path lookup when no secrets found"""
        lookup_plugin._fetch_secret_list = MagicMock(return_value=[])

        result = lookup_plugin._lookup_by_path(["/nonexistent/*"])

        assert result == []


class TestLookupByName:
    """Unit tests for _lookup_by_name orchestration"""

    def test_lookup_by_name_filters_none_values(self, lookup_plugin):
        """Test that None values are filtered in non-join mode"""
        lookup_plugin.params = {"join": False, "version_stage": None, "version_id": None, "nested": False}
        lookup_plugin.get_secret_value = MagicMock(side_effect=["value-1", None, "value-3"])

        result = lookup_plugin._lookup_by_name(["secret-1", "secret-2", "secret-3"])

        assert result == ["value-1", "value-3"]

    def test_lookup_by_name_all_none_returns_empty(self, lookup_plugin):
        """Test that all None values returns empty list in non-join mode"""
        lookup_plugin.params = {"join": False, "version_stage": None, "version_id": None, "nested": False}
        lookup_plugin.get_secret_value = MagicMock(return_value=None)

        result = lookup_plugin._lookup_by_name(["secret-1", "secret-2"])

        assert result == []

    def test_lookup_by_name_join_mode(self, lookup_plugin):
        """Test join mode concatenates non-None values"""
        lookup_plugin.params = {"join": True, "version_stage": None, "version_id": None, "nested": False}
        lookup_plugin.get_secret_value = MagicMock(side_effect=["part1", None, "part2"])

        result = lookup_plugin._lookup_by_name(["secret-1", "secret-2", "secret-3"])

        assert result == ["part1part2"]
