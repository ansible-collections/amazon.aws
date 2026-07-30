# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import sys
import warnings

import pytest


class TestVersionModule:
    """Test suite for version.py module utilities."""

    def test_looseversion_reexport(self):
        """Test that LooseVersion is properly re-exported and functional."""
        from ansible_collections.amazon.aws.plugins.module_utils.version import LooseVersion

        # Suppress deprecation warning for this test
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            # Verify it works as a version comparison class
            v = LooseVersion("1.2.3")
            assert str(v) == "1.2.3"

            # Verify it's the actual class, not a function wrapper
            assert v.__class__.__name__ == "LooseVersion"

    def test_looseversion_comparison(self):
        """Test that LooseVersion comparison operations work correctly."""
        from ansible_collections.amazon.aws.plugins.module_utils.version import LooseVersion

        # Suppress deprecation warning for this test
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            v1 = LooseVersion("1.2.3")
            v2 = LooseVersion("1.2.4")
            v3 = LooseVersion("1.2.3")

            assert v1 < v2
            assert v2 > v1
            assert v1 == v3
            assert v1 <= v3
            assert v1 >= v3

    def test_looseversion_deprecation_warning(self):
        """Test that using LooseVersion emits a deprecation warning."""
        import importlib.util

        # Check if deprecated decorator is available
        if sys.version_info >= (3, 13):
            has_deprecated = True
        else:
            has_deprecated = importlib.util.find_spec("typing_extensions") is not None

        if not has_deprecated:
            pytest.skip("DeprecationWarning requires typing_extensions or Python 3.13+")

        from ansible_collections.amazon.aws.plugins.module_utils.version import LooseVersion

        # Test that instantiation emits deprecation warning
        # pytest.deprecated_call() suppresses the warning from test output
        with pytest.deprecated_call():
            _version = LooseVersion("1.2.3")

    def test_looseversion_all_export(self):
        """Test that LooseVersion is in __all__."""
        from ansible_collections.amazon.aws.plugins.module_utils import version

        assert hasattr(version, "__all__")
        assert "LooseVersion" in version.__all__

    def test_looseversion_fallback_decorator(self):
        """Test the fallback no-op decorator when typing_extensions is unavailable."""
        import importlib
        import unittest.mock

        # Mock sys.modules to simulate ImportError for typing_extensions
        with unittest.mock.patch.dict("sys.modules", {"typing_extensions": None}):
            # Force reload to trigger ImportError path
            from ansible_collections.amazon.aws.plugins.module_utils import version

            importlib.reload(version)

            # The module should still load and provide LooseVersion
            assert hasattr(version, "LooseVersion")

            # Suppress any potential deprecation warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                v = version.LooseVersion("1.2.3")
                assert str(v) == "1.2.3"
