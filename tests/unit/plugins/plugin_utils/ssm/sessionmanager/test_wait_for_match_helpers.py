# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import Mock

import pytest

from ansible_collections.amazon.aws.plugins.plugin_utils.ssm.sessionmanager import ProcessManager


class TestTryMatchString:
    """Tests for the _try_match_string helper method."""

    @pytest.fixture
    def process_manager(self, monkeypatch):
        """Create a minimal ProcessManager instance for testing helper methods."""
        session = Mock()
        stdout = Mock()
        stdout.fileno = Mock(return_value=1)

        mock_poller = Mock()
        monkeypatch.setattr(
            "ansible_collections.amazon.aws.plugins.plugin_utils.ssm.sessionmanager._create_polling_obj",
            lambda fd: mock_poller,
        )

        verbosity_display = Mock()
        pm = ProcessManager(
            instance_id="i-test",
            session=session,
            stdout=stdout,
            timeout=60,
            verbosity_display=verbosity_display,
        )
        return pm

    def test_match_found_returns_true(self, process_manager):
        """Test that _try_match_string returns True when match is found."""
        stdout = "some output with marker here and more"
        match = "marker"
        result = process_manager._try_match_string(stdout, match, "TEST", 1.5)

        assert result is True
        # Should log success message
        process_manager.verbosity_display.assert_called_once()
        call_args = process_manager.verbosity_display.call_args[0]
        assert call_args[0] == 4
        assert "MATCHED" in call_args[1]
        assert "1.50s" in call_args[1]

    def test_match_not_found_returns_false(self, process_manager):
        """Test that _try_match_string returns False when match not found."""
        stdout = "some output without the expected text"
        match = "marker"
        result = process_manager._try_match_string(stdout, match, "TEST", 2.0)

        assert result is False
        # Should log debug message with last 100 chars
        process_manager.verbosity_display.assert_called_once()
        call_args = process_manager.verbosity_display.call_args[0]
        assert call_args[0] == 5
        assert "No match yet" in call_args[1]

    def test_match_at_beginning(self, process_manager):
        """Test matching string at beginning of stdout."""
        stdout = "marker at the start"
        match = "marker"
        result = process_manager._try_match_string(stdout, match, "TEST", 0.1)

        assert result is True

    def test_match_at_end(self, process_manager):
        """Test matching string at end of stdout."""
        stdout = "lots of output before the marker"
        match = "marker"
        result = process_manager._try_match_string(stdout, match, "TEST", 0.1)

        assert result is True

    def test_substring_match_found(self, process_manager):
        """Test that substring matches are found correctly."""
        stdout = "some output with mark but not complete marker"
        match = "marker"
        result = process_manager._try_match_string(stdout, match, "TEST", 0.1)

        # str.find() looks for substrings, so "marker" will be found
        assert result is True


class TestTryMatchCallable:
    """Tests for the _try_match_callable helper method."""

    @pytest.fixture
    def process_manager(self, monkeypatch):
        """Create a minimal ProcessManager instance."""
        session = Mock()
        stdout = Mock()
        stdout.fileno = Mock(return_value=1)

        mock_poller = Mock()
        monkeypatch.setattr(
            "ansible_collections.amazon.aws.plugins.plugin_utils.ssm.sessionmanager._create_polling_obj",
            lambda fd: mock_poller,
        )

        verbosity_display = Mock()
        pm = ProcessManager(
            instance_id="i-test",
            session=session,
            stdout=stdout,
            timeout=60,
            verbosity_display=verbosity_display,
        )
        return pm

    def test_callable_match_on_raw_stdout(self, process_manager):
        """Test callable match succeeds on raw stdout."""
        stdout = "output with PATTERN here"

        def match(text):
            return "PATTERN" in text

        result = process_manager._try_match_callable(stdout, match, False, "TEST", 1.0)

        assert result is True
        process_manager.verbosity_display.assert_called_once()
        call_args = process_manager.verbosity_display.call_args[0]
        assert call_args[0] == 4
        assert "MATCHED" in call_args[1]

    def test_callable_match_on_filtered_stdout(self, process_manager):
        """Test callable match succeeds on ANSI-filtered stdout when raw doesn't match."""
        stdout = "\x1b[31mPATTERN\x1b[0m"  # ANSI color codes around PATTERN

        def match(text):
            # This will only match filtered text (no ANSI codes)
            return "PATTERN" in text and "\x1b" not in text

        # Must use is_windows=True for ANSI filtering to actually happen
        result = process_manager._try_match_callable(stdout, match, True, "TEST", 1.0)

        # Should succeed because filtered stdout will match
        assert result is True

    def test_callable_no_match(self, process_manager):
        """Test callable match fails when pattern not found."""
        stdout = "output without the expected pattern"

        def match(text):
            return "PATTERN" in text

        result = process_manager._try_match_callable(stdout, match, False, "TEST", 1.0)

        assert result is False
        # Should log multiple debug messages (3 total)
        assert process_manager.verbosity_display.call_count == 3

    def test_callable_with_windows_ansi_filtering(self, process_manager):
        """Test that Windows ANSI filtering is applied."""
        # This tests that filter_ansi is called with is_windows=True
        stdout = "some output"
        match = Mock(return_value=False)
        result = process_manager._try_match_callable(stdout, match, True, "TEST", 1.0)

        assert result is False
        # Match should be called twice (raw and filtered)
        assert match.call_count == 2


class TestLogProgressIfNeeded:
    """Tests for the _log_progress_if_needed helper method."""

    @pytest.fixture
    def process_manager(self, monkeypatch):
        """Create a minimal ProcessManager instance."""
        session = Mock()
        stdout = Mock()
        stdout.fileno = Mock(return_value=1)

        mock_poller = Mock()
        monkeypatch.setattr(
            "ansible_collections.amazon.aws.plugins.plugin_utils.ssm.sessionmanager._create_polling_obj",
            lambda fd: mock_poller,
        )

        verbosity_display = Mock()
        pm = ProcessManager(
            instance_id="i-test",
            session=session,
            stdout=stdout,
            timeout=60,
            verbosity_display=verbosity_display,
        )
        return pm

    def test_logs_when_interval_exceeded(self, process_manager):
        """Test progress is logged when 5 seconds have elapsed."""
        current_time = 100.0
        last_progress_log = 94.0  # 6 seconds ago
        wait_start = 90.0

        result = process_manager._log_progress_if_needed(
            current_time, last_progress_log, wait_start, "TEST", 10, 50, 500
        )

        assert result == current_time  # Should update timestamp
        process_manager.verbosity_display.assert_called_once()
        call_args = process_manager.verbosity_display.call_args[0]
        assert call_args[0] == 3
        assert "Still waiting" in call_args[1]
        assert "10 lines" in call_args[1]
        assert "50 polls" in call_args[1]
        assert "500 bytes" in call_args[1]

    def test_does_not_log_when_interval_not_exceeded(self, process_manager):
        """Test progress is not logged when less than 5 seconds have elapsed."""
        current_time = 100.0
        last_progress_log = 98.0  # Only 2 seconds ago
        wait_start = 90.0

        result = process_manager._log_progress_if_needed(
            current_time, last_progress_log, wait_start, "TEST", 5, 20, 200
        )

        assert result == last_progress_log  # Should not update timestamp
        process_manager.verbosity_display.assert_not_called()

    def test_logs_exactly_at_interval(self, process_manager):
        """Test progress is logged when exactly 5 seconds have elapsed."""
        current_time = 100.0
        last_progress_log = 95.0  # Exactly 5 seconds ago
        wait_start = 90.0

        result = process_manager._log_progress_if_needed(
            current_time, last_progress_log, wait_start, "TEST", 8, 30, 300
        )

        assert result == current_time
        process_manager.verbosity_display.assert_called_once()


class TestCheckAndWarnCommandEcho:
    """Tests for the _check_and_warn_command_echo helper method."""

    @pytest.fixture
    def process_manager(self, monkeypatch):
        """Create a minimal ProcessManager instance."""
        session = Mock()
        stdout = Mock()
        stdout.fileno = Mock(return_value=1)

        mock_poller = Mock()
        monkeypatch.setattr(
            "ansible_collections.amazon.aws.plugins.plugin_utils.ssm.sessionmanager._create_polling_obj",
            lambda fd: mock_poller,
        )

        verbosity_display = Mock()
        pm = ProcessManager(
            instance_id="i-test",
            session=session,
            stdout=stdout,
            timeout=60,
            verbosity_display=verbosity_display,
        )
        return pm

    def test_warns_when_powershell_detected(self, process_manager):
        """Test warning is logged when PowerShell keyword detected."""
        stdout = "some output with PowerShell keyword in it"
        process_manager._check_and_warn_command_echo(stdout, 10, True, "EXEC_COMMUNICATE")

        process_manager.verbosity_display.assert_called_once()
        call_args = process_manager.verbosity_display.call_args[0]
        assert call_args[0] == 2
        assert "WARNING" in call_args[1]
        assert "PSReadLine" in call_args[1]

    def test_warns_when_base64_pattern_detected(self, process_manager):
        """Test warning is logged when base64-like pattern detected."""
        # Create output with many repeated capital letters (simulating base64)
        stdout = "A" * 60 + "some other text"
        process_manager._check_and_warn_command_echo(stdout, 10, True, "EXEC_COMMUNICATE")

        process_manager.verbosity_display.assert_called_once()

    def test_no_warn_when_not_windows(self, process_manager):
        """Test no warning when not Windows."""
        stdout = "some output with PowerShell keyword"
        process_manager._check_and_warn_command_echo(stdout, 10, False, "EXEC_COMMUNICATE")

        process_manager.verbosity_display.assert_not_called()

    def test_no_warn_when_wrong_label(self, process_manager):
        """Test no warning when label is not EXEC_COMMUNICATE."""
        stdout = "some output with PowerShell keyword"
        process_manager._check_and_warn_command_echo(stdout, 10, True, "DIFFERENT_LABEL")

        process_manager.verbosity_display.assert_not_called()

    def test_no_warn_when_few_lines(self, process_manager):
        """Test no warning when line count is low."""
        stdout = "some output with PowerShell keyword"
        process_manager._check_and_warn_command_echo(stdout, 3, True, "EXEC_COMMUNICATE")

        process_manager.verbosity_display.assert_not_called()

    def test_no_warn_when_no_suspicious_content(self, process_manager):
        """Test no warning when output looks normal."""
        stdout = "normal command output without suspicious patterns"
        process_manager._check_and_warn_command_echo(stdout, 10, True, "EXEC_COMMUNICATE")

        process_manager.verbosity_display.assert_not_called()
