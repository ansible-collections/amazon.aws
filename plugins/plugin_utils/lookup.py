# -*- coding: utf-8 -*-

# (c) 2022 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.errors import AnsibleLookupError
from ansible.plugins.lookup import LookupBase

from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.plugin_utils._lookup import common as _lookup_common
from ansible_collections.amazon.aws.plugins.plugin_utils.base import AWSPluginBase

LookupErrorHandler = _lookup_common.LookupErrorHandler
NestedKeyNotFoundError = _lookup_common.NestedKeyNotFoundError


class AWSLookupBase(AWSPluginBase, LookupBase):
    """
    Base class for AWS lookup plugins.

    Subclasses should define:
        _SERVICE: AWS service name (e.g., "secretsmanager", "ssm")
    """

    _SERVICE = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cached_client = None
        self._cached_on_missing = None
        self._cached_on_denied = None
        self._cached_on_deleted = None

    @property
    def aws_client(self):
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
    def on_missing(self):
        """
        Cached error handling behavior for missing resources.

        Returns 'error', 'warn', or 'skip' based on plugin configuration.
        Defaults to 'error' if the option is not defined by the plugin.
        """
        if self._cached_on_missing is None:
            try:
                self._cached_on_missing = self.get_option("on_missing") or "error"
            except (KeyError, AttributeError):
                self._cached_on_missing = "error"
        return self._cached_on_missing

    @property
    def on_denied(self):
        """
        Cached error handling behavior for access denied errors.

        Returns 'error', 'warn', or 'skip' based on plugin configuration.
        Defaults to 'error' if the option is not defined by the plugin.
        """
        if self._cached_on_denied is None:
            try:
                self._cached_on_denied = self.get_option("on_denied") or "error"
            except (KeyError, AttributeError):
                self._cached_on_denied = "error"
        return self._cached_on_denied

    @property
    def on_deleted(self):
        """
        Cached error handling behavior for deleted resources.

        Returns 'error', 'warn', or 'skip' based on plugin configuration.
        Defaults to 'error' if the option is not defined by the plugin.
        """
        if self._cached_on_deleted is None:
            try:
                self._cached_on_deleted = self.get_option("on_deleted") or "error"
            except (KeyError, AttributeError):
                self._cached_on_deleted = "error"
        return self._cached_on_deleted

    def _do_fail(self, message):
        raise AnsibleLookupError(message)

    def run(self, terms, variables, botocore_version=None, boto3_version=None, **kwargs):
        self.require_aws_sdk(botocore_version=botocore_version, boto3_version=boto3_version)
        self.set_options(var_options=variables, direct=kwargs)
