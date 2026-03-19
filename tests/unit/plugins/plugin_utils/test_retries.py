# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.plugin_utils.retries import AWSConnectionRetry


class TestAWSConnectionRetry:
    """Tests for the AWSConnectionRetry decorator."""

    def test_successful_execution_no_retry(self):
        """Test that successful execution doesn't trigger retries."""

        class MockConnection:
            reconnection_retries = 3
            verbosity_display = MagicMock()
            close = MagicMock()

        conn = MockConnection()

        @AWSConnectionRetry.exponential_backoff()
        def test_method(self, arg1, arg2):
            return (arg1, arg2, "success")

        result = test_method(conn, "foo", "bar")

        assert result == ("foo", "bar", "success")
        conn.close.assert_not_called()
        conn.verbosity_display.assert_not_called()

    def test_retry_on_exception(self):
        """Test that exceptions trigger retries."""

        class MockConnection:
            reconnection_retries = 2
            verbosity_display = MagicMock()
            close = MagicMock()

        conn = MockConnection()
        call_count = 0

        @AWSConnectionRetry.exponential_backoff()
        def test_method(self):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return ("success",)

        with patch("time.sleep"):  # Skip actual sleep delays
            result = test_method(conn)

        assert result == ("success",)
        assert call_count == 2
        assert conn.close.call_count == 1  # Called once before retry
        assert conn.verbosity_display.call_count == 1  # Logged the retry

    def test_max_retries_exceeded(self):
        """Test that exception is raised after max retries exceeded."""

        class MockConnection:
            reconnection_retries = 2
            verbosity_display = MagicMock()
            close = MagicMock()

        conn = MockConnection()

        @AWSConnectionRetry.exponential_backoff()
        def test_method(self):
            raise ValueError("Persistent failure")

        with patch("time.sleep"):
            with pytest.raises(ValueError, match="Persistent failure"):
                test_method(conn)

        # Should have tried 3 times total (initial + 2 retries)
        assert conn.close.call_count == 2
        assert conn.verbosity_display.call_count == 2

    def test_custom_retry_count(self):
        """Test using custom retry count instead of instance attribute."""

        class MockConnection:
            reconnection_retries = 10  # Should be ignored
            verbosity_display = MagicMock()
            close = MagicMock()

        conn = MockConnection()

        @AWSConnectionRetry.exponential_backoff(retries=1)
        def test_method(self):
            raise ValueError("Failure")

        with patch("time.sleep"):
            with pytest.raises(ValueError):
                test_method(conn)

        # Should only retry once (not 10 times)
        assert conn.close.call_count == 1
        assert conn.verbosity_display.call_count == 1

    def test_no_verbosity_display_method(self):
        """Test that missing verbosity_display doesn't cause errors."""

        class MockConnection:
            reconnection_retries = 1
            close = MagicMock()
            # No verbosity_display method

        conn = MockConnection()
        call_count = 0

        @AWSConnectionRetry.exponential_backoff()
        def test_method(self):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return ("success",)

        with patch("time.sleep"):
            result = test_method(conn)

        assert result == ("success",)
        assert call_count == 2

    def test_no_close_method(self):
        """Test that missing close method doesn't cause errors."""

        class MockConnection:
            reconnection_retries = 1
            verbosity_display = MagicMock()
            # No close method

        conn = MockConnection()
        call_count = 0

        @AWSConnectionRetry.exponential_backoff()
        def test_method(self):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return ("success",)

        with patch("time.sleep"):
            result = test_method(conn)

        assert result == ("success",)
        assert call_count == 2

    @patch("time.sleep")
    def test_backoff_delay_progression(self, mock_sleep):
        """Test that backoff delays increase correctly."""

        class MockConnection:
            reconnection_retries = 3
            verbosity_display = MagicMock()
            close = MagicMock()

        conn = MockConnection()

        @AWSConnectionRetry.exponential_backoff(initial_delay=1, backoff_multiplier=2, max_delay=10)
        def test_method(self):
            raise ValueError("Always fails")

        with pytest.raises(ValueError):
            test_method(conn)

        # Check sleep was called with increasing delays: 1, 2, 4
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert len(sleep_calls) == 3
        assert sleep_calls[0] == 1
        assert sleep_calls[1] == 2
        assert sleep_calls[2] == 4

    @patch("time.sleep")
    def test_max_delay_limit(self, mock_sleep):
        """Test that delay doesn't exceed max_delay."""

        class MockConnection:
            reconnection_retries = 5
            verbosity_display = MagicMock()
            close = MagicMock()

        conn = MockConnection()

        @AWSConnectionRetry.exponential_backoff(initial_delay=1, backoff_multiplier=2, max_delay=3)
        def test_method(self):
            raise ValueError("Always fails")

        with pytest.raises(ValueError):
            test_method(conn)

        # Check that no sleep delay exceeds max_delay
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert all(delay <= 3 for delay in sleep_calls)

    def test_verbosity_display_message_format(self):
        """Test that verbosity_display receives properly formatted messages."""

        class MockConnection:
            reconnection_retries = 1
            verbosity_display = MagicMock()
            close = MagicMock()

        conn = MockConnection()

        @AWSConnectionRetry.exponential_backoff()
        def test_method(self, cmd):
            raise ValueError("Test error")

        with patch("time.sleep"):
            with pytest.raises(ValueError):
                test_method(conn, "test command")

        # Verify verbosity_display was called with level 2 and a message
        assert conn.verbosity_display.call_count == 1
        call_args = conn.verbosity_display.call_args[0]
        assert call_args[0] == 2  # Verbosity level
        message = call_args[1]
        assert "AWSConnectionRetry" in message
        assert "attempt 1/2" in message
        assert "ValueError" in message
        assert "Test error" in message
        assert "test command" in message

    def test_preserves_return_value(self):
        """Test that decorator preserves the return value exactly."""

        class MockConnection:
            reconnection_retries = 3
            verbosity_display = MagicMock()
            close = MagicMock()

        conn = MockConnection()

        @AWSConnectionRetry.exponential_backoff()
        def test_method(self):
            return (123, "string", {"key": "value"}, [1, 2, 3])

        result = test_method(conn)
        assert result == (123, "string", {"key": "value"}, [1, 2, 3])

    def test_with_jitter(self):
        """Test that jitter parameter is accepted (actual jitter tested by BackoffIterator)."""

        class MockConnection:
            reconnection_retries = 1
            verbosity_display = MagicMock()
            close = MagicMock()

        conn = MockConnection()

        @AWSConnectionRetry.exponential_backoff(jitter=True)
        def test_method(self):
            raise ValueError("Failure")

        with patch("time.sleep"):
            with pytest.raises(ValueError):
                test_method(conn)

        # Just verify it doesn't crash with jitter=True
        assert conn.close.call_count == 1

    def test_multiple_args_and_kwargs(self):
        """Test that method args and kwargs are preserved."""

        class MockConnection:
            reconnection_retries = 1
            verbosity_display = MagicMock()
            close = MagicMock()

        conn = MockConnection()

        @AWSConnectionRetry.exponential_backoff()
        def test_method(self, arg1, arg2, kwarg1=None, kwarg2=None):
            return (arg1, arg2, kwarg1, kwarg2)

        result = test_method(conn, "a", "b", kwarg1="c", kwarg2="d")
        assert result == ("a", "b", "c", "d")
