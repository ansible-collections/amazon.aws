#!/usr/bin/env bash

set -eux

export ANSIBLE_ROLES_PATH=../
export AWS_CONFIG_FILE="$( pwd )/boto3_config"
#export AWS_SDK_LOAD_CONFIG=1

ansible-playbook setup.yml -i localhost "$@"
ansible-playbook main.yml -i inventory "$@"
