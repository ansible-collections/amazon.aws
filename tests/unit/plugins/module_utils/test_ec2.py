# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class TestEc2Compatibility:
    """Test suite for ec2.py backwards-compatibility re-exports."""

    def test_compatibility_exports_exist(self):
        """Verify all compatibility re-exports are present."""
        from ansible_collections.amazon.aws.plugins.module_utils import ec2

        # Re-exports from ansible.module_utils.common.dict_transformations
        assert hasattr(ec2, "_camel_to_snake")
        assert hasattr(ec2, "_snake_to_camel")
        assert hasattr(ec2, "camel_dict_to_snake_dict")
        assert hasattr(ec2, "snake_dict_to_camel_dict")

        # Re-exports from botocore module_utils
        assert hasattr(ec2, "HAS_BOTO3")
        assert hasattr(ec2, "boto3_conn")
        assert hasattr(ec2, "boto3_inventory_conn")
        assert hasattr(ec2, "boto_exception")
        assert hasattr(ec2, "get_aws_connection_info")
        assert hasattr(ec2, "get_aws_region")

        # Re-exports from other module_utils
        assert hasattr(ec2, "is_outposts_arn")
        assert hasattr(ec2, "AnsibleAWSError")
        assert hasattr(ec2, "aws_common_argument_spec")
        assert hasattr(ec2, "ec2_argument_spec")
        assert hasattr(ec2, "py3cmp")
        assert hasattr(ec2, "compare_policies")
        assert hasattr(ec2, "AWSRetry")
        assert hasattr(ec2, "ansible_dict_to_boto3_tag_list")
        assert hasattr(ec2, "boto3_tag_list_to_ansible_dict")
        assert hasattr(ec2, "compare_aws_tags")
        assert hasattr(ec2, "ansible_dict_to_boto3_filter_list")
        assert hasattr(ec2, "map_complex_type")
