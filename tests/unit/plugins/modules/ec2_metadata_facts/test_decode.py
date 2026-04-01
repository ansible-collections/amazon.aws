# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock

import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_metadata_facts


@pytest.fixture(name="ec2_instance")
def fixture_ec2_instance():
    module = MagicMock()
    return ec2_metadata_facts.Ec2Metadata(module)


def test_decode_valid_utf8(ec2_instance):
    """Test decoding valid UTF-8 data."""
    data = b"Hello, World!"
    result = ec2_instance._decode(data)

    assert result == "Hello, World!"
    assert isinstance(result, str)


def test_decode_unicode_characters(ec2_instance):
    """Test decoding UTF-8 with unicode characters."""
    data = "Hello, 世界!".encode("utf-8")
    result = ec2_instance._decode(data)

    assert result == "Hello, 世界!"


def test_decode_invalid_utf8(ec2_instance):
    """Test decoding invalid UTF-8 with fallback."""
    # Invalid UTF-8 sequence
    data = b"\x80\x81\x82\x83"
    result = ec2_instance._decode(data)

    # Should not raise an exception and should return a string
    assert isinstance(result, str)
    # Should have called module.warn
    ec2_instance.module.warn.assert_called_once()
    assert "Decoding user-data as UTF-8 failed" in ec2_instance.module.warn.call_args[0][0]


def test_decode_empty_bytes(ec2_instance):
    """Test decoding empty bytes."""
    data = b""
    result = ec2_instance._decode(data)

    assert result == ""
