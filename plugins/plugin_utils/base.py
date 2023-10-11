# -*- coding: utf-8 -*-

# (c) 2022 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.errors import AnsibleError
from ansible.module_utils.basic import to_native
from ansible.utils.display import Display

from ansible_collections.amazon.aws.plugins.module_utils.botocore import check_sdk_version_supported
from ansible_collections.amazon.aws.plugins.module_utils.retries import RetryingBotoClientWrapper
from ansible_collections.amazon.aws.plugins.plugin_utils.botocore import boto3_conn
from ansible_collections.amazon.aws.plugins.plugin_utils.botocore import get_aws_connection_info
from ansible_collections.amazon.aws.plugins.plugin_utils.botocore import get_aws_region

display = Display()


class AWSPluginBase:
    def warn(self, message):
        display.warning(message)

    def debug(self, message):
        display.debug(message)

    # Should be overridden with the plugin-type specific exception
    def _do_fail(self, message):
        raise AnsibleError(message)

    # We don't know what the correct exception is to raise, so the actual "raise" is handled by
    # _do_fail()
    def fail_aws(self, message, exception=None):
        if not exception:
            self._do_fail(to_native(message))
        self._do_fail(f"{message}: {to_native(exception)}")

    def client(self, service, retry_decorator=None, **extra_params):
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
    def region(self):
        return get_aws_region(self)

    def require_aws_sdk(self, botocore_version=None, boto3_version=None):
        return check_sdk_version_supported(
            botocore_version=botocore_version, boto3_version=boto3_version, warn=self.warn
        )
