# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.amazon.aws.plugins.module_utils import botocore as botocore_utils


class ModuleDocFragment:
    # Modules and Plugins can (currently) use the same fragment
    def __init__(self):
        # Minimum requirements for the collection
        requirements = f"""
options: {{}}
requirements:
  - python >= 3.6
  - boto3 >= {botocore_utils.MINIMUM_BOTO3_VERSION}
  - botocore >= {botocore_utils.MINIMUM_BOTOCORE_VERSION}
"""

        self.DOCUMENTATION = requirements
        self.MODULES = requirements
        self.PLUGINS = requirements
