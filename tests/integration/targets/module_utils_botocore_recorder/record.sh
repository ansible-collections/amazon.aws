#!/usr/bin/env bash
#
set -eux

if [ -d recording ]; then
    echo "Please check and remove the 'recording' directory."
    exit 1
fi
if [ -v ANSIBLE_TEST_PYTHON_VERSION ]; then
    echo "Please call ./runme.sh directly without ansible-test"
    exit 1
fi
export _ANSIBLE_PLACEBO_RECORD=recording

mkdir recording
ansible-playbook main.yml -vvv
account_id=$(aws sts get-caller-identity --query "Account" --output text)
user_id=$(aws sts get-caller-identity --query "UserId" --output text)
find recording -type f -exec sed -i "s,$account_id,123456789012,g" "{}" \;
find recording -type f -exec sed -i "s,$user_id,AIDA12345EXAMPLE54321,g" "{}" \;
find recording -type f -exec sed -i "s,$USER,george,g" "{}" \;
tar cfzv recording.tar.gz recording
rm -r recording
