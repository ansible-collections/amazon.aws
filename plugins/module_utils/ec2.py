# -*- coding: utf-8 -*-

# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


"""
This module adds helper functions for various EC2 specific services.

It also includes a large number of imports for functions which historically
lived here.  Most of these functions were not specific to EC2, they ended
up in this module because "that's where the AWS code was" (originally).
"""

import copy
import re
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import ansible.module_utils.common.warnings as ansible_warnings
from ansible.module_utils.ansible_release import __version__

# Used to live here, moved into ansible.module_utils.common.dict_transformations
from ansible.module_utils.common.dict_transformations import _camel_to_snake  # pylint: disable=unused-import
from ansible.module_utils.common.dict_transformations import _snake_to_camel  # pylint: disable=unused-import
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict  # pylint: disable=unused-import
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict  # pylint: disable=unused-import
from ansible.module_utils.six import integer_types
from ansible.module_utils.six import string_types

# Used to live here, moved into ansible_collections.amazon.aws.plugins.module_utils.arn
from .arn import is_outpost_arn as is_outposts_arn  # pylint: disable=unused-import
from .arn import validate_aws_arn

# Used to live here, moved into ansible_collections.amazon.aws.plugins.module_utils.botocore
from .botocore import HAS_BOTO3  # pylint: disable=unused-import
from .botocore import boto3_conn  # pylint: disable=unused-import
from .botocore import boto3_inventory_conn  # pylint: disable=unused-import
from .botocore import boto_exception  # pylint: disable=unused-import
from .botocore import get_aws_connection_info  # pylint: disable=unused-import
from .botocore import get_aws_region  # pylint: disable=unused-import
from .botocore import is_boto3_error_code
from .botocore import paginated_query_with_retries
from .errors import AWSErrorHandler

# Used to live here, moved into ansible_collections.amazon.aws.plugins.module_utils.exceptions
from .exceptions import AnsibleAWSError  # pylint: disable=unused-import
from .iam import list_iam_instance_profiles

# Used to live here, moved into ansible_collections.amazon.aws.plugins.module_utils.modules
# The names have been changed in .modules to better reflect their applicability.
from .modules import _aws_common_argument_spec as aws_common_argument_spec  # pylint: disable=unused-import
from .modules import aws_argument_spec as ec2_argument_spec  # pylint: disable=unused-import

# Used to live here, moved into ansible_collections.amazon.aws.plugins.module_utils.policy
from .policy import _py3cmp as py3cmp  # pylint: disable=unused-import
from .policy import compare_policies  # pylint: disable=unused-import

# Used to live here, moved into ansible_collections.amazon.aws.plugins.module_utils.retries
from .retries import AWSRetry  # pylint: disable=unused-import

# Used to live here, moved into ansible_collections.amazon.aws.plugins.module_utils.tagging
from .tagging import ansible_dict_to_boto3_tag_list  # pylint: disable=unused-import
from .tagging import boto3_tag_list_to_ansible_dict  # pylint: disable=unused-import
from .tagging import boto3_tag_specifications
from .tagging import compare_aws_tags  # pylint: disable=unused-import

# Used to live here, moved into ansible_collections.amazon.aws.plugins.module_utils.transformation
from .transformation import ansible_dict_to_boto3_filter_list  # pylint: disable=unused-import
from .transformation import map_complex_type  # pylint: disable=unused-import

try:
    import botocore
except ImportError:
    pass  # Handled by HAS_BOTO3


class AnsibleEC2Error(AnsibleAWSError):
    pass


EC2TagSpecifications = Dict[str, Union[str, List[Dict[str, str]]]]


@AWSRetry.jittered_backoff()
def describe_availability_zones(
    client, **params: Dict[str, Union[List[str], bool, List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Union[str, List[Dict[str, str]]]]]:
    # The paginator does not exist for `describe_availability_zones()`
    return client.describe_availability_zones(**params)["AvailabilityZones"]


@AWSRetry.jittered_backoff()
def describe_regions(
    client, **params: Dict[str, Union[List[str], bool, List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, str]]:
    # The paginator does not exist for `describe_regions()`
    return client.describe_regions(**params)["Regions"]


# EC2 VPC Subnets
class EC2VpcSubnetErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidSubnetID.NotFound")


@EC2VpcSubnetErrorHandler.deletion_error_handler("delete subnet")
@AWSRetry.jittered_backoff()
def delete_subnet(client, subnet_id: str) -> bool:
    client.delete_subnet(SubnetId=subnet_id)
    return True


@EC2VpcSubnetErrorHandler.list_error_handler("describe subnets", [])
@AWSRetry.jittered_backoff()
def describe_subnets(
    client, **params: Dict[str, Union[List[str], bool, List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("describe_subnets")
    return paginator.paginate(**params).build_full_result()["Subnets"]


@EC2VpcSubnetErrorHandler.common_error_handler("create subnet")
@AWSRetry.jittered_backoff()
def create_subnet(client, **params: Dict[str, Union[str, bool, int, EC2TagSpecifications]]) -> Dict[str, Any]:
    return client.create_subnet(**params)["Subnet"]


@EC2VpcSubnetErrorHandler.common_error_handler("modify subnet")
@AWSRetry.jittered_backoff()
def modify_subnet_attribute(client, subnet_id: str, **params: Dict[str, Union[str, int, Dict[str, bool]]]) -> bool:
    client.modify_subnet_attribute(SubnetId=subnet_id, **params)
    return True


@EC2VpcSubnetErrorHandler.common_error_handler("disassociate subnet cidr block")
@AWSRetry.jittered_backoff()
def disassociate_subnet_cidr_block(client, association_id: str) -> Dict[str, Union[str, Dict[str, str]]]:
    return client.disassociate_subnet_cidr_block(AssociationId=association_id)["Ipv6CidrBlockAssociation"]


@EC2VpcSubnetErrorHandler.common_error_handler("associate subnet cidr block")
@AWSRetry.jittered_backoff()
def associate_subnet_cidr_block(
    client, subnet_id: str, **params: Dict[str, Union[str, int]]
) -> Dict[str, Union[str, Dict[str, str]]]:
    return client.associate_subnet_cidr_block(SubnetId=subnet_id, **params)["Ipv6CidrBlockAssociation"]


# EC2 VPC Route table
class EC2VpcRouteTableErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidRouteTableID.NotFound")


@EC2VpcRouteTableErrorHandler.list_error_handler("describe route tables", [])
@AWSRetry.jittered_backoff()
def describe_route_tables(
    client, **params: Dict[str, Union[List[str], bool, List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("describe_route_tables")
    return paginator.paginate(**params).build_full_result()["RouteTables"]


@EC2VpcRouteTableErrorHandler.common_error_handler("disassociate route table")
@AWSRetry.jittered_backoff()
def disassociate_route_table(client, association_id: str) -> bool:
    client.disassociate_route_table(AssociationId=association_id)
    return True


@EC2VpcRouteTableErrorHandler.common_error_handler("associate route table")
@AWSRetry.jittered_backoff()
def associate_route_table(
    client, route_table_id: str, **params: Dict[str, str]
) -> Dict[str, Union[str, Dict[str, str]]]:
    return client.associate_route_table(RouteTableId=route_table_id, **params)


@EC2VpcRouteTableErrorHandler.common_error_handler("enable vgw route propagation")
@AWSRetry.jittered_backoff()
def enable_vgw_route_propagation(client, gateway_id: str, route_table_id: str) -> bool:
    client.enable_vgw_route_propagation(RouteTableId=route_table_id, GatewayId=gateway_id)
    return True


@EC2VpcRouteTableErrorHandler.deletion_error_handler("delete route table")
@AWSRetry.jittered_backoff()
def delete_route_table(client, route_table_id: str) -> bool:
    client.delete_route_table(RouteTableId=route_table_id)
    return True


@EC2VpcRouteTableErrorHandler.common_error_handler("create route table")
@AWSRetry.jittered_backoff()
def create_route_table(client, vpc_id: str, tags: Optional[Dict[str, str]]) -> Dict[str, Any]:
    params = {"VpcId": vpc_id}
    if tags:
        params["TagSpecifications"] = boto3_tag_specifications(tags, types="route-table")
    return client.create_route_table(**params)["RouteTable"]


# EC2 VPC Route table Route
class EC2VpcRouteTableRouteErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidRoute.NotFound")


@EC2VpcRouteTableRouteErrorHandler.deletion_error_handler("delete route")
@AWSRetry.jittered_backoff()
def delete_route(client, route_table_id: str, **params: Dict[str, str]) -> bool:
    client.delete_route(RouteTableId=route_table_id, **params)
    return True


@EC2VpcRouteTableRouteErrorHandler.common_error_handler("replace route")
@AWSRetry.jittered_backoff()
def replace_route(client, route_table_id: str, **params: Dict[str, Union[str, bool]]) -> bool:
    client.replace_route(RouteTableId=route_table_id, **params)
    return True


@EC2VpcRouteTableRouteErrorHandler.common_error_handler("create route")
@AWSRetry.jittered_backoff()
def create_route(client, route_table_id: str, **params: Dict[str, str]) -> bool:
    return client.create_route(RouteTableId=route_table_id, **params)["Return"]


# EC2 VPC
class EC2VpcErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidVpcID.NotFound")


@EC2VpcErrorHandler.list_error_handler("describe vpcs", [])
@AWSRetry.jittered_backoff()
def describe_vpcs(
    client, **params: Dict[str, Union[List[str], bool, List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("describe_vpcs")
    return paginator.paginate(**params).build_full_result()["Vpcs"]


@EC2VpcErrorHandler.deletion_error_handler("delete vpc")
@AWSRetry.jittered_backoff()
def delete_vpc(client, vpc_id: str) -> bool:
    client.delete_vpc(VpcId=vpc_id)
    return True


@EC2VpcErrorHandler.common_error_handler("describe vpc attribute")
@AWSRetry.jittered_backoff()
def describe_vpc_attribute(client, vpc_id: str, attribute: str) -> Dict[str, Any]:
    # The paginator does not exist for `describe_vpc_attribute`
    return client.describe_vpc_attribute(VpcId=vpc_id, Attribute=attribute)


@EC2VpcErrorHandler.common_error_handler("modify vpc attribute")
@AWSRetry.jittered_backoff()
def modify_vpc_attribute(client, vpc_id: str, **params: Dict[str, Union[str, Dict[str, bool]]]) -> bool:
    client.modify_vpc_attribute(VpcId=vpc_id, **params)
    return True


@EC2VpcErrorHandler.common_error_handler("create vpc")
@AWSRetry.jittered_backoff()
def create_vpc(client, **params: Dict[str, Union[str, bool, int, EC2TagSpecifications]]) -> Dict[str, Any]:
    return client.create_vpc(**params)["Vpc"]


@EC2VpcErrorHandler.common_error_handler("associate vpc cidr block")
@AWSRetry.jittered_backoff()
def associate_vpc_cidr_block(client, vpc_id: str, **params: Dict[str, Union[str, bool, int]]) -> Dict[str, Any]:
    return client.associate_vpc_cidr_block(VpcId=vpc_id, **params)


@EC2VpcErrorHandler.common_error_handler("disassociate vpc cidr block")
@AWSRetry.jittered_backoff()
def disassociate_vpc_cidr_block(client, association_id: str) -> Dict[str, Any]:
    return client.disassociate_vpc_cidr_block(AssociationId=association_id)


# EC2 VPC Peering Connection
class EC2VpcPeeringErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidVpcPeeringConnectionID.NotFound")


@EC2VpcPeeringErrorHandler.list_error_handler("describe vpc peering", [])
@AWSRetry.jittered_backoff()
def describe_vpc_peering_connections(client, **params: Dict[str, Any]) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("describe_vpc_peering_connections")
    return paginator.paginate(**params).build_full_result()["VpcPeeringConnections"]


@EC2VpcSubnetErrorHandler.common_error_handler("create vpc peering")
@AWSRetry.jittered_backoff()
def create_vpc_peering_connection(
    client, **params: Dict[str, Union[str, bool, int, EC2TagSpecifications]]
) -> Dict[str, Any]:
    return client.create_vpc_peering_connection(**params)["VpcPeeringConnection"]


@EC2VpcSubnetErrorHandler.deletion_error_handler("delete vpc peering")
@AWSRetry.jittered_backoff()
def delete_vpc_peering_connection(client, peering_id: str) -> bool:
    client.delete_vpc_peering_connection(VpcPeeringConnectionId=peering_id)
    return True


@EC2VpcSubnetErrorHandler.deletion_error_handler("accept vpc peering")
@AWSRetry.jittered_backoff()
def accept_vpc_peering_connection(client, peering_id: str) -> bool:
    client.accept_vpc_peering_connection(VpcPeeringConnectionId=peering_id)
    return True


@EC2VpcSubnetErrorHandler.deletion_error_handler("reject vpc peering")
@AWSRetry.jittered_backoff()
def reject_vpc_peering_connection(client, peering_id: str) -> bool:
    client.reject_vpc_peering_connection(VpcPeeringConnectionId=peering_id)
    return True


# EC2 vpn
class EC2VpnErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code(["InvalidVpnConnectionID.NotFound", "InvalidRoute.NotFound"])


@EC2VpcErrorHandler.list_error_handler("describe vpn connections", [])
@AWSRetry.jittered_backoff()
def describe_vpn_connections(client, **params: Dict[str, Any]) -> List[Dict[str, Any]]:
    # The paginator does not exist for `describe_vpn_connections`
    return client.describe_vpn_connections(**params)["VpnConnections"]


@EC2VpcErrorHandler.common_error_handler("create vpn connection route")
@AWSRetry.jittered_backoff()
def create_vpn_connection_route(client, vpn_connection_id: str, route: Dict[str, Any]) -> bool:
    client.create_vpn_connection_route(VpnConnectionId=vpn_connection_id, DestinationCidrBlock=route)
    return True


@EC2VpcErrorHandler.deletion_error_handler("delete vpn connection route")
@AWSRetry.jittered_backoff()
def delete_vpn_connection_route(client, vpn_connection_id: str, route: Dict[str, Any]) -> bool:
    client.delete_vpn_connection_route(VpnConnectionId=vpn_connection_id, DestinationCidrBlock=route)
    return True


@EC2VpcErrorHandler.common_error_handler("create vpn connection")
@AWSRetry.jittered_backoff()
def create_vpn_connection(client, **params: Dict[str, Any]) -> Dict[str, Any]:
    return client.create_vpn_connection(**params)["VpnConnection"]


@EC2VpcErrorHandler.deletion_error_handler("delete vpn connection")
@AWSRetry.jittered_backoff()
def delete_vpn_connection(client, vpn_connection_id: str) -> Dict[str, Any]:
    client.delete_vpn_connection(VpnConnectionId=vpn_connection_id)
    return True


# EC2 Internet Gateway
class EC2InternetGatewayErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidInternetGatewayID.NotFound")


@EC2InternetGatewayErrorHandler.list_error_handler("describe internet gateways")
@AWSRetry.jittered_backoff()
def describe_internet_gateways(
    client, **params: Dict[str, Union[List[str], bool, List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("describe_internet_gateways")
    return paginator.paginate(**params).build_full_result()["InternetGateways"]


@EC2InternetGatewayErrorHandler.common_error_handler("create internet gateway")
@AWSRetry.jittered_backoff()
def create_internet_gateway(client, tags: Optional[List[Dict[str, str]]]) -> Dict[str, Any]:
    params = {}
    if tags:
        params["TagSpecifications"] = boto3_tag_specifications(tags, types="internet-gateway")
    return client.create_internet_gateway(**params)["InternetGateway"]


@EC2InternetGatewayErrorHandler.common_error_handler("detach internet gateway")
@AWSRetry.jittered_backoff()
def detach_internet_gateway(client, internet_gateway_id: str, vpc_id: str) -> bool:
    client.detach_internet_gateway(InternetGatewayId=internet_gateway_id, VpcId=vpc_id)
    return True


@EC2InternetGatewayErrorHandler.common_error_handler("attach internet gateway")
@AWSRetry.jittered_backoff()
def attach_internet_gateway(client, internet_gateway_id: str, vpc_id: str) -> bool:
    client.attach_internet_gateway(InternetGatewayId=internet_gateway_id, VpcId=vpc_id)
    return True


@EC2InternetGatewayErrorHandler.deletion_error_handler("delete internet gateway")
@AWSRetry.jittered_backoff()
def delete_internet_gateway(client, internet_gateway_id: str) -> bool:
    client.delete_internet_gateway(InternetGatewayId=internet_gateway_id)
    return True


# EC2 NAT Gateway
class EC2NatGatewayErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidNatGatewayID.NotFound")


@EC2NatGatewayErrorHandler.list_error_handler("describe nat gateways", [])
@AWSRetry.jittered_backoff()
def describe_nat_gateways(
    client, **params: Dict[str, Union[List[str], bool, List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("describe_nat_gateways")
    return paginator.paginate(**params).build_full_result()["NatGateways"]


@EC2NatGatewayErrorHandler.deletion_error_handler("delete nat gateway")
@AWSRetry.jittered_backoff()
def delete_nat_gateway(client, nat_gateway_id: str) -> bool:
    client.delete_nat_gateway(NatGatewayId=nat_gateway_id)
    return True


@EC2NatGatewayErrorHandler.common_error_handler("create nat gateway")
@AWSRetry.jittered_backoff(catch_extra_error_codes=["InvalidElasticIpID.NotFound"])
def create_nat_gateway(
    client, **params: Dict[str, Union[str, bool, int, EC2TagSpecifications, List[str]]]
) -> Dict[str, Any]:
    return client.create_nat_gateway(**params)["NatGateway"]


# EC2 Elastic IP
class EC2ElasticIPErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidAddress.NotFound")


@EC2ElasticIPErrorHandler.list_error_handler("describe addresses", [])
@AWSRetry.jittered_backoff()
def describe_addresses(
    client, **params: Dict[str, Union[List[str], List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Union[str, List[Dict[str, str]]]]]:
    # The paginator does not exist for 'describe_addresses()'
    return client.describe_addresses(**params)["Addresses"]


@EC2ElasticIPErrorHandler.common_error_handler("release address")
@AWSRetry.jittered_backoff()
def release_address(client, allocation_id: str, network_border_group: Optional[str] = None) -> bool:
    params = {"AllocationId": allocation_id}
    if network_border_group:
        params["NetworkBorderGroup"] = network_border_group
    client.release_address(**params)
    return True


@EC2ElasticIPErrorHandler.common_error_handler("associate address")
@AWSRetry.jittered_backoff()
def associate_address(client, **params: Dict[str, Union[str, bool]]) -> Dict[str, str]:
    return client.associate_address(**params)


@EC2ElasticIPErrorHandler.common_error_handler("disassociate address")
@AWSRetry.jittered_backoff()
def disassociate_address(client, association_id: str) -> bool:
    client.disassociate_address(AssociationId=association_id)
    return True


@EC2ElasticIPErrorHandler.common_error_handler("allocate address")
@AWSRetry.jittered_backoff()
def allocate_address(client, **params: Dict[str, Union[str, EC2TagSpecifications]]) -> Dict[str, str]:
    return client.allocate_address(**params)


# EC2 VPC Endpoints
class EC2VpcEndpointsErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code(["InvalidVpcEndpoint.NotFound", "InvalidVpcEndpointId.NotFound"])


@EC2VpcEndpointsErrorHandler.list_error_handler("describe vpc endpoints", [])
@AWSRetry.jittered_backoff()
def describe_vpc_endpoints(
    client, **params: Dict[str, Union[List[str], int, List[Dict[str, Union[str, List[str]]]]]]
) -> Dict[str, Any]:
    paginator = client.get_paginator("describe_vpc_endpoints")
    return paginator.paginate(**params).build_full_result()["VpcEndpoints"]


@EC2VpcEndpointsErrorHandler.deletion_error_handler("delete vpc endpoints")
@AWSRetry.jittered_backoff()
def delete_vpc_endpoints(client, vpc_endpoint_ids: str) -> List[Dict[str, Union[str, Dict[str, str]]]]:
    result = client.delete_vpc_endpoints(VpcEndpointIds=vpc_endpoint_ids)
    return result.get("Unsuccessful", [])


@EC2ElasticIPErrorHandler.common_error_handler("create vpc endpoint")
@AWSRetry.jittered_backoff()
def create_vpc_endpoint(
    client,
    **params: Dict[
        str, Union[str, bool, List[str], Dict[str, Union[str, bool]], List[Dict[str, str]], EC2TagSpecifications]
    ],
) -> Dict[str, Any]:
    return client.create_vpc_endpoint(**params)["VpcEndpoint"]


# EC2 VPC Endpoint Services
class EC2VpcEndpointServiceErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidServiceName")


@EC2VpcEndpointServiceErrorHandler.list_error_handler("describe vpc endpoint services", default_value={})
@AWSRetry.jittered_backoff()
def describe_vpc_endpoint_services(
    client, filters: Optional[List[Dict[str, Any]]] = None, service_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Wrap call to the AWS API describe_vpc_endpoint_services (used to describe available
    services to which you can create a VPC endpoint.)
        Parameters:
            client: The boto3 client.
            filters: Optional filters to pass to the API.
            service_names: the service names.
        Returns:
            results: A dictionnary with keys 'ServiceNames' and 'ServiceDetails'
    """
    paginator = client.get_paginator("describe_vpc_endpoint_services")
    params: dict[str, Any] = {}
    if filters:
        params["Filters"] = filters

    if service_names:
        params["ServiceNames"] = service_names

    results = paginator.paginate(**params).build_full_result()
    return results


# EC2 VPC DHCP Option
class EC2VpcDhcpOptionErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code(["InvalidDhcpOptionsID.NotFound", "InvalidDhcpOptionID.NotFound"])


@EC2VpcDhcpOptionErrorHandler.list_error_handler("describe dhcp options", [])
@AWSRetry.jittered_backoff()
def describe_dhcp_options(
    client, **params: Dict[str, Union[List[str], int, List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("describe_dhcp_options")
    return paginator.paginate(**params).build_full_result()["DhcpOptions"]


@EC2VpcDhcpOptionErrorHandler.deletion_error_handler("delete dhcp options")
@AWSRetry.jittered_backoff()
def delete_dhcp_options(client, dhcp_options_id: str) -> bool:
    client.delete_dhcp_options(DhcpOptionsId=dhcp_options_id)
    return True


@EC2VpcDhcpOptionErrorHandler.common_error_handler("associate dhcp options")
@AWSRetry.jittered_backoff()
def associate_dhcp_options(client, dhcp_options_id: str, vpc_id: str) -> bool:
    client.associate_dhcp_options(DhcpOptionsId=dhcp_options_id, VpcId=vpc_id)
    return True


@EC2VpcDhcpOptionErrorHandler.common_error_handler("create dhcp options")
@AWSRetry.jittered_backoff()
def create_dhcp_options(
    client, **params: Dict[str, Union[Dict[str, Union[str, List[str]]], EC2TagSpecifications]]
) -> Dict[str, Any]:
    return client.create_dhcp_options(**params)["DhcpOptions"]


# EC2 vpn Gateways
class EC2VpnGatewaysErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code(["InvalidVpnGatewayID.NotFound", "InvalidVpnGatewayState"])


@EC2VpnGatewaysErrorHandler.list_error_handler("describe vpn gateways", [])
@AWSRetry.jittered_backoff()
def describe_vpn_gateways(
    client, **params: Dict[str, Union[List[str], int, List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Any]]:
    return client.describe_vpn_gateways(**params)["VpnGateways"]


@EC2VpnGatewaysErrorHandler.common_error_handler("create vpn gateway")
@AWSRetry.jittered_backoff(catch_extra_error_codes=["VpnGatewayLimitExceeded"])
def create_vpn_gateway(
    client, **params: Dict[str, Union[List[str], int, List[Dict[str, Union[str, List[str]]]]]]
) -> Dict[str, Any]:
    return client.create_vpn_gateway(**params)["VpnGateway"]


@EC2VpnGatewaysErrorHandler.deletion_error_handler("delete vpn gateway")
@AWSRetry.jittered_backoff()
def delete_vpn_gateway(client, vpn_gateway_id: str) -> bool:
    client.delete_vpn_gateway(VpnGatewayId=vpn_gateway_id)
    return True


@EC2VpnGatewaysErrorHandler.common_error_handler("attach vpn gateway")
@AWSRetry.jittered_backoff()
def attach_vpn_gateway(client, vpc_id: str, vpn_gateway_id: str) -> bool:
    client.attach_vpn_gateway(VpcId=vpc_id, VpnGatewayId=vpn_gateway_id)
    return True


@EC2VpnGatewaysErrorHandler.common_error_handler("detach vpn gateway")
@AWSRetry.jittered_backoff()
def detach_vpn_gateway(client, vpc_id: str, vpn_gateway_id: str) -> bool:
    client.detach_vpn_gateway(VpcId=vpc_id, VpnGatewayId=vpn_gateway_id)
    return True


# EC2 Volumes
class EC2VolumeErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidVolume.NotFound")


@EC2VolumeErrorHandler.list_error_handler("describe volumes", [])
@AWSRetry.jittered_backoff()
def describe_volumes(
    client, **params: Dict[str, Union[List[str], int, List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("describe_volumes")
    return paginator.paginate(**params).build_full_result()["Volumes"]


@EC2VolumeErrorHandler.deletion_error_handler("delete volume")
@AWSRetry.jittered_backoff()
def delete_volume(client, volume_id: str) -> bool:
    client.delete_volume(VolumeId=volume_id)
    return True


@EC2VolumeErrorHandler.common_error_handler("modify volume")
@AWSRetry.jittered_backoff()
def modify_volume(client, **params: Dict[str, Union[str, bool, int]]) -> Dict[str, Any]:
    return client.modify_volume(**params)["VolumeModification"]


@EC2VolumeErrorHandler.common_error_handler("modify volume")
@AWSRetry.jittered_backoff()
def create_volume(client, **params: Dict[str, Union[str, bool, int, EC2TagSpecifications]]) -> Dict[str, Any]:
    return client.create_volume(**params)


@EC2VolumeErrorHandler.common_error_handler("attach volume")
@AWSRetry.jittered_backoff()
def attach_volume(client, device: str, instance_id: str, volume_id: str) -> Dict[str, Any]:
    return client.attach_volume(Device=device, InstanceId=instance_id, VolumeId=volume_id)


@EC2VolumeErrorHandler.common_error_handler("attach volume")
@AWSRetry.jittered_backoff()
def detach_volume(client, volume_id: str, **params: Dict[str, Union[str, bool]]) -> Dict[str, Any]:
    return client.detach_volume(VolumeId=volume_id, **params)


# EC2 Instance
EC2_INSTANCE_CATCH_EXTRA_CODES = [
    "IncorrectState",
    "InsufficientInstanceCapacity",
    "InvalidInstanceID.NotFound",
]


class EC2InstanceErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidInstanceID.NotFound")


@EC2InstanceErrorHandler.list_error_handler("describe instances", [])
@AWSRetry.jittered_backoff()
def describe_instances(
    client, **params: Dict[str, Union[List[str], int, List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("describe_instances")
    return paginator.paginate(**params).build_full_result()["Reservations"]


@EC2InstanceErrorHandler.common_error_handler("modify instance attribute")
@AWSRetry.jittered_backoff(catch_extra_error_codes=EC2_INSTANCE_CATCH_EXTRA_CODES)
def modify_instance_attribute(
    client,
    instance_id: str,
    **params: Dict[
        str,
        Union[
            str,
            List[str],
            Dict[str, str],
            Dict[str, bool],
            Dict[str, bytes],
            Dict[str, Union[str, Dict[str, Union[str, bool]]]],
        ],
    ],
) -> bool:
    client.modify_instance_attribute(InstanceId=instance_id, **params)
    return True


@EC2InstanceErrorHandler.list_error_handler("terminate instances", [])
@AWSRetry.jittered_backoff()
def terminate_instances(client, instance_ids: List[str]) -> List[Dict[str, Any]]:
    return client.terminate_instances(InstanceIds=instance_ids)["TerminatingInstances"]


@EC2InstanceErrorHandler.list_error_handler("stop instances", [])
@AWSRetry.jittered_backoff()
def stop_instances(
    client, instance_ids: List[str], **params: Dict[str, Union[bool, List[str]]]
) -> List[Dict[str, Any]]:
    return client.stop_instances(InstanceIds=instance_ids, **params)["StoppingInstances"]


@EC2InstanceErrorHandler.list_error_handler("start instances", [])
@AWSRetry.jittered_backoff()
def start_instances(
    client, instance_ids: List[str], **params: Dict[str, Union[str, List[str]]]
) -> List[Dict[str, Any]]:
    return client.start_instances(InstanceIds=instance_ids, **params)["StartingInstances"]


@EC2InstanceErrorHandler.common_error_handler("run instances")
@AWSRetry.jittered_backoff(catch_extra_error_codes=EC2_INSTANCE_CATCH_EXTRA_CODES)
def run_instances(client, **params: Dict[str, Any]) -> Dict[str, Any]:
    return client.run_instances(**params)


@EC2InstanceErrorHandler.common_error_handler("describe instance attribute")
@AWSRetry.jittered_backoff(catch_extra_error_codes=EC2_INSTANCE_CATCH_EXTRA_CODES)
def describe_instance_attribute(client, instance_id: str, attribute: str) -> Dict[str, Any]:
    # The paginator does not exist for describe_instance_attribute()
    return client.describe_instance_attribute(InstanceId=instance_id, Attribute=attribute)


@EC2InstanceErrorHandler.common_error_handler("describe instance status")
@AWSRetry.jittered_backoff(catch_extra_error_codes=EC2_INSTANCE_CATCH_EXTRA_CODES)
def describe_instance_status(
    client, **params: Dict[str, Union[List[str], bool, int, List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("describe_instance_status")
    return paginator.paginate(**params).build_full_result()["InstanceStatuses"]


@EC2InstanceErrorHandler.common_error_handler("modify instance metadata options")
@AWSRetry.jittered_backoff(catch_extra_error_codes=EC2_INSTANCE_CATCH_EXTRA_CODES)
def modify_instance_metadata_options(
    client, instance_id: str, **params: Dict[str, Union[str, int]]
) -> Dict[str, Union[int, str]]:
    return client.modify_instance_metadata_options(InstanceId=instance_id, **params)["InstanceMetadataOptions"]


@EC2InstanceErrorHandler.common_error_handler("describe iam instance profile associations")
@AWSRetry.jittered_backoff(catch_extra_error_codes=EC2_INSTANCE_CATCH_EXTRA_CODES)
def describe_iam_instance_profile_associations(
    client, **params: Dict[str, Union[List[str], int, List[Dict[str, Union[str, List[str]]]]]]
) -> Dict[str, Any]:
    paginator = client.get_paginator("describe_iam_instance_profile_associations")
    return paginator.paginate(**params).build_full_result()["IamInstanceProfileAssociations"]


@EC2InstanceErrorHandler.common_error_handler("replace iam instance profile association")
@AWSRetry.jittered_backoff(catch_extra_error_codes=EC2_INSTANCE_CATCH_EXTRA_CODES)
def replace_iam_instance_profile_association(
    client, iam_instance_profile: Dict[str, str], association_id: str
) -> Dict[str, Union[int, str]]:
    return client.replace_iam_instance_profile_association(
        IamInstanceProfile=iam_instance_profile, AssociationId=association_id
    )["IamInstanceProfileAssociation"]


@EC2InstanceErrorHandler.common_error_handler("associate iam instance profile")
@AWSRetry.jittered_backoff(catch_extra_error_codes=EC2_INSTANCE_CATCH_EXTRA_CODES)
def associate_iam_instance_profile(client, iam_instance_profile: Dict[str, str], instance_id: str) -> Dict[str, Any]:
    return client.associate_iam_instance_profile(IamInstanceProfile=iam_instance_profile, InstanceId=instance_id)[
        "IamInstanceProfileAssociation"
    ]


# EC2 Key
class EC2KeyErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidKeyPair.NotFound")


@EC2KeyErrorHandler.list_error_handler("describe key pairs", [])
@AWSRetry.jittered_backoff()
def describe_key_pairs(
    client, **params: Dict[str, Union[List[str], bool, List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Any]]:
    # The paginator does not exist for `describe_key_pairs()`
    return client.describe_key_pairs(**params)["KeyPairs"]


@EC2KeyErrorHandler.common_error_handler("import key pair")
@AWSRetry.jittered_backoff()
def import_key_pair(
    client, **params: Dict[str, Union[str, bytes, EC2TagSpecifications]]
) -> Dict[str, Union[str, List[Dict[str, str]]]]:
    return client.import_key_pair(**params)


@EC2KeyErrorHandler.common_error_handler("create key pair")
@AWSRetry.jittered_backoff()
def create_key_pair(
    client, **params: Dict[str, Union[str, EC2TagSpecifications]]
) -> Dict[str, Union[str, List[Dict[str, str]]]]:
    return client.create_key_pair(**params)


@EC2KeyErrorHandler.deletion_error_handler("delete key pair")
@AWSRetry.jittered_backoff()
def delete_key_pair(client, key_name: Optional[str] = None, key_id: Optional[str] = None) -> bool:
    params = {}
    if key_name:
        params["KeyName"] = key_name
    if key_id:
        params["KeyPairId"] = key_id
    client.delete_key_pair(**params)
    return True


# EC2 Image
class EC2ImageErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidAMIID.Unavailable")


@EC2ImageErrorHandler.list_error_handler("describe images", [])
@AWSRetry.jittered_backoff()
def describe_images(
    client, **params: Dict[str, Union[List[str], bool, int, List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Any]]:
    # 'DescribeImages' can be paginated depending on the boto3 version
    if client.can_paginate("describe_images"):
        paginator = client.get_paginator("describe_images")
        return paginator.paginate(**params).build_full_result()["Images"]
    else:
        return client.describe_images(**params)["Images"]


@EC2ImageErrorHandler.list_error_handler("describe image attribute", {})
@AWSRetry.jittered_backoff()
def describe_image_attribute(client, image_id: str, attribute: str) -> Optional[Dict[str, Any]]:
    # The paginator does not exist for `describe_image_attribute()`
    return client.describe_image_attribute(Attribute=attribute, ImageId=image_id)


@EC2ImageErrorHandler.deletion_error_handler("deregister image")
@AWSRetry.jittered_backoff()
def deregister_image(client, image_id: str) -> bool:
    client.deregister_image(ImageId=image_id)
    return True


@EC2ImageErrorHandler.common_error_handler("modify image attribute")
@AWSRetry.jittered_backoff()
def modify_image_attribute(client, image_id: str, **params: Dict[str, Any]) -> bool:
    client.modify_image_attribute(ImageId=image_id, **params)
    return True


@EC2ImageErrorHandler.common_error_handler("create image")
@AWSRetry.jittered_backoff()
def create_image(client, **params: Dict[str, Any]) -> Dict[str, str]:
    return client.create_image(**params)


@EC2ImageErrorHandler.common_error_handler("register image")
@AWSRetry.jittered_backoff()
def register_image(client, **params: Dict[str, Any]) -> Dict[str, str]:
    return client.register_image(**params)


# EC2 Snapshot
class EC2SnapshotErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidSnapshot.NotFound")


@EC2SnapshotErrorHandler.deletion_error_handler("delete snapshot")
@AWSRetry.jittered_backoff()
def delete_snapshot(client, snapshot_id: str) -> bool:
    client.delete_snapshot(SnapshotId=snapshot_id)
    return True


@EC2SnapshotErrorHandler.list_error_handler("describe snapshots", [])
@AWSRetry.jittered_backoff()
def describe_snapshots(
    client, **params: Dict[str, Union[List[str], int, List[Dict[str, Union[str, List[str]]]]]]
) -> Dict[str, Any]:
    # We do not use paginator here because the `ec2_snapshot_info` module excepts the NextToken to be returned
    return client.describe_snapshots(**params)


@EC2SnapshotErrorHandler.common_error_handler("describe snapshot attribute")
@AWSRetry.jittered_backoff()
def describe_snapshot_attribute(
    client, snapshot_id: str, attribute: str
) -> Dict[str, Union[str, List[Dict[str, str]]]]:
    return client.describe_snapshot_attribute(Attribute=attribute, SnapshotId=snapshot_id)


@EC2SnapshotErrorHandler.common_error_handler("reset snapshot attribute")
@AWSRetry.jittered_backoff()
def reset_snapshot_attribute(client, snapshot_id: str, attribute: str) -> bool:
    client.reset_snapshot_attribute(Attribute=attribute, SnapshotId=snapshot_id)
    return True


@EC2SnapshotErrorHandler.common_error_handler("modify snapshot attribute")
@AWSRetry.jittered_backoff()
def modify_snapshot_attribute(client, snapshot_id: str, **params: Dict[str, Any]) -> bool:
    client.modify_snapshot_attribute(SnapshotId=snapshot_id, **params)
    return True


@EC2SnapshotErrorHandler.common_error_handler("create snapshot")
# Handle SnapshotCreationPerVolumeRateExceeded separately because we need a much
# longer delay than normal
@AWSRetry.jittered_backoff(catch_extra_error_codes=["SnapshotCreationPerVolumeRateExceeded"], delay=15)
def create_snapshot(client, volume_id: str, **params: Dict[str, Any]) -> Dict[str, Any]:
    return client.create_snapshot(VolumeId=volume_id, **params)


# EC2 ENI
class EC2NetworkInterfacesErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidNetworkInterfaceID.NotFound")


@EC2NetworkInterfacesErrorHandler.list_error_handler("describe network interfaces", [])
@AWSRetry.jittered_backoff()
def describe_network_interfaces(
    client, **params: Dict[str, Union[List[str], int, List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("describe_network_interfaces")
    return paginator.paginate(**params).build_full_result()["NetworkInterfaces"]


@EC2NetworkInterfacesErrorHandler.deletion_error_handler("delete network interface")
@AWSRetry.jittered_backoff()
def delete_network_interface(client, network_interface_id: str) -> bool:
    client.delete_network_interface(NetworkInterfaceId=network_interface_id)
    return True


@EC2NetworkInterfacesErrorHandler.common_error_handler("create network interface")
@AWSRetry.jittered_backoff()
def create_network_interface(client, **params: Dict[str, Any]) -> Dict[str, str]:
    return client.create_network_interface(**params)["NetworkInterface"]


@EC2NetworkInterfacesErrorHandler.common_error_handler("attach network interface")
@AWSRetry.jittered_backoff()
def attach_network_interface(
    client, **params: Dict[str, Union[str, int, Dict[str, Union[bool, Dict[str, bool]]]]]
) -> Dict[str, Union[str, int]]:
    return client.attach_network_interface(**params)


@EC2NetworkInterfacesErrorHandler.common_error_handler("detach network interface")
@AWSRetry.jittered_backoff()
def detach_network_interface(client, attachment_id: str, force: Optional[bool] = None) -> bool:
    params = {"AttachmentId": attachment_id}
    if force is not None:
        params["Force"] = force
    client.detach_network_interface(**params)
    return True


@EC2NetworkInterfacesErrorHandler.common_error_handler("assign private ip addresses")
@AWSRetry.jittered_backoff()
def assign_private_ip_addresses(
    client, **params: Dict[str, Union[bool, int, str, List[str]]]
) -> Dict[str, Union[str, List[Dict[str, str]]]]:
    return client.assign_private_ip_addresses(**params)


@EC2NetworkInterfacesErrorHandler.common_error_handler("unassign private ip addresses")
@AWSRetry.jittered_backoff()
def unassign_private_ip_addresses(client, **params: Dict[str, Union[str, List[str]]]) -> bool:
    client.unassign_private_ip_addresses(**params)
    return True


@EC2NetworkInterfacesErrorHandler.common_error_handler("modify network interface attribute")
@AWSRetry.jittered_backoff()
def modify_network_interface_attribute(client, **params: Dict[str, Any]) -> bool:
    client.modify_network_interface_attribute(**params)
    return True


# EC2 Import Image
class EC2ImportImageErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidConversionTaskId")


@EC2ImportImageErrorHandler.list_error_handler("describe import image tasks", [])
@AWSRetry.jittered_backoff()
def describe_import_image_tasks(
    client, **params: Dict[str, Union[List[str], int, List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("describe_import_image_tasks")
    return paginator.paginate(**params).build_full_result()["ImportImageTasks"]


def describe_import_image_tasks_as_snake_dict(
    client, **params: Dict[str, Union[List[str], int, List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Any]]:
    result = []
    for import_image_info in describe_import_image_tasks(client, **params):
        image = copy.deepcopy(import_image_info)
        image["Tags"] = boto3_tag_list_to_ansible_dict(image["Tags"])
        result.append(camel_dict_to_snake_dict(image, ignore_list=["Tags"]))
    return result


@EC2ImportImageErrorHandler.deletion_error_handler("cancel import task")
@AWSRetry.jittered_backoff()
def cancel_import_task(client, import_task_id: str, cancel_reason: Optional[str] = None) -> bool:
    params = {"ImportTaskId": import_task_id}
    if cancel_reason:
        params["CancelReason"] = cancel_reason
    client.cancel_import_task(**params)
    return True


@EC2ImportImageErrorHandler.common_error_handler("import image")
@AWSRetry.jittered_backoff()
def import_image(client, **params: Dict[str, Any]) -> Dict[str, Any]:
    return client.import_image(**params)


# EC2 Spot instance
class EC2SpotInstanceRequestErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidSpotInstanceRequestID.NotFound")


@EC2SpotInstanceRequestErrorHandler.list_error_handler("describe spot instance requests", [])
@AWSRetry.jittered_backoff()
def describe_spot_instance_requests(
    client, **params: Dict[str, Union[List[str], int, List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("describe_spot_instance_requests")
    return paginator.paginate(**params).build_full_result()["SpotInstanceRequests"]


@EC2SpotInstanceRequestErrorHandler.common_error_handler("cancel spot instance requests")
@AWSRetry.jittered_backoff()
def cancel_spot_instance_requests(client, spot_instance_request_ids: List[str]) -> List[Dict[str, str]]:
    return client.cancel_spot_instance_requests(SpotInstanceRequestIds=spot_instance_request_ids)[
        "CancelledSpotInstanceRequests"
    ]


@EC2SpotInstanceRequestErrorHandler.common_error_handler("request spot instances")
@AWSRetry.jittered_backoff()
def request_spot_instances(client, **params: Dict[str, Any]) -> List[Dict[str, Any]]:
    return client.request_spot_instances(**params)["SpotInstanceRequests"]


# EC2 Security Groups
class EC2SecurityGroupsErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidGroup.NotFound")


@EC2SecurityGroupsErrorHandler.list_error_handler("describe security groups", [])
@AWSRetry.jittered_backoff()
def describe_security_groups(
    client, **params: Dict[str, Union[List[str], int, List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("describe_security_groups")
    return paginator.paginate(**params).build_full_result()["SecurityGroups"]


@EC2SecurityGroupsErrorHandler.deletion_error_handler("delete security group")
@AWSRetry.jittered_backoff()
def delete_security_group(client, group_id: Optional[str], group_name: Optional[str] = None) -> bool:
    params = {}
    if group_id:
        params["GroupId"] = group_id
    if group_name:
        params["GroupName"] = group_name
    client.delete_security_group(**params)
    return True


@EC2SecurityGroupsErrorHandler.common_error_handler("create security group")
@AWSRetry.jittered_backoff()
def create_security_group(client, **params: Dict[str, Union[str, EC2TagSpecifications]]) -> Dict[str, Any]:
    return client.create_security_group(**params)


@EC2SecurityGroupsErrorHandler.common_error_handler("update security group rule descriptions egress")
@AWSRetry.jittered_backoff()
def update_security_group_rule_descriptions_egress(client, **params: Dict[str, Any]) -> bool:
    return client.update_security_group_rule_descriptions_egress(**params)["Return"]


@EC2SecurityGroupsErrorHandler.common_error_handler("update security group rule descriptions ingress")
@AWSRetry.jittered_backoff()
def update_security_group_rule_descriptions_ingress(client, **params: Dict[str, Any]) -> bool:
    return client.update_security_group_rule_descriptions_ingress(**params)["Return"]


@EC2SecurityGroupsErrorHandler.common_error_handler("revoke security group ingress")
@AWSRetry.jittered_backoff()
def revoke_security_group_ingress(client, **params: Dict[str, Any]) -> bool:
    return client.revoke_security_group_ingress(**params)["Return"]


@EC2SecurityGroupsErrorHandler.common_error_handler("revoke security group egress")
@AWSRetry.jittered_backoff()
def revoke_security_group_egress(client, **params: Dict[str, Any]) -> bool:
    return client.revoke_security_group_egress(**params)["Return"]


@EC2SecurityGroupsErrorHandler.common_error_handler("authorize security group ingress")
@AWSRetry.jittered_backoff()
def authorize_security_group_ingress(client, **params: Dict[str, Any]) -> bool:
    return client.authorize_security_group_ingress(**params)["Return"]


@EC2SecurityGroupsErrorHandler.common_error_handler("authorize security group egress")
@AWSRetry.jittered_backoff()
def authorize_security_group_egress(client, **params: Dict[str, Any]) -> bool:
    return client.authorize_security_group_egress(**params)["Return"]


# EC2 Egress only internet Gateway
class EC2EgressOnlyInternetGatewayErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidGatewayID.NotFound")


@EC2EgressOnlyInternetGatewayErrorHandler.list_error_handler("describe egress only internet gateways", [])
@AWSRetry.jittered_backoff()
def describe_egress_only_internet_gateways(
    client, **params: Dict[str, Union[List[str], int, List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("describe_egress_only_internet_gateways")
    return paginator.paginate(**params).build_full_result()["EgressOnlyInternetGateways"]


@EC2EgressOnlyInternetGatewayErrorHandler.deletion_error_handler("delete egress only internet gateway")
@AWSRetry.jittered_backoff()
def delete_egress_only_internet_gateway(client, egress_only_internet_gateway_id: str) -> bool:
    return client.delete_egress_only_internet_gateway(EgressOnlyInternetGatewayId=egress_only_internet_gateway_id)[
        "ReturnCode"
    ]


@EC2EgressOnlyInternetGatewayErrorHandler.common_error_handler("create egress only internet gateway")
@AWSRetry.jittered_backoff()
def create_egress_only_internet_gateway(
    client, vpc_id: str, tags: Optional[EC2TagSpecifications] = None
) -> Dict[str, Any]:
    params = {"VpcId": vpc_id}
    if tags:
        params["TagSpecifications"] = boto3_tag_specifications(tags, types="egress-only-internet-gateway")
    return client.create_egress_only_internet_gateway(**params)


# EC2 Network ACL
class EC2NetworkAclErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidNetworkAclID.NotFound")


@EC2NetworkAclErrorHandler.list_error_handler("describe network acls", [])
@AWSRetry.jittered_backoff()
def describe_network_acls(
    client, **params: Dict[str, Union[List[str], int, List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("describe_network_acls")
    return paginator.paginate(**params).build_full_result()["NetworkAcls"]


@EC2NetworkAclErrorHandler.common_error_handler("create network acl")
@AWSRetry.jittered_backoff()
def create_network_acl(client, vpc_id: str, tags: Optional[EC2TagSpecifications] = None) -> Dict[str, Any]:
    params = {"VpcId": vpc_id}
    if tags:
        params["TagSpecifications"] = boto3_tag_specifications(tags, types="network-acl")
    return client.create_network_acl(**params)["NetworkAcl"]


@EC2NetworkAclErrorHandler.common_error_handler("create network acl entry")
@AWSRetry.jittered_backoff()
def create_network_acl_entry(
    client,
    network_acl_id: str,
    protocol: str,
    egress: bool,
    rule_action: str,
    rule_number: int,
    **params: Dict[str, Any],
) -> bool:
    args = {
        "Egress": egress,
        "NetworkAclId": network_acl_id,
        "Protocol": protocol,
        "RuleAction": rule_action,
        "RuleNumber": rule_number,
    }
    if params:
        args.update(params)
    client.create_network_acl_entry(**args)
    return True


@EC2NetworkAclErrorHandler.deletion_error_handler("delete network acl")
@AWSRetry.jittered_backoff()
def delete_network_acl(client, network_acl_id: str) -> bool:
    client.delete_network_acl(NetworkAclId=network_acl_id)
    return True


@EC2NetworkAclErrorHandler.deletion_error_handler("delete network acl entry")
@AWSRetry.jittered_backoff()
def delete_network_acl_entry(client, network_acl_id: str, rule_number: int, egress: bool) -> bool:
    client.delete_network_acl_entry(NetworkAclId=network_acl_id, Egress=egress, RuleNumber=rule_number)
    return True


@EC2NetworkAclErrorHandler.common_error_handler("replace network acl entry")
@AWSRetry.jittered_backoff()
def replace_network_acl_entry(
    client,
    network_acl_id: str,
    protocol: str,
    egress: bool,
    rule_action: str,
    rule_number: int,
    **params: Dict[str, Any],
) -> Dict[str, Any]:
    args = {
        "Egress": egress,
        "NetworkAclId": network_acl_id,
        "Protocol": protocol,
        "RuleAction": rule_action,
        "RuleNumber": rule_number,
    }
    if params:
        args.update(params)
    return client.replace_network_acl_entry(**args)


@EC2NetworkAclErrorHandler.common_error_handler("replace network acl association")
@AWSRetry.jittered_backoff()
def replace_network_acl_association(client, network_acl_id: str, association_id: str) -> str:
    return client.replace_network_acl_association(NetworkAclId=network_acl_id, AssociationId=association_id)[
        "NewAssociationId"
    ]


# EC2 Placement Group
class EC2PlacementGroupErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidPlacementGroup.Unknown")


@EC2PlacementGroupErrorHandler.list_error_handler("describe placement group", [])
@AWSRetry.jittered_backoff()
def describe_ec2_placement_groups(
    client, **params: Dict[str, Union[List[str], int, List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Any]]:
    return client.describe_placement_groups(**params)["PlacementGroups"]


@EC2PlacementGroupErrorHandler.deletion_error_handler("delete placement group")
@AWSRetry.jittered_backoff()
def delete_ec2_placement_group(client, group_name: str) -> bool:
    client.delete_placement_group(GroupName=group_name)
    return True


@EC2PlacementGroupErrorHandler.common_error_handler("create placement group")
@AWSRetry.jittered_backoff()
def create_ec2_placement_group(client, **params: Dict[str, Union[str, EC2TagSpecifications]]) -> Dict[str, Any]:
    return client.create_placement_group(**params)["PlacementGroup"]


# EC2 Launch template
class EC2LaunchTemplateErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code(["InvalidLaunchTemplateName.NotFoundException", "InvalidLaunchTemplateId.NotFound"])


@EC2LaunchTemplateErrorHandler.list_error_handler("describe launch templates", [])
@AWSRetry.jittered_backoff()
def describe_launch_templates(
    client,
    launch_template_ids: Optional[List[str]] = None,
    launch_template_names: Optional[List[str]] = None,
    filters: Optional[List[Dict[str, List[str]]]] = None,
) -> List[Dict[str, Any]]:
    params = {}
    if launch_template_ids:
        params["LaunchTemplateIds"] = launch_template_ids
    if launch_template_names:
        params["LaunchTemplateNames"] = launch_template_names
    if filters:
        params["Filters"] = filters
    paginator = client.get_paginator("describe_launch_templates")
    return paginator.paginate(**params).build_full_result()["LaunchTemplates"]


@EC2LaunchTemplateErrorHandler.common_error_handler("describe launch template versions")
@AWSRetry.jittered_backoff()
def describe_launch_template_versions(client, **params: Dict[str, Any]) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("describe_launch_template_versions")
    return paginator.paginate(**params).build_full_result()["LaunchTemplateVersions"]


@EC2LaunchTemplateErrorHandler.common_error_handler("delete launch template versions")
@AWSRetry.jittered_backoff()
def delete_launch_template_versions(
    client, versions: List[str], launch_template_id: Optional[str] = None, launch_template_name: Optional[str] = None
) -> Dict[str, Any]:
    params = {}
    if launch_template_id:
        params["LaunchTemplateId"] = launch_template_id
    if launch_template_name:
        params["LaunchTemplateName"] = launch_template_name
    response = {
        "UnsuccessfullyDeletedLaunchTemplateVersions": [],
        "SuccessfullyDeletedLaunchTemplateVersions": [],
    }
    # Using this API, You can specify up to 200 launch template version numbers.
    for i in range(0, len(versions), 200):
        result = client.delete_launch_template_versions(Versions=list(versions[i : i + 200]), **params)
        for x in ("SuccessfullyDeletedLaunchTemplateVersions", "UnsuccessfullyDeletedLaunchTemplateVersions"):
            response[x] += result.get(x, [])
    return response


@EC2LaunchTemplateErrorHandler.common_error_handler("delete launch template")
@AWSRetry.jittered_backoff()
def delete_launch_template(
    client, launch_template_id: Optional[str] = None, launch_template_name: Optional[str] = None
) -> Dict[str, Any]:
    params = {}
    if launch_template_id:
        params["LaunchTemplateId"] = launch_template_id
    if launch_template_name:
        params["LaunchTemplateName"] = launch_template_name
    return client.delete_launch_template(**params)["LaunchTemplate"]


@EC2LaunchTemplateErrorHandler.common_error_handler("create launch template")
@AWSRetry.jittered_backoff()
def create_launch_template(
    client,
    launch_template_name: str,
    launch_template_data: Dict[str, Any],
    tags: Optional[EC2TagSpecifications] = None,
    **kwargs: Dict[str, Any],
) -> Dict[str, Any]:
    params = {"LaunchTemplateName": launch_template_name, "LaunchTemplateData": launch_template_data}
    if tags:
        params["TagSpecifications"] = boto3_tag_specifications(tags, types="launch-template")
    params.update(kwargs)
    return client.create_launch_template(**params)["LaunchTemplate"]


@EC2LaunchTemplateErrorHandler.common_error_handler("create launch template version")
@AWSRetry.jittered_backoff()
def create_launch_template_version(
    client, launch_template_data: Dict[str, Any], **params: Dict[str, Any]
) -> Dict[str, Any]:
    return client.create_launch_template_version(LaunchTemplateData=launch_template_data, **params)[
        "LaunchTemplateVersion"
    ]


@EC2LaunchTemplateErrorHandler.common_error_handler("modify launch template")
@AWSRetry.jittered_backoff()
def modify_launch_template(client, **params: Dict[str, Any]) -> Dict[str, Any]:
    return client.modify_launch_template(**params)["LaunchTemplate"]


def get_ec2_security_group_ids_from_names(sec_group_list, ec2_connection, vpc_id=None, boto3=None):
    """Return list of security group IDs from security group names. Note that security group names are not unique
    across VPCs.  If a name exists across multiple VPCs and no VPC ID is supplied, all matching IDs will be returned. This
    will probably lead to a boto exception if you attempt to assign both IDs to a resource so ensure you wrap the call in
    a try block
    """

    def get_sg_name(sg):
        return str(sg["GroupName"])

    def get_sg_id(sg):
        return str(sg["GroupId"])

    if boto3 is not None:
        ansible_warnings.deprecate(
            (
                "The boto3 parameter for get_ec2_security_group_ids_from_names() has been deprecated."
                "The parameter has been ignored since release 4.0.0."
            ),
            version="10.0.0",
            collection_name="amazon.aws",
        )

    sec_group_id_list = []

    if isinstance(sec_group_list, string_types):
        sec_group_list = [sec_group_list]

    # Get all security groups
    if vpc_id:
        filters = [
            {
                "Name": "vpc-id",
                "Values": [
                    vpc_id,
                ],
            }
        ]
        all_sec_groups = ec2_connection.describe_security_groups(Filters=filters)["SecurityGroups"]
    else:
        all_sec_groups = ec2_connection.describe_security_groups()["SecurityGroups"]

    unmatched = set(sec_group_list).difference(str(get_sg_name(all_sg)) for all_sg in all_sec_groups)
    sec_group_name_list = list(set(sec_group_list) - set(unmatched))

    if len(unmatched) > 0:
        # If we have unmatched names that look like an ID, assume they are
        sec_group_id_list[:] = [sg for sg in unmatched if re.match("sg-[a-fA-F0-9]+$", sg)]
        still_unmatched = [sg for sg in unmatched if not re.match("sg-[a-fA-F0-9]+$", sg)]
        if len(still_unmatched) > 0:
            raise ValueError(f"The following group names are not valid: {', '.join(still_unmatched)}")

    sec_group_id_list += [get_sg_id(all_sg) for all_sg in all_sec_groups if get_sg_name(all_sg) in sec_group_name_list]

    return sec_group_id_list


# EC2 Transit Gateway VPC Attachment Error handler
class EC2TransitGatewayVPCAttachmentErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidGatewayID.NotFound")


@EC2TransitGatewayVPCAttachmentErrorHandler.common_error_handler("describe transit gateway vpc attachments")
@AWSRetry.jittered_backoff()
def describe_transit_gateway_vpc_attachments(
    client, **params: Dict[str, Union[List[str], bool, List[Dict[str, Union[str, List[str]]]]]]
) -> List:
    paginator = client.get_paginator("describe_transit_gateway_vpc_attachments")
    return paginator.paginate(**params).build_full_result()["TransitGatewayVpcAttachments"]


@EC2TransitGatewayVPCAttachmentErrorHandler.common_error_handler("create transit gateway vpc attachment")
@AWSRetry.jittered_backoff()
def create_transit_gateway_vpc_attachment(
    client, **params: Dict[str, Union[List[str], bool, List[Dict[str, Union[str, List[str]]]]]]
) -> Dict[str, Any]:
    return client.create_transit_gateway_vpc_attachment(**params)["TransitGatewayVpcAttachment"]


@EC2TransitGatewayVPCAttachmentErrorHandler.common_error_handler("modify transit gateway vpc attachment")
@AWSRetry.jittered_backoff()
def modify_transit_gateway_vpc_attachment(
    client, **params: Dict[str, Union[List[str], bool, List[Dict[str, Union[str, List[str]]]]]]
) -> Dict[str, Any]:
    return client.modify_transit_gateway_vpc_attachment(**params)["TransitGatewayVpcAttachment"]


@EC2TransitGatewayVPCAttachmentErrorHandler.deletion_error_handler("delete transit gateway vpc attachment")
@AWSRetry.jittered_backoff()
def delete_transit_gateway_vpc_attachment(client, transit_gateway_attachment_id: str) -> bool:
    client.delete_transit_gateway_vpc_attachment(TransitGatewayAttachmentId=transit_gateway_attachment_id)[
        "TransitGatewayVpcAttachment"
    ]
    return True


def add_ec2_tags(client, module, resource_id, tags_to_set, retry_codes=None):
    """
    Sets Tags on an EC2 resource.

    :param client: an EC2 boto3 client
    :param module: an AnsibleAWSModule object
    :param resource_id: the identifier for the resource
    :param tags_to_set: A dictionary of key/value pairs to set
    :param retry_codes: additional boto3 error codes to trigger retries
    """

    if not tags_to_set:
        return False
    if module.check_mode:
        return True

    if not retry_codes:
        retry_codes = []

    try:
        tags_to_add = ansible_dict_to_boto3_tag_list(tags_to_set)
        AWSRetry.jittered_backoff(retries=10, catch_extra_error_codes=retry_codes)(client.create_tags)(
            Resources=[resource_id], Tags=tags_to_add
        )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg=f"Unable to add tags {tags_to_set} to {resource_id}")
    return True


def remove_ec2_tags(client, module, resource_id, tags_to_unset, retry_codes=None):
    """
    Removes Tags from an EC2 resource.

    :param client: an EC2 boto3 client
    :param module: an AnsibleAWSModule object
    :param resource_id: the identifier for the resource
    :param tags_to_unset: a list of tag keys to removes
    :param retry_codes: additional boto3 error codes to trigger retries
    """

    if not tags_to_unset:
        return False
    if module.check_mode:
        return True

    if not retry_codes:
        retry_codes = []

    tags_to_remove = [dict(Key=tagkey) for tagkey in tags_to_unset]

    try:
        AWSRetry.jittered_backoff(retries=10, catch_extra_error_codes=retry_codes)(client.delete_tags)(
            Resources=[resource_id], Tags=tags_to_remove
        )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg=f"Unable to delete tags {tags_to_unset} from {resource_id}")
    return True


def describe_ec2_tags(client, module, resource_id, resource_type=None, retry_codes=None):
    """
    Performs a paginated search of EC2 resource tags.

    :param client: an EC2 boto3 client
    :param module: an AnsibleAWSModule object
    :param resource_id: the identifier for the resource
    :param resource_type: the type of the resource
    :param retry_codes: additional boto3 error codes to trigger retries
    """
    filters = {"resource-id": resource_id}
    if resource_type:
        filters["resource-type"] = resource_type
    filters = ansible_dict_to_boto3_filter_list(filters)

    if not retry_codes:
        retry_codes = []

    try:
        retry_decorator = AWSRetry.jittered_backoff(retries=10, catch_extra_error_codes=retry_codes)
        results = paginated_query_with_retries(
            client, "describe_tags", retry_decorator=retry_decorator, Filters=filters
        )
        return boto3_tag_list_to_ansible_dict(results.get("Tags", None))
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg=f"Failed to describe tags for EC2 Resource: {resource_id}")


def ensure_ec2_tags(client, module, resource_id, resource_type=None, tags=None, purge_tags=True, retry_codes=None):
    """
    Updates the tags on an EC2 resource.

    To remove all tags the tags parameter must be explicitly set to an empty dictionary.

    :param client: an EC2 boto3 client
    :param module: an AnsibleAWSModule object
    :param resource_id: the identifier for the resource
    :param resource_type: the type of the resource
    :param tags: the Tags to apply to the resource
    :param purge_tags: whether tags missing from the tag list should be removed
    :param retry_codes: additional boto3 error codes to trigger retries
    :return: changed: returns True if the tags are changed
    """

    if tags is None:
        return False

    if not retry_codes:
        retry_codes = []

    changed = False
    current_tags = describe_ec2_tags(client, module, resource_id, resource_type, retry_codes)

    tags_to_set, tags_to_unset = compare_aws_tags(current_tags, tags, purge_tags)

    if purge_tags and not tags:
        tags_to_unset = current_tags

    changed |= remove_ec2_tags(client, module, resource_id, tags_to_unset, retry_codes)
    changed |= add_ec2_tags(client, module, resource_id, tags_to_set, retry_codes)

    return changed


def normalize_ec2_vpc_dhcp_config(option_config: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    The boto2 module returned a config dict, but boto3 returns a list of dicts
    Make the data we return look like the old way, so we don't break users.
    This is also much more user-friendly.
    boto3:
        'DhcpConfigurations': [
            {'Key': 'domain-name', 'Values': [{'Value': 'us-west-2.compute.internal'}]},
            {'Key': 'domain-name-servers', 'Values': [{'Value': 'AmazonProvidedDNS'}]},
            {'Key': 'netbios-name-servers', 'Values': [{'Value': '1.2.3.4'}, {'Value': '5.6.7.8'}]},
            {'Key': 'netbios-node-type', 'Values': [1]},
            {'Key': 'ntp-servers', 'Values': [{'Value': '1.2.3.4'}, {'Value': '5.6.7.8'}]}
        ],
    The module historically returned:
        "new_options": {
            "domain-name": "ec2.internal",
            "domain-name-servers": ["AmazonProvidedDNS"],
            "netbios-name-servers": ["10.0.0.1", "10.0.1.1"],
            "netbios-node-type": "1",
            "ntp-servers": ["10.0.0.2", "10.0.1.2"]
        },
    """
    config_data = {}

    if len(option_config) == 0:
        # If there is no provided config, return the empty dictionary
        return config_data

    for config_item in option_config:
        # Handle single value keys
        if config_item["Key"] == "netbios-node-type":
            if isinstance(config_item["Values"], integer_types):
                config_data["netbios-node-type"] = str((config_item["Values"]))
            elif isinstance(config_item["Values"], list):
                config_data["netbios-node-type"] = str((config_item["Values"][0]["Value"]))
        # Handle actual lists of values
        for option in ["domain-name", "domain-name-servers", "ntp-servers", "netbios-name-servers"]:
            if config_item["Key"] == option:
                config_data[option] = [val["Value"] for val in config_item["Values"]]

    return config_data


def determine_iam_arn_from_name(iam_client, name_or_arn: str) -> str:
    if validate_aws_arn(name_or_arn, service="iam", resource_type="instance-profile"):
        return name_or_arn

    iam_instance_profiles = list_iam_instance_profiles(iam_client, name=name_or_arn)
    if not iam_instance_profiles:
        raise AnsibleEC2Error(message=f"Could not find IAM instance profile {name_or_arn}")
    return iam_instance_profiles[0]["Arn"]


# EC2 Transit Gateway
class EC2TransitGatewayErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidTransitGatewayID.NotFound")


@EC2TransitGatewayErrorHandler.list_error_handler("describe transit gateway", [])
@AWSRetry.jittered_backoff()
def describe_ec2_transit_gateways(
    client, **params: Dict[str, Union[List[str], List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("describe_transit_gateways")
    return paginator.paginate(**params).build_full_result()["TransitGateways"]


@EC2TransitGatewayErrorHandler.common_error_handler("create transit gateway")
@AWSRetry.jittered_backoff()
def create_ec2_transit_gateway(
    client, **params: Dict[str, Union[List[str], List[Dict[str, Union[str, List[str]]]]]]
) -> Dict[str, Any]:
    return client.create_transit_gateway(**params)["TransitGateway"]


@EC2TransitGatewayErrorHandler.deletion_error_handler("delete transit gateway")
@AWSRetry.jittered_backoff()
def delete_ec2_transit_gateway(client, transit_gateway_id: str) -> bool:
    client.delete_transit_gateway(TransitGatewayId=transit_gateway_id)
    return True


# EC2 Dedicated host
class EC2DedicatedHost(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleEC2Error

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("InvalidHostID.NotFound")


@EC2DedicatedHost.list_error_handler("describe dedicated host", [])
@AWSRetry.jittered_backoff()
def describe_ec2_dedicated_hosts(
    client, **params: Dict[str, Union[List[str], List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("describe_hosts")
    return paginator.paginate(**params).build_full_result()["Hosts"]


@EC2DedicatedHost.list_error_handler("describe mac dedicated host", [])
@AWSRetry.jittered_backoff()
def describe_ec2_mac_dedicated_hosts(
    client, **params: Dict[str, Union[List[str], List[Dict[str, Union[str, List[str]]]]]]
) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("describe_mac_hosts")
    return paginator.paginate(**params).build_full_result()["MacHosts"]


@EC2DedicatedHost.deletion_error_handler("release dedicated host")
@AWSRetry.jittered_backoff()
def release_ec2_dedicated_host(client, host_id: Union[str, List[str]]) -> bool:
    host_ids = host_id
    if isinstance(host_id, string_types):
        host_ids = [host_id]
    client.release_hosts(HostIds=host_ids)
    return True


@EC2DedicatedHost.common_error_handler("allocate dedicated hosts")
@AWSRetry.jittered_backoff()
def allocate_ec2_dedicated_hosts(
    client, availability_zone: str, **params: Dict[str, Union[List[str], List[Dict[str, Union[str, List[str]]]]]]
) -> List[str]:
    return client.allocate_hosts(AvailabilityZone=availability_zone, **params)["HostIds"]


@EC2DedicatedHost.common_error_handler("modify dedicated hosts")
@AWSRetry.jittered_backoff()
def modify_ec2_dedicated_hosts(
    client,
    host_id: Union[List[str], str],
    **params: Dict[str, Union[List[str], List[Dict[str, Union[str, List[str]]]]]],
) -> Dict[str, Any]:
    host_ids = host_id
    if isinstance(host_id, string_types):
        host_ids = [host_id]
    return client.modify_hosts(HostIds=host_ids, **params)
