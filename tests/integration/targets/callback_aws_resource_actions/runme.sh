#!/usr/bin/env bash

set -eux

export ANSIBLE_CALLBACK_WHITELIST="aws_resource_actions"

OUTFILE="callback_aws_resource_actions.out"
trap 'rm -rvf "${OUTFILE}" "${OUTFILE}.actions"' EXIT

# Tests that the resource_actions are added to each task
ansible-playbook main.yml -i localhost "$@" | tee "${OUTFILE}"

# There should be a summary at the end of the run with the actions performed:
# AWS ACTIONS: ['ec2:DescribeAvailabilityZones', 'ec2:DescribeInstances', 'iam:ListAccountAliases', 'sts:GetCallerIdentity']
grep -E "AWS ACTIONS: \[" "${OUTFILE}" > "${OUTFILE}.actions"
for action in 'ec2:DescribeAvailabilityZones' 'ec2:DescribeInstances' 'iam:ListAccountAliases' 'sts:GetCallerIdentity'
do
    grep "${action}" "${OUTFILE}.actions"
done
