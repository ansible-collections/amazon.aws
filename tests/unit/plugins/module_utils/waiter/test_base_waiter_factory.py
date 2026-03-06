# -*- coding: utf-8 -*-
# Copyright: Ansible Project
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

try:
    import botocore.waiter as botocore_waiter

    HAS_BOTOCORE = True
except ImportError:
    HAS_BOTOCORE = False

from ansible_collections.amazon.aws.plugins.module_utils.waiter import BaseWaiterFactory

if not HAS_BOTOCORE:
    pytestmark = pytest.mark.skip("test_base_waiter_factory.py requires botocore")


class ConcreteWaiterFactory(BaseWaiterFactory):
    """Concrete implementation of BaseWaiterFactory for testing."""

    @property
    def _waiter_model_data(self):
        return {
            "test_waiter": {
                "operation": "DescribeInstances",
                "delay": 5,
                "maxAttempts": 40,
                "acceptors": [
                    {"state": "success", "matcher": "path", "expected": True, "argument": "length(Instances) > `0`"}
                ],
            }
        }


class TestBaseWaiterFactoryInit:
    """Test suite for BaseWaiterFactory.__init__()."""

    def test_init_creates_waiter_model(self):
        """Test that __init__ creates a WaiterModel when botocore is available."""
        factory = ConcreteWaiterFactory()
        assert hasattr(factory, "_model")
        assert isinstance(factory._model, botocore_waiter.WaiterModel)

    def test_init_without_botocore(self):
        """Test that __init__ handles missing botocore gracefully."""
        with patch("ansible_collections.amazon.aws.plugins.module_utils.waiter.botocore_waiter", None):
            factory = BaseWaiterFactory()
            assert not hasattr(factory, "_model")


class TestBaseWaiterFactoryWaiterModelData:
    """Test suite for BaseWaiterFactory._waiter_model_data property."""

    def test_default_waiter_model_data(self):
        """Test that default _waiter_model_data returns empty dict."""
        factory = BaseWaiterFactory()
        assert factory._waiter_model_data == {}


class TestBaseWaiterFactoryInjectRatelimitRetries:
    """Test suite for BaseWaiterFactory._inject_ratelimit_retries()."""

    def test_inject_ratelimit_retries(self):
        """Test that _inject_ratelimit_retries adds error retry acceptors."""
        factory = BaseWaiterFactory()

        original_data = {
            "test_waiter": {
                "operation": "DescribeInstances",
                "delay": 5,
                "maxAttempts": 40,
                "acceptors": [
                    {"state": "success", "matcher": "path", "expected": True, "argument": "length(Instances) > `0`"}
                ],
            }
        }

        injected_data = factory._inject_ratelimit_retries(original_data)

        expected_errors = [
            "RequestLimitExceeded",
            "Unavailable",
            "ServiceUnavailable",
            "InternalFailure",
            "InternalError",
            "TooManyRequestsException",
            "Throttling",
        ]

        acceptors = injected_data["test_waiter"]["acceptors"]
        for error in expected_errors:
            assert any(
                acc.get("state") == "retry" and acc.get("matcher") == "error" and acc.get("expected") == error
                for acc in acceptors
            )

    def test_inject_ratelimit_retries_preserves_original(self):
        """Test that _inject_ratelimit_retries doesn't modify original data."""
        factory = BaseWaiterFactory()

        original_data = {
            "test_waiter": {
                "operation": "DescribeInstances",
                "delay": 5,
                "maxAttempts": 40,
                "acceptors": [
                    {"state": "success", "matcher": "path", "expected": True, "argument": "length(Instances) > `0`"}
                ],
            }
        }

        factory._inject_ratelimit_retries(original_data)

        assert original_data["test_waiter"]["acceptors"] == [
            {"state": "success", "matcher": "path", "expected": True, "argument": "length(Instances) > `0`"}
        ]


class TestBaseWaiterFactoryGetWaiter:
    """Test suite for BaseWaiterFactory.get_waiter()."""

    def test_get_waiter_returns_waiter(self):
        """Test that get_waiter returns a waiter when name exists."""
        factory = ConcreteWaiterFactory()
        mock_client = MagicMock()
        mock_waiter = MagicMock()

        with patch(
            "ansible_collections.amazon.aws.plugins.module_utils.waiter.botocore_waiter.create_waiter_with_client"
        ) as mock_create:
            mock_create.return_value = mock_waiter
            waiter = factory.get_waiter(mock_client, "test_waiter")

            assert waiter == mock_waiter
            mock_create.assert_called_once_with("test_waiter", factory._model, mock_client)

    def test_get_waiter_raises_not_implemented(self):
        """Test that get_waiter raises NotImplementedError when waiter name doesn't exist."""
        factory = ConcreteWaiterFactory()
        mock_client = MagicMock()

        with pytest.raises(NotImplementedError) as exc_info:
            factory.get_waiter(mock_client, "nonexistent_waiter")

        assert "Unable to find waiter nonexistent_waiter" in str(exc_info.value)
        assert "test_waiter" in str(exc_info.value)

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
