#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017, Ben Tomasik <ben@tomasik.io>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ses_rule_set
version_added: 1.0.0
short_description: Manages SES inbound receipt rule sets
description:
  - This module allows you to create, delete, and manage SES receipt rule sets
  - Prior to release 5.0.0 this module was called C(community.aws.aws_ses_rule_set).
    The usage did not change.
author:
  - "Ben Tomasik (@tomislacker)"
  - "Ed Costello (@orthanc)"
options:
  name:
    description:
      - The name of the receipt rule set.
    required: True
    type: str
  state:
    description:
      - Whether to create (or update) or destroy the receipt rule set.
    required: False
    default: present
    choices: ["absent", "present"]
    type: str
  active:
    description:
      - Whether or not this rule set should be the active rule set. Only has an impact if I(state) is C(present).
      - If omitted, the active rule set will not be changed.
      - If C(True) then this rule set will be made active and all others inactive.
      - if C(False) then this rule set will be deactivated. Be careful with this as you can end up with no active rule set.
    type: bool
    required: False
  force:
    description:
      - When deleting a rule set, deactivate it first (AWS prevents deletion of the active rule set).
    type: bool
    required: False
    default: False
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create default rule set and activate it if not already
  community.aws.ses_rule_set:
    name: default-rule-set
    state: present
    active: true

- name: Create some arbitrary rule set but do not activate it
  community.aws.ses_rule_set:
    name: arbitrary-rule-set
    state: present

- name: Explicitly deactivate the default rule set leaving no active rule set
  community.aws.ses_rule_set:
    name: default-rule-set
    state: present
    active: false

- name: Remove an arbitrary inactive rule set
  community.aws.ses_rule_set:
    name: arbitrary-rule-set
    state: absent

- name: Remove an ruleset even if we have to first deactivate it to remove it
  community.aws.ses_rule_set:
    name: default-rule-set
    state: absent
    force: true
"""

RETURN = r"""
active:
  description: if the SES rule set is active
  returned: success if I(state) is C(present)
  type: bool
  sample: true
rule_sets:
  description: The list of SES receipt rule sets that exist after any changes.
  returned: success
  type: list
  sample: [{
      "created_timestamp": "2018-02-25T01:20:32.690000+00:00",
      "name": "default-rule-set"
    }]
"""

try:
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def list_rule_sets(client, module):
    try:
        response = client.list_receipt_rule_sets(aws_retry=True)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Couldn't list rule sets.")
    return response["RuleSets"]


def rule_set_in(name, rule_sets):
    return any(s for s in rule_sets if s["Name"] == name)


def ruleset_active(client, module, name):
    try:
        active_rule_set = client.describe_active_receipt_rule_set(aws_retry=True)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Couldn't get the active rule set.")
    if active_rule_set is not None and "Metadata" in active_rule_set:
        return name == active_rule_set["Metadata"]["Name"]
    else:
        # Metadata was not set meaning there is no active rule set
        return False


def deactivate_rule_set(client, module):
    try:
        # No ruleset name deactivates all rulesets
        client.set_active_receipt_rule_set(aws_retry=True)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Couldn't set active rule set to None.")


def update_active_rule_set(client, module, name, desired_active):
    check_mode = module.check_mode

    active = ruleset_active(client, module, name)

    changed = False
    if desired_active is not None:
        if desired_active and not active:
            if not check_mode:
                try:
                    client.set_active_receipt_rule_set(RuleSetName=name, aws_retry=True)
                except (BotoCoreError, ClientError) as e:
                    module.fail_json_aws(e, msg=f"Couldn't set active rule set to {name}.")
            changed = True
            active = True
        elif not desired_active and active:
            if not check_mode:
                deactivate_rule_set(client, module)
            changed = True
            active = False
    return changed, active


def create_or_update_rule_set(client, module):
    name = module.params.get("name")
    check_mode = module.check_mode
    changed = False

    rule_sets = list_rule_sets(client, module)
    if not rule_set_in(name, rule_sets):
        if not check_mode:
            try:
                client.create_receipt_rule_set(RuleSetName=name, aws_retry=True)
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg=f"Couldn't create rule set {name}.")
        changed = True
        rule_sets = list(rule_sets)
        rule_sets.append(
            {
                "Name": name,
            }
        )

    (active_changed, active) = update_active_rule_set(client, module, name, module.params.get("active"))
    changed |= active_changed

    module.exit_json(
        changed=changed,
        active=active,
        rule_sets=[camel_dict_to_snake_dict(x) for x in rule_sets],
    )


def remove_rule_set(client, module):
    name = module.params.get("name")
    check_mode = module.check_mode
    changed = False

    rule_sets = list_rule_sets(client, module)
    if rule_set_in(name, rule_sets):
        active = ruleset_active(client, module, name)
        if active and not module.params.get("force"):
            module.fail_json(
                msg=(
                    f"Couldn't delete rule set {name} because it is currently active. Set force=true to delete an"
                    " active ruleset."
                ),
                error={
                    "code": "CannotDelete",
                    "message": f"Cannot delete active rule set: {name}",
                },
            )
        if not check_mode:
            if active and module.params.get("force"):
                deactivate_rule_set(client, module)
            try:
                client.delete_receipt_rule_set(RuleSetName=name, aws_retry=True)
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg=f"Couldn't delete rule set {name}.")
        changed = True
        rule_sets = [x for x in rule_sets if x["Name"] != name]

    module.exit_json(
        changed=changed,
        rule_sets=[camel_dict_to_snake_dict(x) for x in rule_sets],
    )


def main():
    argument_spec = dict(
        name=dict(type="str", required=True),
        state=dict(type="str", default="present", choices=["present", "absent"]),
        active=dict(type="bool"),
        force=dict(type="bool", default=False),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    state = module.params.get("state")

    # SES APIs seem to have a much lower throttling threshold than most of the rest of the AWS APIs.
    # Docs say 1 call per second. This shouldn't actually be a big problem for normal usage, but
    # the ansible build runs multiple instances of the test in parallel that's caused throttling
    # failures so apply a jittered backoff to call SES calls.
    client = module.client("ses", retry_decorator=AWSRetry.jittered_backoff())

    if state == "absent":
        remove_rule_set(client, module)
    else:
        create_or_update_rule_set(client, module)


if __name__ == "__main__":
    main()
