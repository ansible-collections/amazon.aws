# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import string

from ansible_collections.amazon.aws.plugins.plugin_utils.ssm.common import MARK_LENGTH
from ansible_collections.amazon.aws.plugins.plugin_utils.ssm.common import generate_mark


class TestGenerateMark:
    """Tests for the generate_mark() function."""

    def test_generate_mark_length(self):
        """Test that generated mark has correct length."""
        mark = generate_mark()
        assert len(mark) == MARK_LENGTH

    def test_generate_mark_only_ascii_letters(self):
        """Test that generated mark contains only ASCII letters."""
        mark = generate_mark()
        assert all(c in string.ascii_letters for c in mark)

    def test_generate_mark_randomness(self):
        """Test that generate_mark produces different results (probabilistically)."""
        # Generate multiple marks and ensure they're not all identical
        # With 26 characters from 52 choices, probability of collision is extremely low
        marks = [generate_mark() for _ in range(10)]
        # At least 8 out of 10 should be unique (allows for rare collisions)
        assert len(set(marks)) >= 8

    def test_generate_mark_no_digits(self):
        """Test that generated mark contains no digits."""
        mark = generate_mark()
        assert not any(c.isdigit() for c in mark)

    def test_generate_mark_no_special_chars(self):
        """Test that generated mark contains no special characters."""
        mark = generate_mark()
        assert mark.isalpha()
