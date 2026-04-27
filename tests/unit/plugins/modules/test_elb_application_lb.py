# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.modules import elb_application_lb


class TestExitIfCheckMode:
    """Tests for _exit_if_check_mode helper function"""

    def test_exits_in_check_mode(self):
        """Should exit with changed=True when in check mode"""
        alb_obj = MagicMock()
        alb_obj.check_mode = True

        elb_application_lb._exit_if_check_mode(alb_obj, action="created")

        alb_obj.exit_json.assert_called_once_with(
            changed=True, msg="Would have created ALB if not in check mode."
        )

    def test_does_not_exit_when_not_check_mode(self):
        """Should not exit when not in check mode"""
        alb_obj = MagicMock()
        alb_obj.check_mode = False

        # Should not raise or exit
        elb_application_lb._exit_if_check_mode(alb_obj, action="created")

        alb_obj.exit_json.assert_not_called()

    def test_default_action_is_updated(self):
        """Should use 'updated' as default action"""
        alb_obj = MagicMock()
        alb_obj.check_mode = True

        elb_application_lb._exit_if_check_mode(alb_obj)

        alb_obj.exit_json.assert_called_once_with(
            changed=True, msg="Would have updated ALB if not in check mode."
        )

    def test_custom_action_message(self):
        """Should use custom action in message"""
        alb_obj = MagicMock()
        alb_obj.check_mode = True

        elb_application_lb._exit_if_check_mode(alb_obj, action="deleted")

        alb_obj.exit_json.assert_called_once_with(
            changed=True, msg="Would have deleted ALB if not in check mode."
        )


class TestUpdateAlbTags:
    """Tests for _update_alb_tags helper function"""

    def test_no_tags_specified(self):
        """Should return early when tags parameter is None"""
        alb_obj = MagicMock()
        alb_obj.tags = None

        elb_application_lb._update_alb_tags(alb_obj)

        # Nothing should be called
        alb_obj.delete_tags.assert_not_called()
        alb_obj.modify_tags.assert_not_called()

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.compare_aws_tags")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.boto3_tag_list_to_ansible_dict")
    def test_no_tag_changes_needed(self, mock_boto3_to_dict, mock_compare):
        """Should return early when no tag changes needed"""
        alb_obj = MagicMock()
        alb_obj.tags = [{"Key": "Name", "Value": "test"}]
        alb_obj.elb = {"tags": [{"Key": "Name", "Value": "test"}]}

        mock_boto3_to_dict.return_value = {"Name": "test"}
        mock_compare.return_value = (False, [])

        elb_application_lb._update_alb_tags(alb_obj)

        alb_obj.delete_tags.assert_not_called()
        alb_obj.modify_tags.assert_not_called()

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.compare_aws_tags")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.boto3_tag_list_to_ansible_dict")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._exit_if_check_mode")
    def test_exits_in_check_mode_when_changes_needed(self, mock_exit, mock_boto3_to_dict, mock_compare):
        """Should exit in check mode when tag changes needed"""
        alb_obj = MagicMock()
        alb_obj.tags = [{"Key": "Name", "Value": "new"}]
        alb_obj.elb = {"tags": [{"Key": "Name", "Value": "old"}]}

        mock_boto3_to_dict.return_value = {"Name": "test"}
        mock_compare.return_value = (True, [])

        elb_application_lb._update_alb_tags(alb_obj)

        mock_exit.assert_called_once_with(alb_obj)

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.compare_aws_tags")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.boto3_tag_list_to_ansible_dict")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._exit_if_check_mode")
    def test_deletes_tags_when_needed(self, mock_exit, mock_boto3_to_dict, mock_compare):
        """Should delete tags when tags_to_delete is not empty"""
        alb_obj = MagicMock()
        alb_obj.check_mode = False
        alb_obj.tags = []
        alb_obj.elb = {"tags": [{"Key": "OldTag", "Value": "value"}]}

        mock_boto3_to_dict.return_value = {}
        mock_compare.return_value = (False, ["OldTag"])

        elb_application_lb._update_alb_tags(alb_obj)

        alb_obj.delete_tags.assert_called_once_with(["OldTag"])

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.compare_aws_tags")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.boto3_tag_list_to_ansible_dict")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._exit_if_check_mode")
    def test_modifies_tags_when_needed(self, mock_exit, mock_boto3_to_dict, mock_compare):
        """Should modify tags when tags_need_modify is True"""
        alb_obj = MagicMock()
        alb_obj.check_mode = False
        alb_obj.tags = [{"Key": "Name", "Value": "new"}]
        alb_obj.elb = {"tags": [{"Key": "Name", "Value": "old"}]}

        mock_boto3_to_dict.return_value = {}
        mock_compare.return_value = (True, [])

        elb_application_lb._update_alb_tags(alb_obj)

        alb_obj.modify_tags.assert_called_once()

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.compare_aws_tags")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.boto3_tag_list_to_ansible_dict")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._exit_if_check_mode")
    def test_both_delete_and_modify(self, mock_exit, mock_boto3_to_dict, mock_compare):
        """Should both delete and modify tags when needed"""
        alb_obj = MagicMock()
        alb_obj.check_mode = False
        alb_obj.tags = [{"Key": "Name", "Value": "new"}]
        alb_obj.elb = {"tags": [{"Key": "Name", "Value": "old"}, {"Key": "OldTag", "Value": "value"}]}

        mock_boto3_to_dict.return_value = {}
        mock_compare.return_value = (True, ["OldTag"])

        elb_application_lb._update_alb_tags(alb_obj)

        alb_obj.delete_tags.assert_called_once_with(["OldTag"])
        alb_obj.modify_tags.assert_called_once()


class TestUpdateExistingAlbProperties:
    """Tests for _update_existing_alb_properties helper function"""

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._update_alb_tags")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._exit_if_check_mode")
    def test_subnets_need_modification(self, mock_exit, mock_update_tags):
        """Should modify subnets when they differ"""
        alb_obj = MagicMock()
        alb_obj.check_mode = False
        alb_obj.compare_subnets.return_value = False
        alb_obj.compare_security_groups.return_value = True
        alb_obj.compare_elb_attributes.return_value = True

        elb_application_lb._update_existing_alb_properties(alb_obj)

        alb_obj.modify_subnets.assert_called_once()

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._update_alb_tags")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._exit_if_check_mode")
    def test_security_groups_need_modification(self, mock_exit, mock_update_tags):
        """Should modify security groups when they differ"""
        alb_obj = MagicMock()
        alb_obj.check_mode = False
        alb_obj.compare_subnets.return_value = True
        alb_obj.compare_security_groups.return_value = False
        alb_obj.compare_elb_attributes.return_value = True

        elb_application_lb._update_existing_alb_properties(alb_obj)

        alb_obj.modify_security_groups.assert_called_once()

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._update_alb_tags")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._exit_if_check_mode")
    def test_attributes_need_modification(self, mock_exit, mock_update_tags):
        """Should modify attributes when they differ"""
        alb_obj = MagicMock()
        alb_obj.check_mode = False
        alb_obj.compare_subnets.return_value = True
        alb_obj.compare_security_groups.return_value = True
        alb_obj.compare_elb_attributes.return_value = False

        elb_application_lb._update_existing_alb_properties(alb_obj)

        alb_obj.update_elb_attributes.assert_called_once()
        alb_obj.modify_elb_attributes.assert_called_once()

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._update_alb_tags")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._exit_if_check_mode")
    def test_no_modifications_needed(self, mock_exit, mock_update_tags):
        """Should not modify anything when everything matches"""
        alb_obj = MagicMock()
        alb_obj.check_mode = False
        alb_obj.compare_subnets.return_value = True
        alb_obj.compare_security_groups.return_value = True
        alb_obj.compare_elb_attributes.return_value = True

        elb_application_lb._update_existing_alb_properties(alb_obj)

        alb_obj.modify_subnets.assert_not_called()
        alb_obj.modify_security_groups.assert_not_called()
        alb_obj.modify_elb_attributes.assert_not_called()

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._update_alb_tags")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._exit_if_check_mode")
    def test_exits_in_check_mode_for_subnets(self, mock_exit, mock_update_tags):
        """Should exit in check mode when subnets need modification"""
        alb_obj = MagicMock()
        alb_obj.compare_subnets.return_value = False

        elb_application_lb._update_existing_alb_properties(alb_obj)

        mock_exit.assert_called_with(alb_obj)


class TestCreateNewAlb:
    """Tests for _create_new_alb helper function"""

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._exit_if_check_mode")
    def test_creates_alb_and_sets_attributes(self, mock_exit):
        """Should create ALB and set attributes"""
        alb_obj = MagicMock()
        alb_obj.check_mode = False

        elb_application_lb._create_new_alb(alb_obj)

        mock_exit.assert_called_once_with(alb_obj, action="created")
        alb_obj.create_elb.assert_called_once()
        alb_obj.update_elb_attributes.assert_called_once()
        alb_obj.modify_elb_attributes.assert_called_once()

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._exit_if_check_mode")
    def test_exits_in_check_mode(self, mock_exit):
        """Should exit in check mode before creating ALB"""
        alb_obj = MagicMock()
        alb_obj.check_mode = True

        # Mock exit_if_check_mode to actually exit (raise exception)
        def exit_side_effect(obj, action="updated"):
            if obj.check_mode:
                obj.exit_json(changed=True, msg=f"Would have {action} ALB if not in check mode.")

        mock_exit.side_effect = exit_side_effect

        elb_application_lb._create_new_alb(alb_obj)

        mock_exit.assert_called_once_with(alb_obj, action="created")


class TestManageAlbListeners:
    """Tests for _manage_alb_listeners helper function"""

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.ELBListeners")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.ELBListener")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._exit_if_check_mode")
    def test_no_listener_changes(self, mock_exit, mock_listener_class, mock_listeners_class):
        """Should not make changes when listeners match"""
        alb_obj = MagicMock()
        alb_obj.elb = {"LoadBalancerArn": "arn:aws:..."}

        listeners_obj = MagicMock()
        listeners_obj.compare_listeners.return_value = ([], [], [])
        mock_listeners_class.return_value = listeners_obj

        result = elb_application_lb._manage_alb_listeners(alb_obj)

        mock_exit.assert_not_called()
        assert result == listeners_obj

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.ELBListeners")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.ELBListener")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._exit_if_check_mode")
    def test_exits_in_check_mode_with_changes(self, mock_exit, mock_listener_class, mock_listeners_class):
        """Should exit in check mode when listener changes needed"""
        alb_obj = MagicMock()
        alb_obj.elb = {"LoadBalancerArn": "arn:aws:..."}

        listeners_obj = MagicMock()
        listeners_obj.compare_listeners.return_value = ([{"Port": 80}], [], [])
        mock_listeners_class.return_value = listeners_obj

        elb_application_lb._manage_alb_listeners(alb_obj)

        mock_exit.assert_called_once_with(alb_obj)

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.ELBListeners")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.ELBListener")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._exit_if_check_mode")
    def test_adds_listeners(self, mock_exit, mock_listener_class, mock_listeners_class):
        """Should add new listeners"""
        alb_obj = MagicMock()
        alb_obj.check_mode = False
        alb_obj.elb = {"LoadBalancerArn": "arn:aws:..."}

        listeners_obj = MagicMock()
        listener_to_add = {"Port": 80, "Protocol": "HTTP"}
        listeners_obj.compare_listeners.return_value = ([listener_to_add], [], [])
        mock_listeners_class.return_value = listeners_obj

        listener_instance = MagicMock()
        mock_listener_class.return_value = listener_instance

        elb_application_lb._manage_alb_listeners(alb_obj)

        mock_listener_class.assert_called_once()
        listener_instance.add.assert_called_once()
        listeners_obj.update.assert_called_once()


class TestManageListenerRules:
    """Tests for _manage_listener_rules helper function"""

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.ELBListenerRules")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.ELBListenerRule")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._exit_if_check_mode")
    def test_no_rules_defined(self, mock_exit, mock_rule_class, mock_rules_class):
        """Should skip listeners without rules defined"""
        alb_obj = MagicMock()
        listeners_obj = MagicMock()
        listeners_obj.listeners = [{"Port": 80}]  # No Rules key

        elb_application_lb._manage_listener_rules(alb_obj, listeners_obj)

        mock_rules_class.assert_not_called()
        mock_exit.assert_not_called()

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.ELBListenerRules")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.ELBListenerRule")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._exit_if_check_mode")
    def test_exits_in_check_mode_with_rule_changes(self, mock_exit, mock_rule_class, mock_rules_class):
        """Should exit in check mode when rule changes needed"""
        alb_obj = MagicMock()
        listeners_obj = MagicMock()
        listeners_obj.listeners = [{"Port": 80, "Rules": [{"Priority": 1}]}]
        listeners_obj.get_listener_arn_from_listener_port.return_value = "arn:listener"

        rules_obj = MagicMock()
        rules_obj.compare_rules.return_value = ([{"Priority": 1}], [], [], [])
        mock_rules_class.return_value = rules_obj

        elb_application_lb._manage_listener_rules(alb_obj, listeners_obj)

        mock_exit.assert_called_once_with(alb_obj)


class TestUpdateAlbIpAddressType:
    """Tests for _update_alb_ip_address_type helper function"""

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._exit_if_check_mode")
    def test_no_ip_address_type_specified(self, mock_exit):
        """Should skip when ip_address_type not specified"""
        alb_obj = MagicMock()
        alb_obj.params = {}

        elb_application_lb._update_alb_ip_address_type(alb_obj)

        alb_obj.modify_ip_address_type.assert_not_called()
        mock_exit.assert_not_called()

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._exit_if_check_mode")
    def test_ip_address_type_matches_current(self, mock_exit):
        """Should skip when ip_address_type matches current value"""
        alb_obj = MagicMock()
        alb_obj.params = {"ip_address_type": "ipv4"}
        alb_obj.elb_ip_addr_type = "ipv4"

        elb_application_lb._update_alb_ip_address_type(alb_obj)

        alb_obj.modify_ip_address_type.assert_not_called()
        mock_exit.assert_not_called()

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._exit_if_check_mode")
    def test_exits_in_check_mode_when_change_needed(self, mock_exit):
        """Should exit in check mode when ip_address_type needs to change"""
        alb_obj = MagicMock()
        alb_obj.params = {"ip_address_type": "dualstack"}
        alb_obj.elb_ip_addr_type = "ipv4"

        elb_application_lb._update_alb_ip_address_type(alb_obj)

        mock_exit.assert_called_once_with(alb_obj)

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._exit_if_check_mode")
    def test_modifies_ip_address_type(self, mock_exit):
        """Should modify ip_address_type when different"""
        alb_obj = MagicMock()
        alb_obj.check_mode = False
        alb_obj.params = {"ip_address_type": "dualstack"}
        alb_obj.elb_ip_addr_type = "ipv4"

        elb_application_lb._update_alb_ip_address_type(alb_obj)

        alb_obj.modify_ip_address_type.assert_called_once_with("dualstack")


class TestDeleteAlb:
    """Tests for delete_alb function"""

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._exit_if_check_mode")
    def test_alb_does_not_exist(self, mock_exit):
        """Should exit with changed=False when ALB doesn't exist"""
        alb_obj = MagicMock()
        alb_obj.elb = None

        # exit_json doesn't actually stop execution, it just sets the response
        # So we need to make it raise an exception to simulate exiting
        alb_obj.exit_json.side_effect = SystemExit()

        with pytest.raises(SystemExit):
            elb_application_lb.delete_alb(alb_obj)

        alb_obj.exit_json.assert_called_once_with(changed=False)
        mock_exit.assert_not_called()

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.ELBListeners")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.ELBListener")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._exit_if_check_mode")
    def test_exits_in_check_mode(self, mock_exit, mock_listener_class, mock_listeners_class):
        """Should exit in check mode before deleting"""
        alb_obj = MagicMock()
        alb_obj.elb = {"LoadBalancerArn": "arn:aws:..."}

        elb_application_lb.delete_alb(alb_obj)

        mock_exit.assert_called_once_with(alb_obj, action="deleted")

    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.ELBListeners")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb.ELBListener")
    @patch("ansible_collections.amazon.aws.plugins.modules.elb_application_lb._exit_if_check_mode")
    def test_deletes_listeners_and_alb(self, mock_exit, mock_listener_class, mock_listeners_class):
        """Should delete all listeners then delete ALB"""
        alb_obj = MagicMock()
        alb_obj.check_mode = False
        alb_obj.elb = {"LoadBalancerArn": "arn:aws:alb"}
        alb_obj.changed = False

        listeners_obj = MagicMock()
        listeners_obj.current_listeners = [
            {"ListenerArn": "arn:listener:1"},
            {"ListenerArn": "arn:listener:2"},
        ]
        mock_listeners_class.return_value = listeners_obj

        listener_instance = MagicMock()
        mock_listener_class.return_value = listener_instance

        elb_application_lb.delete_alb(alb_obj)

        # Should create ELBListener for each listener and delete them
        assert mock_listener_class.call_count == 2
        assert listener_instance.delete.call_count == 2

        # Should delete the ALB
        alb_obj.delete.assert_called_once()
        alb_obj.exit_json.assert_called_once()
        assert alb_obj.exit_json.call_args[1]["changed"] == alb_obj.changed
