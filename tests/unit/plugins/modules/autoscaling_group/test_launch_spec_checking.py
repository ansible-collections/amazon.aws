# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.amazon.aws.plugins.modules.autoscaling_group import _is_instance_using_launch_config
from ansible_collections.amazon.aws.plugins.modules.autoscaling_group import _is_instance_using_launch_template
from ansible_collections.amazon.aws.plugins.modules.autoscaling_group import (
    _should_terminate_instance_for_launch_config,
)
from ansible_collections.amazon.aws.plugins.modules.autoscaling_group import (
    _should_terminate_instance_for_launch_template,
)


class TestIsInstanceUsingLaunchConfig:
    """Test suite for _is_instance_using_launch_config function."""

    def test_instance_with_matching_launch_config(self):
        """Test that instance with matching launch config returns True."""
        props = {
            "launch_config_name": "my-lc-v1",
            "instance_facts": {
                "i-12345": {
                    "health_status": "Healthy",
                    "lifecycle_state": "InService",
                    "launch_config_name": "my-lc-v1",
                }
            },
        }

        assert _is_instance_using_launch_config("i-12345", props) is True

    def test_instance_with_different_launch_config(self):
        """Test that instance with different launch config returns False."""
        props = {
            "launch_config_name": "my-lc-v2",
            "instance_facts": {
                "i-12345": {
                    "health_status": "Healthy",
                    "lifecycle_state": "InService",
                    "launch_config_name": "my-lc-v1",
                }
            },
        }

        assert _is_instance_using_launch_config("i-12345", props) is False

    def test_instance_with_launch_template_instead(self):
        """Test that instance with launch template instead of config returns False."""
        props = {
            "launch_config_name": "my-lc-v1",
            "instance_facts": {
                "i-12345": {
                    "health_status": "Healthy",
                    "lifecycle_state": "InService",
                    "launch_template": {"LaunchTemplateId": "lt-123"},
                }
            },
        }

        assert _is_instance_using_launch_config("i-12345", props) is False

    def test_instance_without_launch_spec(self):
        """Test that instance without any launch spec returns False."""
        props = {
            "launch_config_name": "my-lc-v1",
            "instance_facts": {
                "i-12345": {
                    "health_status": "Healthy",
                    "lifecycle_state": "InService",
                }
            },
        }

        assert _is_instance_using_launch_config("i-12345", props) is False


class TestIsInstanceUsingLaunchTemplate:
    """Test suite for _is_instance_using_launch_template function."""

    def test_instance_with_matching_launch_template(self):
        """Test that instance with matching launch template returns True."""
        lt_spec = {"LaunchTemplateId": "lt-123", "Version": "1"}
        props = {
            "launch_template": lt_spec,
            "instance_facts": {
                "i-12345": {
                    "health_status": "Healthy",
                    "lifecycle_state": "InService",
                    "launch_template": lt_spec,
                }
            },
        }

        assert _is_instance_using_launch_template("i-12345", props) is True

    def test_instance_with_different_launch_template(self):
        """Test that instance with different launch template returns False."""
        props = {
            "launch_template": {"LaunchTemplateId": "lt-456", "Version": "2"},
            "instance_facts": {
                "i-12345": {
                    "health_status": "Healthy",
                    "lifecycle_state": "InService",
                    "launch_template": {"LaunchTemplateId": "lt-123", "Version": "1"},
                }
            },
        }

        assert _is_instance_using_launch_template("i-12345", props) is False

    def test_instance_with_launch_config_instead(self):
        """Test that instance with launch config instead of template returns False."""
        props = {
            "launch_template": {"LaunchTemplateId": "lt-123", "Version": "1"},
            "instance_facts": {
                "i-12345": {
                    "health_status": "Healthy",
                    "lifecycle_state": "InService",
                    "launch_config_name": "my-lc-v1",
                }
            },
        }

        assert _is_instance_using_launch_template("i-12345", props) is False

    def test_instance_without_launch_spec(self):
        """Test that instance without any launch spec returns False."""
        props = {
            "launch_template": {"LaunchTemplateId": "lt-123", "Version": "1"},
            "instance_facts": {
                "i-12345": {
                    "health_status": "Healthy",
                    "lifecycle_state": "InService",
                }
            },
        }

        assert _is_instance_using_launch_template("i-12345", props) is False


class TestShouldTerminateInstanceForLaunchConfig:
    """Test suite for _should_terminate_instance_for_launch_config function."""

    def test_terminate_when_check_disabled_and_in_initial(self):
        """Test termination when lc_check=False and instance in initial list."""
        props = {
            "launch_config_name": "my-lc-v1",
            "instance_facts": {
                "i-12345": {
                    "launch_config_name": "my-lc-v1",
                }
            },
        }

        assert _should_terminate_instance_for_launch_config("i-12345", props, False, ["i-12345"]) is True

    def test_keep_when_check_disabled_and_not_in_initial(self):
        """Test keeping when lc_check=False and instance not in initial list."""
        props = {
            "launch_config_name": "my-lc-v1",
            "instance_facts": {
                "i-12345": {
                    "launch_config_name": "my-lc-v1",
                }
            },
        }

        assert _should_terminate_instance_for_launch_config("i-12345", props, False, ["i-67890"]) is False

    def test_terminate_when_has_launch_template(self):
        """Test termination when migrating from launch template to launch config."""
        props = {
            "launch_config_name": "my-lc-v1",
            "instance_facts": {
                "i-12345": {
                    "launch_template": {"LaunchTemplateId": "lt-123"},
                }
            },
        }

        assert _should_terminate_instance_for_launch_config("i-12345", props, True, []) is True

    def test_terminate_when_different_launch_config(self):
        """Test termination when instance has different launch config."""
        props = {
            "launch_config_name": "my-lc-v2",
            "instance_facts": {
                "i-12345": {
                    "launch_config_name": "my-lc-v1",
                }
            },
        }

        assert _should_terminate_instance_for_launch_config("i-12345", props, True, []) is True

    def test_keep_when_matching_launch_config(self):
        """Test keeping when instance has matching launch config."""
        props = {
            "launch_config_name": "my-lc-v1",
            "instance_facts": {
                "i-12345": {
                    "launch_config_name": "my-lc-v1",
                }
            },
        }

        assert _should_terminate_instance_for_launch_config("i-12345", props, True, []) is False


class TestShouldTerminateInstanceForLaunchTemplate:
    """Test suite for _should_terminate_instance_for_launch_template function."""

    def test_terminate_when_check_disabled_and_in_initial(self):
        """Test termination when lt_check=False and instance in initial list."""
        props = {
            "launch_template": {"LaunchTemplateId": "lt-123", "Version": "1"},
            "instance_facts": {
                "i-12345": {
                    "launch_template": {"LaunchTemplateId": "lt-123", "Version": "1"},
                }
            },
        }

        assert _should_terminate_instance_for_launch_template("i-12345", props, False, ["i-12345"]) is True

    def test_keep_when_check_disabled_and_not_in_initial(self):
        """Test keeping when lt_check=False and instance not in initial list."""
        props = {
            "launch_template": {"LaunchTemplateId": "lt-123", "Version": "1"},
            "instance_facts": {
                "i-12345": {
                    "launch_template": {"LaunchTemplateId": "lt-123", "Version": "1"},
                }
            },
        }

        assert _should_terminate_instance_for_launch_template("i-12345", props, False, ["i-67890"]) is False

    def test_terminate_when_has_launch_config(self):
        """Test termination when migrating from launch config to launch template."""
        props = {
            "launch_template": {"LaunchTemplateId": "lt-123", "Version": "1"},
            "instance_facts": {
                "i-12345": {
                    "launch_config_name": "my-lc-v1",
                }
            },
        }

        assert _should_terminate_instance_for_launch_template("i-12345", props, True, []) is True

    def test_terminate_when_different_launch_template(self):
        """Test termination when instance has different launch template."""
        props = {
            "launch_template": {"LaunchTemplateId": "lt-456", "Version": "2"},
            "instance_facts": {
                "i-12345": {
                    "launch_template": {"LaunchTemplateId": "lt-123", "Version": "1"},
                }
            },
        }

        assert _should_terminate_instance_for_launch_template("i-12345", props, True, []) is True

    def test_keep_when_matching_launch_template(self):
        """Test keeping when instance has matching launch template."""
        lt_spec = {"LaunchTemplateId": "lt-123", "Version": "1"}
        props = {
            "launch_template": lt_spec,
            "instance_facts": {
                "i-12345": {
                    "launch_template": lt_spec,
                }
            },
        }

        assert _should_terminate_instance_for_launch_template("i-12345", props, True, []) is False
