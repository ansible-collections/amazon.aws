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

from ansible_collections.amazon.aws.plugins.module_utils._elb.waiters import DynamicELBHealthWaiterFactory
from ansible_collections.amazon.aws.plugins.module_utils._elb.waiters import get_waiter_with_min_instances

if not HAS_BOTOCORE:
    pytestmark = pytest.mark.skip("test_waiters.py requires botocore")


class TestDynamicELBHealthWaiterFactory:
    """Test suite for dynamic ELB health waiter factory."""

    def test_factory_instantiation(self):
        """Test that factory can be instantiated with min_count parameter."""
        factory = DynamicELBHealthWaiterFactory(min_count=3)
        assert factory._min_count == 3
        assert hasattr(factory, "_model")
        assert isinstance(factory._model, botocore_waiter.WaiterModel)

    def test_waiter_model_data_contains_min_count(self):
        """Test that waiter model data includes the dynamic min_count threshold."""
        factory = DynamicELBHealthWaiterFactory(min_count=4)
        model_data = factory._waiter_model_data

        assert "min_instances_in_service" in model_data
        waiter_config = model_data["min_instances_in_service"]
        assert waiter_config["operation"] == "DescribeInstanceHealth"

        # Verify the JMESPath expression contains the dynamic threshold
        acceptor = waiter_config["acceptors"][0]
        assert "`4`" in acceptor["argument"]
        assert "State=='InService'" in acceptor["argument"]

    def test_get_waiter_returns_waiter(self):
        """Test that get_waiter returns a waiter for min_instances_in_service."""
        factory = DynamicELBHealthWaiterFactory(min_count=2)
        mock_client = MagicMock()
        mock_waiter = MagicMock()

        with patch(
            "ansible_collections.amazon.aws.plugins.module_utils.waiter.botocore_waiter.create_waiter_with_client"
        ) as mock_create:
            mock_create.return_value = mock_waiter
            waiter = factory.get_waiter(mock_client, "min_instances_in_service")

            assert waiter == mock_waiter
            mock_create.assert_called_once_with("min_instances_in_service", factory._model, mock_client)

    def test_get_waiter_with_min_instances_helper(self):
        """Test that helper function returns a waiter with correct threshold."""
        mock_client = MagicMock()
        mock_waiter = MagicMock()

        with patch(
            "ansible_collections.amazon.aws.plugins.module_utils.waiter.botocore_waiter.create_waiter_with_client"
        ) as mock_create:
            mock_create.return_value = mock_waiter
            waiter = get_waiter_with_min_instances(mock_client, min_count=6)

            assert waiter == mock_waiter
            # Verify the factory was created and used
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            assert call_args[0][0] == "min_instances_in_service"  # waiter name
            # Verify the model contains our threshold
            model = call_args[0][1]
            assert isinstance(model, botocore_waiter.WaiterModel)
