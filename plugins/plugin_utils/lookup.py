# -*- coding: utf-8 -*-

# (c) 2022 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import NoReturn

    from ansible_collections.amazon.aws.plugins.module_utils.botocore import ClientType

from ansible.errors import AnsibleLookupError
from ansible.plugins.lookup import LookupBase

from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.plugin_utils._lookup import common as _lookup_common
from ansible_collections.amazon.aws.plugins.plugin_utils.base import AWSPluginBase

LookupErrorHandler = _lookup_common.LookupErrorHandler
LookupResourceNotFoundError = _lookup_common.LookupResourceNotFoundError


class AWSLookupBase(AWSPluginBase, LookupBase):
    """
    Base class for AWS lookup plugins.

    Subclasses should define:
        _SERVICE: AWS service name (e.g., "secretsmanager", "ssm")
    """

    _SERVICE: str | None = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Lookup plugins don't have a host context
        self.host = None
        self._cached_client: ClientType | None = None
        self._cached_on_missing: str | None = None
        self._cached_on_denied: str | None = None
        self._cached_on_deleted: str | None = None

    @property
    def aws_client(self) -> ClientType:
        """
        Cached AWS client for the service defined by _SERVICE.

        Creates and caches the client on first access. Subclasses must define
        the _SERVICE class attribute.
        """
        if self._cached_client is None:
            if self._SERVICE is None:
                raise NotImplementedError(f"{self.__class__.__name__} must define _SERVICE class attribute")
            self._cached_client = self.client(self._SERVICE, AWSRetry.jittered_backoff())
        return self._cached_client

    @property
    def on_missing(self) -> str:
        """
        Cached error handling behavior for missing resources.

        Returns 'error', 'warn', or 'skip' based on plugin configuration.
        Defaults to 'error' if the option is not defined by the plugin.
        """
        if self._cached_on_missing is None:
            try:
                self._cached_on_missing = str(self.get_option("on_missing") or "error")
            except (KeyError, AttributeError):
                self._cached_on_missing = "error"
        return self._cached_on_missing

    @property
    def on_denied(self) -> str:
        """
        Cached error handling behavior for access denied errors.

        Returns 'error', 'warn', or 'skip' based on plugin configuration.
        Defaults to 'error' if the option is not defined by the plugin.
        """
        if self._cached_on_denied is None:
            try:
                self._cached_on_denied = str(self.get_option("on_denied") or "error")
            except (KeyError, AttributeError):
                self._cached_on_denied = "error"
        return self._cached_on_denied

    @property
    def on_deleted(self) -> str:
        """
        Cached error handling behavior for deleted resources.

        Returns 'error', 'warn', or 'skip' based on plugin configuration.
        Defaults to 'error' if the option is not defined by the plugin.
        """
        if self._cached_on_deleted is None:
            try:
                self._cached_on_deleted = str(self.get_option("on_deleted") or "error")
            except (KeyError, AttributeError):
                self._cached_on_deleted = "error"
        return self._cached_on_deleted

    def _do_fail(self, message: str) -> NoReturn:
        raise AnsibleLookupError(message)

    def run(
        self,
        terms: list[str],
        variables: dict[str, Any],
        botocore_version: str | None = None,
        boto3_version: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.require_aws_sdk(botocore_version=botocore_version, boto3_version=boto3_version)
        self.set_options(var_options=variables, direct=kwargs)
