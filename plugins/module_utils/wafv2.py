from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # caught by AnsibleAWSModule


def wafv2_list_web_acls(wafv2, scope, fail_json_aws, nextmarker=None):
    # there is currently no paginator for wafv2
    req_obj = {
        'Scope': scope,
        'Limit': 100
    }
    if nextmarker:
        req_obj['NextMarker'] = nextmarker

    try:
        response = wafv2.list_web_acls(**req_obj)
    except (BotoCoreError, ClientError) as e:
        fail_json_aws(e, msg="Failed to list wafv2 web acl.")

    if response.get('NextMarker'):
        response['WebACLs'] += wafv2_list_web_acls(wafv2, scope, fail_json_aws, nextmarker=response.get('NextMarker')).get('WebACLs')
    return response


def wafv2_list_rule_groups(wafv2, scope, fail_json_aws, nextmarker=None):
    # there is currently no paginator for wafv2
    req_obj = {
        'Scope': scope,
        'Limit': 100
    }
    if nextmarker:
        req_obj['NextMarker'] = nextmarker

    try:
        response = wafv2.list_rule_groups(**req_obj)
    except (BotoCoreError, ClientError) as e:
        fail_json_aws(e, msg="Failed to list wafv2 rule group.")

    if response.get('NextMarker'):
        response['RuleGroups'] += wafv2_list_rule_groups(wafv2, scope, fail_json_aws, nextmarker=response.get('NextMarker')).get('RuleGroups')
    return response


def wafv2_snake_dict_to_camel_dict(a):
    retval = {}
    for item in a.keys():
        if isinstance(a.get(item), dict):
            if 'Ip' in item:
                retval[item.replace('Ip', 'IP')] = wafv2_snake_dict_to_camel_dict(a.get(item))
            elif 'Arn' == item:
                retval['ARN'] = wafv2_snake_dict_to_camel_dict(a.get(item))
            else:
                retval[item] = wafv2_snake_dict_to_camel_dict(a.get(item))
        elif isinstance(a.get(item), list):
            retval[item] = []
            for idx in range(len(a.get(item))):
                retval[item].append(wafv2_snake_dict_to_camel_dict(a.get(item)[idx]))
        elif 'Ip' in item:
            retval[item.replace('Ip', 'IP')] = a.get(item)
        elif 'Arn' == item:
            retval['ARN'] = a.get(item)
        else:
            retval[item] = a.get(item)
    return retval


def nested_byte_values_to_strings(rule, keyname):
    """
    currently valid nested byte values in statements array are
        - OrStatement
        - AndStatement
        - NotStatement
    """
    if rule.get('Statement', {}).get(keyname):
        for idx in range(len(rule.get('Statement', {}).get(keyname, {}).get('Statements'))):
            if rule['Statement'][keyname]['Statements'][idx].get('ByteMatchStatement'):
                rule['Statement'][keyname]['Statements'][idx]['ByteMatchStatement']['SearchString'] = \
                    rule.get('Statement').get(keyname).get('Statements')[idx].get('ByteMatchStatement').get('SearchString').decode('utf-8')

    return rule


def byte_values_to_strings_before_compare(rules):
    for idx in range(len(rules)):
        if rules[idx].get('Statement', {}).get('ByteMatchStatement', {}).get('SearchString'):
            rules[idx]['Statement']['ByteMatchStatement']['SearchString'] = \
                rules[idx].get('Statement').get('ByteMatchStatement').get('SearchString').decode('utf-8')

        else:
            for statement in ['AndStatement', 'OrStatement', 'NotStatement']:
                if rules[idx].get('Statement', {}).get(statement):
                    rules[idx] = nested_byte_values_to_strings(rules[idx], statement)

    return rules


def compare_priority_rules(existing_rules, requested_rules, purge_rules, state):
    diff = False
    existing_rules = sorted(existing_rules, key=lambda k: k['Priority'])
    existing_rules = byte_values_to_strings_before_compare(existing_rules)
    requested_rules = sorted(requested_rules, key=lambda k: k['Priority'])

    if purge_rules and state == 'present':
        merged_rules = requested_rules
        if len(existing_rules) == len(requested_rules):
            for idx in range(len(existing_rules)):
                if existing_rules[idx] != requested_rules[idx]:
                    diff = True
                    break
        else:
            diff = True

    else:
        # find same priority rules
        #   * pop same priority rule from existing rule
        #   * compare existing rule
        merged_rules = []
        ex_idx_pop = []
        for existing_idx in range(len(existing_rules)):
            for requested_idx in range(len(requested_rules)):
                if existing_rules[existing_idx].get('Priority') == requested_rules[requested_idx].get('Priority'):
                    if state == 'present':
                        ex_idx_pop.append(existing_idx)
                        if existing_rules[existing_idx] != requested_rules[requested_idx]:
                            diff = True
                    elif existing_rules[existing_idx] == requested_rules[requested_idx]:
                        ex_idx_pop.append(existing_idx)
                        diff = True

        prev_count = len(existing_rules)
        for idx in ex_idx_pop:
            existing_rules.pop(idx)

        if state == 'present':
            merged_rules = existing_rules + requested_rules

            if len(merged_rules) != prev_count:
                diff = True
        else:
            merged_rules = existing_rules

    return diff, merged_rules
