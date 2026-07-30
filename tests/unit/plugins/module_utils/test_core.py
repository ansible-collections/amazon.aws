# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class TestCoreCompatibility:
    """Test suite for core.py backwards-compatibility re-exports."""

    def test_compatibility_exports_exist(self):
        """Verify all compatibility re-exports are present."""
        from ansible_collections.amazon.aws.plugins.module_utils import core

        # Verify all re-exported names are present
        assert hasattr(core, "parse_aws_arn")
        assert hasattr(core, "HAS_BOTO3")
        assert hasattr(core, "get_boto3_client_method_parameters")
        assert hasattr(core, "is_boto3_error_code")
        assert hasattr(core, "is_boto3_error_message")
        assert hasattr(core, "normalize_boto3_result")
        assert hasattr(core, "AnsibleAWSError")
        assert hasattr(core, "AnsibleAWSModule")
        assert hasattr(core, "scrub_none_parameters")

    def test_all_export(self):
        """Test that __all__ is defined."""
        from ansible_collections.amazon.aws.plugins.module_utils import core

        assert hasattr(core, "__all__")
