# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest
from unittest.mock import sentinel

import ansible_collections.amazon.aws.plugins.module_utils.exceptions as aws_exceptions


@pytest.fixture
def utils_exceptions():
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
