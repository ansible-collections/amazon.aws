# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import copy

try:
    import botocore.waiter as core_waiter
except ImportError:
    pass  # caught by HAS_BOTO3

import ansible_collections.amazon.aws.plugins.module_utils.core as aws_core


ec2_data = {
    "version": 2,
    "waiters": {
        "ImageAvailable": {
            "operation": "DescribeImages",
            "maxAttempts": 80,
            "delay": 15,
            "acceptors": [
                {
                    "state": "success",
                    "matcher": "pathAll",
                    "argument": "Images[].State",
                    "expected": "available"
                },
                {
                    "state": "failure",
                    "matcher": "pathAny",
                    "argument": "Images[].State",
                    "expected": "failed"
                }
            ]
        },
        "InternetGatewayExists": {
            "delay": 5,
            "maxAttempts": 40,
            "operation": "DescribeInternetGateways",
            "acceptors": [
                {
                    "matcher": "path",
                    "expected": True,
                    "argument": "length(InternetGateways) > `0`",
                    "state": "success"
                },
                {
                    "matcher": "error",
                    "expected": "InvalidInternetGatewayID.NotFound",
                    "state": "retry"
                },
            ]
        },
        "NetworkInterfaceAttached": {
            "operation": "DescribeNetworkInterfaces",
            "delay": 5,
            "maxAttempts": 40,
            "acceptors": [
                {
                    "expected": "attached",
                    "matcher": "pathAll",
                    "state": "success",
                    "argument": "NetworkInterfaces[].Attachment.Status"
                },
                {
                    "expected": "InvalidNetworkInterfaceID.NotFound",
                    "matcher": "error",
                    "state": "failure"
                },
            ]
        },
        "NetworkInterfaceAvailable": {
            "operation": "DescribeNetworkInterfaces",
            "delay": 5,
            "maxAttempts": 40,
            "acceptors": [
                {
                    "expected": "available",
                    "matcher": "pathAll",
                    "state": "success",
                    "argument": "NetworkInterfaces[].Status"
                },
                {
                    "expected": "InvalidNetworkInterfaceID.NotFound",
                    "matcher": "error",
                    "state": "retry"
                },
            ]
        },
        "NetworkInterfaceDeleteOnTerminate": {
            "operation": "DescribeNetworkInterfaces",
            "delay": 5,
            "maxAttempts": 10,
            "acceptors": [
                {
                    "expected": True,
                    "matcher": "pathAll",
                    "state": "success",
                    "argument": "NetworkInterfaces[].Attachment.DeleteOnTermination"
                },
                {
                    "expected": "InvalidNetworkInterfaceID.NotFound",
                    "matcher": "error",
                    "state": "failure"
                },
            ]
        },
        "NetworkInterfaceNoDeleteOnTerminate": {
            "operation": "DescribeNetworkInterfaces",
            "delay": 5,
            "maxAttempts": 10,
            "acceptors": [
                {
                    "expected": False,
                    "matcher": "pathAll",
                    "state": "success",
                    "argument": "NetworkInterfaces[].Attachment.DeleteOnTermination"
                },
                {
                    "expected": "InvalidNetworkInterfaceID.NotFound",
                    "matcher": "error",
                    "state": "failure"
                },
            ]
        },
        "RouteTableExists": {
            "delay": 5,
            "maxAttempts": 40,
            "operation": "DescribeRouteTables",
            "acceptors": [
                {
                    "matcher": "path",
                    "expected": True,
                    "argument": "length(RouteTables[]) > `0`",
                    "state": "success"
                },
                {
                    "matcher": "error",
                    "expected": "InvalidRouteTableID.NotFound",
                    "state": "retry"
                },
            ]
        },
        "SecurityGroupExists": {
            "delay": 5,
            "maxAttempts": 40,
            "operation": "DescribeSecurityGroups",
            "acceptors": [
                {
                    "matcher": "path",
                    "expected": True,
                    "argument": "length(SecurityGroups[]) > `0`",
                    "state": "success"
                },
                {
                    "matcher": "error",
                    "expected": "InvalidGroup.NotFound",
                    "state": "retry"
                },
            ]
        },
        "SubnetAvailable": {
            "delay": 15,
            "operation": "DescribeSubnets",
            "maxAttempts": 40,
            "acceptors": [
                {
                    "expected": "available",
                    "matcher": "pathAll",
                    "state": "success",
                    "argument": "Subnets[].State"
                }
            ]
        },
        "SubnetExists": {
            "delay": 5,
            "maxAttempts": 40,
            "operation": "DescribeSubnets",
            "acceptors": [
                {
                    "matcher": "path",
                    "expected": True,
                    "argument": "length(Subnets[]) > `0`",
                    "state": "success"
                },
                {
                    "matcher": "error",
                    "expected": "InvalidSubnetID.NotFound",
                    "state": "retry"
                },
            ]
        },
        "SubnetHasMapPublic": {
            "delay": 5,
            "maxAttempts": 40,
            "operation": "DescribeSubnets",
            "acceptors": [
                {
                    "matcher": "pathAll",
                    "expected": True,
                    "argument": "Subnets[].MapPublicIpOnLaunch",
                    "state": "success"
                },
            ]
        },
        "SubnetNoMapPublic": {
            "delay": 5,
            "maxAttempts": 40,
            "operation": "DescribeSubnets",
            "acceptors": [
                {
                    "matcher": "pathAll",
                    "expected": False,
                    "argument": "Subnets[].MapPublicIpOnLaunch",
                    "state": "success"
                },
            ]
        },
        "SubnetHasAssignIpv6": {
            "delay": 5,
            "maxAttempts": 40,
            "operation": "DescribeSubnets",
            "acceptors": [
                {
                    "matcher": "pathAll",
                    "expected": True,
                    "argument": "Subnets[].AssignIpv6AddressOnCreation",
                    "state": "success"
                },
            ]
        },
        "SubnetNoAssignIpv6": {
            "delay": 5,
            "maxAttempts": 40,
            "operation": "DescribeSubnets",
            "acceptors": [
                {
                    "matcher": "pathAll",
                    "expected": False,
                    "argument": "Subnets[].AssignIpv6AddressOnCreation",
                    "state": "success"
                },
            ]
        },
        "SubnetDeleted": {
            "delay": 5,
            "maxAttempts": 40,
            "operation": "DescribeSubnets",
            "acceptors": [
                {
                    "matcher": "path",
                    "expected": True,
                    "argument": "length(Subnets[]) > `0`",
                    "state": "retry"
                },
                {
                    "matcher": "error",
                    "expected": "InvalidSubnetID.NotFound",
                    "state": "success"
                },
            ]
        },
        "VpcAvailable": {
            "delay": 15,
            "operation": "DescribeVpcs",
            "maxAttempts": 40,
            "acceptors": [
                {
                    "expected": "available",
                    "matcher": "pathAll",
                    "state": "success",
                    "argument": "Vpcs[].State"
                }
            ]
        },
        "VpcExists": {
            "operation": "DescribeVpcs",
            "delay": 1,
            "maxAttempts": 5,
            "acceptors": [
                {
                    "matcher": "status",
                    "expected": 200,
                    "state": "success"
                },
                {
                    "matcher": "error",
                    "expected": "InvalidVpcID.NotFound",
                    "state": "retry"
                }
            ]
        },
        "VpcEndpointExists": {
            "delay": 5,
            "maxAttempts": 40,
            "operation": "DescribeVpcEndpoints",
            "acceptors": [
                {
                    "matcher": "path",
                    "expected": True,
                    "argument": "length(VpcEndpoints[]) > `0`",
                    "state": "success"
                },
                {
                    "matcher": "error",
                    "expected": "InvalidVpcEndpointId.NotFound",
                    "state": "retry"
                },
            ]
        },
        "VpnGatewayExists": {
            "delay": 5,
            "maxAttempts": 40,
            "operation": "DescribeVpnGateways",
            "acceptors": [
                {
                    "matcher": "path",
                    "expected": True,
                    "argument": "length(VpnGateways[]) > `0`",
                    "state": "success"
                },
                {
                    "matcher": "error",
                    "expected": "InvalidVpnGatewayID.NotFound",
                    "state": "retry"
                },
            ]
        },
        "VpnGatewayDetached": {
            "delay": 5,
            "maxAttempts": 40,
            "operation": "DescribeVpnGateways",
            "acceptors": [
                {
                    "matcher": "path",
                    "expected": True,
                    "argument": "VpnGateways[0].State == 'available'",
                    "state": "success"
                },
            ]
        },
        "NatGatewayDeleted": {
            "delay": 5,
            "maxAttempts": 40,
            "operation": "DescribeNatGateways",
            "acceptors": [
                {
                    "state": "success",
                    "matcher": "pathAll",
                    "expected": "deleted",
                    "argument": "NatGateways[].State"
                },
                {
                    "state": "success",
                    "matcher": "error",
                    "expected": "NatGatewayNotFound"
                }
            ]
        },
        "NatGatewayAvailable": {
            "delay": 5,
            "maxAttempts": 40,
            "operation": "DescribeNatGateways",
            "acceptors": [
                {
                    "state": "success",
                    "matcher": "pathAll",
                    "expected": "available",
                    "argument": "NatGateways[].State"
                },
                {
                    "state": "retry",
                    "matcher": "error",
                    "expected": "NatGatewayNotFound"
                }
            ]
        },
    }
}


waf_data = {
    "version": 2,
    "waiters": {
        "ChangeTokenInSync": {
            "delay": 20,
            "maxAttempts": 60,
            "operation": "GetChangeTokenStatus",
            "acceptors": [
                {
                    "matcher": "path",
                    "expected": True,
                    "argument": "ChangeTokenStatus == 'INSYNC'",
                    "state": "success"
                },
                {
                    "matcher": "error",
                    "expected": "WAFInternalErrorException",
                    "state": "retry"
                }
            ]
        }
    }
}

eks_data = {
    "version": 2,
    "waiters": {
        "ClusterActive": {
            "delay": 20,
            "maxAttempts": 60,
            "operation": "DescribeCluster",
            "acceptors": [
                {
                    "state": "success",
                    "matcher": "path",
                    "argument": "cluster.status",
                    "expected": "ACTIVE"
                },
                {
                    "state": "retry",
                    "matcher": "error",
                    "expected": "ResourceNotFoundException"
                }
            ]
        },
        "ClusterDeleted": {
            "delay": 20,
            "maxAttempts": 60,
            "operation": "DescribeCluster",
            "acceptors": [
                {
                    "state": "retry",
                    "matcher": "path",
                    "argument": "cluster.status != 'DELETED'",
                    "expected": True
                },
                {
                    "state": "success",
                    "matcher": "error",
                    "expected": "ResourceNotFoundException"
                }
            ]
        }
    }
}


rds_data = {
    "version": 2,
    "waiters": {
        "DBInstanceStopped": {
            "delay": 20,
            "maxAttempts": 60,
            "operation": "DescribeDBInstances",
            "acceptors": [
                {
                    "state": "success",
                    "matcher": "pathAll",
                    "argument": "DBInstances[].DBInstanceStatus",
                    "expected": "stopped"
                },
            ]
        }
    }
}


def _inject_limit_retries(model):

    extra_retries = [
        'RequestLimitExceeded', 'Unavailable', 'ServiceUnavailable',
        'InternalFailure', 'InternalError', 'TooManyRequestsException',
        'Throttling']

    acceptors = []
    for error in extra_retries:
        acceptors.append({"state": "success", "matcher": "error", "expected": error})

    _model = copy.deepcopy(model)

    for waiter in model["waiters"]:
        _model["waiters"][waiter]["acceptors"].extend(acceptors)

    return _model


def ec2_model(name):
    ec2_models = core_waiter.WaiterModel(waiter_config=_inject_limit_retries(ec2_data))
    return ec2_models.get_waiter(name)


def waf_model(name):
    waf_models = core_waiter.WaiterModel(waiter_config=_inject_limit_retries(waf_data))
    return waf_models.get_waiter(name)


def eks_model(name):
    eks_models = core_waiter.WaiterModel(waiter_config=_inject_limit_retries(eks_data))
    return eks_models.get_waiter(name)


def rds_model(name):
    rds_models = core_waiter.WaiterModel(waiter_config=_inject_limit_retries(rds_data))
    return rds_models.get_waiter(name)


waiters_by_name = {
    ('EC2', 'image_available'): lambda ec2: core_waiter.Waiter(
        'image_available',
        ec2_model('ImageAvailable'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_images
        )),
    ('EC2', 'internet_gateway_exists'): lambda ec2: core_waiter.Waiter(
        'internet_gateway_exists',
        ec2_model('InternetGatewayExists'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_internet_gateways
        )),
    ('EC2', 'network_interface_attached'): lambda ec2: core_waiter.Waiter(
        'network_interface_attached',
        ec2_model('NetworkInterfaceAttached'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_network_interfaces
        )),
    ('EC2', 'network_interface_available'): lambda ec2: core_waiter.Waiter(
        'network_interface_available',
        ec2_model('NetworkInterfaceAvailable'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_network_interfaces
        )),
    ('EC2', 'network_interface_delete_on_terminate'): lambda ec2: core_waiter.Waiter(
        'network_interface_delete_on_terminate',
        ec2_model('NetworkInterfaceDeleteOnTerminate'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_network_interfaces
        )),
    ('EC2', 'network_interface_no_delete_on_terminate'): lambda ec2: core_waiter.Waiter(
        'network_interface_no_delete_on_terminate',
        ec2_model('NetworkInterfaceNoDeleteOnTerminate'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_network_interfaces
        )),
    ('EC2', 'route_table_exists'): lambda ec2: core_waiter.Waiter(
        'route_table_exists',
        ec2_model('RouteTableExists'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_route_tables
        )),
    ('EC2', 'security_group_exists'): lambda ec2: core_waiter.Waiter(
        'security_group_exists',
        ec2_model('SecurityGroupExists'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_security_groups
        )),
    ('EC2', 'subnet_available'): lambda ec2: core_waiter.Waiter(
        'subnet_available',
        ec2_model('SubnetAvailable'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_subnets
        )),
    ('EC2', 'subnet_exists'): lambda ec2: core_waiter.Waiter(
        'subnet_exists',
        ec2_model('SubnetExists'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_subnets
        )),
    ('EC2', 'subnet_has_map_public'): lambda ec2: core_waiter.Waiter(
        'subnet_has_map_public',
        ec2_model('SubnetHasMapPublic'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_subnets
        )),
    ('EC2', 'subnet_no_map_public'): lambda ec2: core_waiter.Waiter(
        'subnet_no_map_public',
        ec2_model('SubnetNoMapPublic'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_subnets
        )),
    ('EC2', 'subnet_has_assign_ipv6'): lambda ec2: core_waiter.Waiter(
        'subnet_has_assign_ipv6',
        ec2_model('SubnetHasAssignIpv6'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_subnets
        )),
    ('EC2', 'subnet_no_assign_ipv6'): lambda ec2: core_waiter.Waiter(
        'subnet_no_assign_ipv6',
        ec2_model('SubnetNoAssignIpv6'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_subnets
        )),
    ('EC2', 'subnet_deleted'): lambda ec2: core_waiter.Waiter(
        'subnet_deleted',
        ec2_model('SubnetDeleted'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_subnets
        )),
    ('EC2', 'vpc_available'): lambda ec2: core_waiter.Waiter(
        'vpc_available',
        ec2_model('VpcAvailable'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_vpcs
        )),
    ('EC2', 'vpc_exists'): lambda ec2: core_waiter.Waiter(
        'vpc_exists',
        ec2_model('VpcExists'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_vpcs
        )),
    ('EC2', 'vpc_endpoint_exists'): lambda ec2: core_waiter.Waiter(
        'vpc_endpoint_exists',
        ec2_model('VpcEndpointExists'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_vpc_endpoints
        )),
    ('EC2', 'vpn_gateway_exists'): lambda ec2: core_waiter.Waiter(
        'vpn_gateway_exists',
        ec2_model('VpnGatewayExists'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_vpn_gateways
        )),
    ('EC2', 'vpn_gateway_detached'): lambda ec2: core_waiter.Waiter(
        'vpn_gateway_detached',
        ec2_model('VpnGatewayDetached'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_vpn_gateways
        )),
    ('EC2', 'nat_gateway_deleted'): lambda ec2: core_waiter.Waiter(
        'nat_gateway_deleted',
        ec2_model('NatGatewayDeleted'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_nat_gateways
        )),
    ('EC2', 'nat_gateway_available'): lambda ec2: core_waiter.Waiter(
        'nat_gateway_available',
        ec2_model('NatGatewayAvailable'),
        core_waiter.NormalizedOperationMethod(
            ec2.describe_nat_gateways
        )),
    ('WAF', 'change_token_in_sync'): lambda waf: core_waiter.Waiter(
        'change_token_in_sync',
        waf_model('ChangeTokenInSync'),
        core_waiter.NormalizedOperationMethod(
            waf.get_change_token_status
        )),
    ('WAFRegional', 'change_token_in_sync'): lambda waf: core_waiter.Waiter(
        'change_token_in_sync',
        waf_model('ChangeTokenInSync'),
        core_waiter.NormalizedOperationMethod(
            waf.get_change_token_status
        )),
    ('EKS', 'cluster_active'): lambda eks: core_waiter.Waiter(
        'cluster_active',
        eks_model('ClusterActive'),
        core_waiter.NormalizedOperationMethod(
            eks.describe_cluster
        )),
    ('EKS', 'cluster_deleted'): lambda eks: core_waiter.Waiter(
        'cluster_deleted',
        eks_model('ClusterDeleted'),
        core_waiter.NormalizedOperationMethod(
            eks.describe_cluster
        )),
    ('RDS', 'db_instance_stopped'): lambda rds: core_waiter.Waiter(
        'db_instance_stopped',
        rds_model('DBInstanceStopped'),
        core_waiter.NormalizedOperationMethod(
            rds.describe_db_instances
        )),
}


def get_waiter(client, waiter_name):
    if isinstance(client, aws_core._RetryingBotoClientWrapper):
        return get_waiter(client.client, waiter_name)
    try:
        return waiters_by_name[(client.__class__.__name__, waiter_name)](client)
    except KeyError:
        raise NotImplementedError("Waiter {0} could not be found for client {1}. Available waiters: {2}".format(
            waiter_name, type(client), ', '.join(repr(k) for k in waiters_by_name.keys())))
