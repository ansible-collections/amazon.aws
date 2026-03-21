# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import sentinel

import pytest

from ansible.errors import AnsibleLookupError

import ansible_collections.amazon.aws.plugins.plugin_utils.lookup as utils_lookup


def test_fail_aws():
    lookup_plugin = utils_lookup.AWSLookupBase()
    with pytest.raises(AnsibleLookupError, match=str(sentinel.ERROR_MSG)):
        lookup_plugin._do_fail(sentinel.ERROR_MSG)


def test_run(monkeypatch):
    kwargs = {"example": sentinel.KWARG}
    require_aws_sdk = MagicMock(name="require_aws_sdk")
    require_aws_sdk.return_value = sentinel.RETURNED_SDK
    set_options = MagicMock(name="set_options")
    set_options.return_value = sentinel.RETURNED_OPTIONS

    lookup_plugin = utils_lookup.AWSLookupBase()
    monkeypatch.setattr(lookup_plugin, "require_aws_sdk", require_aws_sdk)
    monkeypatch.setattr(lookup_plugin, "set_options", set_options)

    lookup_plugin.run(sentinel.PARAM_TERMS, sentinel.PARAM_VARS, **kwargs)
    assert require_aws_sdk.call_args == call(botocore_version=None, boto3_version=None)
    assert set_options.call_args == call(var_options=sentinel.PARAM_VARS, direct=kwargs)

    lookup_plugin.run(
        sentinel.PARAM_TERMS,
        sentinel.PARAM_VARS,
        boto3_version=sentinel.PARAM_BOTO3,
        botocore_version=sentinel.PARAM_BOTOCORE,
        **kwargs,
    )
    assert require_aws_sdk.call_args == call(
        botocore_version=sentinel.PARAM_BOTOCORE, boto3_version=sentinel.PARAM_BOTO3
    )
    assert set_options.call_args == call(var_options=sentinel.PARAM_VARS, direct=kwargs)


def test_on_missing_property_with_option():
    """Test on_missing property when get_option returns a value"""
    lookup_plugin = utils_lookup.AWSLookupBase()
    lookup_plugin.get_option = MagicMock(return_value="warn")

    assert lookup_plugin.on_missing == "warn"
    lookup_plugin.get_option.assert_called_once_with("on_missing")


def test_on_missing_property_without_option():
    """Test on_missing property when get_option raises KeyError (option not defined)"""
    lookup_plugin = utils_lookup.AWSLookupBase()
    lookup_plugin.get_option = MagicMock(side_effect=KeyError("on_missing"))

    # Should default to "error" when option doesn't exist
    assert lookup_plugin.on_missing == "error"


def test_on_denied_property_with_option():
    """Test on_denied property when get_option returns a value"""
    lookup_plugin = utils_lookup.AWSLookupBase()
    lookup_plugin.get_option = MagicMock(return_value="skip")

    assert lookup_plugin.on_denied == "skip"
    lookup_plugin.get_option.assert_called_once_with("on_denied")


def test_on_denied_property_without_option():
    """Test on_denied property when get_option raises KeyError (option not defined)"""
    lookup_plugin = utils_lookup.AWSLookupBase()
    lookup_plugin.get_option = MagicMock(side_effect=KeyError("on_denied"))

    # Should default to "error" when option doesn't exist
    assert lookup_plugin.on_denied == "error"


def test_on_deleted_property_with_option():
    """Test on_deleted property when get_option returns a value"""
    lookup_plugin = utils_lookup.AWSLookupBase()
    lookup_plugin.get_option = MagicMock(return_value="warn")

    assert lookup_plugin.on_deleted == "warn"
    lookup_plugin.get_option.assert_called_once_with("on_deleted")


def test_on_deleted_property_without_option():
    """Test on_deleted property when get_option raises KeyError (option not defined)"""
    lookup_plugin = utils_lookup.AWSLookupBase()
    lookup_plugin.get_option = MagicMock(side_effect=KeyError("on_deleted"))

    # Should default to "error" when option doesn't exist
    assert lookup_plugin.on_deleted == "error"
