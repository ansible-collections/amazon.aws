# (c) 2022 Red Hat Inc.

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock, patch, ANY, call
import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_ami_info

module_name = "ansible_collections.amazon.aws.plugins.modules.ec2_ami_info"


@pytest.mark.parametrize("executable_users,filters,image_ids,owners,expected", [
    ([], {}, [], [], {}),
    ([], {}, ['ami-1234567890'], [], {'ImageIds': ['ami-1234567890']}),
    ([], {}, [], ['1234567890'], {'Filters': [{'Name': 'owner-id', 'Values': ['1234567890']}]}),
    ([], {'owner-alias': 'test_ami_owner'}, [], ['1234567890'], {'Filters': [{'Name': 'owner-alias', 'Values': ['test_ami_owner']}, {'Name': 'owner-id', 'Values': ['1234567890']}]})])
def test_build_request_args(executable_users, filters, image_ids, owners, expected):
    assert ec2_ami_info.build_request_args(
        executable_users, filters, image_ids, owners) == expected
