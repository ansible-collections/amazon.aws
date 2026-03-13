# -*- coding: utf-8 -*-

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

__metaclass__ = type

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError

from ansible_collections.amazon.aws.plugins.module_utils.route53 import AnsibleRoute53Error
from ansible_collections.amazon.aws.plugins.module_utils.route53 import get_tags
from ansible_collections.amazon.aws.plugins.module_utils.route53 import manage_tags


class TestGetTags:
    def test_get_tags_happy_path(self):
        client = MagicMock()
        client.list_tags_for_resource.return_value = {
            "ResourceTagSet": {
                "Tags": [
                    {"Key": "Name", "Value": "test-zone"},
                    {"Key": "Environment", "Value": "testing"},
                ]
            }
        }
        resource_type = "hostedzone"
        resource_id = "Z123456"

        tags = get_tags(client, resource_type, resource_id)

        assert tags == {"Name": "test-zone", "Environment": "testing"}
        client.list_tags_for_resource.assert_called_once_with(ResourceType=resource_type, ResourceId=resource_id)

    def test_get_tags_no_tags(self):
        client = MagicMock()
        client.list_tags_for_resource.return_value = {"ResourceTagSet": {"Tags": []}}
        resource_type = "hostedzone"
        resource_id = "Z123456"

        tags = get_tags(client, resource_type, resource_id)

        assert tags == {}
        client.list_tags_for_resource.assert_called_once_with(ResourceType=resource_type, ResourceId=resource_id)

    def test_get_tags_not_found(self):
        client = MagicMock()
        error = ClientError({"Error": {"Code": "NoSuchHostedZone"}}, "ListTagsForResource")
        client.list_tags_for_resource.side_effect = error
        resource_type = "hostedzone"
        resource_id = "Z123456"

        tags = get_tags(client, resource_type, resource_id)

        assert tags == {}
        client.list_tags_for_resource.assert_called_once_with(ResourceType=resource_type, ResourceId=resource_id)

    def test_get_tags_other_client_error(self):
        client = MagicMock()
        error = ClientError({"Error": {"Code": "SomeOtherError"}}, "ListTagsForResource")
        client.list_tags_for_resource.side_effect = error
        resource_type = "hostedzone"
        resource_id = "Z123456"

        with pytest.raises(AnsibleRoute53Error) as e:
            get_tags(client, resource_type, resource_id)

        assert "list tags for resource" in str(e.value)
        client.list_tags_for_resource.assert_called_once_with(ResourceType=resource_type, ResourceId=resource_id)


class TestManageTags:
    @patch("ansible_collections.amazon.aws.plugins.module_utils.route53.get_tags")
    def test_manage_tags_no_new_tags(self, mock_get_tags):
        client = MagicMock()
        changed = manage_tags(client, "hostedzone", "Z123456", None, True, False)
        assert changed is False
        mock_get_tags.assert_not_called()

    @patch("ansible_collections.amazon.aws.plugins.module_utils.route53.get_tags")
    def test_manage_tags_no_change(self, mock_get_tags):
        client = MagicMock()
        mock_get_tags.return_value = {"Name": "test"}
        changed = manage_tags(client, "hostedzone", "Z123456", {"Name": "test"}, True, False)
        assert changed is False

    @patch("ansible_collections.amazon.aws.plugins.module_utils.route53._change_tags_for_resource")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.route53.get_tags")
    def test_manage_tags_add_tags(self, mock_get_tags, mock_change_tags):
        client = MagicMock()
        mock_get_tags.return_value = {"Name": "test"}
        new_tags = {"Name": "test", "Env": "dev"}
        changed = manage_tags(client, "hostedzone", "Z123456", new_tags, False, False)
        assert changed is True
        mock_change_tags.assert_called_once_with(
            client,
            "hostedzone",
            "Z123456",
            AddTags=[{"Key": "Env", "Value": "dev"}],
        )

    @patch("ansible_collections.amazon.aws.plugins.module_utils.route53._change_tags_for_resource")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.route53.get_tags")
    def test_manage_tags_remove_tags(self, mock_get_tags, mock_change_tags):
        client = MagicMock()
        mock_get_tags.return_value = {"Name": "test", "Env": "dev"}
        new_tags = {"Name": "test"}
        changed = manage_tags(client, "hostedzone", "Z123456", new_tags, True, False)
        assert changed is True
        mock_change_tags.assert_called_once_with(
            client,
            "hostedzone",
            "Z123456",
            RemoveTagKeys=["Env"],
        )

    @patch("ansible_collections.amazon.aws.plugins.module_utils.route53.get_tags")
    def test_manage_tags_check_mode(self, mock_get_tags):
        client = MagicMock()
        mock_get_tags.return_value = {}
        new_tags = {"Name": "test"}
        changed = manage_tags(client, "hostedzone", "Z123456", new_tags, True, True)
        assert changed is True

    @patch("ansible_collections.amazon.aws.plugins.module_utils.route53._change_tags_for_resource")
    @patch("ansible_collections.amazon.aws.plugins.module_utils.route53.get_tags")
    def test_manage_tags_complex_update(self, mock_get_tags, mock_change_tags):
        client = MagicMock()
        mock_get_tags.return_value = {"Name": "test", "Env": "old", "Keep": "me"}
        new_tags = {"Name": "test-updated", "Env": "new", "Add": "this"}

        changed = manage_tags(client, "hostedzone", "Z123456", new_tags, True, False)

        assert changed is True
        mock_change_tags.assert_called_once()
        call_args = mock_change_tags.call_args[0]
        call_kwargs = mock_change_tags.call_args[1]
        assert call_args[0] == client
        assert call_args[1] == "hostedzone"
        assert call_args[2] == "Z123456"
        assert call_kwargs["RemoveTagKeys"] == ["Keep"]
        add_tags_expected = [
            {"Key": "Name", "Value": "test-updated"},
            {"Key": "Env", "Value": "new"},
            {"Key": "Add", "Value": "this"},
        ]
        add_tags_actual_set = set(map(lambda x: tuple(sorted(x.items())), call_kwargs["AddTags"]))
        add_tags_expected_set = set(map(lambda x: tuple(sorted(x.items())), add_tags_expected))
        assert add_tags_actual_set == add_tags_expected_set
