#!/usr/bin/env bash

set -eux

ANSIBLE_ROLES_PATH="../"
export ANSIBLE_ROLES_PATH

ansible-playbook main.yml -i inventory "$@"
