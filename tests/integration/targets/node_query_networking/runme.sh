#!/usr/bin/env bash

set -eux

function cleanup() {
    ansible-playbook teardown.yml "$@"
    rm -f aws_vars.yml
    exit 1
}

rm -rf aws_vars.yml

trap 'cleanup "${@}"'  ERR

export ANSIBLE_ROLES_PATH=../

# Setup
ansible-playbook setup.yml "$@"

# Validate
ansible-playbook validate.yml -i inventory.ini "$@"

# clean resources
ansible-playbook teardown.yml "$@"
rm -f aws_vars.yml