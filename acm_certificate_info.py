#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: acm_certificate_info
short_description: Retrieve certificate information from AWS Certificate Manager service
version_added: 1.0.0
description:
  - Retrieve information for ACM certificates.
  - Note that this will not return information about uploaded keys of size 4096 bits, due to a limitation of the ACM API.
  - Prior to release 5.0.0 this module was called C(community.aws.aws_acm_info).
    The usage did not change.
options:
  certificate_arn:
    description:
      - If provided, the results will be filtered to show only the certificate with this ARN.
      - If no certificate with this ARN exists, this task will fail.
      - If a certificate with this ARN exists in a different region, this task will fail.
    aliases:
      - arn
    type: str
  domain_name:
    description:
      - The domain name of an ACM certificate to limit the search to.
    aliases:
      - name
    type: str
  statuses:
    description:
      - Status to filter the certificate results.
    choices: ['PENDING_VALIDATION', 'ISSUED', 'INACTIVE', 'EXPIRED', 'VALIDATION_TIMED_OUT', 'REVOKED', 'FAILED']
    type: list
    elements: str
  tags:
    description:
      - Filter results to show only certificates with tags that match all the tags specified here.
    type: dict
author:
  - Will Thames (@willthames)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: obtain all ACM certificates
  community.aws.aws_acm_info:

- name: obtain all information for a single ACM certificate
  community.aws.aws_acm_info:
    domain_name: "*.example_com"

- name: obtain all certificates pending validation
  community.aws.aws_acm_info:
    statuses:
    - PENDING_VALIDATION

- name: obtain all certificates with tag Name=foo and myTag=bar
  community.aws.aws_acm_info:
    tags:
      Name: foo
      myTag: bar


# The output is still a list of certificates, just one item long.
- name: obtain information about a certificate with a particular ARN
  community.aws.aws_acm_info:
    certificate_arn:  "arn:aws:acm:ap-southeast-2:123456789012:certificate/abcdeabc-abcd-1234-4321-abcdeabcde12"

"""

RETURN = r"""
certificates:
  description: A list of certificates
  returned: always
  type: complex
  contains:
    certificate:
      description: The ACM Certificate body
      returned: when certificate creation is complete
      sample: '-----BEGIN CERTIFICATE-----\\nMII.....-----END CERTIFICATE-----\\n'
      type: str
    certificate_arn:
      description: Certificate ARN
      returned: always
      sample: arn:aws:acm:ap-southeast-2:123456789012:certificate/abcd1234-abcd-1234-abcd-123456789abc
      type: str
    certificate_chain:
      description: Full certificate chain for the certificate
      returned: when certificate creation is complete
      sample: '-----BEGIN CERTIFICATE-----\\nMII...\\n-----END CERTIFICATE-----\\n-----BEGIN CERTIFICATE-----\\n...'
      type: str
    created_at:
      description: Date certificate was created
      returned: always
      sample: '2017-08-15T10:31:19+10:00'
      type: str
    domain_name:
      description: Domain name for the certificate
      returned: always
      sample: '*.example.com'
      type: str
    domain_validation_options:
      description: Options used by ACM to validate the certificate
      returned: when certificate type is AMAZON_ISSUED
      type: complex
      contains:
        domain_name:
          description: Fully qualified domain name of the certificate
          returned: always
          sample: example.com
          type: str
        validation_domain:
          description: The domain name ACM used to send validation emails
          returned: always
          sample: example.com
          type: str
        validation_emails:
          description: A list of email addresses that ACM used to send domain validation emails
          returned: always
          sample:
          - admin@example.com
          - postmaster@example.com
          type: list
          elements: str
        validation_status:
          description: Validation status of the domain
          returned: always
          sample: SUCCESS
          type: str
    failure_reason:
      description: Reason certificate request failed
      returned: only when certificate issuing failed
      type: str
      sample: NO_AVAILABLE_CONTACTS
    in_use_by:
      description: A list of ARNs for the AWS resources that are using the certificate.
      returned: always
      sample: []
      type: list
      elements: str
    issued_at:
      description: Date certificate was issued
      returned: always
      sample: '2017-01-01T00:00:00+10:00'
      type: str
    issuer:
      description: Issuer of the certificate
      returned: always
      sample: Amazon
      type: str
    key_algorithm:
      description: Algorithm used to generate the certificate
      returned: always
      sample: RSA-2048
      type: str
    not_after:
      description: Date after which the certificate is not valid
      returned: always
      sample: '2019-01-01T00:00:00+10:00'
      type: str
    not_before:
      description: Date before which the certificate is not valid
      returned: always
      sample: '2017-01-01T00:00:00+10:00'
      type: str
    renewal_summary:
      description: Information about managed renewal process
      returned: when certificate is issued by Amazon and a renewal has been started
      type: complex
      contains:
        domain_validation_options:
          description: Options used by ACM to validate the certificate
          returned: when certificate type is AMAZON_ISSUED
          type: complex
          contains:
            domain_name:
              description: Fully qualified domain name of the certificate
              returned: always
              sample: example.com
              type: str
            validation_domain:
              description: The domain name ACM used to send validation emails
              returned: always
              sample: example.com
              type: str
            validation_emails:
              description: A list of email addresses that ACM used to send domain validation emails
              returned: always
              sample:
              - admin@example.com
              - postmaster@example.com
              type: list
              elements: str
            validation_status:
              description: Validation status of the domain
              returned: always
              sample: SUCCESS
              type: str
        renewal_status:
          description: Status of the domain renewal
          returned: always
          sample: PENDING_AUTO_RENEWAL
          type: str
    revocation_reason:
      description: Reason for certificate revocation
      returned: when the certificate has been revoked
      sample: SUPERCEDED
      type: str
    revoked_at:
      description: Date certificate was revoked
      returned: when the certificate has been revoked
      sample: '2017-09-01T10:00:00+10:00'
      type: str
    serial:
      description: The serial number of the certificate
      returned: always
      sample: 00:01:02:03:04:05:06:07:08:09:0a:0b:0c:0d:0e:0f
      type: str
    signature_algorithm:
      description: Algorithm used to sign the certificate
      returned: always
      sample: SHA256WITHRSA
      type: str
    status:
      description: Status of the certificate in ACM
      returned: always
      sample: ISSUED
      type: str
    subject:
      description: The name of the entity that is associated with the public key contained in the certificate
      returned: always
      sample: CN=*.example.com
      type: str
    subject_alternative_names:
      description: Subject Alternative Names for the certificate
      returned: always
      sample:
      - '*.example.com'
      type: list
      elements: str
    tags:
      description: Tags associated with the certificate
      returned: always
      type: dict
      sample:
        Application: helloworld
        Environment: test
    type:
      description: The source of the certificate
      returned: always
      sample: AMAZON_ISSUED
      type: str
"""

from ansible_collections.amazon.aws.plugins.module_utils.acm import ACMServiceManager

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def main():
    argument_spec = dict(
        certificate_arn=dict(aliases=["arn"]),
        domain_name=dict(aliases=["name"]),
        statuses=dict(
            type="list",
            elements="str",
            choices=[
                "PENDING_VALIDATION",
                "ISSUED",
                "INACTIVE",
                "EXPIRED",
                "VALIDATION_TIMED_OUT",
                "REVOKED",
                "FAILED",
            ],
        ),
        tags=dict(type="dict"),
    )
    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)
    acm_info = ACMServiceManager(module)

    client = module.client("acm")

    certificates = acm_info.get_certificates(
        client,
        module,
        domain_name=module.params["domain_name"],
        statuses=module.params["statuses"],
        arn=module.params["certificate_arn"],
        only_tags=module.params["tags"],
    )

    if module.params["certificate_arn"] and len(certificates) != 1:
        module.fail_json(msg=f"No certificate exists in this region with ARN {module.params['certificate_arn']}")

    module.exit_json(certificates=certificates)


if __name__ == "__main__":
    main()
