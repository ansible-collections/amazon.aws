# (c) 2020 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import botocore
import boto3

from ansible_collections.amazon.aws.plugins.module_utils.botocore import BotocoreBaseMixin


class TestBotocoreGetters():
    # ========================================================
    # Prepare some data for use in our testing
    # ========================================================
    def setup_method(self):
        self.MINIMAL_BOTO3 = '1.17.0'
        self.MINIMAL_BOTOCORE = '1.20.0'
        self.OLD_BOTO3 = '1.16.999'
        self.OLD_BOTOCORE = '1.19.999'

        module = BotocoreBaseMixin()
        module.__SUPPORTED_BOTO3 = self.MINIMAL_BOTO3  # pylint: disable=unused-private-member
        module.__SUPPORTED_BOTOCORE = self.MINIMAL_BOTOCORE  # pylint: disable=unused-private-member
        self.module = module

    # ========================================================
    #   Test boto3/botocore protected getters
    # ========================================================
    def test_library_version_getters(self, monkeypatch):
        monkeypatch.setattr(botocore, "__version__", self.MINIMAL_BOTOCORE)
        monkeypatch.setattr(boto3, "__version__", self.MINIMAL_BOTO3)

        module = self.module
        gathered_versions = module._gather_versions()
        assert 'boto3_version' in gathered_versions
        assert 'botocore_version' in gathered_versions
        assert gathered_versions['boto3_version'] == self.MINIMAL_BOTO3
        assert gathered_versions['botocore_version'] == self.MINIMAL_BOTOCORE
        assert module._library_version('boto3') == self.MINIMAL_BOTO3
        assert module._library_version('botocore') == self.MINIMAL_BOTOCORE

    # ========================================================
    #   Test the pubic getters
    # ========================================================
    def test_version_getters(self, monkeypatch):
        monkeypatch.setattr(botocore, "__version__", self.MINIMAL_BOTOCORE)
        monkeypatch.setattr(boto3, "__version__", self.MINIMAL_BOTO3)

        module = self.module
        module.__SUPPORTED_BOTOCORE = self.MINIMAL_BOTOCORE  # pylint: disable=unused-private-member
        module.__SUPPORTED_BOTO3 = self.MINIMAL_BOTO3  # pylint: disable=unused-private-member
        module._REQUIRED_BOTOCORE = self.OLD_BOTOCORE
        module._REQUIRED_BOTO3 = self.OLD_BOTO3
        assert module.minimum_supported_boto3 == self.MINIMAL_BOTO3
        assert module.minimum_supported_botocore == self.MINIMAL_BOTOCORE
        assert module.minimum_required_boto3 == self.OLD_BOTO3
        assert module.minimum_required_botocore == self.OLD_BOTOCORE
