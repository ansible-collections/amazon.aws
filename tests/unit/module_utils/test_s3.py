#
# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
from operator import mod

__metaclass__ = type

from ansible_collections.amazon.aws.tests.unit.compat.mock import MagicMock
from ansible_collections.amazon.aws.plugins.module_utils import s3
from ansible.module_utils.basic import AnsibleModule
from unittest.mock import MagicMock, Mock, patch, ANY, call


class FakeAnsibleModule(AnsibleModule):
    def __init__(self):
        pass


def test_calculate_etag_single_part(tmp_path_factory):
    module = FakeAnsibleModule()
    my_image = tmp_path_factory.mktemp("data") / "my.txt"
    my_image.write_text("Hello World!")

    etag = s3.calculate_etag(
        module, str(my_image), etag="", s3=None, bucket=None, obj=None
    )
    assert etag == '"ed076287532e86365e841e92bfc50d8c"'


def test_calculate_etag_multi_part(tmp_path_factory):
    module = FakeAnsibleModule()
    my_image = tmp_path_factory.mktemp("data") / "my.txt"
    my_image.write_text("Hello World!" * 1000)

    mocked_s3 = MagicMock()
    mocked_s3.head_object.side_effect = [{"ContentLength": "1000"} for _i in range(12)]

    etag = s3.calculate_etag(
        module,
        str(my_image),
        etag='"f20e84ac3d0c33cea77b3f29e3323a09-12"',
        s3=mocked_s3,
        bucket="my-bucket",
        obj="my-obj",
    )
    assert etag == '"f20e84ac3d0c33cea77b3f29e3323a09-12"'
    mocked_s3.head_object.assert_called_with(
        Bucket="my-bucket", Key="my-obj", PartNumber=12
    )


def test_validate_bucket_name():
    module = MagicMock()

    assert s3.validate_bucket_name(module, "docexamplebucket1") is True
    assert not module.fail_json.called
    assert s3.validate_bucket_name(module, "log-delivery-march-2020") is True
    assert not module.fail_json.called
    assert s3.validate_bucket_name(module, "my-hosted-content") is True
    assert not module.fail_json.called

    assert s3.validate_bucket_name(module, "docexamplewebsite.com") is True
    assert not module.fail_json.called
    assert s3.validate_bucket_name(module, "www.docexamplewebsite.com") is True
    assert not module.fail_json.called
    assert s3.validate_bucket_name(module, "my.example.s3.bucket") is True
    assert not module.fail_json.called
    assert s3.validate_bucket_name(module, "doc") is True
    assert not module.fail_json.called

    module.fail_json.reset_mock()
    s3.validate_bucket_name(module, "doc_example_bucket")
    assert module.fail_json.called

    module.fail_json.reset_mock()
    s3.validate_bucket_name(module, "DocExampleBucket")
    assert module.fail_json.called
    module.fail_json.reset_mock()
    s3.validate_bucket_name(module, "doc-example-bucket-")
    assert module.fail_json.called
    s3.validate_bucket_name(module, "my")
    assert module.fail_json.called


def test_is_fakes3_with_none_arg():
    result = s3.is_fakes3(None)
    assert not result


def test_is_fakes3_with_valid_protocol():
    assert s3.is_fakes3("https://test-s3.amazon.com")


def test_is_fakes3_with_fakes3_protocol():
    assert s3.is_fakes3("fakes3://test-s3.amazon.com")


def test_is_fakes3_with_fakes3s_protocol():
    assert s3.is_fakes3("fakes3s://test-s3.amazon.com")


def test_get_s3_connection_ceph_with_https():
    aws_connect = dict(
        aws_access_key_id="ACCESS012345",
        aws_secret_access_key="SECRET123",
    )
    region = "us-east-1"
    s3_url = "https://test.ceph-s3.domain-name.com:8080"

    module = MagicMock()
    module.params = dict()
    # module.boto3_conn.return_value = True

    result = s3.get_s3_connection(
        module=module,
        aws_connect_kwargs=aws_connect,
        location=region,
        ceph=True,
        endpoint_url=s3_url
    )

    # print("Result MagicMock: {}".format(result))

    print("called: {}".format(module.called))
    print("method call_count: {}".format(module.boto3_conn.call_count))
    # print("call_args: {}".format(result.call_args))
    # print("mock_calls: {}".format(result.mock_calls))
    # print("call_args_list: {}".format(result.call_args_list))
    print("method_calls: {}".format(module.method_calls))
    # assert module.boto3_conn.assert_called_once()
    assert module.boto3_conn.assert_called_with(
        conn_type='client',
        resource='s3',
        region=region,
        endpoint=s3_url,
        use_ssl=True,
        **aws_connect
    )
