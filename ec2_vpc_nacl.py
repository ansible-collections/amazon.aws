#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
module: ec2_vpc_nacl
short_description: create and delete Network ACLs
version_added: 1.0.0
description:
  - Read the AWS documentation for Network ACLS
    U(https://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/VPC_ACLs.html)
options:
  name:
    description:
      - Tagged name identifying a network ACL.
      - One and only one of the I(name) or I(nacl_id) is required.
    required: false
    type: str
  nacl_id:
    description:
      - NACL id identifying a network ACL.
      - One and only one of the I(name) or I(nacl_id) is required.
    required: false
    type: str
  vpc_id:
    description:
      - VPC id of the requesting VPC.
      - Required when state present.
    required: false
    type: str
  subnets:
    description:
      - The list of subnets that should be associated with the network ACL.
      - Must be specified as a list
      - Each subnet can be specified as subnet ID, or its tagged name.
    required: false
    type: list
    elements: str
    default: []
  egress:
    description:
      - A list of rules for outgoing traffic. Each rule must be specified as a list.
        Each rule may contain the rule number (integer 1-32766), protocol (one of ['tcp', 'udp', 'icmp', 'ipv6-icmp', '-1', 'all']),
        the rule action ('allow' or 'deny') the CIDR of the IPv4 or IPv6 network range to allow or deny,
        the ICMP type (-1 means all types), the ICMP code (-1 means all codes), the last port in the range for
        TCP or UDP protocols, and the first port in the range for TCP or UDP protocols.
        See examples.
    default: []
    required: false
    type: list
    elements: list
  ingress:
    description:
      - List of rules for incoming traffic. Each rule must be specified as a list.
        Each rule may contain the rule number (integer 1-32766), protocol (one of ['tcp', 'udp', 'icmp', 'ipv6-icmp', '-1', 'all']),
        the rule action ('allow' or 'deny') the CIDR of the IPv4 or IPv6 network range to allow or deny,
        the ICMP type (-1 means all types), the ICMP code (-1 means all codes), the last port in the range for
        TCP or UDP protocols, and the first port in the range for TCP or UDP protocols.
        See examples.
    default: []
    required: false
    type: list
    elements: list
  state:
    description:
      - Creates or modifies an existing NACL
      - Deletes a NACL and reassociates subnets to the default NACL
    required: false
    type: str
    choices: ['present', 'absent']
    default: present
author: Mike Mochan (@mmochan)
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.boto3
  - amazon.aws.tags
notes:
  - Support for I(purge_tags) was added in release 4.0.0.
'''

EXAMPLES = r'''

# Complete example to create and delete a network ACL
# that allows SSH, HTTP and ICMP in, and all traffic out.
- name: "Create and associate production DMZ network ACL with DMZ subnets"
  community.aws.ec2_vpc_nacl:
    vpc_id: vpc-12345678
    name: prod-dmz-nacl
    region: ap-southeast-2
    subnets: ['prod-dmz-1', 'prod-dmz-2']
    tags:
      CostCode: CC1234
      Project: phoenix
      Description: production DMZ
    ingress:
        # rule no, protocol, allow/deny, cidr, icmp_type, icmp_code,
        #                                             port from, port to
        - [100, 'tcp', 'allow', '0.0.0.0/0', null, null, 22, 22]
        - [200, 'tcp', 'allow', '0.0.0.0/0', null, null, 80, 80]
        - [205, 'tcp', 'allow', '::/0', null, null, 80, 80]
        - [300, 'icmp', 'allow', '0.0.0.0/0', 0, 8]
        - [305, 'ipv6-icmp', 'allow', '::/0', 0, 8]
    egress:
        - [100, 'all', 'allow', '0.0.0.0/0', null, null, null, null]
        - [105, 'all', 'allow', '::/0', null, null, null, null]
    state: 'present'

- name: "Remove the ingress and egress rules - defaults to deny all"
  community.aws.ec2_vpc_nacl:
    vpc_id: vpc-12345678
    name: prod-dmz-nacl
    region: ap-southeast-2
    subnets:
      - prod-dmz-1
      - prod-dmz-2
    tags:
      CostCode: CC1234
      Project: phoenix
      Description: production DMZ
    state: present

- name: "Remove the NACL subnet associations and tags"
  community.aws.ec2_vpc_nacl:
    vpc_id: 'vpc-12345678'
    name: prod-dmz-nacl
    region: ap-southeast-2
    state: present

- name: "Delete nacl and subnet associations"
  community.aws.ec2_vpc_nacl:
    vpc_id: vpc-12345678
    name: prod-dmz-nacl
    state: absent

- name: "Delete nacl by its id"
  community.aws.ec2_vpc_nacl:
    nacl_id: acl-33b4ee5b
    state: absent
'''
RETURN = r'''
task:
  description: The result of the create, or delete action.
  returned: success
  type: dict
nacl_id:
  description: The id of the NACL (when creating or updating an ACL)
  returned: success
  type: str
  sample: acl-123456789abcdef01
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications

# VPC-supported IANA protocol numbers
# http://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml
PROTOCOL_NUMBERS = {'all': -1, 'icmp': 1, 'tcp': 6, 'udp': 17, 'ipv6-icmp': 58}


# Utility methods
def icmp_present(entry):
    if len(entry) == 6 and entry[1] in ['icmp', 'ipv6-icmp'] or entry[1] in [1, 58]:
        return True


def subnets_removed(nacl_id, subnets, client, module):
    results = find_acl_by_id(nacl_id, client, module)
    associations = results['NetworkAcls'][0]['Associations']
    subnet_ids = [assoc['SubnetId'] for assoc in associations]
    return [subnet for subnet in subnet_ids if subnet not in subnets]


def subnets_added(nacl_id, subnets, client, module):
    results = find_acl_by_id(nacl_id, client, module)
    associations = results['NetworkAcls'][0]['Associations']
    subnet_ids = [assoc['SubnetId'] for assoc in associations]
    return [subnet for subnet in subnets if subnet not in subnet_ids]


def subnets_changed(nacl, client, module):
    changed = False
    vpc_id = module.params.get('vpc_id')
    nacl_id = nacl['NetworkAcls'][0]['NetworkAclId']
    subnets = subnets_to_associate(nacl, client, module)
    if not subnets:
        default_nacl_id = find_default_vpc_nacl(vpc_id, client, module)[0]
        subnets = find_subnet_ids_by_nacl_id(nacl_id, client, module)
        if subnets:
            replace_network_acl_association(default_nacl_id, subnets, client, module)
            changed = True
            return changed
        changed = False
        return changed
    subs_added = subnets_added(nacl_id, subnets, client, module)
    if subs_added:
        replace_network_acl_association(nacl_id, subs_added, client, module)
        changed = True
    subs_removed = subnets_removed(nacl_id, subnets, client, module)
    if subs_removed:
        default_nacl_id = find_default_vpc_nacl(vpc_id, client, module)[0]
        replace_network_acl_association(default_nacl_id, subs_removed, client, module)
        changed = True
    return changed


def nacls_changed(nacl, client, module):
    changed = False
    params = dict()
    params['egress'] = module.params.get('egress')
    params['ingress'] = module.params.get('ingress')

    nacl_id = nacl['NetworkAcls'][0]['NetworkAclId']
    nacl = describe_network_acl(client, module)
    entries = nacl['NetworkAcls'][0]['Entries']
    egress = [rule for rule in entries if rule['Egress'] is True and rule['RuleNumber'] < 32767]
    ingress = [rule for rule in entries if rule['Egress'] is False and rule['RuleNumber'] < 32767]
    if rules_changed(egress, params['egress'], True, nacl_id, client, module):
        changed = True
    if rules_changed(ingress, params['ingress'], False, nacl_id, client, module):
        changed = True
    return changed


def tags_changed(nacl_id, client, module):
    tags = module.params.get('tags')
    name = module.params.get('name')
    purge_tags = module.params.get('purge_tags')

    if name is None and tags is None:
        return False

    if module.params.get('tags') is None:
        # Only purge tags if tags is explicitly set to {} and purge_tags is True
        purge_tags = False

    new_tags = dict()
    if module.params.get('name') is not None:
        new_tags['Name'] = module.params.get('name')
    new_tags.update(module.params.get('tags') or {})

    return ensure_ec2_tags(client, module, nacl_id, tags=new_tags,
                           purge_tags=purge_tags, retry_codes=['InvalidNetworkAclID.NotFound'])


def rules_changed(aws_rules, param_rules, Egress, nacl_id, client, module):
    changed = False
    rules = list()
    for entry in param_rules:
        rules.append(process_rule_entry(entry, Egress))
    if rules == aws_rules:
        return changed
    else:
        removed_rules = [x for x in aws_rules if x not in rules]
        if removed_rules:
            params = dict()
            for rule in removed_rules:
                params['NetworkAclId'] = nacl_id
                params['RuleNumber'] = rule['RuleNumber']
                params['Egress'] = Egress
                delete_network_acl_entry(params, client, module)
            changed = True
        added_rules = [x for x in rules if x not in aws_rules]
        if added_rules:
            for rule in added_rules:
                rule['NetworkAclId'] = nacl_id
                create_network_acl_entry(rule, client, module)
            changed = True
    return changed


def is_ipv6(cidr):
    return ':' in cidr


def process_rule_entry(entry, Egress):
    params = dict()
    params['RuleNumber'] = entry[0]
    params['Protocol'] = str(PROTOCOL_NUMBERS[entry[1]])
    params['RuleAction'] = entry[2]
    params['Egress'] = Egress
    if is_ipv6(entry[3]):
        params['Ipv6CidrBlock'] = entry[3]
    else:
        params['CidrBlock'] = entry[3]
    if icmp_present(entry):
        params['IcmpTypeCode'] = {"Type": int(entry[4]), "Code": int(entry[5])}
    else:
        if entry[6] or entry[7]:
            params['PortRange'] = {"From": entry[6], 'To': entry[7]}
    return params


def restore_default_associations(assoc_ids, default_nacl_id, client, module):
    if assoc_ids:
        params = dict()
        params['NetworkAclId'] = default_nacl_id[0]
        for assoc_id in assoc_ids:
            params['AssociationId'] = assoc_id
            restore_default_acl_association(params, client, module)
        return True


def construct_acl_entries(nacl, client, module):
    for entry in module.params.get('ingress'):
        params = process_rule_entry(entry, Egress=False)
        params['NetworkAclId'] = nacl['NetworkAcl']['NetworkAclId']
        create_network_acl_entry(params, client, module)
    for rule in module.params.get('egress'):
        params = process_rule_entry(rule, Egress=True)
        params['NetworkAclId'] = nacl['NetworkAcl']['NetworkAclId']
        create_network_acl_entry(params, client, module)


# Module invocations
def setup_network_acl(client, module):
    changed = False
    nacl = describe_network_acl(client, module)
    if not nacl['NetworkAcls']:
        tags = {}
        if module.params.get('name'):
            tags['Name'] = module.params.get('name')
        tags.update(module.params.get('tags') or {})
        nacl = create_network_acl(module.params.get('vpc_id'), client, module, tags)
        nacl_id = nacl['NetworkAcl']['NetworkAclId']
        subnets = subnets_to_associate(nacl, client, module)
        replace_network_acl_association(nacl_id, subnets, client, module)
        construct_acl_entries(nacl, client, module)
        changed = True
        return changed, nacl['NetworkAcl']['NetworkAclId']
    else:
        changed = False
        nacl_id = nacl['NetworkAcls'][0]['NetworkAclId']
        changed |= subnets_changed(nacl, client, module)
        changed |= nacls_changed(nacl, client, module)
        changed |= tags_changed(nacl_id, client, module)
        return changed, nacl_id


def remove_network_acl(client, module):
    changed = False
    result = dict()
    nacl = describe_network_acl(client, module)
    if nacl['NetworkAcls']:
        nacl_id = nacl['NetworkAcls'][0]['NetworkAclId']
        vpc_id = nacl['NetworkAcls'][0]['VpcId']
        associations = nacl['NetworkAcls'][0]['Associations']
        assoc_ids = [a['NetworkAclAssociationId'] for a in associations]
        default_nacl_id = find_default_vpc_nacl(vpc_id, client, module)
        if not default_nacl_id:
            result = {vpc_id: "Default NACL ID not found - Check the VPC ID"}
            return changed, result
        if restore_default_associations(assoc_ids, default_nacl_id, client, module):
            delete_network_acl(nacl_id, client, module)
            changed = True
            result[nacl_id] = "Successfully deleted"
            return changed, result
        if not assoc_ids:
            delete_network_acl(nacl_id, client, module)
            changed = True
            result[nacl_id] = "Successfully deleted"
            return changed, result
    return changed, result


# Boto3 client methods
@AWSRetry.jittered_backoff()
def _create_network_acl(client, *args, **kwargs):
    return client.create_network_acl(*args, **kwargs)


def create_network_acl(vpc_id, client, module, tags):
    params = dict(VpcId=vpc_id)
    if tags:
        params['TagSpecifications'] = boto3_tag_specifications(tags, ['network-acl'])
    try:
        if module.check_mode:
            nacl = dict(NetworkAcl=dict(NetworkAclId="nacl-00000000"))
        else:
            nacl = _create_network_acl(client, **params)
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)
    return nacl


@AWSRetry.jittered_backoff(catch_extra_error_codes=['InvalidNetworkAclID.NotFound'])
def _create_network_acl_entry(client, *args, **kwargs):
    return client.create_network_acl_entry(*args, **kwargs)


def create_network_acl_entry(params, client, module):
    try:
        if not module.check_mode:
            _create_network_acl_entry(client, **params)
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)


@AWSRetry.jittered_backoff()
def _delete_network_acl(client, *args, **kwargs):
    return client.delete_network_acl(*args, **kwargs)


def delete_network_acl(nacl_id, client, module):
    try:
        if not module.check_mode:
            _delete_network_acl(client, NetworkAclId=nacl_id)
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)


@AWSRetry.jittered_backoff(catch_extra_error_codes=['InvalidNetworkAclID.NotFound'])
def _delete_network_acl_entry(client, *args, **kwargs):
    return client.delete_network_acl_entry(*args, **kwargs)


def delete_network_acl_entry(params, client, module):
    try:
        if not module.check_mode:
            _delete_network_acl_entry(client, **params)
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)


@AWSRetry.jittered_backoff()
def _describe_network_acls(client, **kwargs):
    return client.describe_network_acls(**kwargs)


@AWSRetry.jittered_backoff(catch_extra_error_codes=['InvalidNetworkAclID.NotFound'])
def _describe_network_acls_retry_missing(client, **kwargs):
    return client.describe_network_acls(**kwargs)


def describe_acl_associations(subnets, client, module):
    if not subnets:
        return []
    try:
        results = _describe_network_acls_retry_missing(client, Filters=[
            {'Name': 'association.subnet-id', 'Values': subnets}
        ])
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)
    associations = results['NetworkAcls'][0]['Associations']
    return [a['NetworkAclAssociationId'] for a in associations if a['SubnetId'] in subnets]


def describe_network_acl(client, module):
    try:
        if module.params.get('nacl_id'):
            nacl = _describe_network_acls(client, Filters=[
                {'Name': 'network-acl-id', 'Values': [module.params.get('nacl_id')]}
            ])
        else:
            nacl = _describe_network_acls(client, Filters=[
                {'Name': 'tag:Name', 'Values': [module.params.get('name')]}
            ])
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)
    return nacl


def find_acl_by_id(nacl_id, client, module):
    try:
        return _describe_network_acls_retry_missing(client, NetworkAclIds=[nacl_id])
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)


def find_default_vpc_nacl(vpc_id, client, module):
    try:
        response = _describe_network_acls_retry_missing(client, Filters=[
            {'Name': 'vpc-id', 'Values': [vpc_id]}])
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)
    nacls = response['NetworkAcls']
    return [n['NetworkAclId'] for n in nacls if n['IsDefault'] is True]


def find_subnet_ids_by_nacl_id(nacl_id, client, module):
    try:
        results = _describe_network_acls_retry_missing(client, Filters=[
            {'Name': 'association.network-acl-id', 'Values': [nacl_id]}
        ])
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)
    if results['NetworkAcls']:
        associations = results['NetworkAcls'][0]['Associations']
        return [s['SubnetId'] for s in associations if s['SubnetId']]
    else:
        return []


@AWSRetry.jittered_backoff(catch_extra_error_codes=['InvalidNetworkAclID.NotFound'])
def _replace_network_acl_association(client, *args, **kwargs):
    return client.replace_network_acl_association(*args, **kwargs)


def replace_network_acl_association(nacl_id, subnets, client, module):
    params = dict()
    params['NetworkAclId'] = nacl_id
    for association in describe_acl_associations(subnets, client, module):
        params['AssociationId'] = association
        try:
            if not module.check_mode:
                _replace_network_acl_association(client, **params)
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e)


@AWSRetry.jittered_backoff(catch_extra_error_codes=['InvalidNetworkAclID.NotFound'])
def _replace_network_acl_entry(client, *args, **kwargs):
    return client.replace_network_acl_entry(*args, **kwargs)


def replace_network_acl_entry(entries, Egress, nacl_id, client, module):
    for entry in entries:
        params = entry
        params['NetworkAclId'] = nacl_id
        try:
            if not module.check_mode:
                _replace_network_acl_entry(client, **params)
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e)


@AWSRetry.jittered_backoff(catch_extra_error_codes=['InvalidNetworkAclID.NotFound'])
def _replace_network_acl_association(client, *args, **kwargs):
    return client.replace_network_acl_association(*args, **kwargs)


def restore_default_acl_association(params, client, module):
    try:
        if not module.check_mode:
            _replace_network_acl_association(client, **params)
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)


@AWSRetry.jittered_backoff()
def _describe_subnets(client, *args, **kwargs):
    return client.describe_subnets(*args, **kwargs)


def subnets_to_associate(nacl, client, module):
    params = list(module.params.get('subnets'))
    if not params:
        return []
    all_found = []
    if any(x.startswith("subnet-") for x in params):
        try:
            subnets = _describe_subnets(client, Filters=[
                {'Name': 'subnet-id', 'Values': params}])
            all_found.extend(subnets.get('Subnets', []))
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e)
    if len(params) != len(all_found):
        try:
            subnets = _describe_subnets(client, Filters=[
                {'Name': 'tag:Name', 'Values': params}])
            all_found.extend(subnets.get('Subnets', []))
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e)
    return list(set(s['SubnetId'] for s in all_found if s.get('SubnetId')))


def main():
    argument_spec = dict(
        vpc_id=dict(),
        name=dict(),
        nacl_id=dict(),
        subnets=dict(required=False, type='list', default=list(), elements='str'),
        tags=dict(required=False, type='dict', aliases=['resource_tags']),
        purge_tags=dict(required=False, type='bool', default=True),
        ingress=dict(required=False, type='list', default=list(), elements='list'),
        egress=dict(required=False, type='list', default=list(), elements='list'),
        state=dict(default='present', choices=['present', 'absent']),
    )
    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True,
                              required_one_of=[['name', 'nacl_id']],
                              required_if=[['state', 'present', ['vpc_id']]])

    state = module.params.get('state').lower()

    client = module.client('ec2')

    invocations = {
        "present": setup_network_acl,
        "absent": remove_network_acl
    }
    (changed, results) = invocations[state](client, module)
    module.exit_json(changed=changed, nacl_id=results)


if __name__ == '__main__':
    main()
