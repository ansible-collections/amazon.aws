# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment:
    # Minimum requirements for the collection.
    # Each section is a plain string so the docs can be read without running this code.
    DOCUMENTATION = r"""
options: {}
requirements:
  - python >= 3.6
  - boto3 >= 1.38.23
  - botocore >= 1.38.23
"""

    # Modules and Plugins can (currently) use the same fragment
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
