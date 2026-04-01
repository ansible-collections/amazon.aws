# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.amazon.aws.plugins.modules import ec2_metadata_facts


def test_build_key_multiple_fields():
    """Test building key from multiple path components."""
    split_fields = ["placement", "availability-zone"]
    result = ec2_metadata_facts.Ec2Metadata._build_metadata_key(split_fields)

    assert result == "placement-availability-zone"


def test_build_key_three_fields():
    """Test building key from three path components."""
    split_fields = ["network", "interfaces", "macs"]
    result = ec2_metadata_facts.Ec2Metadata._build_metadata_key(split_fields)

    assert result == "network-interfaces-macs"


def test_build_key_single_field():
    """Test building key from single path component."""
    split_fields = ["ami-id"]
    result = ec2_metadata_facts.Ec2Metadata._build_metadata_key(split_fields)

    assert result == "ami-id"


def test_build_key_with_empty_second_field():
    """Test that empty second field triggers concatenation instead of joining."""
    split_fields = ["hostname", ""]
    result = ec2_metadata_facts.Ec2Metadata._build_metadata_key(split_fields)

    # When split_fields[1] is empty, should concatenate
    assert result == "hostname"


def test_build_key_empty_list():
    """Test building key from empty list."""
    split_fields = []
    result = ec2_metadata_facts.Ec2Metadata._build_metadata_key(split_fields)

    assert result == ""


def test_build_key_with_numbers():
    """Test building key with numeric components."""
    split_fields = ["block-device-mapping", "ebs1"]
    result = ec2_metadata_facts.Ec2Metadata._build_metadata_key(split_fields)

    assert result == "block-device-mapping-ebs1"


def test_build_key_many_components():
    """Test building key from many path components."""
    split_fields = ["network", "interfaces", "macs", "00:11:22:33:44:55", "subnet-id"]
    result = ec2_metadata_facts.Ec2Metadata._build_metadata_key(split_fields)

    assert result == "network-interfaces-macs-00:11:22:33:44:55-subnet-id"
