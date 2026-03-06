# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import sentinel

import pytest
from botocore.exceptions import ClientError

import ansible_collections.amazon.aws.plugins.module_utils.exceptions as aws_exceptions


@pytest.fixture(name="utils_exceptions")
def fixture_utils_exceptions():
    return aws_exceptions


def test_with_kwargs(utils_exceptions):
    nested_exception = Exception(sentinel.EXCEPTION)
    with pytest.raises(utils_exceptions.AnsibleAWSError) as e:
        raise utils_exceptions.AnsibleAWSError(kw1=sentinel.KW1, kw2=sentinel.KW2)
    assert str(e.value) == ""
    assert e.value.exception is None
    assert e.value.message is None
    assert e.value.kwargs == dict(kw1=sentinel.KW1, kw2=sentinel.KW2)

    with pytest.raises(utils_exceptions.AnsibleAWSError) as e:
        raise utils_exceptions.AnsibleAWSError(
            message=sentinel.MESSAGE, exception=nested_exception, kw1=sentinel.KW1, kw2=sentinel.KW2
        )
    assert str(e.value) == "sentinel.MESSAGE: sentinel.EXCEPTION"
    assert e.value.exception is nested_exception
    assert e.value.message is sentinel.MESSAGE
    assert e.value.kwargs == dict(kw1=sentinel.KW1, kw2=sentinel.KW2)


def test_with_both(utils_exceptions):
    nested_exception = Exception(sentinel.EXCEPTION)

    with pytest.raises(utils_exceptions.AnsibleAWSError) as e:
        raise utils_exceptions.AnsibleAWSError(message=sentinel.MESSAGE, exception=nested_exception)
    assert str(e.value) == "sentinel.MESSAGE: sentinel.EXCEPTION"
    assert e.value.exception is nested_exception
    assert e.value.message is sentinel.MESSAGE
    assert e.value.kwargs == {}

    with pytest.raises(utils_exceptions.AnsibleAWSError) as e:
        raise utils_exceptions.AnsibleAWSError(sentinel.MESSAGE, exception=nested_exception)
    assert str(e.value) == "sentinel.MESSAGE: sentinel.EXCEPTION"
    assert e.value.exception is nested_exception
    assert e.value.message is sentinel.MESSAGE
    assert e.value.kwargs == {}


def test_with_exception(utils_exceptions):
    nested_exception = Exception(sentinel.EXCEPTION)

    with pytest.raises(utils_exceptions.AnsibleAWSError) as e:
        raise utils_exceptions.AnsibleAWSError(exception=nested_exception)
    assert str(e.value) == "sentinel.EXCEPTION"
    assert e.value.exception is nested_exception
    assert e.value.message is None
    assert e.value.kwargs == {}


def test_with_message(utils_exceptions):
    with pytest.raises(utils_exceptions.AnsibleAWSError) as e:
        raise utils_exceptions.AnsibleAWSError(message=sentinel.MESSAGE)
    assert str(e.value) == "sentinel.MESSAGE"
    assert e.value.exception is None
    assert e.value.message is sentinel.MESSAGE
    assert e.value.kwargs == {}

    with pytest.raises(utils_exceptions.AnsibleAWSError) as e:
        raise utils_exceptions.AnsibleAWSError(sentinel.MESSAGE)
    assert str(e.value) == "sentinel.MESSAGE"
    assert e.value.exception is None
    assert e.value.message is sentinel.MESSAGE
    assert e.value.kwargs == {}


def test_empty(utils_exceptions):
    with pytest.raises(utils_exceptions.AnsibleAWSError) as e:
        raise utils_exceptions.AnsibleAWSError()
    assert str(e.value) == ""
    assert e.value.exception is None
    assert e.value.message is None
    assert e.value.kwargs == {}


def test_inheritence(utils_exceptions):
    aws_exception = utils_exceptions.AnsibleAWSError()

    assert isinstance(aws_exception, Exception)
    assert isinstance(aws_exception, utils_exceptions.AnsibleAWSError)

    botocore_exception = utils_exceptions.AnsibleBotocoreError()

    assert isinstance(botocore_exception, Exception)
    assert isinstance(botocore_exception, utils_exceptions.AnsibleAWSError)
    assert isinstance(botocore_exception, utils_exceptions.AnsibleBotocoreError)


def _make_clienterror(code, message):
    """Helper to create a botocore ClientError exception."""
    params = {
        "Error": {"Code": code, "Message": message},
        "ResponseMetadata": {"RequestId": "01234567-89ab-cdef-0123-456789abcdef"},
    }
    return ClientError(params, "test_operation")


class TestIsAnsibleAwsErrorCode:
    """Test suite for is_ansible_aws_error_code() function."""

    def test_catch_matching_error_code(self, utils_exceptions):
        """Test that matching error codes are caught by is_ansible_aws_error_code."""
        client_error = _make_clienterror("IdempotentParameterMismatch", "Parameter mismatch")
        aws_error = utils_exceptions.AnsibleAWSError(exception=client_error)

        # Should catch the exception when error code matches
        caught = False
        try:
            raise aws_error
        except utils_exceptions.is_ansible_aws_error_code("IdempotentParameterMismatch"):
            caught = True

        assert caught

    def test_not_catch_non_matching_error_code(self, utils_exceptions):
        """Test that non-matching error codes pass through is_ansible_aws_error_code."""
        client_error = _make_clienterror("ResourceNotFound", "Resource not found")
        aws_error = utils_exceptions.AnsibleAWSError(exception=client_error)

        # Should not catch exception when error code doesn't match
        # pytest.raises verifies the exception propagates through the except clause
        with pytest.raises(utils_exceptions.AnsibleAWSError):
            try:
                raise aws_error
            except utils_exceptions.is_ansible_aws_error_code("IdempotentParameterMismatch"):
                pass

    def test_catch_code_from_list(self, utils_exceptions):
        """Test catching when error code is in a list of codes."""
        client_error = _make_clienterror("RouteAlreadyExists", "Route already exists")
        aws_error = utils_exceptions.AnsibleAWSError(exception=client_error)

        # Should catch when code is in the list
        caught = False
        try:
            raise aws_error
        except utils_exceptions.is_ansible_aws_error_code(["IdempotentParameterMismatch", "RouteAlreadyExists"]):
            caught = True

        assert caught

    def test_catch_code_from_tuple(self, utils_exceptions):
        """Test catching when error code is in a tuple."""
        client_error = _make_clienterror("AccessDenied", "Access denied")
        aws_error = utils_exceptions.AnsibleAWSError(exception=client_error)

        # Should catch when code is in the tuple
        caught = False
        try:
            raise aws_error
        except utils_exceptions.is_ansible_aws_error_code(("InvalidParameter", "AccessDenied")):
            caught = True

        assert caught

    def test_catch_code_from_set(self, utils_exceptions):
        """Test catching when error code is in a set."""
        client_error = _make_clienterror("Throttling", "Request throttled")
        aws_error = utils_exceptions.AnsibleAWSError(exception=client_error)

        # Should catch when code is in the set
        caught = False
        try:
            raise aws_error
        except utils_exceptions.is_ansible_aws_error_code({"InvalidParameter", "Throttling"}):
            caught = True

        assert caught

    def test_does_not_catch_regular_exception(self, utils_exceptions):
        """Test that non-AnsibleAWSError exceptions pass through."""
        regular_exception = ValueError("Some error")

        # Should not catch regular exceptions - verify they propagate
        with pytest.raises(ValueError):
            try:
                raise regular_exception
            except utils_exceptions.is_ansible_aws_error_code("SomeCode"):
                pass

    def test_does_not_catch_ansible_aws_error_without_client_error(self, utils_exceptions):
        """Test that AnsibleAWSError without ClientError passes through."""
        aws_error = utils_exceptions.AnsibleAWSError(message="Some error")

        # Should not catch AnsibleAWSError that doesn't wrap a ClientError
        with pytest.raises(utils_exceptions.AnsibleAWSError):
            try:
                raise aws_error
            except utils_exceptions.is_ansible_aws_error_code("SomeCode"):
                pass

    def test_returns_ansible_aws_error_class_on_match(self, utils_exceptions):
        """Test that matching returns AnsibleAWSError class."""
        client_error = _make_clienterror("InvalidParameter", "Invalid parameter")
        aws_error = utils_exceptions.AnsibleAWSError(exception=client_error)

        result = utils_exceptions.is_ansible_aws_error_code("InvalidParameter", aws_error)
        assert result is utils_exceptions.AnsibleAWSError

    def test_returns_dummy_exception_on_no_match(self, utils_exceptions):
        """Test that non-matching returns dummy exception class."""
        client_error = _make_clienterror("ResourceNotFound", "Resource not found")
        aws_error = utils_exceptions.AnsibleAWSError(exception=client_error)

        result = utils_exceptions.is_ansible_aws_error_code("InvalidParameter", aws_error)
        assert result is not utils_exceptions.AnsibleAWSError
        assert issubclass(result, Exception)
        assert result.__name__ == "NeverEverRaisedException"


class TestIsAnsibleAwsErrorMessage:
    """Test suite for is_ansible_aws_error_message() function."""

    def test_catch_matching_error_message(self, utils_exceptions):
        """Test that matching error messages are caught."""
        client_error = _make_clienterror(
            "VpcClassicLinkNotSupported", "The functionality you requested is not available in this region."
        )
        aws_error = utils_exceptions.AnsibleAWSError(exception=client_error)

        # Should catch when message matches
        caught = False
        try:
            raise aws_error
        except utils_exceptions.is_ansible_aws_error_message(
            "The functionality you requested is not available in this region."
        ):
            caught = True

        assert caught

    def test_catch_message_substring(self, utils_exceptions):
        """Test that substring matching works for error messages."""
        client_error = _make_clienterror(
            "VpcClassicLinkNotSupported", "The functionality you requested is not available in this region."
        )
        aws_error = utils_exceptions.AnsibleAWSError(exception=client_error)

        # Should catch when substring matches
        caught = False
        try:
            raise aws_error
        except utils_exceptions.is_ansible_aws_error_message("functionality you requested"):
            caught = True

        assert caught

    def test_not_catch_non_matching_message(self, utils_exceptions):
        """Test that non-matching messages pass through."""
        client_error = _make_clienterror("ResourceNotFound", "The specified resource does not exist")
        aws_error = utils_exceptions.AnsibleAWSError(exception=client_error)

        # Should not catch when message doesn't match - verify exception propagates
        with pytest.raises(utils_exceptions.AnsibleAWSError):
            try:
                raise aws_error
            except utils_exceptions.is_ansible_aws_error_message("access denied"):
                pass

    def test_case_sensitive_matching(self, utils_exceptions):
        """Test that message matching is case-sensitive."""
        client_error = _make_clienterror("AccessDenied", "Access Denied")
        aws_error = utils_exceptions.AnsibleAWSError(exception=client_error)

        # Should catch with correct case
        caught_correct_case = False
        try:
            raise aws_error
        except utils_exceptions.is_ansible_aws_error_message("Access Denied"):
            caught_correct_case = True

        assert caught_correct_case

        # Should not catch with different case - verify exception propagates
        client_error2 = _make_clienterror("AccessDenied", "Access Denied")
        aws_error2 = utils_exceptions.AnsibleAWSError(exception=client_error2)

        with pytest.raises(utils_exceptions.AnsibleAWSError):
            try:
                raise aws_error2
            except utils_exceptions.is_ansible_aws_error_message("access denied"):
                pass

    def test_does_not_catch_regular_exception(self, utils_exceptions):
        """Test that non-AnsibleAWSError exceptions pass through."""
        regular_exception = ValueError("Some error")

        # Should not catch regular exceptions - verify they propagate
        with pytest.raises(ValueError):
            try:
                raise regular_exception
            except utils_exceptions.is_ansible_aws_error_message("Some message"):
                pass

    def test_does_not_catch_ansible_aws_error_without_client_error(self, utils_exceptions):
        """Test that AnsibleAWSError without ClientError passes through."""
        aws_error = utils_exceptions.AnsibleAWSError(message="Some error")

        # Should not catch AnsibleAWSError that doesn't wrap a ClientError
        with pytest.raises(utils_exceptions.AnsibleAWSError):
            try:
                raise aws_error
            except utils_exceptions.is_ansible_aws_error_message("Some message"):
                pass

    def test_returns_ansible_aws_error_class_on_match(self, utils_exceptions):
        """Test that matching returns AnsibleAWSError class."""
        client_error = _make_clienterror("InvalidParameter", "Invalid parameter value")
        aws_error = utils_exceptions.AnsibleAWSError(exception=client_error)

        result = utils_exceptions.is_ansible_aws_error_message("Invalid parameter", aws_error)
        assert result is utils_exceptions.AnsibleAWSError

    def test_returns_dummy_exception_on_no_match(self, utils_exceptions):
        """Test that non-matching returns dummy exception class."""
        client_error = _make_clienterror("ResourceNotFound", "Resource not found")
        aws_error = utils_exceptions.AnsibleAWSError(exception=client_error)

        result = utils_exceptions.is_ansible_aws_error_message("access denied", aws_error)
        assert result is not utils_exceptions.AnsibleAWSError
        assert issubclass(result, Exception)
        assert result.__name__ == "NeverEverRaisedException"
