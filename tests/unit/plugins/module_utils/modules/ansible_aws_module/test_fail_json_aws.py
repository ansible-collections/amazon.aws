# (c) 2020 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json

import pytest

try:
    import boto3
    import botocore
except ImportError:
    pass

from ansible.module_utils.ansible_release import __version__ as ANSIBLE_VERSION
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule


def _ansible_version_at_least(version_str):
    """Check if running ansible-core version is at least the specified version."""
    try:
        current = tuple(int(p) for p in ANSIBLE_VERSION.split(".")[:2])
        required = tuple(int(p) for p in version_str.split(".")[:2])
        return current >= required
    except Exception:
        return False


if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_fail_json_aws.py requires the python modules 'boto3' and 'botocore'")

# ansible-core >= 2.19 only reports a traceback (the `exception` field) when it
# has been enabled for the module. On the target side this is driven by the
# `_ansible_tracebacks_for` module argument rather than the controller-side
# ANSIBLE_DISPLAY_TRACEBACK setting. Older cores don't recognise this argument
# (it is rejected as an unsupported parameter) and always populate `exception`,
# so it must only be passed on ansible-core >= 2.19.
# See: https://github.com/ansible-collections/amazon.aws/issues/2929
TRACEBACK_ARGS = {"_ansible_tracebacks_for": ["error"]} if _ansible_version_at_least("2.19") else {}


class TestFailJsonAwsTestSuite:
    # ========================================================
    # Prepare some data for use in our testing
    # ========================================================
    def setup_method(self):
        # Basic information that ClientError needs to spawn off an error
        self.EXAMPLE_EXCEPTION_DATA = {
            "Error": {"Code": "InvalidParameterValue", "Message": "The filter 'exampleFilter' is invalid"},
            "ResponseMetadata": {
                "RequestId": "01234567-89ab-cdef-0123-456789abcdef",
                "HTTPStatusCode": 400,
                "HTTPHeaders": {
                    "transfer-encoding": "chunked",
                    "date": "Fri, 13 Nov 2020 00:00:00 GMT",
                    "connection": "close",
                    "server": "AmazonEC2",
                },
                "RetryAttempts": 0,
            },
        }
        self.CAMEL_RESPONSE = camel_dict_to_snake_dict(self.EXAMPLE_EXCEPTION_DATA.get("ResponseMetadata"))
        self.CAMEL_ERROR = camel_dict_to_snake_dict(self.EXAMPLE_EXCEPTION_DATA.get("Error"))
        # ClientError(EXAMPLE_EXCEPTION_DATA, "testCall") will generate this
        self.EXAMPLE_MSG = (
            "An error occurred (InvalidParameterValue) when calling the testCall operation: The filter 'exampleFilter'"
            " is invalid"
        )
        self.DEFAULT_CORE_MSG = "An unspecified error occurred"
        self.FAIL_MSG = "I Failed!"

    # ========================================================
    #   Passing fail_json_aws nothing more than a ClientError
    # ========================================================
    @pytest.mark.parametrize("stdin", [TRACEBACK_ARGS], indirect=["stdin"])
    def test_fail_client_minimal(self, monkeypatch, stdin, capfd):
        monkeypatch.setattr(botocore, "__version__", "1.2.3")
        monkeypatch.setattr(boto3, "__version__", "1.2.4")

        # Create a minimal module that we can call
        module = AnsibleAWSModule(argument_spec=dict())
        try:
            raise botocore.exceptions.ClientError(self.EXAMPLE_EXCEPTION_DATA, "testCall")
        except botocore.exceptions.ClientError as e:
            with pytest.raises(SystemExit) as ctx:
                module.fail_json_aws(e)
            assert ctx.value.code == 1
        out, _err = capfd.readouterr()
        return_val = json.loads(out)

        assert return_val.get("msg") == self.EXAMPLE_MSG
        assert return_val.get("boto3_version") == "1.2.4"
        assert return_val.get("botocore_version") == "1.2.3"
        assert return_val.get("failed")
        assert return_val.get("response_metadata") == self.CAMEL_RESPONSE
        assert return_val.get("error") == self.CAMEL_ERROR
        assert return_val.get("exception") is not None

    # ========================================================
    #   Passing fail_json_aws a ClientError and a message
    # ========================================================
    @pytest.mark.parametrize("stdin", [TRACEBACK_ARGS], indirect=["stdin"])
    def test_fail_client_msg(self, monkeypatch, stdin, capfd):
        monkeypatch.setattr(botocore, "__version__", "1.2.3")
        monkeypatch.setattr(boto3, "__version__", "1.2.4")

        # Create a minimal module that we can call
        module = AnsibleAWSModule(argument_spec=dict())
        try:
            raise botocore.exceptions.ClientError(self.EXAMPLE_EXCEPTION_DATA, "testCall")
        except botocore.exceptions.ClientError as e:
            with pytest.raises(SystemExit) as ctx:
                module.fail_json_aws(e, msg=self.FAIL_MSG)
            assert ctx.value.code == 1
        out, _err = capfd.readouterr()
        return_val = json.loads(out)

        assert return_val.get("msg") == self.FAIL_MSG + ": " + self.EXAMPLE_MSG
        assert return_val.get("boto3_version") == "1.2.4"
        assert return_val.get("botocore_version") == "1.2.3"
        assert return_val.get("failed")
        assert return_val.get("response_metadata") == self.CAMEL_RESPONSE
        assert return_val.get("error") == self.CAMEL_ERROR
        assert return_val.get("exception") is not None

    # ========================================================
    #   Passing fail_json_aws a ClientError and a message as a positional argument
    # ========================================================
    @pytest.mark.parametrize("stdin", [TRACEBACK_ARGS], indirect=["stdin"])
    def test_fail_client_positional_msg(self, monkeypatch, stdin, capfd):
        monkeypatch.setattr(botocore, "__version__", "1.2.3")
        monkeypatch.setattr(boto3, "__version__", "1.2.4")

        # Create a minimal module that we can call
        module = AnsibleAWSModule(argument_spec=dict())
        try:
            raise botocore.exceptions.ClientError(self.EXAMPLE_EXCEPTION_DATA, "testCall")
        except botocore.exceptions.ClientError as e:
            with pytest.raises(SystemExit) as ctx:
                module.fail_json_aws(e, self.FAIL_MSG)
            assert ctx.value.code == 1
        out, _err = capfd.readouterr()
        return_val = json.loads(out)

        assert return_val.get("msg") == self.FAIL_MSG + ": " + self.EXAMPLE_MSG
        assert return_val.get("boto3_version") == "1.2.4"
        assert return_val.get("botocore_version") == "1.2.3"
        assert return_val.get("failed")
        assert return_val.get("response_metadata") == self.CAMEL_RESPONSE
        assert return_val.get("error") == self.CAMEL_ERROR
        assert return_val.get("exception") is not None

    # ========================================================
    #   Passing fail_json_aws a ClientError and an arbitrary key
    # ========================================================
    @pytest.mark.parametrize("stdin", [TRACEBACK_ARGS], indirect=["stdin"])
    def test_fail_client_key(self, monkeypatch, stdin, capfd):
        monkeypatch.setattr(botocore, "__version__", "1.2.3")
        monkeypatch.setattr(boto3, "__version__", "1.2.4")

        # Create a minimal module that we can call
        module = AnsibleAWSModule(argument_spec=dict())
        try:
            raise botocore.exceptions.ClientError(self.EXAMPLE_EXCEPTION_DATA, "testCall")
        except botocore.exceptions.ClientError as e:
            with pytest.raises(SystemExit) as ctx:
                module.fail_json_aws(e, extra_key="Some Value")
            assert ctx.value.code == 1
        out, _err = capfd.readouterr()
        return_val = json.loads(out)

        assert return_val.get("msg") == self.EXAMPLE_MSG
        assert return_val.get("extra_key") == "Some Value"
        assert return_val.get("boto3_version") == "1.2.4"
        assert return_val.get("botocore_version") == "1.2.3"
        assert return_val.get("failed")
        assert return_val.get("response_metadata") == self.CAMEL_RESPONSE
        assert return_val.get("error") == self.CAMEL_ERROR
        assert return_val.get("exception") is not None

    # ========================================================
    #   Passing fail_json_aws a ClientError, and arbitraty key and a message
    # ========================================================
    @pytest.mark.parametrize("stdin", [TRACEBACK_ARGS], indirect=["stdin"])
    def test_fail_client_msg_and_key(self, monkeypatch, stdin, capfd):
        monkeypatch.setattr(botocore, "__version__", "1.2.3")
        monkeypatch.setattr(boto3, "__version__", "1.2.4")

        # Create a minimal module that we can call
        module = AnsibleAWSModule(argument_spec=dict())
        try:
            raise botocore.exceptions.ClientError(self.EXAMPLE_EXCEPTION_DATA, "testCall")
        except botocore.exceptions.ClientError as e:
            with pytest.raises(SystemExit) as ctx:
                module.fail_json_aws(e, extra_key="Some Value", msg=self.FAIL_MSG)
            assert ctx.value.code == 1
        out, _err = capfd.readouterr()
        return_val = json.loads(out)

        assert return_val.get("msg") == self.FAIL_MSG + ": " + self.EXAMPLE_MSG
        assert return_val.get("extra_key") == "Some Value"
        assert return_val.get("boto3_version") == "1.2.4"
        assert return_val.get("botocore_version") == "1.2.3"
        assert return_val.get("failed")
        assert return_val.get("response_metadata") == self.CAMEL_RESPONSE
        assert return_val.get("error") == self.CAMEL_ERROR
        assert return_val.get("exception") is not None

    # ========================================================
    #   Passing fail_json_aws nothing more than a BotoCoreError
    # ========================================================
    @pytest.mark.parametrize("stdin", [TRACEBACK_ARGS], indirect=["stdin"])
    def test_fail_botocore_minimal(self, monkeypatch, stdin, capfd):
        monkeypatch.setattr(botocore, "__version__", "1.2.3")
        monkeypatch.setattr(boto3, "__version__", "1.2.4")

        # Create a minimal module that we can call
        module = AnsibleAWSModule(argument_spec=dict())
        try:
            raise botocore.exceptions.BotoCoreError()
        except botocore.exceptions.BotoCoreError as e:
            with pytest.raises(SystemExit) as ctx:
                module.fail_json_aws(e)
            assert ctx.value.code == 1
        out, _err = capfd.readouterr()
        return_val = json.loads(out)

        assert return_val.get("msg") == self.DEFAULT_CORE_MSG
        assert return_val.get("boto3_version") == "1.2.4"
        assert return_val.get("botocore_version") == "1.2.3"
        assert return_val.get("failed")
        assert "response_metadata" not in return_val
        assert "error" not in return_val
        assert return_val.get("exception") is not None

    # ========================================================
    #   Passing fail_json_aws BotoCoreError and a message
    # ========================================================
    @pytest.mark.parametrize("stdin", [TRACEBACK_ARGS], indirect=["stdin"])
    def test_fail_botocore_msg(self, monkeypatch, stdin, capfd):
        monkeypatch.setattr(botocore, "__version__", "1.2.3")
        monkeypatch.setattr(boto3, "__version__", "1.2.4")

        # Create a minimal module that we can call
        module = AnsibleAWSModule(argument_spec=dict())
        try:
            raise botocore.exceptions.BotoCoreError()
        except botocore.exceptions.BotoCoreError as e:
            with pytest.raises(SystemExit) as ctx:
                module.fail_json_aws(e, msg=self.FAIL_MSG)
            assert ctx.value.code == 1
        out, _err = capfd.readouterr()
        return_val = json.loads(out)

        assert return_val.get("msg") == self.FAIL_MSG + ": " + self.DEFAULT_CORE_MSG
        assert return_val.get("boto3_version") == "1.2.4"
        assert return_val.get("botocore_version") == "1.2.3"
        assert return_val.get("failed")
        assert "response_metadata" not in return_val
        assert "error" not in return_val
        assert return_val.get("exception") is not None

    # ========================================================
    #   Passing fail_json_aws BotoCoreError and a message as a positional
    #   argument
    # ========================================================
    @pytest.mark.parametrize("stdin", [TRACEBACK_ARGS], indirect=["stdin"])
    def test_fail_botocore_positional_msg(self, monkeypatch, stdin, capfd):
        monkeypatch.setattr(botocore, "__version__", "1.2.3")
        monkeypatch.setattr(boto3, "__version__", "1.2.4")

        # Create a minimal module that we can call
        module = AnsibleAWSModule(argument_spec=dict())
        try:
            raise botocore.exceptions.BotoCoreError()
        except botocore.exceptions.BotoCoreError as e:
            with pytest.raises(SystemExit) as ctx:
                module.fail_json_aws(e, self.FAIL_MSG)
            assert ctx.value.code == 1
        out, _err = capfd.readouterr()
        return_val = json.loads(out)

        assert return_val.get("msg") == self.FAIL_MSG + ": " + self.DEFAULT_CORE_MSG
        assert return_val.get("boto3_version") == "1.2.4"
        assert return_val.get("botocore_version") == "1.2.3"
        assert return_val.get("failed")
        assert "response_metadata" not in return_val
        assert "error" not in return_val
        assert return_val.get("exception") is not None

    # ========================================================
    #   Passing fail_json_aws a BotoCoreError and an arbitrary key
    # ========================================================
    @pytest.mark.parametrize("stdin", [TRACEBACK_ARGS], indirect=["stdin"])
    def test_fail_botocore_key(self, monkeypatch, stdin, capfd):
        monkeypatch.setattr(botocore, "__version__", "1.2.3")
        monkeypatch.setattr(boto3, "__version__", "1.2.4")

        # Create a minimal module that we can call
        module = AnsibleAWSModule(argument_spec=dict())
        try:
            raise botocore.exceptions.BotoCoreError()
        except botocore.exceptions.BotoCoreError as e:
            with pytest.raises(SystemExit) as ctx:
                module.fail_json_aws(e, extra_key="Some Value")
            assert ctx.value.code == 1
        out, _err = capfd.readouterr()
        return_val = json.loads(out)

        assert return_val.get("msg") == self.DEFAULT_CORE_MSG
        assert return_val.get("extra_key") == "Some Value"
        assert return_val.get("boto3_version") == "1.2.4"
        assert return_val.get("botocore_version") == "1.2.3"
        assert return_val.get("failed")
        assert "response_metadata" not in return_val
        assert "error" not in return_val
        assert return_val.get("exception") is not None

    # ========================================================
    #   Passing fail_json_aws BotoCoreError, an arbitry key and a message
    # ========================================================
    @pytest.mark.parametrize("stdin", [TRACEBACK_ARGS], indirect=["stdin"])
    def test_fail_botocore_msg_and_key(self, monkeypatch, stdin, capfd):
        monkeypatch.setattr(botocore, "__version__", "1.2.3")
        monkeypatch.setattr(boto3, "__version__", "1.2.4")

        # Create a minimal module that we can call
        module = AnsibleAWSModule(argument_spec=dict())
        try:
            raise botocore.exceptions.BotoCoreError()
        except botocore.exceptions.BotoCoreError as e:
            with pytest.raises(SystemExit) as ctx:
                module.fail_json_aws(e, extra_key="Some Value", msg=self.FAIL_MSG)
            assert ctx.value.code == 1
        out, _err = capfd.readouterr()
        return_val = json.loads(out)

        assert return_val.get("msg") == self.FAIL_MSG + ": " + self.DEFAULT_CORE_MSG
        assert return_val.get("extra_key") == "Some Value"
        assert return_val.get("boto3_version") == "1.2.4"
        assert return_val.get("botocore_version") == "1.2.3"
        assert return_val.get("failed")
        assert "response_metadata" not in return_val
        assert "error" not in return_val
        assert return_val.get("exception") is not None
