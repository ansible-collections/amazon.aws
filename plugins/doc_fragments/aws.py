# -*- coding: utf-8 -*-

# (c) 2022 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from .common import ModuleDocFragment as CommonFragment

#
# The amazon.aws.aws docs fragment has been deprecated,
# please migrate to amazon.aws.common.modules.
#


class ModuleDocFragment:
    def __init__(self):
        self.DOCUMENTATION = CommonFragment.MODULES
