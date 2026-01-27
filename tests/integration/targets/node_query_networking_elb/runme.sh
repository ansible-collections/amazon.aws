#!/usr/bin/env bash

export ANSIBLE_ROLES_PATH=../

ansible-playbook play.yaml "$@"

