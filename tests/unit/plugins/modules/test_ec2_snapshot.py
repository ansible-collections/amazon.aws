# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.modules import ec2_snapshot

module_name = "ansible_collections.amazon.aws.plugins.modules.ec2_snapshot"

USER_A = {"UserId": "111111111111"}
USER_B = {"UserId": "222222222222"}
GROUP_ALL = {"Group": "all"}


@pytest.mark.parametrize(
    "existing,user_ids,group_names,purge,expected",
    [
        # No purge - requested user IDs are already a subset of the existing ones
        ([USER_A, USER_B], ["111111111111"], None, False, False),
        ([USER_A, USER_B], ["111111111111", "222222222222"], None, False, False),
        # No purge - a requested user ID is missing
        ([USER_A], ["111111111111", "222222222222"], None, False, True),
        ([], ["111111111111"], None, False, True),
        # No purge - already public, nothing to add
        ([GROUP_ALL], ["111111111111"], None, False, False),
        ([GROUP_ALL, USER_A], None, ["all"], False, False),
        # No purge - make public
        ([USER_A], None, ["all"], False, True),
        # Purge - extra user IDs must be removed
        ([USER_A, USER_B], ["111111111111"], None, True, True),
        ([USER_A], ["111111111111"], None, True, False),
        ([GROUP_ALL, USER_A], ["111111111111"], None, True, True),
        ([GROUP_ALL], None, ["all"], True, False),
        ([GROUP_ALL, USER_A], None, ["all"], True, True),
        # Purge - reset to private
        ([], None, None, True, False),
        ([USER_A], None, None, True, True),
    ],
)
@patch(module_name + ".describe_snapshot_attribute")
def test_check_user_or_group_update_needed(m_describe, existing, user_ids, group_names, purge, expected):
    module = MagicMock()
    module.params = {
        "snapshot_id": "snap-123456789",
        "purge_create_vol_permission": purge,
        "user_ids": user_ids,
        "group_names": group_names,
    }
    m_describe.return_value = {"CreateVolumePermissions": existing}

    assert ec2_snapshot.check_user_or_group_update_needed(module, MagicMock()) is expected
