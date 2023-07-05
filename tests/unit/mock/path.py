#  GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from ansible.utils.path import unfrackpath


mock_unfrackpath_noop = MagicMock(spec_set=unfrackpath, side_effect=lambda x, *args, **kwargs: x)
