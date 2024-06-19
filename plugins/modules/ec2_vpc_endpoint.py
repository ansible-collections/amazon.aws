#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: ec2_vpc_endpoint
short_description: Create and delete AWS VPC endpoints
version_added: 1.0.0
description:
  - Creates AWS VPC endpoints.
  - Deletes AWS VPC endpoints.
  - This module supports check mode.
options:
  vpc_id:
    description:
      - Required when creating a VPC endpoint.
    required: false
    type: str
  vpc_endpoint_type:
    description:
      - The type of endpoint.
    required: false
    default: Gateway
    choices: [ "Interface", "Gateway", "GatewayLoadBalancer" ]
    type: str
    version_added: 1.5.0
  vpc_endpoint_subnets:
    description:
      - The list of subnets to attach to the endpoint.
      - Requires O(vpc_endpoint_type=GatewayLoadBalancer) or O(vpc_endpoint_type=Interface).
    required: false
    type: list
    elements: str
    version_added: 2.1.0
  vpc_endpoint_security_groups:
    description:
      - The list of security groups to attach to the endpoint.
      - Requires O(vpc_endpoint_type=GatewayLoadBalancer) or O(vpc_endpoint_type=Interface).
    required: false
    type: list
    elements: str
    version_added: 2.1.0
  service:
    description:
      - An AWS supported VPC endpoint service. Use the M(amazon.aws.ec2_vpc_endpoint_info)
        module to describe the supported endpoint services.
      - Required when creating an endpoint.
    required: false
    type: str
  policy:
    description:
      - A properly formatted JSON policy as string, see
        U(https://github.com/ansible/ansible/issues/7005#issuecomment-42894813).
      - Option when creating an endpoint. If not provided AWS will
        utilise a default policy which provides full access to the service.
    required: false
    type: json
  state:
    description:
      - V(present) to ensure resource is created.
      - V(absent) to remove resource.
    required: false
    default: present
    choices: [ "present", "absent" ]
    type: str
  wait:
    description:
      - When specified, will wait for status to reach available for O(state=present).
      - Unfortunately this is ignored for delete actions due to a difference in
        behaviour from AWS.
    required: false
    default: false
    type: bool
  wait_timeout:
    description:
      - Used in conjunction with O(wait).
      - Number of seconds to wait for status.
      - Unfortunately this is ignored for delete actions due to a difference in
        behaviour from AWS.
    required: false
    default: 320
    type: int
  route_table_ids:
    description:
      - List of one or more route table IDs to attach to the endpoint.
      - A route is added to the route table with the destination of the
        endpoint if provided.
      - Route table IDs are only valid for Gateway endpoints.
    required: false
    type: list
    elements: str
  vpc_endpoint_id:
    description:
      - One or more VPC endpoint IDs to remove from the AWS account.
      - Required if O(state=absent).
    required: false
    type: str
  client_token:
    description:
      - Optional client token to ensure idempotency.
    required: false
    type: str
author:
  - Karen Cheng (@Etherdaemon)
notes:
  - Support for O(tags) and I(purge_tags) was added in release 1.5.0.
  - The I(policy_file) paramater was removed in release 6.0.0 please use the
    O(policy) option and the P(ansible.builtin.file#lookup) lookup plugin instead.
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create new vpc endpoint with a json template for policy
  amazon.aws.ec2_vpc_endpoint:
    state: present
    region: ap-southeast-2
    vpc_id: vpc-12345678
    service: com.amazonaws.ap-southeast-2.s3
    policy: " {{ lookup( 'template', 'endpoint_policy.json.j2') }} "
    route_table_ids:
      - rtb-12345678
      - rtb-87654321
  register: new_vpc_endpoint

- name: Create new vpc endpoint with the default policy
  amazon.aws.ec2_vpc_endpoint:
    state: present
    region: ap-southeast-2
    vpc_id: vpc-12345678
    service: com.amazonaws.ap-southeast-2.s3
    route_table_ids:
      - rtb-12345678
      - rtb-87654321
  register: new_vpc_endpoint

- name: Delete newly created vpc endpoint
  amazon.aws.ec2_vpc_endpoint:
    state: absent
    vpc_endpoint_id: "{{ new_vpc_endpoint.result['VpcEndpointId'] }}"
    region: ap-southeast-2
"""

RETURN = r"""
endpoints:
  description: The resulting endpoints from the module call.
  returned: success
  type: list
  elements: dict
  contains:
    creation_timestamp:
      description: The date and time that the endpoint was created.
      returned: always
      type: str
    dns_entries:
      description: List of DNS entires for the endpoint.
      returned: always
      type: list
      elements: dict
      contains:
        dns_name:
          description: The DNS name.
          returned: always
          type: str
        hosted_zone_id:
          description: The ID of the private hosted zone.
          type: str
    groups:
      description: List of security groups associated with the network interface.
      returned: always
      type: list
      elements: dict
      contains:
        group_id:
          description: The ID of the security group.
          returned: always
          type: str
        group_name:
          description: The name of the security group.
          returned: always
          type: str
    ip_address_type:
      description: The IP address type for the endpoint.
      type: str
    network_interface_ids:
      description: List of network interfaces for the endpoint.
      returned: always
      type: list
      elements: str
    owner_id:
      description: The ID of the AWS account that owns the endpoint.
      returned: always
      type: str
    policy_document:
      description: The policy document associated with the endpoint.
      returned: always
      type: str
    private_dns_enabled:
      description: Indicates whether the VPC is associated with a private hosted zone.
      returned: always
      type: bool
    requester_managed:
      description: Indicated whether the endpoint is being managed by its service.
      returned: always
      type: bool
    route_table_ids:
      description: List of route table IDs associated with the endpoint.
      returned: always
      type: list
      elements: str
    service_name:
      description: The name of the service to which the endpoint is associated.
      returned: always
      type: str
    state:
      description: The state of the endpoint.
      returned: always
      type: str
    subnet_ids:
      description: List of subnets associated with the endpoint.
      returned: always
      type: list
    tags:
      description: List of tags associated with the endpoint.
      returned: always
      type: list
      elements: dict
    vpc_endpoint_id:
      description: The ID of the endpoint.
      returned: always
      type: str
    vpc_endpoint_type:
      description: The type of endpoint.
      returned: always
      type: str
    vpc_id:
      description: The ID of the VPC.
      returned: always
      type: str
"""

import datetime
import json
import traceback
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.six import string_types

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.botocore import normalize_boto3_result
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import create_vpc_endpoint
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import delete_vpc_endpoints
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_vpc_endpoints
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import is_ansible_aws_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications
from ansible_collections.amazon.aws.plugins.module_utils.waiters import wait_for_resource_state


def get_endpoints(client, params: Dict[str, Any], endpoint_id: Optional[str] = None) -> List[Dict[str, Any]]:
    api_params = dict()
    if endpoint_id:
        api_params["VpcEndpointIds"] = [endpoint_id]
    else:
        filters = list()
        if params.get("service"):
            filters.append({"Name": "service-name", "Values": [params.get("service")]})
        if params.get("vpc_id"):
            filters.append({"Name": "vpc-id", "Values": [params.get("vpc_id")]})
        api_params["Filters"] = filters
    result = describe_vpc_endpoints(client, **api_params)

    # normalize iso datetime fields in result
    normalized_result = normalize_boto3_result(result)
    return normalized_result


def match_endpoints(route_table_ids, service_name, vpc_id, endpoint):
    found = False
    sorted_route_table_ids = []

    if route_table_ids:
        sorted_route_table_ids = sorted(route_table_ids)

    if endpoint["VpcId"] == vpc_id and endpoint["ServiceName"] == service_name:
        sorted_endpoint_rt_ids = sorted(endpoint["RouteTableIds"])
        if sorted_endpoint_rt_ids == sorted_route_table_ids:
            found = True
    return found


def setup_creation(client, module: AnsibleAWSModule) -> Tuple[bool, Dict[str, Any]]:
    endpoint_id = module.params.get("vpc_endpoint_id")
    route_table_ids = module.params.get("route_table_ids")
    service_name = module.params.get("service")
    vpc_id = module.params.get("vpc_id")
    changed = False

    if not endpoint_id:
        # Try to use the module parameters to match any existing endpoints
        all_endpoints = get_endpoints(client, module.params, endpoint_id)
        for endpoint in all_endpoints:
            if match_endpoints(route_table_ids, service_name, vpc_id, endpoint):
                endpoint_id = endpoint["VpcEndpointId"]
                break

    if endpoint_id:
        # If we have an endpoint now, just ensure tags and exit
        if module.params.get("tags"):
            changed |= ensure_ec2_tags(
                client,
                module,
                endpoint_id,
                resource_type="vpc-endpoint",
                tags=module.params.get("tags"),
                purge_tags=module.params.get("purge_tags"),
            )
        normalized_result = get_endpoints(client, module.params, endpoint_id=endpoint_id)[0]
        return changed, camel_dict_to_snake_dict(normalized_result, ignore_list=["Tags"])

    changed, result = create_aws_vpc_endpoint(client, module)

    return changed, camel_dict_to_snake_dict(result, ignore_list=["Tags"])


def create_aws_vpc_endpoint(client, module: AnsibleAWSModule) -> Tuple[bool, Dict[str, Any]]:
    params = {}
    changed = False
    token_provided = False
    params["VpcId"] = module.params.get("vpc_id")
    params["VpcEndpointType"] = module.params.get("vpc_endpoint_type")
    params["ServiceName"] = module.params.get("service")

    if module.params.get("vpc_endpoint_type") != "Gateway" and module.params.get("route_table_ids"):
        module.fail_json(msg="Route table IDs are only supported for Gateway type VPC Endpoint.")

    if module.check_mode:
        changed = True
        result = "Would have created VPC Endpoint if not in check mode"
        module.exit_json(changed=changed, result=result)

    if module.params.get("route_table_ids"):
        params["RouteTableIds"] = module.params.get("route_table_ids")

    if module.params.get("vpc_endpoint_subnets"):
        params["SubnetIds"] = module.params.get("vpc_endpoint_subnets")

    if module.params.get("vpc_endpoint_security_groups"):
        params["SecurityGroupIds"] = module.params.get("vpc_endpoint_security_groups")

    if module.params.get("client_token"):
        token_provided = True
        request_time = datetime.datetime.utcnow()
        params["ClientToken"] = module.params.get("client_token")

    policy = None
    if module.params.get("policy"):
        try:
            policy = json.loads(module.params.get("policy"))
        except ValueError as e:
            module.fail_json(msg=str(e), exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    if policy:
        params["PolicyDocument"] = json.dumps(policy)

    if module.params.get("tags"):
        params["TagSpecifications"] = boto3_tag_specifications(module.params.get("tags"), ["vpc-endpoint"])

    try:
        changed = True
        result = create_vpc_endpoint(client, **params)
        if token_provided and (request_time > result["creation_timestamp"].replace(tzinfo=None)):
            changed = False
        elif module.params.get("wait") and not module.check_mode:
            wait_for_resource_state(
                client,
                module,
                "vpc_endpoint_exists",
                delay=15,
                max_attempts=int(module.params.get("wait_timeout") // 15),
                VpcEndpointIds=[result["VpcEndpointId"]],
            )

    except is_ansible_aws_error_code("IdempotentParameterMismatch"):
        module.fail_json(msg="IdempotentParameterMismatch - updates of endpoints are not allowed by the API")
    except is_ansible_aws_error_code("RouteAlreadyExists"):  # pylint: disable=duplicate-except
        module.fail_json(msg="RouteAlreadyExists for one of the route tables - update is not allowed by the API")
    except AnsibleAWSError as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to create VPC Endpoint.")

    # describe and normalize iso datetime fields in result after adding tags
    normalized_result = get_endpoints(client, module.params, endpoint_id=result["VpcEndpointId"])[0]
    return changed, normalized_result


def setup_removal(client, module: AnsibleAWSModule) -> Tuple[bool, Dict[str, Any]]:
    changed = False

    if module.check_mode:
        try:
            result = {"msg": "Would have deleted VPC Endpoint if not in check mode"}
            changed = True
            exists = describe_vpc_endpoints(client, VpcEndpointIds=[module.params.get("vpc_endpoint_id")])
            if not exists:
                result = {"msg": "Endpoint does not exist, nothing to delete."}
                changed = False
        except AnsibleEC2Error as e:
            module.fail_json_aws(e, msg="Failed to get endpoints")

        return changed, result

    vpc_endpoint_ids = module.params.get("vpc_endpoint_id")
    if isinstance(vpc_endpoint_ids, string_types):
        vpc_endpoint_ids = [vpc_endpoint_ids]

    try:
        result = delete_vpc_endpoints(client, vpc_endpoint_ids)
        if len(result) < len(vpc_endpoint_ids):
            changed = True
        # For some reason delete_vpc_endpoints doesn't throw exceptions it
        # returns a list of failed 'results' instead.  Throw these so we can
        # catch them the way we expect
        for r in result:
            try:
                raise botocore.exceptions.ClientError(r, "delete_vpc_endpoints")
            except is_boto3_error_code("InvalidVpcEndpoint.NotFound"):
                continue

    except AnsibleEC2Error as e:
        module.fail_json_aws(e, "Failed to delete VPC endpoint")
    return changed, result


def main() -> None:
    argument_spec = dict(
        vpc_id=dict(),
        vpc_endpoint_type=dict(default="Gateway", choices=["Interface", "Gateway", "GatewayLoadBalancer"]),
        vpc_endpoint_security_groups=dict(type="list", elements="str"),
        vpc_endpoint_subnets=dict(type="list", elements="str"),
        service=dict(),
        policy=dict(type="json"),
        state=dict(default="present", choices=["present", "absent"]),
        wait=dict(type="bool", default=False),
        wait_timeout=dict(type="int", default=320, required=False),
        route_table_ids=dict(type="list", elements="str"),
        vpc_endpoint_id=dict(),
        client_token=dict(no_log=False),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ["state", "present", ["vpc_id", "service"]],
            ["state", "absent", ["vpc_endpoint_id"]],
        ],
    )

    # Validate Requirements
    state = module.params.get("state")

    if module.params.get("vpc_endpoint_type"):
        if module.params.get("vpc_endpoint_type") == "Gateway":
            if module.params.get("vpc_endpoint_subnets") or module.params.get("vpc_endpoint_security_groups"):
                module.fail_json(
                    msg=(
                        "Parameter vpc_endpoint_subnets and/or vpc_endpoint_security_groups can't be used with Gateway"
                        " endpoint type"
                    )
                )

        if module.params.get("vpc_endpoint_type") == "GatewayLoadBalancer":
            if module.params.get("vpc_endpoint_security_groups"):
                module.fail_json(
                    msg="Parameter vpc_endpoint_security_groups can't be used with GatewayLoadBalancer endpoint type"
                )

        if module.params.get("vpc_endpoint_type") == "Interface":
            if module.params.get("vpc_endpoint_subnets") and not module.params.get("vpc_endpoint_security_groups"):
                module.fail_json(
                    msg=(
                        "Parameter vpc_endpoint_security_groups must be set when endpoint type is Interface and"
                        " vpc_endpoint_subnets is defined"
                    )
                )
            if not module.params.get("vpc_endpoint_subnets") and module.params.get("vpc_endpoint_security_groups"):
                module.fail_json(
                    msg=(
                        "Parameter vpc_endpoint_subnets must be set when endpoint type is Interface and"
                        " vpc_endpoint_security_groups is defined"
                    )
                )

    try:
        ec2 = module.client("ec2")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    try:
        # Ensure resource is present
        if state == "present":
            (changed, results) = setup_creation(ec2, module)
        else:
            (changed, results) = setup_removal(ec2, module)
    except AnsibleEC2Error as e:
        module.fail_json_aws_error(e)

    module.exit_json(changed=changed, result=results)


if __name__ == "__main__":
    main()
