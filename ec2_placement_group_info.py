#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: ec2_placement_group_info
version_added: 1.0.0
short_description: List EC2 Placement Group(s) details
description:
    - List details of EC2 Placement Group(s).
author: "Brad Macpherson (@iiibrad)"
options:
  names:
    description:
      - A list of names to filter on. If a listed group does not exist, there
        will be no corresponding entry in the result; no error will be raised.
    type: list
    elements: str
    required: false
    default: []
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
- amazon.aws.boto3

'''

EXAMPLES = r'''
# Note: These examples do not set authentication details or the AWS region,
# see the AWS Guide for details.

- name: List all placement groups.
  community.aws.ec2_placement_group_info:
  register: all_ec2_placement_groups

- name: List two placement groups.
  community.aws.ec2_placement_group_info:
    names:
     - my-cluster
     - my-other-cluster
  register: specific_ec2_placement_groups

- ansible.builtin.debug:
    msg: >
      {{ specific_ec2_placement_groups | json_query("[?name=='my-cluster']") }}

'''


RETURN = r'''
placement_groups:
  description: Placement group attributes
  returned: always
  type: complex
  contains:
    name:
      description: PG name
      type: str
      sample: my-cluster
    state:
      description: PG state
      type: str
      sample: "available"
    strategy:
      description: PG strategy
      type: str
      sample: "cluster"

'''

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
try:
    from botocore.exceptions import (BotoCoreError, ClientError)
except ImportError:
    pass  # caught by AnsibleAWSModule


def get_placement_groups_details(connection, module):
    names = module.params.get("names")
    try:
        if len(names) > 0:
            response = connection.describe_placement_groups(
                Filters=[{
                    "Name": "group-name",
                    "Values": names
                }])
        else:
            response = connection.describe_placement_groups()
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(
            e,
            msg="Couldn't find placement groups named [%s]" % names)

    results = []
    for placement_group in response['PlacementGroups']:
        results.append({
            "name": placement_group['GroupName'],
            "state": placement_group['State'],
            "strategy": placement_group['Strategy'],
        })
    return results


def main():
    argument_spec = dict(
        names=dict(type='list', default=[], elements='str')
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    connection = module.client('ec2')

    placement_groups = get_placement_groups_details(connection, module)
    module.exit_json(changed=False, placement_groups=placement_groups)


if __name__ == '__main__':
    main()
