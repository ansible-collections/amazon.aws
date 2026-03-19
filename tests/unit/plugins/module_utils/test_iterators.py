# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.iterators import chunked_payload
from ansible_collections.amazon.aws.plugins.module_utils.iterators import chunks


class TestChunks:
    """Tests for the chunks() function."""

    def test_chunks_even_division(self):
        """Test chunking a list that divides evenly."""
        data = [1, 2, 3, 4, 5, 6]
        result = list(chunks(data, 2))
        assert result == [[1, 2], [3, 4], [5, 6]]

    def test_chunks_uneven_division(self):
        """Test chunking a list that doesn't divide evenly."""
        data = [1, 2, 3, 4, 5]
        result = list(chunks(data, 2))
        assert result == [[1, 2], [3, 4], [5]]

    def test_chunks_single_chunk(self):
        """Test when chunk size is larger than list."""
        data = [1, 2, 3]
        result = list(chunks(data, 10))
        assert result == [[1, 2, 3]]

    def test_chunks_empty_list(self):
        """Test chunking an empty list."""
        data = []
        result = list(chunks(data, 2))
        assert result == []

    def test_chunks_chunk_size_one(self):
        """Test chunking with size 1."""
        data = [1, 2, 3]
        result = list(chunks(data, 1))
        assert result == [[1], [2], [3]]


class TestChunkedPayload:
    """Tests for the chunked_payload() function."""

    def test_chunked_payload_bytes(self):
        """Test chunking bytes data."""
        data = b"0123456789"
        result = list(chunked_payload(data, buffer_size=4))
        expected = [
            (b"0123", False),
            (b"4567", False),
            (b"89", True),
        ]
        assert result == expected

    def test_chunked_payload_string(self):
        """Test chunking string data (converted to bytes)."""
        data = "hello world"
        result = list(chunked_payload(data, buffer_size=5))
        expected = [
            (b"hello", False),
            (b" worl", False),
            (b"d", True),
        ]
        assert result == expected

    def test_chunked_payload_exact_buffer_size(self):
        """Test when payload size is exactly buffer size."""
        data = b"12345"
        result = list(chunked_payload(data, buffer_size=5))
        assert result == [(b"12345", True)]

    def test_chunked_payload_smaller_than_buffer(self):
        """Test when payload is smaller than buffer size."""
        data = b"123"
        result = list(chunked_payload(data, buffer_size=10))
        assert result == [(b"123", True)]

    def test_chunked_payload_empty(self):
        """Test chunking empty payload."""
        data = b""
        result = list(chunked_payload(data, buffer_size=4))
        # Empty payload yields no chunks (range(0, 0, 4) produces no iterations)
        assert result == []

    def test_chunked_payload_unicode_string(self):
        """Test chunking unicode string."""
        data = "héllo wörld"  # Unicode characters
        result = list(chunked_payload(data, buffer_size=6))
        # String should be converted to UTF-8 bytes
        # "héllo wörld" in UTF-8 is 13 bytes (é=2 bytes, ö=2 bytes)
        assert len(result) == 3
        assert result[0][1] is False  # Not last
        assert result[1][1] is False  # Not last
        assert result[2][1] is True  # Last chunk

    def test_chunked_payload_large_buffer(self):
        """Test with default buffer size."""
        data = b"x" * 2500  # Larger than default 1024
        result = list(chunked_payload(data))  # Default buffer_size=1024
        assert len(result) == 3  # 1024 + 1024 + 452
        assert result[0] == (b"x" * 1024, False)
        assert result[1] == (b"x" * 1024, False)
        assert result[2] == (b"x" * 452, True)

    def test_chunked_payload_is_last_flag(self):
        """Test that is_last flag is correct for all chunks."""
        data = b"0123456789"
        result = list(chunked_payload(data, buffer_size=3))

        # All chunks except last should have is_last=False
        for chunk, is_last in result[:-1]:
            assert is_last is False

        # Last chunk should have is_last=True
        assert result[-1][1] is True
