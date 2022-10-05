#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: s3_lifecycle
version_added: 1.0.0
short_description: Manage S3 bucket lifecycle rules in AWS
description:
    - Manage S3 bucket lifecycle rules in AWS.
author: "Rob White (@wimnat)"
notes:
  - If specifying expiration time as days then transition time must also be specified in days.
  - If specifying expiration time as a date then transition time must also be specified as a date.
options:
  name:
    description:
      - Name of the S3 bucket.
    required: true
    type: str
  abort_incomplete_multipart_upload_days:
    description:
      - Specifies the days since the initiation of an incomplete multipart upload that Amazon S3 will wait before permanently removing all parts of the upload.
    type: int
    version_added: 2.2.0
  expiration_date:
    description:
      - Indicates the lifetime of the objects that are subject to the rule by the date they will expire.
      - The value must be ISO-8601 format, the time must be midnight and a GMT timezone must be specified.
      - This cannot be specified with I(expire_object_delete_marker)
    type: str
  expiration_days:
    description:
      - Indicates the lifetime, in days, of the objects that are subject to the rule.
      - The value must be a non-zero positive integer.
      - This cannot be specified with I(expire_object_delete_marker)
    type: int
  expire_object_delete_marker:
    description:
      - Indicates whether Amazon S3 will remove a delete marker with no noncurrent versions.
      - If set to C(true), the delete marker will be expired; if set to C(false) the policy takes no action.
      - This cannot be specified with I(expiration_days) or I(expiration_date).
    type: bool
    version_added: 2.2.0
  prefix:
    description:
      - Prefix identifying one or more objects to which the rule applies.
      - If no prefix is specified, the rule will apply to the whole bucket.
    type: str
  purge_transitions:
    description:
      - Whether to replace all the current transition(s) with the new transition(s).
      - When C(false), the provided transition(s) will be added, replacing transitions
        with the same storage_class. When true, existing transitions will be removed
        and replaced with the new transition(s)
    default: true
    type: bool
  noncurrent_version_expiration_days:
    description:
      - The number of days after which non-current versions should be deleted.
    required: false
    type: int
  noncurrent_version_storage_class:
    description:
      - The storage class to which non-current versions are transitioned.
    default: glacier
    choices: ['glacier', 'onezone_ia', 'standard_ia', 'intelligent_tiering', 'deep_archive']
    required: false
    type: str
  noncurrent_version_transition_days:
    description:
      - The number of days after which non-current versions will be transitioned
        to the storage class specified in I(noncurrent_version_storage_class).
    required: false
    type: int
  noncurrent_version_transitions:
    description:
      - A list of transition behaviors to be applied to noncurrent versions for the rule.
      - Each storage class may be used only once. Each transition behavior contains these elements
          I(transition_days)
          I(storage_class)
    type: list
    elements: dict
  rule_id:
    description:
      - Unique identifier for the rule.
      - The value cannot be longer than 255 characters.
      - A unique value for the rule will be generated if no value is provided.
    type: str
  state:
    description:
      - Create or remove the lifecycle rule.
    default: present
    choices: [ 'present', 'absent' ]
    type: str
  status:
    description:
      - If C(enabled), the rule is currently being applied.
      - If C(disabled), the rule is not currently being applied.
    default: enabled
    choices: [ 'enabled', 'disabled' ]
    type: str
  storage_class:
    description:
      - The storage class to transition to.
    default: glacier
    choices: [ 'glacier', 'onezone_ia', 'standard_ia', 'intelligent_tiering', 'deep_archive']
    type: str
  transition_date:
    description:
      - Indicates the lifetime of the objects that are subject to the rule by the date they
        will transition to a different storage class.
      - The value must be ISO-8601 format, the time must be midnight and a GMT timezone must
        be specified.
      - If (transition_days) is not specified, this parameter is required.
    type: str
  transition_days:
    description:
      - Indicates when, in days, an object transitions to a different storage class.
      - If I(transition_date) is not specified, this parameter is required.
    type: int
  transitions:
    description:
      - A list of transition behaviors to be applied to the rule.
      - Each storage class may be used only once. Each transition behavior may contain these elements
          I(transition_days)
          I(transition_date)
          I(storage_class)
    type: list
    elements: dict
  wait:
    description:
      - Wait for the configuration to complete before returning.
    version_added: 1.5.0
    type: bool
    default: false
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
- amazon.aws.boto3

'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Configure a lifecycle rule on a bucket to expire (delete) items with a prefix of /logs/ after 30 days
  community.aws.s3_lifecycle:
    name: mybucket
    expiration_days: 30
    prefix: logs/
    status: enabled
    state: present

- name: Configure a lifecycle rule to transition all items with a prefix of /logs/ to glacier after 7 days and then delete after 90 days
  community.aws.s3_lifecycle:
    name: mybucket
    transition_days: 7
    expiration_days: 90
    prefix: logs/
    status: enabled
    state: present

# Note that midnight GMT must be specified.
# Be sure to quote your date strings
- name: Configure a lifecycle rule to transition all items with a prefix of /logs/ to glacier on 31 Dec 2020 and then delete on 31 Dec 2030.
  community.aws.s3_lifecycle:
    name: mybucket
    transition_date: "2020-12-30T00:00:00.000Z"
    expiration_date: "2030-12-30T00:00:00.000Z"
    prefix: logs/
    status: enabled
    state: present

- name: Disable the rule created above
  community.aws.s3_lifecycle:
    name: mybucket
    prefix: logs/
    status: disabled
    state: present

- name: Delete the lifecycle rule created above
  community.aws.s3_lifecycle:
    name: mybucket
    prefix: logs/
    state: absent

- name: Configure a lifecycle rule to transition all backup files older than 31 days in /backups/ to standard infrequent access class.
  community.aws.s3_lifecycle:
    name: mybucket
    prefix: backups/
    storage_class: standard_ia
    transition_days: 31
    state: present
    status: enabled

- name: Configure a lifecycle rule to transition files to infrequent access after 30 days and glacier after 90
  community.aws.s3_lifecycle:
    name: mybucket
    prefix: logs/
    state: present
    status: enabled
    transitions:
      - transition_days: 30
        storage_class: standard_ia
      - transition_days: 90
        storage_class: glacier
'''

from copy import deepcopy
import datetime
import time

try:
    from dateutil import parser as date_parser
    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAwsModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_message
from ansible_collections.amazon.aws.plugins.module_utils.core import normalize_boto3_result
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry


def parse_date(date):
    if date is None:
        return None
    try:
        if HAS_DATEUTIL:
            return date_parser.parse(date)
        else:
            # Very simplistic
            return datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.000Z")
    except ValueError:
        return None


def fetch_rules(client, module, name):
    # Get the bucket's current lifecycle rules
    try:
        current_lifecycle = client.get_bucket_lifecycle_configuration(aws_retry=True, Bucket=name)
        current_lifecycle_rules = normalize_boto3_result(current_lifecycle['Rules'])
    except is_boto3_error_code('NoSuchLifecycleConfiguration'):
        current_lifecycle_rules = []
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e)
    return current_lifecycle_rules


def build_rule(client, module):
    name = module.params.get("name")
    abort_incomplete_multipart_upload_days = module.params.get("abort_incomplete_multipart_upload_days")
    expiration_date = parse_date(module.params.get("expiration_date"))
    expiration_days = module.params.get("expiration_days")
    expire_object_delete_marker = module.params.get("expire_object_delete_marker")
    noncurrent_version_expiration_days = module.params.get("noncurrent_version_expiration_days")
    noncurrent_version_transition_days = module.params.get("noncurrent_version_transition_days")
    noncurrent_version_transitions = module.params.get("noncurrent_version_transitions")
    noncurrent_version_storage_class = module.params.get("noncurrent_version_storage_class")
    prefix = module.params.get("prefix") or ""
    rule_id = module.params.get("rule_id")
    status = module.params.get("status")
    storage_class = module.params.get("storage_class")
    transition_date = parse_date(module.params.get("transition_date"))
    transition_days = module.params.get("transition_days")
    transitions = module.params.get("transitions")
    purge_transitions = module.params.get("purge_transitions")

    rule = dict(Filter=dict(Prefix=prefix), Status=status.title())
    if rule_id is not None:
        rule['ID'] = rule_id

    if abort_incomplete_multipart_upload_days:
        rule['AbortIncompleteMultipartUpload'] = {
            'DaysAfterInitiation': abort_incomplete_multipart_upload_days
        }

    # Create expiration
    if expiration_days is not None:
        rule['Expiration'] = dict(Days=expiration_days)
    elif expiration_date is not None:
        rule['Expiration'] = dict(Date=expiration_date.isoformat())
    elif expire_object_delete_marker is not None:
        rule['Expiration'] = dict(ExpiredObjectDeleteMarker=expire_object_delete_marker)

    if noncurrent_version_expiration_days is not None:
        rule['NoncurrentVersionExpiration'] = dict(NoncurrentDays=noncurrent_version_expiration_days)

    if transition_days is not None:
        rule['Transitions'] = [dict(Days=transition_days, StorageClass=storage_class.upper()), ]

    elif transition_date is not None:
        rule['Transitions'] = [dict(Date=transition_date.isoformat(), StorageClass=storage_class.upper()), ]

    if transitions is not None:
        if not rule.get('Transitions'):
            rule['Transitions'] = []
        for transition in transitions:
            t_out = dict()
            if transition.get('transition_date'):
                t_out['Date'] = transition['transition_date']
            elif transition.get('transition_days') is not None:
                t_out['Days'] = transition['transition_days']
            if transition.get('storage_class'):
                t_out['StorageClass'] = transition['storage_class'].upper()
                rule['Transitions'].append(t_out)

    if noncurrent_version_transition_days is not None:
        rule['NoncurrentVersionTransitions'] = [dict(NoncurrentDays=noncurrent_version_transition_days,
                                                     StorageClass=noncurrent_version_storage_class.upper()), ]

    if noncurrent_version_transitions is not None:
        if not rule.get('NoncurrentVersionTransitions'):
            rule['NoncurrentVersionTransitions'] = []
        for noncurrent_version_transition in noncurrent_version_transitions:
            t_out = dict()
            t_out['NoncurrentDays'] = noncurrent_version_transition['transition_days']
            if noncurrent_version_transition.get('storage_class'):
                t_out['StorageClass'] = noncurrent_version_transition['storage_class'].upper()
                rule['NoncurrentVersionTransitions'].append(t_out)

    return rule


def compare_and_update_configuration(client, module, current_lifecycle_rules, rule):
    purge_transitions = module.params.get("purge_transitions")
    rule_id = module.params.get("rule_id")

    lifecycle_configuration = dict(Rules=[])
    changed = False
    appended = False

    # If current_lifecycle_obj is not None then we have rules to compare, otherwise just add the rule
    if current_lifecycle_rules:
        # If rule ID exists, use that for comparison otherwise compare based on prefix
        for existing_rule in current_lifecycle_rules:
            if rule.get('ID') == existing_rule.get('ID') and rule['Filter'].get('Prefix', '') != existing_rule.get('Filter', {}).get('Prefix', ''):
                existing_rule.pop('ID')
            elif rule_id is None and rule['Filter'].get('Prefix', '') == existing_rule.get('Filter', {}).get('Prefix', ''):
                existing_rule.pop('ID')
            if rule.get('ID') == existing_rule.get('ID'):
                changed_, appended_ = update_or_append_rule(rule, existing_rule, purge_transitions, lifecycle_configuration)
                changed = changed_ or changed
                appended = appended_ or appended
            else:
                lifecycle_configuration['Rules'].append(existing_rule)

        # If nothing appended then append now as the rule must not exist
        if not appended:
            lifecycle_configuration['Rules'].append(rule)
            changed = True
    else:
        lifecycle_configuration['Rules'].append(rule)
        changed = True

    return changed, lifecycle_configuration


def update_or_append_rule(new_rule, existing_rule, purge_transitions, lifecycle_obj):
    changed = False
    if existing_rule['Status'] != new_rule['Status']:
        if not new_rule.get('Transitions') and existing_rule.get('Transitions'):
            new_rule['Transitions'] = existing_rule['Transitions']
        if not new_rule.get('Expiration') and existing_rule.get('Expiration'):
            new_rule['Expiration'] = existing_rule['Expiration']
        if not new_rule.get('NoncurrentVersionExpiration') and existing_rule.get('NoncurrentVersionExpiration'):
            new_rule['NoncurrentVersionExpiration'] = existing_rule['NoncurrentVersionExpiration']
        lifecycle_obj['Rules'].append(new_rule)
        changed = True
        appended = True
    else:
        if not purge_transitions:
            merge_transitions(new_rule, existing_rule)
        if compare_rule(new_rule, existing_rule, purge_transitions):
            lifecycle_obj['Rules'].append(new_rule)
            appended = True
        else:
            lifecycle_obj['Rules'].append(new_rule)
            changed = True
            appended = True
    return changed, appended


def compare_and_remove_rule(current_lifecycle_rules, rule_id=None, prefix=None):
    changed = False
    lifecycle_configuration = dict(Rules=[])

    # Check if rule exists
    # If an ID exists, use that otherwise compare based on prefix
    if rule_id is not None:
        for existing_rule in current_lifecycle_rules:
            if rule_id == existing_rule['ID']:
                # We're not keeping the rule (i.e. deleting) so mark as changed
                changed = True
            else:
                lifecycle_configuration['Rules'].append(existing_rule)
    else:
        for existing_rule in current_lifecycle_rules:
            if prefix == existing_rule['Filter'].get('Prefix', ''):
                # We're not keeping the rule (i.e. deleting) so mark as changed
                changed = True
            else:
                lifecycle_configuration['Rules'].append(existing_rule)

    return changed, lifecycle_configuration


def compare_rule(new_rule, old_rule, purge_transitions):

    # Copy objects
    rule1 = deepcopy(new_rule)
    rule2 = deepcopy(old_rule)

    if purge_transitions:
        return rule1 == rule2
    else:
        transitions1 = rule1.pop('Transitions', [])
        transitions2 = rule2.pop('Transitions', [])
        noncurrent_transtions1 = rule1.pop('NoncurrentVersionTransitions', [])
        noncurrent_transtions2 = rule2.pop('NoncurrentVersionTransitions', [])
        if rule1 != rule2:
            return False
        for transition in transitions1:
            if transition not in transitions2:
                return False
        for transition in noncurrent_transtions1:
            if transition not in noncurrent_transtions2:
                return False
        return True


def merge_transitions(updated_rule, updating_rule):
    # because of the legal S3 transitions, we know only one can exist for each storage class.
    # So, our strategy is build some dicts, keyed on storage class and add the storage class transitions that are only
    # in updating_rule to updated_rule
    updated_transitions = {}
    updating_transitions = {}
    for transition in updated_rule.get('Transitions', []):
        updated_transitions[transition['StorageClass']] = transition
    for transition in updating_rule.get('Transitions', []):
        updating_transitions[transition['StorageClass']] = transition
    for storage_class, transition in updating_transitions.items():
        if updated_transitions.get(storage_class) is None:
            updated_rule['Transitions'].append(transition)


def create_lifecycle_rule(client, module):

    name = module.params.get("name")
    wait = module.params.get("wait")
    changed = False

    old_lifecycle_rules = fetch_rules(client, module, name)
    new_rule = build_rule(client, module)
    (changed, lifecycle_configuration) = compare_and_update_configuration(client, module,
                                                                          old_lifecycle_rules,
                                                                          new_rule)

    # Write lifecycle to bucket
    try:
        client.put_bucket_lifecycle_configuration(
            aws_retry=True,
            Bucket=name,
            LifecycleConfiguration=lifecycle_configuration)
    except is_boto3_error_message('At least one action needs to be specified in a rule'):
        # Amazon interpretted this as not changing anything
        changed = False
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, lifecycle_configuration=lifecycle_configuration, name=name, old_lifecycle_rules=old_lifecycle_rules)

    _changed = changed
    _retries = 10
    _not_changed_cnt = 6
    while wait and _changed and _retries and _not_changed_cnt:
        # We've seen examples where get_bucket_lifecycle_configuration returns
        # the updated rules, then the old rules, then the updated rules again and
        # again couple of times.
        # Thus try to read the rule few times in a row to check if it has changed.
        time.sleep(5)
        _retries -= 1
        new_rules = fetch_rules(client, module, name)
        (_changed, lifecycle_configuration) = compare_and_update_configuration(client, module,
                                                                               new_rules,
                                                                               new_rule)
        if not _changed:
            _not_changed_cnt -= 1
            _changed = True
        else:
            _not_changed_cnt = 6

    new_rules = fetch_rules(client, module, name)

    module.exit_json(changed=changed, new_rule=new_rule, rules=new_rules,
                     old_rules=old_lifecycle_rules, _retries=_retries,
                     _config=lifecycle_configuration)


def destroy_lifecycle_rule(client, module):

    name = module.params.get("name")
    prefix = module.params.get("prefix")
    rule_id = module.params.get("rule_id")
    wait = module.params.get("wait")
    changed = False

    if prefix is None:
        prefix = ""

    current_lifecycle_rules = fetch_rules(client, module, name)
    changed, lifecycle_obj = compare_and_remove_rule(current_lifecycle_rules, rule_id, prefix)

    # Write lifecycle to bucket or, if there no rules left, delete lifecycle configuration
    try:
        if lifecycle_obj['Rules']:
            client.put_bucket_lifecycle_configuration(
                aws_retry=True,
                Bucket=name,
                LifecycleConfiguration=lifecycle_obj)
        elif current_lifecycle_rules:
            changed = True
            client.delete_bucket_lifecycle(aws_retry=True, Bucket=name)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e)

    _changed = changed
    _retries = 10
    _not_changed_cnt = 6
    while wait and _changed and _retries and _not_changed_cnt:
        # We've seen examples where get_bucket_lifecycle_configuration returns
        # the updated rules, then the old rules, then the updated rules again and
        # again couple of times.
        # Thus try to read the rule few times in a row to check if it has changed.
        time.sleep(5)
        _retries -= 1
        new_rules = fetch_rules(client, module, name)
        (_changed, lifecycle_configuration) = compare_and_remove_rule(new_rules, rule_id, prefix)
        if not _changed:
            _not_changed_cnt -= 1
            _changed = True
        else:
            _not_changed_cnt = 6

    new_rules = fetch_rules(client, module, name)

    module.exit_json(changed=changed, rules=new_rules, old_rules=current_lifecycle_rules,
                     _retries=_retries)


def main():
    s3_storage_class = ['glacier', 'onezone_ia', 'standard_ia', 'intelligent_tiering', 'deep_archive']
    argument_spec = dict(
        name=dict(required=True, type='str'),
        abort_incomplete_multipart_upload_days=dict(type='int'),
        expiration_days=dict(type='int'),
        expiration_date=dict(),
        expire_object_delete_marker=dict(type='bool'),
        noncurrent_version_expiration_days=dict(type='int'),
        noncurrent_version_storage_class=dict(default='glacier', type='str', choices=s3_storage_class),
        noncurrent_version_transition_days=dict(type='int'),
        noncurrent_version_transitions=dict(type='list', elements='dict'),
        prefix=dict(),
        rule_id=dict(),
        state=dict(default='present', choices=['present', 'absent']),
        status=dict(default='enabled', choices=['enabled', 'disabled']),
        storage_class=dict(default='glacier', type='str', choices=s3_storage_class),
        transition_days=dict(type='int'),
        transition_date=dict(),
        transitions=dict(type='list', elements='dict'),
        purge_transitions=dict(default=True, type='bool'),
        wait=dict(type='bool', default=False)
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              mutually_exclusive=[
                                  ['expiration_days', 'expiration_date', 'expire_object_delete_marker'],
                                  ['expiration_days', 'transition_date'],
                                  ['transition_days', 'transition_date'],
                                  ['transition_days', 'expiration_date'],
                                  ['transition_days', 'transitions'],
                                  ['transition_date', 'transitions'],
                                  ['noncurrent_version_transition_days', 'noncurrent_version_transitions'],
                              ],)

    client = module.client('s3', retry_decorator=AWSRetry.jittered_backoff())

    expiration_date = module.params.get("expiration_date")
    transition_date = module.params.get("transition_date")
    state = module.params.get("state")

    if state == 'present' and module.params["status"] == "enabled":  # allow deleting/disabling a rule by id/prefix

        required_when_present = ('abort_incomplete_multipart_upload_days',
                                 'expiration_date', 'expiration_days', 'expire_object_delete_marker',
                                 'transition_date', 'transition_days', 'transitions',
                                 'noncurrent_version_expiration_days',
                                 'noncurrent_version_transition_days',
                                 'noncurrent_version_transitions')
        for param in required_when_present:
            if module.params.get(param) is None:
                break
        else:
            msg = "one of the following is required when 'state' is 'present': %s" % ', '.join(required_when_present)
            module.fail_json(msg=msg)

    # If dates have been set, make sure they're in a valid format
    if expiration_date:
        expiration_date = parse_date(expiration_date)
        if expiration_date is None:
            module.fail_json(msg="expiration_date is not a valid ISO-8601 format."
                             "  The time must be midnight and a timezone of GMT must be included")
    if transition_date:
        transition_date = parse_date(transition_date)
        if transition_date is None:
            module.fail_json(msg="transition_date is not a valid ISO-8601 format."
                             "  The time must be midnight and a timezone of GMT must be included")

    if state == 'present':
        create_lifecycle_rule(client, module)
    elif state == 'absent':
        destroy_lifecycle_rule(client, module)


if __name__ == '__main__':
    main()
