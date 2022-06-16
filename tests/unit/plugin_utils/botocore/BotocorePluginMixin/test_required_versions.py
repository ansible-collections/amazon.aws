# (c) 2020 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from pprint import pprint

from ansible_collections.amazon.aws.plugins.plugin_utils.botocore import BotocorePluginMixin
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

        module = BotocorePluginMixin()
        module.fail = MagicMock(side_effect=FailException('Fail'))
        module.warn = MagicMock()

        module.__SUPPORTED_BOTO3 = self.MINIMAL_BOTO3  # pylint: disable=unused-private-member
        module.__SUPPORTED_BOTOCORE = self.MINIMAL_BOTOCORE  # pylint: disable=unused-private-member
        self.module = module

    # ========================================================
    #   Test we don't warn/fail when using valid versions
    # ========================================================
    def test_no_warn(self):
        module = self.module

        module.boto3_at_least = MagicMock(return_value=True)
        module.botocore_at_least = MagicMock(return_value=True)

        module.require_botocore_at_least(self.MINIMAL_BOTOCORE)
        module.require_boto3_at_least(self.MINIMAL_BOTO3)
        assert not module.fail.called
        assert not module.warn.called

        module.boto3_at_least = MagicMock(return_value=False)
        module.botocore_at_least = MagicMock(return_value=True)

        module.require_botocore_at_least(self.MINIMAL_BOTOCORE)
        assert not module.fail.called
        assert not module.warn.called

        module.boto3_at_least = MagicMock(return_value=True)
        module.botocore_at_least = MagicMock(return_value=False)

        module.require_boto3_at_least(self.MINIMAL_BOTO3)
        assert not module.fail.called
        assert not module.warn.called

    # ========================================================
    #   Test failure when botocore isn't enough
    # ========================================================
    def test_require_botocore_at_least(self):
        module = self.module

        module.boto3_at_least = MagicMock(return_value=True)
        module.botocore_at_least = MagicMock(return_value=False)

        module.require_boto3_at_least(self.MINIMAL_BOTO3)
        assert not module.fail.called
        assert not module.warn.called

        try:
            module.require_botocore_at_least(self.MINIMAL_BOTOCORE)
            assert False
        except FailException:
            pass

        assert not module.warn.called
        assert module.fail.called
        assert len(module.fail.call_args.args) == 1
        fail_message = module.fail.call_args.args[0]
        assert "boto3" not in fail_message
        assert "botocore" in fail_message
        pprint(fail_message)
        assert self.MINIMAL_BOTOCORE in fail_message

    # ========================================================
    #   Test failure when boto3 isn't enough
    # ========================================================
    def test_require_boto3_at_least(self):
        module = self.module

        module.boto3_at_least = MagicMock(return_value=False)
        module.botocore_at_least = MagicMock(return_value=True)

        module.require_botocore_at_least(self.MINIMAL_BOTOCORE)
        assert not module.fail.called
        assert not module.warn.called

        try:
            module.require_boto3_at_least(self.MINIMAL_BOTO3)
            assert False
        except FailException:
            pass
        assert not module.warn.called
        assert module.fail.called
        assert len(module.fail.call_args.args) == 1
        fail_message = module.fail.call_args.args[0]
        assert "boto3" in fail_message
        assert "botocore" not in fail_message
        pprint(fail_message)
        assert self.MINIMAL_BOTO3 in fail_message

    # ========================================================
    #   Test failure when _test_required_libraries fails
    # ========================================================
    def test_check_required_libraries(self):
        module = self.module
        mock_message = "Open unlocks the world's potential"

        module._test_required_libraries = MagicMock(return_value=None)
        module.check_required_libraries()
        assert not module.fail.called
        assert not module.warn.called

        module._test_required_libraries = MagicMock(return_value=mock_message)
        try:
            module.check_required_libraries()
            assert False
        except FailException:
            pass
        assert not module.warn.called
        assert module.fail.called
        assert len(module.fail.call_args.args) == 1
        fail_message = module.fail.call_args.args[0]
        assert mock_message in fail_message
