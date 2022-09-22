#!/usr/bin/env bash
#
# Beware: most of our tests here are run in parallel.
# To add new tests you'll need to add a new host to the inventory and a matching
# '{{ inventory_hostname }}'.yml file in roles/ec2_instance/tasks/


set -eux

export ANSIBLE_ROLES_PATH=../
tiny_prefix="$(uuidgen -r|cut -d- -f1)"

# shellcheck disable=SC2016,SC2086
echo '
{
"ansible_test": {
    "environment": {
        "ANSIBLE_DEBUG_BOTOCORE_LOGS": "True"
    },
    "module_defaults": null
},
"resource_prefix": "'${tiny_prefix}'",
"tiny_prefix": "'${tiny_prefix}'",
"aws_region": "us-east-2"
}' > _config-file.json

ansible-playbook main.yml -i inventory "$@" -e @_config-file.json
