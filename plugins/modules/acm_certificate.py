#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Author:
#   - Matthew Davis <Matthew.Davis.2@team.telstra.com>
#     on behalf of Telstra Corporation Limited

DOCUMENTATION = r"""
---
module: acm_certificate
short_description: Upload and delete certificates in the AWS Certificate Manager service
version_added: 1.0.0
description:
  - >
    Import and delete certificates in Amazon Web Service's Certificate
    Manager (AWS ACM).
  - >
    This module does not currently interact with AWS-provided certificates.
    It currently only manages certificates provided to AWS by the user.
  - The ACM API allows users to upload multiple certificates for the same domain
    name, and even multiple identical certificates. This module attempts to
    restrict such freedoms, to be idempotent, as per the Ansible philosophy.
    It does this through applying AWS resource "Name" tags to ACM certificates.
  - >
    When I(state=present),
    if there is one certificate in ACM
    with a C(Name) tag equal to the I(name_tag) parameter,
    and an identical body and chain,
    this task will succeed without effect.
  - >
    When I(state=present),
    if there is one certificate in ACM
    a I(Name) tag equal to the I(name_tag) parameter,
    and a different body,
    this task will overwrite that certificate.
  - >
    When I(state=present),
    if there are multiple certificates in ACM
    with a I(Name) tag equal to the I(name_tag) parameter,
    this task will fail.
  - >
    When I(state=absent) and I(certificate_arn) is defined,
    this module will delete the ACM resource with that ARN if it exists in this
    region, and succeed without effect if it doesn't exist.
  - >
    When I(state=absent) and I(domain_name) is defined, this module will delete
    all ACM resources in this AWS region with a corresponding domain name.
    If there are none, it will succeed without effect.
  - >
    When I(state=absent) and I(certificate_arn) is not defined,
    and I(domain_name) is not defined, this module will delete all ACM resources
    in this AWS region with a corresponding I(Name) tag.
    If there are none, it will succeed without effect.
  - >
    Note that this may not work properly with keys of size 4096 bits, due to a
    limitation of the ACM API.
  - Prior to release 5.0.0 this module was called C(community.aws.aws_acm).
    The usage did not change.
options:
  certificate:
    description:
      - The body of the PEM encoded public certificate.
      - Required when I(state) is not C(absent) and the certificate does not exist.
      - >
        If your certificate is in a file,
        use C(lookup('file', 'path/to/cert.pem')).
    type: str
  certificate_arn:
    description:
      - The ARN of a certificate in ACM to modify or delete.
      - >
        If I(state=present), the certificate with the specified ARN can be updated.
        For example, this can be used to add/remove tags to an existing certificate.
      - >
        If I(state=absent), you must provide one of
        I(certificate_arn), I(domain_name) or I(name_tag).
      - >
        If I(state=absent) and no resource exists with this ARN in this region,
        the task will succeed with no effect.
      - >
        If I(state=absent) and the corresponding resource exists in a different
        region, this task may report success without deleting that resource.
    type: str
    aliases: [arn]
  certificate_chain:
    description:
      - The body of the PEM encoded chain for your certificate.
      - >
        If your certificate chain is in a file,
        use C(lookup('file', 'path/to/chain.pem')).
      - Ignored when I(state=absent)
    type: str
  domain_name:
    description:
      - The domain name of the certificate.
      - >
        If I(state=absent) and I(domain_name) is specified,
        this task will delete all ACM certificates with this domain.
      - >
        Exactly one of I(domain_name), I(name_tag) and I(certificate_arn)
        must be provided.
      - >
        If I(state=present) this must not be specified.
        (Since the domain name is encoded within the public certificate's body.)
    type: str
    aliases: [domain]
  name_tag:
    description:
      - >
        The unique identifier for tagging resources using AWS tags,
        with key I(Name).
      - This can be any set of characters accepted by AWS for tag values.
      - >
        This is to ensure Ansible can treat certificates idempotently,
        even though the ACM API allows duplicate certificates.
      - If I(state=preset), this must be specified.
      - >
        If I(state=absent) and I(name_tag) is specified,
        this task will delete all ACM certificates with this Name tag.
      - >
        If I(state=absent), you must provide exactly one of
        I(certificate_arn), I(domain_name) or I(name_tag).
      - >
        If both I(name_tag) and the 'Name' tag in I(tags) are set,
        the values must be the same.
      - >
        If the 'Name' tag in I(tags) is not set and I(name_tag) is set,
        the I(name_tag) value is copied to I(tags).
    type: str
    aliases: [name]
  private_key:
    description:
      - The body of the PEM encoded private key.
      - Required when I(state=present) and the certificate does not exist.
      - Ignored when I(state=absent).
      - >
        If your private key is in a file,
        use C(lookup('file', 'path/to/key.pem')).
    type: str
  state:
    description:
      - >
        If I(state=present), the specified public certificate and private key
        will be uploaded, with I(Name) tag equal to I(name_tag).
      - >
        If I(state=absent), any certificates in this region
        with a corresponding I(domain_name), I(name_tag) or I(certificate_arn)
        will be deleted.
    choices: [present, absent]
    default: present
    type: str

notes:
  - Support for I(tags) and I(purge_tags) was added in release 3.2.0
author:
  - Matthew Davis (@matt-telstra) on behalf of Telstra Corporation Limited
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""

- name: upload a self-signed certificate
  community.aws.acm_certificate:
    certificate: "{{ lookup('file', 'cert.pem' ) }}"
    privateKey: "{{ lookup('file', 'key.pem' ) }}"
    name_tag: my_cert # to be applied through an AWS tag as  "Name":"my_cert"
    region: ap-southeast-2 # AWS region

- name: create/update a certificate with a chain
  community.aws.acm_certificate:
    certificate: "{{ lookup('file', 'cert.pem' ) }}"
    private_key: "{{ lookup('file', 'key.pem' ) }}"
    name_tag: my_cert
    certificate_chain: "{{ lookup('file', 'chain.pem' ) }}"
    state: present
    region: ap-southeast-2
  register: cert_create

- name: print ARN of cert we just created
  ansible.builtin.debug:
    var: cert_create.certificate.arn

- name: delete the cert we just created
  community.aws.acm_certificate:
    name_tag: my_cert
    state: absent
    region: ap-southeast-2

- name: delete a certificate with a particular ARN
  community.aws.acm_certificate:
    certificate_arn: "arn:aws:acm:ap-southeast-2:123456789012:certificate/01234567-abcd-abcd-abcd-012345678901"
    state: absent
    region: ap-southeast-2

- name: delete all certificates with a particular domain name
  community.aws.acm_certificate:
    domain_name: acm.ansible.com
    state: absent
    region: ap-southeast-2

- name: add tags to an existing certificate with a particular ARN
  community.aws.acm_certificate:
    certificate_arn: "arn:aws:acm:ap-southeast-2:123456789012:certificate/01234567-abcd-abcd-abcd-012345678901"
    tags:
      Name: my_certificate
      Application: search
      Environment: development
    purge_tags: true
"""

RETURN = r"""
certificate:
  description: Information about the certificate which was uploaded
  type: complex
  returned: when I(state=present)
  contains:
    arn:
      description: The ARN of the certificate in ACM
      type: str
      returned: when I(state=present) and not in check mode
      sample: "arn:aws:acm:ap-southeast-2:123456789012:certificate/01234567-abcd-abcd-abcd-012345678901"
    domain_name:
      description: The domain name encoded within the public certificate
      type: str
      returned: when I(state=present)
      sample: acm.ansible.com
arns:
  description: A list of the ARNs of the certificates in ACM which were deleted
  type: list
  elements: str
  returned: when I(state=absent)
  sample:
   - "arn:aws:acm:ap-southeast-2:123456789012:certificate/01234567-abcd-abcd-abcd-012345678901"
"""


import base64
import re  # regex library
from copy import deepcopy

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible.module_utils._text import to_text

from ansible_collections.amazon.aws.plugins.module_utils.acm import ACMServiceManager
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def ensure_tags(client, module, resource_arn, existing_tags, tags, purge_tags):
    if tags is None:
        return (False, existing_tags)

    tags_to_add, tags_to_remove = compare_aws_tags(existing_tags, tags, purge_tags)
    changed = bool(tags_to_add or tags_to_remove)
    if tags_to_add and not module.check_mode:
        try:
            client.add_tags_to_certificate(
                CertificateArn=resource_arn,
                Tags=ansible_dict_to_boto3_tag_list(tags_to_add),
            )
        except (
            botocore.exceptions.ClientError,
            botocore.exceptions.BotoCoreError,
        ) as e:
            module.fail_json_aws(e, f"Couldn't add tags to certificate {resource_arn}")
    if tags_to_remove and not module.check_mode:
        # remove_tags_from_certificate wants a list of key, value pairs, not a list of keys.
        tags_list = [{"Key": key, "Value": existing_tags.get(key)} for key in tags_to_remove]
        try:
            client.remove_tags_from_certificate(
                CertificateArn=resource_arn,
                Tags=tags_list,
            )
        except (
            botocore.exceptions.ClientError,
            botocore.exceptions.BotoCoreError,
        ) as e:
            module.fail_json_aws(e, f"Couldn't remove tags from certificate {resource_arn}")
    new_tags = deepcopy(existing_tags)
    for key, value in tags_to_add.items():
        new_tags[key] = value
    for key in tags_to_remove:
        new_tags.pop(key, None)
    return (changed, new_tags)


# Takes in two text arguments
# Each a PEM encoded certificate
# Or a chain of PEM encoded certificates
# May include some lines between each chain in the cert, e.g. "Subject: ..."
# Returns True iff the chains/certs are functionally identical (including chain order)
def chain_compare(module, a, b):
    chain_a_pem = pem_chain_split(module, a)
    chain_b_pem = pem_chain_split(module, b)

    if len(chain_a_pem) != len(chain_b_pem):
        return False

    # Chain length is the same
    for ca, cb in zip(chain_a_pem, chain_b_pem):
        der_a = PEM_body_to_DER(module, ca)
        der_b = PEM_body_to_DER(module, cb)
        if der_a != der_b:
            return False

    return True


# Takes in PEM encoded data with no headers
# returns equivilent DER as byte array
def PEM_body_to_DER(module, pem):
    try:
        der = base64.b64decode(to_text(pem))
    except (ValueError, TypeError) as e:
        module.fail_json_aws(e, msg="Unable to decode certificate chain")
    return der


# Store this globally to avoid repeated recompilation
pem_chain_split_regex = re.compile(
    r"------?BEGIN [A-Z0-9. ]*CERTIFICATE------?([a-zA-Z0-9\+\/=\s]+)------?END [A-Z0-9. ]*CERTIFICATE------?"
)


# Use regex to split up a chain or single cert into an array of base64 encoded data
# Using "-----BEGIN CERTIFICATE-----" and "----END CERTIFICATE----"
# Noting that some chains have non-pem data in between each cert
# This function returns only what's between the headers, excluding the headers
def pem_chain_split(module, pem):
    pem_arr = re.findall(pem_chain_split_regex, to_text(pem))

    if len(pem_arr) == 0:
        # This happens if the regex doesn't match at all
        module.fail_json(msg="Unable to split certificate chain. Possibly zero-length chain?")

    return pem_arr


def update_imported_certificate(client, module, acm, old_cert, desired_tags):
    """
    Update the existing certificate that was previously imported in ACM.
    """
    module.debug("Existing certificate found in ACM")
    if ("tags" not in old_cert) or ("Name" not in old_cert["tags"]):
        # shouldn't happen
        module.fail_json(msg="Internal error, unsure which certificate to update", certificate=old_cert)
    if module.params.get("name_tag") is not None and (old_cert["tags"]["Name"] != module.params.get("name_tag")):
        # This could happen if the user identified the certificate using 'certificate_arn' or 'domain_name',
        # and the 'Name' tag in the AWS API does not match the ansible 'name_tag'.
        module.fail_json(msg="Internal error, Name tag does not match", certificate=old_cert)
    if "certificate" not in old_cert:
        # shouldn't happen
        module.fail_json(msg="Internal error, unsure what the existing cert in ACM is", certificate=old_cert)

    cert_arn = None
    # Are the existing certificate in ACM and the local certificate the same?
    same = True
    if module.params.get("certificate") is not None:
        same &= chain_compare(module, old_cert["certificate"], module.params["certificate"])
        if module.params["certificate_chain"]:
            # Need to test this
            # not sure if Amazon appends the cert itself to the chain when self-signed
            same &= chain_compare(module, old_cert["certificate_chain"], module.params["certificate_chain"])
        else:
            # When there is no chain with a cert
            # it seems Amazon returns the cert itself as the chain
            same &= chain_compare(module, old_cert["certificate_chain"], module.params["certificate"])

    if same:
        module.debug("Existing certificate in ACM is the same")
        cert_arn = old_cert["certificate_arn"]
        changed = False
    else:
        absent_args = ["certificate", "name_tag", "private_key"]
        if sum([(module.params[a] is not None) for a in absent_args]) < 3:
            module.fail_json(
                msg="When importing a certificate, all of 'name_tag', 'certificate' and 'private_key' must be specified"
            )
        module.debug("Existing certificate in ACM is different, overwriting")
        changed = True
        if module.check_mode:
            cert_arn = old_cert["certificate_arn"]
            # note: returned domain will be the domain of the previous cert
        else:
            # update cert in ACM
            cert_arn = acm.import_certificate(
                client,
                module,
                certificate=module.params["certificate"],
                private_key=module.params["private_key"],
                certificate_chain=module.params["certificate_chain"],
                arn=old_cert["certificate_arn"],
                tags=desired_tags,
            )
    return (changed, cert_arn)


def import_certificate(client, module, acm, desired_tags):
    """
    Import a certificate to ACM.
    """
    # Validate argument requirements
    absent_args = ["certificate", "name_tag", "private_key"]
    cert_arn = None
    if sum([(module.params[a] is not None) for a in absent_args]) < 3:
        module.fail_json(
            msg="When importing a new certificate, all of 'name_tag', 'certificate' and 'private_key' must be specified"
        )
    module.debug("No certificate in ACM. Creating new one.")
    changed = True
    if module.check_mode:
        domain = "example.com"
        module.exit_json(certificate=dict(domain_name=domain), changed=True)
    else:
        cert_arn = acm.import_certificate(
            client,
            module,
            certificate=module.params["certificate"],
            private_key=module.params["private_key"],
            certificate_chain=module.params["certificate_chain"],
            tags=desired_tags,
        )
    return (changed, cert_arn)


def ensure_certificates_present(client, module, acm, certificates, desired_tags, filter_tags):
    cert_arn = None
    changed = False
    if len(certificates) > 1:
        msg = f"More than one certificate with Name={module.params['name_tag']} exists in ACM in this region"
        module.fail_json(msg=msg, certificates=certificates)
    elif len(certificates) == 1:
        # Update existing certificate that was previously imported to ACM.
        (changed, cert_arn) = update_imported_certificate(client, module, acm, certificates[0], desired_tags)
    else:  # len(certificates) == 0
        # Import new certificate to ACM.
        (changed, cert_arn) = import_certificate(client, module, acm, desired_tags)

    # Add/remove tags to/from certificate
    try:
        existing_tags = boto3_tag_list_to_ansible_dict(
            client.list_tags_for_certificate(CertificateArn=cert_arn)["Tags"]
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, "Couldn't get tags for certificate")

    purge_tags = module.params.get("purge_tags")
    (c, new_tags) = ensure_tags(client, module, cert_arn, existing_tags, desired_tags, purge_tags)
    changed |= c
    domain = acm.get_domain_of_cert(client=client, module=module, arn=cert_arn)
    module.exit_json(certificate=dict(domain_name=domain, arn=cert_arn, tags=new_tags), changed=changed)


def ensure_certificates_absent(client, module, acm, certificates):
    for cert in certificates:
        if not module.check_mode:
            acm.delete_certificate(client, module, cert["certificate_arn"])
    module.exit_json(arns=[cert["certificate_arn"] for cert in certificates], changed=(len(certificates) > 0))


def main():
    argument_spec = dict(
        certificate=dict(),
        certificate_arn=dict(aliases=["arn"]),
        certificate_chain=dict(),
        domain_name=dict(aliases=["domain"]),
        name_tag=dict(aliases=["name"]),
        private_key=dict(no_log=True),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        state=dict(default="present", choices=["present", "absent"]),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    acm = ACMServiceManager(module)

    # Check argument requirements
    if module.params["state"] == "present":
        # at least one of these should be specified.
        absent_args = ["certificate_arn", "domain_name", "name_tag"]
        if sum([(module.params[a] is not None) for a in absent_args]) < 1:
            for a in absent_args:
                module.debug(f"{a} is {module.params[a]}")
            module.fail_json(
                msg="If 'state' is specified as 'present' then at least one of 'name_tag', 'certificate_arn' or 'domain_name' must be specified"
            )
    else:  # absent
        # exactly one of these should be specified
        absent_args = ["certificate_arn", "domain_name", "name_tag"]
        if sum([(module.params[a] is not None) for a in absent_args]) != 1:
            for a in absent_args:
                module.debug(f"{a} is {module.params[a]}")
            module.fail_json(
                msg="If 'state' is specified as 'absent' then exactly one of 'name_tag', 'certificate_arn' or 'domain_name' must be specified"
            )

    filter_tags = None
    desired_tags = None
    if module.params.get("tags") is not None:
        desired_tags = module.params["tags"]
    else:
        # Because we're setting the Name tag, we need to explicitly not purge when tags isn't passed
        module.params["purge_tags"] = False
    if module.params.get("name_tag") is not None:
        # The module was originally implemented to filter certificates based on the 'Name' tag.
        # Other tags are not used to filter certificates.
        # It would make sense to replace the existing name_tag, domain, certificate_arn attributes
        # with a 'filter' attribute, but that would break backwards-compatibility.
        filter_tags = dict(Name=module.params["name_tag"])
        if desired_tags is not None:
            if "Name" in desired_tags:
                if desired_tags["Name"] != module.params["name_tag"]:
                    module.fail_json(msg="Value of 'name_tag' conflicts with value of 'tags.Name'")
            else:
                desired_tags["Name"] = module.params["name_tag"]
        else:
            desired_tags = deepcopy(filter_tags)

    client = module.client("acm")

    # fetch the list of certificates currently in ACM
    certificates = acm.get_certificates(
        client=client,
        module=module,
        domain_name=module.params["domain_name"],
        arn=module.params["certificate_arn"],
        only_tags=filter_tags,
    )

    module.debug(f"Found {len(certificates)} corresponding certificates in ACM")
    if module.params["state"] == "present":
        ensure_certificates_present(client, module, acm, certificates, desired_tags, filter_tags)

    else:  # state == absent
        ensure_certificates_absent(client, module, acm, certificates)


if __name__ == "__main__":
    # tests()
    main()
