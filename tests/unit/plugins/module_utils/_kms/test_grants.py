# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.amazon.aws.plugins.module_utils._kms.grants import compare_grants
from ansible_collections.amazon.aws.plugins.module_utils._kms.grants import different_grant


class TestDifferentGrant:
    def test_same_grant(self):
        grant = {
            "name": "test",
            "grantee_principal": "arn:aws:iam::123456789012:role/test",
            "operations": ["Decrypt", "Encrypt"],
        }
        assert different_grant(grant, grant) is False

    def test_different_grantee(self):
        grant1 = {"name": "test", "grantee_principal": "arn:aws:iam::123456789012:role/test1"}
        grant2 = {"name": "test", "grantee_principal": "arn:aws:iam::123456789012:role/test2"}
        assert different_grant(grant1, grant2) is True

    def test_different_operations(self):
        grant1 = {"name": "test", "grantee_principal": "arn:aws:iam::123456789012:role/test", "operations": ["Decrypt"]}
        grant2 = {
            "name": "test",
            "grantee_principal": "arn:aws:iam::123456789012:role/test",
            "operations": ["Decrypt", "Encrypt"],
        }
        assert different_grant(grant1, grant2) is True

    def test_operations_order_irrelevant(self):
        grant1 = {
            "name": "test",
            "grantee_principal": "arn:aws:iam::123456789012:role/test",
            "operations": ["Decrypt", "Encrypt"],
        }
        grant2 = {
            "name": "test",
            "grantee_principal": "arn:aws:iam::123456789012:role/test",
            "operations": ["Encrypt", "Decrypt"],
        }
        assert different_grant(grant1, grant2) is False

    def test_different_retiring_principal(self):
        grant1 = {
            "name": "test",
            "grantee_principal": "arn:aws:iam::123456789012:role/test",
            "retiring_principal": "arn:aws:iam::123456789012:role/retire1",
        }
        grant2 = {
            "name": "test",
            "grantee_principal": "arn:aws:iam::123456789012:role/test",
            "retiring_principal": "arn:aws:iam::123456789012:role/retire2",
        }
        assert different_grant(grant1, grant2) is True

    def test_different_constraints(self):
        grant1 = {
            "name": "test",
            "grantee_principal": "arn:aws:iam::123456789012:role/test",
            "constraints": {"encryption_context_equals": {"Department": "Finance"}},
        }
        grant2 = {
            "name": "test",
            "grantee_principal": "arn:aws:iam::123456789012:role/test",
            "constraints": {"encryption_context_equals": {"Department": "Engineering"}},
        }
        assert different_grant(grant1, grant2) is True

    def test_same_constraints(self):
        grant1 = {
            "name": "test",
            "grantee_principal": "arn:aws:iam::123456789012:role/test",
            "constraints": {"encryption_context_equals": {"Department": "Finance"}},
        }
        grant2 = {
            "name": "test",
            "grantee_principal": "arn:aws:iam::123456789012:role/test",
            "constraints": {"encryption_context_equals": {"Department": "Finance"}},
        }
        assert different_grant(grant1, grant2) is False

    def test_different_retiring_principal(self):
        grant1 = {
            "name": "test",
            "grantee_principal": "arn:aws:iam::123456789012:role/test",
            "retiring_principal": "arn:aws:iam::123456789012:role/retire1",
        }
        grant2 = {
            "name": "test",
            "grantee_principal": "arn:aws:iam::123456789012:role/test",
            "retiring_principal": "arn:aws:iam::123456789012:role/retire2",
        }
        assert different_grant(grant1, grant2) is True

    def test_different_constraints(self):
        grant1 = {
            "name": "test",
            "grantee_principal": "arn:aws:iam::123456789012:role/test",
            "constraints": {"encryption_context_equals": {"Department": "Finance"}},
        }
        grant2 = {
            "name": "test",
            "grantee_principal": "arn:aws:iam::123456789012:role/test",
            "constraints": {"encryption_context_equals": {"Department": "Engineering"}},
        }
        assert different_grant(grant1, grant2) is True

    def test_same_constraints(self):
        grant1 = {
            "name": "test",
            "grantee_principal": "arn:aws:iam::123456789012:role/test",
            "constraints": {"encryption_context_equals": {"Department": "Finance"}},
        }
        grant2 = {
            "name": "test",
            "grantee_principal": "arn:aws:iam::123456789012:role/test",
            "constraints": {"encryption_context_equals": {"Department": "Finance"}},
        }
        assert different_grant(grant1, grant2) is False


class TestCompareGrants:
    def test_no_changes_needed(self):
        existing = [{"name": "grant1", "grantee_principal": "arn:aws:iam::123456789012:role/test"}]
        desired = [{"name": "grant1", "grantee_principal": "arn:aws:iam::123456789012:role/test"}]
        to_add, to_remove = compare_grants(existing, desired)
        assert to_add == []
        assert to_remove == []

    def test_add_new_grant(self):
        existing = []
        desired = [{"name": "grant1", "grantee_principal": "arn:aws:iam::123456789012:role/test"}]
        to_add, to_remove = compare_grants(existing, desired)
        assert len(to_add) == 1
        assert to_add[0]["name"] == "grant1"
        assert to_remove == []

    def test_remove_grant_with_purge(self):
        existing = [{"name": "grant1", "grantee_principal": "arn:aws:iam::123456789012:role/test"}]
        desired = []
        to_add, to_remove = compare_grants(existing, desired, purge_grants=True)
        assert to_add == []
        assert len(to_remove) == 1
        assert to_remove[0]["name"] == "grant1"

    def test_keep_grant_without_purge(self):
        existing = [{"name": "grant1", "grantee_principal": "arn:aws:iam::123456789012:role/test"}]
        desired = []
        to_add, to_remove = compare_grants(existing, desired, purge_grants=False)
        assert to_add == []
        assert to_remove == []

    def test_modify_grant(self):
        existing = [{"name": "grant1", "grantee_principal": "arn:aws:iam::123456789012:role/test1"}]
        desired = [{"name": "grant1", "grantee_principal": "arn:aws:iam::123456789012:role/test2"}]
        to_add, to_remove = compare_grants(existing, desired)
        # When a grant changes, we remove the old and add the new
        assert len(to_add) == 1
        assert to_add[0]["grantee_principal"] == "arn:aws:iam::123456789012:role/test2"
        assert len(to_remove) == 1
        assert to_remove[0]["grantee_principal"] == "arn:aws:iam::123456789012:role/test1"
