# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import sentinel

import pytest

from ansible_collections.amazon.aws.plugins.module_utils import ec2_instance_utils


@pytest.fixture
def ec2_module_object():
    module_obj = MagicMock()
    module_obj.params = {
        "iam_instance_profile": None,
        "exact_count": None,
        "count": None,
        "launch_template": None,
        "instance_type": sentinel.INSTANCE_TYPE,
    }
    module_obj.connection = MagicMock()
    return module_obj


@pytest.fixture
def utils(monkeypatch):
    # monkey patches various ec2_instance_utils functions, we'll separately test the operation of
    # these functions, we just care that it's passing the results into the right place in the
    # instance spec.
    monkeypatch.setattr(
        ec2_instance_utils, "build_top_level_options", lambda params: {"TOP_LEVEL_OPTIONS": sentinel.TOP_LEVEL}
    )
    monkeypatch.setattr(ec2_instance_utils, "build_network_spec", lambda conn, params: sentinel.NETWORK_SPEC)
    monkeypatch.setattr(ec2_instance_utils, "build_volume_spec", lambda params: sentinel.VOlUME_SPEC)
    monkeypatch.setattr(ec2_instance_utils, "build_instance_tags", lambda params: sentinel.TAG_SPEC)
    return ec2_instance_utils


def _assert_defaults(instance_spec, to_skip=None):
    if not to_skip:
        to_skip = []

    assert isinstance(instance_spec, dict)

    if "TagSpecifications" not in to_skip:
        assert "TagSpecifications" in instance_spec
        assert instance_spec["TagSpecifications"] is sentinel.TAG_SPEC

    if "NetworkInterfaces" not in to_skip:
        assert "NetworkInterfaces" in instance_spec
        assert instance_spec["NetworkInterfaces"] is sentinel.NETWORK_SPEC

    if "BlockDeviceMappings" not in to_skip:
        assert "BlockDeviceMappings" in instance_spec
        assert instance_spec["BlockDeviceMappings"] is sentinel.VOlUME_SPEC

    if "IamInstanceProfile" not in to_skip:
        # By default, this shouldn't be returned
        assert "IamInstanceProfile" not in instance_spec

    if "MinCount" not in to_skip:
        assert "MinCount" in instance_spec
        instance_spec["MinCount"] == 1

    if "MaxCount" not in to_skip:
        assert "MaxCount" in instance_spec
        instance_spec["MaxCount"] == 1

    if "TOP_LEVEL_OPTIONS" not in to_skip:
        assert "TOP_LEVEL_OPTIONS" in instance_spec
        assert instance_spec["TOP_LEVEL_OPTIONS"] is sentinel.TOP_LEVEL

    if "InstanceType" not in to_skip:
        assert "InstanceType" in instance_spec
        instance_spec["InstanceType"] == sentinel.INSTANCE_TYPE


def test_build_run_instance_spec_defaults(ec2_module_object, utils):
    instance_spec = utils.build_run_instance_spec(ec2_module_object.connection, ec2_module_object.params)
    _assert_defaults(instance_spec)


def test_build_run_instance_spec_type_required(ec2_module_object, utils):
    ec2_module_object.params["instance_type"] = None
    ec2_module_object.params["launch_template"] = None
    # Test that we throw an AnsibleEC2Error if passed neither
    with pytest.raises(utils.AnsibleEC2Error):
        instance_spec = utils.build_run_instance_spec(ec2_module_object.connection, ec2_module_object.params)

    # Test that instance_type can be None if launch_template is set
    ec2_module_object.params["launch_template"] = sentinel.LAUNCH_TEMPLATE
    instance_spec = utils.build_run_instance_spec(ec2_module_object.connection, ec2_module_object.params)
    _assert_defaults(instance_spec, ["InstanceType"])
    assert "InstanceType" not in instance_spec


def test_build_run_instance_spec_tagging(ec2_module_object, utils, monkeypatch):
    # build_instance_tags can return None, RunInstance doesn't like this
    monkeypatch.setattr(utils, "build_instance_tags", lambda params: None)
    instance_spec = utils.build_run_instance_spec(ec2_module_object.connection, ec2_module_object.params)
    _assert_defaults(instance_spec, ["TagSpecifications"])
    assert "TagSpecifications" not in instance_spec

    # if someone *explicitly* passes {} (rather than not setting it), then [] can be returned
    monkeypatch.setattr(utils, "build_instance_tags", lambda params: [])
    instance_spec = utils.build_run_instance_spec(ec2_module_object.connection, ec2_module_object.params)
    _assert_defaults(instance_spec, ["TagSpecifications"])
    assert "TagSpecifications" in instance_spec
    assert instance_spec["TagSpecifications"] == []


def test_build_run_instance_spec_instance_profile(ec2_module_object, utils):
    instance_spec = utils.build_run_instance_spec(
        ec2_module_object.connection, ec2_module_object.params, iam_role_arn=sentinel.IAM_PROFILE_ARN
    )
    _assert_defaults(instance_spec, ["IamInstanceProfile"])
    assert "IamInstanceProfile" in instance_spec
    assert instance_spec["IamInstanceProfile"] == {"Arn": sentinel.IAM_PROFILE_ARN}


def test_build_run_instance_spec_count(ec2_module_object, utils):
    # When someone passes 'count', that number of instances will be *launched*
    ec2_module_object.params["count"] = sentinel.COUNT
    instance_spec = utils.build_run_instance_spec(ec2_module_object.connection, ec2_module_object.params)
    _assert_defaults(instance_spec, ["MaxCount", "MinCount"])
    assert "MaxCount" in instance_spec
    assert "MinCount" in instance_spec
    assert instance_spec["MaxCount"] == sentinel.COUNT
    assert instance_spec["MinCount"] == sentinel.COUNT


def test_build_run_instance_spec_exact_count(ec2_module_object, utils):
    # The "exact_count" logic relies on enforce_count doing the math to figure out how many
    # instances to start/stop.  The enforce_count call is responsible for ensuring that 'to_launch'
    # is set and is a positive integer.
    ec2_module_object.params["exact_count"] = 42
    ec2_module_object.params["to_launch"] = sentinel.TO_LAUNCH
    instance_spec = utils.build_run_instance_spec(ec2_module_object.connection, ec2_module_object.params)

    _assert_defaults(instance_spec, ["MaxCount", "MinCount"])
    assert "MaxCount" in instance_spec
    assert "MinCount" in instance_spec
    assert instance_spec["MaxCount"] == 42
    assert instance_spec["MinCount"] == 42

    instance_spec = utils.build_run_instance_spec(ec2_module_object.connection, ec2_module_object.params, 7)

    _assert_defaults(instance_spec, ["MaxCount", "MinCount"])
    assert "MaxCount" in instance_spec
    assert "MinCount" in instance_spec
    assert instance_spec["MaxCount"] == 35
    assert instance_spec["MinCount"] == 35
