#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import boto3
import time
from botocore.exceptions import ClientError


DOCUMENTATION = r'''
---
module: aws_organizations_account
short_description: Creates or moves AWS accounts within an Organization
version_added: "1.0"
description:
  - "Module to create AWS accounts in an Organization and move existing accounts to Organizational Units (OUs)."
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
author:
    - Lauro Gomes (@laurobmb)
'''

EXAMPLES = r'''
- name: Create new AWS account (simple)
  laurobmb.aws.aws_organizations_account:
    action: create_account
    email: "laurobmb+demo@hotmail.com"
    account_name: "DemoProject"
  register: create_account_result

- name: Create new AWS account with custom Role and Tags
  laurobmb.aws.aws_organizations_account:
    action: create_account
    email: "laurobmb+demotags@hotmail.com"
    account_name: "DemoProjectWithTags"
    role_name: "CustomOrganizationRole"
    account_tags:
      - Key: Environment
        Value: Production
      - Key: BilledTo
        Value: "Dept-123"
  register: create_account_custom_result

- name: Move the newly created account to the destination OU
  laurobmb.aws.aws_organizations_account:
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
changed:
    description: Indicates if a change was made to the environment
    type: bool
    returned: always
status:
    description: Detailed status of the account creation (only for create_account)
    type: dict
    returned: when action is create_account
response:
    description: Response from the AWS API (only for move_account)
    type: dict
    returned: when action is move_account
'''


def get_current_parent_id(client, account_id):
    """Descobre o Parent ID (Root ou OU) atual de uma conta."""
    parents = client.list_parents(ChildId=account_id)
    return parents['Parents'][0]['Id']


def move_account(client, account_id, destination_ou_id):
    """Move uma conta para uma nova OU."""
    try:
        source_parent_id = get_current_parent_id(client, account_id)
        
        if source_parent_id == destination_ou_id:
            return dict(
                changed=False,
                msg=f"Conta {account_id} já está na OU de destino {destination_ou_id}."
            )

        response = client.move_account(
            AccountId=account_id,
            SourceParentId=source_parent_id,
            DestinationParentId=destination_ou_id
        )
        return dict(
            changed=True,
            msg=f"Conta {account_id} movida de {source_parent_id} para {destination_ou_id}.",
            response=response
        )
    except ClientError as e:
        return dict(
            failed=True,
            msg=f"Erro ao mover conta: {e.response['Error']['Message']}"
        )


def create_account(client, email, projeto, role_name=None, tags=None):
    """
    Cria uma nova conta na AWS Organization, com suporte opcional para RoleName e Tags,
    e aguarda sua conclusão.
    """
    try:
        params = {
            'Email': email,
            'AccountName': projeto,
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
                    msg=f"Conta {status['AccountId']} criada com sucesso para o projeto {projeto}.",
                    status=status
                )

            if state == 'FAILED':
                return dict(
                    failed=True,
                    msg=f"Criação da conta falhou. Motivo: {status.get('FailureReason', 'Não especificado')}"
                )
            
            time.sleep(15)

    except ClientError as e:
        return dict(
            failed=True,
            msg=f"Erro de API da AWS ao criar conta: {e.response['Error']['Message']}"
        )


def run_module():
    # 🔧 1. DEFINIÇÃO DE PARÂMETROS ATUALIZADA
    module_args = dict(
        action=dict(type='str', required=True, choices=['create_account', 'move_account']),
        email=dict(type='str', required=False),
        projeto=dict(type='str', required=False),
        role_name=dict(type='str', required=False),
        account_tags=dict(type='list', elements='dict', required=False), # Nome amigável para o playbook
        account_id=dict(type='str', required=False),
        destination_ou_id=dict(type='str', required=False),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    action = module.params['action']
    result = {}

    try:
        client = boto3.client('organizations')
    except Exception as e:
        module.fail_json(msg=f"Falha ao iniciar cliente boto3: {str(e)}")

    if action == 'create_account':
        if not module.params['email'] or not module.params['projeto']:
            module.fail_json(msg="Parâmetros 'email' e 'projeto' são obrigatórios para create_account.")
        
        # 🚀 2. PASSANDO OS NOVOS PARÂMETROS PARA A FUNÇÃO
        result = create_account(
            client=client,
            email=module.params['email'],
            projeto=module.params['projeto'],
            role_name=module.params['role_name'],
            tags=module.params['account_tags'] # Passando 'account_tags' para o parâmetro 'tags' da função
        )

    elif action == 'move_account':
        if not module.params['account_id'] or not module.params['destination_ou_id']:
            module.fail_json(msg="Parâmetros 'account_id' e 'destination_ou_id' são obrigatórios para move_account.")
        result = move_account(client, module.params['account_id'], module.params['destination_ou_id'])

    if result.get("failed"):
        module.fail_json(**result)
    else:
        module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()