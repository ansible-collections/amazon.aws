# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import patch

import ansible_collections.amazon.aws.plugins.modules.autoscaling_group as asg_module


class TestShouldTerminateInstanceForLaunchConfig:
    def test_no_lc_check_instance_in_initial(self):
        """Test when lc_check=False and instance is in initial_instances"""
        props = {"instance_facts": {"i-123": {}}}
        result = asg_module._should_terminate_instance_for_launch_config(
            instance_id="i-123", props=props, lc_check=False, initial_instances=["i-123", "i-456"]
        )
        assert result is True

    def test_no_lc_check_instance_not_in_initial(self):
        """Test when lc_check=False and instance is not in initial_instances"""
        props = {"instance_facts": {"i-789": {}}}
        result = asg_module._should_terminate_instance_for_launch_config(
            instance_id="i-789", props=props, lc_check=False, initial_instances=["i-123", "i-456"]
        )
        assert result is False

    def test_lc_check_migrating_from_launch_template(self):
        """Test terminating instance when migrating from launch template to launch config"""
        props = {
            "instance_facts": {"i-123": {"launch_template": {"LaunchTemplateId": "lt-123", "Version": "1"}}},
            "launch_config_name": "my-lc",
        }
        result = asg_module._should_terminate_instance_for_launch_config(
            instance_id="i-123", props=props, lc_check=True, initial_instances=[]
        )
        assert result is True

    def test_lc_check_different_launch_config(self):
        """Test terminating instance with different launch config"""
        props = {
            "instance_facts": {"i-123": {"launch_config_name": "old-lc"}},
            "launch_config_name": "new-lc",
        }
        result = asg_module._should_terminate_instance_for_launch_config(
            instance_id="i-123", props=props, lc_check=True, initial_instances=[]
        )
        assert result is True

    def test_lc_check_same_launch_config(self):
        """Test keeping instance with same launch config"""
        props = {
            "instance_facts": {"i-123": {"launch_config_name": "my-lc"}},
            "launch_config_name": "my-lc",
        }
        result = asg_module._should_terminate_instance_for_launch_config(
            instance_id="i-123", props=props, lc_check=True, initial_instances=[]
        )
        assert result is False

    def test_lc_check_no_launch_config_in_facts(self):
        """Test when instance has no launch_config_name (should terminate)"""
        props = {
            "instance_facts": {"i-123": {}},
            "launch_config_name": "my-lc",
        }
        result = asg_module._should_terminate_instance_for_launch_config(
            instance_id="i-123", props=props, lc_check=True, initial_instances=[]
        )
        assert result is True


class TestShouldTerminateInstanceForLaunchTemplate:
    def test_no_lt_check_instance_in_initial(self):
        """Test when lt_check=False and instance is in initial_instances"""
        props = {"instance_facts": {"i-123": {}}}
        result = asg_module._should_terminate_instance_for_launch_template(
            instance_id="i-123", props=props, lt_check=False, initial_instances=["i-123", "i-456"]
        )
        assert result is True

    def test_no_lt_check_instance_not_in_initial(self):
        """Test when lt_check=False and instance is not in initial_instances"""
        props = {"instance_facts": {"i-789": {}}}
        result = asg_module._should_terminate_instance_for_launch_template(
            instance_id="i-789", props=props, lt_check=False, initial_instances=["i-123", "i-456"]
        )
        assert result is False

    def test_lt_check_migrating_from_launch_config(self):
        """Test terminating instance when migrating from launch config to launch template"""
        props = {
            "instance_facts": {"i-123": {"launch_config_name": "old-lc"}},
            "launch_template": {"LaunchTemplateId": "lt-123", "Version": "1"},
        }
        result = asg_module._should_terminate_instance_for_launch_template(
            instance_id="i-123", props=props, lt_check=True, initial_instances=[]
        )
        assert result is True

    def test_lt_check_different_launch_template(self):
        """Test terminating instance with different launch template"""
        props = {
            "instance_facts": {"i-123": {"launch_template": {"LaunchTemplateId": "lt-old", "Version": "1"}}},
            "launch_template": {"LaunchTemplateId": "lt-new", "Version": "2"},
        }
        result = asg_module._should_terminate_instance_for_launch_template(
            instance_id="i-123", props=props, lt_check=True, initial_instances=[]
        )
        assert result is True

    def test_lt_check_same_launch_template(self):
        """Test keeping instance with same launch template"""
        lt_spec = {"LaunchTemplateId": "lt-123", "Version": "1"}
        props = {
            "instance_facts": {"i-123": {"launch_template": lt_spec}},
            "launch_template": lt_spec,
        }
        result = asg_module._should_terminate_instance_for_launch_template(
            instance_id="i-123", props=props, lt_check=True, initial_instances=[]
        )
        assert result is False

    def test_lt_check_no_launch_template_in_facts(self):
        """Test when instance has no launch_template (should terminate)"""
        props = {
            "instance_facts": {"i-123": {}},
            "launch_template": {"LaunchTemplateId": "lt-123", "Version": "1"},
        }
        result = asg_module._should_terminate_instance_for_launch_template(
            instance_id="i-123", props=props, lt_check=True, initial_instances=[]
        )
        assert result is True


class TestListPurgeableInstances:
    @patch.object(asg_module, "module", create=True)
    def test_launch_config_mode_terminate_all(self, mock_module):
        """Test launch config mode with instances that should be terminated"""
        mock_module.params = {"launch_config_name": "new-lc"}

        props = {
            "instances": ["i-123", "i-456"],
            "instance_facts": {
                "i-123": {"launch_config_name": "old-lc"},
                "i-456": {"launch_config_name": "old-lc"},
            },
            "launch_config_name": "new-lc",
        }

        result = asg_module.list_purgeable_instances(
            props=props,
            lc_check=True,
            lt_check=False,
            replace_instances=["i-123", "i-456"],
            initial_instances=[],
        )

        assert set(result) == {"i-123", "i-456"}

    @patch.object(asg_module, "module", create=True)
    def test_launch_config_mode_keep_all(self, mock_module):
        """Test launch config mode with instances that should be kept"""
        mock_module.params = {"launch_config_name": "my-lc"}

        props = {
            "instances": ["i-123", "i-456"],
            "instance_facts": {
                "i-123": {"launch_config_name": "my-lc"},
                "i-456": {"launch_config_name": "my-lc"},
            },
            "launch_config_name": "my-lc",
        }

        result = asg_module.list_purgeable_instances(
            props=props,
            lc_check=True,
            lt_check=False,
            replace_instances=["i-123", "i-456"],
            initial_instances=[],
        )

        assert result == []

    @patch.object(asg_module, "module", create=True)
    def test_launch_config_mode_mixed(self, mock_module):
        """Test launch config mode with some instances to terminate"""
        mock_module.params = {"launch_config_name": "new-lc"}

        props = {
            "instances": ["i-123", "i-456", "i-789"],
            "instance_facts": {
                "i-123": {"launch_config_name": "old-lc"},
                "i-456": {"launch_config_name": "new-lc"},
                "i-789": {"launch_config_name": "old-lc"},
            },
            "launch_config_name": "new-lc",
        }

        result = asg_module.list_purgeable_instances(
            props=props,
            lc_check=True,
            lt_check=False,
            replace_instances=["i-123", "i-456", "i-789"],
            initial_instances=[],
        )

        assert set(result) == {"i-123", "i-789"}

    @patch.object(asg_module, "module", create=True)
    def test_launch_template_mode_terminate_all(self, mock_module):
        """Test launch template mode with instances that should be terminated"""
        mock_module.params = {"launch_template": {"launch_template_id": "lt-new", "version": "2"}}

        props = {
            "instances": ["i-123", "i-456"],
            "instance_facts": {
                "i-123": {"launch_template": {"LaunchTemplateId": "lt-old", "Version": "1"}},
                "i-456": {"launch_template": {"LaunchTemplateId": "lt-old", "Version": "1"}},
            },
            "launch_template": {"LaunchTemplateId": "lt-new", "Version": "2"},
        }

        result = asg_module.list_purgeable_instances(
            props=props,
            lc_check=False,
            lt_check=True,
            replace_instances=["i-123", "i-456"],
            initial_instances=[],
        )

        assert set(result) == {"i-123", "i-456"}

    @patch.object(asg_module, "module", create=True)
    def test_launch_template_mode_keep_all(self, mock_module):
        """Test launch template mode with instances that should be kept"""
        mock_module.params = {"launch_template": {"launch_template_id": "lt-123", "version": "1"}}

        lt_spec = {"LaunchTemplateId": "lt-123", "Version": "1"}
        props = {
            "instances": ["i-123", "i-456"],
            "instance_facts": {
                "i-123": {"launch_template": lt_spec},
                "i-456": {"launch_template": lt_spec},
            },
            "launch_template": lt_spec,
        }

        result = asg_module.list_purgeable_instances(
            props=props,
            lc_check=False,
            lt_check=True,
            replace_instances=["i-123", "i-456"],
            initial_instances=[],
        )

        assert result == []

    @patch.object(asg_module, "module", create=True)
    def test_filters_instances_not_in_asg(self, mock_module):
        """Test that instances not in the ASG are filtered out"""
        mock_module.params = {"launch_config_name": "my-lc"}

        props = {
            "instances": ["i-123", "i-456"],  # Only these are in the ASG
            "instance_facts": {
                "i-123": {"launch_config_name": "old-lc"},
                "i-456": {"launch_config_name": "old-lc"},
            },
            "launch_config_name": "new-lc",
        }

        # i-789 is in replace_instances but not in the ASG
        result = asg_module.list_purgeable_instances(
            props=props,
            lc_check=True,
            lt_check=False,
            replace_instances=["i-123", "i-456", "i-789"],
            initial_instances=[],
        )

        # i-789 should not be in the result even though it's in replace_instances
        assert set(result) == {"i-123", "i-456"}

    @patch.object(asg_module, "module", create=True)
    def test_no_lc_check_uses_initial_instances(self, mock_module):
        """Test that when lc_check=False, initial_instances is used"""
        mock_module.params = {"launch_config_name": "my-lc"}

        props = {
            "instances": ["i-123", "i-456", "i-789"],
            "instance_facts": {
                "i-123": {"launch_config_name": "old-lc"},
                "i-456": {"launch_config_name": "old-lc"},
                "i-789": {"launch_config_name": "old-lc"},
            },
            "launch_config_name": "new-lc",
        }

        result = asg_module.list_purgeable_instances(
            props=props,
            lc_check=False,
            lt_check=False,
            replace_instances=["i-123", "i-456", "i-789"],
            initial_instances=["i-123", "i-789"],  # Only these should be terminated
        )

        assert set(result) == {"i-123", "i-789"}

    @patch.object(asg_module, "module", create=True)
    def test_empty_replace_instances(self, mock_module):
        """Test with empty replace_instances list"""
        mock_module.params = {"launch_config_name": "my-lc"}

        props = {
            "instances": ["i-123", "i-456"],
            "instance_facts": {
                "i-123": {"launch_config_name": "old-lc"},
                "i-456": {"launch_config_name": "old-lc"},
            },
            "launch_config_name": "new-lc",
        }

        result = asg_module.list_purgeable_instances(
            props=props, lc_check=True, lt_check=False, replace_instances=[], initial_instances=[]
        )

        assert result == []

    @patch.object(asg_module, "module", create=True)
    def test_migration_from_lc_to_lt(self, mock_module):
        """Test migrating from launch config to launch template"""
        mock_module.params = {"launch_template": {"launch_template_id": "lt-new", "version": "1"}}

        props = {
            "instances": ["i-123", "i-456"],
            "instance_facts": {
                "i-123": {"launch_config_name": "old-lc"},  # Has launch config
                "i-456": {"launch_config_name": "old-lc"},
            },
            "launch_template": {"LaunchTemplateId": "lt-new", "Version": "1"},
        }

        result = asg_module.list_purgeable_instances(
            props=props,
            lc_check=False,
            lt_check=True,
            replace_instances=["i-123", "i-456"],
            initial_instances=[],
        )

        # Both should be terminated because they have launch configs but we want launch template
        assert set(result) == {"i-123", "i-456"}

    @patch.object(asg_module, "module", create=True)
    def test_migration_from_lt_to_lc(self, mock_module):
        """Test migrating from launch template to launch config"""
        mock_module.params = {"launch_config_name": "new-lc"}

        props = {
            "instances": ["i-123", "i-456"],
            "instance_facts": {
                "i-123": {"launch_template": {"LaunchTemplateId": "lt-old", "Version": "1"}},
                "i-456": {"launch_template": {"LaunchTemplateId": "lt-old", "Version": "1"}},
            },
            "launch_config_name": "new-lc",
        }

        result = asg_module.list_purgeable_instances(
            props=props,
            lc_check=True,
            lt_check=False,
            replace_instances=["i-123", "i-456"],
            initial_instances=[],
        )

        # Both should be terminated because they have launch templates but we want launch config
        assert set(result) == {"i-123", "i-456"}
