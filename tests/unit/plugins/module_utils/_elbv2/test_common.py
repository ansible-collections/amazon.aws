# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

try:
    import botocore
except ImportError:
    pass

import pytest

from ansible_collections.amazon.aws.plugins.module_utils._elbv2.common import AnsibleELBv2Error
from ansible_collections.amazon.aws.plugins.module_utils._elbv2.common import ELBv2ErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils._elbv2.common import ELBv2ListenerErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils._elbv2.common import ELBv2RuleErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils._elbv2.common import ELBv2TargetGroupErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_common.py requires the python modules 'boto3' and 'botocore'")


class TestELBv2ErrorHandler:
    """Test that ELBv2ErrorHandler raises the correct custom exception."""

    def test_raises_custom_exception(self):
        """Verify ELBv2ErrorHandler raises AnsibleELBv2Error on botocore errors."""
        err_response = {"Error": {"Code": "InvalidParameterValue"}}

        @ELBv2ErrorHandler.common_error_handler("test operation")
        def raise_client_error():
            raise botocore.exceptions.ClientError(err_response, "TestOperation")

        with pytest.raises(AnsibleELBv2Error) as e_info:
            raise_client_error()

        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "test operation" in raised.message

    def test_handles_load_balancer_not_found(self):
        """Verify _is_missing matches LoadBalancerNotFound error code."""
        err_response = {"Error": {"Code": "LoadBalancerNotFound"}}

        @ELBv2ErrorHandler.deletion_error_handler("delete load balancer")
        def raise_not_found():
            raise botocore.exceptions.ClientError(err_response, "DeleteLoadBalancer")

        # deletion_error_handler should suppress LoadBalancerNotFound
        result = raise_not_found()
        assert result is False


class TestELBv2ListenerErrorHandler:
    """Test that ELBv2ListenerErrorHandler raises the correct custom exception."""

    def test_raises_custom_exception(self):
        """Verify ELBv2ListenerErrorHandler raises AnsibleELBv2Error on botocore errors."""
        err_response = {"Error": {"Code": "InvalidParameterValue"}}

        @ELBv2ListenerErrorHandler.common_error_handler("test listener operation")
        def raise_client_error():
            raise botocore.exceptions.ClientError(err_response, "TestListenerOperation")

        with pytest.raises(AnsibleELBv2Error) as e_info:
            raise_client_error()

        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "test listener operation" in raised.message

    def test_handles_listener_not_found(self):
        """Verify _is_missing matches ListenerNotFound error code."""
        err_response = {"Error": {"Code": "ListenerNotFound"}}

        @ELBv2ListenerErrorHandler.deletion_error_handler("delete listener")
        def raise_not_found():
            raise botocore.exceptions.ClientError(err_response, "DeleteListener")

        # deletion_error_handler should suppress ListenerNotFound
        result = raise_not_found()
        assert result is False


class TestELBv2RuleErrorHandler:
    """Test that ELBv2RuleErrorHandler raises the correct custom exception."""

    def test_raises_custom_exception(self):
        """Verify ELBv2RuleErrorHandler raises AnsibleELBv2Error on botocore errors."""
        err_response = {"Error": {"Code": "InvalidParameterValue"}}

        @ELBv2RuleErrorHandler.common_error_handler("test rule operation")
        def raise_client_error():
            raise botocore.exceptions.ClientError(err_response, "TestRuleOperation")

        with pytest.raises(AnsibleELBv2Error) as e_info:
            raise_client_error()

        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "test rule operation" in raised.message

    def test_handles_rule_not_found(self):
        """Verify _is_missing matches RuleNotFound error code."""
        err_response = {"Error": {"Code": "RuleNotFound"}}

        @ELBv2RuleErrorHandler.deletion_error_handler("delete rule")
        def raise_not_found():
            raise botocore.exceptions.ClientError(err_response, "DeleteRule")

        # deletion_error_handler should suppress RuleNotFound
        result = raise_not_found()
        assert result is False


class TestELBv2TargetGroupErrorHandler:
    """Test that ELBv2TargetGroupErrorHandler raises the correct custom exception."""

    def test_raises_custom_exception(self):
        """Verify ELBv2TargetGroupErrorHandler raises AnsibleELBv2Error on botocore errors."""
        err_response = {"Error": {"Code": "InvalidParameterValue"}}

        @ELBv2TargetGroupErrorHandler.common_error_handler("test target group operation")
        def raise_client_error():
            raise botocore.exceptions.ClientError(err_response, "TestTargetGroupOperation")

        with pytest.raises(AnsibleELBv2Error) as e_info:
            raise_client_error()

        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "test target group operation" in raised.message

    def test_handles_target_group_not_found(self):
        """Verify _is_missing matches TargetGroupNotFound error code."""
        err_response = {"Error": {"Code": "TargetGroupNotFound"}}

        @ELBv2TargetGroupErrorHandler.common_error_handler("describe target groups")
        def raise_not_found():
            raise botocore.exceptions.ClientError(err_response, "DescribeTargetGroups")

        # common_error_handler should raise AnsibleELBv2Error for TargetGroupNotFound
        with pytest.raises(AnsibleELBv2Error) as e_info:
            raise_not_found()

        raised = e_info.value
        assert isinstance(raised.exception, botocore.exceptions.ClientError)
        assert "describe target groups" in raised.message
