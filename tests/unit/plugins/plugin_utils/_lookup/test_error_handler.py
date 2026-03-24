# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from ansible.errors import AnsibleLookupError

from ansible_collections.amazon.aws.plugins.plugin_utils._lookup.common import LookupErrorHandler
from ansible_collections.amazon.aws.plugins.plugin_utils._lookup.common import LookupResourceNotFoundError


def _raise_boto_clienterror(code, msg):
    """Helper to create a ClientError"""
    params = {
        "Error": {"Code": code, "Message": msg},
        "ResponseMetadata": {"RequestId": "01234567-89ab-cdef-0123-456789abcdef"},
    }
    return ClientError(params, "test_operation")


class MockLookup:
    """Mock lookup class for testing the decorator"""

    def __init__(self):
        self._display = MagicMock()
        self.warn = MagicMock()
        self.aws_client = MagicMock()
        # Set default values for cached properties
        self.on_missing = "error"
        self.on_denied = "error"
        self.on_deleted = "error"


class TestHandleResponse:
    """Unit tests for _handle_response static method"""

    def test_handle_response_error_action(self):
        """Test _handle_response raises error for 'error' action"""
        lookup_instance = MagicMock()

        with pytest.raises(AnsibleLookupError) as exc_info:
            LookupErrorHandler._handle_response(
                lookup_instance,
                action="error",
                term="test-resource",
                resource_type="secret",
                error_msg="Failed to find secret {term}",
                warn_msg="Skipping {term}",
            )
        assert "Failed to find secret test-resource" in str(exc_info.value)

    def test_handle_response_warn_action(self):
        """Test _handle_response logs warning for 'warn' action"""
        lookup_instance = MagicMock()

        result = LookupErrorHandler._handle_response(
            lookup_instance,
            action="warn",
            term="test-resource",
            resource_type="secret",
            error_msg="Failed",
            warn_msg="Skipping {term}",
        )

        assert result is None
        lookup_instance.warn.assert_called_once_with("Skipping test-resource")

    def test_handle_response_skip_action(self):
        """Test _handle_response returns None for 'skip' action"""
        lookup_instance = MagicMock()

        result = LookupErrorHandler._handle_response(
            lookup_instance,
            action="skip",
            term="test-resource",
            resource_type="secret",
            error_msg="Failed",
            warn_msg="Skipping {term}",
        )

        assert result is None
        lookup_instance._display.warning.assert_not_called()

    def test_handle_response_default_value(self):
        """Test _handle_response returns default_value for skip/warn"""
        lookup_instance = MagicMock()
        default_value = [{"test": "value"}]

        result = LookupErrorHandler._handle_response(
            lookup_instance,
            action="skip",
            term="test-resource",
            resource_type="secret",
            error_msg="Failed",
            warn_msg="Skipping",
            default_value=default_value,
        )

        assert result == default_value

    def test_handle_response_message_formatting(self):
        """Test message templates are formatted correctly"""
        lookup_instance = MagicMock()

        with pytest.raises(AnsibleLookupError) as exc_info:
            LookupErrorHandler._handle_response(
                lookup_instance,
                action="error",
                term="my-secret",
                resource_type="secret",
                error_msg="Cannot access secret '{term}' (AccessDenied)",
                warn_msg="Skipping",
            )
        assert "Cannot access secret 'my-secret' (AccessDenied)" == str(exc_info.value)


class TestLookupErrorHandler:
    """Tests for the LookupErrorHandler decorator"""

    def test_handle_lookup_errors_success(self):
        """Test decorator allows successful calls to pass through"""
        mock_lookup = MockLookup()
        mock_lookup.aws_client.get_value.return_value = {"Value": "test-value"}

        @LookupErrorHandler.handle_lookup_errors("test resource")
        def get_value(self, term, on_missing=None, on_denied=None, on_deleted=None):
            return self.aws_client.get_value(Name=term)

        result = get_value(mock_lookup, "test-term")
        assert result == {"Value": "test-value"}
        mock_lookup.aws_client.get_value.assert_called_once_with(Name="test-term")

    @pytest.mark.parametrize("on_missing", ["error", "warn", "skip"])
    def test_handle_resource_not_found(self, on_missing):
        """Test decorator handles ResourceNotFoundException correctly"""
        mock_lookup = MockLookup()
        mock_lookup.on_missing = on_missing
        mock_lookup.aws_client.get_value.side_effect = _raise_boto_clienterror(
            "ResourceNotFoundException", "Resource not found"
        )

        @LookupErrorHandler.handle_lookup_errors("test resource")
        def get_value(self, term):
            return self.aws_client.get_value(Name=term)

        if on_missing == "error":
            with pytest.raises(AnsibleLookupError) as exc_info:
                get_value(mock_lookup, "missing-resource")
            assert "Failed to find test resource missing-resource (ResourceNotFound)" == str(exc_info.value)
        else:
            result = get_value(mock_lookup, "missing-resource")
            assert result is None
            if on_missing == "warn":
                mock_lookup.warn.assert_called_once_with(
                    "Skipping, did not find test resource missing-resource"
                )

    @pytest.mark.parametrize("on_missing", ["error", "warn", "skip"])
    def test_handle_parameter_not_found(self, on_missing):
        """Test decorator handles ParameterNotFound correctly"""
        mock_lookup = MockLookup()
        mock_lookup.on_missing = on_missing
        mock_lookup.aws_client.get_value.side_effect = _raise_boto_clienterror(
            "ParameterNotFound", "Parameter not found"
        )

        @LookupErrorHandler.handle_lookup_errors("SSM parameter")
        def get_value(self, term):
            return self.aws_client.get_value(Name=term)

        if on_missing == "error":
            with pytest.raises(AnsibleLookupError) as exc_info:
                get_value(mock_lookup, "missing-param")
            assert "Failed to find SSM parameter missing-param (ResourceNotFound)" == str(exc_info.value)
        else:
            result = get_value(mock_lookup, "missing-param")
            assert result is None
            if on_missing == "warn":
                mock_lookup.warn.assert_called_once_with(
                    "Skipping, did not find SSM parameter missing-param"
                )

    @pytest.mark.parametrize("on_denied", ["error", "warn", "skip"])
    def test_handle_access_denied(self, on_denied):
        """Test decorator handles AccessDeniedException correctly"""
        mock_lookup = MockLookup()
        mock_lookup.on_denied = on_denied
        mock_lookup.aws_client.get_value.side_effect = _raise_boto_clienterror("AccessDeniedException", "Access denied")

        @LookupErrorHandler.handle_lookup_errors("secret")
        def get_value(self, term):
            return self.aws_client.get_value(Name=term)

        if on_denied == "error":
            with pytest.raises(AnsibleLookupError) as exc_info:
                get_value(mock_lookup, "denied-secret")
            assert "Failed to access secret denied-secret (AccessDenied)" == str(exc_info.value)
        else:
            result = get_value(mock_lookup, "denied-secret")
            assert result is None
            if on_denied == "warn":
                mock_lookup.warn.assert_called_once_with("Skipping, access denied for secret denied-secret")

    @pytest.mark.parametrize("on_deleted", ["error", "warn", "skip"])
    def test_handle_marked_for_deletion(self, on_deleted):
        """Test decorator handles marked for deletion correctly"""
        mock_lookup = MockLookup()
        mock_lookup.on_deleted = on_deleted
        # Using error message match pattern
        error = _raise_boto_clienterror("ResourceMarkedForDeletion", "marked for deletion")
        mock_lookup.aws_client.get_value.side_effect = error

        @LookupErrorHandler.handle_lookup_errors("secret")
        def get_value(self, term):
            return self.aws_client.get_value(Name=term)

        if on_deleted == "error":
            with pytest.raises(AnsibleLookupError) as exc_info:
                get_value(mock_lookup, "deleted-secret")
            assert "Failed to find secret deleted-secret (marked for deletion)" == str(exc_info.value)
        else:
            result = get_value(mock_lookup, "deleted-secret")
            assert result is None
            if on_deleted == "warn":
                mock_lookup.warn.assert_called_once_with(
                    "Skipping, did not find secret (marked for deletion) deleted-secret"
                )

    def test_handle_unexpected_client_error(self):
        """Test decorator re-raises unexpected ClientErrors"""
        mock_lookup = MockLookup()
        mock_lookup.aws_client.get_value.side_effect = _raise_boto_clienterror(
            "UnexpectedError", "Something went wrong"
        )

        @LookupErrorHandler.handle_lookup_errors("resource")
        def get_value(self, term):
            return self.aws_client.get_value(Name=term)

        with pytest.raises(AnsibleLookupError) as exc_info:
            get_value(mock_lookup, "test-resource")
        assert "Failed to retrieve resource:" in str(exc_info.value)
        assert "UnexpectedError" in str(exc_info.value)

    def test_default_value_parameter(self):
        """Test decorator returns default_value when specified"""
        mock_lookup = MockLookup()
        mock_lookup.on_missing = "skip"
        mock_lookup.aws_client.get_value.side_effect = _raise_boto_clienterror("ResourceNotFoundException", "Not found")

        @LookupErrorHandler.handle_lookup_errors("parameter", default_value=[{}])
        def get_value(self, term):
            return self.aws_client.get_value(Name=term)

        result = get_value(mock_lookup, "missing")
        assert result == [{}]

    def test_term_extraction_from_kwargs(self):
        """Test decorator extracts term from kwargs correctly"""
        mock_lookup = MockLookup()
        mock_lookup.on_missing = "error"
        mock_lookup.aws_client.get_value.side_effect = _raise_boto_clienterror("ResourceNotFoundException", "Not found")

        @LookupErrorHandler.handle_lookup_errors("resource")
        def get_value(self, term):
            return self.aws_client.get_value(Name=term)

        with pytest.raises(AnsibleLookupError) as exc_info:
            get_value(mock_lookup, term="my-resource")
        assert "Failed to find resource my-resource (ResourceNotFound)" == str(exc_info.value)

    @pytest.mark.parametrize("on_missing", ["error", "warn", "skip"])
    def test_handle_nested_key_not_found(self, on_missing):
        """Test decorator handles LookupResourceNotFoundError correctly"""
        mock_lookup = MockLookup()
        mock_lookup.on_missing = on_missing

        @LookupErrorHandler.handle_lookup_errors("secret")
        def extract_value(self, term):
            # Simulate nested key traversal that fails
            raise LookupResourceNotFoundError("root.child.missing_key")

        if on_missing == "error":
            with pytest.raises(AnsibleLookupError) as exc_info:
                extract_value(mock_lookup, "secret.root.child.missing_key")
            assert "Successfully retrieved secret but there exists no key root.child.missing_key in the secret" == str(
                exc_info.value
            )
        else:
            result = extract_value(mock_lookup, "secret.root.child.missing_key")
            assert result is None
            if on_missing == "warn":
                mock_lookup.warn.assert_called_once_with(
                    "Skipping, Successfully retrieved secret but there exists no key root.child.missing_key in the secret"
                )

    @pytest.mark.parametrize("on_missing", ["error", "warn", "skip"])
    def test_handle_nested_key_not_found_custom_templates(self, on_missing):
        """Test decorator handles LookupResourceNotFoundError with custom templates"""
        mock_lookup = MockLookup()
        mock_lookup.on_missing = on_missing

        @LookupErrorHandler.handle_lookup_errors("parameter")
        def extract_value(self, term):
            # Simulate nested key traversal with custom error messages
            raise LookupResourceNotFoundError(
                "config.database.port",
                error_template="SSM parameter retrieved but nested key {term} is missing",
                warn_template="Skipping nested key {term} in SSM parameter",
            )

        if on_missing == "error":
            with pytest.raises(AnsibleLookupError) as exc_info:
                extract_value(mock_lookup, "parameter.config.database.port")
            assert "SSM parameter retrieved but nested key config.database.port is missing" == str(exc_info.value)
        else:
            result = extract_value(mock_lookup, "parameter.config.database.port")
            assert result is None
            if on_missing == "warn":
                mock_lookup.warn.assert_called_once_with(
                    "Skipping nested key config.database.port in SSM parameter"
                )

    def test_handle_botocore_error(self):
        """Test decorator handles BotoCoreError (not ClientError)"""
        from botocore.exceptions import BotoCoreError

        mock_lookup = MockLookup()

        # Create a BotoCoreError
        botocore_error = BotoCoreError()
        mock_lookup.aws_client.get_value.side_effect = botocore_error

        @LookupErrorHandler.handle_lookup_errors("secret")
        def get_value(self, term):
            return self.aws_client.get_value(Name=term)

        with pytest.raises(AnsibleLookupError) as exc_info:
            get_value(mock_lookup, "test-secret")
        assert "Failed to retrieve secret:" in str(exc_info.value)

    def test_term_extraction_from_positional_args(self):
        """Test decorator extracts term from positional args when not in kwargs"""
        mock_lookup = MockLookup()
        mock_lookup.on_missing = "error"
        mock_lookup.aws_client.get_value.side_effect = _raise_boto_clienterror("ResourceNotFoundException", "Not found")

        @LookupErrorHandler.handle_lookup_errors("parameter")
        def get_value(self, term):
            return self.aws_client.get_value(Name=term)

        # Call with positional arg (not kwargs)
        with pytest.raises(AnsibleLookupError) as exc_info:
            get_value(mock_lookup, "my-param")
        assert "Failed to find parameter my-param (ResourceNotFound)" == str(exc_info.value)

    def test_default_value_with_warn_action(self):
        """Test decorator returns default_value with warn action"""
        mock_lookup = MockLookup()
        mock_lookup.on_missing = "warn"
        mock_lookup.aws_client.get_value.side_effect = _raise_boto_clienterror("ResourceNotFoundException", "Not found")

        default_dict = {"default": "value"}

        @LookupErrorHandler.handle_lookup_errors("secret", default_value=default_dict)
        def get_value(self, term):
            return self.aws_client.get_value(Name=term)

        result = get_value(mock_lookup, "missing-secret")
        assert result == default_dict
        mock_lookup.warn.assert_called_once()

    def test_default_value_with_access_denied(self):
        """Test decorator returns default_value when access is denied"""
        mock_lookup = MockLookup()
        mock_lookup.on_denied = "skip"
        mock_lookup.aws_client.get_value.side_effect = _raise_boto_clienterror("AccessDeniedException", "Access denied")

        default_list = [{"default": "item"}]

        @LookupErrorHandler.handle_lookup_errors("secret", default_value=default_list)
        def get_value(self, term):
            return self.aws_client.get_value(Name=term)

        result = get_value(mock_lookup, "denied-secret")
        assert result == default_list

    def test_default_value_with_deleted_resource(self):
        """Test decorator returns default_value for deleted resources"""
        mock_lookup = MockLookup()
        mock_lookup.on_deleted = "skip"
        error = _raise_boto_clienterror("InvalidParameterValue", "marked for deletion")
        mock_lookup.aws_client.get_value.side_effect = error

        @LookupErrorHandler.handle_lookup_errors("secret", default_value=[])
        def get_value(self, term):
            return self.aws_client.get_value(Name=term)

        result = get_value(mock_lookup, "deleted-secret")
        assert result == []
