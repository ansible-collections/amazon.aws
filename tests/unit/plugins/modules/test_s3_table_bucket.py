# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.modules import s3_table_bucket

module_name = "ansible_collections.amazon.aws.plugins.modules.s3_table_bucket"

EXISTING_BUCKET = {
    "arn": "arn:aws:s3tables:us-east-1:123456789012:bucket/my-bucket",
    "name": "my-bucket",
    "ownerAccountId": "123456789012",
    "createdAt": "2025-01-01T12:00:00+00:00",
    "tableBucketId": "abcd1234-ab12-cd34-ef56-abcdef123456",
    "type": "customer",
}


@pytest.fixture(name="ansible_module")
def fixture_ansible_module():
    module = MagicMock()
    module.params = {}
    module.check_mode = False
    module.exit_json = MagicMock(side_effect=SystemExit(0))
    module.fail_json = MagicMock(side_effect=SystemExit(1))
    return module


class TestValidateEncryptionConfiguration:
    def test_none(self, ansible_module):
        s3_table_bucket._validate_encryption_configuration(ansible_module, None)
        ansible_module.fail_json.assert_not_called()

    def test_aes256_does_not_require_kms_key(self, ansible_module):
        s3_table_bucket._validate_encryption_configuration(ansible_module, {"sse_algorithm": "AES256"})
        ansible_module.fail_json.assert_not_called()

    def test_kms_without_key_fails(self, ansible_module):
        with pytest.raises(SystemExit):
            s3_table_bucket._validate_encryption_configuration(ansible_module, {"sse_algorithm": "aws:kms"})
        ansible_module.fail_json.assert_called_once()

    def test_kms_with_key_passes(self, ansible_module):
        s3_table_bucket._validate_encryption_configuration(
            ansible_module, {"sse_algorithm": "aws:kms", "kms_key_arn": "arn:aws:kms:us-east-1:123456789012:key/abc"}
        )
        ansible_module.fail_json.assert_not_called()


class TestDesiredEncryptionConfiguration:
    def test_aes256(self):
        assert s3_table_bucket._desired_encryption_configuration({"sse_algorithm": "AES256"}) == {
            "sseAlgorithm": "AES256"
        }

    def test_kms(self):
        assert s3_table_bucket._desired_encryption_configuration(
            {"sse_algorithm": "aws:kms", "kms_key_arn": "arn:aws:kms:us-east-1:123456789012:key/abc"}
        ) == {"sseAlgorithm": "aws:kms", "kmsKeyArn": "arn:aws:kms:us-east-1:123456789012:key/abc"}


class TestEncryptionNeedsUpdate:
    def test_no_current_needs_update(self):
        assert s3_table_bucket._encryption_needs_update(None, {"sseAlgorithm": "AES256"}) is True

    def test_matching_does_not_need_update(self):
        current = {"sseAlgorithm": "AES256"}
        assert s3_table_bucket._encryption_needs_update(current, {"sseAlgorithm": "AES256"}) is False

    def test_different_algorithm_needs_update(self):
        current = {"sseAlgorithm": "AES256"}
        assert s3_table_bucket._encryption_needs_update(current, {"sseAlgorithm": "aws:kms"}) is True

    def test_different_kms_key_needs_update(self):
        current = {"sseAlgorithm": "aws:kms", "kmsKeyArn": "arn:aws:kms:us-east-1:123456789012:key/old"}
        desired = {"sseAlgorithm": "aws:kms", "kmsKeyArn": "arn:aws:kms:us-east-1:123456789012:key/new"}
        assert s3_table_bucket._encryption_needs_update(current, desired) is True


class TestFormatTableBucket:
    def test_without_tags_or_encryption(self):
        result = s3_table_bucket._format_table_bucket(EXISTING_BUCKET)
        assert "tags" not in result
        assert "encryption_configuration" not in result
        assert result["name"] == "my-bucket"

    def test_with_tags_and_encryption(self):
        result = s3_table_bucket._format_table_bucket(
            EXISTING_BUCKET, tags={"Environment": "Test"}, encryption_configuration={"sseAlgorithm": "AES256"}
        )
        assert result["tags"] == {"Environment": "Test"}
        assert result["encryption_configuration"] == {"sse_algorithm": "AES256"}


class TestEnsurePresent:
    @patch(module_name + ".create_table_bucket")
    def test_create_new_bucket(self, m_create_table_bucket, ansible_module):
        ansible_module.params = {
            "table_bucket_name": "my-bucket",
            "tags": None,
            "purge_tags": True,
            "encryption_configuration": None,
        }
        client = MagicMock()
        m_create_table_bucket.return_value = EXISTING_BUCKET["arn"]
        client.get_table_bucket.return_value = EXISTING_BUCKET

        with pytest.raises(SystemExit):
            s3_table_bucket.ensure_present(client, ansible_module, None)

        m_create_table_bucket.assert_called_once_with(client, "my-bucket")
        ansible_module.exit_json.assert_called_once_with(
            changed=True,
            table_bucket=s3_table_bucket._format_table_bucket(EXISTING_BUCKET),
            msg="Table bucket updated.",
        )

    def test_create_new_bucket_check_mode(self, ansible_module):
        ansible_module.params = {
            "table_bucket_name": "my-bucket",
            "tags": None,
            "purge_tags": True,
            "encryption_configuration": None,
        }
        ansible_module.check_mode = True
        client = MagicMock()

        with pytest.raises(SystemExit):
            s3_table_bucket.ensure_present(client, ansible_module, None)

        ansible_module.exit_json.assert_called_once_with(
            changed=True, msg="Check mode: would have created table bucket 'my-bucket'."
        )
        client.create_table_bucket.assert_not_called()

    def test_no_changes_when_up_to_date(self, ansible_module):
        ansible_module.params = {
            "table_bucket_name": "my-bucket",
            "tags": None,
            "purge_tags": True,
            "encryption_configuration": None,
        }
        client = MagicMock()
        client.get_table_bucket.return_value = EXISTING_BUCKET

        with pytest.raises(SystemExit):
            s3_table_bucket.ensure_present(client, ansible_module, EXISTING_BUCKET)

        ansible_module.exit_json.assert_called_once_with(
            changed=False,
            table_bucket=s3_table_bucket._format_table_bucket(EXISTING_BUCKET),
            msg="Table bucket is up to date.",
        )

    @patch(module_name + ".compare_aws_tags")
    @patch(module_name + ".tag_resource")
    @patch(module_name + ".untag_resource")
    def test_tags_updated(self, m_untag_resource, m_tag_resource, m_compare_aws_tags, ansible_module):
        ansible_module.params = {
            "table_bucket_name": "my-bucket",
            "tags": {"Environment": "Prod"},
            "purge_tags": True,
            "encryption_configuration": None,
        }
        client = MagicMock()
        client.get_table_bucket.return_value = EXISTING_BUCKET
        client.list_tags_for_resource.return_value = {"tags": {"Environment": "Test"}}
        m_compare_aws_tags.return_value = ({"Environment": "Prod"}, ["Stage"])

        with pytest.raises(SystemExit):
            s3_table_bucket.ensure_present(client, ansible_module, EXISTING_BUCKET)

        m_untag_resource.assert_called_once_with(client, EXISTING_BUCKET["arn"], ["Stage"])
        m_tag_resource.assert_called_once_with(client, EXISTING_BUCKET["arn"], {"Environment": "Prod"})
        exit_kwargs = ansible_module.exit_json.call_args.kwargs
        assert exit_kwargs["changed"] is True
        assert exit_kwargs["msg"] == "Table bucket updated."

    @patch(module_name + ".get_table_bucket_encryption")
    @patch(module_name + ".put_table_bucket_encryption")
    def test_encryption_updated(self, m_put_table_bucket_encryption, m_get_table_bucket_encryption, ansible_module):
        ansible_module.params = {
            "table_bucket_name": "my-bucket",
            "tags": None,
            "purge_tags": True,
            "encryption_configuration": {"sse_algorithm": "AES256"},
        }
        client = MagicMock()
        client.get_table_bucket.return_value = EXISTING_BUCKET
        m_get_table_bucket_encryption.return_value = None

        with pytest.raises(SystemExit):
            s3_table_bucket.ensure_present(client, ansible_module, EXISTING_BUCKET)

        m_put_table_bucket_encryption.assert_called_once_with(
            client, EXISTING_BUCKET["arn"], {"sseAlgorithm": "AES256"}
        )


class TestEnsureAbsent:
    def test_already_absent(self, ansible_module):
        ansible_module.params = {"table_bucket_name": "my-bucket"}
        client = MagicMock()

        with pytest.raises(SystemExit):
            s3_table_bucket.ensure_absent(client, ansible_module, None)

        ansible_module.exit_json.assert_called_once_with(
            changed=False, table_bucket={}, msg="Table bucket 'my-bucket' does not exist."
        )
        client.delete_table_bucket.assert_not_called()

    def test_delete_check_mode(self, ansible_module):
        ansible_module.params = {"table_bucket_name": "my-bucket"}
        ansible_module.check_mode = True
        client = MagicMock()

        with pytest.raises(SystemExit):
            s3_table_bucket.ensure_absent(client, ansible_module, EXISTING_BUCKET)

        ansible_module.exit_json.assert_called_once_with(
            changed=True, msg="Check mode: would have deleted table bucket 'my-bucket'."
        )
        client.delete_table_bucket.assert_not_called()

    @patch(module_name + ".delete_table_bucket")
    def test_delete(self, m_delete_table_bucket, ansible_module):
        ansible_module.params = {"table_bucket_name": "my-bucket"}
        client = MagicMock()

        with pytest.raises(SystemExit):
            s3_table_bucket.ensure_absent(client, ansible_module, EXISTING_BUCKET)

        m_delete_table_bucket.assert_called_once_with(client, EXISTING_BUCKET["arn"])
        ansible_module.exit_json.assert_called_once_with(
            changed=True, table_bucket={}, msg="Table bucket 'my-bucket' deleted."
        )
