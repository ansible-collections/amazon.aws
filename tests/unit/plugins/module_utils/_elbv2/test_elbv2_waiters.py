# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

try:
    import botocore.waiter as botocore_waiter

    HAS_BOTOCORE = True
except ImportError:
    HAS_BOTOCORE = False

from ansible_collections.amazon.aws.plugins.module_utils._elbv2.waiters import waiter_factory

if not HAS_BOTOCORE:
    pytestmark = pytest.mark.skip("test_waiters.py requires botocore")


class TestELBv2Waiters:
    """Test suite for ELBv2 waiter factory."""

    def test_waiter_factory_has_model(self):
        """Test that waiter factory has a waiter model."""
        assert hasattr(waiter_factory, "_model")
        assert isinstance(waiter_factory._model, botocore_waiter.WaiterModel)

    @pytest.mark.parametrize(
        "waiter_name",
        [
            "target_in_service",
            "target_deregistered",
        ],
    )
    def test_get_waiter_returns_waiter(self, waiter_name):
        """Test that get_waiter returns a waiter for valid waiter names."""
        mock_client = MagicMock()
        mock_waiter = MagicMock()

        with patch(
            "ansible_collections.amazon.aws.plugins.module_utils.waiter.botocore_waiter.create_waiter_with_client"
        ) as mock_create:
            mock_create.return_value = mock_waiter
            waiter = waiter_factory.get_waiter(mock_client, waiter_name)

            assert waiter == mock_waiter
            mock_create.assert_called_once_with(waiter_name, waiter_factory._model, mock_client)

    def test_get_waiter_invalid_name_raises(self):
        """Test that get_waiter raises NotImplementedError for invalid waiter names."""
        mock_client = MagicMock()
        with pytest.raises(NotImplementedError) as exc_info:
            waiter_factory.get_waiter(mock_client, "invalid_waiter_name")
        assert "Unable to find waiter invalid_waiter_name" in str(exc_info.value)
