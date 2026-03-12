# -*- coding: utf-8 -*-
# Copyright: Ansible Project
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.waiter import BaseWaiterFactory


class TestBaseWaiterFactoryWithoutBotocore:
    """Test suite for BaseWaiterFactory when botocore is not available."""

    def test_init_without_botocore(self):
        """Test that __init__ handles missing botocore gracefully."""
        with patch("ansible_collections.amazon.aws.plugins.module_utils.waiter.botocore_waiter", None):
            factory = BaseWaiterFactory()
            assert not hasattr(factory, "_model")

    def test_init_without_botocore_does_not_raise(self):
        """Test that __init__ does not raise ImportError even when botocore is missing."""
        import_error = ImportError("No module named 'botocore.waiter'")

        with patch("ansible_collections.amazon.aws.plugins.module_utils.waiter.botocore_waiter", None):
            with patch("ansible_collections.amazon.aws.plugins.module_utils.waiter.import_error", import_error):
                factory = BaseWaiterFactory()
                assert not hasattr(factory, "_model")

    def test_get_waiter_raises_import_error_when_botocore_missing(self):
        """Test that get_waiter raises import error when botocore is not available."""
        import_error = ImportError("No module named 'botocore'")

        with patch("ansible_collections.amazon.aws.plugins.module_utils.waiter.botocore_waiter", None):
            with patch("ansible_collections.amazon.aws.plugins.module_utils.waiter.import_error", import_error):
                factory = BaseWaiterFactory()
                mock_client = MagicMock()

                with pytest.raises(ImportError) as exc_info:
                    factory.get_waiter(mock_client, "test_waiter")

                assert exc_info.value == import_error
                assert "botocore" in str(exc_info.value)

    def test_get_waiter_preserves_original_import_error(self):
        """Test that get_waiter re-raises the exact original ImportError."""
        original_import_error = ImportError("Cannot import botocore.waiter from /some/path")

        with patch("ansible_collections.amazon.aws.plugins.module_utils.waiter.botocore_waiter", None):
            with patch(
                "ansible_collections.amazon.aws.plugins.module_utils.waiter.import_error", original_import_error
            ):
                factory = BaseWaiterFactory()
                mock_client = MagicMock()

                with pytest.raises(ImportError) as exc_info:
                    factory.get_waiter(mock_client, "some_waiter")

                assert exc_info.value is original_import_error
