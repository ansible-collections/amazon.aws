# -*- coding: utf-8 -*-

# (c) 2022 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from typing import NoReturn
from typing import Optional

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import to_native
from ansible.utils.display import Display

from ansible_collections.amazon.aws.plugins.module_utils.botocore import check_sdk_version_supported
from ansible_collections.amazon.aws.plugins.module_utils.retries import RetryingBotoClientWrapper
from ansible_collections.amazon.aws.plugins.plugin_utils.botocore import boto3_conn
from ansible_collections.amazon.aws.plugins.plugin_utils.botocore import get_aws_connection_info
from ansible_collections.amazon.aws.plugins.plugin_utils.botocore import get_aws_region

display = Display()


class AWSPluginBase:
    def warn(self, message: str):
        display.warning(message)

    def debug(self, message: str):
        display.debug(message)

    def v_log(self, level: int, message: str, host: Optional[str] = None) -> None:
        """
        Display a message at the specified verbosity level.

        :param level: The verbosity level (1-6)
        :param message: The message to display
        :param host: Optional host identifier for the message. If not provided, attempts to use self.host if available.
        """
        # Use the provided host, or fall back to self.host if it exists
        if host is None:
            host = getattr(self, "host", None)

        if host:
            host_args = {"host": host}
        else:
            host_args = {}

        verbosity_level = {
            1: display.v,
            2: display.vv,
            3: display.vvv,
            4: display.vvvv,
            5: display.vvvvv,
            6: display.vvvvvv,
        }

        if level not in verbosity_level.keys():
            raise AnsibleError(f"Invalid verbosity level: {level}")
        verbosity_level[level](to_text(message), **host_args)

    # Should be overridden with the plugin-type specific exception
    def _do_fail(self, message: str) -> NoReturn:
        raise AnsibleError(message)

    # We don't know what the correct exception is to raise, so the actual "raise" is handled by
    # _do_fail()
    def fail_aws(self, message: str, exception: Optional[Exception] = None) -> NoReturn:
        if not exception:
            self._do_fail(to_native(message))
        self._do_fail(f"{message}: {to_native(exception)}")

    def client(self, service: str, retry_decorator=None, **extra_params):
        region, endpoint_url, aws_connect_kwargs = get_aws_connection_info(self)
        kw_args = dict(region=region, endpoint=endpoint_url, **aws_connect_kwargs)
        kw_args.update(extra_params)
        conn = boto3_conn(self, conn_type="client", resource=service, **kw_args)
        return conn if retry_decorator is None else RetryingBotoClientWrapper(conn, retry_decorator)

    def resource(self, service, **extra_params):
        region, endpoint_url, aws_connect_kwargs = get_aws_connection_info(self)
        kw_args = dict(region=region, endpoint=endpoint_url, **aws_connect_kwargs)
        kw_args.update(extra_params)
        return boto3_conn(self, conn_type="resource", resource=service, **kw_args)

    @property
    def region(self) -> Optional[str]:
        return get_aws_region(self)

    def require_aws_sdk(self, botocore_version: Optional[str] = None, boto3_version: Optional[str] = None) -> bool:
        return check_sdk_version_supported(
            botocore_version=botocore_version, boto3_version=boto3_version, warn=self.warn
        )
