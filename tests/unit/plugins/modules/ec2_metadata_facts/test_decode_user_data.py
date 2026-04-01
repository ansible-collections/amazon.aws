# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import gzip
import zlib
from unittest.mock import MagicMock

import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_metadata_facts


@pytest.fixture(name="ec2_instance")
def fixture_ec2_instance():
    module = MagicMock()
    return ec2_metadata_facts.Ec2Metadata(module)


def test_decode_plain_text(ec2_instance):
    """Test decoding plain text user data."""
    data = b"#!/bin/bash\necho 'Hello World'"
    result = ec2_instance.decode_user_data(data)

    assert result == "#!/bin/bash\necho 'Hello World'"


def test_decode_zlib_compressed(ec2_instance):
    """Test decoding zlib compressed data."""
    original = b"#!/bin/bash\necho 'Hello World'"
    compressed = zlib.compress(original)
    result = ec2_instance.decode_user_data(compressed)

    assert result == original.decode("utf-8")


def test_decode_gzip_compressed(ec2_instance):
    """Test decoding gzip compressed data."""
    original = b"#!/bin/bash\necho 'Hello World'"
    compressed = gzip.compress(original)
    result = ec2_instance.decode_user_data(compressed)

    assert result == original.decode("utf-8")


def test_decode_invalid_compressed_data(ec2_instance):
    """Test handling of data that looks compressed but isn't valid."""
    # Starts with zlib header but isn't valid compressed data
    data = b"\x78\x9c" + b"invalid data"
    result = ec2_instance.decode_user_data(data)

    # Should fall back to decoding the original data
    assert isinstance(result, str)
    # Two warnings should be called: one for failed decompression, one for failed UTF-8 decode
    assert ec2_instance.module.warn.call_count == 2
    # First warning is about decompression failure
    first_warning = ec2_instance.module.warn.call_args_list[0][0][0]
    assert "Unable to decompress user-data using zlib" in first_warning
    # Second warning is about UTF-8 decoding failure
    second_warning = ec2_instance.module.warn.call_args_list[1][0][0]
    assert "Decoding user-data as UTF-8 failed" in second_warning


def test_decode_empty_data(ec2_instance):
    """Test decoding empty user data."""
    data = b""
    result = ec2_instance.decode_user_data(data)

    assert result == ""


def test_decode_unicode_in_compressed(ec2_instance):
    """Test decoding compressed data with unicode characters."""
    original = "Hello, 世界!".encode("utf-8")
    compressed = zlib.compress(original)
    result = ec2_instance.decode_user_data(compressed)

    assert result == "Hello, 世界!"


def test_decode_invalid_utf8_in_plain_data(ec2_instance):
    """Test handling of invalid UTF-8 in plain (uncompressed) data."""
    # Invalid UTF-8 sequence that doesn't start with compression headers
    data = b"\x00\x80\x81\x82\x83"
    result = ec2_instance.decode_user_data(data)

    # Should attempt to decode and fall back with ignore
    assert isinstance(result, str)
    ec2_instance.module.warn.assert_called()
