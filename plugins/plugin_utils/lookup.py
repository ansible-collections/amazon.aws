# -*- coding: utf-8 -*-

# (c) 2022 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.errors import AnsibleLookupError
from ansible.plugins.lookup import LookupBase

from ansible_collections.amazon.aws.plugins.plugin_utils.base import AWSPluginBase


class AWSLookupBase(AWSPluginBase, LookupBase):
    def _do_fail(self, message):
        raise AnsibleLookupError(message)

    def run(self, terms, variables, botocore_version=None, boto3_version=None, **kwargs):
        self.require_aws_sdk(botocore_version=botocore_version, boto3_version=boto3_version)
        self.set_options(var_options=variables, direct=kwargs)
