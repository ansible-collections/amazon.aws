# -*- coding: utf-8 -*-
#
# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.plugins.module_utils import s3

SAMPLE_OWNER = {
    "DisplayName": "example-root+123456789012",
    "ID": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
}

SAMPLE_GRANT_FULL = {
    "Grantee": {
        "DisplayName": "example-root+123456789012",
        "ID": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "Type": "CanonicalUser",
    },
    "Permission": "FULL_CONTROL",
}

SAMPLE_GRANT_PUBLIC_READ = {
    "Grantee": {"Type": "Group", "URI": "http://acs.amazonaws.com/groups/global/AllUsers"},
    "Permission": "READ",
}

SAMPLE_GRANT_PUBLIC_WRITE = {
    "Grantee": {"Type": "Group", "URI": "http://acs.amazonaws.com/groups/global/AllUsers"},
    "Permission": "WRITE",
}

SAMPLE_GRANT_AUTH_READ = {
    "Grantee": {"Type": "Group", "URI": "http://acs.amazonaws.com/groups/global/AuthenticatedUsers"},
    "Permission": "READ",
}

SAMPLE_GRANT_OTHER = {
    "Grantee": {
        "DisplayName": "example-root+001122334455",
        "ID": "123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0",
        "Type": "CanonicalUser",
    },
    "Permission": "FULL_CONTROL",
}


@pytest.mark.parametrize(
    "acl,result",
    [
        ({"Grants": [SAMPLE_GRANT_FULL]}, None),
        ({"Owner": SAMPLE_OWNER}, None),
        ({"Owner": SAMPLE_OWNER, "Grants": [SAMPLE_GRANT_FULL]}, "private"),
        ({"Owner": SAMPLE_OWNER, "Grants": [SAMPLE_GRANT_FULL, SAMPLE_GRANT_AUTH_READ]}, "authenticated-read"),
        ({"Owner": SAMPLE_OWNER, "Grants": [SAMPLE_GRANT_AUTH_READ, SAMPLE_GRANT_FULL]}, "authenticated-read"),
        ({"Owner": SAMPLE_OWNER, "Grants": [SAMPLE_GRANT_FULL, SAMPLE_GRANT_PUBLIC_READ]}, "public-read"),
        ({"Owner": SAMPLE_OWNER, "Grants": [SAMPLE_GRANT_PUBLIC_READ, SAMPLE_GRANT_FULL]}, "public-read"),
        (
            {"Owner": SAMPLE_OWNER, "Grants": [SAMPLE_GRANT_FULL, SAMPLE_GRANT_PUBLIC_READ, SAMPLE_GRANT_PUBLIC_WRITE]},
            "public-read-write",
        ),
        (
            {"Owner": SAMPLE_OWNER, "Grants": [SAMPLE_GRANT_FULL, SAMPLE_GRANT_PUBLIC_WRITE, SAMPLE_GRANT_PUBLIC_READ]},
            "public-read-write",
        ),
        (
            {"Owner": SAMPLE_OWNER, "Grants": [SAMPLE_GRANT_PUBLIC_READ, SAMPLE_GRANT_FULL, SAMPLE_GRANT_PUBLIC_WRITE]},
            "public-read-write",
        ),
        (
            {"Owner": SAMPLE_OWNER, "Grants": [SAMPLE_GRANT_PUBLIC_WRITE, SAMPLE_GRANT_FULL, SAMPLE_GRANT_PUBLIC_READ]},
            "public-read-write",
        ),
    ],
)
def test_s3_acl_to_name(acl, result):
    assert result == s3.s3_acl_to_name(acl)
