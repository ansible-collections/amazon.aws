# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.modules import s3_table_bucket_info

module_name = "ansible_collections.amazon.aws.plugins.modules.s3_table_bucket_info"

EXISTING_BUCKET = {
    "arn": "arn:aws:s3tables:us-east-1:123456789012:bucket/my-bucket",
    "name": "my-bucket",
    "ownerAccountId": "123456789012",
    "createdAt": "2025-01-01T12:00:00+00:00",
    "tableBucketId": "abcd1234-ab12-cd34-ef56-abcdef123456",
    "type": "customer",
}

EXISTING_TABLE = {
    "namespace": ["my_namespace"],
    "name": "my_table",
    "type": "customer",
    "tableARN": "arn:aws:s3tables:us-east-1:123456789012:bucket/my-bucket/table/abcd1234",
}


@pytest.fixture(name="ansible_module")
def fixture_ansible_module():
    module = MagicMock()
    module.params = {}
    module.check_mode = False
    module.exit_json = MagicMock(side_effect=SystemExit(0))
    module.fail_json = MagicMock(side_effect=SystemExit(1))
    return module


class TestDescribeTableBucket:
    @patch(module_name + ".list_table_summaries")
    @patch(module_name + ".get_table_bucket")
    def test_describe_table_bucket(self, m_get_table_bucket, m_list_table_summaries):
        client = MagicMock()
        m_get_table_bucket.return_value = EXISTING_BUCKET
        m_list_table_summaries.return_value = [EXISTING_TABLE]

        result = s3_table_bucket_info._describe_table_bucket(client, EXISTING_BUCKET["arn"])

        assert result["name"] == "my-bucket"
        assert result["tables"] == [
            {
                "namespace": ["my_namespace"],
                "name": "my_table",
                "type": "customer",
                "table_arn": "arn:aws:s3tables:us-east-1:123456789012:bucket/my-bucket/table/abcd1234",
            }
        ]
        m_get_table_bucket.assert_called_once_with(client, EXISTING_BUCKET["arn"])
        m_list_table_summaries.assert_called_once_with(client, EXISTING_BUCKET["arn"])


class TestMain:
    @patch(module_name + ".AnsibleAWSModule")
    @patch(module_name + ".find_table_bucket")
    @patch(module_name + ".get_table_bucket")
    @patch(module_name + ".list_table_summaries")
    def test_found_bucket(
        self, m_list_table_summaries, m_get_table_bucket, m_find_table_bucket, m_ansible_aws_module, ansible_module
    ):
        m_ansible_aws_module.return_value = ansible_module
        ansible_module.params = {"table_bucket_name": "my-bucket"}
        m_find_table_bucket.return_value = EXISTING_BUCKET
        m_get_table_bucket.return_value = EXISTING_BUCKET
        m_list_table_summaries.return_value = []

        with pytest.raises(SystemExit):
            s3_table_bucket_info.main()

        exit_kwargs = ansible_module.exit_json.call_args.kwargs
        assert exit_kwargs["changed"] is False
        assert len(exit_kwargs["table_buckets"]) == 1
        assert exit_kwargs["table_buckets"][0]["name"] == "my-bucket"

    @patch(module_name + ".AnsibleAWSModule")
    @patch(module_name + ".find_table_bucket")
    def test_bucket_not_found(self, m_find_table_bucket, m_ansible_aws_module, ansible_module):
        m_ansible_aws_module.return_value = ansible_module
        ansible_module.params = {"table_bucket_name": "my-bucket"}
        m_find_table_bucket.return_value = None

        with pytest.raises(SystemExit):
            s3_table_bucket_info.main()

        ansible_module.exit_json.assert_called_once_with(changed=False, table_buckets=[])
