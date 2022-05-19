# -*- coding: utf-8 -*-

# Copyright: (c) 2022,  Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # Minimum requirements for the collection
    DOCUMENTATION = r'''
options: {}
requirements:
  - python >= 3.6
  - boto3 >= 1.16.0
  - botocore >= 1.19.0
'''
