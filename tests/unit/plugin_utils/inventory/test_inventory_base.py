# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import re
from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch
from unittest.mock import sentinel

import pytest

import ansible.plugins.inventory as base_inventory
from ansible.errors import AnsibleError
from ansible.module_utils.six import string_types

import ansible_collections.amazon.aws.plugins.plugin_utils.inventory as utils_inventory


@patch("ansible.plugins.inventory.BaseInventoryPlugin.parse", MagicMock)
def test_parse(monkeypatch):
    require_aws_sdk = MagicMock(name="require_aws_sdk")
    require_aws_sdk.return_value = sentinel.RETURNED_SDK
    config_data = MagicMock(name="_read_config_data")
    config_data.return_value = sentinel.RETURNED_OPTIONS
    frozen_credentials = MagicMock(name="_set_frozen_credentials")
    frozen_credentials.return_value = sentinel.RETURNED_CREDENTIALS

    inventory_plugin = utils_inventory.AWSInventoryBase()
    monkeypatch.setattr(inventory_plugin, "require_aws_sdk", require_aws_sdk)
    monkeypatch.setattr(inventory_plugin, "_read_config_data", config_data)
    monkeypatch.setattr(inventory_plugin, "_set_frozen_credentials", frozen_credentials)

    inventory_plugin.parse(sentinel.PARAM_INVENTORY, sentinel.PARAM_LOADER, sentinel.PARAM_PATH)
    assert require_aws_sdk.call_args == call(botocore_version=None, boto3_version=None)
    assert config_data.call_args == call(sentinel.PARAM_PATH)
    assert frozen_credentials.call_args == call()


@pytest.mark.parametrize(
    "filename,result",
    [
        ("inventory_aws_ec2.yml", True),
        ("inventory_aws_ec2.yaml", True),
        ("inventory_aws_EC2.yaml", False),
        ("inventory_Aws_ec2.yaml", False),
        ("aws_ec2_inventory.yml", False),
        ("aws_ec2.yml_inventory", False),
        ("aws_ec2.yml", True),
        ("aws_ec2.yaml", True),
    ],
)
def test_inventory_verify_file(monkeypatch, filename, result):
    base_verify = MagicMock(name="verify_file")
    monkeypatch.setattr(base_inventory.BaseInventoryPlugin, "verify_file", base_verify)
    inventory_plugin = utils_inventory.AWSInventoryBase()

    # With INVENTORY_FILE_SUFFIXES not set, we should simply pass through the return from the base
    base_verify.return_value = True
    assert inventory_plugin.verify_file(filename) is True
    base_verify.return_value = False
    assert inventory_plugin.verify_file(filename) is False

    # With INVENTORY_FILE_SUFFIXES set, we only return True of the base is good *and* the filename matches
    inventory_plugin.INVENTORY_FILE_SUFFIXES = ("aws_ec2.yml", "aws_ec2.yaml")
    base_verify.return_value = True
    assert inventory_plugin.verify_file(filename) is result
    base_verify.return_value = False
    assert inventory_plugin.verify_file(filename) is False


class AwsUnitTestTemplar:
    def __init__(self, config):
        self.config = config

    def is_template_string(self, key):
        m = re.findall("{{([ ]*[a-zA-Z0-9_]*[ ]*)}}", key)
        return bool(m)

    def is_template(self, data):
        if isinstance(data, string_types):
            return self.is_template_string(data)
        elif isinstance(data, (list, tuple)):
            for v in data:
                if self.is_template(v):
                    return True
        elif isinstance(data, dict):
            for k in data:
                if self.is_template(k) or self.is_template(data[k]):
                    return True
        return False

    def template(self, variable, disable_lookups):
        for k, v in self.config.items():
            variable = re.sub("{{([ ]*%s[ ]*)}}" % k, v, variable)
        if self.is_template_string(variable):
            m = re.findall("{{([ ]*[a-zA-Z0-9_]*[ ]*)}}", variable)
            raise AnsibleError(f"Missing variables: {','.join([k.replace(' ', '') for k in m])}")
        return variable


@pytest.fixture
def aws_inventory_base():
    inventory = utils_inventory.AWSInventoryBase()
    inventory._options = {}
    inventory.templar = None
    return inventory


@pytest.mark.parametrize(
    "option,value",
    [
        ("access_key", "amazon_ansible_access_key_001"),
        ("secret_key", "amazon_ansible_secret_key_890"),
        ("session_token", None),
        ("use_ssm_inventory", False),
        ("This_field_is_undefined", None),
        ("assume_role_arn", "arn:aws:iam::123456789012:role/ansible-test-inventory"),
        ("region", "us-east-2"),
    ],
)
def test_inventory_get_options_without_templar(aws_inventory_base, mocker, option, value):
    inventory_options = {
        "access_key": "amazon_ansible_access_key_001",
        "secret_key": "amazon_ansible_secret_key_890",
        "endpoint": "http//ansible.amazon.com",
        "assume_role_arn": "arn:aws:iam::123456789012:role/ansible-test-inventory",
        "region": "us-east-2",
        "use_ssm_inventory": False,
    }
    aws_inventory_base._options = inventory_options

    super_get_options_patch = mocker.patch(
        "ansible_collections.amazon.aws.plugins.plugin_utils.inventory.BaseInventoryPlugin.get_options"
    )
    super_get_options_patch.return_value = aws_inventory_base._options

    options = aws_inventory_base.get_options()
    assert value == options.get(option)


@pytest.mark.parametrize(
    "option,value,error",
    [
        ("access_key", "amazon_ansible_access_key_001", None),
        ("session_token", None, None),
        ("use_ssm_inventory", "{{ aws_inventory_use_ssm }}", None),
        ("This_field_is_undefined", None, None),
        ("region", "us-east-1", None),
        ("profile", None, "Missing variables: ansible_version"),
    ],
)
def test_inventory_get_options_with_templar(aws_inventory_base, mocker, option, value, error):
    inventory_options = {
        "access_key": "amazon_ansible_access_key_001",
        "profile": "ansbile_{{ ansible_os }}_{{ ansible_version }}",
        "endpoint": "{{ aws_endpoint }}",
        "region": "{{ aws_region_country }}-east-{{ aws_region_id }}",
        "use_ssm_inventory": "{{ aws_inventory_use_ssm }}",
    }
    aws_inventory_base._options = inventory_options
    templar_config = {
        "ansible_os": "RedHat",
        "aws_region_country": "us",
        "aws_region_id": "1",
        "aws_endpoint": "http//ansible.amazon.com",
    }
    aws_inventory_base.templar = AwsUnitTestTemplar(templar_config)

    super_get_options_patch = mocker.patch(
        "ansible_collections.amazon.aws.plugins.plugin_utils.inventory.BaseInventoryPlugin.get_options"
    )
    super_get_options_patch.return_value = aws_inventory_base._options

    super_get_option_patch = mocker.patch(
        "ansible_collections.amazon.aws.plugins.plugin_utils.inventory.BaseInventoryPlugin.get_option"
    )
    super_get_option_patch.side_effect = lambda x, hostvars=None: aws_inventory_base._options.get(x)

    if error:
        # test using get_options()
        with pytest.raises(AnsibleError) as exc:
            options = aws_inventory_base.get_options()
            options.get(option)
        assert error == str(exc.value)

        # test using get_option()
        with pytest.raises(AnsibleError) as exc:
            aws_inventory_base.get_option(option)
        assert error == str(exc.value)
    else:
        # test using get_options()
        options = aws_inventory_base.get_options()
        assert value == options.get(option)

        # test using get_option()
        assert value == aws_inventory_base.get_option(option)
