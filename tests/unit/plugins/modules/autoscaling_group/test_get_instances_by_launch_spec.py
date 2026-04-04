# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import patch

import ansible_collections.amazon.aws.plugins.modules.autoscaling_group as asg_module


class TestIsInstanceUsingLaunchConfig:
    def test_instance_has_launch_template_not_config(self):
        """Test instance with launch template instead of launch config"""
        props = {
            "instance_facts": {"i-123": {"launch_template": {"LaunchTemplateId": "lt-123", "Version": "1"}}},
            "launch_config_name": "my-lc",
        }
        result = asg_module._is_instance_using_launch_config("i-123", props)
        assert result is False

    def test_instance_matches_current_launch_config(self):
        """Test instance with matching launch config"""
        props = {
            "instance_facts": {"i-123": {"launch_config_name": "my-lc"}},
            "launch_config_name": "my-lc",
        }
        result = asg_module._is_instance_using_launch_config("i-123", props)
        assert result is True

    def test_instance_has_different_launch_config(self):
        """Test instance with different launch config"""
        props = {
            "instance_facts": {"i-123": {"launch_config_name": "old-lc"}},
            "launch_config_name": "new-lc",
        }
        result = asg_module._is_instance_using_launch_config("i-123", props)
        assert result is False

    def test_instance_has_no_launch_config(self):
        """Test instance with no launch config"""
        props = {
            "instance_facts": {"i-123": {}},
            "launch_config_name": "my-lc",
        }
        result = asg_module._is_instance_using_launch_config("i-123", props)
        assert result is False


class TestIsInstanceUsingLaunchTemplate:
    def test_instance_has_launch_config_not_template(self):
        """Test instance with launch config instead of launch template"""
        props = {
            "instance_facts": {"i-123": {"launch_config_name": "old-lc"}},
            "launch_template": {"LaunchTemplateId": "lt-123", "Version": "1"},
        }
        result = asg_module._is_instance_using_launch_template("i-123", props)
        assert result is False

    def test_instance_matches_current_launch_template(self):
        """Test instance with matching launch template"""
        lt_spec = {"LaunchTemplateId": "lt-123", "Version": "1"}
        props = {
            "instance_facts": {"i-123": {"launch_template": lt_spec}},
            "launch_template": lt_spec,
        }
        result = asg_module._is_instance_using_launch_template("i-123", props)
        assert result is True

    def test_instance_has_different_launch_template(self):
        """Test instance with different launch template"""
        props = {
            "instance_facts": {"i-123": {"launch_template": {"LaunchTemplateId": "lt-old", "Version": "1"}}},
            "launch_template": {"LaunchTemplateId": "lt-new", "Version": "2"},
        }
        result = asg_module._is_instance_using_launch_template("i-123", props)
        assert result is False

    def test_instance_has_no_launch_template(self):
        """Test instance with no launch template"""
        props = {
            "instance_facts": {"i-123": {}},
            "launch_template": {"LaunchTemplateId": "lt-123", "Version": "1"},
        }
        result = asg_module._is_instance_using_launch_template("i-123", props)
        assert result is False


class TestGetInstancesByLaunchSpec:
    @patch.object(asg_module, "module", create=True)
    def test_check_enabled_all_new(self, mock_module):
        """Test with check enabled and all instances using current spec"""
        mock_module.debug = lambda x: None
        props = {"instances": ["i-123", "i-456", "i-789"]}

        def all_use_current(instance_id, props):
            return True

        new_instances, old_instances = asg_module._get_instances_by_launch_spec(
            props, check_enabled=True, initial_instances=[], is_using_current_spec=all_use_current
        )

        assert set(new_instances) == {"i-123", "i-456", "i-789"}
        assert old_instances == []

    @patch.object(asg_module, "module", create=True)
    def test_check_enabled_all_old(self, mock_module):
        """Test with check enabled and no instances using current spec"""
        mock_module.debug = lambda x: None
        props = {"instances": ["i-123", "i-456", "i-789"]}

        def none_use_current(instance_id, props):
            return False

        new_instances, old_instances = asg_module._get_instances_by_launch_spec(
            props, check_enabled=True, initial_instances=[], is_using_current_spec=none_use_current
        )

        assert new_instances == []
        assert set(old_instances) == {"i-123", "i-456", "i-789"}

    @patch.object(asg_module, "module", create=True)
    def test_check_enabled_mixed(self, mock_module):
        """Test with check enabled and mixed instances"""
        mock_module.debug = lambda x: None
        props = {"instances": ["i-123", "i-456", "i-789"]}

        def mixed_use_current(instance_id, props):
            return instance_id in ["i-123", "i-789"]

        new_instances, old_instances = asg_module._get_instances_by_launch_spec(
            props, check_enabled=True, initial_instances=[], is_using_current_spec=mixed_use_current
        )

        assert set(new_instances) == {"i-123", "i-789"}
        assert set(old_instances) == {"i-456"}

    @patch.object(asg_module, "module", create=True)
    def test_check_disabled_uses_initial_instances(self, mock_module):
        """Test with check disabled - uses initial_instances list"""
        mock_module.debug = lambda x: None
        props = {"instances": ["i-123", "i-456", "i-789", "i-000"]}

        def should_not_be_called(instance_id, props):
            raise AssertionError("is_using_current_spec should not be called when check is disabled")

        new_instances, old_instances = asg_module._get_instances_by_launch_spec(
            props,
            check_enabled=False,
            initial_instances=["i-123", "i-789"],
            is_using_current_spec=should_not_be_called,
        )

        assert set(new_instances) == {"i-456", "i-000"}
        assert set(old_instances) == {"i-123", "i-789"}

    @patch.object(asg_module, "module", create=True)
    def test_check_disabled_all_initial(self, mock_module):
        """Test with check disabled - all instances in initial_instances"""
        mock_module.debug = lambda x: None
        props = {"instances": ["i-123", "i-456"]}

        new_instances, old_instances = asg_module._get_instances_by_launch_spec(
            props, check_enabled=False, initial_instances=["i-123", "i-456"], is_using_current_spec=lambda x, y: True
        )

        assert new_instances == []
        assert set(old_instances) == {"i-123", "i-456"}

    @patch.object(asg_module, "module", create=True)
    def test_check_disabled_none_initial(self, mock_module):
        """Test with check disabled - no instances in initial_instances"""
        mock_module.debug = lambda x: None
        props = {"instances": ["i-123", "i-456"]}

        new_instances, old_instances = asg_module._get_instances_by_launch_spec(
            props, check_enabled=False, initial_instances=[], is_using_current_spec=lambda x, y: True
        )

        assert set(new_instances) == {"i-123", "i-456"}
        assert old_instances == []


class TestGetInstancesByLaunchConfig:
    @patch.object(asg_module, "module", create=True)
    def test_all_instances_use_current_config(self, mock_module):
        """Test when all instances use the current launch config"""
        mock_module.debug = lambda x: None
        props = {
            "instances": ["i-123", "i-456"],
            "instance_facts": {
                "i-123": {"launch_config_name": "my-lc"},
                "i-456": {"launch_config_name": "my-lc"},
            },
            "launch_config_name": "my-lc",
        }

        new_instances, old_instances = asg_module.get_instances_by_launch_config(
            props, lc_check=True, initial_instances=[]
        )

        assert set(new_instances) == {"i-123", "i-456"}
        assert old_instances == []

    @patch.object(asg_module, "module", create=True)
    def test_mixed_launch_configs(self, mock_module):
        """Test with mix of old and new launch configs"""
        mock_module.debug = lambda x: None
        props = {
            "instances": ["i-123", "i-456", "i-789"],
            "instance_facts": {
                "i-123": {"launch_config_name": "old-lc"},
                "i-456": {"launch_config_name": "new-lc"},
                "i-789": {"launch_config_name": "old-lc"},
            },
            "launch_config_name": "new-lc",
        }

        new_instances, old_instances = asg_module.get_instances_by_launch_config(
            props, lc_check=True, initial_instances=[]
        )

        assert set(new_instances) == {"i-456"}
        assert set(old_instances) == {"i-123", "i-789"}

    @patch.object(asg_module, "module", create=True)
    def test_migration_from_launch_template(self, mock_module):
        """Test migration from launch template to launch config"""
        mock_module.debug = lambda x: None
        props = {
            "instances": ["i-123", "i-456"],
            "instance_facts": {
                "i-123": {"launch_template": {"LaunchTemplateId": "lt-old", "Version": "1"}},
                "i-456": {"launch_config_name": "new-lc"},
            },
            "launch_config_name": "new-lc",
        }

        new_instances, old_instances = asg_module.get_instances_by_launch_config(
            props, lc_check=True, initial_instances=[]
        )

        assert set(new_instances) == {"i-456"}
        assert set(old_instances) == {"i-123"}


class TestGetInstancesByLaunchTemplate:
    @patch.object(asg_module, "module", create=True)
    def test_all_instances_use_current_template(self, mock_module):
        """Test when all instances use the current launch template"""
        mock_module.debug = lambda x: None
        lt_spec = {"LaunchTemplateId": "lt-123", "Version": "1"}
        props = {
            "instances": ["i-123", "i-456"],
            "instance_facts": {
                "i-123": {"launch_template": lt_spec},
                "i-456": {"launch_template": lt_spec},
            },
            "launch_template": lt_spec,
        }

        new_instances, old_instances = asg_module.get_instances_by_launch_template(
            props, lt_check=True, initial_instances=[]
        )

        assert set(new_instances) == {"i-123", "i-456"}
        assert old_instances == []

    @patch.object(asg_module, "module", create=True)
    def test_mixed_launch_templates(self, mock_module):
        """Test with mix of old and new launch templates"""
        mock_module.debug = lambda x: None
        props = {
            "instances": ["i-123", "i-456", "i-789"],
            "instance_facts": {
                "i-123": {"launch_template": {"LaunchTemplateId": "lt-old", "Version": "1"}},
                "i-456": {"launch_template": {"LaunchTemplateId": "lt-new", "Version": "2"}},
                "i-789": {"launch_template": {"LaunchTemplateId": "lt-old", "Version": "1"}},
            },
            "launch_template": {"LaunchTemplateId": "lt-new", "Version": "2"},
        }

        new_instances, old_instances = asg_module.get_instances_by_launch_template(
            props, lt_check=True, initial_instances=[]
        )

        assert set(new_instances) == {"i-456"}
        assert set(old_instances) == {"i-123", "i-789"}

    @patch.object(asg_module, "module", create=True)
    def test_migration_from_launch_config(self, mock_module):
        """Test migration from launch config to launch template"""
        mock_module.debug = lambda x: None
        props = {
            "instances": ["i-123", "i-456"],
            "instance_facts": {
                "i-123": {"launch_config_name": "old-lc"},
                "i-456": {"launch_template": {"LaunchTemplateId": "lt-new", "Version": "1"}},
            },
            "launch_template": {"LaunchTemplateId": "lt-new", "Version": "1"},
        }

        new_instances, old_instances = asg_module.get_instances_by_launch_template(
            props, lt_check=True, initial_instances=[]
        )

        assert set(new_instances) == {"i-456"}
        assert set(old_instances) == {"i-123"}
