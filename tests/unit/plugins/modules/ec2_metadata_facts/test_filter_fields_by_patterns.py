# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.amazon.aws.plugins.modules import ec2_metadata_facts


def test_filter_single_pattern():
    """Test filtering with a single pattern."""
    fields = {
        "ansible_ec2_ami_id": "ami-12345",
        "ansible_ec2_public-keys-0": "ssh-rsa ...",
        "ansible_ec2_instance_id": "i-12345",
    }
    patterns = ["public-keys-0"]
    result = ec2_metadata_facts.Ec2Metadata._filter_fields_by_patterns(fields, patterns)

    assert "ansible_ec2_ami_id" in result
    assert "ansible_ec2_instance_id" in result
    assert "ansible_ec2_public-keys-0" not in result


def test_filter_multiple_patterns():
    """Test filtering with multiple patterns."""
    fields = {
        "ansible_ec2_ami_id": "ami-12345",
        "ansible_ec2_public-keys-0": "ssh-rsa ...",
        "ansible_ec2_public-keys-1": "ssh-rsa ...",
        "ansible_ec2_instance_id": "i-12345",
        "ansible_ec2_test_data": "test",
    }
    patterns = ["public-keys", "test"]
    result = ec2_metadata_facts.Ec2Metadata._filter_fields_by_patterns(fields, patterns)

    assert "ansible_ec2_ami_id" in result
    assert "ansible_ec2_instance_id" in result
    assert "ansible_ec2_public-keys-0" not in result
    assert "ansible_ec2_public-keys-1" not in result
    assert "ansible_ec2_test_data" not in result


def test_filter_no_matches():
    """Test filtering when no patterns match."""
    fields = {
        "ansible_ec2_ami_id": "ami-12345",
        "ansible_ec2_instance_id": "i-12345",
    }
    patterns = ["public-keys"]
    result = ec2_metadata_facts.Ec2Metadata._filter_fields_by_patterns(fields, patterns)

    assert result == fields


def test_filter_empty_patterns():
    """Test filtering with empty pattern list."""
    fields = {
        "ansible_ec2_ami_id": "ami-12345",
        "ansible_ec2_public-keys-0": "ssh-rsa ...",
    }
    patterns = []
    result = ec2_metadata_facts.Ec2Metadata._filter_fields_by_patterns(fields, patterns)

    assert result == fields


def test_filter_empty_fields():
    """Test filtering with empty fields dict."""
    fields = {}
    patterns = ["public-keys"]
    result = ec2_metadata_facts.Ec2Metadata._filter_fields_by_patterns(fields, patterns)

    assert result == {}


def test_filter_regex_pattern():
    """Test filtering with regex pattern."""
    fields = {
        "ansible_ec2_network_interfaces_macs_00_11_22_33_44_55_device_number": "0",
        "ansible_ec2_network_interfaces_macs_aa_bb_cc_dd_ee_ff_device_number": "1",
        "ansible_ec2_instance_id": "i-12345",
    }
    patterns = ["macs.*device_number"]
    result = ec2_metadata_facts.Ec2Metadata._filter_fields_by_patterns(fields, patterns)

    assert "ansible_ec2_instance_id" in result
    assert "ansible_ec2_network_interfaces_macs_00_11_22_33_44_55_device_number" not in result
    assert "ansible_ec2_network_interfaces_macs_aa_bb_cc_dd_ee_ff_device_number" not in result


def test_filter_does_not_modify_original():
    """Test that filtering doesn't modify the original dict."""
    fields = {
        "ansible_ec2_ami_id": "ami-12345",
        "ansible_ec2_public-keys-0": "ssh-rsa ...",
    }
    original_fields = dict(fields)
    patterns = ["public-keys"]
    result = ec2_metadata_facts.Ec2Metadata._filter_fields_by_patterns(fields, patterns)

    # Original should be unchanged
    assert fields == original_fields
    # Result should be filtered
    assert "ansible_ec2_public-keys-0" not in result


def test_filter_partial_match():
    """Test that partial matches work correctly."""
    fields = {
        "ansible_ec2_public_hostname": "ec2-1-2-3-4.compute.amazonaws.com",
        "ansible_ec2_public_ipv4": "1.2.3.4",
        "ansible_ec2_public-keys-0": "ssh-rsa ...",
    }
    patterns = ["public-keys"]
    result = ec2_metadata_facts.Ec2Metadata._filter_fields_by_patterns(fields, patterns)

    # Should only filter exact pattern matches, not partial
    assert "ansible_ec2_public_hostname" in result
    assert "ansible_ec2_public_ipv4" in result
    assert "ansible_ec2_public-keys-0" not in result
