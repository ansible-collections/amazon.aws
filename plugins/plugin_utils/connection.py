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
