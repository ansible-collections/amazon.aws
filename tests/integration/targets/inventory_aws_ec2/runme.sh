#!/usr/bin/env bash

# generate inventory with access_key provided through a templated variable
ansible-playbook playbooks/create_environment_script.yml "$@"
source access_key.sh

set -eux

function cleanup() {
    set +x
    source access_key.sh
    set -x
    ansible-playbook playbooks/manage_ec2_instances.yml -e "task=tear_down" "$@"
    exit 1
}

trap 'cleanup "${@}"'  ERR

# ensure test config is empty
ansible-playbook playbooks/empty_inventory_config.yml "$@"

export ANSIBLE_INVENTORY_ENABLED="amazon.aws.aws_ec2"

# test with default inventory file
ansible-playbook playbooks/test_invalid_aws_ec2_inventory_config.yml "$@"

export ANSIBLE_INVENTORY=test.aws_ec2.yml

# test empty inventory config
ansible-playbook playbooks/test_invalid_aws_ec2_inventory_config.yml "$@"

# create minimal config for tests
ansible-playbook playbooks/manage_ec2_instances.yml -e "task=setup" "$@"

# generate inventory config and test using it
ansible-playbook playbooks/create_inventory_config.yml "$@"
ansible-playbook playbooks/test_populating_inventory.yml "$@"

ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_template.yml.j2'" "$@"
ansible-playbook playbooks/test_populating_inventory.yml "$@"

# generate inventory config with constructed features and test using it
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_constructed.yml.j2'" "$@"
ansible-playbook playbooks/test_populating_inventory_with_constructed.yml "$@"
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_concatenation.yml.j2'" "$@"
ansible-playbook playbooks/test_populating_inventory_with_concatenation.yml "$@"
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_literal_string.yml.j2'" "$@"
ansible-playbook playbooks/test_populating_inventory_with_literal_string.yml "$@"
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_hostnames_using_tags_classic.yml.j2'" "$@"
ansible-playbook playbooks/test_populating_inventory_with_hostnames_using_tags_classic.yml "$@"
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_hostnames_using_tags.yml.j2'" "$@"
ansible-playbook playbooks/test_populating_inventory_with_hostnames_using_tags.yml "$@"

# generate inventory config with hostvars_prefix
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_hostvars_prefix_suffix.yml.j2'" -e "hostvars_prefix='aws_ec2_'" "$@"
ansible-playbook playbooks/test_populating_inventory_with_hostvars_prefix_suffix.yml -e "hostvars_prefix='aws_ec2_'" "$@"
# generate inventory config with hostvars_suffix
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_hostvars_prefix_suffix.yml.j2'" -e "hostvars_suffix='_aws_ec2'" "$@"
ansible-playbook playbooks/test_populating_inventory_with_hostvars_prefix_suffix.yml -e "hostvars_suffix='_aws_ec2'" "$@"
# generate inventory config with hostvars_prefix and hostvars_suffix
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_hostvars_prefix_suffix.yml.j2'" -e "hostvars_prefix='aws_'" -e "hostvars_suffix='_ec2'" "$@"
ansible-playbook playbooks/test_populating_inventory_with_hostvars_prefix_suffix.yml -e "hostvars_prefix='aws_'" -e "hostvars_suffix='_ec2'" "$@"

# generate inventory config with includes_entries_matching and prepare the tests
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_include_or_exclude_filters.yml.j2'" "$@"
ansible-playbook playbooks/test_populating_inventory_with_include_or_exclude_filters.yml "$@"

# generate inventory config with caching and test using it
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_use_contrib_script_keys.yml.j2'" "$@"
ANSIBLE_TRANSFORM_INVALID_GROUP_CHARS=never ansible-playbook playbooks/test_populating_inventory_with_use_contrib_script_keys.yml "$@"

# generate inventory config with caching and test using it
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_cache.yml.j2'" "$@"
ansible-playbook playbooks/populate_cache.yml "$@"
ansible-playbook playbooks/test_inventory_cache.yml "$@"

# generate inventory config with ssm inventory information
ansible-playbook playbooks/create_inventory_config.yml -e "template='inventory_with_ssm.yml.j2'" "$@"
ansible-playbook playbooks/test_inventory_ssm.yml "$@"

# remove inventory cache
rm -r aws_ec2_cache_dir/

# cleanup inventory config
ansible-playbook playbooks/empty_inventory_config.yml "$@"

# cleanup testing environment
ansible-playbook playbooks/manage_ec2_instances.yml -e "task=tear_down" "$@"
