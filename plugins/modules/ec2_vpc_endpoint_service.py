#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


DOCUMENTATION = r"""
---
module: ec2_vpc_endpoint_service
short_description: create, delete VPC endpoint service
version_added: 6.1.0
description:
  - Creates, updates, or deletes AWS Endpoint Services.
  - For more information see the AWS documentation for VPC endpoint services
    U(https://docs.aws.amazon.com/vpc/latest/privatelink/what-is-privatelink.html).
options:
  acceptance_required:
    description:
      - Indicates whether requests from service consumers to create an endpoint to your service must be accepted manually.
    required: false
    default: false
    type: bool
  gateway_load_balancer_arns:
    description:
      - The Amazon Resource Names (ARNs) of the Gateway Load Balancers.
    required: false
    type: list
  network_load_balancer_arns:
    description:
      -  The Amazon Resource Names (ARNs) of the Network Load Balancers.
    required: false
    type: list
  private_dns_name:
    description:
      - (Interface endpoint configuration) The private DNS name to assign to the VPC endpoint service.
    required: false
    type: str
  supported_ip_address_types:
    description:
      -  The supported IP address types.
    choices: ['ipv4', 'ipv6'].
    required: false
    type: list
  service_id:
    description:
      - The ID of the service.
    required: false
    type: str
  state:
    description:
      - Create, delete a VPC endpoint service
    required: false
    default: present
    choices: ['present', 'absent']
    type: str
  permissions:
    description:
     - The list of Amazon Resource Names (ARN) of the principals having access to the service. Permissions are granted to the principals in this list.
     - To grant permissions to all principals, specify an asterisk (*).
    required: false
    default: []
    tyoe: list
notes: []
author:
  - Kristof Imre Szabo (@krisek)
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.boto3
  - amazon.aws.tags
"""

EXAMPLES = r"""
  - name: Gather information about specific NLB
    community.aws.elb_application_lb_info:
      names: "my-nlb"
    register: nlb_info

  - name: Create a VPC Endpoint Service
    ec2_vpc_endpoint_service:
      networkloadbalancer_arns:
      - "{{ nlb_info.load_balancers.0.load_balancer_arn }}"
      state: present
      permissions:
      - arn:aws:iam::111122223333:role/*
    register: endpoint_service
"""

RETURN = r"""
exists:
    description: Whether the resource exists.
    returned: always
    type: bool
    sample: true
endpoint_service:
    description: AWS service configuration record, permissions and tags
    returned: I(state=present)
    type: dict
    contains:
        acceptance_required:
            description:
            - Indicates whether requests from other Amazon Web Services accounts to create an endpoint to the service must first be accepted.
            returned: always
            tpye: bool
            sample:
        availability_zones:
            description: The Availability Zones in which the service is available.
            returned: always
            type: list
        base_endpoint_dns_names:
            description: The DNS names for the service.
            returned: always
            type: list
        manages_vpc_endpoints:
            description:
            - Indicates whether the service manages its VPC endpoints. Management of the service VPC endpoints using the VPC endpoint API is restricted.
            returned: always
            type: bool
        network_load_balancer_arns:
            description: The Amazon Resource Names (ARNs) of the Network Load Balancers for the service.
            returned: if network load balancers are backing the service
            type: list
        gateway_load_balancer_arns:
            description: The Amazon Resource Names (ARNs) of the Gateway Load Balancers for the service.
            returned: if gateway load balancers are backing the service
            type: list
        private_dns_name_configuration:
            description: Information about the endpoint service private DNS name configuration.
            returned: always
            tpye: dict
        service_id:
            description: The ID of the service.
            returned: always
            type: str
        service_name:
            description: The name of the service.
            returned: always
            tpye: str
        service_state:
            description: The service state.
            returned: always
            tpye: str
        service_type:
            description: The type of service. Describes the type of service for a VPC endpoint.
            returned: always
            tpye: dict
        supported_ip_address_types:
            description: The supported IP address types.
            returned: always
            type: list
        permissions:
            description: The list of Amazon Resource Names (ARN) of the principals having access to the service.
            returned: always
            type: list
        tags:
            description: Tags of the endpoint service.
            returned: always
            type: dict
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from datetime import datetime
from typing import Optional

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # Handled by AnsibleAWSModule

ARGUMENT_SPEC = dict(
    state=dict(type="str", choices=['present', 'absent'], default='present'),
    private_dns_name=dict(required=False, type='str'),
    supported_ip_address_types=dict(required=False, type='list', default=["ipv4"], choices=["ipv4", "ipv6"]),
    gateway_load_balancer_arns=dict(required=False, type='list', default=[]),
    network_load_balancer_arns=dict(required=False, type='list', default=[]),
    permissions=dict(required=False, type='list', default=[]),
    purge_permissions=dict(default=False, type='bool'),
    tags=dict(required=False, type='dict', aliases=['resource_tags']),
    acceptance_required=dict(default=False, type='bool'),
    service_id=dict(required=False, type='str'),
)

REQUIRED_IF = [
    ('state', 'absent', ['service_id']),
]

SUPPORTS_CHECK_MODE = True


def format_client_params(
    module: AnsibleAWSModule,
    endpoint_service: dict,
    tags: Optional[dict] = None,
    service_id: Optional[str] = None,
    operation: Optional[str] = None,
) -> dict:
    """
    Formats plan details to match boto3 backup client param expectations.

    module : AnsibleAWSModule object
    endpoint_service: Dict of endpoint service details
    tags: Dict of endpoint service tags
    service_id: ID of endpoint service to update, only needed for update operation
    operation: Operation to add specific params for, either create or update
    """

    params = snake_dict_to_camel_dict(
        {k: v for k, v in endpoint_service.items() if k not in ['permissions', 'purge_permissions', 'service_id', 'update_needed'] and v is not None},
        capitalize_first=True,
    )

    if operation == "create":  # Add create-specific params
        if tags:
            params["TagSpecifications"] = [{'ResourceType': 'vpc-endpoint-service', 'Tags': ansible_dict_to_boto3_tag_list(tags)}]

    elif operation == "update":  # Add update-specific params
        params["ServiceId"] = service_id

    return params


def create_vpc_endpoint_service(module: AnsibleAWSModule, client, create_params: dict) -> dict:

    try:
        response = client.create_vpc_endpoint_service_configuration(**create_params)
    except (
        BotoCoreError,
        ClientError,
    ) as err:
        module.fail_json_aws(err, msg="Failed to create vpc  endpoint service {err}")
    return response


def modify_vpc_endpoint_service(module: AnsibleAWSModule, client, modify_params: dict) -> dict:

    try:
        response = client.modify_vpc_endpoint_service_configuration(**modify_params)
    except (
        BotoCoreError,
        ClientError,
    ) as err:
        module.fail_json_aws(err, msg="Failed to modify vpc endpoint service {err}")
    return response


def delete_vpc_endpoint_service(module: AnsibleAWSModule, client, service_id) -> dict:

    try:
        response = client.delete_vpc_endpoint_service_configurations(ServiceIds=[service_id])
    except (
        BotoCoreError,
        ClientError,
    ) as err:
        module.fail_json_aws(err, msg="Failed to delete endpoint service {err}")
    return response


def get_vpc_endpoint_service_details(module: AnsibleAWSModule, client, endpoint_service: dict) -> dict:

    paginator = client.get_paginator('describe_vpc_endpoint_service_configurations')
    service_configurations = []
    for page in paginator.paginate():
        service_configurations.extend(page['ServiceConfigurations'])

    endpoint_service_nlba = set(endpoint_service.get('network_load_balancer_arns', []))
    endpoint_service_glba = set(endpoint_service.get('gateway_load_balancer_arns', []))

    for service_configuration in service_configurations:
        if (not endpoint_service['service_id'] and
            set(service_configuration.get('NetworkLoadBalancerArns', [])) == endpoint_service_nlba and
                set(service_configuration.get('GatewayLoadBalancerArns', [])) == endpoint_service_glba):
            return camel_dict_to_snake_dict(service_configuration)

        if endpoint_service.get('service_id') == service_configuration.get('ServiceId'):
            return camel_dict_to_snake_dict(service_configuration)

    return None


def vpc_endpoint_update_needed(existing_endpoint_configuration: dict, new_endpoint_configuration: dict) -> dict:
    """
    Determines whether existing and new vpc endpoint configuration matches and update parameters

    existing_endpoint_configuration: Dict of existing ,
        in snake-case format
    new_endpoint_configuration: Dict of new configuration , in
        snake-case format
    """

    update_endpoint_configuration = {
        'update_needed': False,
        'service_id': existing_endpoint_configuration['service_id']
    }

    supported_ip_address_types = existing_endpoint_configuration.get('supported_ip_address_types', [])
    network_load_balancer_arns = existing_endpoint_configuration.get('network_load_balancer_arns', [])
    gateway_load_balancer_arns = existing_endpoint_configuration.get('gateway_load_balancer_arns', [])

    if existing_endpoint_configuration.get('acceptance_required', False) != new_endpoint_configuration.get('acceptance_required', False):
        update_endpoint_configuration['update_needed'] = True

    update_endpoint_configuration['acceptance_required'] = new_endpoint_configuration.get('acceptance_required', False)

    update_endpoint_configuration['remove_private_dns_name'] = False

    existing_private_dns_name = existing_endpoint_configuration.get('private_dns_name', '') or ''
    new_private_dns_name = new_endpoint_configuration.get('private_dns_name', '') or ''

    if existing_private_dns_name != new_private_dns_name:
        update_endpoint_configuration['update_needed'] = True
        update_endpoint_configuration['private_dns_name'] = new_endpoint_configuration.get('private_dns_name')
        if new_endpoint_configuration.get('private_dns_name', '') == '':
            update_endpoint_configuration['remove_private_dns_name'] = True

    #
    # names1: what we have
    # names2: what we want
    # to_remove = list(set(names1) - set(names2))
    # to_add = list(set(names1).symmetric_difference(set(names2)) - set(to_remove))
    #

    for field in ['supported_ip_address_types', 'network_load_balancer_arns', 'gateway_load_balancer_arns']:
        # double protection -- maybe not needed
        if existing_endpoint_configuration.get(field, []) is None:
            existing_endpoint_configuration[field] = []

        update_endpoint_configuration[f'remove_{field}'] = list(set(existing_endpoint_configuration.get(field, [])) - set(new_endpoint_configuration[field]))

        update_endpoint_configuration[f'add_{field}'] = list(
            set(existing_endpoint_configuration.get(field, [])).symmetric_difference(set(new_endpoint_configuration.get(field, []))) -
            set(update_endpoint_configuration[f'remove_{field}'])
        )

        if len(update_endpoint_configuration[f'remove_{field}']) > 0 or len(update_endpoint_configuration[f'add_{field}']) > 0:
            update_endpoint_configuration['update_needed'] = True

    return update_endpoint_configuration


def get_vpc_endpoint_service_permissions(module: AnsibleAWSModule, client, service_id: str) -> list:

    permissions_paginator = client.get_paginator('describe_vpc_endpoint_service_permissions')
    permissions_principals = []
    for page in permissions_paginator.paginate(ServiceId=service_id):
        permissions_principals.extend(page['AllowedPrincipals'])

    permissions = list(map(lambda AllowedPrincipal: AllowedPrincipal.get('Principal'), permissions_principals))
    if permissions is None:
        permissions = []
    return permissions


def vpc_endpoint_service_permissions_update_needed(service_id: str, existing_permissions: list, new_permissions: list, purge_permissions: bool) -> dict:

    update_permissions = {
        'update_needed': False,
        'service_id': service_id
    }

    if purge_permissions:
        update_permissions['remove_allowed_principals'] = list(set(existing_permissions) - set(new_permissions))
    else:
        update_permissions['remove_allowed_principals'] = []

    update_permissions['add_allowed_principals'] = list(set(existing_permissions).symmetric_difference(set(new_permissions)) - set(existing_permissions))

    if len(update_permissions['remove_allowed_principals']) > 0 or len(update_permissions['add_allowed_principals']) > 0:
        update_permissions['update_needed'] = True

    return update_permissions


def modify_vpc_endpoint_service_permissions(module: AnsibleAWSModule, client, permission_params: list) -> dict:

    try:
        response = client.modify_vpc_endpoint_service_permissions(**permission_params)
    except (
        BotoCoreError,
        ClientError,
    ) as err:
        module.fail_json_aws(err, msg="Failed to modify permissions {err}")
    return response


def format_check_mode_response(endpoint_service: dict, tags: dict, delete: bool = False) -> dict:

    timestamp = datetime.now().isoformat()
    if delete:
        return {
            "endpoint_service": endpoint_service,
            "deletion_date": timestamp,
            "version_id": "",
        }
    else:
        return {
            "creation_date": timestamp,
            "version_id": "",
            "endpoint_service": dict({'tags': tags}, **endpoint_service),
        }


def main():
    module = AnsibleAWSModule(
        argument_spec=ARGUMENT_SPEC,
        required_if=REQUIRED_IF,
        supports_check_mode=SUPPORTS_CHECK_MODE,
    )

    # Set initial result values
    result = dict(changed=False, exists=False)
    client = module.client("ec2", retry_decorator=AWSRetry.jittered_backoff())
    state = module.params["state"]
    endpoint_service = {
        "private_dns_name": module.params["private_dns_name"],
        "supported_ip_address_types": module.params["supported_ip_address_types"],
        "gateway_load_balancer_arns": module.params["gateway_load_balancer_arns"],
        "network_load_balancer_arns": module.params["network_load_balancer_arns"],
        "permissions": module.params["permissions"],
        "purge_permissions": module.params["purge_permissions"],
        "acceptance_required": module.params["acceptance_required"],
        "service_id": module.params["service_id"],
    }

    tags = module.params["tags"]
    existing_endpoint_service = get_vpc_endpoint_service_details(module, client, endpoint_service)

    if state == "present":  # Create or update endpoint service
        if existing_endpoint_service is None:  # endpoint service doesn't exist create it
            resulting_endpoint_service = {}
            if module.check_mode:  # Use supplied params as result data in check mode
                resulting_endpoint_service = format_check_mode_response(endpoint_service, tags)
            else:
                client_params = format_client_params(module, endpoint_service, tags=tags, operation="create")
                response = create_vpc_endpoint_service(module, client, client_params)
                resulting_endpoint_service = camel_dict_to_snake_dict(response.get('ServiceConfiguration'))
                if 'tags' in resulting_endpoint_service:
                    resulting_endpoint_service['tags'] = boto3_tag_list_to_ansible_dict(resulting_endpoint_service['tags'])
                if len(endpoint_service.get('permissions', [])) > 0:
                    permission_params = {
                        'ServiceId': response.get('ServiceConfiguration').get('ServiceId'),
                        'AddAllowedPrincipals': endpoint_service['permissions'],
                    }
                    response_permissions = modify_vpc_endpoint_service_permissions(module, client, permission_params)
                    resulting_endpoint_service['permissions'] = endpoint_service['permissions']

            result["exists"] = True
            result["changed"] = True
            result['endpoint_service'] = resulting_endpoint_service

        else:  # Endpoint service exists, update as needed
            result["exists"] = True
            service_id = existing_endpoint_service['service_id']

            # configuration changes
            update_endpoint_configuration = vpc_endpoint_update_needed(existing_endpoint_service, endpoint_service)
            if update_endpoint_configuration.get('update_needed', False):
                if not module.check_mode:
                    client_params = format_client_params(module, update_endpoint_configuration, tags=tags, operation="update", service_id=service_id)
                    response = modify_vpc_endpoint_service(module, client, client_params)
                    result["changed"] = True

            # permission changes
            update_permissions = vpc_endpoint_service_permissions_update_needed(
                service_id,
                get_vpc_endpoint_service_permissions(module, client, service_id), endpoint_service.get('permissions', []),
                endpoint_service.get('purge_permissions', False)
            )
            if update_permissions['update_needed']:
                if not module.check_mode:
                    client_params = format_client_params(module, update_permissions, operation="update", service_id=service_id)
                    response_permissions = modify_vpc_endpoint_service_permissions(module, client, client_params)
                    result["changed"] = True

            # now we see what we have done
            resulting_endpoint_service = get_vpc_endpoint_service_details(module, client, existing_endpoint_service)
            if 'tags' in resulting_endpoint_service:
                resulting_endpoint_service['tags'] = boto3_tag_list_to_ansible_dict(resulting_endpoint_service['tags'])
            resulting_endpoint_service['permissions'] = get_vpc_endpoint_service_permissions(module, client, service_id)
            result['endpoint_service'] = resulting_endpoint_service

    elif state == "absent":  # Delete endpoint service
        if existing_endpoint_service is None:  # Endpoint service does not exist, can't delete it
            module.debug(msg=f"Endpoint service {endpoint_service.service_id} not found.")
        else:  # Plan exists, delete it
            if module.check_mode:
                response = format_check_mode_response(endpoint_service, tags, True)
            else:
                response = delete_vpc_endpoint_service(module, client, endpoint_service['service_id'])
            result["changed"] = True
            result["exists"] = False
            # result.update(camel_dict_to_snake_dict(response))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
