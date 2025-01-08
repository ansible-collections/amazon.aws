#!/usr/bin/env bash

set -eux
export ANSIBLE_HOST_KEY_CHECKING=False
export ANSIBLE_SSH_ARGS='-o UserKnownHostsFile=/dev/null'

CMD_ARGS=("$@")

ln -s "$(pwd)/../" playbooks/roles
ln -s ../templates playbooks/templates

# Destroy Environment
cleanup() {
    ansible-playbook playbooks/teardown.yml -i inventory -c local "${CMD_ARGS[@]}"
}
trap "cleanup" EXIT

# create test resources and inventory
ansible-playbook playbooks/setup.yml -c local "$@"

# test ec2_instance_metadata
ansible-playbook playbooks/test_metadata.yml -i inventory \
    -e local_tmp=/tmp/ansible-local \
    -e remote_tmp=/tmp/ansible-remote \
    "$@"
