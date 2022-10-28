# -*- coding: utf-8 -*-

# Copyright 2017 Sloane Hertel <shertel@redhat.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
import pytest
from unittest.mock import MagicMock

from ansible.errors import AnsibleError
from ansible.template import Templar
from ansible.parsing.dataloader import DataLoader
from ansible_collections.amazon.aws.plugins.plugin_utils.inventory import AWSInventoryBase


@pytest.fixture()
def inventory():
    inventory = AWSInventoryBase()
    inventory._options = {
        "aws_profile": "first_precedence",
        "aws_access_key": "test_access_key",
        "aws_secret_key": "test_secret_key",
        "aws_security_token": "test_security_token",
        "iam_role_arn": None,
        "use_contrib_script_compatible_ec2_tag_keys": False,
        "hostvars_prefix": "",
        "hostvars_suffix": "",
        "strict": True,
        "compose": {},
        "groups": {},
        "keyed_groups": [],
        "regions": ["us-east-1"],
        "filters": [],
        "include_filters": [],
        "exclude_filters": [],
        "hostnames": [],
        "strict_permissions": False,
        "allow_duplicated_hosts": False,
        "cache": False,
        "include_extra_api_calls": False,
        "use_contrib_script_compatible_sanitization": False,
    }
    inventory.inventory = MagicMock()
    return inventory


@pytest.fixture()
def loader():
    return DataLoader()


def test_boto3_conn(inventory, loader):
    inventory._options = {"aws_profile": "first_precedence",
                          "aws_access_key": "test_access_key",
                          "aws_secret_key": "test_secret_key",
                          "aws_security_token": "test_security_token",
                          "iam_role_arn": None}
    inventory._set_credentials(loader)
    with pytest.raises(AnsibleError) as error_message:
        for _connection, _region in inventory._boto3_conn(regions=['us-east-1'], resource="test"):
            assert "Insufficient credentials found" in error_message


def test_set_credentials(inventory, loader):
    inventory._options = {'aws_access_key': 'test_access_key',
                          'aws_secret_key': 'test_secret_key',
                          'aws_security_token': 'test_security_token',
                          'aws_profile': 'test_profile',
                          'iam_role_arn': 'arn:aws:iam::123456789012:role/test-role'}
    inventory._set_credentials(loader)

    assert inventory.boto_profile == "test_profile"
    assert inventory.aws_access_key_id == "test_access_key"
    assert inventory.aws_secret_access_key == "test_secret_key"
    assert inventory.aws_security_token == "test_security_token"
    assert inventory.iam_role_arn == "arn:aws:iam::123456789012:role/test-role"


def test_insufficient_credentials(inventory, loader):
    inventory._options = {
        'aws_access_key': None,
        'aws_secret_key': None,
        'aws_security_token': None,
        'aws_profile': None,
        'iam_role_arn': None
    }
    with pytest.raises(AnsibleError) as error_message:
        inventory._set_credentials(loader)
        assert "Insufficient credentials found" in error_message
