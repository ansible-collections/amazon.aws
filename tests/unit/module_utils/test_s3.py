#
# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import random
import string
from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

import pytest

from ansible_collections.amazon.aws.plugins.module_utils import s3

try:
    import botocore
except ImportError:
    pass


def generate_random_string(size, include_digits=True):
    buffer = string.ascii_lowercase
    if include_digits:
        buffer += string.digits

    return "".join(random.choice(buffer) for i in range(size))


@pytest.mark.parametrize("parts", range(0, 10, 3))
@pytest.mark.parametrize("version", [True, False])
def test_s3_head_objects(parts, version):
    client = MagicMock()

    s3bucket_name = f"s3-bucket-{generate_random_string(8, False)}"
    s3bucket_object = f"s3-bucket-object-{generate_random_string(8, False)}"
    versionId = None
    if version:
        versionId = random.randint(0, 1000)

    total = 0
    for head in s3.s3_head_objects(client, parts, s3bucket_name, s3bucket_object, versionId):
        assert head == client.head_object.return_value
        total += 1

    assert total == parts
    params = {"Bucket": s3bucket_name, "Key": s3bucket_object}
    if versionId:
        params["VersionId"] = versionId

    api_calls = [call(PartNumber=i, **params) for i in range(1, parts + 1)]
    client.head_object.assert_has_calls(api_calls, any_order=True)


def raise_botoclient_exception():
    params = {
        "Error": {"Code": 1, "Message": "Something went wrong"},
        "ResponseMetadata": {"RequestId": "01234567-89ab-cdef-0123-456789abcdef"},
    }
    return botocore.exceptions.ClientError(params, "some_called_method")


@pytest.mark.parametrize("use_file", [False, True])
@pytest.mark.parametrize("parts", range(0, 10, 3))
@patch("ansible_collections.amazon.aws.plugins.module_utils.s3.md5")
@patch("ansible_collections.amazon.aws.plugins.module_utils.s3.s3_head_objects")
def test_calculate_checksum(m_s3_head_objects, m_s3_md5, use_file, parts, tmp_path):
    client = MagicMock()
    mock_md5 = m_s3_md5.return_value

    mock_md5.digest.return_value = b"1"
    mock_md5.hexdigest.return_value = "".join(["f" for i in range(32)])

    m_s3_head_objects.return_value = [{"ContentLength": f"{int(i + 1)}"} for i in range(parts)]

    content = b'"f20e84ac3d0c33cea77b3f29e3323a09"'
    test_function = s3.calculate_checksum_with_content
    if use_file:
        test_function = s3.calculate_checksum_with_file
        test_dir = tmp_path / "test_s3"
        test_dir.mkdir()
        etag_file = test_dir / "etag.bin"
        etag_file.write_bytes(content)

        content = str(etag_file)

    s3bucket_name = f"s3-bucket-{generate_random_string(8, False)}"
    s3bucket_object = f"s3-bucket-object-{generate_random_string(8, False)}"
    version = random.randint(0, 1000)

    result = test_function(client, parts, s3bucket_name, s3bucket_object, version, content)

    expected = f'"{mock_md5.hexdigest.return_value}-{parts}"'
    assert result == expected

    mock_md5.digest.assert_has_calls([call() for i in range(parts)])
    mock_md5.hexdigest.assert_called_once()

    m_s3_head_objects.assert_called_once_with(client, parts, s3bucket_name, s3bucket_object, version)


@pytest.mark.parametrize("etag_multipart", [True, False])
@patch("ansible_collections.amazon.aws.plugins.module_utils.s3.calculate_checksum_with_file")
def test_calculate_etag(m_checksum_file, etag_multipart):
    module = MagicMock()
    client = MagicMock()

    module.fail_json_aws.side_effect = SystemExit(2)
    module.md5.return_value = generate_random_string(32)

    s3bucket_name = f"s3-bucket-{generate_random_string(8, False)}"
    s3bucket_object = f"s3-bucket-object-{generate_random_string(8, False)}"
    version = random.randint(0, 1000)
    parts = 3

    etag = '"f20e84ac3d0c33cea77b3f29e3323a09"'
    digest = '"9aa254f7f76fd14435b21e9448525b99"'

    file_name = generate_random_string(32)

    if not etag_multipart:
        result = s3.calculate_etag(module, file_name, etag, client, s3bucket_name, s3bucket_object, version)
        assert result == f'"{module.md5.return_value}"'
        module.md5.assert_called_once_with(file_name)
    else:
        etag = f'"f20e84ac3d0c33cea77b3f29e3323a09-{parts}"'
        m_checksum_file.return_value = digest
        assert digest == s3.calculate_etag(module, file_name, etag, client, s3bucket_name, s3bucket_object, version)

        m_checksum_file.assert_called_with(client, parts, s3bucket_name, s3bucket_object, version, file_name)


@pytest.mark.parametrize("etag_multipart", [True, False])
@patch("ansible_collections.amazon.aws.plugins.module_utils.s3.calculate_checksum_with_content")
def test_calculate_etag_content(m_checksum_content, etag_multipart):
    module = MagicMock()
    client = MagicMock()

    module.fail_json_aws.side_effect = SystemExit(2)

    s3bucket_name = f"s3-bucket-{generate_random_string(8, False)}"
    s3bucket_object = f"s3-bucket-object-{generate_random_string(8, False)}"
    version = random.randint(0, 1000)
    parts = 3

    etag = '"f20e84ac3d0c33cea77b3f29e3323a09"'
    content = b'"f20e84ac3d0c33cea77b3f29e3323a09"'
    digest = '"9aa254f7f76fd14435b21e9448525b99"'

    if not etag_multipart:
        assert digest == s3.calculate_etag_content(
            module, content, etag, client, s3bucket_name, s3bucket_object, version
        )
    else:
        etag = f'"f20e84ac3d0c33cea77b3f29e3323a09-{parts}"'
        m_checksum_content.return_value = digest
        result = s3.calculate_etag_content(module, content, etag, client, s3bucket_name, s3bucket_object, version)
        assert result == digest

        m_checksum_content.assert_called_with(client, parts, s3bucket_name, s3bucket_object, version, content)


@pytest.mark.parametrize("using_file", [True, False])
@patch("ansible_collections.amazon.aws.plugins.module_utils.s3.calculate_checksum_with_content")
@patch("ansible_collections.amazon.aws.plugins.module_utils.s3.calculate_checksum_with_file")
def test_calculate_etag_failure(m_checksum_file, m_checksum_content, using_file):
    module = MagicMock()
    client = MagicMock()

    module.fail_json_aws.side_effect = SystemExit(2)

    s3bucket_name = f"s3-bucket-{generate_random_string(8, False)}"
    s3bucket_object = f"s3-bucket-object-{generate_random_string(8, False)}"
    version = random.randint(0, 1000)
    parts = 3

    etag = f'"f20e84ac3d0c33cea77b3f29e3323a09-{parts}"'
    content = "some content or file name"

    if using_file:
        test_method = s3.calculate_etag
        m_checksum_file.side_effect = raise_botoclient_exception()
    else:
        test_method = s3.calculate_etag_content
        m_checksum_content.side_effect = raise_botoclient_exception()

    with pytest.raises(SystemExit):
        test_method(module, content, etag, client, s3bucket_name, s3bucket_object, version)
    module.fail_json_aws.assert_called()


@pytest.mark.parametrize(
    "bucket_name,result",
    [
        ("docexamplebucket1", None),
        ("log-delivery-march-2020", None),
        ("my-hosted-content", None),
        ("docexamplewebsite.com", None),
        ("www.docexamplewebsite.com", None),
        ("my.example.s3.bucket", None),
        ("doc", None),
        ("doc_example_bucket", "invalid character(s) found in the bucket name"),
        ("DocExampleBucket", "invalid character(s) found in the bucket name"),
        ("doc-example-bucket-", "bucket names must begin and end with a letter or number"),
        (
            "this.string.has.more.than.63.characters.so.it.should.not.passed.the.validated",
            "the length of an S3 bucket cannot exceed 63 characters",
        ),
        ("my", "the length of an S3 bucket must be at least 3 characters"),
    ],
)
def test_validate_bucket_name(bucket_name, result):
    assert result == s3.validate_bucket_name(bucket_name)


mod_urlparse = "ansible_collections.amazon.aws.plugins.module_utils.s3.urlparse"


class UrlInfo:
    def __init__(self, scheme=None, hostname=None, port=None):
        self.hostname = hostname
        self.scheme = scheme
        self.port = port


@patch(mod_urlparse)
def test_is_fakes3_with_none_arg(m_urlparse):
    m_urlparse.side_effect = SystemExit(1)
    result = s3.is_fakes3(None)
    assert not result
    m_urlparse.assert_not_called()


@pytest.mark.parametrize(
    "url,scheme,result",
    [
        ("https://test-s3.amazon.com", "https", False),
        ("fakes3://test-s3.amazon.com", "fakes3", True),
        ("fakes3s://test-s3.amazon.com", "fakes3s", True),
    ],
)
@patch(mod_urlparse)
def test_is_fakes3(m_urlparse, url, scheme, result):
    m_urlparse.return_value = UrlInfo(scheme=scheme)
    assert result == s3.is_fakes3(url)
    m_urlparse.assert_called_with(url)


@pytest.mark.parametrize(
    "url,urlinfo,endpoint",
    [
        (
            "fakes3://test-s3.amazon.com",
            {"scheme": "fakes3", "hostname": "test-s3.amazon.com"},
            {"endpoint": "http://test-s3.amazon.com:80", "use_ssl": False},
        ),
        (
            "fakes3://test-s3.amazon.com:8080",
            {"scheme": "fakes3", "hostname": "test-s3.amazon.com", "port": 8080},
            {"endpoint": "http://test-s3.amazon.com:8080", "use_ssl": False},
        ),
        (
            "fakes3s://test-s3.amazon.com",
            {"scheme": "fakes3s", "hostname": "test-s3.amazon.com"},
            {"endpoint": "https://test-s3.amazon.com:443", "use_ssl": True},
        ),
        (
            "fakes3s://test-s3.amazon.com:9096",
            {"scheme": "fakes3s", "hostname": "test-s3.amazon.com", "port": 9096},
            {"endpoint": "https://test-s3.amazon.com:9096", "use_ssl": True},
        ),
    ],
)
@patch(mod_urlparse)
def test_parse_fakes3_endpoint(m_urlparse, url, urlinfo, endpoint):
    m_urlparse.return_value = UrlInfo(**urlinfo)
    result = s3.parse_fakes3_endpoint(url)
    assert endpoint == result
    m_urlparse.assert_called_with(url)


@pytest.mark.parametrize(
    "url,scheme,use_ssl",
    [
        ("https://test-s3-ceph.amazon.com", "https", True),
        ("http://test-s3-ceph.amazon.com", "http", False),
    ],
)
@patch(mod_urlparse)
def test_parse_ceph_endpoint(m_urlparse, url, scheme, use_ssl):
    m_urlparse.return_value = UrlInfo(scheme=scheme)
    result = s3.parse_ceph_endpoint(url)
    assert result == {"endpoint": url, "use_ssl": use_ssl}
    m_urlparse.assert_called_with(url)
