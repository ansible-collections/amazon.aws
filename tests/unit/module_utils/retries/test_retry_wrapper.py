# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import sentinel

import pytest

try:
    import botocore
except ImportError:
    pass

import ansible_collections.amazon.aws.plugins.module_utils.botocore as util_botocore
import ansible_collections.amazon.aws.plugins.module_utils.retries as util_retries


@pytest.fixture
def fake_client():
    retryable_response = {"Error": {"Code": "RequestLimitExceeded", "Message": "Something went wrong"}}
    retryable_exception = botocore.exceptions.ClientError(retryable_response, "fail_retryable")
    not_retryable_response = {"Error": {"Code": "AnotherProblem", "Message": "Something went wrong"}}
    not_retryable_exception = botocore.exceptions.ClientError(not_retryable_response, "fail_not_retryable")

    client = MagicMock()

    client.fail_retryable.side_effect = retryable_exception
    client.fail_not_retryable.side_effect = not_retryable_exception
    client.my_attribute = sentinel.ATTRIBUTE
    client.successful.return_value = sentinel.RETURNED_SUCCESSFUL

    return client


@pytest.fixture
def quick_backoff():
    # Because RetryingBotoClientWrapper will wrap resources using the this decorator,
    # we're going to rely on AWSRetry.jittered_backoff rather than trying to mock out
    # a decorator use a really short delay to keep the tests quick, and we only need
    # to actually retry once
    retry = util_retries.AWSRetry.jittered_backoff(retries=2, delay=0.1)
    return retry


def test_retry_wrapper_non_callable(fake_client, quick_backoff):
    wrapped_client = util_retries.RetryingBotoClientWrapper(fake_client, quick_backoff)

    # non-callable's shouldn't be wrapped, we should just get them back
    assert wrapped_client.my_attribute is sentinel.ATTRIBUTE


def test_retry_wrapper_callable(fake_client, quick_backoff):
    # Minimal test: not testing the aws_retry=True behaviour
    # (In general) callables should be wrapped
    wrapped_client = util_retries.RetryingBotoClientWrapper(fake_client, quick_backoff)

    assert isinstance(fake_client.fail_retryable, MagicMock)
    assert not isinstance(wrapped_client.fail_retryable, MagicMock)
    assert callable(wrapped_client.fail_retryable)
    with pytest.raises(botocore.exceptions.ClientError) as e:
        wrapped_client.fail_retryable()
    boto3_code = util_botocore.is_boto3_error_code("RequestLimitExceeded", e=e.value)
    boto3_message = util_botocore.is_boto3_error_message("Something went wrong", e=e.value)
    assert boto3_code is botocore.exceptions.ClientError
    assert boto3_message is botocore.exceptions.ClientError
    assert fake_client.fail_retryable.called
    assert fake_client.fail_retryable.call_count == 1

    assert isinstance(fake_client.fail_not_retryable, MagicMock)
    assert not isinstance(wrapped_client.fail_not_retryable, MagicMock)
    assert callable(wrapped_client.fail_not_retryable)
    with pytest.raises(botocore.exceptions.ClientError) as e:
        wrapped_client.fail_not_retryable()
    boto3_code = util_botocore.is_boto3_error_code("AnotherProblem", e=e.value)
    boto3_message = util_botocore.is_boto3_error_message("Something went wrong", e=e.value)
    assert boto3_code is botocore.exceptions.ClientError
    assert boto3_message is botocore.exceptions.ClientError
    assert fake_client.fail_not_retryable.called
    assert fake_client.fail_not_retryable.call_count == 1

    assert isinstance(fake_client.successful, MagicMock)
    assert not isinstance(wrapped_client.successful, MagicMock)
    assert callable(fake_client.successful)
    assert wrapped_client.successful() is sentinel.RETURNED_SUCCESSFUL
    assert fake_client.successful.called
    assert fake_client.successful.call_count == 1


def test_retry_wrapper_never_wrap(fake_client, quick_backoff):
    wrapped_client = util_retries.RetryingBotoClientWrapper(fake_client, quick_backoff)

    assert isinstance(fake_client.get_paginator, MagicMock)
    assert isinstance(wrapped_client.get_paginator, MagicMock)
    assert wrapped_client.get_paginator is fake_client.get_paginator


def test_retry_wrapper_no_retry_no_args(fake_client, quick_backoff):
    # Minimal test: not testing the aws_retry=True behaviour
    # (In general) callables should be wrapped
    wrapped_client = util_retries.RetryingBotoClientWrapper(fake_client, quick_backoff)
    call_args = call()

    assert isinstance(fake_client.fail_retryable, MagicMock)
    assert not isinstance(wrapped_client.fail_retryable, MagicMock)
    assert callable(wrapped_client.fail_retryable)
    with pytest.raises(botocore.exceptions.ClientError) as e:
        wrapped_client.fail_retryable(aws_retry=False)
    boto3_code = util_botocore.is_boto3_error_code("RequestLimitExceeded", e=e.value)
    boto3_message = util_botocore.is_boto3_error_message("Something went wrong", e=e.value)
    assert boto3_code is botocore.exceptions.ClientError
    assert boto3_message is botocore.exceptions.ClientError
    assert fake_client.fail_retryable.called
    assert fake_client.fail_retryable.call_count == 1
    assert fake_client.fail_retryable.call_args_list == [call_args]

    assert isinstance(fake_client.fail_not_retryable, MagicMock)
    assert not isinstance(wrapped_client.fail_not_retryable, MagicMock)
    assert callable(wrapped_client.fail_not_retryable)
    with pytest.raises(botocore.exceptions.ClientError) as e:
        wrapped_client.fail_not_retryable(aws_retry=False)
    boto3_code = util_botocore.is_boto3_error_code("AnotherProblem", e=e.value)
    boto3_message = util_botocore.is_boto3_error_message("Something went wrong", e=e.value)
    assert boto3_code is botocore.exceptions.ClientError
    assert boto3_message is botocore.exceptions.ClientError
    assert fake_client.fail_not_retryable.called
    assert fake_client.fail_not_retryable.call_count == 1
    assert fake_client.fail_not_retryable.call_args_list == [call_args]

    assert isinstance(fake_client.successful, MagicMock)
    assert not isinstance(wrapped_client.successful, MagicMock)
    assert callable(fake_client.successful)
    assert wrapped_client.successful(aws_retry=False) is sentinel.RETURNED_SUCCESSFUL
    assert fake_client.successful.called
    assert fake_client.successful.call_count == 1
    assert fake_client.successful.call_args_list == [call_args]


def test_retry_wrapper_retry_no_args(fake_client, quick_backoff):
    # Minimal test: not testing the aws_retry=True behaviour
    # (In general) callables should be wrapped
    wrapped_client = util_retries.RetryingBotoClientWrapper(fake_client, quick_backoff)
    call_args = call()

    assert isinstance(fake_client.fail_retryable, MagicMock)
    assert not isinstance(wrapped_client.fail_retryable, MagicMock)
    assert callable(wrapped_client.fail_retryable)
    with pytest.raises(botocore.exceptions.ClientError) as e:
        wrapped_client.fail_retryable(aws_retry=True)
    boto3_code = util_botocore.is_boto3_error_code("RequestLimitExceeded", e=e.value)
    boto3_message = util_botocore.is_boto3_error_message("Something went wrong", e=e.value)
    assert boto3_code is botocore.exceptions.ClientError
    assert boto3_message is botocore.exceptions.ClientError
    assert fake_client.fail_retryable.called
    assert fake_client.fail_retryable.call_count == 2
    assert fake_client.fail_retryable.call_args_list == [call_args, call_args]

    assert isinstance(fake_client.fail_not_retryable, MagicMock)
    assert not isinstance(wrapped_client.fail_not_retryable, MagicMock)
    assert callable(wrapped_client.fail_not_retryable)
    with pytest.raises(botocore.exceptions.ClientError) as e:
        wrapped_client.fail_not_retryable(aws_retry=True)
    boto3_code = util_botocore.is_boto3_error_code("AnotherProblem", e=e.value)
    boto3_message = util_botocore.is_boto3_error_message("Something went wrong", e=e.value)
    assert boto3_code is botocore.exceptions.ClientError
    assert boto3_message is botocore.exceptions.ClientError
    assert fake_client.fail_not_retryable.called
    assert fake_client.fail_not_retryable.call_count == 1
    assert fake_client.fail_not_retryable.call_args_list == [call_args]

    assert isinstance(fake_client.successful, MagicMock)
    assert not isinstance(wrapped_client.successful, MagicMock)
    assert callable(fake_client.successful)
    assert wrapped_client.successful(aws_retry=True) is sentinel.RETURNED_SUCCESSFUL
    assert fake_client.successful.called
    assert fake_client.successful.call_count == 1
    assert fake_client.successful.call_args_list == [call_args]


def test_retry_wrapper_no_retry_args(fake_client, quick_backoff):
    # Minimal test: not testing the aws_retry=True behaviour
    # (In general) callables should be wrapped
    wrapped_client = util_retries.RetryingBotoClientWrapper(fake_client, quick_backoff)
    args = [sentinel.ARG_1, sentinel.ARG_2]
    kwargs = {"kw1": sentinel.KWARG_1, "kw2": sentinel.KWARG_2}
    # aws_retry=False shouldn't be passed to the 'wrapped' call
    call_args = call(*args, **kwargs)

    assert isinstance(fake_client.fail_retryable, MagicMock)
    assert not isinstance(wrapped_client.fail_retryable, MagicMock)
    assert callable(wrapped_client.fail_retryable)
    with pytest.raises(botocore.exceptions.ClientError) as e:
        wrapped_client.fail_retryable(*args, aws_retry=False, **kwargs)
    boto3_code = util_botocore.is_boto3_error_code("RequestLimitExceeded", e=e.value)
    boto3_message = util_botocore.is_boto3_error_message("Something went wrong", e=e.value)
    assert boto3_code is botocore.exceptions.ClientError
    assert boto3_message is botocore.exceptions.ClientError
    assert fake_client.fail_retryable.called
    assert fake_client.fail_retryable.call_count == 1
    assert fake_client.fail_retryable.call_args_list == [call_args]

    assert isinstance(fake_client.fail_not_retryable, MagicMock)
    assert not isinstance(wrapped_client.fail_not_retryable, MagicMock)
    assert callable(wrapped_client.fail_not_retryable)
    with pytest.raises(botocore.exceptions.ClientError) as e:
        wrapped_client.fail_not_retryable(*args, aws_retry=False, **kwargs)
    boto3_code = util_botocore.is_boto3_error_code("AnotherProblem", e=e.value)
    boto3_message = util_botocore.is_boto3_error_message("Something went wrong", e=e.value)
    assert boto3_code is botocore.exceptions.ClientError
    assert boto3_message is botocore.exceptions.ClientError
    assert fake_client.fail_not_retryable.called
    assert fake_client.fail_not_retryable.call_count == 1
    assert fake_client.fail_not_retryable.call_args_list == [call_args]

    assert isinstance(fake_client.successful, MagicMock)
    assert not isinstance(wrapped_client.successful, MagicMock)
    assert callable(fake_client.successful)
    assert wrapped_client.successful(*args, aws_retry=False, **kwargs) is sentinel.RETURNED_SUCCESSFUL
    assert fake_client.successful.called
    assert fake_client.successful.call_count == 1
    assert fake_client.successful.call_args_list == [call_args]


def test_retry_wrapper_retry_no_args(fake_client, quick_backoff):
    # Minimal test: not testing the aws_retry=True behaviour
    # (In general) callables should be wrapped
    wrapped_client = util_retries.RetryingBotoClientWrapper(fake_client, quick_backoff)
    args = [sentinel.ARG_1, sentinel.ARG_2]
    kwargs = {"kw1": sentinel.KWARG_1, "kw2": sentinel.KWARG_2}
    # aws_retry=True shouldn't be passed to the 'wrapped' call
    call_args = call(*args, **kwargs)

    assert isinstance(fake_client.fail_retryable, MagicMock)
    assert not isinstance(wrapped_client.fail_retryable, MagicMock)
    assert callable(wrapped_client.fail_retryable)
    with pytest.raises(botocore.exceptions.ClientError) as e:
        wrapped_client.fail_retryable(*args, aws_retry=True, **kwargs)
    boto3_code = util_botocore.is_boto3_error_code("RequestLimitExceeded", e=e.value)
    boto3_message = util_botocore.is_boto3_error_message("Something went wrong", e=e.value)
    assert boto3_code is botocore.exceptions.ClientError
    assert boto3_message is botocore.exceptions.ClientError
    assert fake_client.fail_retryable.called
    assert fake_client.fail_retryable.call_count == 2
    assert fake_client.fail_retryable.call_args_list == [call_args, call_args]

    assert isinstance(fake_client.fail_not_retryable, MagicMock)
    assert not isinstance(wrapped_client.fail_not_retryable, MagicMock)
    assert callable(wrapped_client.fail_not_retryable)
    with pytest.raises(botocore.exceptions.ClientError) as e:
        wrapped_client.fail_not_retryable(*args, aws_retry=True, **kwargs)
    boto3_code = util_botocore.is_boto3_error_code("AnotherProblem", e=e.value)
    boto3_message = util_botocore.is_boto3_error_message("Something went wrong", e=e.value)
    assert boto3_code is botocore.exceptions.ClientError
    assert boto3_message is botocore.exceptions.ClientError
    assert fake_client.fail_not_retryable.called
    assert fake_client.fail_not_retryable.call_count == 1
    assert fake_client.fail_not_retryable.call_args_list == [call_args]

    assert isinstance(fake_client.successful, MagicMock)
    assert not isinstance(wrapped_client.successful, MagicMock)
    assert callable(fake_client.successful)
    assert wrapped_client.successful(*args, aws_retry=True, **kwargs) is sentinel.RETURNED_SUCCESSFUL
    assert fake_client.successful.called
    assert fake_client.successful.call_count == 1
    assert fake_client.successful.call_args_list == [call_args]
