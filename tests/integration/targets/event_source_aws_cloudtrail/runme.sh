#!/usr/bin/env bash
#
# Beware: most of our tests here are run in parallel.
# To add new tests you'll need to add a new host to the inventory and a matching
# '{{ inventory_hostname }}'.yml file in roles/ec2_instance/tasks/


set -eux

export ANSIBLE_ROLES_PATH=../

CMD_ARGS=("$@")
# For ansible-rulebook --vars: pass only the var file path (e.g. after -e), not "-e $'@...'"
if [[ ${#CMD_ARGS[@]} -ge 2 && "${CMD_ARGS[0]}" == "-e" ]]; then
    VAR_FILE="${CMD_ARGS[1]}"
    # Strip $'@ prefix and trailing ' (e.g. $'@/path/to/file.json' -> /path/to/file.json)
    VAR_FILE="${VAR_FILE#@}"
fi

jq -s 'add' "${VAR_FILE}" vars.json > /tmp/vars.json

ansible-rulebook --inventory inventory --rulebook rulebooks/aws_manage_cloudtrail_ec2_keypair.yml --vars /tmp/vars.json &

# sleep 10 seconds for make sure ansible-rulebook had no errors
sleep 10

ansible-playbook ec2_keypair.yml -i inventory -e @/tmp/vars.json