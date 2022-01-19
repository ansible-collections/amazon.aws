#!/usr/bin/env bash

set -eux

# ensure test config is empty
ansible-playbook playbooks/empty_inventory_config.yml "$@"

export ANSIBLE_INVENTORY_ENABLED="amazon.aws.aws_rds"

# test with default inventory file
ansible-playbook playbooks/test_invalid_aws_rds_inventory_config.yml "$@"

export ANSIBLE_INVENTORY=test.aws_rds.yml

# test empty inventory config
ansible-playbook playbooks/test_invalid_aws_rds_inventory_config.yml "$@"

# generate inventory config and test using it
ansible-playbook playbooks/create_inventory_config.yml "$@"
ansible-playbook playbooks/test_populating_inventory.yml "$@"

# generate inventory config with caching and test using it
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_cache.j2'" "$@"
ansible-playbook playbooks/populate_cache.yml "$@"
ansible-playbook playbooks/test_inventory_cache.yml "$@"

# remove inventory cache
rm -r aws_rds_cache_dir/

# generate inventory config with constructed features and test using it
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_constructed.j2'" "$@"
ansible-playbook playbooks/test_populating_inventory_with_constructed.yml "$@"

# generate inventory config with hostvars_prefix features and test using it
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_hostvars_prefix_suffix.j2'" -e "inventory_prefix='aws_rds_'" "$@"
ansible-playbook playbooks/test_inventory_with_hostvars_prefix_suffix.yml -e "inventory_prefix='aws_rds_'" "$@"

# generate inventory config with hostvars_suffix features and test using it
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_hostvars_prefix_suffix.j2'" -e "inventory_suffix='_aws_rds'" "$@"
ansible-playbook playbooks/test_inventory_with_hostvars_prefix_suffix.yml -e "inventory_suffix='_aws_rds'" "$@"

# generate inventory config with hostvars_prefix and hostvars_suffix features and test using it
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_hostvars_prefix_suffix.j2'" -e "inventory_prefix='aws_'" -e "inventory_suffix='_rds'" "$@"
ansible-playbook playbooks/test_inventory_with_hostvars_prefix_suffix.yml -e "inventory_prefix='aws_'" -e "inventory_suffix='_rds'" "$@"

# cleanup inventory config
ansible-playbook playbooks/empty_inventory_config.yml "$@"
