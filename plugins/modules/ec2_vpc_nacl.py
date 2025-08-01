#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: ec2_vpc_nacl
short_description: create and delete Network ACLs
version_added: 1.0.0
version_added_collection: community.aws
description:
  - Read the AWS documentation for Network ACLS
    U(https://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/VPC_ACLs.html).
options:
  name:
    description:
      - Tagged name identifying a network ACL.
      - One and only one of the O(name) or O(nacl_id) is required.
      - Mutually exclusive with O(nacl_id).
    required: false
    type: str
  nacl_id:
    description:
      - NACL id identifying a network ACL.
      - One and only one of the O(name) or O(nacl_id) is required.
      - Mutually exclusive with O(name).
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
      - Creates or modifies an existing NACL.
      - Deletes a NACL and reassociates subnets to the default NACL.
    required: false
    type: str
    choices: ['present', 'absent']
    default: present
author:
  - Mike Mochan (@mmochan)
notes:
  - Support for I(purge_tags) was added in release 4.0.0.
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
  - amazon.aws.tags
"""

EXAMPLES = r"""
# Complete example to create and delete a network ACL
# that allows SSH, HTTP and ICMP in, and all traffic out.
- name: "Create and associate production DMZ network ACL with DMZ subnets"
  amazon.aws.ec2_vpc_nacl:
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
  amazon.aws.ec2_vpc_nacl:
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
  amazon.aws.ec2_vpc_nacl:
    vpc_id: 'vpc-12345678'
    name: prod-dmz-nacl
    region: ap-southeast-2
    state: present

- name: "Delete nacl and subnet associations"
  amazon.aws.ec2_vpc_nacl:
    vpc_id: vpc-12345678
    name: prod-dmz-nacl
    state: absent

- name: "Delete nacl by its id"
  amazon.aws.ec2_vpc_nacl:
    nacl_id: acl-33b4ee5b
    state: absent
"""

RETURN = r"""
nacl_id:
  description: The id of the NACL (when creating or updating an ACL).
  returned: success
  type: str
  sample: "acl-123456789abcdef01"
"""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleEC2Error
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import create_network_acl
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import create_network_acl_entry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import delete_network_acl
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import delete_network_acl_entry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_network_acls
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import describe_subnets
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import replace_network_acl_association
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule

# VPC-supported IANA protocol numbers
# http://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml
PROTOCOL_NUMBERS = {"all": -1, "icmp": 1, "tcp": 6, "udp": 17, "ipv6-icmp": 58}


# Utility methods
def icmp_present(entry: List[str]) -> bool:
    return len(entry) == 6 and entry[1] in ["icmp", "ipv6-icmp"] or entry[1] in [1, 58]


def subnets_changed(client, module: AnsibleAWSModule, nacl_id: str, subnets_ids: List[str]) -> bool:
    changed = False
    vpc_id = module.params.get("vpc_id")

    if not subnets_ids:
        default_nacl_id = find_default_vpc_nacl(client, vpc_id)
        # Find subnets by Network ACL ids
        network_acls = describe_network_acls(
            client, Filters=[{"Name": "association.network-acl-id", "Values": [nacl_id]}]
        )
        subnets = [
            association["SubnetId"]
            for nacl in network_acls
            for association in nacl["Associations"]
            if association["SubnetId"]
        ]
        changed = associate_nacl_to_subnets(client, module, default_nacl_id, subnets)
        return changed

    network_acls = describe_network_acls(client, NetworkAclIds=[nacl_id])
    current_subnets = [
        association["SubnetId"]
        for nacl in network_acls
        for association in nacl["Associations"]
        if association["SubnetId"]
    ]
    subnets_added = [subnet for subnet in subnets_ids if subnet not in current_subnets]
    subnets_removed = [subnet for subnet in current_subnets if subnet not in subnets_ids]

    if subnets_added:
        changed |= associate_nacl_to_subnets(client, module, nacl_id, subnets_added)
    if subnets_removed:
        default_nacl_id = find_default_vpc_nacl(client, vpc_id)
        changed |= associate_nacl_to_subnets(client, module, default_nacl_id, subnets_removed)

    return changed


def nacls_changed(client, module: AnsibleAWSModule, nacl_info: Dict[str, Any]) -> bool:
    changed = False
    entries = nacl_info["Entries"]
    nacl_id = nacl_info["NetworkAclId"]
    aws_egress_rules = [rule for rule in entries if rule["Egress"] is True and rule["RuleNumber"] < 32767]
    aws_ingress_rules = [rule for rule in entries if rule["Egress"] is False and rule["RuleNumber"] < 32767]

    # Egress Rules
    changed |= rules_changed(client, nacl_id, module.params.get("egress"), aws_egress_rules, True, module.check_mode)
    # Ingress Rules
    changed |= rules_changed(client, nacl_id, module.params.get("ingress"), aws_ingress_rules, False, module.check_mode)
    return changed


def tags_changed(client, module: AnsibleAWSModule, nacl_id: str) -> bool:
    tags = module.params.get("tags")
    name = module.params.get("name")
    purge_tags = module.params.get("purge_tags")

    if name is None and tags is None:
        return False

    if module.params.get("tags") is None:
        # Only purge tags if tags is explicitly set to {} and purge_tags is True
        purge_tags = False

    new_tags = dict()
    if module.params.get("name") is not None:
        new_tags["Name"] = module.params.get("name")
    new_tags.update(module.params.get("tags") or {})

    return ensure_ec2_tags(
        client, module, nacl_id, tags=new_tags, purge_tags=purge_tags, retry_codes=["InvalidNetworkAclID.NotFound"]
    )


def ansible_to_boto3_dict_rule(ansible_rule: List[Any], egress: bool) -> Dict[str, Any]:
    boto3_rule = {}
    if isinstance(ansible_rule, list):
        boto3_rule["RuleNumber"] = ansible_rule[0]
        boto3_rule["Protocol"] = str(PROTOCOL_NUMBERS[ansible_rule[1]])
        boto3_rule["RuleAction"] = ansible_rule[2]
        boto3_rule["Egress"] = egress
        if is_ipv6(ansible_rule[3]):
            boto3_rule["Ipv6CidrBlock"] = ansible_rule[3]
        else:
            boto3_rule["CidrBlock"] = ansible_rule[3]
        if icmp_present(ansible_rule):
            boto3_rule["IcmpTypeCode"] = {"Type": int(ansible_rule[4]), "Code": int(ansible_rule[5])}
        else:
            if ansible_rule[6] or ansible_rule[7]:
                boto3_rule["PortRange"] = {"From": ansible_rule[6], "To": ansible_rule[7]}
    return boto3_rule


def find_added_rules(rules_a: List[Dict[str, Any]], rules_b: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    # A rule is considered as a new rule if either the RuleNumber does exist in the list of
    # current Rules stored in AWS or if the Rule differs with the Rule stored in AWS with the same RuleNumber
    for a in rules_a:
        if not any(a["RuleNumber"] == b["RuleNumber"] and a == b for b in rules_b):
            results.append(a)
    return results


def rules_changed(
    client,
    nacl_id: str,
    ansible_rules: List[List[str]],
    aws_rules: List[Dict[str, Any]],
    egress: bool,
    check_mode: bool,
) -> bool:
    # transform rules: from ansible list to boto3 dict
    ansible_rules = [ansible_to_boto3_dict_rule(r, egress) for r in ansible_rules]

    # find added rules
    added_rules = find_added_rules(ansible_rules, aws_rules)
    # find removed rules
    removed_rules = find_added_rules(aws_rules, ansible_rules)

    changed = False
    # Removed Rules
    for rule in removed_rules:
        changed = True
        if not check_mode:
            delete_network_acl_entry(client, network_acl_id=nacl_id, rule_number=rule["RuleNumber"], egress=egress)

    # Added Rules
    for rule in added_rules:
        changed = True
        if not check_mode:
            rule_number = rule.pop("RuleNumber")
            protocol = rule.pop("Protocol")
            rule_action = rule.pop("RuleAction")
            egress = rule.pop("Egress")
            create_network_acl_entry(
                client,
                network_acl_id=nacl_id,
                protocol=protocol,
                egress=egress,
                rule_action=rule_action,
                rule_number=rule_number,
                **rule,
            )

    return changed


def is_ipv6(cidr: str) -> bool:
    return ":" in cidr


def process_rule_entry(entry: List[Any]) -> Dict[str, Any]:
    params = {}
    if is_ipv6(entry[3]):
        params["Ipv6CidrBlock"] = entry[3]
    else:
        params["CidrBlock"] = entry[3]
    if icmp_present(entry):
        params["IcmpTypeCode"] = {"Type": int(entry[4]), "Code": int(entry[5])}
    else:
        if entry[6] or entry[7]:
            params["PortRange"] = {"From": entry[6], "To": entry[7]}

    return params


def add_network_acl_entries(
    client, nacl_id: str, ansible_entries: List[List[str]], egress: bool, check_mode: bool
) -> bool:
    changed = False
    for entry in ansible_entries:
        changed = True
        if not check_mode:
            create_network_acl_entry(
                client,
                network_acl_id=nacl_id,
                protocol=str(PROTOCOL_NUMBERS[entry[1]]),
                egress=egress,
                rule_action=entry[2],
                rule_number=entry[0],
                **process_rule_entry(entry),
            )
    return changed


def associate_nacl_to_subnets(client, module: AnsibleAWSModule, nacl_id: str, subnets_ids: List[str]) -> bool:
    changed = False
    if subnets_ids:
        network_acls = describe_network_acls(client, Filters=[{"Name": "association.subnet-id", "Values": subnets_ids}])
        associations = [
            association["NetworkAclAssociationId"]
            for nacl in network_acls
            for association in nacl["Associations"]
            if association["SubnetId"] in subnets_ids
        ]
        for association_id in associations:
            changed = True
            if not module.check_mode:
                replace_network_acl_association(client, network_acl_id=nacl_id, association_id=association_id)
    return changed


def ensure_present(client, module: AnsibleAWSModule) -> None:
    changed = False
    nacl = describe_network_acl(client, module)
    nacl_id = None
    subnets_ids = []
    subnets = module.params.get("subnets")
    if subnets:
        subnets_ids = find_subnets_ids(client, module, subnets)

    if not nacl:
        if module.check_mode:
            module.exit_json(changed=True, msg="Would have created Network ACL if not in check mode.")

        # Create Network ACL
        tags = {}
        name = module.params.get("name")
        vpc_id = module.params.get("vpc_id")
        if name:
            tags["Name"] = name
        if module.params.get("tags"):
            tags.update(module.params.get("tags"))
        nacl = create_network_acl(client, vpc_id, tags)
        changed = True

        # Associate Subnets to Network ACL
        nacl_id = nacl["NetworkAclId"]
        changed |= associate_nacl_to_subnets(client, module, nacl_id, subnets_ids)

        # Create Network ACL entries (ingress and egress)
        changed |= add_network_acl_entries(
            client, nacl_id, module.params.get("ingress"), egress=False, check_mode=module.check_mode
        )
        changed |= add_network_acl_entries(
            client, nacl_id, module.params.get("egress"), egress=True, check_mode=module.check_mode
        )
    else:
        nacl_id = nacl["NetworkAclId"]
        changed |= subnets_changed(client, module, nacl_id, subnets_ids)
        changed |= nacls_changed(client, module, nacl)
        changed |= tags_changed(client, module, nacl_id)

    module.exit_json(changed=changed, nacl_id=nacl_id)


def ensure_absent(client, module: AnsibleAWSModule) -> None:
    changed = False
    nacl = describe_network_acl(client, module)
    if not nacl:
        module.exit_json(changed=changed)

    nacl_id = nacl["NetworkAclId"]
    vpc_id = nacl["VpcId"]
    associations = nacl["Associations"]
    assoc_ids = [a["NetworkAclAssociationId"] for a in associations]

    # Find default NACL associated to the VPC
    default_nacl_id = find_default_vpc_nacl(client, vpc_id)
    if not default_nacl_id:
        module.exit_json(changed=changed, msg="Default NACL ID not found - Check the VPC ID")

    # Replace Network ACL association
    for assoc_id in assoc_ids:
        changed = True
        if not module.check_mode:
            replace_network_acl_association(client, network_acl_id=default_nacl_id, association_id=assoc_id)

    # Delete Network ACL
    changed = True
    if module.check_mode:
        module.exit_json(changed=changed, msg=f"Would have deleted Network ACL id '{nacl_id}' if not in check mode.")

    changed = delete_network_acl(client, network_acl_id=nacl_id)
    module.exit_json(changed=changed, msg=f"Network ACL id '{nacl_id}' successfully deleted.")


def describe_network_acl(client, module: AnsibleAWSModule) -> Optional[Dict[str, Any]]:
    nacl_id = module.params.get("nacl_id")
    name = module.params.get("name")

    if nacl_id:
        filters = [{"Name": "network-acl-id", "Values": [nacl_id]}]
    else:
        filters = [{"Name": "tag:Name", "Values": [name]}]
    network_acls = describe_network_acls(client, Filters=filters)
    return None if not network_acls else network_acls[0]


def find_default_vpc_nacl(client, vpc_id: str) -> Optional[str]:
    default_nacl_id = None
    for nacl in describe_network_acls(client, Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]):
        if nacl.get("IsDefault", False):
            default_nacl_id = nacl["NetworkAclId"]
            break
    return default_nacl_id


def find_subnets_ids(client, module: AnsibleAWSModule, subnets_ids_or_names: List[str]) -> List[str]:
    subnets_ids = []
    subnets_names = []

    # Find Subnets by ID
    subnets = describe_subnets(client, Filters=[{"Name": "subnet-id", "Values": subnets_ids_or_names}])
    subnets_ids += [subnet["SubnetId"] for subnet in subnets]
    subnets_names += [tag["Value"] for subnet in subnets for tag in subnet.get("Tags", []) if tag["Key"] == "Name"]

    # Find Subnets by Name
    subnets = describe_subnets(client, Filters=[{"Name": "tag:Name", "Values": subnets_ids_or_names}])
    subnets_ids += [subnet["SubnetId"] for subnet in subnets]
    subnets_names += [tag["Value"] for subnet in subnets for tag in subnet.get("Tags", []) if tag["Key"] == "Name"]

    unexisting_subnets = [s for s in subnets_ids_or_names if s not in subnets_names + subnets_ids]
    if unexisting_subnets:
        module.fail_json(msg=f"The following subnets do not exist: {unexisting_subnets}")
    return subnets_ids


def main():
    argument_spec = dict(
        vpc_id=dict(),
        name=dict(),
        nacl_id=dict(),
        subnets=dict(required=False, type="list", default=[], elements="str"),
        tags=dict(required=False, type="dict", aliases=["resource_tags"]),
        purge_tags=dict(required=False, type="bool", default=True),
        ingress=dict(required=False, type="list", default=list(), elements="list"),
        egress=dict(required=False, type="list", default=list(), elements="list"),
        state=dict(default="present", choices=["present", "absent"]),
    )

    mutually_exclusive = [
        ["name", "nacl_id"],
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[["name", "nacl_id"]],
        required_if=[["state", "present", ["vpc_id"]]],
        mutually_exclusive=mutually_exclusive,
    )

    client = module.client("ec2")

    try:
        if module.params.get("state") == "present":
            ensure_present(client, module)
        else:
            ensure_absent(client, module)
    except AnsibleEC2Error as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
