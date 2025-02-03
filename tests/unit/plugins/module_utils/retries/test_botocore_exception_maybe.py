# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

try:
    import botocore
except ImportError:
    pass

import ansible_collections.amazon.aws.plugins.module_utils.retries as util_retries


def test_botocore_exception_maybe(monkeypatch):
    none_type = type(None)
    assert util_retries._botocore_exception_maybe() is botocore.exceptions.ClientError
    monkeypatch.setattr(util_retries, "HAS_BOTO3", False)
    assert util_retries._botocore_exception_maybe() is none_type
