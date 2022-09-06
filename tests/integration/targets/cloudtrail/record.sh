#!/usr/bin/env bash
#
set -eux

export ANSIBLE_ROLES_PATH=../


if [ -d recording ]; then
    echo "Please check and remove the 'recording' directory."
    exit 1
fi
if [ -v ANSIBLE_TEST_PYTHON_VERSION ]; then
    echo "Please call ./runme.sh directly without ansible-test"
    exit 1
fi
export _ANSIBLE_PLACEBO_RECORD=recording

tiny_prefix=$(uuidgen -r|cut -d- -f1)

# shellcheck disable=SC2016,SC2086
echo '
{
"ansible_test": {
    "environment": {
        "ANSIBLE_DEBUG_BOTOCORE_LOGS": "True"
    },
    "module_defaults": null
},
"resource_prefix": "cloudtrail-'${tiny_prefix}'",
"tiny_prefix": "'${tiny_prefix}'",
"aws_region": "us-east-2"
}' > _config-file.json

mkdir recording
ansible-playbook main.yml -e @_config-file.json -vvv
account_id=$(aws sts get-caller-identity --query "Account" --output text)
user_id=$(aws sts get-caller-identity --query "UserId" --output text)
find recording -type f -exec sed -i "s,$account_id,1111111111111,g" "{}" \;
find recording -type f -exec sed -i "s,$user_id,AWZBREIZHEOMABRONIFVGFS6GH,g" "{}" \;
find recording -type f -exec sed -i "s,$USER,george,g" "{}" \;
tar cfzv recording.tar.gz recording
rm -r recording
