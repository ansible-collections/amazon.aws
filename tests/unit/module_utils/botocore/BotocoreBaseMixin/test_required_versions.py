# (c) 2020 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from pprint import pprint

import botocore
import boto3

import ansible_collections.amazon.aws.plugins.module_utils.botocore as botocore_utils
from ansible_collections.amazon.aws.plugins.module_utils.botocore import BotocoreBaseMixin
from ansible_collections.amazon.aws.tests.unit.compat.mock import MagicMock


class FailException(Exception):
    pass


class TestRequiredVersions():
    # ========================================================
    # Prepare some data for use in our testing
    # ========================================================
    def setup_method(self):
        self.MINIMAL_BOTO3 = '1.17.0'
        self.MINIMAL_BOTOCORE = '1.20.0'
        self.OLD_BOTO3 = '1.16.999'
        self.OLD_BOTOCORE = '1.19.999'

        botocore_utils.HAS_BOTO3 = True

        module = BotocoreBaseMixin()
        self.module = module
        module.fail = MagicMock(side_effect=FailException('Fail'))
        module.warn = MagicMock()

        module._REQUIRED_BOTO3 = self.MINIMAL_BOTO3
        module._REQUIRED_BOTOCORE = self.MINIMAL_BOTOCORE
        module.__SUPPORTED_BOTO3 = self.MINIMAL_BOTO3  # pylint: disable=unused-private-member
        module.__SUPPORTED_BOTOCORE = self.MINIMAL_BOTOCORE  # pylint: disable=unused-private-member

    # ========================================================
    #   Test we warn when boto3/botocore is missing
    # ========================================================
    def test_missing(self):
        # There's no good way to 'hide' the modules, but we rely on HAS_BOTO3 to
        # fail cleanly.
        botocore_utils.HAS_BOTO3 = False
        module = BotocoreBaseMixin()

        module.fail = MagicMock()
        module.warn = MagicMock()
        module.check_supported_libraries()
        message = module._test_required_libraries()

        assert not module.fail.called
        assert not module.warn.called
        assert message is not None
        assert "boto3" in message
        assert "botocore" in message

    # ========================================================
    #   Test we don't warn when using valid versions
    # ========================================================
    def test_no_warn(self, monkeypatch):
        monkeypatch.setattr(botocore, "__version__", self.MINIMAL_BOTOCORE)
        monkeypatch.setattr(boto3, "__version__", self.MINIMAL_BOTO3)

        module = self.module

        module.botocore_at_least()
        module.boto3_at_least()
        module.check_supported_libraries()
        message = module._test_required_libraries()

        assert not module.fail.called
        assert not module.warn.called
        assert message is None

    # ========================================================
    #   Test we warn when using an old version of boto3
    # ========================================================
    def test_fail_boto3(self, monkeypatch):
        monkeypatch.setattr(botocore, "__version__", self.MINIMAL_BOTOCORE)
        monkeypatch.setattr(boto3, "__version__", self.OLD_BOTO3)

        module = self.module

        message = module._test_required_libraries()
        pprint(message)

        assert not module.warn.called
        assert not module.fail.called
        assert message is not None
        assert "boto3" in message
        assert self.MINIMAL_BOTO3 in message

    # ========================================================
    #   Test we warn when using an old version of botocore
    # ========================================================
    def test_fail_botocore(self, monkeypatch):
        monkeypatch.setattr(botocore, "__version__", self.OLD_BOTOCORE)
        monkeypatch.setattr(boto3, "__version__", self.MINIMAL_BOTO3)

        module = self.module

        message = module._test_required_libraries()
        pprint(message)

        assert not module.warn.called
        assert not module.fail.called
        assert message is not None
        assert "botocore" in message
        assert self.MINIMAL_BOTOCORE in message
