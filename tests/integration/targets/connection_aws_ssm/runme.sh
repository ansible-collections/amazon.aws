#!/usr/bin/env bash

set -eux

CMD_ARGS=("$@")

# Destroy Environment
cleanup() {

    cd ../connection_aws_ssm

    ansible-playbook -c local aws_ssm_integration_test_teardown.yml "${CMD_ARGS[@]}"

}

trap "cleanup" EXIT

# Setup Environment
ansible-playbook -c local aws_ssm_integration_test_setup.yml "$@"

# Export the AWS Keys
set +x
. ./aws-env-vars.sh
set -x

cd ../connection

# Execute Integration tests
INVENTORY=../connection_aws_ssm/ssm_inventory ./test.sh \
    -e target_hosts=aws_ssm \
    "$@"
