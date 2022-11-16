#!/usr/bin/env bash

set -eux

function cleanup() {
    ansible-playbook playbooks/setup_instance.yml -e "operation=delete" "$@"
    exit 1
}

trap 'cleanup "${@}"'  ERR

# ensure test config is empty
ansible-playbook playbooks/empty_inventory_config.yml "$@"

export ANSIBLE_INVENTORY_ENABLED="amazon.aws.aws_rds"

# test with default inventory file
ansible-playbook playbooks/test_invalid_aws_rds_inventory_config.yml "$@"

export ANSIBLE_INVENTORY=test.aws_rds.yml

# test empty inventory config
ansible-playbook playbooks/test_invalid_aws_rds_inventory_config.yml "$@"

# delete existing resources
ansible-playbook playbooks/setup_instance.yml -e "operation=delete" -e "aws_api_wait=true" "$@"

# generate inventory config and test using it
ansible-playbook playbooks/create_inventory_config.yml "$@" &&

# test inventory with no hosts
ansible-playbook playbooks/test_inventory_no_hosts.yml "$@" &&

# create RDS resources
ansible-playbook playbooks/setup_instance.yml -e "operation=create" "$@" &&

# test inventory populated with RDS instance
ansible-playbook playbooks/test_populating_inventory.yml "$@" &&

# generate inventory config with constructed features and test using it
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_constructed.j2'" "$@" &&
ansible-playbook playbooks/test_populating_inventory_with_constructed.yml "$@" &&

# generate inventory config with hostvars_prefix features and test using it
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_hostvars_prefix_suffix.j2'" -e "inventory_prefix='aws_rds_'" "$@" &&
ansible-playbook playbooks/test_inventory_with_hostvars_prefix_suffix.yml -e "inventory_prefix='aws_rds_'" "$@" &&

# generate inventory config with hostvars_suffix features and test using it
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_hostvars_prefix_suffix.j2'" -e "inventory_suffix='_aws_rds'" "$@" &&
ansible-playbook playbooks/test_inventory_with_hostvars_prefix_suffix.yml -e "inventory_suffix='_aws_rds'" "$@" &&

# generate inventory config with hostvars_prefix and hostvars_suffix features and test using it
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_hostvars_prefix_suffix.j2'" -e "inventory_prefix='aws_'" -e "inventory_suffix='_rds'" "$@" &&
ansible-playbook playbooks/test_inventory_with_hostvars_prefix_suffix.yml -e "inventory_prefix='aws_'" -e "inventory_suffix='_rds'" "$@" &&

# generate inventory config with statuses and test using it
ansible-playbook playbooks/create_inventory_config.yml -e '{"inventory_statuses": true}' "$@" &&
ansible-playbook playbooks/test_inventory_no_hosts.yml "$@" &&

# generate inventory config with caching and test using it
AWS_RDS_CACHE_DIR="aws_rds_cache_dir"
rm -rf "${AWS_RDS_CACHE_DIR}"  &&
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_cache.j2'" -e "aws_inventory_cache_dir=$AWS_RDS_CACHE_DIR" "$@" &&
ansible-playbook playbooks/populate_cache.yml "$@" &&
ansible-playbook playbooks/test_inventory_cache.yml "$@" &&
rm -rf "${AWS_RDS_CACHE_DIR}" &&

# cleanup inventory config
ansible-playbook playbooks/empty_inventory_config.yml "$@"

ansible-playbook playbooks/setup_instance.yml -e "operation=delete" "$@"
