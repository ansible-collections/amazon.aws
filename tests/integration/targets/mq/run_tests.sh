#!/usr/bin/env bash
# to have debugging:  export DEGUG="-vv"
THIS_DIR=$(dirname $0)

export ANSIBLE_LIBRARY=${THIS_DIR}/../../../../plugins/
export ANSIBLE_MODULE_UTILS=${ANSIBLE_LIBRARY}/module_utils/

if [ -z "$MQ_BROKER_ID" ]; then
  echo "MQ_BROKER_ID must be set"
  exit 1
fi
if [ -z "$AWS_REGION" ]; then
  echo "AWS_REGION must be set"
  exit 1
fi
if [ -z "$AWS_ACCESS_KEY_ID" ]; then
  echo "AWS_ACCESS_KEY_ID must be set"
  exit 1
fi
if [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
  echo "AWS_SECRET_ACCESS_KEY must be set"
  exit 1
fi
if [ -z "$AWS_SESSION_TOKEN" ]; then
  echo "AWS_SESSION_TOKEN must be set"
  exit 1
fi

FAILED_PLAYBOOKS=0
TEST_PLAYBOOKS="test_mq_user.yml test_mq_user_info.yml test_mq_broker.yml test_mq_broker_config.yml"
for playbook in $TEST_PLAYBOOKS; do
  echo "Run test playbook $playbook"
  ansible-playbook -i inventory.ini tasks/$playbook $DEBUG
  RC=$?
  if [ $RC != 0 ]; then
    echo "test playbook $playbook failed"
    FAILED_PLAYBOOKS=$(( $FAILED_PLAYBOOKS + 1 ))
  fi
done

if [ $FAILED_PLAYBOOKS -gt 0 ]; then
  echo "$FAILED_PLAYBOOKS test playbooks failed"
  exit 1
fi
