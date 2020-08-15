#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: ec2_vpc_route_table_info
version_added: 1.0.0
short_description: Gather information about ec2 VPC route tables in AWS
description:
    - Gather information about ec2 VPC route tables in AWS
    - This module was called C(ec2_vpc_route_table_facts) before Ansible 2.9. The usage did not change.
author: "Rob White (@wimnat)"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeRouteTables.html) for possible filters.
    type: dict
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather information about all VPC route tables
  community.aws.ec2_vpc_route_table_info:

- name: Gather information about a particular VPC route table using route table ID
  community.aws.ec2_vpc_route_table_info:
    filters:
      route-table-id: rtb-00112233

- name: Gather information about any VPC route table with a tag key Name and value Example
  community.aws.ec2_vpc_route_table_info:
    filters:
      "tag:Name": Example

- name: Gather information about any VPC route table within VPC with ID vpc-abcdef00
  community.aws.ec2_vpc_route_table_info:
    filters:
      vpc-id: vpc-abcdef00

'''

try:
    import boto.vpc
    from boto.exception import BotoServerError
except ImportError:
    pass  # Handled by HAS_BOTO

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import connect_to_aws
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import get_aws_connection_info
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import HAS_BOTO


def get_route_table_info(route_table):

    # Add any routes to array
    routes = []
    associations = []
    for route in route_table.routes:
        routes.append(route.__dict__)
    for association in route_table.associations:
        associations.append(association.__dict__)

    route_table_info = {'id': route_table.id,
                        'routes': routes,
                        'associations': associations,
                        'tags': route_table.tags,
                        'vpc_id': route_table.vpc_id
                        }

    return route_table_info


def list_ec2_vpc_route_tables(connection, module):

    filters = module.params.get("filters")
    route_table_dict_array = []

    try:
        all_route_tables = connection.get_all_route_tables(filters=filters)
    except BotoServerError as e:
        module.fail_json_aws(e, msg="Failed to get route tables")

    for route_table in all_route_tables:
        route_table_dict_array.append(get_route_table_info(route_table))

    module.exit_json(route_tables=route_table_dict_array)


def main():
    argument_spec = dict(
        filters=dict(default=None, type='dict'),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True)
    if module._name == 'ec2_vpc_route_table_facts':
        module.deprecate("The 'ec2_vpc_route_table_facts' module has been renamed to 'ec2_vpc_route_table_info'",
                         date='2021-12-01', collection_name='community.aws')

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    if region:
        try:
            connection = connect_to_aws(boto.vpc, region, **aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError) as e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="region must be specified")

    list_ec2_vpc_route_tables(connection, module)


if __name__ == '__main__':
    main()
