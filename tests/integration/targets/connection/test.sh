#!/usr/bin/env bash

set -eux

[ -f "${INVENTORY}" ]

ansible-playbook test_connection.yml -i "${INVENTORY}" "$@"

# Ansible 2.14 dropped support for non UTF-8 Locale
# https://github.com/ansible/ansible/pull/78175
# LC_ALL=C LANG=C ansible-playbook test_connection.yml -i "${INVENTORY}" "$@"
