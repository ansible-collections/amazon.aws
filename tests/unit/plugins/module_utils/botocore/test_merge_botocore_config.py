# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock

import pytest

try:
    import botocore
except ImportError:
    # Handled by HAS_BOTO3
    pass

import ansible_collections.amazon.aws.plugins.module_utils.botocore as utils_botocore

MINIMAL_CONFIG = {
    "user_agent_extra": "Ansible/unit-test",
}


@pytest.fixture(name="basic_config")
def fixture_basic_config():
    config = botocore.config.Config(**MINIMAL_CONFIG)
    return config


def test_none_config(monkeypatch, basic_config):
    original_options = basic_config._user_provided_options.copy()

    monkeypatch.setattr(basic_config, "merge", MagicMock(name="merge"))
    updated_config = utils_botocore._merge_botocore_config(basic_config, None)
    assert not basic_config.merge.called
    assert basic_config._user_provided_options == original_options
    assert updated_config._user_provided_options == original_options


def test_botocore_config(basic_config):
    original_options = basic_config._user_provided_options.copy()
    config_b = botocore.config.Config(parameter_validation=False)
    updated_config = utils_botocore._merge_botocore_config(basic_config, config_b)

    assert basic_config._user_provided_options == original_options
    assert not updated_config._user_provided_options == original_options
    assert updated_config._user_provided_options.get("parameter_validation") is False
    assert updated_config._user_provided_options.get("user_agent_extra") == "Ansible/unit-test"

    config_c = botocore.config.Config(user_agent_extra="Ansible/unit-test Updated")
    updated_config = utils_botocore._merge_botocore_config(updated_config, config_c)
    assert updated_config._user_provided_options.get("parameter_validation") is False
    assert updated_config._user_provided_options.get("user_agent_extra") == "Ansible/unit-test Updated"


def test_botocore_dict(basic_config):
    original_options = basic_config._user_provided_options.copy()
    config_b = dict(parameter_validation=False)
    updated_config = utils_botocore._merge_botocore_config(basic_config, config_b)

    assert basic_config._user_provided_options == original_options
    assert not updated_config._user_provided_options == original_options
    assert updated_config._user_provided_options.get("parameter_validation") is False
    assert updated_config._user_provided_options.get("user_agent_extra") == "Ansible/unit-test"

    config_c = dict(user_agent_extra="Ansible/unit-test Updated")
    updated_config = utils_botocore._merge_botocore_config(updated_config, config_c)
    assert updated_config._user_provided_options.get("parameter_validation") is False
    assert updated_config._user_provided_options.get("user_agent_extra") == "Ansible/unit-test Updated"


def test_empty_dict(basic_config):
    """Test that merging an empty dict returns the original config unchanged."""
    original_options = basic_config._user_provided_options.copy()
    updated_config = utils_botocore._merge_botocore_config(basic_config, {})

    assert basic_config._user_provided_options == original_options
    assert updated_config._user_provided_options == original_options


def test_retries_config(basic_config):
    """Test merging retry configuration."""
    retry_config = dict(retries={"max_attempts": 10, "mode": "adaptive"})
    updated_config = utils_botocore._merge_botocore_config(basic_config, retry_config)

    assert updated_config._user_provided_options.get("retries") == {"max_attempts": 10, "mode": "adaptive"}
    assert updated_config._user_provided_options.get("user_agent_extra") == "Ansible/unit-test"


def test_multiple_parameters(basic_config):
    """Test merging multiple configuration parameters at once."""
    multi_config = dict(
        parameter_validation=False,
        signature_version="s3v4",
        s3={"use_accelerate_endpoint": True},
    )
    updated_config = utils_botocore._merge_botocore_config(basic_config, multi_config)

    assert updated_config._user_provided_options.get("parameter_validation") is False
    assert updated_config._user_provided_options.get("signature_version") == "s3v4"
    assert updated_config._user_provided_options.get("s3") == {"use_accelerate_endpoint": True}
    assert updated_config._user_provided_options.get("user_agent_extra") == "Ansible/unit-test"


def test_region_config(basic_config):
    """Test merging region configuration."""
    region_config = botocore.config.Config(region_name="us-west-2")
    updated_config = utils_botocore._merge_botocore_config(basic_config, region_config)

    assert updated_config._user_provided_options.get("region_name") == "us-west-2"
    assert updated_config._user_provided_options.get("user_agent_extra") == "Ansible/unit-test"
