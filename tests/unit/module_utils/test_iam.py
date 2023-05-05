#
# (c) 2020 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest
from unittest.mock import MagicMock

try:
    import botocore
except ImportError:
    # Handled by HAS_BOTO3
    pass

import ansible_collections.amazon.aws.plugins.module_utils.iam as utils_iam
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import HAS_BOTO3

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_iam.py requires the python modules 'boto3' and 'botocore'")


class TestIamUtils:
    def _make_denied_exception(self, partition):
        return botocore.exceptions.ClientError(
            {
                "Error": {
                    "Code": "AccessDenied",
                    "Message": (
                        "User: arn:"
                        + partition
                        + ":iam::123456789012:user/ExampleUser "
                        + "is not authorized to perform: iam:GetUser on resource: user ExampleUser"
                    ),
                },
                "ResponseMetadata": {"RequestId": "01234567-89ab-cdef-0123-456789abcdef"},
            },
            "getUser",
        )

    def _make_unexpected_exception(self):
        return botocore.exceptions.ClientError(
            {
                "Error": {"Code": "SomeThingWentWrong", "Message": "Boom!"},
                "ResponseMetadata": {"RequestId": "01234567-89ab-cdef-0123-456789abcdef"},
            },
            "someCall",
        )

    def _make_encoded_exception(self):
        return botocore.exceptions.ClientError(
            {
                "Error": {
                    "Code": "AccessDenied",
                    "Message": (
                        "You are not authorized to perform this operation. Encoded authorization failure message: "
                        + "fEwXX6llx3cClm9J4pURgz1XPnJPrYexEbrJcLhFkwygMdOgx_-aEsj0LqRM6Kxt2HVI6prUhDwbJqBo9U2V7iRKZ"
                        + "T6ZdJvHH02cXmD0Jwl5vrTsf0PhBcWYlH5wl2qME7xTfdolEUr4CzumCiti7ETiO-RDdHqWlasBOW5bWsZ4GSpPdU"
                        + "06YAX0TfwVBs48uU5RpCHfz1uhSzez-3elbtp9CmTOHLt5pzJodiovccO55BQKYLPtmJcs6S9YLEEogmpI4Cb1D26"
                        + "fYahDh51jEmaohPnW5pb1nQe2yPEtuIhtRzNjhFCOOMwY5DBzNsymK-Gj6eJLm7FSGHee4AHLU_XmZMe_6bcLAiOx"
                        + "6Zdl65Kdd0hLcpwVxyZMi27HnYjAdqRlV3wuCW2PkhAW14qZQLfiuHZDEwnPe2PBGSlFcCmkQvJvX-YLoA7Uyc2wf"
                        + "NX5RJm38STwfiJSkQaNDhHKTWKiLOsgY4Gze6uZoG7zOcFXFRyaA4cbMmI76uyBO7j-9uQUCtBYqYto8x_9CUJcxI"
                        + "VC5SPG_C1mk-WoDMew01f0qy-bNaCgmJ9TOQGd08FyuT1SaMpCC0gX6mHuOnEgkFw3veBIowMpp9XcM-yc42fmIOp"
                        + "FOdvQO6uE9p55Qc-uXvsDTTvT3A7EeFU8a_YoAIt9UgNYM6VTvoprLz7dBI_P6C-bdPPZCY2amm-dJNVZelT6TbJB"
                        + "H_Vxh0fzeiSUBersy_QzB0moc-vPWgnB-IkgnYLV-4L3K0L2"
                    ),
                },
                "ResponseMetadata": {"RequestId": "01234567-89ab-cdef-0123-456789abcdef"},
            },
            "someCall",
        )

    def _make_botocore_exception(self):
        return botocore.exceptions.EndpointConnectionError(endpoint_url="junk.endpoint")

    def setup_method(self):
        self.sts_client = MagicMock()
        self.iam_client = MagicMock()
        self.module = MagicMock()
        clients = {"sts": self.sts_client, "iam": self.iam_client}

        def get_client(*args, **kwargs):
            return clients[args[0]]

        self.module.client.side_effect = get_client
        self.module.fail_json_aws.side_effect = SystemExit(1)
        self.module.fail_json.side_effect = SystemExit(2)

    # ========== get_aws_account_id ============
    # This is just a minimal (compatibility) wrapper around get_aws_account_info
    # Perform some basic testing and call it a day.

    # Test the simplest case - We're permitted to call GetCallerIdentity
    def test_get_aws_account_id__caller_success(self):
        # Prepare
        self.sts_client.get_caller_identity.side_effect = [
            {
                "UserId": "AIDA12345EXAMPLE54321",
                "Account": "123456789012",
                "Arn": "arn:aws:iam::123456789012:user/ExampleUser",
            }
        ]
        # Run module
        return_value = utils_iam.get_aws_account_id(self.module)
        # Check we only saw the calls we mocked out
        self.module.client.assert_called_once()
        self.sts_client.get_caller_identity.assert_called_once()
        # Check we got the values back we expected.
        assert return_value == "123456789012"

    # Test the simplest case - We're permitted to call GetCallerIdentity
    # (China partition)
    def test_get_aws_account_id__caller_success_cn(self):
        # Prepare
        self.sts_client.get_caller_identity.side_effect = [
            {
                "UserId": "AIDA12345EXAMPLE54321",
                "Account": "123456789012",
                "Arn": "arn:aws-cn:iam::123456789012:user/ExampleUser",
            }
        ]
        # Run module
        return_value = utils_iam.get_aws_account_id(self.module)
        # Check we only saw the calls we mocked out
        self.module.client.assert_called_once()
        self.sts_client.get_caller_identity.assert_called_once()
        # Check we got the values back we expected.
        assert return_value == "123456789012"

    # ========== get_aws_account_info ============
    # Test the simplest case - We're permitted to call GetCallerIdentity
    def test_get_aws_account_info__caller_success(self):
        # Prepare
        self.sts_client.get_caller_identity.side_effect = [
            {
                "UserId": "AIDA12345EXAMPLE54321",
                "Account": "123456789012",
                "Arn": "arn:aws:iam::123456789012:user/ExampleUser",
            }
        ]
        # Run module
        return_value = utils_iam.get_aws_account_info(self.module)
        # Check we only saw the calls we mocked out
        self.module.client.assert_called_once()
        self.sts_client.get_caller_identity.assert_called_once()
        # Check we got the values back we expected.
        assert return_value == (
            "123456789012",
            "aws",
        )

    # (China partition)
    def test_get_aws_account_info__caller_success_cn(self):
        # Prepare
        self.sts_client.get_caller_identity.side_effect = [
            {
                "UserId": "AIDA12345EXAMPLE54321",
                "Account": "123456789012",
                "Arn": "arn:aws-cn:iam::123456789012:user/ExampleUser",
            }
        ]
        # Run module
        return_value = utils_iam.get_aws_account_info(self.module)
        # Check we only saw the calls we mocked out
        self.module.client.assert_called_once()
        self.sts_client.get_caller_identity.assert_called_once()
        # Check we got the values back we expected.
        assert return_value == (
            "123456789012",
            "aws-cn",
        )

    # (US-Gov partition)
    def test_get_aws_account_info__caller_success_gov(self):
        # Prepare
        self.sts_client.get_caller_identity.side_effect = [
            {
                "UserId": "AIDA12345EXAMPLE54321",
                "Account": "123456789012",
                "Arn": "arn:aws-us-gov:iam::123456789012:user/ExampleUser",
            }
        ]
        # Run module
        return_value = utils_iam.get_aws_account_info(self.module)
        # Check we only saw the calls we mocked out
        self.module.client.assert_called_once()
        self.sts_client.get_caller_identity.assert_called_once()
        # Check we got the values back we expected.
        assert return_value == (
            "123456789012",
            "aws-us-gov",
        )

    # If sts:get_caller_identity fails (most likely something wierd on the
    # client side), then try a few extra options.
    # Test response if STS fails and we need to fall back to GetUser
    def test_get_aws_account_info__user_success(self):
        # Prepare
        self.sts_client.get_caller_identity.side_effect = [self._make_botocore_exception()]
        self.iam_client.get_user.side_effect = [
            {
                "User": {
                    "Path": "/",
                    "UserName": "ExampleUser",
                    "UserId": "AIDA12345EXAMPLE54321",
                    "Arn": "arn:aws:iam::123456789012:user/ExampleUser",
                    "CreateDate": "2020-09-08T14:04:32Z",
                }
            }
        ]
        # Run module
        return_value = utils_iam.get_aws_account_info(self.module)
        # Check we only saw the calls we mocked out
        assert self.module.client.call_count == 2
        self.sts_client.get_caller_identity.assert_called_once()
        self.iam_client.get_user.assert_called_once()
        # Check we got the values back we expected.
        assert return_value == (
            "123456789012",
            "aws",
        )

    # (China partition)
    def test_get_aws_account_info__user_success_cn(self):
        # Prepare
        self.sts_client.get_caller_identity.side_effect = [self._make_botocore_exception()]
        self.iam_client.get_user.side_effect = [
            {
                "User": {
                    "Path": "/",
                    "UserName": "ExampleUser",
                    "UserId": "AIDA12345EXAMPLE54321",
                    "Arn": "arn:aws-cn:iam::123456789012:user/ExampleUser",
                    "CreateDate": "2020-09-08T14:04:32Z",
                }
            }
        ]
        # Run module
        return_value = utils_iam.get_aws_account_info(self.module)
        # Check we only saw the calls we mocked out
        assert self.module.client.call_count == 2
        self.sts_client.get_caller_identity.assert_called_once()
        self.iam_client.get_user.assert_called_once()
        # Check we got the values back we expected.
        assert return_value == (
            "123456789012",
            "aws-cn",
        )

    # (US-Gov partition)
    def test_get_aws_account_info__user_success_gov(self):
        # Prepare
        self.sts_client.get_caller_identity.side_effect = [self._make_botocore_exception()]
        self.iam_client.get_user.side_effect = [
            {
                "User": {
                    "Path": "/",
                    "UserName": "ExampleUser",
                    "UserId": "AIDA12345EXAMPLE54321",
                    "Arn": "arn:aws-us-gov:iam::123456789012:user/ExampleUser",
                    "CreateDate": "2020-09-08T14:04:32Z",
                }
            }
        ]
        # Run module
        return_value = utils_iam.get_aws_account_info(self.module)
        # Check we only saw the calls we mocked out
        assert self.module.client.call_count == 2
        self.sts_client.get_caller_identity.assert_called_once()
        self.iam_client.get_user.assert_called_once()
        # Check we got the values back we expected.
        assert return_value == (
            "123456789012",
            "aws-us-gov",
        )

    # Test response if STS and IAM fails and we need to fall back to the denial message
    def test_get_aws_account_info__user_denied(self):
        # Prepare
        self.sts_client.get_caller_identity.side_effect = [self._make_botocore_exception()]
        self.iam_client.get_user.side_effect = [self._make_denied_exception("aws")]
        # Run module
        return_value = utils_iam.get_aws_account_info(self.module)
        # Check we only saw the calls we mocked out
        assert self.module.client.call_count == 2
        self.sts_client.get_caller_identity.assert_called_once()
        self.iam_client.get_user.assert_called_once()
        # Check we got the values back we expected.
        assert return_value == (
            "123456789012",
            "aws",
        )

    # (China partition)
    def test_get_aws_account_info__user_denied_cn(self):
        # Prepare
        self.sts_client.get_caller_identity.side_effect = [self._make_botocore_exception()]
        self.iam_client.get_user.side_effect = [self._make_denied_exception("aws-cn")]
        # Run module
        return_value = utils_iam.get_aws_account_info(self.module)
        # Check we only saw the calls we mocked out
        assert self.module.client.call_count == 2
        self.sts_client.get_caller_identity.assert_called_once()
        self.iam_client.get_user.assert_called_once()
        # Check we got the values back we expected.
        assert return_value == (
            "123456789012",
            "aws-cn",
        )

    # (US-Gov partition)
    def test_get_aws_account_info__user_denied_gov(self):
        # Prepare
        self.sts_client.get_caller_identity.side_effect = [self._make_botocore_exception()]
        self.iam_client.get_user.side_effect = [self._make_denied_exception("aws-us-gov")]
        # Run module
        return_value = utils_iam.get_aws_account_info(self.module)
        # Check we only saw the calls we mocked out
        assert self.module.client.call_count == 2
        self.sts_client.get_caller_identity.assert_called_once()
        self.iam_client.get_user.assert_called_once()
        # Check we got the values back we expected.
        assert return_value == (
            "123456789012",
            "aws-us-gov",
        )

    # Test that we fail gracefully if Boto throws exceptions at us...
    def test_get_aws_account_info__boto_failures(self):
        # Prepare
        self.sts_client.get_caller_identity.side_effect = [self._make_botocore_exception()]
        self.iam_client.get_user.side_effect = [self._make_botocore_exception()]
        # Run module
        with pytest.raises(SystemExit) as e:
            utils_iam.get_aws_account_info(self.module)
        # Check we only saw the calls we mocked out
        assert self.module.client.call_count == 2
        self.sts_client.get_caller_identity.assert_called_once()
        self.iam_client.get_user.assert_called_once()
        # Check we got the values back we expected.
        assert e.type == SystemExit
        assert e.value.code == 1  # 1 == fail_json_aws

    def test_get_aws_account_info__client_failures(self):
        # Prepare
        self.sts_client.get_caller_identity.side_effect = [self._make_unexpected_exception()]
        self.iam_client.get_user.side_effect = [self._make_unexpected_exception()]
        # Run module
        with pytest.raises(SystemExit) as e:
            utils_iam.get_aws_account_info(self.module)
        # Check we only saw the calls we mocked out
        assert self.module.client.call_count == 2
        self.sts_client.get_caller_identity.assert_called_once()
        self.iam_client.get_user.assert_called_once()
        # Check we got the values back we expected.
        assert e.type == SystemExit
        assert e.value.code == 1  # 1 == fail_json_aws

    def test_get_aws_account_info__encoded_failures(self):
        # Prepare
        self.sts_client.get_caller_identity.side_effect = [self._make_encoded_exception()]
        self.iam_client.get_user.side_effect = [self._make_encoded_exception()]
        # Run module
        with pytest.raises(SystemExit) as e:
            utils_iam.get_aws_account_info(self.module)
        # Check we only saw the calls we mocked out
        assert self.module.client.call_count == 2
        self.sts_client.get_caller_identity.assert_called_once()
        self.iam_client.get_user.assert_called_once()
        # Check we got the values back we expected.
        assert e.type == SystemExit
        assert e.value.code == 1  # 1 == fail_json (we couldn't parse the AccessDenied errors)
