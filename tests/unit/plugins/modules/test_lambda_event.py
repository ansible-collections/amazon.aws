#
# (c) 2024 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from contextlib import nullcontext as does_not_raise
from copy import deepcopy
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.modules.lambda_event import get_qualifier
from ansible_collections.amazon.aws.plugins.modules.lambda_event import lambda_event_stream
from ansible_collections.amazon.aws.plugins.modules.lambda_event import set_default_values
from ansible_collections.amazon.aws.plugins.modules.lambda_event import validate_params

mock_get_qualifier = "ansible_collections.amazon.aws.plugins.modules.lambda_event.get_qualifier"
mock_camel_dict_to_snake_dict = "ansible_collections.amazon.aws.plugins.modules.lambda_event.camel_dict_to_snake_dict"


@pytest.fixture(name="ansible_aws_module")
def fixture_ansible_aws_module():
    module = MagicMock()
    module.check_mode = False
    module.params = {
        "state": "present",
        "lambda_function_arn": None,
        "event_source": "sqs",
        "source_params": {
            "source_arn": "arn:aws:sqs:us-east-2:123456789012:ansible-test-sqs",
            "batch_size": 200,
            "starting_position": "LATEST",
        },
        "alias": None,
        "version": 0,
    }
    module.exit_json = MagicMock()
    module.exit_json.side_effect = SystemExit(1)
    module.fail_json_aws = MagicMock()
    module.fail_json_aws.side_effect = SystemExit(2)
    module.fail_json = MagicMock()
    module.fail_json.side_effect = SystemExit(2)
    module.client = MagicMock()
    module.client.return_value = MagicMock()
    module.boolean = MagicMock()
    module.boolean.side_effect = lambda x: x.lower() in ["true", "1", "t", "y", "yes"]
    return module


@pytest.mark.parametrize(
    "module_params,expected",
    [
        ({"version": 1}, "1"),
        ({"alias": "ansible-test"}, "ansible-test"),
        ({"version": 1, "alias": "ansible-test"}, "1"),
        ({}, None),
    ],
)
def test_get_qualifier(ansible_aws_module, module_params, expected):
    ansible_aws_module.params.update(module_params)
    assert get_qualifier(ansible_aws_module) == expected


@pytest.mark.parametrize(
    "function_name,error_msg",
    [
        (
            "invalid+function+name",
            "Function name invalid+function+name is invalid. Names must contain only alphanumeric characters and hyphens.",
        ),
        (
            "this_invalid_function_name_has_more_than_64_character_limit_this_is_not_allowed_by_the_module",
            'Function name "this_invalid_function_name_has_more_than_64_character_limit_this_is_not_allowed_by_the_module" exceeds 64 character limit',
        ),
        (
            "arn:aws:lambda:us-east-2:123456789012:function:ansible-test-ansible-test-ansible-test-sqs-lambda-function:"
            "ansible-test-ansible-test-ansible-test-sqs-lambda-function-alias",
            'ARN "arn:aws:lambda:us-east-2:123456789012:function:ansible-test-ansible-test-ansible-test-sqs-lambda-function:'
            'ansible-test-ansible-test-ansible-test-sqs-lambda-function-alias" exceeds 140 character limit',
        ),
    ],
)
def test_validate_params_function_name_errors(ansible_aws_module, function_name, error_msg):
    ansible_aws_module.params.update({"lambda_function_arn": function_name})
    client = MagicMock()
    client.get_function = MagicMock()
    client.get_function.return_value = {}
    with pytest.raises(SystemExit):
        validate_params(ansible_aws_module, client)

    ansible_aws_module.fail_json.assert_called_once_with(msg=error_msg)


@pytest.mark.parametrize(
    "qualifier",
    [None, "ansible-test"],
)
@patch(mock_get_qualifier)
def test_validate_params_with_function_arn(m_get_qualifier, ansible_aws_module, qualifier):
    function_name = "arn:aws:lambda:us-east-2:123456789012:function:sqs_consumer"
    ansible_aws_module.params.update({"lambda_function_arn": function_name})
    m_get_qualifier.return_value = qualifier

    client = MagicMock()
    client.get_function = MagicMock()
    client.get_function.return_value = {}

    params = deepcopy(ansible_aws_module.params)
    params["lambda_function_arn"] = f"{function_name}:{qualifier}" if qualifier else function_name

    validate_params(ansible_aws_module, client)
    assert params == ansible_aws_module.params
    m_get_qualifier.assert_called_once()


@pytest.mark.parametrize(
    "qualifier",
    [None, "ansible-test"],
)
@patch(mock_get_qualifier)
def test_validate_params_with_function_name(m_get_qualifier, ansible_aws_module, qualifier):
    function_arn = "arn:aws:lambda:us-east-2:123456789012:function:sqs_consumer"
    function_name = "sqs_consumer"
    ansible_aws_module.params.update({"lambda_function_arn": function_name})
    m_get_qualifier.return_value = qualifier

    client = MagicMock()
    client.get_function = MagicMock()
    client.get_function.return_value = {
        "Configuration": {"FunctionArn": function_arn},
    }

    params = deepcopy(ansible_aws_module.params)
    params["lambda_function_arn"] = function_arn

    validate_params(ansible_aws_module, client)

    assert params == ansible_aws_module.params
    m_get_qualifier.assert_called_once()
    api_params = {"FunctionName": function_name}
    if qualifier:
        api_params.update({"Qualifier": qualifier})
    client.get_function.assert_called_once_with(**api_params)


EventSourceMappings = [
    {
        "BatchSize": 10,
        "EventSourceArn": "arn:aws:sqs:us-east-2:123456789012:sqs_consumer",
        "FunctionArn": "arn:aws:lambda:us-east-2:123456789012:function:sqs_consumer",
        "LastModified": "2024-02-08T15:24:57.014000+01:00",
        "MaximumBatchingWindowInSeconds": 0,
        "State": "Enabled",
        "StateTransitionReason": "USER_INITIATED",
        "UUID": "3ab96d4c-b0c4-4885-87d0-f58cb9c0a4cc",
    }
]


@pytest.mark.parametrize(
    "check_mode",
    [True, False],
)
@pytest.mark.parametrize(
    "existing_event_source",
    [True, False],
)
@patch(mock_camel_dict_to_snake_dict)
def test_lambda_event_stream_with_state_absent(
    m_camel_dict_to_snake_dict, ansible_aws_module, check_mode, existing_event_source
):
    function_name = "sqs_consumer"
    ansible_aws_module.params.update({"lambda_function_arn": function_name, "state": "absent"})
    ansible_aws_module.check_mode = check_mode

    client = MagicMock()
    client.list_event_source_mappings = MagicMock()

    client.list_event_source_mappings.return_value = {
        "EventSourceMappings": EventSourceMappings if existing_event_source else []
    }
    client.delete_event_source_mapping = MagicMock()
    event_source_deleted = {"msg": "event source successfully deleted."}
    client.delete_event_source_mapping.return_value = event_source_deleted
    m_camel_dict_to_snake_dict.side_effect = lambda x: x

    events = []
    changed = False
    result = lambda_event_stream(ansible_aws_module, client)
    changed = existing_event_source
    if existing_event_source:
        events = EventSourceMappings
        if not check_mode:
            events = event_source_deleted
            client.delete_event_source_mapping.assert_called_once_with(UUID=EventSourceMappings[0]["UUID"])
    else:
        client.delete_event_source_mapping.assert_not_called()
    assert dict(changed=changed, events=events) == result


def test_lambda_event_stream_create_event_missing_starting_position(ansible_aws_module):
    ansible_aws_module.params = {
        "state": "present",
        "lambda_function_arn": "sqs_consumer",
        "event_source": "stream",
        "source_params": {
            "source_arn": "arn:aws:sqs:us-east-2:123456789012:ansible-test-sqs",
            "maximum_batching_window_in_seconds": 1,
            "batch_size": 200,
        },
        "alias": None,
        "version": 0,
    }

    client = MagicMock()
    client.list_event_source_mappings = MagicMock()
    client.list_event_source_mappings.return_value = {"EventSourceMappings": []}

    error_message = "Source parameter 'starting_position' is required for stream event notification."
    with pytest.raises(SystemExit):
        lambda_event_stream(ansible_aws_module, client)
    ansible_aws_module.fail_json.assert_called_once_with(msg=error_message)


@pytest.mark.parametrize(
    "check_mode",
    [True, False],
)
@pytest.mark.parametrize(
    "module_params,api_params",
    [
        (
            {
                "state": "present",
                "lambda_function_arn": "sqs_consumer",
                "event_source": "stream",
                "source_params": {
                    "source_arn": "arn:aws:sqs:us-east-2:123456789012:ansible-test-sqs",
                    "maximum_batching_window_in_seconds": 1,
                    "batch_size": 250,
                    "starting_position": "END",
                    "function_response_types": ["ReportBatchItemFailures"],
                },
                "alias": None,
                "version": 0,
            },
            {
                "FunctionName": "sqs_consumer",
                "EventSourceArn": "arn:aws:sqs:us-east-2:123456789012:ansible-test-sqs",
                "StartingPosition": "END",
                "Enabled": True,
                "MaximumBatchingWindowInSeconds": 1,
                "BatchSize": 250,
                "FunctionResponseTypes": ["ReportBatchItemFailures"],
            },
        ),
        (
            {
                "state": "present",
                "lambda_function_arn": "sqs_consumer",
                "event_source": "stream",
                "source_params": {
                    "source_arn": "arn:aws:sqs:us-east-2:123456789012:ansible-test-sqs",
                    "maximum_batching_window_in_seconds": 1,
                    "batch_size": 250,
                    "starting_position": "END",
                    "function_response_types": ["ReportBatchItemFailures"],
                    "enabled": "no",
                },
                "alias": None,
                "version": 0,
            },
            {
                "FunctionName": "sqs_consumer",
                "EventSourceArn": "arn:aws:sqs:us-east-2:123456789012:ansible-test-sqs",
                "StartingPosition": "END",
                "Enabled": False,
                "MaximumBatchingWindowInSeconds": 1,
                "BatchSize": 250,
                "FunctionResponseTypes": ["ReportBatchItemFailures"],
            },
        ),
        (
            {
                "state": "present",
                "lambda_function_arn": "sqs_consumer",
                "event_source": "sqs",
                "source_params": {
                    "source_arn": "arn:aws:sqs:us-east-2:123456789012:ansible-test-sqs",
                    "maximum_batching_window_in_seconds": 1,
                    "batch_size": 101,
                },
                "alias": None,
                "version": 0,
            },
            {
                "FunctionName": "sqs_consumer",
                "EventSourceArn": "arn:aws:sqs:us-east-2:123456789012:ansible-test-sqs",
                "Enabled": True,
                "MaximumBatchingWindowInSeconds": 1,
                "BatchSize": 101,
            },
        ),
    ],
)
@patch(mock_camel_dict_to_snake_dict)
def test_lambda_event_stream_create_event(
    m_camel_dict_to_snake_dict, ansible_aws_module, check_mode, module_params, api_params
):
    ansible_aws_module.params = module_params
    ansible_aws_module.check_mode = check_mode

    client = MagicMock()
    client.list_event_source_mappings = MagicMock()
    client.list_event_source_mappings.return_value = {"EventSourceMappings": []}

    client.create_event_source_mapping = MagicMock()
    event_source_created = {"msg": "event source successfully created."}
    client.create_event_source_mapping.return_value = event_source_created
    m_camel_dict_to_snake_dict.side_effect = lambda x: x

    result = lambda_event_stream(ansible_aws_module, client)

    events = []

    if not check_mode:
        events = event_source_created
        client.create_event_source_mapping.assert_called_once_with(**api_params)
    else:
        client.create_event_source_mapping.assert_not_called()

    assert dict(changed=True, events=events) == result


@pytest.mark.parametrize(
    "check_mode",
    [True, False],
)
@pytest.mark.parametrize(
    "module_source_params,current_mapping,api_params",
    [
        (
            {"batch_size": 100, "enabled": "false"},
            {"BatchSize": 120, "State": "Enabled"},
            {"BatchSize": 100, "Enabled": False},
        ),
        (
            {"batch_size": 100, "enabled": "true"},
            {"BatchSize": 100, "State": "Enabled"},
            {},
        ),
    ],
)
@patch(mock_camel_dict_to_snake_dict)
def test_lambda_event_stream_update_event(
    m_camel_dict_to_snake_dict, ansible_aws_module, check_mode, module_source_params, current_mapping, api_params
):
    function_name = "ansible-test-update-event-function"
    ansible_aws_module.params.update({"lambda_function_arn": function_name})
    ansible_aws_module.params["source_params"].update(module_source_params)
    ansible_aws_module.check_mode = check_mode

    client = MagicMock()
    client.list_event_source_mappings = MagicMock()
    existing_event_source = deepcopy(EventSourceMappings)
    existing_event_source[0].update(current_mapping)
    client.list_event_source_mappings.return_value = {"EventSourceMappings": existing_event_source}

    client.update_event_source_mapping = MagicMock()
    event_source_updated = {"msg": "event source successfully updated."}
    client.update_event_source_mapping.return_value = event_source_updated
    m_camel_dict_to_snake_dict.side_effect = lambda x: x

    result = lambda_event_stream(ansible_aws_module, client)
    if not api_params:
        assert dict(changed=False, events=existing_event_source) == result
        client.update_event_source_mapping.assert_not_called()
    elif check_mode:
        assert dict(changed=True, events=existing_event_source) == result
        client.update_event_source_mapping.assert_not_called()
    else:
        api_params.update({"FunctionName": function_name, "UUID": existing_event_source[0]["UUID"]})
        assert dict(changed=True, events=event_source_updated) == result
        client.update_event_source_mapping.assert_called_once_with(**api_params)


@pytest.mark.parametrize(
    "params, expected, exception, message, source_type",
    [
        (
            {
                "source_arn": "arn:aws:sqs:us-east-1:123456789012:ansible-test-28277052.fifo",
                "enabled": True,
                "batch_size": 100,
                "starting_position": None,
                "function_response_types": None,
                "maximum_batching_window_in_seconds": None,
            },
            None,
            pytest.raises(SystemExit),
            "For FIFO queues the maximum batch_size is 10.",
            "sqs",
        ),
        (
            {
                "source_arn": "arn:aws:sqs:us-east-1:123456789012:ansible-test-28277052.fifo",
                "enabled": True,
                "batch_size": 10,
                "starting_position": None,
                "function_response_types": None,
                "maximum_batching_window_in_seconds": 1,
            },
            None,
            pytest.raises(SystemExit),
            "maximum_batching_window_in_seconds is not supported by Amazon SQS FIFO event sources.",
            "sqs",
        ),
        (
            {
                "source_arn": "arn:aws:sqs:us-east-1:123456789012:ansible-test-28277052.fifo",
                "enabled": True,
                "batch_size": 10,
                "starting_position": None,
                "function_response_types": None,
                "maximum_batching_window_in_seconds": None,
            },
            {
                "source_arn": "arn:aws:sqs:us-east-1:123456789012:ansible-test-28277052.fifo",
                "enabled": True,
                "batch_size": 10,
                "starting_position": None,
                "function_response_types": None,
                "maximum_batching_window_in_seconds": None,
            },
            does_not_raise(),
            None,
            "sqs",
        ),
        (
            {
                "source_arn": "arn:aws:sqs:us-east-1:123456789012:ansible-test-28277052",
                "enabled": True,
                "batch_size": 11000,
                "starting_position": None,
                "function_response_types": None,
                "maximum_batching_window_in_seconds": None,
            },
            None,
            pytest.raises(SystemExit),
            "For standard queue batch_size must be lower than 10000.",
            "sqs",
        ),
        (
            {
                "source_arn": "arn:aws:sqs:us-east-1:123456789012:ansible-test-28277052",
                "enabled": True,
                "batch_size": 100,
                "starting_position": None,
                "function_response_types": None,
                "maximum_batching_window_in_seconds": None,
            },
            {
                "source_arn": "arn:aws:sqs:us-east-1:123456789012:ansible-test-28277052",
                "enabled": True,
                "batch_size": 100,
                "starting_position": None,
                "function_response_types": None,
                "maximum_batching_window_in_seconds": 1,
            },
            does_not_raise(),
            None,
            "sqs",
        ),
        (
            {
                "source_arn": "arn:aws:sqs:us-east-1:123456789012:ansible-test-28277052",
                "enabled": True,
                "starting_position": None,
                "function_response_types": None,
                "maximum_batching_window_in_seconds": None,
            },
            {
                "source_arn": "arn:aws:sqs:us-east-1:123456789012:ansible-test-28277052",
                "enabled": True,
                "batch_size": 100,
                "starting_position": None,
                "function_response_types": None,
                "maximum_batching_window_in_seconds": 1,
            },
            does_not_raise(),
            None,
            "stream",
        ),
        (
            {
                "source_arn": "arn:aws:sqs:us-east-1:123456789012:ansible-test-28277052",
                "enabled": True,
                "starting_position": None,
                "function_response_types": None,
            },
            {
                "source_arn": "arn:aws:sqs:us-east-1:123456789012:ansible-test-28277052",
                "enabled": True,
                "batch_size": 10,
                "starting_position": None,
                "function_response_types": None,
            },
            does_not_raise(),
            None,
            "sqs",
        ),
        (
            {
                "source_arn": "arn:aws:sqs:us-east-1:123456789012:ansible-test-28277052",
                "enabled": True,
                "batch_size": 10,
                "starting_position": None,
                "function_response_types": None,
                "maximum_batching_window_in_seconds": None,
            },
            None,
            pytest.raises(SystemExit),
            "batch_size for streams must be between 100 and 10000",
            "stream",
        ),
    ],
)
def test__set_default_values(params, expected, exception, message, source_type):
    result = None
    module = MagicMock()
    module.check_mode = False
    module.params = {
        "event_source": source_type,
        "source_params": params,
    }
    module.fail_json = MagicMock()
    module.fail_json.side_effect = SystemExit(message)
    with exception as e:
        result = set_default_values(module, params)
    assert message is None or message in str(e)
    if expected is not None:
        assert result == expected
