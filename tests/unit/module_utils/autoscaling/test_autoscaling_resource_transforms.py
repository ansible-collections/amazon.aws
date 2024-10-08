# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.amazon.aws.plugins.module_utils._autoscaling.transformations import (
    normalize_autoscaling_instances,
)

# The various normalize_ functions are based upon ..transformation.boto3_resource_to_ansible_dict
# As such these tests will be relatively light touch.


class TestAutoScalingResourceToAnsibleDict:
    def setup_method(self):
        pass

    def test_normalize_autoscaling_instances(self):
        INPUT = [
            {
                "AvailabilityZone": "us-east-1a",
                "HealthStatus": "UNHEALTHY",
                "InstanceId": "i-123456789abcdef12",
                "InstanceType": "t3.small",
                "LaunchConfigurationName": "ansible-test-lc-2",
                "LifecycleState": "Standby",
                "ProtectedFromScaleIn": True,
            },
            {
                "AutoScalingGroupName": "ansible-test-asg",
                "AvailabilityZone": "us-east-1a",
                "HealthStatus": "Healthy",
                "InstanceId": "i-0123456789abcdef0",
                "InstanceType": "t3.micro",
                "LaunchConfigurationName": "ansible-test-lc",
                "LifecycleState": "InService",
                "ProtectedFromScaleIn": False,
            },
        ]
        OUTPUT = [
            {
                "auto_scaling_group_name": "ansible-test-asg",
                "availability_zone": "us-east-1a",
                "health_status": "HEALTHY",
                "instance_id": "i-0123456789abcdef0",
                "instance_type": "t3.micro",
                "launch_configuration_name": "ansible-test-lc",
                "lifecycle_state": "InService",
                "protected_from_scale_in": False,
            },
            {
                "availability_zone": "us-east-1a",
                "health_status": "UNHEALTHY",
                "instance_id": "i-123456789abcdef12",
                "instance_type": "t3.small",
                "launch_configuration_name": "ansible-test-lc-2",
                "lifecycle_state": "Standby",
                "protected_from_scale_in": True,
            },
        ]

        assert OUTPUT == normalize_autoscaling_instances(INPUT)

    def test_normalize_autoscaling_instances_with_group(self):
        INPUT = [
            {
                "AvailabilityZone": "us-east-1a",
                "HealthStatus": "Unhealthy",
                "InstanceId": "i-123456789abcdef12",
                "InstanceType": "t3.small",
                "LaunchConfigurationName": "ansible-test-lc-2",
                "LifecycleState": "Standby",
                "ProtectedFromScaleIn": True,
            },
            {
                "AutoScalingGroupName": "ansible-test-asg",
                "AvailabilityZone": "us-east-1a",
                "HealthStatus": "HEALTHY",
                "InstanceId": "i-0123456789abcdef0",
                "InstanceType": "t3.micro",
                "LaunchConfigurationName": "ansible-test-lc",
                "LifecycleState": "InService",
                "ProtectedFromScaleIn": False,
            },
        ]
        OUTPUT = [
            {
                "auto_scaling_group_name": "ansible-test-asg",
                "availability_zone": "us-east-1a",
                "health_status": "HEALTHY",
                "instance_id": "i-0123456789abcdef0",
                "instance_type": "t3.micro",
                "launch_configuration_name": "ansible-test-lc",
                "lifecycle_state": "InService",
                "protected_from_scale_in": False,
            },
            {
                "auto_scaling_group_name": "ansible-test-asg-2",
                "availability_zone": "us-east-1a",
                "health_status": "UNHEALTHY",
                "instance_id": "i-123456789abcdef12",
                "instance_type": "t3.small",
                "launch_configuration_name": "ansible-test-lc-2",
                "lifecycle_state": "Standby",
                "protected_from_scale_in": True,
            },
        ]

        assert OUTPUT == normalize_autoscaling_instances(INPUT, "ansible-test-asg-2")
