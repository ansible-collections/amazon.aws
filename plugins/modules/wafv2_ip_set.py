#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: wafv2_ip_set
version_added: 1.5.0
author:
  - "Markus Bergholz (@markuman)"
short_description: wafv2_ip_set
description:
  - Create, modify and delete IP sets for WAFv2.
requirements:
  - boto3
  - botocore
options:
    state:
      description:
        - Whether the rule is present or absent.
      choices: ["present", "absent"]
      required: true
      type: str
    name:
      description:
        - The name of the IP set.
      required: true
      type: str
    description:
      description:
        - Description of the IP set.
      required: false
      type: str
    scope:
      description:
        - Specifies whether this is for an AWS CloudFront distribution or for a regional application,
          such as API Gateway or Application LoadBalancer.
      choices: ["CLOUDFRONT","REGIONAL"]
      required: true
      type: str
    ip_address_version:
      description:
        - Specifies whether this is an IPv4 or an IPv6 IP set.
        - Required when I(state=present).
      choices: ["IPV4","IPV6"]
      type: str
    addresses:
      description:
        - Contains an array of strings that specify one or more IP addresses or blocks of IP addresses in
          Classless Inter-Domain Routing (CIDR) notation.
        - Required when I(state=present).
        - When I(state=absent) and I(addresses) is defined, only the given IP addresses will be removed
          from the IP set. The entire IP set itself will stay present.
      type: list
      elements: str
    tags:
      description:
        - Key value pairs to associate with the resource.
        - Currently tags are not visible. Nor in the web ui, nor via cli and nor in boto3.
      required: false
      type: dict
    purge_addresses:
      description:
        - When set to C(no), keep the existing addresses in place. Will modify and add, but will not delete.
      default: yes
      type: bool

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
- name: test ip set
  wafv2_ip_set:
    name: test02
    state: present
    description: hallo eins
    scope: REGIONAL
    ip_address_version: IPV4
    addresses:
      - 8.8.8.8/32
      - 8.8.4.4/32
    tags:
      A: B
      C: D
'''

RETURN = """
addresses:
  description: Current addresses of the ip set
  sample:
    - 8.8.8.8/32
    - 8.8.4.4/32
  returned: Always, as long as the ip set exists
  type: list
arn:
  description: IP set arn
  sample: "arn:aws:wafv2:eu-central-1:11111111:regional/ipset/test02/4b007330-2934-4dc5-af24-82dcb3aeb127"
  type: str
  returned: Always, as long as the ip set exists
description:
  description: Description of the ip set
  sample: Some IP set description
  returned: Always, as long as the ip set exists
  type: str
ip_address_version:
  description: IP version of the ip set
  sample: IPV4
  type: str
  returned: Always, as long as the ip set exists
name:
  description: IP set name
  sample: test02
  returned: Always, as long as the ip set exists
  type: str
"""
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule, is_boto3_error_code, get_boto3_client_method_parameters
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict, ansible_dict_to_boto3_tag_list

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # caught by AnsibleAWSModule


class IpSet:
    def __init__(self, wafv2, name, scope, fail_json_aws):
        self.wafv2 = wafv2
        self.name = name
        self.scope = scope
        self.fail_json_aws = fail_json_aws
        self.existing_set, self.id, self.locktoken = self.get_set()

    def description(self):
        return self.existing_set.get('Description')

    def get(self):
        if self.existing_set:
            return camel_dict_to_snake_dict(self.existing_set)
        return None

    def remove(self):
        try:
            response = self.wafv2.delete_ip_set(
                Name=self.name,
                Scope=self.scope,
                Id=self.id,
                LockToken=self.locktoken
            )
        except (BotoCoreError, ClientError) as e:
            self.fail_json_aws(e, msg="Failed to remove wafv2 ip set.")
        return {}

    def create(self, description, ip_address_version, addresses, tags):
        req_obj = {
            'Name': self.name,
            'Scope': self.scope,
            'IPAddressVersion': ip_address_version,
            'Addresses': addresses,
        }

        if description:
            req_obj['Description'] = description

        if tags:
            req_obj['Tags'] = ansible_dict_to_boto3_tag_list(tags)

        try:
            response = self.wafv2.create_ip_set(**req_obj)
        except (BotoCoreError, ClientError) as e:
            self.fail_json_aws(e, msg="Failed to create wafv2 ip set.")

        self.existing_set, self.id, self.locktoken = self.get_set()
        return camel_dict_to_snake_dict(self.existing_set)

    def update(self, description, addresses):
        req_obj = {
            'Name': self.name,
            'Scope': self.scope,
            'Id': self.id,
            'Addresses': addresses,
            'LockToken': self.locktoken
        }

        if description:
            req_obj['Description'] = description

        try:
            response = self.wafv2.update_ip_set(**req_obj)
        except (BotoCoreError, ClientError) as e:
            self.fail_json_aws(e, msg="Failed to update wafv2 ip set.")

        self.existing_set, self.id, self.locktoken = self.get_set()
        return camel_dict_to_snake_dict(self.existing_set)

    def get_set(self):
        response = self.list()
        existing_set = None
        id = None
        locktoken = None
        for item in response.get('IPSets'):
            if item.get('Name') == self.name:
                id = item.get('Id')
                locktoken = item.get('LockToken')
                arn = item.get('ARN')
        if id:
            try:
                existing_set = self.wafv2.get_ip_set(
                    Name=self.name,
                    Scope=self.scope,
                    Id=id
                ).get('IPSet')
            except (BotoCoreError, ClientError) as e:
                self.fail_json_aws(e, msg="Failed to get wafv2 ip set.")

        return existing_set, id, locktoken

    def list(self, Nextmarker=None):
        # there is currently no paginator for wafv2
        req_obj = {
            'Scope': self.scope,
            'Limit': 100
        }
        if Nextmarker:
            req_obj['NextMarker'] = Nextmarker

        try:
            response = self.wafv2.list_ip_sets(**req_obj)
            if response.get('NextMarker'):
                response['IPSets'] += self.list(Nextmarker=response.get('NextMarker')).get('IPSets')
        except (BotoCoreError, ClientError) as e:
            self.fail_json_aws(e, msg="Failed to list wafv2 ip set.")

        return response


def compare(existing_set, addresses, purge_addresses, state):
    diff = False
    new_rules = []
    existing_rules = existing_set.get('addresses')
    if state == 'present':
        if purge_addresses:
            new_rules = addresses
            if sorted(addresses) != sorted(existing_set.get('addresses')):
                diff = True

        else:
            for requested_rule in addresses:
                if requested_rule not in existing_rules:
                    diff = True
                    new_rules.append(requested_rule)

            new_rules += existing_rules
    else:
        if purge_addresses and addresses:
            for requested_rule in addresses:
                if requested_rule in existing_rules:
                    diff = True
                    existing_rules.pop(existing_rules.index(requested_rule))
            new_rules = existing_rules

    return diff, new_rules


def main():

    arg_spec = dict(
        state=dict(type='str', required=True, choices=['present', 'absent']),
        name=dict(type='str', required=True),
        scope=dict(type='str', required=True, choices=['CLOUDFRONT', 'REGIONAL']),
        description=dict(type='str'),
        ip_address_version=dict(type='str', choices=['IPV4', 'IPV6']),
        addresses=dict(type='list', elements='str'),
        tags=dict(type='dict'),
        purge_addresses=dict(type='bool', default=True)
    )

    module = AnsibleAWSModule(
        argument_spec=arg_spec,
        supports_check_mode=True,
        required_if=[['state', 'present', ['ip_address_version', 'addresses']]]
    )

    state = module.params.get("state")
    name = module.params.get("name")
    scope = module.params.get("scope")
    description = module.params.get("description")
    ip_address_version = module.params.get("ip_address_version")
    addresses = module.params.get("addresses")
    tags = module.params.get("tags")
    purge_addresses = module.params.get("purge_addresses")
    check_mode = module.check_mode

    wafv2 = module.client('wafv2')

    change = False
    retval = {}

    ip_set = IpSet(wafv2, name, scope, module.fail_json_aws)

    if state == 'present':
        if ip_set.get():
            change, addresses = compare(ip_set.get(), addresses, purge_addresses, state)
            if (change or ip_set.description() != description) and not check_mode:
                retval = ip_set.update(
                    description=description,
                    addresses=addresses
                )
            else:
                retval = ip_set.get()
        else:
            if not check_mode:
                retval = ip_set.create(
                    description=description,
                    ip_address_version=ip_address_version,
                    addresses=addresses,
                    tags=tags
                )
            change = True

    if state == 'absent':
        if ip_set.get():
            if addresses:
                if len(addresses) > 0:
                    change, addresses = compare(ip_set.get(), addresses, purge_addresses, state)
                    if change and not check_mode:
                        retval = ip_set.update(
                            description=description,
                            addresses=addresses
                        )
            else:
                if not check_mode:
                    retval = ip_set.remove()
                change = True

    module.exit_json(changed=change, **retval)


if __name__ == '__main__':
    main()
