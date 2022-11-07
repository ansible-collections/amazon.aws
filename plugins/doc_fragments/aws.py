# -*- coding: utf-8 -*-
# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from .common import ModuleDocFragment as CommonFragment

#
# The amazon.aws.aws docs fragment has been deprecated,
# please migrate to amazon.aws.common.modules.
#


class ModuleDocFragment(object):
    def __init__(self):
        self.DOCUMENTATION = CommonFragment.MODULES
