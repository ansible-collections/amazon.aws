#!/usr/bin/env bash

set -eux

# ensure test config is empty
ansible-playbook -vvv main.yaml "$@"
