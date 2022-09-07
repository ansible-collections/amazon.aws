#!/usr/bin/env bash
#

set -eux

export ANSIBLE_ROLES_PATH=../


tar xfzv recording.tar.gz
export _ANSIBLE_PLACEBO_REPLAY=${PWD}/recording
export AWS_ACCESS_KEY_ID=disabled
export AWS_SECRET_ACCESS_KEY=disabled
export AWS_SESSION_TOKEN=disabled
export AWS_DEFAULT_REGION=us-east-2
ansible-playbook main.yml -vvv
