# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError
from ansible.errors import AnsibleLookupError
from ansible.module_utils._text import to_native
from ansible.plugins.lookup import LookupBase

from ansible.module_utils.basic import missing_required_lib
from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3
from ansible_collections.amazon.aws.plugins.plugin_utils.botocore import BotocorePluginMixin

from .botocore import get_aws_connection_info
from .botocore import boto3_conn


class AWSBaseModule(BotocorePluginMixin):

    name = None

    def fail(self, msg):
        raise AnsibleError(msg)

    def warn(self, msg):
        if hasattr(self, '_display'):
            self._display.warning(msg)

    def debug(self, msg):
        if hasattr(self, '_display'):
            self._display.vvv(msg)

    @property
    def module_description(self):
        if self.name:
            return "{0} module".format(self.name)
        return "module"

    def fail_aws(self, exception, msg=None):
        # to_native is trusted to handle exceptions that str() could
        # convert to text.
        try:
            except_msg = to_native(exception.message)
        except AttributeError:
            except_msg = to_native(exception)

        if msg is not None:
            message = '{0}: {1}'.format(msg, except_msg)
        else:
            message = except_msg

        self.fail(message)


class AWSLookupModule(AWSBaseModule, LookupBase):

    def fail(self, msg):
        raise AnsibleLookupError(msg)

    @property
    def module_description(self):
        if self.name:
            return "{0} lookup module".format(self.name)
        return "lookup module"

    def run(self, terms, variables=None, **kwargs):
        if not HAS_BOTO3:
            self.fail("The {0} requires boto3 and botocore.".format(self.module_description))

        self.set_options(var_options=variables, direct=kwargs)
