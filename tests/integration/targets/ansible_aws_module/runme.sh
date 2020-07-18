#!/usr/bin/env bash

set -eux

ANSIBLE_ROLES_PATH="../"
AWS_CONFIG_FILE="$( pwd )/boto3_config"
export ANSIBLE_ROLES_PATH
export AWS_CONFIG_FILE

ansible-playbook setup.yml -i localhost "$@"
ansible-playbook main.yml -i inventory "$@" -e "@session_credentials.yml"
