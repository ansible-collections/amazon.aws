# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Provide version object to compare version numbers."""

# This should be directly imported by modules, rather than importing from here.
# The import is being kept for backwards compatibility.
from ansible.module_utils.compat.version import LooseVersion  # pylint: disable=unused-import
