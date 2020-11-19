#!/usr/bin/env bash

set -eux
export ANSIBLE_HOST_KEY_CHECKING=False
export ANSIBLE_SSH_ARGS='-o UserKnownHostsFile=/dev/null'

# create test resources and inventory
ansible-playbook playbooks/setup.yml -c local "$@"

# test ec2_instance_metadata
ansible-playbook playbooks/test_initial_metadata.yml -i inventory "$@"

# teardown
ansible-playbook playbooks/teardown.yml -i inventory -c local "$@"
