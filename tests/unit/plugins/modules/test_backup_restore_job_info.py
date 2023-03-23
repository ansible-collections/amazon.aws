# (c) 2022 Red Hat Inc.

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest
from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

from ansible_collections.amazon.aws.plugins.modules import backup_restore_job_info

module_name = "ansible_collections.amazon.aws.plugins.modules.backup_restore_job_info"


@pytest.mark.parametrize(
    "account_id, status, created_before, created_after, completed_before, completed_after,expected",
    [
        ("", "", "", "", "", "", {}),
        ("123456789012", "", "", "", "", "", {"ByAccountId": "123456789012"}),
        ("123456789012", "COMPLETED", "","", "","",{"ByAccountId": "123456789012", "ByStatus": "COMPLETED"},)
    ],
)
def test_build_request_args(account_id, status, created_before, created_after, completed_before, completed_after, expected):
    assert backup_restore_job_info.build_request_args(account_id, status, created_before, created_after, completed_before, completed_after) == expected
