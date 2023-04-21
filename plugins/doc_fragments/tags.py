# -*- coding: utf-8 -*-

# Copyright: (c) 2022,  Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment:
    # Standard Tagging related parameters
    DOCUMENTATION = r"""
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
"""

    # Modules and Plugins can (currently) use the same fragment
    def __init__(self):
        self.MODULES = self.DOCUMENTATION
        self.PLUGINS = self.DOCUMENTATION
