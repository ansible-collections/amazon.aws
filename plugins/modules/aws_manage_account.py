#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
import time

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass


DOCUMENTATION = r'''
---
module: aws_manage_account
version_added: 7.0.0
short_description: Creates or moves AWS accounts within an Organization
description:
  - Module to create AWS accounts in an Organization and move existing accounts to Organizational Units (OUs).
  - This module supports creating new AWS accounts with optional custom IAM role names and tags.
  - It also supports moving existing accounts between Organizational Units.
options:
    action:
        description:
          - Action to be performed: create or move an account.
        required: true
        type: str
        choices: ['create_account', 'move_account']
    email:
        description:
          - Email for the account to be created. Required for create_account.
        required: false
        type: str
    account_name:
        description:
          - Name of the account to be created. Required for create_account.
        required: false
        type: str
    role_name:
        description:
          - Name of the IAM role to be created by default in the new account (e.g., 'OrganizationAccountAccessRole').
        required: false
        type: str
    account_tags:
        description:
          - A list of tags (key/value) to apply to the new account.
        required: false
        type: list
        elements: dict
    account_id:
        description:
          - ID of the account to be moved. Required for move_account.
        required: false
        type: str
    destination_ou_id:
        description:
          - ID of the destination OU. Required for move_account.
        required: false
        type: str
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
author:
    - Lauro Gomes (@laurobmb)
'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create new AWS account (simple)
  amazon.aws.aws_manage_account:
    action: create_account
    email: "admin@company.com"
    account_name: "DemoProject"
  register: create_account_result

- name: Create new AWS account with custom Role and Tags
  amazon.aws.aws_manage_account:
    action: create_account
    email: "admin@company.com"
    account_name: "DemoProjectWithTags"
    role_name: "CustomOrganizationRole"
    account_tags:
      - Key: Environment
        Value: Production
      - Key: BilledTo
        Value: "Dept-123"
  register: create_account_custom_result

- name: Move the newly created account to the destination OU
  amazon.aws.aws_manage_account:
    action: move_account
    account_id: "{{ create_account_result.status.AccountId }}"
    destination_ou_id: "ou-jojo-zeg98nd3"
  when: create_account_result.changed
'''

RETURN = r'''
msg:
    description: Summary message of the action performed
    type: str
    returned: always
    sample: "Account 123456789012 created successfully for the project DemoProject."
changed:
    description: Indicates if a change was made to the environment
    type: bool
    returned: always
status:
    description: Detailed status of the account creation (only for create_account)
    type: dict
    returned: when action is create_account
    contains:
        AccountId:
            description: The ID of the created account
            type: str
            sample: "123456789012"
        State:
            description: The state of the account creation
            type: str
            sample: "SUCCEEDED"
response:
    description: Response from the AWS API (only for move_account)
    type: dict
    returned: when action is move_account
'''


@AWSRetry.jittered_backoff()
def get_current_parent_id(client, account_id):
    """Get the current Parent ID (Root or OU) of an account."""
    parents = client.list_parents(ChildId=account_id)
    return parents['Parents'][0]['Id']


@AWSRetry.jittered_backoff()
def move_account(client, account_id, destination_ou_id):
    """Move an account to a new OU."""
    try:
        source_parent_id = get_current_parent_id(client, account_id)

        if source_parent_id == destination_ou_id:
            return dict(
                changed=False,
                msg=f"Account {account_id} is already in the destination OU {destination_ou_id}."
            )

        response = client.move_account(
            AccountId=account_id,
            SourceParentId=source_parent_id,
            DestinationParentId=destination_ou_id
        )
        return dict(
            changed=True,
            msg=f"Account {account_id} moved from {source_parent_id} to {destination_ou_id}.",
            response=response
        )
    except ClientError as e:
        return dict(
            failed=True,
            msg=f"Error moving account: {e.response['Error']['Message']}"
        )


@AWSRetry.jittered_backoff()
def create_account(client, email, account_name, role_name=None, tags=None):
    """
    Create a new account in AWS Organization with optional RoleName and Tags,
    and wait for its completion.
    """
    try:
        params = {
            'Email': email,
            'AccountName': account_name,
            'IamUserAccessToBilling': 'ALLOW'
        }
        if role_name:
            params['RoleName'] = role_name
        if tags:
            params['Tags'] = tags

        response = client.create_account(**params)
        request_id = response['CreateAccountStatus']['Id']

        while True:
            status_response = client.describe_create_account_status(
                CreateAccountRequestId=request_id
            )
            status = status_response['CreateAccountStatus']
            state = status['State']

            if state == 'SUCCEEDED':
                return dict(
                    changed=True,
                    msg=f"Account {status['AccountId']} created successfully for the project {account_name}.",
                    status=status
                )

            if state == 'FAILED':
                return dict(
                    failed=True,
                    msg=f"Account creation failed. Reason: {status.get('FailureReason', 'Not specified')}"
                )

            time.sleep(15)

    except ClientError as e:
        return dict(
            failed=True,
            msg=f"AWS API error when creating account: {e.response['Error']['Message']}"
        )


def run_module():
    module_args = dict(
        action=dict(type='str', required=True, choices=['create_account', 'move_account']),
        email=dict(type='str', required=False),
        account_name=dict(type='str', required=False),
        role_name=dict(type='str', required=False),
        account_tags=dict(type='list', elements='dict', required=False),
        account_id=dict(type='str', required=False),
        destination_ou_id=dict(type='str', required=False),
    )

    module = AnsibleAWSModule(
        argument_spec=module_args,
        supports_check_mode=False,
        required_if=[
            ('action', 'create_account', ['email', 'account_name']),
            ('action', 'move_account', ['account_id', 'destination_ou_id']),
        ]
    )

    action = module.params['action']
    result = {}

    try:
        client = module.client('organizations')
    except Exception as e:
        module.fail_json(msg=f"Failed to initialize boto3 client: {str(e)}")

    if action == 'create_account':
        result = create_account(
            client=client,
            email=module.params['email'],
            account_name=module.params['account_name'],
            role_name=module.params['role_name'],
            tags=module.params['account_tags']
        )

    elif action == 'move_account':
        result = move_account(client, module.params['account_id'], module.params['destination_ou_id'])

    if result.get("failed"):
        module.fail_json(**result)
    else:
        module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
