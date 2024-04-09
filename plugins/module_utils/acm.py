# -*- coding: utf-8 -*-

# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Author:
#   - Matthew Davis <Matthew.Davis.2@team.telstra.com>
#     on behalf of Telstra Corporation Limited
#
# Common functionality to be used by the modules:
#   - acm_certificate
#   - acm_certificate_info

"""
Common Amazon Certificate Manager facts shared between modules
"""

try:
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
except ImportError:
    pass

from ansible.module_utils._text import to_bytes
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from .botocore import is_boto3_error_code
from .retries import AWSRetry
from .tagging import ansible_dict_to_boto3_tag_list
from .tagging import boto3_tag_list_to_ansible_dict


def acm_catch_boto_exception(func):
    def runner(*args, **kwargs):
        module = kwargs.pop("module", None)
        error = kwargs.pop("error", None)
        ignore_error_codes = kwargs.pop("ignore_error_codes", [])

        try:
            return func(*args, **kwargs)
        except is_boto3_error_code(ignore_error_codes):
            return None
        except (BotoCoreError, ClientError) as e:  # pylint: disable=duplicate-except
            if not module:
                raise
            module.fail_json_aws(e, msg=error)

    return runner


class ACMServiceManager:
    """Handles ACM Facts Services"""

    def __init__(self, module):
        self.module = module
        self.client = module.client("acm")

    @acm_catch_boto_exception
    @AWSRetry.jittered_backoff(delay=5, catch_extra_error_codes=["RequestInProgressException"])
    def delete_certificate_with_backoff(self, arn):
        self.client.delete_certificate(CertificateArn=arn)

    @acm_catch_boto_exception
    @AWSRetry.jittered_backoff(delay=5, catch_extra_error_codes=["RequestInProgressException"])
    def list_certificates_with_backoff(self, statuses=None):
        paginator = self.client.get_paginator("list_certificates")
        # `list_certificates` requires explicit key type filter, or it returns only RSA_2048 certificates
        kwargs = {
            "Includes": {
                "keyTypes": [
                    "RSA_1024",
                    "RSA_2048",
                    "RSA_3072",
                    "RSA_4096",
                    "EC_prime256v1",
                    "EC_secp384r1",
                    "EC_secp521r1",
                ],
            },
        }
        if statuses:
            kwargs["CertificateStatuses"] = statuses
        return paginator.paginate(**kwargs).build_full_result()["CertificateSummaryList"]

    @acm_catch_boto_exception
    @AWSRetry.jittered_backoff(
        delay=5, catch_extra_error_codes=["RequestInProgressException", "ResourceNotFoundException"]
    )
    def get_certificate_with_backoff(self, certificate_arn):
        response = self.client.get_certificate(CertificateArn=certificate_arn)
        # strip out response metadata
        return {"Certificate": response["Certificate"], "CertificateChain": response["CertificateChain"]}

    @acm_catch_boto_exception
    @AWSRetry.jittered_backoff(
        delay=5, catch_extra_error_codes=["RequestInProgressException", "ResourceNotFoundException"]
    )
    def describe_certificate_with_backoff(self, certificate_arn):
        return self.client.describe_certificate(CertificateArn=certificate_arn)["Certificate"]

    @acm_catch_boto_exception
    @AWSRetry.jittered_backoff(
        delay=5, catch_extra_error_codes=["RequestInProgressException", "ResourceNotFoundException"]
    )
    def list_certificate_tags_with_backoff(self, certificate_arn):
        return self.client.list_tags_for_certificate(CertificateArn=certificate_arn)["Tags"]

    @acm_catch_boto_exception
    @AWSRetry.jittered_backoff(delay=5, catch_extra_error_codes=["RequestInProgressException"])
    def import_certificate_with_backoff(self, certificate, private_key, certificate_chain, arn):
        params = {"Certificate": to_bytes(certificate), "PrivateKey": to_bytes(private_key)}
        if arn:
            params["CertificateArn"] = arn
        if certificate_chain:
            params["CertificateChain"] = certificate_chain

        return self.client.import_certificate(**params)["CertificateArn"]

    # Tags are a normal Ansible style dict
    # {'Key':'Value'}
    @AWSRetry.jittered_backoff(
        delay=5, catch_extra_error_codes=["RequestInProgressException", "ResourceNotFoundException"]
    )
    def tag_certificate_with_backoff(self, arn, tags):
        aws_tags = ansible_dict_to_boto3_tag_list(tags)
        self.client.add_tags_to_certificate(CertificateArn=arn, Tags=aws_tags)

    def _match_tags(self, ref_tags, cert_tags):
        if ref_tags is None:
            return True
        try:
            return all(k in cert_tags for k in ref_tags) and all(cert_tags.get(k) == ref_tags[k] for k in ref_tags)
        except (TypeError, AttributeError) as e:
            self.module.fail_json_aws(e, msg="ACM tag filtering err")

    def delete_certificate(self, *args, arn=None):
        # hacking for backward compatibility
        if arn is None:
            if len(args) < 3:
                self.module.fail_json(msg="Missing required certificate arn to delete.")
            arn = args[2]
        error = f"Couldn't delete certificate {arn}"
        self.delete_certificate_with_backoff(arn, module=self.module, error=error)

    def get_certificates(self, *args, domain_name=None, statuses=None, arn=None, only_tags=None, **kwargs):
        """
        Returns a list of certificates
        if domain_name is specified, returns only certificates with that domain
        if an ARN is specified, returns only that certificate
        only_tags is a dict, e.g. {'key':'value'}. If specified this function will return
        only certificates which contain all those tags (key exists, value matches).
        """
        all_certificates = self.list_certificates_with_backoff(
            statuses=statuses, module=self.module, error="Couldn't obtain certificates"
        )

        def _filter_certificate(cert):
            if domain_name and cert["DomainName"] != domain_name:
                return False
            if arn and cert["CertificateArn"] != arn:
                return False
            return True

        certificates = list(filter(_filter_certificate, all_certificates))

        results = []
        for certificate in certificates:
            cert_data = self.describe_certificate_with_backoff(
                certificate["CertificateArn"],
                module=self.module,
                error=f"Couldn't obtain certificate metadata for domain {certificate['DomainName']}",
                ignore_error_codes=["ResourceNotFoundException"],
            )
            if cert_data is None:
                continue

            # in some states, ACM resources do not have a corresponding cert
            if cert_data["Status"] not in ("PENDING_VALIDATION", "VALIDATION_TIMED_OUT", "FAILED"):
                cert_info = self.get_certificate_with_backoff(
                    certificate["CertificateArn"],
                    module=self.module,
                    error=f"Couldn't obtain certificate data for domain {certificate['DomainName']}",
                    ignore_error_codes=["ResourceNotFoundException"],
                )
                if cert_info is None:
                    continue
                cert_data.update(cert_info)

            cert_data = camel_dict_to_snake_dict(cert_data)
            tags = self.list_certificate_tags_with_backoff(
                certificate["CertificateArn"],
                module=self.module,
                error=f"Couldn't obtain tags for domain {certificate['DomainName']}",
                ignore_error_codes=["ResourceNotFoundException"],
            )
            if tags is None:
                continue

            tags = boto3_tag_list_to_ansible_dict(tags)
            if not self._match_tags(only_tags, tags):
                continue
            cert_data["tags"] = tags
            results.append(cert_data)
        return results

    def get_domain_of_cert(self, arn, **kwargs):
        """
        returns the domain name of a certificate (encoded in the public cert)
        for a given ARN A cert with that ARN must already exist
        """
        if arn is None:
            self.module.fail_json(msg="Internal error with ACM domain fetching, no certificate ARN specified")
        error = f"Couldn't obtain certificate data for arn {arn}"
        cert_data = self.describe_certificate_with_backoff(certificate_arn=arn, module=self.module, error=error)
        return cert_data["DomainName"]

    def import_certificate(self, *args, certificate, private_key, arn=None, certificate_chain=None, tags=None):
        original_arn = arn

        # upload cert
        params = {
            "certificate": certificate,
            "private_key": private_key,
            "certificate_chain": certificate_chain,
            "arn": arn,
            "module": self.module,
            "error": "Couldn't upload new certificate",
        }
        arn = self.import_certificate_with_backoff(**params)
        if original_arn and (arn != original_arn):
            # I'm not sure whether the API guarentees that the ARN will not change
            # I'm failing just in case.
            # If I'm wrong, I'll catch it in the integration tests.
            self.module.fail_json(msg=f"ARN changed with ACM update, from {original_arn} to {arn}")

        # tag that cert
        try:
            self.tag_certificate_with_backoff(arn, tags)
        except (BotoCoreError, ClientError) as e:
            try:
                self.delete_certificate_with_backoff(arn)
            except (BotoCoreError, ClientError):
                self.module.warn(
                    f"Certificate {arn} exists, and is not tagged. So Ansible will not see it on the next run."
                )
                self.module.fail_json_aws(e, msg=f"Couldn't tag certificate {arn}, couldn't delete it either")
            self.module.fail_json_aws(e, msg=f"Couldn't tag certificate {arn}")

        return arn
