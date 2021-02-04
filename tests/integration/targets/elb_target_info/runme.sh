#!/usr/bin/env bash

set -eux

# Run full test suite
source virtualenv.sh
pip install 'botocore' 'boto3>=1.16.57'
ansible-playbook -i ../../inventory -v playbooks/full_test.yml "$@"
