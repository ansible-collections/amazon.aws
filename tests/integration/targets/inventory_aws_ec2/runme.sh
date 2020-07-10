#!/usr/bin/env bash

set -eux

# ensure test config is empty
ansible-playbook playbooks/empty_inventory_config.yml "$@"

export ANSIBLE_INVENTORY_ENABLED="amazon.aws.aws_ec2"

# test with default inventory file
#ansible-playbook playbooks/test_invalid_aws_ec2_inventory_config.yml "$@"

export ANSIBLE_INVENTORY=test.aws_ec2.yml

# test empty inventory config
#ansible-playbook playbooks/test_invalid_aws_ec2_inventory_config.yml "$@"

# generate inventory config and test using it
#ansible-playbook playbooks/create_inventory_config.yml "$@"
#ansible-playbook playbooks/test_populating_inventory.yml "$@"

# generate inventory config with caching and test using it
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_cache.yml.j2'" "$@"
ansible-playbook playbooks/populate_cache.yml "$@"
ansible-playbook playbooks/test_inventory_cache.yml "$@"

# remove inventory cache
rm -r aws_ec2_cache_dir/

# generate inventory config with constructed features and test using it
#ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_constructed.yml.j2'" "$@"
#ansible-playbook playbooks/test_populating_inventory_with_constructed.yml "$@"

# cleanup inventory config
ansible-playbook playbooks/empty_inventory_config.yml "$@"
