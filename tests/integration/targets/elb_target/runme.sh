#!/usr/bin/env bash

set -eux

# Test graceful failure for older versions of botocore
source virtualenv.sh
pip install 'botocore<=1.7.1' boto3
ansible-playbook -i ../../inventory -v playbooks/version_fail.yml "$@"

# Run full test suite
source virtualenv.sh
pip install 'botocore' 'boto3>=1.16.57'
ansible-playbook -i ../../inventory -v playbooks/full_test.yml "$@"
