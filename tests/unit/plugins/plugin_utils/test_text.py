# -*- coding: utf-8 -*-

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.plugins.plugin_utils.text import filter_ansi


@pytest.mark.parametrize(
    "input_line,is_windows,expected_output",
    [
        # Non-Windows: should return line unchanged
        ("Simple text", False, "Simple text"),
        ("Text with\nnewline", False, "Text with\nnewline"),
        # Windows: should filter ANSI codes
        ("Simple text", True, "Simple text"),
        # OSC sequences (ESC ] ... BEL)
        ("\x1b]0;Window Title\x07Hello", True, "Hello"),
        # CSI sequences
        ("\x1b[31mRed text\x1b[0m", True, "Red text"),
        ("\x9B31mRed text\x9B0m", True, "Red text"),
        # Mixed ANSI codes
        ("\x1b[1;32m\x1b]0;Title\x07Bold Green\x1b[0m", True, "Bold Green"),
        # Windows line ending replacement
        ("Line1\r\r\nLine2", True, "Line1\nLine2"),
        # 201 character line truncation
        ("a" * 201, True, "a" * 200),
        ("a" * 200, True, "a" * 200),
        ("a" * 202, True, "a" * 202),  # Not exactly 201, no truncation
    ],
)
def test_filter_ansi(input_line, is_windows, expected_output):
    """Test that filter_ansi correctly removes ANSI codes and handles Windows quirks."""
    result = filter_ansi(input_line, is_windows)
    assert result == expected_output


def test_filter_ansi_with_bytes():
    """Test that filter_ansi handles bytes input by converting to text."""
    result = filter_ansi(b"Test bytes", False)
    assert result == "Test bytes"


def test_filter_ansi_complex_windows():
    """Test complex Windows terminal output with multiple ANSI sequences."""
    # Simulating PowerShell progress bar output
    input_line = "\x1b]0;PowerShell\x07\x1b[?25l\x1b[1;32mProcessing\x1b[0m\x1b[?25h"
    expected = "Processing"
    result = filter_ansi(input_line, is_windows=True)
    assert result == expected
