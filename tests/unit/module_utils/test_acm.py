#
# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


import random
from unittest.mock import ANY
from unittest.mock import MagicMock

import pytest

try:
    import botocore
except ImportError:
    # Handled by HAS_BOTO3
    pass


from ansible_collections.amazon.aws.plugins.module_utils.acm import ACMServiceManager
from ansible_collections.amazon.aws.plugins.module_utils.acm import acm_catch_boto_exception

MODULE_NAME = "ansible_collections.amazon.aws.plugins.module_utils.acm"


@pytest.fixture()
def acm_service_mgr():
    module = MagicMock()
    module.fail_json_aws.side_effect = SystemExit(2)
    module.fail_json.side_effect = SystemExit(1)
    module.client.return_value = MagicMock()

    acm_service_mgr_obj = ACMServiceManager(module)

    return acm_service_mgr_obj


def raise_botocore_error(code="AccessDenied"):
    return botocore.exceptions.ClientError({"Error": {"Code": code}}, "Certificate")


@pytest.mark.parametrize("has_module_arg", [True, False])
def test_acm_catch_boto_exception_failure(has_module_arg):
    module = MagicMock()
    module.fail_json_aws.side_effect = SystemExit(2)

    boto_err = raise_botocore_error()

    @acm_catch_boto_exception
    def generate_boto_exception():
        raise boto_err

    if has_module_arg:
        with pytest.raises(SystemExit):
            generate_boto_exception(module=module, error="test")
        module.fail_json_aws.assert_called_with(boto_err, msg="test")
    else:
        with pytest.raises(botocore.exceptions.ClientError):
            generate_boto_exception(error="test")
        module.fail_json_aws.assert_not_called()


def test_acm_catch_boto_exception_with_ignore_code():
    codes = ["this_exception_code_is_ignored", "this_another_exception_code_is_ignored"]

    @acm_catch_boto_exception
    def raise_exception_with_ignore_error_code(**kwargs):
        raise raise_botocore_error(code=random.choice(codes))

    assert raise_exception_with_ignore_error_code(ignore_error_codes=codes) is None


def test_acm_catch_boto_exception():
    data = {i: MagicMock() for i in range(10)}

    @acm_catch_boto_exception
    def get_data(*args, **kwargs):
        if len(args) > 0:
            return data.get(args[0])
        return data.get(kwargs.get("id"))

    for i in range(10):
        assert data.get(i) == get_data(i)
        assert data.get(i) == get_data(id=i)


def test_acm_service_manager_init():
    module = MagicMock()
    module.client.return_value = {"client": "unit_tests"}

    ACMServiceManager(module)
    module.client.assert_called_once_with("acm")


def test_acm_service_manager_get_domain_of_cert(acm_service_mgr):
    arn = "arn:aws:acm:us-west-01:123456789012:certificate/12345678-1234-1234-1234-123456789012"

    certificate = {"Certificate": {"DomainName": MagicMock()}, "ResponseMetaData": {"code": 200}}
    acm_service_mgr.client.describe_certificate.return_value = certificate
    assert acm_service_mgr.get_domain_of_cert(arn=arn) == certificate["Certificate"]["DomainName"]


def test_acm_service_manager_get_domain_of_cert_missing_arn(acm_service_mgr):
    with pytest.raises(SystemExit):
        acm_service_mgr.get_domain_of_cert(arn=None)
    error = "Internal error with ACM domain fetching, no certificate ARN specified"
    acm_service_mgr.module.fail_json.assert_called_with(msg=error)
    acm_service_mgr.module.fail_json_aws.assert_not_called()


def test_acm_service_manager_get_domain_of_cert_failure(acm_service_mgr):
    arn = "arn:aws:acm:us-west-01:123456789012:certificate/12345678-1234-1234-1234-123456789012"
    boto_err = raise_botocore_error()

    acm_service_mgr.client.describe_certificate.side_effect = boto_err
    with pytest.raises(SystemExit):
        acm_service_mgr.get_domain_of_cert(arn=arn)

    error = f"Couldn't obtain certificate data for arn {arn}"
    acm_service_mgr.module.fail_json_aws.assert_called_with(boto_err, msg=error)
    acm_service_mgr.module.fail.assert_not_called()


def test_acm_service_manager_get_domain_of_cert_with_retry_and_success(acm_service_mgr):
    arn = "arn:aws:acm:us-west-01:123456789012:certificate/12345678-1234-1234-1234-123456789012"
    boto_err = raise_botocore_error(code="ResourceNotFoundException")
    certificate = {"Certificate": {"DomainName": MagicMock()}, "ResponseMetaData": {"code": 200}}
    acm_service_mgr.client.describe_certificate.side_effect = [boto_err, certificate]
    assert acm_service_mgr.get_domain_of_cert(arn=arn) == certificate["Certificate"]["DomainName"]


def test_acm_service_manager_get_domain_of_cert_with_retry_and_failure(acm_service_mgr):
    arn = "arn:aws:acm:us-west-01:123456789012:certificate/12345678-1234-1234-1234-123456789012"
    boto_err = raise_botocore_error(code="ResourceNotFoundException")

    acm_service_mgr.client.describe_certificate.side_effect = [boto_err for i in range(10)]
    with pytest.raises(SystemExit):
        acm_service_mgr.get_domain_of_cert(arn=arn)


def test_acm_service_manager_import_certificate_failure_at_import(acm_service_mgr):
    acm_service_mgr.client.import_certificate.side_effect = raise_botocore_error()
    with pytest.raises(SystemExit):
        acm_service_mgr.import_certificate(certificate=MagicMock(), private_key=MagicMock())


def test_acm_service_manager_import_certificate_failure_at_tagging(acm_service_mgr):
    arn = "arn:aws:acm:us-west-01:123456789012:certificate/12345678-1234-1234-1234-123456789012"
    acm_service_mgr.client.import_certificate.return_value = {"CertificateArn": arn}

    boto_err = raise_botocore_error()
    acm_service_mgr.client.add_tags_to_certificate.side_effect = boto_err

    with pytest.raises(SystemExit):
        acm_service_mgr.import_certificate(certificate=MagicMock(), private_key=MagicMock())
    acm_service_mgr.module.fail_json_aws.assert_called_with(boto_err, msg=f"Couldn't tag certificate {arn}")


def test_acm_service_manager_import_certificate_failure_at_deletion(acm_service_mgr):
    arn = "arn:aws:acm:us-west-01:123456789012:certificate/12345678-1234-1234-1234-123456789012"
    acm_service_mgr.client.import_certificate.return_value = {"CertificateArn": arn}

    acm_service_mgr.client.add_tags_to_certificate.side_effect = raise_botocore_error()
    delete_err = raise_botocore_error(code="DeletionError")
    acm_service_mgr.client.delete_certificate.side_effect = delete_err

    with pytest.raises(SystemExit):
        acm_service_mgr.import_certificate(certificate=MagicMock(), private_key=MagicMock())
    acm_service_mgr.module.warn.assert_called_with(
        f"Certificate {arn} exists, and is not tagged. So Ansible will not see it on the next run."
    )


def test_acm_service_manager_import_certificate_failure_with_arn_change(acm_service_mgr):
    original_arn = "original_arn:aws:acm:us-west-01:123456789012:certificate/12345678-1234-1234-1234-123456789012"
    arn = "arn:aws:acm:us-west-01:123456789012:certificate/12345678-1234-1234-1234-123456789012"

    acm_service_mgr.import_certificate_with_backoff = MagicMock()
    acm_service_mgr.import_certificate_with_backoff.return_value = arn

    with pytest.raises(SystemExit):
        acm_service_mgr.import_certificate(certificate=MagicMock(), private_key=MagicMock(), arn=original_arn)
    acm_service_mgr.module.fail_json.assert_called_with(
        msg=f"ARN changed with ACM update, from {original_arn} to {arn}"
    )


def test_acm_service_manager_import_certificate(acm_service_mgr):
    arn = "arn:aws:acm:us-west-01:123456789012:certificate/12345678-1234-1234-1234-123456789012"

    acm_service_mgr.import_certificate_with_backoff = MagicMock()
    acm_service_mgr.import_certificate_with_backoff.return_value = arn

    acm_service_mgr.tag_certificate_with_backoff = MagicMock()

    assert arn == acm_service_mgr.import_certificate(certificate=MagicMock(), private_key=MagicMock(), arn=arn)


def test_acm_service_manager_delete_certificate_keyword_arn(acm_service_mgr):
    arn = "arn:aws:acm:us-west-01:123456789012:certificate/12345678-1234-1234-1234-123456789012"
    acm_service_mgr.delete_certificate_with_backoff = MagicMock()
    acm_service_mgr.delete_certificate(arn=arn)
    err = f"Couldn't delete certificate {arn}"
    acm_service_mgr.delete_certificate_with_backoff.assert_called_with(arn, module=acm_service_mgr.module, error=err)


def test_acm_service_manager_delete_certificate_positional_arn(acm_service_mgr):
    arn = "arn:aws:acm:us-west-01:123456789012:certificate/12345678-1234-1234-1234-123456789012"
    acm_service_mgr.delete_certificate_with_backoff = MagicMock()
    module = MagicMock()
    client = MagicMock()
    acm_service_mgr.delete_certificate(module, client, arn)
    err = f"Couldn't delete certificate {arn}"
    acm_service_mgr.delete_certificate_with_backoff.assert_called_with(arn, module=acm_service_mgr.module, error=err)


def test_acm_service_manager_delete_certificate_missing_arn(acm_service_mgr):
    with pytest.raises(SystemExit):
        acm_service_mgr.delete_certificate()
    acm_service_mgr.module.fail_json.assert_called_with(msg="Missing required certificate arn to delete.")


def test_acm_service_manager_delete_certificate_failure(acm_service_mgr):
    arn = "arn:aws:acm:us-west-01:123456789012:certificate/12345678-1234-1234-1234-123456789012"
    acm_service_mgr.client.delete_certificate.side_effect = raise_botocore_error()
    with pytest.raises(SystemExit):
        acm_service_mgr.delete_certificate(arn=arn)


@pytest.mark.parametrize(
    "ref,cert,result",
    [
        (None, ANY, True),
        ({"phase": "test"}, {"Phase": "test"}, False),
        ({"phase": "test"}, {"phase": "test"}, True),
        ({"phase": "test"}, {"phase": "test", "collection": "amazon.aws"}, True),
        ({"phase": "test", "collection": "amazon"}, {"phase": "test", "collection": "amazon.aws"}, False),
        ({"phase": "test", "collection": "amazon"}, {"phase": "test"}, False),
    ],
)
def test_acm_service_manager_match_tags(acm_service_mgr, ref, cert, result):
    assert acm_service_mgr._match_tags(ref, cert) == result


def test_acm_service_manager_match_tags_failure(acm_service_mgr):
    with pytest.raises(SystemExit):
        acm_service_mgr._match_tags({"Tag": "tag1"}, 10)
    acm_service_mgr.module.fail_json_aws.assert_called_once()


def test_acm_service_manager_get_certificates_no_certificates(acm_service_mgr):
    acm_service_mgr.list_certificates_with_backoff = MagicMock()
    acm_service_mgr.list_certificates_with_backoff.return_value = []

    assert acm_service_mgr.get_certificates(domain_name=MagicMock(), statuses=MagicMock(), arn=ANY, only_tags=ANY) == []


@pytest.mark.parametrize(
    "domain_name,arn,tags,expected",
    [
        (None, None, None, [0, 1, 3]),
        ("ansible.com", None, None, [0]),
        ("ansible.com", "arn:aws:1", None, [0]),
        (None, "arn:aws:1", None, [0]),
        (None, "arn:aws:4", None, [3]),
        ("ansible.com", "arn:aws:3", None, []),
        ("ansible.org", None, None, [1, 3]),
        ("ansible.org", "arn:aws:2", None, [1]),
        ("ansible.org", "arn:aws:4", None, [3]),
        (None, None, {"CertificateArn": "arn:aws:2"}, [1]),
        (None, None, {"CertificateType": "x509"}, [0, 1]),
        (None, None, {"CertificateType": "x509", "CertificateArn": "arn:aws:2"}, [1]),
    ],
)
def test_acm_service_manager_get_certificates(acm_service_mgr, domain_name, arn, tags, expected):
    all_certificates = [
        {"CertificateArn": "arn:aws:1", "DomainName": "ansible.com"},
        {"CertificateArn": "arn:aws:2", "DomainName": "ansible.org"},
        {"CertificateArn": "arn:aws:3", "DomainName": "ansible.com"},
        {"CertificateArn": "arn:aws:4", "DomainName": "ansible.org"},
    ]

    acm_service_mgr.list_certificates_with_backoff = MagicMock()
    acm_service_mgr.list_certificates_with_backoff.return_value = all_certificates

    describe_certificates = {
        "arn:aws:1": {"Status": "VALIDATED", "CertificateArn": "arn:aws:1", "AnotherKey": "some_key_value"},
        "arn:aws:2": {"Status": "VALIDATION_TIMED_OUT", "CertificateArn": "arn:aws:2"},
        "arn:aws:3": {"Status": "FAILED", "CertificateArn": "arn:aws:3", "CertificateValidity": "11222022"},
        "arn:aws:4": {"Status": "PENDING_VALIDATION", "CertificateArn": "arn:aws:4"},
    }

    get_certificates = {
        "arn:aws:1": {"Provider": "Dummy", "Private": True},
        "arn:aws:2": None,
        "arn:aws:3": {},
        "arn:aws:4": {},
    }

    certificate_tags = {
        "arn:aws:1": [
            {"Key": "Validated", "Value": True},
            {"Key": "CertificateType", "Value": "x509"},
            {"Key": "CertificateArn", "Value": "arn:aws:1"},
        ],
        "arn:aws:2": [{"Key": "CertificateType", "Value": "x509"}, {"Key": "CertificateArn", "Value": "arn:aws:2"}],
        "arn:aws:3": None,
        "arn:aws:4": {},
    }

    all_results = [
        {
            "status": "VALIDATED",
            "certificate_arn": "arn:aws:1",
            "another_key": "some_key_value",
            "provider": "Dummy",
            "private": True,
            "tags": {"Validated": True, "CertificateType": "x509", "CertificateArn": "arn:aws:1"},
        },
        {
            "status": "VALIDATION_TIMED_OUT",
            "certificate_arn": "arn:aws:2",
            "tags": {"CertificateType": "x509", "CertificateArn": "arn:aws:2"},
        },
        {"status": "FAILED", "certificate_arn": "arn:aws:3", "certificate_validity": "11222022"},
        {"status": "PENDING_VALIDATION", "certificate_arn": "arn:aws:4", "tags": {}},
    ]

    results = [all_results[i] for i in range(len(all_results)) if i in expected]

    acm_service_mgr.describe_certificate_with_backoff = MagicMock()
    acm_service_mgr.describe_certificate_with_backoff.side_effect = lambda *args, **kwargs: describe_certificates.get(
        args[0]
    )

    acm_service_mgr.get_certificate_with_backoff = MagicMock()
    acm_service_mgr.get_certificate_with_backoff.side_effect = lambda *args, **kwargs: get_certificates.get(args[0])

    acm_service_mgr.list_certificate_tags_with_backoff = MagicMock()
    acm_service_mgr.list_certificate_tags_with_backoff.side_effect = lambda *args, **kwargs: certificate_tags.get(
        args[0], []
    )

    assert (
        acm_service_mgr.get_certificates(domain_name=domain_name, statuses=MagicMock(), arn=arn, only_tags=tags)
        == results
    )
