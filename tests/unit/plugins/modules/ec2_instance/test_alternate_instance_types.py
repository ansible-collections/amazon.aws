#!/usr/bin/env python3

"""
Test script to verify the alternate instance types functionality.
This script simulates the key parts of the retry logic.
"""

import copy
from unittest.mock import Mock, MagicMock

def simulate_run_instances(client, module, **instance_spec):
    """
    Simulate the run_instances function to test the retry logic.
    """
    
    # Mock the exceptions for testing
    def mock_is_ansible_aws_error_code(error_code):
        def decorator(exception):
            return exception.code == error_code
        return decorator
    
    def mock_is_ansible_aws_error_message(error_message):
        def decorator(exception):
            return error_message in str(exception)
        return decorator
    
    # Mock AWS exception
    class MockAWSError(Exception):
        def __init__(self, code, message):
            self.code = code
            self.message = message
            super().__init__(message)
    
    # Mock run_ec2_instances function
    def mock_run_ec2_instances(client, **spec):
        instance_type = spec.get("InstanceType")
        if instance_type == "t3.large":
            raise MockAWSError("InsufficientInstanceCapacity", "Insufficient capacity for t3.large")
        elif instance_type == "t3.medium":
            raise MockAWSError("InsufficientInstanceCapacity", "Insufficient capacity for t3.medium")
        elif instance_type == "t3.small":
            # This one succeeds
            return {"Instances": [{"InstanceId": "i-1234567890abcdef0", "InstanceType": "t3.small"}]}
        else:
            return {"Instances": [{"InstanceId": "i-1234567890abcdef0", "InstanceType": instance_type}]}
    
    # Get the primary instance type and alternate types
    primary_instance_type = instance_spec.get("InstanceType")
    alternate_instance_types = module.params.get("alternate_instance_types", [])
    
    # List of instance types to try (primary first, then alternates)
    instance_types_to_try = [primary_instance_type] if primary_instance_type else []
    if alternate_instance_types:
        instance_types_to_try.extend(alternate_instance_types)
    
    # If no instance types to try, fallback to original behavior
    if not instance_types_to_try:
        return mock_run_ec2_instances(client, **instance_spec)
    
    last_error = None
    
    for i, instance_type in enumerate(instance_types_to_try):
        # Create a copy of the instance spec with the current instance type
        current_spec = copy.deepcopy(instance_spec)
        current_spec["InstanceType"] = instance_type
        
        try:
            result = mock_run_ec2_instances(client, **current_spec)
            
            # If we successfully launched with an alternate instance type, log a message
            if i > 0:
                print(f"Successfully launched instance with alternate instance type '{instance_type}' "
                      f"after primary instance type '{primary_instance_type}' failed with InsufficientInstanceCapacity")
            
            return result
            
        except MockAWSError as e:
            if e.code == "InsufficientInstanceCapacity":
                last_error = e
                # If this is not the last instance type to try, continue to the next one
                if i < len(instance_types_to_try) - 1:
                    print(f"Instance type '{instance_type}' failed with InsufficientInstanceCapacity, trying next alternate")
                    continue
                else:
                    # This was the last instance type to try, re-raise the error
                    raise
            else:
                # For any other error, re-raise immediately
                raise
    
    # If we get here, all instance types failed with InsufficientInstanceCapacity
    raise last_error

# Test cases
def test_alternate_instance_types():
    print("Testing alternate instance types functionality...")
    
    # Test case 1: Primary instance type fails, alternate succeeds
    print("\nTest case 1: Primary fails, alternate succeeds")
    module = Mock()
    module.params = {
        "alternate_instance_types": ["t3.medium", "t3.small", "t2.micro"]
    }
    module.warn = Mock()
    
    instance_spec = {"InstanceType": "t3.large"}
    
    try:
        result = simulate_run_instances(None, module, **instance_spec)
        print("Success! Result:", result)
    except Exception as e:
        print("Failed:", e)
    
    # Test case 2: Primary instance type succeeds
    print("\nTest case 2: Primary succeeds")
    module = Mock()
    module.params = {
        "alternate_instance_types": ["t3.medium", "t3.small", "t2.micro"]
    }
    module.warn = Mock()
    
    instance_spec = {"InstanceType": "t2.micro"}
    
    try:
        result = simulate_run_instances(None, module, **instance_spec)
        print("Success! Result:", result)
    except Exception as e:
        print("Failed:", e)
    
    # Test case 3: All instance types fail
    print("\nTest case 3: All instance types fail")
    module = Mock()
    module.params = {
        "alternate_instance_types": ["t3.medium", "t3.large"]
    }
    module.warn = Mock()
    
    instance_spec = {"InstanceType": "t3.large"}
    
    try:
        result = simulate_run_instances(None, module, **instance_spec)
        print("Success! Result:", result)
    except Exception as e:
        print("Failed (expected):", e)

if __name__ == "__main__":
    test_alternate_instance_types()
