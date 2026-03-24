# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import functools
import typing

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Callable

try:
    import botocore
except ImportError:
    pass  # Handled by the calling module

from ansible.errors import AnsibleLookupError

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_message


class NestedKeyNotFoundError(KeyError):
    """
    KeyError that includes the full nested path that failed lookup.

    Used when traversing nested dictionaries/JSON structures to preserve
    the key path for error messages. Optionally carries custom error and
    warning message templates.

    Parameters:
        path: The full dotted path that failed (e.g., "root.child.missing_key")
        error_template: Template for error messages (default: standard nested key message)
        warn_template: Template for warning messages (default: standard nested key message)

    Templates should include a {term} placeholder for the path.
    """

    def __init__(
        self,
        path: str,
        error_template: str | None = None,
        warn_template: str | None = None,
    ) -> None:
        self.path = path
        self.error_template = (
            error_template or "Successfully retrieved secret but there exists no key {term} in the secret"
        )
        self.warn_template = (
            warn_template or "Skipping, Successfully retrieved secret but there exists no key {term} in the secret"
        )
        super().__init__(path)


class LookupErrorHandler:
    """
    Error handler for AWS lookup plugins with support for on_missing, on_denied, and on_deleted parameters.

    Provides decorators for handling common AWS lookup error patterns where the error handling
    behavior (error/warn/skip) is read from cached properties on the lookup instance.
    """

    @staticmethod
    def handle_lookup_errors(resource_type: str, default_value: Any = None) -> Callable:
        """
        Decorator for handling AWS lookup errors based on runtime error handling parameters.

        Handles common AWS error codes and defers to on_missing, on_denied, and on_deleted
        parameters to determine whether to raise an exception, log a warning, or silently skip.

        The decorator extracts the 'term' parameter for use in error messages. The term should
        be the first positional argument after 'self', or passed as a keyword argument 'term'.

        Error Handling Behavior:
            - Reads on_missing, on_denied, on_deleted from cached properties on the lookup instance
            - Catches boto3 ClientError/BotoCoreError and handles based on error code
            - Catches NestedKeyNotFoundError for nested dictionary traversal failures
            - ResourceNotFoundException/ParameterNotFound -> delegates to on_missing
            - AccessDeniedException -> delegates to on_denied
            - Error message containing "marked for deletion" -> delegates to on_deleted
            - All other ClientError/BotoCoreError -> raises AnsibleLookupError

        Parameters:
            resource_type: Description of the resource type (e.g., "secret", "SSM parameter")
            default_value: Value to return when warn/skip is triggered (default: None)

        Decorated Function Convention:
            The first positional argument after 'self' should be 'term' (the resource identifier).
            This is used in error messages. Example signatures:
                def get_secret_value(self, term, **kwargs)
                def get_parameter(self, term, version_id=None)

        Usage:
            @LookupErrorHandler.handle_lookup_errors("secret")
            def get_secret_value(self, term, version_stage=None, version_id=None):
                return self.aws_client.get_secret_value(SecretId=term)

            @LookupErrorHandler.handle_lookup_errors("SSM parameter path", default_value=[{}])
            def get_path_parameters(self, term):
                return self.aws_client.get_parameters_by_path(Path=term)
        """

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
                # Read error handling parameters from cached properties on the lookup instance
                on_missing = self.on_missing
                on_denied = self.on_denied
                on_deleted = self.on_deleted

                # term is typically the first positional argument after self
                term = kwargs.get("term") or (args[0] if len(args) > 0 else None)

                try:
                    return func(self, *args, **kwargs)
                except is_boto3_error_message("marked for deletion"):
                    return LookupErrorHandler._handle_response(
                        self,
                        on_deleted,
                        term,
                        resource_type,
                        f"Failed to find {resource_type} {{term}} (marked for deletion)",
                        f"Skipping, did not find {resource_type} (marked for deletion) {{term}}",
                        default_value,
                    )
                except is_boto3_error_code(
                    ["ResourceNotFoundException", "ParameterNotFound"]
                ):  # pylint: disable=duplicate-except
                    return LookupErrorHandler._handle_response(
                        self,
                        on_missing,
                        term,
                        resource_type,
                        f"Failed to find {resource_type} {{term}} (ResourceNotFound)",
                        f"Skipping, did not find {resource_type} {{term}}",
                        default_value,
                    )
                except NestedKeyNotFoundError as e:  # pylint: disable=duplicate-except
                    return LookupErrorHandler._handle_response(
                        self,
                        on_missing,
                        e.path,
                        "key",
                        e.error_template,
                        e.warn_template,
                        default_value,
                    )
                except is_boto3_error_code("AccessDeniedException"):  # pylint: disable=duplicate-except
                    return LookupErrorHandler._handle_response(
                        self,
                        on_denied,
                        term,
                        resource_type,
                        f"Failed to access {resource_type} {{term}} (AccessDenied)",
                        f"Skipping, access denied for {resource_type} {{term}}",
                        default_value,
                    )
                except (
                    botocore.exceptions.ClientError,
                    botocore.exceptions.BotoCoreError,
                ) as e:  # pylint: disable=duplicate-except
                    raise AnsibleLookupError(f"Failed to retrieve {resource_type}: {e}") from e

            return wrapper

        return decorator

    @staticmethod
    def _handle_response(
        lookup_instance: Any,
        action: str,
        term: str,
        resource_type: str,
        error_msg: str,
        warn_msg: str,
        default_value: Any = None,
    ) -> Any:
        """
        Handle the response based on the action parameter (error/warn/skip).

        Parameters:
            lookup_instance: The lookup plugin instance (for accessing _display)
            action: The action to take ("error", "warn", or "skip")
            term: The resource identifier
            resource_type: Description of the resource type
            error_msg: Message template for error (should contain {term} placeholder)
            warn_msg: Message template for warning (should contain {term} placeholder)
            default_value: Value to return for warn/skip (default: None)

        Returns:
            default_value for warn/skip, raises exception for error
        """
        if action == "error":
            raise AnsibleLookupError(error_msg.format(term=term))
        elif action == "warn":
            lookup_instance._display.warning(warn_msg.format(term=term))
        # For "skip" or "warn", return the default value
        return default_value
