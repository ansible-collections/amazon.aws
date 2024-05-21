# (c) 2017 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.plugins.module_utils.botocore import boto_exception
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.retries import RetryingBotoClientWrapper
from ansible_collections.amazon.aws.plugins.modules import cloudformation as cfn_module

# isort: off
# Magic...
# pylint: disable-next=unused-import
from ansible_collections.amazon.aws.tests.unit.utils.amazon_placebo_fixtures import maybe_sleep

# pylint: disable-next=unused-import
from ansible_collections.amazon.aws.tests.unit.utils.amazon_placebo_fixtures import placeboify

# isort: on

basic_yaml_tpl = """
---
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Basic template that creates an S3 bucket'
Resources:
  MyBucket:
    Type: "AWS::S3::Bucket"
Outputs:
  TheName:
    Value:
      !Ref MyBucket
"""

bad_json_tpl = """{
  "AWSTemplateFormatVersion": "2010-09-09",
  "Description": "Broken template, no comma here ->"
  "Resources": {
    "MyBucket": {
      "Type": "AWS::S3::Bucket"
    }
  }
}"""

failing_yaml_tpl = """
---
AWSTemplateFormatVersion: 2010-09-09
Resources:
  ECRRepo:
    Type: AWS::ECR::Repository
    Properties:
      RepositoryPolicyText:
        Version: 3000-10-17 # <--- invalid version
        Statement:
          - Effect: Allow
            Action:
              - 'ecr:*'
            Principal:
              AWS: !Sub arn:${AWS::Partition}:iam::${AWS::AccountId}:root
"""

default_events_limit = 10


class FakeModule:
    def __init__(self, **kwargs):
        self.params = kwargs

    def fail_json(self, *args, **kwargs):
        self.exit_args = args
        self.exit_kwargs = kwargs
        raise Exception("FAIL")

    def fail_json_aws(self, *args, **kwargs):
        self.exit_args = args
        self.exit_kwargs = kwargs
        raise Exception("FAIL")

    def exit_json(self, *args, **kwargs):
        self.exit_args = args
        self.exit_kwargs = kwargs
        raise Exception("EXIT")


def _create_wrapped_client(placeboify):
    connection = placeboify.client("cloudformation")
    retry_decorator = AWSRetry.jittered_backoff()
    wrapped_conn = RetryingBotoClientWrapper(connection, retry_decorator)
    return wrapped_conn


def test_invalid_template_json(placeboify):
    connection = _create_wrapped_client(placeboify)
    params = {
        "StackName": "ansible-test-wrong-json",
        "TemplateBody": bad_json_tpl,
    }
    m = FakeModule(disable_rollback=False)
    with pytest.raises(Exception) as exc_info:
        cfn_module.create_stack(m, params, connection, default_events_limit)
        pytest.fail("Expected malformed JSON to have caused the call to fail")

    assert exc_info.match("FAIL")
    assert "ValidationError" in boto_exception(m.exit_args[0])


def test_client_request_token_s3_stack(maybe_sleep, placeboify):
    connection = _create_wrapped_client(placeboify)
    params = {
        "StackName": "ansible-test-client-request-token-yaml",
        "TemplateBody": basic_yaml_tpl,
        "ClientRequestToken": "3faf3fb5-b289-41fc-b940-44151828f6cf",
    }
    m = FakeModule(disable_rollback=False)
    result = cfn_module.create_stack(m, params, connection, default_events_limit)
    assert result["changed"]
    assert len(result["events"]) > 1
    # require that the final recorded stack state was CREATE_COMPLETE
    # events are retrieved newest-first, so 0 is the latest
    assert "CREATE_COMPLETE" in result["events"][0]
    connection.delete_stack(StackName="ansible-test-client-request-token-yaml")


def test_basic_s3_stack(maybe_sleep, placeboify):
    connection = _create_wrapped_client(placeboify)
    params = {"StackName": "ansible-test-basic-yaml", "TemplateBody": basic_yaml_tpl}
    m = FakeModule(disable_rollback=False)
    result = cfn_module.create_stack(m, params, connection, default_events_limit)
    assert result["changed"]
    assert len(result["events"]) > 1
    # require that the final recorded stack state was CREATE_COMPLETE
    # events are retrieved newest-first, so 0 is the latest
    assert "CREATE_COMPLETE" in result["events"][0]
    connection.delete_stack(StackName="ansible-test-basic-yaml")


def test_delete_nonexistent_stack(maybe_sleep, placeboify):
    connection = _create_wrapped_client(placeboify)
    # module is only used if we threw an unexpected error
    module = None
    result = cfn_module.stack_operation(module, connection, "ansible-test-nonexist", "DELETE", default_events_limit)
    assert result["changed"]
    assert "Stack does not exist." in result["log"]


def test_get_nonexistent_stack(placeboify):
    connection = _create_wrapped_client(placeboify)
    # module is only used if we threw an unexpected error
    module = None
    assert cfn_module.get_stack_facts(module, connection, "ansible-test-nonexist") is None


def test_missing_template_body():
    m = FakeModule()
    with pytest.raises(Exception) as exc_info:
        cfn_module.create_stack(module=m, stack_params={}, cfn=None, events_limit=default_events_limit)
        pytest.fail("Expected module to have failed with no template")

    assert exc_info.match("FAIL")
    assert not m.exit_args
    assert (
        "Either 'template', 'template_body' or 'template_url' is required when the stack does not exist."
        == m.exit_kwargs["msg"]
    )


def test_on_create_failure_delete(maybe_sleep, placeboify):
    m = FakeModule(
        on_create_failure="DELETE",
        disable_rollback=False,
    )
    connection = _create_wrapped_client(placeboify)
    params = {"StackName": "ansible-test-on-create-failure-delete", "TemplateBody": failing_yaml_tpl}
    result = cfn_module.create_stack(m, params, connection, default_events_limit)
    assert result["changed"]
    assert result["failed"]
    assert len(result["events"]) > 1
    # require that the final recorded stack state was DELETE_COMPLETE
    # events are retrieved newest-first, so 0 is the latest
    assert "DELETE_COMPLETE" in result["events"][0]


def test_on_create_failure_rollback(maybe_sleep, placeboify):
    m = FakeModule(
        on_create_failure="ROLLBACK",
        disable_rollback=False,
    )
    connection = _create_wrapped_client(placeboify)
    params = {"StackName": "ansible-test-on-create-failure-rollback", "TemplateBody": failing_yaml_tpl}
    result = cfn_module.create_stack(m, params, connection, default_events_limit)
    assert result["changed"]
    assert result["failed"]
    assert len(result["events"]) > 1
    # require that the final recorded stack state was ROLLBACK_COMPLETE
    # events are retrieved newest-first, so 0 is the latest
    assert "ROLLBACK_COMPLETE" in result["events"][0]
    connection.delete_stack(StackName=params["StackName"])


def test_on_create_failure_do_nothing(maybe_sleep, placeboify):
    m = FakeModule(
        on_create_failure="DO_NOTHING",
        disable_rollback=False,
    )
    connection = _create_wrapped_client(placeboify)
    params = {"StackName": "ansible-test-on-create-failure-do-nothing", "TemplateBody": failing_yaml_tpl}
    result = cfn_module.create_stack(m, params, connection, default_events_limit)
    assert result["changed"]
    assert result["failed"]
    assert len(result["events"]) > 1
    # require that the final recorded stack state was CREATE_FAILED
    # events are retrieved newest-first, so 0 is the latest
    assert "CREATE_FAILED" in result["events"][0]
    connection.delete_stack(StackName=params["StackName"])
