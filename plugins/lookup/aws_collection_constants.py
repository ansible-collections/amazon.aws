# -*- coding: utf-8 -*-

# (c) 2023 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
name: aws_collection_constants
author:
  - Mark Chappell (@tremble)
short_description: expose various collection related constants
version_added: 6.0.0
description:
  - Exposes various collection related constants for use in integration tests.
options:
  _terms:
    description: Name of the constant.
    choices:
      - MINIMUM_BOTOCORE_VERSION
      - MINIMUM_BOTO3_VERSION
      - HAS_BOTO3
      - AMAZON_AWS_COLLECTION_VERSION
      - AMAZON_AWS_COLLECTION_NAME
      - COMMUNITY_AWS_COLLECTION_VERSION
      - COMMUNITY_AWS_COLLECTION_NAME
    required: True
"""

EXAMPLES = r"""
"""

RETURN = r"""
_raw:
  description: value
  type: str
"""

from ansible.errors import AnsibleLookupError
from ansible.plugins.lookup import LookupBase

import ansible_collections.amazon.aws.plugins.module_utils.botocore as botocore_utils
import ansible_collections.amazon.aws.plugins.module_utils.common as common_utils

try:
    import ansible_collections.community.aws.plugins.module_utils.common as community_utils

    HAS_COMMUNITY = True
except ImportError:
    HAS_COMMUNITY = False


class LookupModule(LookupBase):
    def lookup_constant(self, name):  # pylint: disable=too-many-return-statements
        if name == "MINIMUM_BOTOCORE_VERSION":
            return botocore_utils.MINIMUM_BOTOCORE_VERSION
        if name == "MINIMUM_BOTO3_VERSION":
            return botocore_utils.MINIMUM_BOTO3_VERSION
        if name == "HAS_BOTO3":
            return botocore_utils.HAS_BOTO3

        if name == "AMAZON_AWS_COLLECTION_VERSION":
            return common_utils.AMAZON_AWS_COLLECTION_VERSION
        if name == "AMAZON_AWS_COLLECTION_NAME":
            return common_utils.AMAZON_AWS_COLLECTION_NAME

        if name == "COMMUNITY_AWS_COLLECTION_VERSION":
            if not HAS_COMMUNITY:
                raise AnsibleLookupError("Unable to load ansible_collections.community.aws.plugins.module_utils.common")
            return community_utils.COMMUNITY_AWS_COLLECTION_VERSION
        if name == "COMMUNITY_AWS_COLLECTION_NAME":
            if not HAS_COMMUNITY:
                raise AnsibleLookupError("Unable to load ansible_collections.community.aws.plugins.module_utils.common")
            return community_utils.COMMUNITY_AWS_COLLECTION_NAME

    def run(self, terms, variables, **kwargs):
        self.set_options(var_options=variables, direct=kwargs)
        if not terms:
            raise AnsibleLookupError("Constant name not provided")
        if len(terms) > 1:
            raise AnsibleLookupError("Multiple constant names provided")
        name = terms[0].upper()

        return [self.lookup_constant(name)]
