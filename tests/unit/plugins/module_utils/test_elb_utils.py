# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class TestElbUtilsCompatibility:
    """Test suite for elb_utils.py backwards-compatibility re-exports."""

    def test_compatibility_exports_exist(self):
        """Verify all compatibility re-exports are present."""
        from ansible_collections.amazon.aws.plugins.module_utils import elb_utils

        # Re-exports from elbv2 (originally _elbv2.api)
        assert hasattr(elb_utils, "add_listener_certificates")
        assert hasattr(elb_utils, "add_tags")
        assert hasattr(elb_utils, "create_listener")
        assert hasattr(elb_utils, "create_load_balancer")
        assert hasattr(elb_utils, "create_rule")
        assert hasattr(elb_utils, "delete_listener")
        assert hasattr(elb_utils, "delete_load_balancer")
        assert hasattr(elb_utils, "delete_rule")
        assert hasattr(elb_utils, "describe_listeners")
        assert hasattr(elb_utils, "describe_load_balancer_attributes")
        assert hasattr(elb_utils, "describe_load_balancers")
        assert hasattr(elb_utils, "describe_rules")
        assert hasattr(elb_utils, "describe_tags")
        assert hasattr(elb_utils, "describe_target_groups")
        assert hasattr(elb_utils, "modify_listener")
        assert hasattr(elb_utils, "modify_load_balancer_attributes")
        assert hasattr(elb_utils, "modify_rule")
        assert hasattr(elb_utils, "remove_tags")
        assert hasattr(elb_utils, "set_ip_address_type")
        assert hasattr(elb_utils, "set_rule_priorities")
        assert hasattr(elb_utils, "set_security_groups")
        assert hasattr(elb_utils, "set_subnets")

        # Re-exports from elbv2 (originally _elbv2.common)
        assert hasattr(elb_utils, "AnsibleELBv2Error")
        assert hasattr(elb_utils, "ELBv2ListenerErrorHandler")
        assert hasattr(elb_utils, "ELBv2RuleErrorHandler")
        assert hasattr(elb_utils, "ELBv2TargetGroupErrorHandler")

    def test_wrapper_functions_exist(self):
        """Verify backwards-compatibility wrapper functions are present."""
        from ansible_collections.amazon.aws.plugins.module_utils import elb_utils

        # Wrapper functions that provide fail_json_aws handling
        assert hasattr(elb_utils, "get_elb")
        assert hasattr(elb_utils, "get_elb_listener_rules")
        assert hasattr(elb_utils, "convert_tg_name_to_arn")
