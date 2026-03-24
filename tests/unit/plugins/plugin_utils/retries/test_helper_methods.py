# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock

from ansible_collections.amazon.aws.plugins.plugin_utils.retries import AWSConnectionRetry


class TestGetMaxRetries:
    """Tests for the _get_max_retries helper method."""

    def test_returns_parameter_when_provided(self):
        """Test that the retries parameter takes precedence."""

        class MockInstance:
            reconnection_retries = 10

        instance = MockInstance()
        result = AWSConnectionRetry._get_max_retries(instance, 5)
        assert result == 5

    def test_returns_instance_attribute_when_parameter_none(self):
        """Test that instance attribute is used when parameter is None."""

        class MockInstance:
            reconnection_retries = 7

        instance = MockInstance()
        result = AWSConnectionRetry._get_max_retries(instance, None)
        assert result == 7

    def test_defaults_to_zero_when_attribute_missing(self):
        """Test that defaults to 0 when reconnection_retries is missing."""

        class MockInstance:
            pass

        instance = MockInstance()
        result = AWSConnectionRetry._get_max_retries(instance, None)
        assert result == 0

    def test_converts_attribute_to_int(self):
        """Test that the attribute value is converted to int."""

        class MockInstance:
            reconnection_retries = "3"

        instance = MockInstance()
        result = AWSConnectionRetry._get_max_retries(instance, None)
        assert result == 3
        assert isinstance(result, int)


class TestGetCmdSummary:
    """Tests for the _get_cmd_summary helper method."""

    def test_returns_first_arg_with_ellipsis_when_present(self):
        """Test that command summary is generated from first arg."""
        args = ("some command here", "arg2", "arg3")
        result = AWSConnectionRetry._get_cmd_summary(args)
        assert result == "some command here..."

    def test_returns_default_when_args_empty(self):
        """Test that default 'command' is returned for empty args."""
        args = ()
        result = AWSConnectionRetry._get_cmd_summary(args)
        assert result == "command"

    def test_handles_various_arg_types(self):
        """Test that first arg can be various types."""
        # String
        assert AWSConnectionRetry._get_cmd_summary(("test",)) == "test..."

        # Bytes
        assert AWSConnectionRetry._get_cmd_summary((b"bytes",)) == "b'bytes'..."

        # Number
        assert AWSConnectionRetry._get_cmd_summary((123,)) == "123..."


class TestGetDisplayFunc:
    """Tests for the _get_display_func helper method."""

    def test_returns_instance_verbosity_display_when_present(self):
        """Test that instance's verbosity_display is returned when available."""

        class MockInstance:
            verbosity_display = MagicMock()

        instance = MockInstance()
        result = AWSConnectionRetry._get_display_func(instance)
        assert result is instance.verbosity_display

    def test_returns_no_op_lambda_when_missing(self):
        """Test that a no-op lambda is returned when verbosity_display is missing."""

        class MockInstance:
            pass

        instance = MockInstance()
        result = AWSConnectionRetry._get_display_func(instance)

        # Verify it's callable and doesn't raise
        result(2, "test message")
        result(5, "another message")

        # Verify it returns None
        assert result(1, "msg") is None


class TestRestartConnection:
    """Tests for the _restart_connection helper method."""

    def test_calls_close_when_method_exists(self):
        """Test that close() is called when it exists."""

        class MockInstance:
            close = MagicMock()

        instance = MockInstance()
        AWSConnectionRetry._restart_connection(instance)
        instance.close.assert_called_once_with()

    def test_does_nothing_when_close_missing(self):
        """Test that no error occurs when close() doesn't exist."""

        class MockInstance:
            pass

        instance = MockInstance()
        # Should not raise
        AWSConnectionRetry._restart_connection(instance)


class TestFormatRetryMessage:
    """Tests for the _format_retry_message helper method."""

    def test_formats_message_correctly(self):
        """Test that the retry message is formatted with all components."""
        exception = ValueError("Connection lost")
        result = AWSConnectionRetry._format_retry_message(
            attempt=1, max_retries=3, exception=exception, cmd_summary="ls -la...", pause=2.5
        )

        assert "AWSConnectionRetry" in result
        assert "attempt 1/4" in result  # 1 out of (max_retries + 1)
        assert "ValueError" in result
        assert "Connection lost" in result
        assert "ls -la..." in result
        assert "2.5 seconds" in result

    def test_handles_different_exception_types(self):
        """Test that different exception types are formatted correctly."""
        exceptions = [
            RuntimeError("Runtime error"),
            ConnectionError("Connection error"),
            TimeoutError("Timeout error"),
        ]

        for exc in exceptions:
            result = AWSConnectionRetry._format_retry_message(
                attempt=2, max_retries=5, exception=exc, cmd_summary="test...", pause=1.0
            )
            assert type(exc).__name__ in result
            assert str(exc) in result

    def test_formats_attempt_count_correctly(self):
        """Test that attempt counting is correct."""
        exception = ValueError("test")

        # Attempt 1 of 3 total (2 retries)
        result = AWSConnectionRetry._format_retry_message(
            attempt=1, max_retries=2, exception=exception, cmd_summary="cmd...", pause=1.0
        )
        assert "attempt 1/3" in result

        # Attempt 2 of 3 total
        result = AWSConnectionRetry._format_retry_message(
            attempt=2, max_retries=2, exception=exception, cmd_summary="cmd...", pause=1.0
        )
        assert "attempt 2/3" in result
