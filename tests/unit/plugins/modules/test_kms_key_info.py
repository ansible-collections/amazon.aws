# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.amazon.aws.plugins.modules import kms_key_info


class TestKeyMatchesFilter:
    def test_key_id_match(self):
        key = {"key_id": "abc123", "tags": {}, "aliases": []}
        assert kms_key_info.key_matches_filter(key, ("key-id", "abc123")) is True

    def test_key_id_no_match(self):
        key = {"key_id": "abc123", "tags": {}, "aliases": []}
        assert kms_key_info.key_matches_filter(key, ("key-id", "xyz789")) is False

    def test_tag_key_match(self):
        key = {"key_id": "abc123", "tags": {"Environment": "Test", "Owner": "Alice"}, "aliases": []}
        assert kms_key_info.key_matches_filter(key, ("tag-key", "Environment")) is True

    def test_tag_key_no_match(self):
        key = {"key_id": "abc123", "tags": {"Environment": "Test"}, "aliases": []}
        assert kms_key_info.key_matches_filter(key, ("tag-key", "Owner")) is False

    def test_tag_value_match(self):
        key = {"key_id": "abc123", "tags": {"Environment": "Test", "Owner": "Alice"}, "aliases": []}
        assert kms_key_info.key_matches_filter(key, ("tag-value", "Test")) is True

    def test_tag_value_no_match(self):
        key = {"key_id": "abc123", "tags": {"Environment": "Test"}, "aliases": []}
        assert kms_key_info.key_matches_filter(key, ("tag-value", "Production")) is False

    def test_alias_match(self):
        key = {"key_id": "abc123", "tags": {}, "aliases": ["mykey", "testkey"]}
        assert kms_key_info.key_matches_filter(key, ("alias", "mykey")) is True

    def test_alias_no_match(self):
        key = {"key_id": "abc123", "tags": {}, "aliases": ["mykey"]}
        assert kms_key_info.key_matches_filter(key, ("alias", "otherkey")) is False

    def test_tag_specific_match(self):
        key = {"key_id": "abc123", "tags": {"Environment": "Test", "Owner": "Alice"}, "aliases": []}
        assert kms_key_info.key_matches_filter(key, ("tag:Environment", "Test")) is True

    def test_tag_specific_no_match(self):
        key = {"key_id": "abc123", "tags": {"Environment": "Test"}, "aliases": []}
        assert kms_key_info.key_matches_filter(key, ("tag:Environment", "Production")) is False

    def test_tag_specific_key_missing(self):
        key = {"key_id": "abc123", "tags": {"Environment": "Test"}, "aliases": []}
        assert kms_key_info.key_matches_filter(key, ("tag:Owner", "Alice")) is False


class TestKeyMatchesFilters:
    def test_no_filters(self):
        key = {"key_id": "abc123", "tags": {}, "aliases": []}
        assert kms_key_info.key_matches_filters(key, {}) is True

    def test_none_filters(self):
        key = {"key_id": "abc123", "tags": {}, "aliases": []}
        assert kms_key_info.key_matches_filters(key, None) is True

    def test_single_filter_match(self):
        key = {"key_id": "abc123", "tags": {"Environment": "Test"}, "aliases": []}
        filters = {"key-id": "abc123"}
        assert kms_key_info.key_matches_filters(key, filters) is True

    def test_single_filter_no_match(self):
        key = {"key_id": "abc123", "tags": {"Environment": "Test"}, "aliases": []}
        filters = {"key-id": "xyz789"}
        assert kms_key_info.key_matches_filters(key, filters) is False

    def test_multiple_filters_all_match(self):
        key = {"key_id": "abc123", "tags": {"Environment": "Test", "Owner": "Alice"}, "aliases": ["mykey"]}
        filters = {"key-id": "abc123", "tag:Environment": "Test", "alias": "mykey"}
        assert kms_key_info.key_matches_filters(key, filters) is True

    def test_multiple_filters_partial_match(self):
        key = {"key_id": "abc123", "tags": {"Environment": "Test"}, "aliases": ["mykey"]}
        filters = {"key-id": "abc123", "tag:Environment": "Production"}
        assert kms_key_info.key_matches_filters(key, filters) is False

    def test_multiple_filters_no_match(self):
        key = {"key_id": "abc123", "tags": {"Environment": "Test"}, "aliases": []}
        filters = {"key-id": "xyz789", "alias": "otherkey"}
        assert kms_key_info.key_matches_filters(key, filters) is False
