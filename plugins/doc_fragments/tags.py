# -*- coding: utf-8 -*-

# Copyright: (c) 2022,  Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # Standard Tagging related parameters
    DOCUMENTATION = r'''
options:
  tags:
    description:
      - A dictionary representing the tags to be applied to the resource.
      - If the I(tags) parameter is not set then tags will not be modified.
    type: dict
    required: false
    aliases: ['resource_tags']
  purge_tags:
    description:
      - If I(purge_tags=true) and I(tags) is set, existing tags will be purged
        from the resource to match exactly what is defined by I(tags) parameter.
      - If the I(tags) parameter is not set then tags will not be modified, even
        if I(purge_tags=True).
      - Tag keys beginning with C(aws:) are reserved by Amazon and can not be
        modified.  As such they will be ignored for the purposes of the
        I(purge_tags) parameter.  See the Amazon documentation for more information
        U(https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html#tag-conventions).
    type: bool
    default: true
    required: false
'''

    # Some modules had a default of purge_tags=False, this was generally
    # deprecated in release 4.0.0
    DEPRECATED_PURGE = r'''
options:
  tags:
    description:
      - A dictionary representing the tags to be applied to the resource.
      - If the I(tags) parameter is not set then tags will not be modified.
    type: dict
    required: false
    aliases: ['resource_tags']
  purge_tags:
    description:
      - If I(purge_tags=true) and I(tags) is set, existing tags will be purged
        from the resource to match exactly what is defined by I(tags) parameter.
      - If the I(tags) parameter is not set then tags will not be modified, even
        if I(purge_tags=True).
      - Tag keys beginning with C(aws:) are reserved by Amazon and can not be
        modified.  As such they will be ignored for the purposes of the
        I(purge_tags) parameter.  See the Amazon documentation for more information
        U(https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html#tag-conventions).
      - The current default value of C(False) has been deprecated.  The default
        value will change to C(True) in release 5.0.0.
    type: bool
    required: false
'''
