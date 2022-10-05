#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: iam_server_certificate_info
version_added: 1.0.0
short_description: Retrieve the information of a server certificate
description:
  - Retrieve the attributes of a server certificate.
author: "Allen Sanabria (@linuxdynasty)"
options:
  name:
    description:
      - The name of the server certificate you are retrieving attributes for.
    type: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
- amazon.aws.boto3

'''

EXAMPLES = '''
- name: Retrieve server certificate
  community.aws.iam_server_certificate_info:
    name: production-cert
  register: server_cert

- name: Fail if the server certificate name was not found
  community.aws.iam_server_certificate_info:
    name: production-cert
  register: server_cert
  failed_when: "{{ server_cert.results | length == 0 }}"
'''

RETURN = '''
server_certificate_id:
    description: The 21 character certificate id
    returned: success
    type: str
    sample: "ADWAJXWTZAXIPIMQHMJPO"
certificate_body:
    description: The asn1der encoded PEM string
    returned: success
    type: str
    sample: "-----BEGIN CERTIFICATE-----\nbunch of random data\n-----END CERTIFICATE-----"
server_certificate_name:
    description: The name of the server certificate
    returned: success
    type: str
    sample: "server-cert-name"
arn:
    description: The Amazon resource name of the server certificate
    returned: success
    type: str
    sample: "arn:aws:iam::123456789012:server-certificate/server-cert-name"
path:
    description: The path of the server certificate
    returned: success
    type: str
    sample: "/"
expiration:
    description: The date and time this server certificate will expire, in ISO 8601 format.
    returned: success
    type: str
    sample: "2017-06-15T12:00:00+00:00"
upload_date:
    description: The date and time this server certificate was uploaded, in ISO 8601 format.
    returned: success
    type: str
    sample: "2015-04-25T00:36:40+00:00"
'''


try:
    import botocore
    import botocore.exceptions
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule


def get_server_certs(iam, name=None):
    """Retrieve the attributes of a server certificate if it exists or all certs.
    Args:
        iam (botocore.client.IAM): The boto3 iam instance.

    Kwargs:
        name (str): The name of the server certificate.

    Basic Usage:
        >>> import boto3
        >>> iam = boto3.client('iam')
        >>> name = "server-cert-name"
        >>> results = get_server_certs(iam, name)
        {
            "upload_date": "2015-04-25T00:36:40+00:00",
            "server_certificate_id": "ADWAJXWTZAXIPIMQHMJPO",
            "certificate_body": "-----BEGIN CERTIFICATE-----\nbunch of random data\n-----END CERTIFICATE-----",
            "server_certificate_name": "server-cert-name",
            "expiration": "2017-06-15T12:00:00+00:00",
            "path": "/",
            "arn": "arn:aws:iam::123456789012:server-certificate/server-cert-name"
        }
    """
    results = dict()
    try:
        if name:
            server_certs = [iam.get_server_certificate(ServerCertificateName=name)['ServerCertificate']]
        else:
            server_certs = iam.list_server_certificates()['ServerCertificateMetadataList']

        for server_cert in server_certs:
            if not name:
                server_cert = iam.get_server_certificate(ServerCertificateName=server_cert['ServerCertificateName'])['ServerCertificate']
            cert_md = server_cert['ServerCertificateMetadata']
            results[cert_md['ServerCertificateName']] = {
                'certificate_body': server_cert['CertificateBody'],
                'server_certificate_id': cert_md['ServerCertificateId'],
                'server_certificate_name': cert_md['ServerCertificateName'],
                'arn': cert_md['Arn'],
                'path': cert_md['Path'],
                'expiration': cert_md['Expiration'].isoformat(),
                'upload_date': cert_md['UploadDate'].isoformat(),
            }

    except botocore.exceptions.ClientError:
        pass

    return results


def main():
    argument_spec = dict(
        name=dict(type='str'),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        iam = module.client('iam')
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    cert_name = module.params.get('name')
    results = get_server_certs(iam, cert_name)
    module.exit_json(results=results)


if __name__ == '__main__':
    main()
