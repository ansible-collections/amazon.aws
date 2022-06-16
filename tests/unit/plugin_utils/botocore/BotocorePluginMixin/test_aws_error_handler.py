# (c) 2020 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from pprint import pprint

import botocore

from ansible_collections.amazon.aws.plugins.plugin_utils.botocore import BotocorePluginMixin
from ansible_collections.amazon.aws.tests.unit.compat.mock import MagicMock


class FailException(Exception):
    pass


class FailAWSException(Exception):
    pass


class FakeModule(BotocorePluginMixin):
    @BotocorePluginMixin.aws_error_handler("do something")
    def do_something(self):
        return self._do_something()


class TestAWSErrorHandler():
    # ========================================================
    # Prepare some data for use in our testing
    # ========================================================
    def setup_method(self):

        module = FakeModule()
        module.fail = MagicMock(side_effect=FailException('Fail'))
        module.fail_aws = MagicMock(side_effect=FailAWSException('FailAWS'))
        module.warn = MagicMock()
        self.module = module

    # ========================================================
    #   Test wrapping calls using aws_error_handler
    # ========================================================
    def test_success(self):
        module = self.module

        expected_value = "I did something!"
        module._do_something = MagicMock(return_value=expected_value)

        ret = module.do_something()
        assert not module.warn.called
        assert not module.fail.called
        assert not module.fail_aws.called
        assert ret == expected_value

    # ========================================================
    #   Test wrapping calls using aws_error_handler
    # ========================================================
    def test_uncaught_failure(self):
        module = self.module

        module._do_something = MagicMock(side_effect=FailAWSException('I failed :('))

        try:
            ret = module.do_something()
            pprint(ret)
            assert False
        except FailAWSException:
            assert True

        assert not module.warn.called
        assert not module.fail.called
        assert not module.fail_aws.called

    def test_botocore_failure(self):
        module = self.module

        error_message = 'I failed :('
        module._do_something = MagicMock(side_effect=botocore.exceptions.BotoCoreError(msg=error_message))

        try:
            ret = module.do_something()
            pprint(ret)
            assert False
        except FailAWSException:
            assert True

        assert not module.warn.called
        assert not module.fail.called
        assert module.fail_aws.called
        pprint(module.fail_aws.call_args.args)
        pprint(module.fail_aws.call_args.kwargs)
        assert len(module.fail_aws.call_args.args) == 1
        fail_exception = module.fail_aws.call_args.args[0]
        assert isinstance(fail_exception, botocore.exceptions.BotoCoreError)
        assert "msg" in module.fail_aws.call_args.kwargs
        fail_message = module.fail_aws.call_args.kwargs["msg"]
        assert "do something" in fail_message
        assert "waiting" not in fail_message

    def test_client_failure(self):
        module = self.module

        error_message = 'I failed :('
        err_msg = {'Error': {'Code': 'RequestLimitExceeded'}}
        module._do_something = MagicMock(side_effect=botocore.exceptions.ClientError(err_msg, error_message))

        try:
            ret = module.do_something()
            pprint(ret)
            assert False
        except FailAWSException:
            assert True

        assert not module.warn.called
        assert not module.fail.called
        assert module.fail_aws.called
        pprint(module.fail_aws.call_args.args)
        pprint(module.fail_aws.call_args.kwargs)
        assert len(module.fail_aws.call_args.args) == 1
        fail_exception = module.fail_aws.call_args.args[0]
        assert isinstance(fail_exception, botocore.exceptions.ClientError)
        assert "msg" in module.fail_aws.call_args.kwargs
        fail_message = module.fail_aws.call_args.kwargs["msg"]
        pprint(fail_message)
        assert "do something" in fail_message
        assert "waiting" not in fail_message

    def test_wait_failure(self):
        module = self.module

        error_code = 'SomethingWrong'
        error_message = 'I failed :('
        error_detail = {"Description": "I was doing something", "ProgressStatus": "FAILED"}
        error = botocore.exceptions.WaiterError(error_code, error_message, error_detail)
        module._do_something = MagicMock(side_effect=error)

        try:
            ret = module.do_something()
            pprint(ret)
            assert False
        except FailAWSException:
            assert True

        assert not module.warn.called
        assert not module.fail.called
        assert module.fail_aws.called
        pprint(module.fail_aws.call_args.args)
        pprint(module.fail_aws.call_args.kwargs)
        assert len(module.fail_aws.call_args.args) == 1
        fail_exception = module.fail_aws.call_args.args[0]
        assert isinstance(fail_exception, botocore.exceptions.WaiterError)
        assert "msg" in module.fail_aws.call_args.kwargs
        fail_message = module.fail_aws.call_args.kwargs["msg"]
        pprint(fail_message)
        assert "do something" in fail_message
        assert "waiting" in fail_message
