# -*- coding: utf-8 -*-

# (c) 2023 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.errors import AnsibleConnectionFailure
from ansible.plugins.connection import ConnectionBase

from ansible_collections.amazon.aws.plugins.plugin_utils.base import AWSPluginBase


class AWSConnectionBase(AWSPluginBase, ConnectionBase):
    def _do_fail(self, message):
        raise AnsibleConnectionFailure(message)

    def __init__(self, *args, boto3_version=None, botocore_version=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.require_aws_sdk(botocore_version=botocore_version, boto3_version=boto3_version)
        # Set host from play context for logging purposes
        # In tests, _play_context may not be set if ConnectionBase.__init__ is mocked
        if hasattr(self, "_play_context") and self._play_context:
            self.host = self._play_context.remote_addr

    def verbosity_display(self, level: int, message: str) -> None:
        """
        Convenience wrapper for v_log that automatically includes the connection host.

        :param level: The verbosity level (1-5)
        :param message: The message to display
        """
        self.v_log(level, message)
