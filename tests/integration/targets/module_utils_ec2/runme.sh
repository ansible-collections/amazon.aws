#!/usr/bin/env bash

set -eux

ANSIBLE_ROLES_PATH="../"
# Boto3
AWS_CONFIG_FILE="$( pwd )/boto3_config"
# Boto2
BOTO_CONFIG="$( pwd )/boto3_config"

export ANSIBLE_ROLES_PATH
export AWS_CONFIG_FILE
export BOTO_CONFIG

ansible-playbook setup.yml -i localhost "$@"
ansible-playbook main.yml -i inventory "$@" -e "@session_credentials.yml"
