# -*- coding: utf-8 -*-

# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from .region import ModuleDocFragment as RegionFragment

#
# The amazon.aws.aws_region docs fragment has been deprecated,
# please migrate to amazon.aws.region.plugins.
#


class ModuleDocFragment(object):
    def __init__(self):
        self.DOCUMENTATION = RegionFragment.PLUGINS
