# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3
from ansible_collections.amazon.aws.plugins.module_utils.rds import AnsibleRDSError
from ansible_collections.amazon.aws.plugins.module_utils.rds import ensure_tags
from ansible_collections.amazon.aws.plugins.module_utils.rds import get_tags

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_rds_tags.py requires the python modules 'boto3' and 'botocore'")

mod_tags = "ansible_collections.amazon.aws.plugins.module_utils._rds.tags"


class TestGetTags:
    @patch(mod_tags + ".list_tags_for_resource")
    def test_get_tags_returns_ansible_dict(self, m_list_tags):
        m_list_tags.return_value = [
            {"Key": "Name", "Value": "my-db"},
            {"Key": "Environment", "Value": "production"},
        ]
        client = MagicMock()
        module = MagicMock()

        result = get_tags(client, module, "arn:aws:rds:us-east-1:123456789012:db:my-db")

        assert result == {"Name": "my-db", "Environment": "production"}
        m_list_tags.assert_called_once_with(client, "arn:aws:rds:us-east-1:123456789012:db:my-db")

    @patch(mod_tags + ".list_tags_for_resource")
    def test_get_tags_empty(self, m_list_tags):
        m_list_tags.return_value = []
        client = MagicMock()
        module = MagicMock()

        result = get_tags(client, module, "arn:aws:rds:us-east-1:123456789012:db:my-db")

        assert result == {}

    @patch(mod_tags + ".list_tags_for_resource")
    def test_get_tags_error_fails_module(self, m_list_tags):
        m_list_tags.side_effect = AnsibleRDSError(message="API error")
        client = MagicMock()
        module = MagicMock()
        arn = "arn:aws:rds:us-east-1:123456789012:db:my-db"

        # fail_json_aws is mocked so it doesn't exit; the function then hits
        # UnboundLocalError on `tags` — expected since real fail_json_aws exits
        with pytest.raises(UnboundLocalError):
            get_tags(client, module, arn)

        module.fail_json_aws.assert_called_once()
        assert f"Unable to list tags for resource {arn}" in module.fail_json_aws.call_args[1]["msg"]


class TestEnsureTags:
    @patch(mod_tags + ".call_method")
    def test_ensure_tags_none_tags_no_change(self, m_call_method):
        client = MagicMock()
        module = MagicMock()

        result = ensure_tags(
            client, module, "arn:aws:rds:us-east-1:123456789012:db:my-db", {"Name": "test"}, None, True
        )

        assert result is False
        m_call_method.assert_not_called()

    @patch(mod_tags + ".call_method")
    def test_ensure_tags_no_change_needed(self, m_call_method):
        client = MagicMock()
        module = MagicMock()
        existing = {"Name": "my-db", "Env": "prod"}
        desired = {"Name": "my-db", "Env": "prod"}

        result = ensure_tags(client, module, "arn:aws:rds:us-east-1:123456789012:db:my-db", existing, desired, True)

        assert result is False
        m_call_method.assert_not_called()

    @patch(mod_tags + ".call_method")
    def test_ensure_tags_add_tags(self, m_call_method):
        client = MagicMock()
        module = MagicMock()
        existing = {"Name": "my-db"}
        desired = {"Name": "my-db", "Env": "prod"}
        arn = "arn:aws:rds:us-east-1:123456789012:db:my-db"

        result = ensure_tags(client, module, arn, existing, desired, False)

        assert result is True
        m_call_method.assert_called_once_with(
            client,
            module,
            method_name="add_tags_to_resource",
            parameters={"ResourceName": arn, "Tags": [{"Key": "Env", "Value": "prod"}]},
        )

    @patch(mod_tags + ".call_method")
    def test_ensure_tags_remove_tags_with_purge(self, m_call_method):
        client = MagicMock()
        module = MagicMock()
        existing = {"Name": "my-db", "Env": "prod", "Temp": "yes"}
        desired = {"Name": "my-db"}
        arn = "arn:aws:rds:us-east-1:123456789012:db:my-db"

        result = ensure_tags(client, module, arn, existing, desired, True)

        assert result is True
        m_call_method.assert_called_once_with(
            client,
            module,
            method_name="remove_tags_from_resource",
            parameters={"ResourceName": arn, "TagKeys": ["Env", "Temp"]},
        )

    @patch(mod_tags + ".call_method")
    def test_ensure_tags_no_purge_keeps_extra(self, m_call_method):
        client = MagicMock()
        module = MagicMock()
        existing = {"Name": "my-db", "Env": "prod"}
        desired = {"Name": "my-db"}
        arn = "arn:aws:rds:us-east-1:123456789012:db:my-db"

        result = ensure_tags(client, module, arn, existing, desired, False)

        assert result is False
        m_call_method.assert_not_called()

    @patch(mod_tags + ".call_method")
    def test_ensure_tags_add_and_remove(self, m_call_method):
        client = MagicMock()
        module = MagicMock()
        existing = {"Name": "my-db", "OldTag": "remove-me"}
        desired = {"Name": "my-db", "NewTag": "add-me"}
        arn = "arn:aws:rds:us-east-1:123456789012:db:my-db"

        result = ensure_tags(client, module, arn, existing, desired, True)

        assert result is True
        assert m_call_method.call_count == 2
        add_call = call(
            client,
            module,
            method_name="add_tags_to_resource",
            parameters={"ResourceName": arn, "Tags": [{"Key": "NewTag", "Value": "add-me"}]},
        )
        remove_call = call(
            client,
            module,
            method_name="remove_tags_from_resource",
            parameters={"ResourceName": arn, "TagKeys": ["OldTag"]},
        )
        m_call_method.assert_has_calls([add_call, remove_call], any_order=True)

    @patch(mod_tags + ".call_method")
    def test_ensure_tags_empty_desired_with_purge(self, m_call_method):
        client = MagicMock()
        module = MagicMock()
        existing = {"Name": "my-db", "Env": "prod"}
        desired = {}
        arn = "arn:aws:rds:us-east-1:123456789012:db:my-db"

        result = ensure_tags(client, module, arn, existing, desired, True)

        assert result is True
        m_call_method.assert_called_once()
        call_kwargs = m_call_method.call_args[1]
        assert call_kwargs["method_name"] == "remove_tags_from_resource"
        assert call_kwargs["parameters"]["ResourceName"] == arn
        assert sorted(call_kwargs["parameters"]["TagKeys"]) == ["Env", "Name"]

    @patch(mod_tags + ".call_method")
    def test_ensure_tags_update_value(self, m_call_method):
        client = MagicMock()
        module = MagicMock()
        existing = {"Name": "old-name"}
        desired = {"Name": "new-name"}
        arn = "arn:aws:rds:us-east-1:123456789012:db:my-db"

        result = ensure_tags(client, module, arn, existing, desired, True)

        assert result is True
        m_call_method.assert_called_once_with(
            client,
            module,
            method_name="add_tags_to_resource",
            parameters={"ResourceName": arn, "Tags": [{"Key": "Name", "Value": "new-name"}]},
        )
