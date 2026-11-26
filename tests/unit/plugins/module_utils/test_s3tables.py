# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock

try:
    import botocore
except ImportError:
    pass

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3
from ansible_collections.amazon.aws.plugins.module_utils.s3tables import AnsibleS3TablesError
from ansible_collections.amazon.aws.plugins.module_utils.s3tables import find_table_bucket
from ansible_collections.amazon.aws.plugins.module_utils.s3tables import get_table_bucket
from ansible_collections.amazon.aws.plugins.module_utils.s3tables import get_table_bucket_encryption
from ansible_collections.amazon.aws.plugins.module_utils.s3tables import list_table_buckets
from ansible_collections.amazon.aws.plugins.module_utils.s3tables import list_table_summaries
from ansible_collections.amazon.aws.plugins.module_utils.s3tables import list_tags_for_resource

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_s3tables.py requires the python modules 'boto3' and 'botocore'")


def _not_found_error():
    return botocore.exceptions.ClientError(
        {"Error": {"Code": "NotFoundException", "Message": "The table bucket does not exist."}},
        "GetTableBucket",
    )


class TestListTableBuckets:
    def test_list_table_buckets(self):
        client = MagicMock()
        paginator = MagicMock()
        client.get_paginator.return_value = paginator
        paginator.paginate.return_value.build_full_result.return_value = {
            "tableBuckets": [{"arn": "arn:aws:s3tables:us-east-1:123456789012:bucket/my-bucket", "name": "my-bucket"}]
        }

        result = list_table_buckets(client, prefix="my-bucket")

        assert result == [{"arn": "arn:aws:s3tables:us-east-1:123456789012:bucket/my-bucket", "name": "my-bucket"}]
        client.get_paginator.assert_called_once_with("list_table_buckets")
        paginator.paginate.assert_called_once_with(prefix="my-bucket")


class TestFindTableBucket:
    def test_find_table_bucket_match(self):
        client = MagicMock()
        paginator = MagicMock()
        client.get_paginator.return_value = paginator
        paginator.paginate.return_value.build_full_result.return_value = {
            "tableBuckets": [
                {"arn": "arn:aws:s3tables:us-east-1:123456789012:bucket/other-bucket", "name": "other-bucket"},
                {"arn": "arn:aws:s3tables:us-east-1:123456789012:bucket/my-bucket", "name": "my-bucket"},
            ]
        }

        result = find_table_bucket(client, "my-bucket")

        assert result == {"arn": "arn:aws:s3tables:us-east-1:123456789012:bucket/my-bucket", "name": "my-bucket"}

    def test_find_table_bucket_no_match(self):
        client = MagicMock()
        paginator = MagicMock()
        client.get_paginator.return_value = paginator
        paginator.paginate.return_value.build_full_result.return_value = {
            "tableBuckets": [
                {"arn": "arn:aws:s3tables:us-east-1:123456789012:bucket/other-bucket", "name": "other-bucket"}
            ]
        }

        assert find_table_bucket(client, "my-bucket") is None


class TestGetTableBucket:
    def test_get_table_bucket(self):
        client = MagicMock()
        client.get_table_bucket.return_value = {"arn": "arn:aws:s3tables:us-east-1:123456789012:bucket/my-bucket"}

        result = get_table_bucket(client, "arn:aws:s3tables:us-east-1:123456789012:bucket/my-bucket")

        assert result == {"arn": "arn:aws:s3tables:us-east-1:123456789012:bucket/my-bucket"}
        client.get_table_bucket.assert_called_once_with(
            tableBucketARN="arn:aws:s3tables:us-east-1:123456789012:bucket/my-bucket"
        )

    def test_get_table_bucket_not_found_returns_default(self):
        client = MagicMock()
        client.get_table_bucket.side_effect = _not_found_error()

        assert get_table_bucket(client, "arn:aws:s3tables:us-east-1:123456789012:bucket/missing") is None

    def test_get_table_bucket_other_error_raises(self):
        client = MagicMock()
        client.get_table_bucket.side_effect = botocore.exceptions.ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied."}}, "GetTableBucket"
        )

        with pytest.raises(AnsibleS3TablesError):
            get_table_bucket(client, "arn:aws:s3tables:us-east-1:123456789012:bucket/my-bucket")


class TestListTagsForResource:
    def test_list_tags_for_resource_not_found_returns_default(self):
        client = MagicMock()
        client.list_tags_for_resource.side_effect = _not_found_error()

        assert list_tags_for_resource(client, "arn:aws:s3tables:us-east-1:123456789012:bucket/missing") == {}


class TestGetTableBucketEncryption:
    def test_get_table_bucket_encryption(self):
        client = MagicMock()
        client.get_table_bucket_encryption.return_value = {"encryptionConfiguration": {"sseAlgorithm": "AES256"}}

        result = get_table_bucket_encryption(client, "arn:aws:s3tables:us-east-1:123456789012:bucket/my-bucket")

        assert result == {"sseAlgorithm": "AES256"}

    def test_get_table_bucket_encryption_not_found_returns_default(self):
        client = MagicMock()
        client.get_table_bucket_encryption.side_effect = _not_found_error()

        assert get_table_bucket_encryption(client, "arn:aws:s3tables:us-east-1:123456789012:bucket/missing") is None


class TestListTableSummaries:
    def test_list_table_summaries(self):
        client = MagicMock()
        paginator = MagicMock()
        client.get_paginator.return_value = paginator
        paginator.paginate.return_value.build_full_result.return_value = {
            "tables": [{"name": "my-table", "namespace": ["my_namespace"]}]
        }

        result = list_table_summaries(client, "arn:aws:s3tables:us-east-1:123456789012:bucket/my-bucket")

        assert result == [{"name": "my-table", "namespace": ["my_namespace"]}]
        client.get_paginator.assert_called_once_with("list_tables")
        paginator.paginate.assert_called_once_with(
            tableBucketARN="arn:aws:s3tables:us-east-1:123456789012:bucket/my-bucket"
        )
