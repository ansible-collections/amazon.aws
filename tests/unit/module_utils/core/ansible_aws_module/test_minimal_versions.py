# (c) 2020 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import botocore
import boto3
import json
import warnings

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from pprint import pprint


class TestMinimalVersions(object):
    # ========================================================
    # Prepare some data for use in our testing
    # ========================================================
    def setup_method(self):
        self.MINIMAL_BOTO3 = '1.16.0'
        self.MINIMAL_BOTOCORE = '1.19.0'
        self.OLD_BOTO3 = '1.15.999'
        self.OLD_BOTOCORE = '1.18.999'

    # ========================================================
    #   Test we don't warn when using valid versions
    # ========================================================
    @pytest.mark.parametrize("stdin", [{}], indirect=["stdin"])
    def test_no_warn(self, monkeypatch, stdin, capfd):
        monkeypatch.setattr(botocore, "__version__", self.MINIMAL_BOTOCORE)
        monkeypatch.setattr(boto3, "__version__", self.MINIMAL_BOTO3)

        # Create a minimal module that we can call
        module = AnsibleAWSModule(argument_spec=dict())

        with pytest.raises(SystemExit) as e:
            module.exit_json()

        out, err = capfd.readouterr()
        return_val = json.loads(out)

        assert return_val.get("exception") is None
        assert return_val.get("invocation") is not None
        assert return_val.get("failed") is None
        assert return_val.get("error") is None
        assert return_val.get("warnings") is None

    # ========================================================
    #   Test we don't warn when botocore/boto3 isn't required
    # ========================================================
    @pytest.mark.parametrize("stdin", [{}], indirect=["stdin"])
    def test_no_check(self, monkeypatch, stdin, capfd):
        monkeypatch.setattr(botocore, "__version__", self.OLD_BOTOCORE)
        monkeypatch.setattr(boto3, "__version__", self.OLD_BOTO3)

        # Create a minimal module that we can call
        module = AnsibleAWSModule(argument_spec=dict(), check_boto3=False)

        with pytest.raises(SystemExit) as e:
            module.exit_json()

        out, err = capfd.readouterr()
        return_val = json.loads(out)

        assert return_val.get("exception") is None
        assert return_val.get("invocation") is not None
        assert return_val.get("failed") is None
        assert return_val.get("error") is None
        assert return_val.get("warnings") is None

    # ========================================================
    #   Test we warn when using an old version of boto3
    # ========================================================
    @pytest.mark.parametrize("stdin", [{}], indirect=["stdin"])
    def test_warn_boto3(self, monkeypatch, stdin, capfd):
        monkeypatch.setattr(botocore, "__version__", self.MINIMAL_BOTOCORE)
        monkeypatch.setattr(boto3, "__version__", self.OLD_BOTO3)

        # Create a minimal module that we can call
        module = AnsibleAWSModule(argument_spec=dict())

        with pytest.raises(SystemExit) as e:
            module.exit_json()

        out, err = capfd.readouterr()
        return_val = json.loads(out)

        pprint(out)
        pprint(err)
        pprint(return_val)

        assert return_val.get("exception") is None
        assert return_val.get("invocation") is not None
        assert return_val.get("failed") is None
        assert return_val.get("error") is None
        assert return_val.get("warnings") is not None
        warnings = return_val.get("warnings")
        assert len(warnings) == 1
        # Assert that we have a warning about the version but be
        # relaxed about the exact message
        assert 'boto3' in warnings[0]
        assert self.MINIMAL_BOTO3 in warnings[0]

    # ========================================================
    #   Test we warn when using an old version of botocore
    # ========================================================
    @pytest.mark.parametrize("stdin", [{}], indirect=["stdin"])
    def test_warn_botocore(self, monkeypatch, stdin, capfd):
        monkeypatch.setattr(botocore, "__version__", self.OLD_BOTOCORE)
        monkeypatch.setattr(boto3, "__version__", self.MINIMAL_BOTO3)

        # Create a minimal module that we can call
        module = AnsibleAWSModule(argument_spec=dict())

        with pytest.raises(SystemExit) as e:
            module.exit_json()

        out, err = capfd.readouterr()
        return_val = json.loads(out)

        pprint(out)
        pprint(err)
        pprint(return_val)

        assert return_val.get("exception") is None
        assert return_val.get("invocation") is not None
        assert return_val.get("failed") is None
        assert return_val.get("error") is None
        assert return_val.get("warnings") is not None
        warnings = return_val.get("warnings")
        assert len(warnings) == 1
        # Assert that we have a warning about the version but be
        # relaxed about the exact message
        assert 'botocore' in warnings[0]
        assert self.MINIMAL_BOTOCORE in warnings[0]

    # ========================================================
    #   Test we warn when using an old version of botocore and boto3
    # ========================================================
    @pytest.mark.parametrize("stdin", [{}], indirect=["stdin"])
    def test_warn_boto3_and_botocore(self, monkeypatch, stdin, capfd):
        monkeypatch.setattr(botocore, "__version__", self.OLD_BOTOCORE)
        monkeypatch.setattr(boto3, "__version__", self.OLD_BOTO3)

        # Create a minimal module that we can call
        module = AnsibleAWSModule(argument_spec=dict())

        with pytest.raises(SystemExit) as e:
            module.exit_json()

        out, err = capfd.readouterr()
        return_val = json.loads(out)

        pprint(out)
        pprint(err)
        pprint(return_val)

        assert return_val.get("exception") is None
        assert return_val.get("invocation") is not None
        assert return_val.get("failed") is None
        assert return_val.get("error") is None
        assert return_val.get("warnings") is not None

        warnings = return_val.get("warnings")
        assert len(warnings) == 2

        warning_dict = dict()
        for warning in warnings:
            if 'boto3' in warning:
                warning_dict['boto3'] = warning
            if 'botocore' in warning:
                warning_dict['botocore'] = warning

        # Assert that we have a warning about the version but be
        # relaxed about the exact message
        assert warning_dict.get('boto3') is not None
        assert self.MINIMAL_BOTO3 in warning_dict.get('boto3')
        assert warning_dict.get('botocore') is not None
        assert self.MINIMAL_BOTOCORE in warning_dict.get('botocore')
