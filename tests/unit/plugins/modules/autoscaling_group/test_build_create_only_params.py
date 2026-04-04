# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import ansible_collections.amazon.aws.plugins.modules.autoscaling_group as asg_module


class TestBuildCreateOnlyParams:
    def test_tags_only(self):
        """Test with only tags (minimal create params)"""
        tags = [
            {
                "Key": "Name",
                "Value": "test-instance",
                "PropagateAtLaunch": True,
                "ResourceType": "auto-scaling-group",
                "ResourceId": "test-asg",
            }
        ]
        result = asg_module.build_create_only_params(tags=tags)

        assert result == {"Tags": tags}
        assert "PlacementGroup" not in result
        assert "LoadBalancerNames" not in result
        assert "TargetGroupARNs" not in result

    def test_with_placement_group(self):
        """Test with placement group"""
        tags = [{"Key": "Environment", "Value": "production"}]
        result = asg_module.build_create_only_params(tags=tags, placement_group="my-cluster")

        assert result["Tags"] == tags
        assert result["PlacementGroup"] == "my-cluster"

    def test_with_load_balancers(self):
        """Test with classic load balancers"""
        tags = []
        load_balancers = ["elb-1", "elb-2"]
        result = asg_module.build_create_only_params(tags=tags, load_balancers=load_balancers)

        assert result["Tags"] == tags
        assert result["LoadBalancerNames"] == ["elb-1", "elb-2"]
        assert "TargetGroupARNs" not in result

    def test_with_target_group_arns(self):
        """Test with target group ARNs"""
        tags = []
        target_group_arns = [
            "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/my-targets/50dc6c495c0c9188",
            "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/other-targets/73e2d6bc24d8a067",
        ]
        result = asg_module.build_create_only_params(tags=tags, target_group_arns=target_group_arns)

        assert result["Tags"] == tags
        assert result["TargetGroupARNs"] == target_group_arns
        assert "LoadBalancerNames" not in result

    def test_with_all_params(self):
        """Test with all create-only parameters"""
        tags = [
            {"Key": "Name", "Value": "web-server"},
            {"Key": "Environment", "Value": "production"},
        ]
        placement_group = "cluster-1"
        load_balancers = ["classic-elb"]
        target_group_arns = ["arn:aws:elasticloadbalancing:region:account:targetgroup/name/id"]

        result = asg_module.build_create_only_params(
            tags=tags,
            placement_group=placement_group,
            load_balancers=load_balancers,
            target_group_arns=target_group_arns,
        )

        assert result["Tags"] == tags
        assert result["PlacementGroup"] == "cluster-1"
        assert result["LoadBalancerNames"] == ["classic-elb"]
        assert result["TargetGroupARNs"] == ["arn:aws:elasticloadbalancing:region:account:targetgroup/name/id"]

    def test_empty_tags_list(self):
        """Test with empty tags list"""
        result = asg_module.build_create_only_params(tags=[])

        assert result == {"Tags": []}

    def test_none_optional_params(self):
        """Test that None values don't add keys to result"""
        tags = [{"Key": "Test", "Value": "value"}]
        result = asg_module.build_create_only_params(
            tags=tags, placement_group=None, load_balancers=None, target_group_arns=None
        )

        assert result == {"Tags": tags}
        assert "PlacementGroup" not in result
        assert "LoadBalancerNames" not in result
        assert "TargetGroupARNs" not in result

    def test_empty_load_balancers_list(self):
        """Test with empty load balancers list (should not include key)"""
        tags = []
        result = asg_module.build_create_only_params(tags=tags, load_balancers=[])

        assert result == {"Tags": []}
        assert "LoadBalancerNames" not in result

    def test_empty_target_group_arns_list(self):
        """Test with empty target group ARNs list (should not include key)"""
        tags = []
        result = asg_module.build_create_only_params(tags=tags, target_group_arns=[])

        assert result == {"Tags": []}
        assert "TargetGroupARNs" not in result

    def test_multiple_load_balancers(self):
        """Test with multiple load balancers"""
        tags = []
        load_balancers = ["elb-web-1", "elb-web-2", "elb-app-1"]
        result = asg_module.build_create_only_params(tags=tags, load_balancers=load_balancers)

        assert result["LoadBalancerNames"] == ["elb-web-1", "elb-web-2", "elb-app-1"]
