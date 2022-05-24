#!/usr/bin/env bash

set -eux

# ensure test config is empty
ansible-playbook playbooks/empty_inventory_config.yml "$@"

export ANSIBLE_INVENTORY_ENABLED="amazon.aws.aws_ec2"

# test with default inventory file
ansible-playbook playbooks/test_invalid_aws_ec2_inventory_config.yml "$@"

export ANSIBLE_INVENTORY=test.aws_ec2.yml

# test empty inventory config
ansible-playbook playbooks/test_invalid_aws_ec2_inventory_config.yml "$@"

# generate inventory config and test using it
ansible-playbook playbooks/create_inventory_config.yml "$@"
ansible-playbook playbooks/test_populating_inventory.yml "$@"

# generate inventory with access_key provided through a templated variable
ansible-playbook playbooks/create_environment_script.yml "$@"
source access_key.sh
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_template.yml.j2'" "$@"
ansible-playbook playbooks/test_populating_inventory.yml "$@"

# generate inventory config with caching and test using it
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_cache.yml.j2'" "$@"
ansible-playbook playbooks/populate_cache.yml "$@"
ansible-playbook playbooks/test_inventory_cache.yml "$@"

# remove inventory cache
rm -r aws_ec2_cache_dir/

# generate inventory config with constructed features and test using it
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_constructed.yml.j2'" "$@"
ansible-playbook playbooks/test_populating_inventory_with_constructed.yml "$@"
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_concatenation.yml.j2'" "$@"
ansible-playbook playbooks/test_populating_inventory_with_concatenation.yml "$@"
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_literal_string.yml.j2'" "$@"
ansible-playbook playbooks/test_populating_inventory_with_literal_string.yml "$@"

# generate inventory config with includes_entries_matching and prepare the tests
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_include_or_exclude_filters.yml.j2'" "$@"
ansible-playbook playbooks/test_populating_inventory_with_include_or_exclude_filters.yml "$@"

# generate inventory config with hostvars_prefix
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_hostvars_prefix_suffix.yml.j2'" -e "hostvars_prefix='aws_ec2_'" "$@"
ansible-playbook playbooks/test_populating_inventory_with_hostvars_prefix_suffix.yml -e "hostvars_prefix='aws_ec2_'" "$@"
# generate inventory config with hostvars_suffix
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_hostvars_prefix_suffix.yml.j2'" -e "hostvars_suffix='_aws_ec2'" "$@"
ansible-playbook playbooks/test_populating_inventory_with_hostvars_prefix_suffix.yml -e "hostvars_suffix='_aws_ec2'" "$@"
# generate inventory config with hostvars_prefix and hostvars_suffix
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_hostvars_prefix_suffix.yml.j2'" -e "hostvars_prefix='aws_'" -e "hostvars_suffix='_ec2'" "$@"
ansible-playbook playbooks/test_populating_inventory_with_hostvars_prefix_suffix.yml -e "hostvars_prefix='aws_'" -e "hostvars_suffix='_ec2'" "$@"

# generate inventory config with caching and test using it
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_use_contrib_script_keys.yml.j2'" "$@"
ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS=never ansible-playbook playbooks/test_populating_inventory_with_use_contrib_script_keys.yml "$@"

# cleanup inventory config
ansible-playbook playbooks/empty_inventory_config.yml "$@"
