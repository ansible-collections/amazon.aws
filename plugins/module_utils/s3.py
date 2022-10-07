# Copyright (c) 2018 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import to_text
from ansible.module_utils.six.moves.urllib.parse import urlparse
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import get_aws_connection_info


try:
    import botocore
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass    # Handled by the calling module

HAS_MD5 = True
try:
    from hashlib import md5
except ImportError:
    try:
        from md5 import md5
    except ImportError:
        HAS_MD5 = False


import string


def calculate_etag(module, filename, etag, s3, bucket, obj, version=None):
    if not HAS_MD5:
        return None

    if '-' in etag:
        # Multi-part ETag; a hash of the hashes of each part.
        parts = int(etag[1:-1].split('-')[1])
        digests = []

        s3_kwargs = dict(
            Bucket=bucket,
            Key=obj,
        )
        if version:
            s3_kwargs['VersionId'] = version

        with open(filename, 'rb') as f:
            for part_num in range(1, parts + 1):
                s3_kwargs['PartNumber'] = part_num
                try:
                    head = s3.head_object(**s3_kwargs)
                except (BotoCoreError, ClientError) as e:
                    module.fail_json_aws(e, msg="Failed to get head object")
                digests.append(md5(f.read(int(head['ContentLength']))))

        digest_squared = md5(b''.join(m.digest() for m in digests))
        return '"{0}-{1}"'.format(digest_squared.hexdigest(), len(digests))
    else:  # Compute the MD5 sum normally
        return '"{0}"'.format(module.md5(filename))


def calculate_etag_content(module, content, etag, s3, bucket, obj, version=None):
    if not HAS_MD5:
        return None

    if '-' in etag:
        # Multi-part ETag; a hash of the hashes of each part.
        parts = int(etag[1:-1].split('-')[1])
        digests = []
        offset = 0

        s3_kwargs = dict(
            Bucket=bucket,
            Key=obj,
        )
        if version:
            s3_kwargs['VersionId'] = version

        for part_num in range(1, parts + 1):
            s3_kwargs['PartNumber'] = part_num
            try:
                head = s3.head_object(**s3_kwargs)
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg="Failed to get head object")
            length = int(head['ContentLength'])
            digests.append(md5(content[offset:offset + length]))
            offset += length

        digest_squared = md5(b''.join(m.digest() for m in digests))
        return '"{0}-{1}"'.format(digest_squared.hexdigest(), len(digests))
    else:  # Compute the MD5 sum normally
        return '"{0}"'.format(md5(content).hexdigest())


def validate_bucket_name(module, name):
    # See: https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html
    if len(name) < 3:
        module.fail_json(msg='the length of an S3 bucket must be at least 3 characters')
    if len(name) > 63:
        module.fail_json(msg='the length of an S3 bucket cannot exceed 63 characters')

    legal_characters = string.ascii_lowercase + ".-" + string.digits
    illegal_characters = [c for c in name if c not in legal_characters]
    if illegal_characters:
        module.fail_json(msg='invalid character(s) found in the bucket name')
    if name[-1] not in string.ascii_lowercase + string.digits:
        module.fail_json(msg='bucket names must begin and end with a letter or number')
    return True


# To get S3 connection, in case of dealing with ceph, dualstack, etc.
def is_fakes3(endpoint_url):
    """ Return True if endpoint_url has scheme fakes3:// """
    result = False
    if endpoint_url is not None:
        result = urlparse(endpoint_url).scheme in ('fakes3', 'fakes3s')
    return result


def get_s3_connection(module, aws_connect_kwargs, location, ceph, endpoint_url, sig_4=False):
    params = dict(
        conn_type='client',
        resource='s3',
        region=location,
        endpoint=endpoint_url,
        **aws_connect_kwargs
    )
    if ceph:  # TODO - test this
        ceph = urlparse(endpoint_url)
        use_ssl = bool(ceph.scheme == 'https')
        params.update(
            dict(
                use_ssl=use_ssl
            )
        )
    elif is_fakes3(endpoint_url):
        fakes3 = urlparse(endpoint_url)
        protocol = "http"
        port = fakes3.port or 80
        if fakes3.scheme == 'fakes3s':
            protocol = "https"
            port = fakes3.port or 443
        endpoint_url = f"{protocol}://{fakes3.hostname}:{to_text(port)}"
        use_ssl = bool(fakes3.scheme == 'fakes3s')
        params.update(
            dict(
                endpoint=endpoint_url,
                use_ssl=use_ssl,
            )
        )
    else:
        mode = module.params.get("mode")
        encryption_mode = module.params.get("encryption_mode")
        config = None
        if (mode in ('get', 'getstr') and sig_4) or (mode == "put" and encryption_mode == "aws:kms"):
            config = botocore.client.Config(signature_version='s3v4')
        if module.params.get("dualstack"):
            use_dualstack = dict(use_dualstack_endpoint=True)
            if config is not None:
                config.merge(botocore.client.Config(s3=use_dualstack))
            else:
                config = botocore.client.Config(s3=use_dualstack)
        if config:
            params.update(
                dict(
                    config=config
                )
            )
    return module.boto3_conn(**params)
