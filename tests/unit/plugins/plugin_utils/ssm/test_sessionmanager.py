# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from io import BytesIO
from unittest.mock import Mock

import pytest

from ansible_collections.amazon.aws.plugins.plugin_utils.ssm.sessionmanager import ProcessManager


class TestProcessManager:
    """Tests for the ProcessManager class."""

    @pytest.fixture
    def process_manager(self, monkeypatch):
        """Create a ProcessManager instance for testing."""
        session = Mock()
        session.stdin = Mock()
        session.stdin.write = Mock()
        session.stdin.flush = Mock()
        session.poll = Mock(return_value=None)
        session.stderr = Mock()

        # Create a mock stdout that has both BytesIO functionality and fileno
        stdout = Mock()
        stdout_buffer = BytesIO()
        stdout.write = stdout_buffer.write
        stdout.read = stdout_buffer.read
        stdout.readline = stdout_buffer.readline
        stdout.seek = stdout_buffer.seek
        stdout.fileno = Mock(return_value=1)

        verbosity_display = Mock()

        # Mock _create_polling_obj to avoid issues with select.poll()
        mock_poller = Mock()
        mock_poller.poll = Mock(return_value=[])

        def mock_create_polling_obj(fd):
            return mock_poller

        monkeypatch.setattr(
            "ansible_collections.amazon.aws.plugins.plugin_utils.ssm.sessionmanager._create_polling_obj",
            mock_create_polling_obj,
        )

        pm = ProcessManager(
            instance_id="i-1234567890abcdef0",
            session=session,
            stdout=stdout,
            timeout=60,
            verbosity_display=verbosity_display,
        )

        # Store the mock poller for test access
        pm._test_poller = mock_poller
        pm._test_stdout_buffer = stdout_buffer

        return pm

    def test_stdin_write_with_string(self, process_manager):
        """Test stdin_write converts string to bytes."""
        process_manager.stdin_write("test command")

        # Should encode to UTF-8 and write
        process_manager._session.stdin.write.assert_called_once_with(b"test command")
        process_manager._session.stdin.flush.assert_called_once()

    def test_stdin_write_with_bytes(self, process_manager):
        """Test stdin_write handles bytes directly."""
        process_manager.stdin_write(b"test command")

        # Should write bytes directly
        process_manager._session.stdin.write.assert_called_once_with(b"test command")
        process_manager._session.stdin.flush.assert_called_once()

    def test_stdin_write_with_unicode(self, process_manager):
        """Test stdin_write handles Unicode strings."""
        process_manager.stdin_write("test with émojis 🎉")

        # Should encode Unicode to UTF-8
        expected = "test with émojis 🎉".encode("utf-8")
        process_manager._session.stdin.write.assert_called_once_with(expected)

    def test_stdout_read_text(self, process_manager):
        """Test stdout_read_text reads and decodes data."""
        # Write some test data to stdout buffer
        process_manager._test_stdout_buffer.write(b"test output")
        process_manager._test_stdout_buffer.seek(0)

        result = process_manager.stdout_read_text(size=11)
        assert result == "test output"

    def test_stdout_read_text_with_unicode(self, process_manager):
        """Test stdout_read_text handles Unicode."""
        # Write Unicode data
        unicode_text = "test émojis 🎉"
        process_manager._test_stdout_buffer.write(unicode_text.encode("utf-8"))
        process_manager._test_stdout_buffer.seek(0)

        result = process_manager.stdout_read_text(size=100)
        assert result == unicode_text

    def test_stdout_readline(self, process_manager):
        """Test stdout_readline reads a line."""
        # Write a line to stdout buffer
        process_manager._test_stdout_buffer.write(b"test line\n")
        process_manager._test_stdout_buffer.seek(0)

        result = process_manager.stdout_readline()
        assert result == "test line\n"

    def test_stdout_readline_with_unicode(self, process_manager):
        """Test stdout_readline handles Unicode."""
        # Write Unicode line
        unicode_line = "test émojis 🎉\n"
        process_manager._test_stdout_buffer.write(unicode_line.encode("utf-8"))
        process_manager._test_stdout_buffer.seek(0)

        result = process_manager.stdout_readline()
        assert result == unicode_line

    def test_poll_stdout(self, process_manager):
        """Test poll_stdout returns boolean result."""
        # Configure the test poller to return data available
        process_manager._test_poller.poll.return_value = [(1, 1)]  # File descriptor ready

        result = process_manager.poll_stdout(length=1000)
        assert result is True
        process_manager._test_poller.poll.assert_called_with(1000)

    def test_poll_stdout_no_data(self, process_manager):
        """Test poll_stdout returns False when no data."""
        # Configure the test poller to return no data
        process_manager._test_poller.poll.return_value = []

        result = process_manager.poll_stdout(length=500)
        assert result is False
        process_manager._test_poller.poll.assert_called_with(500)
