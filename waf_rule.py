#!/usr/bin/python
# Copyright (c) 2017 Will Thames
# Copyright (c) 2015 Mike Mochan
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
module: waf_rule
short_description: Create and delete WAF Rules
version_added: 1.0.0
description:
  - Read the AWS documentation for WAF
    U(https://aws.amazon.com/documentation/waf/).
  - Prior to release 5.0.0 this module was called C(community.aws.aws_waf_rule).
    The usage did not change.

author:
  - Mike Mochan (@mmochan)
  - Will Thames (@willthames)
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.boto3

options:
  name:
    description: Name of the Web Application Firewall rule.
    required: true
    type: str
  metric_name:
    description:
      - A friendly name or description for the metrics for the rule.
      - The name can contain only alphanumeric characters (A-Z, a-z, 0-9); the name may not contain whitespace.
      - You can't change I(metric_name) after you create the rule.
      - Defaults to the same as I(name) with disallowed characters removed.
    type: str
  state:
    description: Whether the rule should be present or absent.
    choices: ['present', 'absent']
    default: present
    type: str
  conditions:
    description: >
      List of conditions used in the rule. M(community.aws.waf_condition) can be used to create new conditions.
    type: list
    elements: dict
    suboptions:
      type:
        required: true
        type: str
        choices: ['byte','geo','ip','size','sql','xss']
        description: The type of rule to match.
      negated:
        required: true
        type: bool
        description: Whether the condition should be negated.
      condition:
        required: true
        type: str
        description: The name of the condition.  The condition must already exist.
  purge_conditions:
    description:
      - Whether or not to remove conditions that are not passed when updating I(conditions).
    default: false
    type: bool
  waf_regional:
    description: Whether to use C(waf-regional) module.
    default: false
    required: false
    type: bool
'''

EXAMPLES = r'''
  - name: create WAF rule
    community.aws.waf_rule:
      name: my_waf_rule
      conditions:
        - name: my_regex_condition
          type: regex
          negated: false
        - name: my_geo_condition
          type: geo
          negated: false
        - name: my_byte_condition
          type: byte
          negated: true

  - name: remove WAF rule
    community.aws.waf_rule:
      name: "my_waf_rule"
      state: absent
'''

RETURN = r'''
rule:
  description: WAF rule contents
  returned: always
  type: complex
  contains:
    metric_name:
      description: Metric name for the rule.
      returned: always
      type: str
      sample: ansibletest1234rule
    name:
      description: Friendly name for the rule.
      returned: always
      type: str
      sample: ansible-test-1234_rule
    predicates:
      description: List of conditions used in the rule.
      returned: always
      type: complex
      contains:
        data_id:
          description: ID of the condition.
          returned: always
          type: str
          sample: 8251acdb-526c-42a8-92bc-d3d13e584166
        negated:
          description: Whether the sense of the condition is negated.
          returned: always
          type: bool
          sample: false
        type:
          description: type of the condition.
          returned: always
          type: str
          sample: ByteMatch
    rule_id:
      description: ID of the WAF rule.
      returned: always
      type: str
      sample: 15de0cbc-9204-4e1f-90e6-69b2f415c261
'''

import re

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.waf import (
    MATCH_LOOKUP,
    list_regional_rules_with_backoff,
    list_rules_with_backoff,
    run_func_with_change_token_backoff,
    get_web_acl_with_backoff,
    list_web_acls_with_backoff,
    list_regional_web_acls_with_backoff,
)


def get_rule_by_name(client, module, name):
    rules = [d['RuleId'] for d in list_rules(client, module) if d['Name'] == name]
    if rules:
        return rules[0]


def get_rule(client, module, rule_id):
    try:
        return client.get_rule(RuleId=rule_id)['Rule']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Could not get WAF rule')


def list_rules(client, module):
    if client.__class__.__name__ == 'WAF':
        try:
            return list_rules_with_backoff(client)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg='Could not list WAF rules')
    elif client.__class__.__name__ == 'WAFRegional':
        try:
            return list_regional_rules_with_backoff(client)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg='Could not list WAF Regional rules')


def list_regional_rules(client, module):
    try:
        return list_regional_rules_with_backoff(client)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Could not list WAF rules')


def find_and_update_rule(client, module, rule_id):
    rule = get_rule(client, module, rule_id)
    rule_id = rule['RuleId']

    existing_conditions = dict((condition_type, dict()) for condition_type in MATCH_LOOKUP)
    desired_conditions = dict((condition_type, dict()) for condition_type in MATCH_LOOKUP)
    all_conditions = dict()

    for condition_type in MATCH_LOOKUP:
        method = 'list_' + MATCH_LOOKUP[condition_type]['method'] + 's'
        all_conditions[condition_type] = dict()
        try:
            paginator = client.get_paginator(method)
            func = paginator.paginate().build_full_result
        except (KeyError, botocore.exceptions.OperationNotPageableError):
            # list_geo_match_sets and list_regex_match_sets do not have a paginator
            # and throw different exceptions
            func = getattr(client, method)
        try:
            pred_results = func()[MATCH_LOOKUP[condition_type]['conditionset'] + 's']
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg='Could not list %s conditions' % condition_type)
        for pred in pred_results:
            pred['DataId'] = pred[MATCH_LOOKUP[condition_type]['conditionset'] + 'Id']
            all_conditions[condition_type][pred['Name']] = camel_dict_to_snake_dict(pred)
            all_conditions[condition_type][pred['DataId']] = camel_dict_to_snake_dict(pred)

    for condition in module.params['conditions']:
        desired_conditions[condition['type']][condition['name']] = condition

    reverse_condition_types = dict((v['type'], k) for (k, v) in MATCH_LOOKUP.items())
    for condition in rule['Predicates']:
        existing_conditions[reverse_condition_types[condition['Type']]][condition['DataId']] = camel_dict_to_snake_dict(condition)

    insertions = list()
    deletions = list()

    for condition_type in desired_conditions:
        for (condition_name, condition) in desired_conditions[condition_type].items():
            if condition_name not in all_conditions[condition_type]:
                module.fail_json(msg="Condition %s of type %s does not exist" % (condition_name, condition_type))
            condition['data_id'] = all_conditions[condition_type][condition_name]['data_id']
            if condition['data_id'] not in existing_conditions[condition_type]:
                insertions.append(format_for_insertion(condition))

    if module.params['purge_conditions']:
        for condition_type in existing_conditions:
            deletions.extend([format_for_deletion(condition) for condition in existing_conditions[condition_type].values()
                              if not all_conditions[condition_type][condition['data_id']]['name'] in desired_conditions[condition_type]])

    changed = bool(insertions or deletions)
    update = {
        'RuleId': rule_id,
        'Updates': insertions + deletions
    }
    if changed:
        try:
            run_func_with_change_token_backoff(client, module, update, client.update_rule, wait=True)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg='Could not update rule conditions')

    return changed, get_rule(client, module, rule_id)


def format_for_insertion(condition):
    return dict(Action='INSERT',
                Predicate=dict(Negated=condition['negated'],
                               Type=MATCH_LOOKUP[condition['type']]['type'],
                               DataId=condition['data_id']))


def format_for_deletion(condition):
    return dict(Action='DELETE',
                Predicate=dict(Negated=condition['negated'],
                               Type=condition['type'],
                               DataId=condition['data_id']))


def remove_rule_conditions(client, module, rule_id):
    conditions = get_rule(client, module, rule_id)['Predicates']
    updates = [format_for_deletion(camel_dict_to_snake_dict(condition)) for condition in conditions]
    try:
        run_func_with_change_token_backoff(client, module, {'RuleId': rule_id, 'Updates': updates}, client.update_rule)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Could not remove rule conditions')


def ensure_rule_present(client, module):
    name = module.params['name']
    rule_id = get_rule_by_name(client, module, name)
    params = dict()
    if rule_id:
        return find_and_update_rule(client, module, rule_id)
    else:
        params['Name'] = module.params['name']
        metric_name = module.params['metric_name']
        if not metric_name:
            metric_name = re.sub(r'[^a-zA-Z0-9]', '', module.params['name'])
        params['MetricName'] = metric_name
        try:
            new_rule = run_func_with_change_token_backoff(client, module, params, client.create_rule)['Rule']
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg='Could not create rule')
        return find_and_update_rule(client, module, new_rule['RuleId'])


def find_rule_in_web_acls(client, module, rule_id):
    web_acls_in_use = []
    try:
        if client.__class__.__name__ == 'WAF':
            all_web_acls = list_web_acls_with_backoff(client)
        elif client.__class__.__name__ == 'WAFRegional':
            all_web_acls = list_regional_web_acls_with_backoff(client)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Could not list Web ACLs')
    for web_acl in all_web_acls:
        try:
            web_acl_details = get_web_acl_with_backoff(client, web_acl['WebACLId'])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg='Could not get Web ACL details')
        if rule_id in [rule['RuleId'] for rule in web_acl_details['Rules']]:
            web_acls_in_use.append(web_acl_details['Name'])
    return web_acls_in_use


def ensure_rule_absent(client, module):
    rule_id = get_rule_by_name(client, module, module.params['name'])
    in_use_web_acls = find_rule_in_web_acls(client, module, rule_id)
    if in_use_web_acls:
        web_acl_names = ', '.join(in_use_web_acls)
        module.fail_json(msg="Rule %s is in use by Web ACL(s) %s" %
                         (module.params['name'], web_acl_names))
    if rule_id:
        remove_rule_conditions(client, module, rule_id)
        try:
            return True, run_func_with_change_token_backoff(client, module, {'RuleId': rule_id}, client.delete_rule, wait=True)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg='Could not delete rule')
    return False, {}


def main():
    argument_spec = dict(
        name=dict(required=True),
        metric_name=dict(),
        state=dict(default='present', choices=['present', 'absent']),
        conditions=dict(type='list', elements='dict'),
        purge_conditions=dict(type='bool', default=False),
        waf_regional=dict(type='bool', default=False),
    )
    module = AnsibleAWSModule(argument_spec=argument_spec)
    state = module.params.get('state')

    resource = 'waf' if not module.params['waf_regional'] else 'waf-regional'
    client = module.client(resource)
    if state == 'present':
        (changed, results) = ensure_rule_present(client, module)
    else:
        (changed, results) = ensure_rule_absent(client, module)

    module.exit_json(changed=changed, rule=camel_dict_to_snake_dict(results))


if __name__ == '__main__':
    main()
