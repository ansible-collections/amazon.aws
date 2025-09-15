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
module: organization_account
version_added: 7.0.0
short_description: Creates AWS accounts within an Organization
description:
  - Module to create AWS accounts in an Organization.
  - This module supports creating new AWS accounts with optional custom IAM role names and tags.
  - If ou_id is specified, the account will be automatically moved to the specified OU after creation.
  - This module is idempotent - if an account with the same email already exists, it will use the existing account, apply any specified tags, and move it to the specified OU if needed.
options:
    state:
        description: 
          - Whether the account should exist or not.
        required: true
        type: str
        choices: ['present', 'absent']
    email:
        description:
          - Email for the account to be created.
        required: true
        type: str
    name:
        description:
          - Name of the account to be created.
        required: true
        type: str
    admin_role_name:
        description:
          - Name of the IAM role to be created by default in the new account (e.g., 'OrganizationAccountAccessRole').
        required: false
        type: str
    tags:
        description:
          - A list of tags (key/value) to apply to the new account.
        required: false
        type: list
        elements: dict
    ou_id:
        description:
          - ID of the destination OU. If specified, the account will be moved to this OU after creation.
        required: false
        type: str
    aws_access_key:
        description:
          - AWS access key ID. If not set then the value of the AWS_ACCESS_KEY_ID, AWS_ACCESS_KEY, or EC2_ACCESS_KEY environment variable is used.
        required: false
        type: str
        aliases: ['ec2_access_key', 'access_key']
    aws_secret_key:
        description:
          - AWS secret access key. If not set then the value of the AWS_SECRET_ACCESS_KEY, AWS_SECRET_KEY, or EC2_SECRET_KEY environment variable is used.
        required: false
        type: str
        aliases: ['ec2_secret_key', 'secret_key']
    aws_security_token:
        description:
          - AWS STS security token. If not set then the value of the AWS_SECURITY_TOKEN or EC2_SECURITY_TOKEN environment variable is used.
        required: false
        type: str
        aliases: ['access_token']
    region:
        description:
          - The AWS region to use. If not specified then the value of the AWS_REGION or EC2_REGION environment variable, if any, is used.
        required: false
        type: str
        aliases: ['aws_region', 'ec2_region']
    profile:
        description:
          - Uses a boto profile. Only works with boto >= 2.24.0.
        required: false
        type: str
    validate_certs:
        description:
          - When set to "no", SSL certificates will not be validated for boto versions >= 2.6.0.
        required: false
        type: bool
        default: true
author:
    - Lauro Gomes (@laurobmb)
'''

EXAMPLES = r'''

- name: Create new AWS account (simple)
  community.aws.organization_account:
    state: present
    email: "admin@company.com"
    name: "DemoProject"
  register: create_account_result

- name: Create new AWS account with custom Role and Tags
  community.aws.organization_account:
    state: present
    email: "admin@company.com"
    name: "DemoProjectWithTags"
    admin_role_name: "CustomOrganizationRole"
    tags:
      - Key: Environment
        Value: Production
      - Key: BilledTo
        Value: "Dept-123"
  register: create_account_custom_result

- name: Create new AWS account and move to specific OU
  community.aws.organization_account:
    state: present
    email: "admin@company.com"
    name: "DemoProjectInOU"
    ou_id: "ou-jojo-zeg98nd3"
  register: create_and_move_result
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
    description: Detailed status of the account creation
    type: dict
    returned: when state is present
    contains:
        AccountId:
            description: The ID of the created account
            type: str
            sample: "123456789012"
        State:
            description: The state of the account creation
            type: str
            sample: "SUCCEEDED"
move_result:
    description: Result of moving the account to the specified OU (if ou_id was provided)
    type: dict
    returned: when ou_id is provided
    contains:
        changed:
            description: Whether the account was moved
            type: bool
        msg:
            description: Message about the move operation
            type: str
        current_parent:
            description: Current parent ID of the account
            type: str
tag_result:
    description: Result of applying tags to the account (if tags were provided)
    type: dict
    returned: when tags are provided
    contains:
        changed:
            description: Whether tags were applied or updated
            type: bool
        msg:
            description: Message about the tag operation
            type: str
        tags_applied:
            description: List of tags that were applied
            type: list
        tags_removed:
            description: List of tags that were removed
            type: list
'''


@AWSRetry.jittered_backoff()
def get_current_parent_id(client, id):
    """Get the current Parent ID (Root or OU) of an account."""
    parents = client.list_parents(ChildId=id)
    return parents['Parents'][0]['Id']


@AWSRetry.jittered_backoff()
def find_account_by_email(client, email):
    """Find an account by email address."""
    try:
        paginator = client.get_paginator('list_accounts')
        for page in paginator.paginate():
            for account in page['Accounts']:
                if account['Email'] == email:
                    return account
        return None
    except ClientError as e:
        return None


@AWSRetry.jittered_backoff()
def get_account_tags(client, account_id):
    """Get current tags for an account."""
    try:
        response = client.list_tags_for_resource(ResourceId=account_id)
        return response.get('Tags', [])
    except ClientError as e:
        return []


@AWSRetry.jittered_backoff()
def apply_tags_to_account(client, account_id, tags):
    """Apply tags to an account."""
    if not tags:
        return dict(changed=False, msg="No tags to apply")
    
    try:
        current_tags = get_account_tags(client, account_id)
        current_tag_dict = {tag['Key']: tag['Value'] for tag in current_tags}
        
        desired_tag_dict = {}
        for tag in tags:
            if isinstance(tag, dict) and 'Key' in tag and 'Value' in tag:
                desired_tag_dict[tag['Key']] = tag['Value']
        
        tags_to_add = []
        tags_to_remove = []
        
        for key, value in desired_tag_dict.items():
            if key not in current_tag_dict or current_tag_dict[key] != value:
                tags_to_add.append({'Key': key, 'Value': value})
        
        for key in current_tag_dict:
            if key not in desired_tag_dict:
                tags_to_remove.append({'Key': key})
        
        changed = False
        messages = []
        
        if tags_to_add:
            client.tag_resource(ResourceId=account_id, Tags=tags_to_add)
            changed = True
            messages.append(f"Applied {len(tags_to_add)} tags")
        
        if tags_to_remove:
            client.untag_resource(ResourceId=account_id, TagKeys=[tag['Key'] for tag in tags_to_remove])
            changed = True
            messages.append(f"Removed {len(tags_to_remove)} tags")
        
        if changed:
            return dict(
                changed=True,
                msg="; ".join(messages),
                tags_applied=tags_to_add,
                tags_removed=tags_to_remove
            )
        else:
            return dict(
                changed=False,
                msg="Account tags are already up to date"
            )
            
    except ClientError as e:
        return dict(
            failed=True,
            msg=f"Error applying tags: {e.response['Error']['Message']}"
        )


@AWSRetry.jittered_backoff()
def move_account(client, id, ou_id):
    """Move an account to a new OU."""
    try:
        source_parent_id = get_current_parent_id(client, id)

        if source_parent_id == ou_id:
            return dict(
                changed=False,
                msg=f"Account {id} is already in the destination OU {ou_id}."
            )

        response = client.move_account(
            AccountId=id,
            SourceParentId=source_parent_id,
            DestinationParentId=ou_id
        )
        return dict(
            changed=True,
            msg=f"Account {id} moved from {source_parent_id} to {ou_id}.",
            response=response
        )
    except ClientError as e:
        return dict(
            failed=True,
            msg=f"Error moving account: {e.response['Error']['Message']}"
        )


@AWSRetry.jittered_backoff()
def create_account(client, email, name, admin_role_name=None, tags=None):
    """
    Create a new account in AWS Organization with optional RoleName and Tags,
    and wait for its completion. If account already exists, return existing account info.
    """
    try:
        existing_account = find_account_by_email(client, email)
        if existing_account:
            return dict(
                changed=False,
                msg=f"Account {existing_account['Id']} already exists for email {email}.",
                status={
                    'AccountId': existing_account['Id'],
                    'State': 'EXISTING',
                    'Email': existing_account['Email'],
                    'Name': existing_account['Name']
                }
            )

        params = {
            'Email': email,
            'AccountName': name,
            'IamUserAccessToBilling': 'ALLOW'
        }
        if admin_role_name:
            params['RoleName'] = admin_role_name
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
                    msg=f"Account {status['AccountId']} created successfully for the project {name}.",
                    status=status
                )

            if state == 'FAILED':
                failure_reason = status.get('FailureReason', '')
                if 'EMAIL_ALREADY_EXISTS' in failure_reason:
                    existing_account = find_account_by_email(client, email)
                    if existing_account:
                        return dict(
                            changed=False,
                            msg=f"Account {existing_account['Id']} already exists for email {email}.",
                            status={
                                'AccountId': existing_account['Id'],
                                'State': 'EXISTING',
                                'Email': existing_account['Email'],
                                'Name': existing_account['Name']
                            }
                        )
                
                return dict(
                    failed=True,
                    msg=f"Account creation failed. Reason: {failure_reason}"
                )

            time.sleep(15)

    except ClientError as e:
        error_message = e.response['Error']['Message']
        if 'EMAIL_ALREADY_EXISTS' in error_message:
            existing_account = find_account_by_email(client, email)
            if existing_account:
                return dict(
                    changed=False,
                    msg=f"Account {existing_account['Id']} already exists for email {email}.",
                    status={
                        'AccountId': existing_account['Id'],
                        'State': 'EXISTING',
                        'Email': existing_account['Email'],
                        'Name': existing_account['Name']
                    }
                )
        
        return dict(
            failed=True,
            msg=f"AWS API error when creating account: {error_message}"
        )


def run_module():
    module_args = dict(
        state=dict(type='str', required=True, choices=['present', 'absent']),
        email=dict(type='str', required=True),
        name=dict(type='str', required=True),
        admin_role_name=dict(type='str', required=False),
        tags=dict(type='list', elements='dict', required=False),
        ou_id=dict(type='str', required=False),
        aws_access_key=dict(type='str', required=False, aliases=['ec2_access_key', 'access_key']),
        aws_secret_key=dict(type='str', required=False, aliases=['ec2_secret_key', 'secret_key'], no_log=True),
        aws_security_token=dict(type='str', required=False, aliases=['access_token'], no_log=True),
        region=dict(type='str', required=False, aliases=['aws_region', 'ec2_region']),
        profile=dict(type='str', required=False),
        validate_certs=dict(type='bool', required=False, default=True),
    )

    module = AnsibleAWSModule(
        argument_spec=module_args,
        supports_check_mode=False,
    )

    state = module.params['state']
    result = {}

    try:
        client = module.client('organizations')
    except Exception as e:
        module.fail_json(msg=f"Failed to initialize boto3 client: {str(e)}")

    if state == 'present':
        result = create_account(
            client=client,
            email=module.params['email'],
            name=module.params['name'],
            admin_role_name=module.params['admin_role_name'],
            tags=module.params['tags']
        )
        
        if not result.get("failed"):
            account_id = result.get('status', {}).get('AccountId')
            if account_id:
                if module.params.get('tags'):
                    tag_result = apply_tags_to_account(client, account_id, module.params['tags'])
                    result['tag_result'] = tag_result
                    if tag_result.get('changed'):
                        result['changed'] = True
                        result['msg'] += f" {tag_result['msg']}"
                
                if module.params.get('ou_id'):
                    move_result = move_account(client, account_id, module.params['ou_id'])
                    result['move_result'] = move_result
                    if move_result.get('changed'):
                        result['changed'] = True
                        result['msg'] += f" {move_result['msg']}"
                    else:
                        if result.get('status', {}).get('State') == 'EXISTING':
                            result['msg'] += f" Account is already in the correct OU."
            else:
                result['move_result'] = {
                    'changed': False,
                    'msg': 'Could not move account: Account ID not available'
                }
                
    elif state == 'absent':
        result = dict(
            changed=False,
            msg="Account deletion is not supported by AWS Organizations API. Accounts must be closed through AWS Support."
        )

    if result.get("failed"):
        module.fail_json(**result)
    else:
        module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
