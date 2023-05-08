#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: iam_server_certificate
version_added: 1.0.0
short_description: Manage IAM server certificates for use on ELBs and CloudFront
description:
  - Allows for the management of IAM server certificates.
options:
  name:
    description:
      - Name of certificate to add, update or remove.
    required: true
    type: str
  new_name:
    description:
      - When I(state=present), this will update the name of the cert.
      - The I(cert), I(key) and I(cert_chain) parameters will be ignored if this is defined.
    type: str
  new_path:
    description:
      - When I(state=present), this will update the path of the cert.
      - The I(cert), I(key) and I(cert_chain) parameters will be ignored if this is defined.
    type: str
  state:
    description:
      - Whether to create (or update) or delete the certificate.
      - If I(new_path) or I(new_name) is defined, specifying present will attempt to make an update these.
    required: true
    choices: [ "present", "absent" ]
    type: str
  path:
    description:
      - When creating or updating, specify the desired path of the certificate.
    default: "/"
    type: str
  cert_chain:
    description:
      - The content of the CA certificate chain in PEM encoded format.
    type: str
  cert:
    description:
      - The content of the certificate body in PEM encoded format.
    type: str
  key:
    description:
      - The content of the private key in PEM encoded format.
    type: str
  dup_ok:
    description:
      - By default the module will not upload a certificate that is already uploaded into AWS.
      - If I(dup_ok=True), it will upload the certificate as long as the name is unique.
      - The default value for this value changed in release 5.0.0 to C(true).
    default: true
    type: bool

author:
  - Jonathan I. Davila (@defionscode)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

RETURN = r""" # """

EXAMPLES = r"""
- name: Basic server certificate upload from local file
  community.aws.iam_server_certificate:
    name: very_ssl
    state: present
    cert: "{{ lookup('file', 'path/to/cert') }}"
    key: "{{ lookup('file', 'path/to/key') }}"
    cert_chain: "{{ lookup('file', 'path/to/certchain') }}"

- name: Server certificate upload using key string
  community.aws.iam_server_certificate:
    name: very_ssl
    state: present
    path: "/a/cert/path/"
    cert: "{{ lookup('file', 'path/to/cert') }}"
    key: "{{ lookup('file', 'path/to/key') }}"
    cert_chain: "{{ lookup('file', 'path/to/certchain') }}"

- name: Basic rename of existing certificate
  community.aws.iam_server_certificate:
    name: very_ssl
    new_name: new_very_ssl
    state: present
"""

try:
    import botocore
except ImportError:
    pass  # Handled by HAS_BOTO

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


@AWSRetry.jittered_backoff()
def _list_server_certficates():
    paginator = client.get_paginator("list_server_certificates")
    return paginator.paginate().build_full_result()["ServerCertificateMetadataList"]


def check_duplicate_cert(new_cert):
    orig_cert_names = list(c["ServerCertificateName"] for c in _list_server_certficates())
    for cert_name in orig_cert_names:
        cert = get_server_certificate(cert_name)
        if not cert:
            continue
        cert_body = cert.get("certificate_body", None)
        if not _compare_cert(new_cert, cert_body):
            continue
        module.fail_json(
            changed=False,
            msg=f"This certificate already exists under the name {cert_name} and dup_ok=False",
            duplicate_cert=cert,
        )


def _compare_cert(cert_a, cert_b):
    if not cert_a and not cert_b:
        return True
    if not cert_a or not cert_b:
        return False
    # Trim out the whitespace before comparing the certs.  While this could mean
    # an invalid cert 'matches' a valid cert, that's better than some stray
    # whitespace breaking things
    cert_a.replace("\r", "")
    cert_a.replace("\n", "")
    cert_a.replace(" ", "")
    cert_b.replace("\r", "")
    cert_b.replace("\n", "")
    cert_b.replace(" ", "")

    return cert_a == cert_b


def update_server_certificate(current_cert):
    changed = False
    cert = module.params.get("cert")
    cert_chain = module.params.get("cert_chain")

    if not _compare_cert(cert, current_cert.get("certificate_body", None)):
        module.fail_json(msg="Modifying the certificate body is not supported by AWS")
    if not _compare_cert(cert_chain, current_cert.get("certificate_chain", None)):
        module.fail_json(msg="Modifying the chaining certificate is not supported by AWS")
    # We can't compare keys.

    if module.check_mode:
        return changed

    # For now we can't make any changes.  Updates to tagging would go here and
    # update 'changed'

    return changed


def create_server_certificate():
    cert = module.params.get("cert")
    key = module.params.get("key")
    cert_chain = module.params.get("cert_chain")

    if not module.params.get("dup_ok"):
        check_duplicate_cert(cert)

    path = module.params.get("path")
    name = module.params.get("name")

    params = dict(
        ServerCertificateName=name,
        CertificateBody=cert,
        PrivateKey=key,
    )

    if cert_chain:
        params["CertificateChain"] = cert_chain
    if path:
        params["Path"] = path

    if module.check_mode:
        return True

    try:
        client.upload_server_certificate(aws_retry=True, **params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg=f"Failed to update server certificate {name}")

    return True


def rename_server_certificate(current_cert):
    name = module.params.get("name")
    new_name = module.params.get("new_name")
    new_path = module.params.get("new_path")

    changes = dict()

    # Try to be nice, if we've already been renamed exit quietly.
    if not current_cert:
        current_cert = get_server_certificate(new_name)
    else:
        if new_name:
            changes["NewServerCertificateName"] = new_name

    cert_metadata = current_cert.get("server_certificate_metadata", {})

    if not current_cert:
        module.fail_json(msg=f"Unable to find certificate {name}")

    current_path = cert_metadata.get("path", None)
    if new_path and current_path != new_path:
        changes["NewPath"] = new_path

    if not changes:
        return False

    if module.check_mode:
        return True

    try:
        client.update_server_certificate(aws_retry=True, ServerCertificateName=name, **changes)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg=f"Failed to update server certificate {name}", changes=changes)

    return True


def delete_server_certificate(current_cert):
    if not current_cert:
        return False

    if module.check_mode:
        return True

    name = module.params.get("name")

    try:
        result = client.delete_server_certificate(
            aws_retry=True,
            ServerCertificateName=name,
        )
    except is_boto3_error_code("NoSuchEntity"):
        return None
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg=f"Failed to delete server certificate {name}")

    return True


def get_server_certificate(name):
    if not name:
        return None
    try:
        result = client.get_server_certificate(
            aws_retry=True,
            ServerCertificateName=name,
        )
    except is_boto3_error_code("NoSuchEntity"):
        return None
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg=f"Failed to get server certificate {name}")
    cert = dict(camel_dict_to_snake_dict(result.get("ServerCertificate")))
    return cert


def compatability_results(current_cert):
    compat_results = dict()

    if not current_cert:
        return compat_results

    metadata = current_cert.get("server_certificate_metadata", {})

    if current_cert.get("certificate_body", None):
        compat_results["cert_body"] = current_cert.get("certificate_body")
    if current_cert.get("certificate_chain", None):
        compat_results["chain_cert_body"] = current_cert.get("certificate_chain")
    if metadata.get("arn", None):
        compat_results["arn"] = metadata.get("arn")
    if metadata.get("expiration", None):
        compat_results["expiration_date"] = metadata.get("expiration")
    if metadata.get("path", None):
        compat_results["cert_path"] = metadata.get("path")
    if metadata.get("server_certificate_name", None):
        compat_results["name"] = metadata.get("server_certificate_name")
    if metadata.get("upload_date", None):
        compat_results["upload_date"] = metadata.get("upload_date")

    return compat_results


def main():
    global module
    global client

    argument_spec = dict(
        state=dict(required=True, choices=["present", "absent"]),
        name=dict(required=True),
        cert=dict(),
        key=dict(no_log=True),
        cert_chain=dict(),
        new_name=dict(),
        path=dict(default="/"),
        new_path=dict(),
        dup_ok=dict(type="bool", default=True),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ["new_path", "key"],
            ["new_path", "cert"],
            ["new_path", "cert_chain"],
            ["new_name", "key"],
            ["new_name", "cert"],
            ["new_name", "cert_chain"],
        ],
        supports_check_mode=True,
    )

    client = module.client("iam", retry_decorator=AWSRetry.jittered_backoff())

    state = module.params.get("state")
    name = module.params.get("name")
    path = module.params.get("path")
    new_name = module.params.get("new_name")
    new_path = module.params.get("new_path")
    dup_ok = module.params.get("dup_ok")

    current_cert = get_server_certificate(name)

    results = dict()
    if state == "absent":
        changed = delete_server_certificate(current_cert)
        if changed:
            results["deleted_cert"] = name
        else:
            msg = f"Certificate with the name {name} already absent"
            results["msg"] = msg
    else:
        if new_name or new_path:
            changed = rename_server_certificate(current_cert)
            if new_name:
                name = new_name
            updated_cert = get_server_certificate(name)
        elif current_cert:
            changed = update_server_certificate(current_cert)
            updated_cert = get_server_certificate(name)
        else:
            changed = create_server_certificate()
            updated_cert = get_server_certificate(name)

        results["server_certificate"] = updated_cert
        compat_results = compatability_results(updated_cert)
        if compat_results:
            results.update(compat_results)

    module.exit_json(changed=changed, **results)


if __name__ == "__main__":
    main()
