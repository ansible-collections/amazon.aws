# (c) 2020 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from pprint import pprint

import botocore
import boto3

from ansible_collections.amazon.aws.plugins.module_utils.botocore import BotocoreBaseMixin
from ansible_collections.amazon.aws.tests.unit.compat.mock import MagicMock


class FailException(Exception):
    pass


class TestSupportedVersions():
    # ========================================================
    # Prepare some data for use in our testing
    # ========================================================
    def setup_method(self):
        self.MINIMAL_BOTO3 = '1.17.0'
        self.MINIMAL_BOTOCORE = '1.20.0'
        self.OLD_BOTO3 = '1.16.999'
        self.OLD_BOTOCORE = '1.19.999'

        module = BotocoreBaseMixin()
        module.fail = MagicMock(side_effect=FailException('Fail'))
        module.warn = MagicMock()
        module.__SUPPORTED_BOTO3 = self.MINIMAL_BOTO3  # pylint: disable=unused-private-member
        module.__SUPPORTED_BOTOCORE = self.MINIMAL_BOTOCORE  # pylint: disable=unused-private-member
        self.module = module

    # ========================================================
    #   Test we don't warn when using valid versions
    # ========================================================
    def test_no_warn(self, monkeypatch):
        monkeypatch.setattr(botocore, "__version__", self.MINIMAL_BOTOCORE)
        monkeypatch.setattr(boto3, "__version__", self.MINIMAL_BOTO3)

        module = self.module
        module.fail = MagicMock()
        module.warn = MagicMock()

        module.botocore_at_least()
        module.boto3_at_least()

        message = module._test_required_libraries()
        assert message is None

        module.check_supported_libraries()

        assert not module.fail.called
        assert not module.warn.called
        assert message is None

    # ========================================================
    #   Test we warn when using an old version of boto3
    # ========================================================
    def test_warn_boto3(self, monkeypatch):
        monkeypatch.setattr(botocore, "__version__", self.MINIMAL_BOTOCORE)
        monkeypatch.setattr(boto3, "__version__", self.OLD_BOTO3)

        module = self.module

        assert module.botocore_at_least()
        assert not module.boto3_at_least()
        assert not module.boto3_at_least(self.MINIMAL_BOTO3)
        assert module.boto3_at_least(self.OLD_BOTO3)

        message = module._test_required_libraries()
        assert message is None

        module.check_supported_libraries()

        assert not module.fail.called
        assert module.warn.call_count == 1
        assert len(module.warn.call_args.args) == 1
        warn_message = module.warn.call_args.args[0]
        assert "boto3" in warn_message
        assert "botocore" not in warn_message
        pprint(warn_message)
        assert self.MINIMAL_BOTO3 in warn_message

    # ========================================================
    #   Test we warn when using an old version of botocore
    # ========================================================
    def test_warn_botocore(self, monkeypatch):
        monkeypatch.setattr(botocore, "__version__", self.OLD_BOTOCORE)
        monkeypatch.setattr(boto3, "__version__", self.MINIMAL_BOTO3)

        module = self.module

        assert not module.botocore_at_least()
        assert module.boto3_at_least()
        assert not module.botocore_at_least(self.MINIMAL_BOTOCORE)
        assert module.botocore_at_least(self.OLD_BOTOCORE)

        message = module._test_required_libraries()
        assert message is None

        module.check_supported_libraries()

        assert not module.fail.called
        assert module.warn.call_count == 1
        assert len(module.warn.call_args.args) == 1
        warn_message = module.warn.call_args.args[0]
        assert "boto3" not in warn_message
        assert "botocore" in warn_message
        pprint(warn_message)
        assert self.MINIMAL_BOTOCORE in warn_message

    # ========================================================
    #   Test we warn when using an old version of botocore and boto3
    # ========================================================
    def test_warn_boto3_and_botocore(self, monkeypatch):
        monkeypatch.setattr(botocore, "__version__", self.OLD_BOTOCORE)
        monkeypatch.setattr(boto3, "__version__", self.OLD_BOTO3)

        module = self.module

        assert not module.botocore_at_least()
        assert not module.boto3_at_least()

        message = module._test_required_libraries()
        assert message is None

        module.check_supported_libraries()

        assert not module.fail.called
        assert module.warn.call_count > 0
        called_args = module.warn.call_args_list
        messages = {}
        for called_arg in called_args:
            assert len(called_arg.args) == 1
            warn_message = called_arg.args[0]
            pprint(warn_message)
            if "boto3" in warn_message:
                messages["boto3"] = warn_message
            if "botocore" in warn_message:
                messages["botocore"] = warn_message

        assert "boto3" in messages
        assert "botocore" in messages
        assert self.MINIMAL_BOTO3 in messages["boto3"]
        assert self.MINIMAL_BOTOCORE in messages["botocore"]
