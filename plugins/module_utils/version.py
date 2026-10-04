# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Provide version object to compare version numbers."""

# Deprecated backwards-compatibility re-export; import LooseVersion from
# ansible.module_utils.compat.version directly in new code.
# pylint: disable-next=unused-import,useless-import-alias
from ansible.module_utils.compat.version import LooseVersion as LooseVersion
