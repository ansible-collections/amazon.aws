# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
Backwards-compatibility module for version comparison utilities.

.. deprecated::
   The re-export in this module is deprecated and will be removed in a future major release.
   New code should import directly from ansible.module_utils.compat.version.

See the developer guidelines for details:
https://ansible-collections.github.io/amazon.aws/branch/main/dev_guidelines.html
"""

from __future__ import annotations

import sys

# Try to import deprecated decorator for static analysis tools
# Falls back to no-op if typing_extensions isn't available (e.g., ansible-test sanity)
try:
    if sys.version_info >= (3, 13):
        from warnings import deprecated
    else:
        from typing_extensions import deprecated
except ImportError:
    # typing_extensions not available - define no-op decorator
    def deprecated(message):  # NOSONAR S1172 - signature must match typing_extensions.deprecated
        """No-op decorator when typing_extensions is unavailable."""
        return lambda obj: obj


from ansible.module_utils.compat.version import LooseVersion as _LooseVersion


LooseVersion = deprecated(
    "Import LooseVersion directly from ansible.module_utils.compat.version instead. "
    "This re-export will be removed in a future major release."
)(_LooseVersion)


__all__ = ("LooseVersion",)
