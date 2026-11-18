# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment:
    # Minimum requirements for the collection.
    # Each section is a plain string so the docs can be read without running this code.
    # .github/scripts/check_sdk_floor_versions.py checks the versions against module_utils/botocore.py.
    DOCUMENTATION = r"""
options: {}
requirements:
  - python >= 3.6
  - boto3 >= 1.38.23
  - botocore >= 1.38.23
"""

    # Because the docs will be statically generated, without executing the code,
    # we need to copy the documentation for both Modules and Plugins
    MODULES = r"""
options: {}
requirements:
  - python >= 3.6
  - boto3 >= 1.38.23
  - botocore >= 1.38.23
"""

    PLUGINS = r"""
options: {}
requirements:
  - python >= 3.6
  - boto3 >= 1.38.23
  - botocore >= 1.38.23
"""
