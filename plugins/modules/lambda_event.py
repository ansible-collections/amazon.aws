#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Pierre Jodouin <pjodouin@virtualcomputing.solutions>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: lambda_event
version_added: 5.0.0
short_description: Creates, updates or deletes AWS Lambda function event mappings
description:
  - This module allows the management of AWS Lambda function event source mappings such as DynamoDB and Kinesis stream
    events via the Ansible framework. These event source mappings are relevant only in the AWS Lambda pull model, where
    AWS Lambda invokes the function.
    It is idempotent and supports "Check" mode. Use module M(amazon.aws.lambda) to manage the lambda
    function itself and M(amazon.aws.lambda_alias) to manage function aliases.
  - This module was originally added to C(community.aws) in release 1.0.0.

author:
  - Pierre Jodouin (@pjodouin)
  - Ryan Brown (@ryansb)
options:
  lambda_function_arn:
    description:
      - The name or ARN of the lambda function.
    required: true
    aliases: ['function_name', 'function_arn']
    type: str
  state:
    description:
      - Describes the desired state.
    default: "present"
    choices: ["present", "absent"]
    type: str
  alias:
    description:
      - Name of the function alias.
      - Mutually exclusive with O(version).
    type: str
  version:
    description:
      - Version of the Lambda function.
      - Mutually exclusive with O(alias).
    type: int
    default: 0
  event_source:
    description:
      - Source of the event that triggers the lambda function.
      - For DynamoDB and Kinesis events, select V(stream).
      - For SQS queues, select V(sqs).
    default: stream
    choices: ['stream', 'sqs']
    type: str
  source_params:
    description:
      - Sub-parameters required for event source.
    suboptions:
      source_arn:
        description:
          - The Amazon Resource Name (ARN) of the SQS queue, Kinesis stream or DynamoDB stream that is the event source.
        type: str
        required: true
      enabled:
        description:
          - Indicates whether AWS Lambda should begin polling or readin from the event source.
        default: true
        type: bool
      batch_size:
        description:
          - The largest number of records that AWS Lambda will retrieve from your event source at the time of invoking your function.
          - Amazon Kinesis - Default V(100). Max V(10000).
          - Amazon DynamoDB Streams - Default V(100). Max V(10000).
          - Amazon Simple Queue Service - Default V(10). For standard queues the max is V(10000). For FIFO queues the max is V(10).
          - Amazon Managed Streaming for Apache Kafka - Default V(100). Max V(10000).
          - Self-managed Apache Kafka - Default C(100). Max V(10000).
          - Amazon MQ (ActiveMQ and RabbitMQ) - Default V(100). Max V(10000).
          - DocumentDB - Default V(100). Max V(10000).
        type: int
      starting_position:
        description:
          - The position in the stream where AWS Lambda should start reading.
          - Required when O(event_source=stream).
        choices: [TRIM_HORIZON,LATEST]
        type: str
      function_response_types:
        description:
          - (Streams and Amazon SQS) A list of current response type enums applied to the event source mapping.
        type: list
        elements: str
        choices: [ReportBatchItemFailures]
        version_added: 5.5.0
      maximum_batching_window_in_seconds:
        description:
          - The maximum amount of time, in seconds, that Lambda spends gathering records before invoking the function.
          - You can configure O(source_params.maximum_batching_window_in_seconds) to any value from V(0) seconds to V(300) seconds in increments of seconds.
          - For streams and Amazon SQS event sources, when O(source_params.batch_size) is set to a value greater than V(10),
            O(source_params.maximum_batching_window_in_seconds) defaults to V(1).
          - O(source_params.maximum_batching_window_in_seconds) is not supported by FIFO queues.
        type: int
        version_added: 8.0.0
    required: true
    type: dict
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Example that creates a lambda event notification for a DynamoDB stream
- name: DynamoDB stream event mapping
  amazon.aws.lambda_event:
    state: present
    event_source: stream
    function_name: "{{ function_name }}"
    alias: Dev
    source_params:
      source_arn: arn:aws:dynamodb:us-east-1:123456789012:table/tableName/stream/2016-03-19T19:51:37.457
      enabled: true
      batch_size: 100
      starting_position: TRIM_HORIZON
  register: event

# Example that creates a lambda event notification for a DynamoDB stream
- name: DynamoDB stream event mapping
  amazon.aws.lambda_event:
    state: present
    event_source: stream
    function_name: "{{ function_name }}"
    source_params:
      source_arn: arn:aws:dynamodb:us-east-1:123456789012:table/tableName/stream/2016-03-19T19:51:37.457
      enabled: true
      batch_size: 100
      starting_position: LATEST
      function_response_types:
        - ReportBatchItemFailures
  register: event

- name: Show source event
  ansible.builtin.debug:
    var: event.lambda_stream_events
"""

RETURN = r"""
---
events:
    description: Dictionary returned by the API describing stream event mappings
    returned: success
    type: dict
    contains:
      batch_size:
        description: The maximum number of records in each batch that Lambda pulls.
        type: int
        returned: always
      bisect_batch_on_function_error:
        description: If the function returns an error, split the batch in two and retry.
        type: bool
        returned: for Kinesis and DynamoDB Streams only
        sample: false
      destination_config:
        description: Configuration object that specifies the destination of an event after Lambda processes it.
        type: dict
        returned: For Kinesis, DynamoDB Streams, Amazon MSK, and self-managed Kafka only
        contains:
          on_failure:
            description: The destination configuration for failed invocations.
            type: dict
            contains:
              destination:
                description: Destination resource ARN.
                type: str
          on_success:
            description: The destination configuration for failed invocations.
            type: dict
            contains:
              destination:
                description: Destination resource ARN.
                type: str
      event_source_arn:
        description: The Amazon Resource Name (ARN) of the event source.
        type: str
        returned: always
        sample: "arn:aws:dynamodb:us-west-2:123456789012:table/yyyy/stream/2024-06-06T07:03:58.956"
      function_arn:
        description: The ARN of the Lambda function.
        type: str
        returned: always
        sample: "arn:aws:lambda:us-west-2:123456789012:function:test-lambda-3a0a29d0dbb5:1"
      function_response_types:
        description: A list of current response type enums applied to the event source mapping.
        type: list
        returned: For Kinesis, DynamoDB Streams, and Amazon SQS
        sample: ["ReportBatchItemFailures"]
      last_modified:
        description: The date that the event source mapping was last updated or that its state changed.
        type: str
        returned: always
        sample: "2024-06-06T12:34:21.990000+05:30"
      last_processing_result:
        description: The result of the last Lambda invocation of your function.
        type: str
        returned: always
        sample: "No records processed"
      maximum_batching_window_in_seconds:
        description: The maximum amount of time, in seconds, that Lambda spends gathering records before invoking the function.
        type: int
        returned: always
        sample: 1
      maximum_record_age_in_seconds:
        description: Discard records older than the specified age. The default value is infinite (-1).
        type: int
        returned: For Kinesis and DynamoDB Streams only
        sample: -1
      maximum_retry_attempts:
        description: Discard records after the specified number of retries.
        type: int
        returned: For Kinesis and DynamoDB Streams only
        sample: -1
      parallelization_factor:
        description: The number of batches to process concurrently from each shard.
        type: int
        returned: For Kinesis and DynamoDB Streams only
        sample: 1
      starting_position:
        description: The position in a stream from which to start reading.
        type: str
        returned: For Kinesis and DynamoDB Streams only
        sample: "LATEST"
      state:
        description: The state of the event source mapping.
        type: str
        returned: always
        sample: "deleting"
      state_transition_reason:
        description: Indicates whether a user or Lambda made the last change to the event source mapping.
        type: str
        returned: always
        sample: "USER_INITIATED"
      tumbling_window_in_seconds:
        description: The duration in seconds of a processing window for DynamoDB and Kinesis Streams event sources.
        type: int
        returned: For Kinesis and DynamoDB Streams only
        sample: 1
      uuid:
        description: The identifier of the event source mapping.
        type: str
        returned: always
        sample: "a1b2c3d4-5678-90ab-cdef-11111EXAMPLE"
"""

import copy
import re

try:
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
    from botocore.exceptions import MissingParametersError
    from botocore.exceptions import ParamValidationError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry

# ---------------------------------------------------------------------------------------------------
#
#   Helper Functions & classes
#
# ---------------------------------------------------------------------------------------------------


def validate_params(module, client):
    """
    Performs basic parameter validation.

    :param module: The AnsibleAWSModule object
    :param client: The client used to perform requests to AWS
    :return:
    """

    function_name = module.params["lambda_function_arn"]
    qualifier = get_qualifier(module)

    # validate function name
    if not re.search(r"^[\w\-:]+$", function_name):
        module.fail_json(
            msg=f"Function name {function_name} is invalid. Names must contain only alphanumeric characters and hyphens.",
        )

    # lamba_fuction_arn contains only the function name (not the arn)
    if not function_name.startswith("arn:aws:lambda:"):
        if len(function_name) > 64:
            module.fail_json(msg=f'Function name "{function_name}" exceeds 64 character limit')
        try:
            params = {"FunctionName": function_name}
            if qualifier:
                params["Qualifier"] = qualifier
            response = client.get_function(**params)
            module.params["lambda_function_arn"] = response["Configuration"]["FunctionArn"]
        except is_boto3_error_code("ResourceNotFoundException"):
            msg = f"An error occurred: The function '{function_name}' does not exist."
            if qualifier:
                msg = f"An error occurred: The function '{function_name}' (qualifier={qualifier}) does not exist."
            module.fail_json(msg=msg)
        except ClientError as e:  # pylint: disable=duplicate-except
            module.fail_json(msg=f"An error occurred while trying to describe function '{function_name}': {e}")
    else:
        if len(function_name) > 140:
            module.fail_json(msg=f'ARN "{function_name}" exceeds 140 character limit')

        if qualifier:
            module.params["lambda_function_arn"] = f"{function_name}:{qualifier}"


def get_qualifier(module):
    """
    Returns the function qualifier as a version or alias or None.

    :param module:
    :return:
    """

    qualifier = None
    if module.params["version"] > 0:
        qualifier = str(module.params["version"])
    elif module.params["alias"]:
        qualifier = str(module.params["alias"])

    return qualifier


# ---------------------------------------------------------------------------------------------------
#
#   Lambda Event Handlers
#
#   This section defines a lambda_event_X function where X is an AWS service capable of initiating
#   the execution of a Lambda function (pull only).
#
# ---------------------------------------------------------------------------------------------------


def set_default_values(module, source_params):
    _source_params_cpy = copy.deepcopy(source_params)

    if module.params["event_source"].lower() == "sqs":
        # Default 10. For standard queues the max is 10,000. For FIFO queues the max is 10.
        _source_params_cpy.setdefault("batch_size", 10)

        if source_params["source_arn"].endswith(".fifo"):
            if _source_params_cpy["batch_size"] > 10:
                module.fail_json(msg="For FIFO queues the maximum batch_size is 10.")
            if _source_params_cpy.get("maximum_batching_window_in_seconds"):
                module.fail_json(
                    msg="maximum_batching_window_in_seconds is not supported by Amazon SQS FIFO event sources."
                )
        else:
            if _source_params_cpy["batch_size"] >= 10000:
                module.fail_json(msg="For standard queue batch_size must be between lower than 10000.")

    elif module.params["event_source"].lower() == "stream":
        # Default 100.
        _source_params_cpy.setdefault("batch_size", 100)

        if not (100 <= _source_params_cpy["batch_size"] <= 10000):
            module.fail_json(msg="batch_size for streams must be between 100 and 10000")

    if _source_params_cpy["batch_size"] > 10 and not _source_params_cpy.get("maximum_batching_window_in_seconds"):
        _source_params_cpy["maximum_batching_window_in_seconds"] = 1

    return _source_params_cpy


def lambda_event_stream(module, client):
    """
    Adds, updates or deletes lambda stream (DynamoDb, Kinesis) event notifications.
    :param module:
    :param aws:
    :return:
    """

    facts = dict()
    changed = False
    current_state = "absent"
    state = module.params["state"]

    api_params = dict(FunctionName=module.params["lambda_function_arn"])

    # check if required sub-parameters are present and valid
    source_params = module.params["source_params"]

    source_arn = source_params.get("source_arn")
    if source_arn:
        api_params.update(EventSourceArn=source_arn)
    else:
        module.fail_json(msg="Source parameter 'source_arn' is required for stream event notification.")

    if state == "present":
        source_params = set_default_values(module, source_params)

    # optional boolean value needs special treatment as not present does not imply False
    source_param_enabled = module.boolean(source_params.get("enabled", "True"))

    # check if event mapping exist
    try:
        facts = client.list_event_source_mappings(**api_params)["EventSourceMappings"]
        if facts:
            current_state = "present"
    except ClientError as e:
        module.fail_json(msg=f"Error retrieving stream event notification configuration: {e}")

    if state == "present":
        if current_state == "absent":
            starting_position = source_params.get("starting_position")
            event_source = module.params.get("event_source")
            if event_source == "stream":
                if not starting_position:
                    module.fail_json(
                        msg="Source parameter 'starting_position' is required for stream event notification."
                    )
                api_params.update(StartingPosition=starting_position)

            api_params.update(Enabled=source_param_enabled)
            if source_params.get("batch_size"):
                api_params.update(BatchSize=source_params.get("batch_size"))
            if source_params.get("maximum_batching_window_in_seconds"):
                api_params.update(
                    MaximumBatchingWindowInSeconds=source_params.get("maximum_batching_window_in_seconds")
                )
            if source_params.get("function_response_types"):
                api_params.update(FunctionResponseTypes=source_params.get("function_response_types"))

            try:
                if not module.check_mode:
                    facts = client.create_event_source_mapping(**api_params)
                changed = True
            except (ClientError, ParamValidationError, MissingParametersError) as e:
                module.fail_json(msg=f"Error creating stream source event mapping: {e}")

        else:
            # current_state is 'present'
            current_mapping = facts[0]
            api_params = dict(FunctionName=module.params["lambda_function_arn"], UUID=current_mapping["UUID"])
            mapping_changed = False

            # check if anything changed
            if source_params.get("batch_size") and source_params["batch_size"] != current_mapping["BatchSize"]:
                api_params.update(BatchSize=source_params["batch_size"])
                mapping_changed = True

            if source_param_enabled is not None:
                if source_param_enabled:
                    if current_mapping["State"] not in ("Enabled", "Enabling"):
                        api_params.update(Enabled=True)
                        mapping_changed = True
                else:
                    if current_mapping["State"] not in ("Disabled", "Disabling"):
                        api_params.update(Enabled=False)
                        mapping_changed = True

            if mapping_changed:
                try:
                    if not module.check_mode:
                        facts = client.update_event_source_mapping(**api_params)
                    changed = True
                except (ClientError, ParamValidationError, MissingParametersError) as e:
                    module.fail_json(msg=f"Error updating stream source event mapping: {e}")

    else:
        if current_state == "present":
            # remove the stream event mapping
            api_params = dict(UUID=facts[0]["UUID"])

            try:
                if not module.check_mode:
                    facts = client.delete_event_source_mapping(**api_params)
                changed = True
            except (ClientError, ParamValidationError, MissingParametersError) as e:
                module.fail_json(msg=f"Error removing stream source event mapping: {e}")

    return camel_dict_to_snake_dict(dict(changed=changed, events=facts))


def main():
    """Produce a list of function suffixes which handle lambda events."""
    source_choices = ["stream", "sqs"]

    argument_spec = dict(
        state=dict(required=False, default="present", choices=["present", "absent"]),
        lambda_function_arn=dict(required=True, aliases=["function_name", "function_arn"]),
        event_source=dict(required=False, default="stream", choices=source_choices),
        source_params=dict(
            type="dict",
            required=True,
            options=dict(
                source_arn=dict(type="str", required=True),
                enabled=dict(type="bool", default=True),
                batch_size=dict(type="int"),
                starting_position=dict(type="str", choices=["TRIM_HORIZON", "LATEST"]),
                function_response_types=dict(type="list", elements="str", choices=["ReportBatchItemFailures"]),
                maximum_batching_window_in_seconds=dict(type="int"),
            ),
        ),
        alias=dict(required=False, default=None),
        version=dict(type="int", required=False, default=0),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[["alias", "version"]],
        required_together=[],
    )

    try:
        client = module.client("lambda", retry_decorator=AWSRetry.jittered_backoff())
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, msg="Trying to connect to AWS")

    validate_params(module, client)

    if module.params["event_source"].lower() in ("stream", "sqs"):
        results = lambda_event_stream(module, client)
    else:
        module.fail_json(msg="Please select `stream` or `sqs` as the event type")

    module.exit_json(**results)


if __name__ == "__main__":
    main()
