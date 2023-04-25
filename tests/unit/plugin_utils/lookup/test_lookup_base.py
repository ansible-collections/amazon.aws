# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import sentinel

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
