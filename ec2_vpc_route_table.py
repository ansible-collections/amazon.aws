#!/usr/bin/python
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: ec2_vpc_route_table
version_added: 1.0.0
short_description: Manage route tables for AWS virtual private clouds
description:
    - Manage route tables for AWS virtual private clouds
author:
- Robert Estelle (@erydo)
- Rob White (@wimnat)
- Will Thames (@willthames)
options:
  lookup:
    description: Look up route table by either tags or by route table ID. Non-unique tag lookup will fail.
      If no tags are specified then no lookup for an existing route table is performed and a new
      route table will be created. To change tags of a route table you must look up by id.
    default: tag
    choices: [ 'tag', 'id' ]
    type: str
  propagating_vgw_ids:
    description: Enable route propagation from virtual gateways specified by ID.
    type: list
    elements: str
  purge_routes:
    description: Purge existing routes that are not found in routes.
    type: bool
    default: 'yes'
  purge_subnets:
    description: Purge existing subnets that are not found in subnets. Ignored unless the subnets option is supplied.
    default: 'true'
    type: bool
  purge_tags:
    description: Purge existing tags that are not found in route table.
    type: bool
    default: 'no'
  route_table_id:
    description:
    - The ID of the route table to update or delete.
    - Required when I(lookup=id).
    type: str
  routes:
    description: List of routes in the route table.
        Routes are specified as dicts containing the keys 'dest' and one of 'gateway_id',
        'instance_id', 'network_interface_id', or 'vpc_peering_connection_id'.
        If 'gateway_id' is specified, you can refer to the VPC's IGW by using the value 'igw'.
        Routes are required for present states.
    type: list
    elements: dict
  state:
    description: Create or destroy the VPC route table.
    default: present
    choices: [ 'present', 'absent' ]
    type: str
  subnets:
    description: An array of subnets to add to this route table. Subnets may be specified
      by either subnet ID, Name tag, or by a CIDR such as '10.0.0.0/24'.
    type: list
    elements: str
  tags:
    description: >
      A dictionary of resource tags of the form: C({ tag1: value1, tag2: value2 }). Tags are
      used to uniquely identify route tables within a VPC when the route_table_id is not supplied.
    aliases: [ "resource_tags" ]
    type: dict
  vpc_id:
    description:
    - VPC ID of the VPC in which to create the route table.
    - Required when I(state=present) or I(lookup=tag).
    type: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Basic creation example:
- name: Set up public subnet route table
  community.aws.ec2_vpc_route_table:
    vpc_id: vpc-1245678
    region: us-west-1
    tags:
      Name: Public
    subnets:
      - "{{ jumpbox_subnet.subnet.id }}"
      - "{{ frontend_subnet.subnet.id }}"
      - "{{ vpn_subnet.subnet_id }}"
    routes:
      - dest: 0.0.0.0/0
        gateway_id: "{{ igw.gateway_id }}"
  register: public_route_table

- name: Set up NAT-protected route table
  community.aws.ec2_vpc_route_table:
    vpc_id: vpc-1245678
    region: us-west-1
    tags:
      Name: Internal
    subnets:
      - "{{ application_subnet.subnet.id }}"
      - 'Database Subnet'
      - '10.0.0.0/8'
    routes:
      - dest: 0.0.0.0/0
        instance_id: "{{ nat.instance_id }}"
  register: nat_route_table

- name: delete route table
  community.aws.ec2_vpc_route_table:
    vpc_id: vpc-1245678
    region: us-west-1
    route_table_id: "{{ route_table.id }}"
    lookup: id
    state: absent
'''

RETURN = r'''
route_table:
  description: Route Table result
  returned: always
  type: complex
  contains:
    associations:
      description: List of subnets associated with the route table
      returned: always
      type: complex
      contains:
        main:
          description: Whether this is the main route table
          returned: always
          type: bool
          sample: false
        route_table_association_id:
          description: ID of association between route table and subnet
          returned: always
          type: str
          sample: rtbassoc-ab47cfc3
        route_table_id:
          description: ID of the route table
          returned: always
          type: str
          sample: rtb-bf779ed7
        subnet_id:
          description: ID of the subnet
          returned: always
          type: str
          sample: subnet-82055af9
    id:
      description: ID of the route table (same as route_table_id for backwards compatibility)
      returned: always
      type: str
      sample: rtb-bf779ed7
    propagating_vgws:
      description: List of Virtual Private Gateways propagating routes
      returned: always
      type: list
      sample: []
    route_table_id:
      description: ID of the route table
      returned: always
      type: str
      sample: rtb-bf779ed7
    routes:
      description: List of routes in the route table
      returned: always
      type: complex
      contains:
        destination_cidr_block:
          description: CIDR block of destination
          returned: always
          type: str
          sample: 10.228.228.0/22
        gateway_id:
          description: ID of the gateway
          returned: when gateway is local or internet gateway
          type: str
          sample: local
        instance_id:
          description: ID of a NAT instance
          returned: when the route is via an EC2 instance
          type: str
          sample: i-abcd123456789
        instance_owner_id:
          description: AWS account owning the NAT instance
          returned: when the route is via an EC2 instance
          type: str
          sample: 123456789012
        nat_gateway_id:
          description: ID of the NAT gateway
          returned: when the route is via a NAT gateway
          type: str
          sample: local
        origin:
          description: mechanism through which the route is in the table
          returned: always
          type: str
          sample: CreateRouteTable
        state:
          description: state of the route
          returned: always
          type: str
          sample: active
    tags:
      description: Tags applied to the route table
      returned: always
      type: dict
      sample:
        Name: Public route table
        Public: 'true'
    vpc_id:
      description: ID for the VPC in which the route lives
      returned: always
      type: str
      sample: vpc-6e2d2407
'''

import re
from time import sleep

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.waiters import get_waiter


@AWSRetry.jittered_backoff()
def describe_subnets_with_backoff(connection, **params):
    paginator = connection.get_paginator('describe_subnets')
    return paginator.paginate(**params).build_full_result()['Subnets']


@AWSRetry.jittered_backoff()
def describe_igws_with_backoff(connection, **params):
    paginator = connection.get_paginator('describe_internet_gateways')
    return paginator.paginate(**params).build_full_result()['InternetGateways']


@AWSRetry.jittered_backoff()
def describe_route_tables_with_backoff(connection, **params):
    try:
        paginator = connection.get_paginator('describe_route_tables')
        return paginator.paginate(**params).build_full_result()['RouteTables']
    except is_boto3_error_code('InvalidRouteTableID.NotFound'):
        return None


def find_subnets(connection, module, vpc_id, identified_subnets):
    """
    Finds a list of subnets, each identified either by a raw ID, a unique
    'Name' tag, or a CIDR such as 10.0.0.0/8.
    """
    CIDR_RE = re.compile(r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$')
    SUBNET_RE = re.compile(r'^subnet-[A-z0-9]+$')

    subnet_ids = []
    subnet_names = []
    subnet_cidrs = []
    for subnet in (identified_subnets or []):
        if re.match(SUBNET_RE, subnet):
            subnet_ids.append(subnet)
        elif re.match(CIDR_RE, subnet):
            subnet_cidrs.append(subnet)
        else:
            subnet_names.append(subnet)

    subnets_by_id = []
    if subnet_ids:
        filters = ansible_dict_to_boto3_filter_list({'vpc-id': vpc_id})
        try:
            subnets_by_id = describe_subnets_with_backoff(connection, SubnetIds=subnet_ids, Filters=filters)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't find subnet with id %s" % subnet_ids)

    subnets_by_cidr = []
    if subnet_cidrs:
        filters = ansible_dict_to_boto3_filter_list({'vpc-id': vpc_id, 'cidr': subnet_cidrs})
        try:
            subnets_by_cidr = describe_subnets_with_backoff(connection, Filters=filters)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't find subnet with cidr %s" % subnet_cidrs)

    subnets_by_name = []
    if subnet_names:
        filters = ansible_dict_to_boto3_filter_list({'vpc-id': vpc_id, 'tag:Name': subnet_names})
        try:
            subnets_by_name = describe_subnets_with_backoff(connection, Filters=filters)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't find subnet with names %s" % subnet_names)

        for name in subnet_names:
            matching_count = len([1 for s in subnets_by_name for t in s.get('Tags', []) if t['Key'] == 'Name' and t['Value'] == name])
            if matching_count == 0:
                module.fail_json(msg='Subnet named "{0}" does not exist'.format(name))
            elif matching_count > 1:
                module.fail_json(msg='Multiple subnets named "{0}"'.format(name))

    return subnets_by_id + subnets_by_cidr + subnets_by_name


def find_igw(connection, module, vpc_id):
    """
    Finds the Internet gateway for the given VPC ID.
    """
    filters = ansible_dict_to_boto3_filter_list({'attachment.vpc-id': vpc_id})
    try:
        igw = describe_igws_with_backoff(connection, Filters=filters)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='No IGW found for VPC {0}'.format(vpc_id))
    if len(igw) == 1:
        return igw[0]['InternetGatewayId']
    elif len(igw) == 0:
        module.fail_json(msg='No IGWs found for VPC {0}'.format(vpc_id))
    else:
        module.fail_json(msg='Multiple IGWs found for VPC {0}'.format(vpc_id))


def tags_match(match_tags, candidate_tags):
    return all((k in candidate_tags and candidate_tags[k] == v
                for k, v in match_tags.items()))


def get_route_table_by_id(connection, module, route_table_id):

    route_table = None
    try:
        route_tables = describe_route_tables_with_backoff(connection, RouteTableIds=[route_table_id])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get route table")
    if route_tables:
        route_table = route_tables[0]

    return route_table


def get_route_table_by_tags(connection, module, vpc_id, tags):
    count = 0
    route_table = None
    filters = ansible_dict_to_boto3_filter_list({'vpc-id': vpc_id})
    try:
        route_tables = describe_route_tables_with_backoff(connection, Filters=filters)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get route table")
    for table in route_tables:
        this_tags = describe_ec2_tags(connection, module, table['RouteTableId'])
        if tags_match(tags, this_tags):
            route_table = table
            count += 1

    if count > 1:
        module.fail_json(msg="Tags provided do not identify a unique route table")
    else:
        return route_table


def route_spec_matches_route(route_spec, route):
    if route_spec.get('GatewayId') and 'nat-' in route_spec['GatewayId']:
        route_spec['NatGatewayId'] = route_spec.pop('GatewayId')
    if route_spec.get('GatewayId') and 'vpce-' in route_spec['GatewayId']:
        if route_spec.get('DestinationCidrBlock', '').startswith('pl-'):
            route_spec['DestinationPrefixListId'] = route_spec.pop('DestinationCidrBlock')

    return set(route_spec.items()).issubset(route.items())


def route_spec_matches_route_cidr(route_spec, route):
    return route_spec['DestinationCidrBlock'] == route.get('DestinationCidrBlock')


def rename_key(d, old_key, new_key):
    d[new_key] = d.pop(old_key)


def index_of_matching_route(route_spec, routes_to_match):
    for i, route in enumerate(routes_to_match):
        if route_spec_matches_route(route_spec, route):
            return "exact", i
        elif 'Origin' in route_spec and route_spec['Origin'] != 'EnableVgwRoutePropagation':
            if route_spec_matches_route_cidr(route_spec, route):
                return "replace", i


def ensure_routes(connection=None, module=None, route_table=None, route_specs=None,
                  propagating_vgw_ids=None, check_mode=None, purge_routes=None):
    routes_to_match = list(route_table['Routes'])
    route_specs_to_create = []
    route_specs_to_recreate = []
    for route_spec in route_specs:
        match = index_of_matching_route(route_spec, routes_to_match)
        if match is None:
            if route_spec.get('DestinationCidrBlock'):
                route_specs_to_create.append(route_spec)
            else:
                module.warn("Skipping creating {0} because it has no destination cidr block. "
                            "To add VPC endpoints to route tables use the ec2_vpc_endpoint module.".format(route_spec))
        else:
            if match[0] == "replace":
                if route_spec.get('DestinationCidrBlock'):
                    route_specs_to_recreate.append(route_spec)
                else:
                    module.warn("Skipping recreating route {0} because it has no destination cidr block.".format(route_spec))
            del routes_to_match[match[1]]

    routes_to_delete = []
    if purge_routes:
        for r in routes_to_match:
            if not r.get('DestinationCidrBlock'):
                module.warn("Skipping purging route {0} because it has no destination cidr block. "
                            "To remove VPC endpoints from route tables use the ec2_vpc_endpoint module.".format(r))
                continue
            if r['Origin'] == 'CreateRoute':
                routes_to_delete.append(r)

    changed = bool(routes_to_delete or route_specs_to_create or route_specs_to_recreate)
    if changed and not check_mode:
        for route in routes_to_delete:
            try:
                connection.delete_route(
                    aws_retry=True,
                    RouteTableId=route_table['RouteTableId'],
                    DestinationCidrBlock=route['DestinationCidrBlock'])
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Couldn't delete route")

        for route_spec in route_specs_to_recreate:
            try:
                connection.replace_route(aws_retry=True, RouteTableId=route_table['RouteTableId'], **route_spec)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Couldn't recreate route")

        for route_spec in route_specs_to_create:
            try:
                connection.create_route(aws_retry=True, RouteTableId=route_table['RouteTableId'], **route_spec)
            except is_boto3_error_code('RouteAlreadyExists'):
                changed = False
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
                module.fail_json_aws(e, msg="Couldn't create route")

    return {'changed': bool(changed)}


def ensure_subnet_association(connection=None, module=None, vpc_id=None, route_table_id=None, subnet_id=None,
                              check_mode=None):
    filters = ansible_dict_to_boto3_filter_list({'association.subnet-id': subnet_id, 'vpc-id': vpc_id})
    try:
        route_tables = describe_route_tables_with_backoff(connection, Filters=filters)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get route tables")
    for route_table in route_tables:
        if route_table['RouteTableId'] is None:
            continue
        for a in route_table['Associations']:
            if a['Main']:
                continue
            if a['SubnetId'] == subnet_id:
                if route_table['RouteTableId'] == route_table_id:
                    return {'changed': False, 'association_id': a['RouteTableAssociationId']}
                else:
                    if check_mode:
                        return {'changed': True}
                    try:
                        connection.disassociate_route_table(
                            aws_retry=True, AssociationId=a['RouteTableAssociationId'])
                    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                        module.fail_json_aws(e, msg="Couldn't disassociate subnet from route table")

    try:
        association_id = connection.associate_route_table(aws_retry=True,
                                                          RouteTableId=route_table_id,
                                                          SubnetId=subnet_id)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't associate subnet with route table")
    return {'changed': True, 'association_id': association_id}


def ensure_subnet_associations(connection=None, module=None, route_table=None, subnets=None,
                               check_mode=None, purge_subnets=None):
    current_association_ids = [a['RouteTableAssociationId'] for a in route_table['Associations'] if not a['Main']]
    new_association_ids = []
    changed = False
    for subnet in subnets:
        result = ensure_subnet_association(
            connection=connection, module=module, vpc_id=route_table['VpcId'],
            route_table_id=route_table['RouteTableId'], subnet_id=subnet['SubnetId'],
            check_mode=check_mode)
        changed = changed or result['changed']
        if changed and check_mode:
            return {'changed': True}
        new_association_ids.append(result['association_id'])

    if purge_subnets:
        to_delete = [a_id for a_id in current_association_ids
                     if a_id not in new_association_ids]

        for a_id in to_delete:
            changed = True
            if not check_mode:
                try:
                    connection.disassociate_route_table(aws_retry=True, AssociationId=a_id)
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    module.fail_json_aws(e, msg="Couldn't disassociate subnet from route table")

    return {'changed': changed}


def ensure_propagation(connection=None, module=None, route_table=None, propagating_vgw_ids=None,
                       check_mode=None):
    changed = False
    gateways = [gateway['GatewayId'] for gateway in route_table['PropagatingVgws']]
    to_add = set(propagating_vgw_ids) - set(gateways)
    if to_add:
        changed = True
        if not check_mode:
            for vgw_id in to_add:
                try:
                    connection.enable_vgw_route_propagation(
                        aws_retry=True,
                        RouteTableId=route_table['RouteTableId'],
                        GatewayId=vgw_id)
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    module.fail_json_aws(e, msg="Couldn't enable route propagation")

    return {'changed': changed}


def ensure_route_table_absent(connection, module):

    lookup = module.params.get('lookup')
    route_table_id = module.params.get('route_table_id')
    tags = module.params.get('tags')
    vpc_id = module.params.get('vpc_id')
    purge_subnets = module.params.get('purge_subnets')

    if lookup == 'tag':
        if tags is not None:
            route_table = get_route_table_by_tags(connection, module, vpc_id, tags)
        else:
            route_table = None
    elif lookup == 'id':
        route_table = get_route_table_by_id(connection, module, route_table_id)

    if route_table is None:
        return {'changed': False}

    # disassociate subnets before deleting route table
    if not module.check_mode:
        ensure_subnet_associations(connection=connection, module=module, route_table=route_table,
                                   subnets=[], check_mode=False, purge_subnets=purge_subnets)
        try:
            connection.delete_route_table(aws_retry=True, RouteTableId=route_table['RouteTableId'])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Error deleting route table")

    return {'changed': True}


def get_route_table_info(connection, module, route_table):
    result = get_route_table_by_id(connection, module, route_table['RouteTableId'])
    try:
        result['Tags'] = describe_ec2_tags(connection, module, route_table['RouteTableId'])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get tags for route table")
    result = camel_dict_to_snake_dict(result, ignore_list=['Tags'])
    # backwards compatibility
    result['id'] = result['route_table_id']
    return result


def create_route_spec(connection, module, vpc_id):
    routes = module.params.get('routes')

    for route_spec in routes:
        rename_key(route_spec, 'dest', 'destination_cidr_block')

        if route_spec.get('gateway_id') and route_spec['gateway_id'].lower() == 'igw':
            igw = find_igw(connection, module, vpc_id)
            route_spec['gateway_id'] = igw
        if route_spec.get('gateway_id') and route_spec['gateway_id'].startswith('nat-'):
            rename_key(route_spec, 'gateway_id', 'nat_gateway_id')

    return snake_dict_to_camel_dict(routes, capitalize_first=True)


def ensure_route_table_present(connection, module):

    lookup = module.params.get('lookup')
    propagating_vgw_ids = module.params.get('propagating_vgw_ids')
    purge_routes = module.params.get('purge_routes')
    purge_subnets = module.params.get('purge_subnets')
    purge_tags = module.params.get('purge_tags')
    route_table_id = module.params.get('route_table_id')
    subnets = module.params.get('subnets')
    tags = module.params.get('tags')
    vpc_id = module.params.get('vpc_id')
    routes = create_route_spec(connection, module, vpc_id)

    changed = False
    tags_valid = False

    if lookup == 'tag':
        if tags is not None:
            try:
                route_table = get_route_table_by_tags(connection, module, vpc_id, tags)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Error finding route table with lookup 'tag'")
        else:
            route_table = None
    elif lookup == 'id':
        try:
            route_table = get_route_table_by_id(connection, module, route_table_id)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Error finding route table with lookup 'id'")

    # If no route table returned then create new route table
    if route_table is None:
        changed = True
        if not module.check_mode:
            try:
                route_table = connection.create_route_table(aws_retry=True, VpcId=vpc_id)['RouteTable']
                # try to wait for route table to be present before moving on
                get_waiter(
                    connection, 'route_table_exists'
                ).wait(
                    RouteTableIds=[route_table['RouteTableId']],
                )
            except botocore.exceptions.WaiterError as e:
                module.fail_json_aws(e, msg='Timeout waiting for route table creation')
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                module.fail_json_aws(e, msg="Error creating route table")
        else:
            route_table = {"id": "rtb-xxxxxxxx", "route_table_id": "rtb-xxxxxxxx", "vpc_id": vpc_id}
            module.exit_json(changed=changed, route_table=route_table)

    if routes is not None:
        result = ensure_routes(connection=connection, module=module, route_table=route_table,
                               route_specs=routes, propagating_vgw_ids=propagating_vgw_ids,
                               check_mode=module.check_mode, purge_routes=purge_routes)
        changed = changed or result['changed']

    if propagating_vgw_ids is not None:
        result = ensure_propagation(connection=connection, module=module, route_table=route_table,
                                    propagating_vgw_ids=propagating_vgw_ids, check_mode=module.check_mode)
        changed = changed or result['changed']

    if not tags_valid and tags is not None:
        changed |= ensure_ec2_tags(connection, module, route_table['RouteTableId'],
                                   tags=tags, purge_tags=purge_tags,
                                   retry_codes=['InvalidRouteTableID.NotFound'])
        route_table['Tags'] = describe_ec2_tags(connection, module, route_table['RouteTableId'])

    if subnets is not None:
        associated_subnets = find_subnets(connection, module, vpc_id, subnets)

        result = ensure_subnet_associations(connection=connection, module=module, route_table=route_table,
                                            subnets=associated_subnets, check_mode=module.check_mode,
                                            purge_subnets=purge_subnets)
        changed = changed or result['changed']

    if changed:
        # pause to allow route table routes/subnets/associations to be updated before exiting with final state
        sleep(5)
    module.exit_json(changed=changed, route_table=get_route_table_info(connection, module, route_table))


def main():
    argument_spec = dict(
        lookup=dict(default='tag', choices=['tag', 'id']),
        propagating_vgw_ids=dict(type='list', elements='str'),
        purge_routes=dict(default=True, type='bool'),
        purge_subnets=dict(default=True, type='bool'),
        purge_tags=dict(default=False, type='bool'),
        route_table_id=dict(),
        routes=dict(default=[], type='list', elements='dict'),
        state=dict(default='present', choices=['present', 'absent']),
        subnets=dict(type='list', elements='str'),
        tags=dict(type='dict', aliases=['resource_tags']),
        vpc_id=dict()
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              required_if=[['lookup', 'id', ['route_table_id']],
                                           ['lookup', 'tag', ['vpc_id']],
                                           ['state', 'present', ['vpc_id']]],
                              supports_check_mode=True)

    # The tests for RouteTable existing uses its own decorator, we can safely
    # retry on InvalidRouteTableID.NotFound
    retry_decorator = AWSRetry.jittered_backoff(retries=10, catch_extra_error_codes=['InvalidRouteTableID.NotFound'])
    connection = module.client('ec2', retry_decorator=retry_decorator)

    state = module.params.get('state')

    if state == 'present':
        result = ensure_route_table_present(connection, module)
    elif state == 'absent':
        result = ensure_route_table_absent(connection, module)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
