# Copyright (c) 2018 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import to_text
from urllib.parse import urlparse

from .botocore import boto3_conn

try:
    from botocore.client import Config
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


def s3_head_objects(client, parts, bucket, obj, versionId):
    args = {"Bucket": bucket, "Key": obj}
    if versionId:
        args["VersionId"] = versionId

    for part in range(1, parts + 1):
        args["PartNumber"] = part
        yield client.head_object(**args)


def calculate_checksum_with_file(client, parts, bucket, obj, versionId, filename):
    digests = []
    with open(filename, 'rb') as f:
        for head in s3_head_objects(client, parts, bucket, obj, versionId):
            digests.append(md5(f.read(int(head['ContentLength']))).digest())

    digest_squared = b''.join(digests)
    return '"{0}-{1}"'.format(md5(digest_squared).hexdigest(), len(digests))


def calculate_checksum_with_content(client, parts, bucket, obj, versionId, content):
    digests = []
    offset = 0
    for head in s3_head_objects(client, parts, bucket, obj, versionId):
        length = int(head['ContentLength'])
        digests.append(md5(content[offset:offset + length]).digest())
        offset += length

    digest_squared = b''.join(digests)
    return '"{0}-{1}"'.format(md5(digest_squared).hexdigest(), len(digests))


def calculate_etag(module, filename, etag, s3, bucket, obj, version=None):
    if not HAS_MD5:
        return None

    if '-' in etag:
        # Multi-part ETag; a hash of the hashes of each part.
        parts = int(etag[1:-1].split('-')[1])
        try:
            return calculate_checksum_with_file(s3, parts, bucket, obj, version, filename)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Failed to get head object")
    else:  # Compute the MD5 sum normally
        return '"{0}"'.format(module.md5(filename))


def calculate_etag_content(module, content, etag, s3, bucket, obj, version=None):
    if not HAS_MD5:
        return None

    if '-' in etag:
        # Multi-part ETag; a hash of the hashes of each part.
        parts = int(etag[1:-1].split('-')[1])
        try:
            return calculate_checksum_with_content(s3, parts, bucket, obj, version, content)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Failed to get head object")
    else:  # Compute the MD5 sum normally
        return '"{0}"'.format(md5(content).hexdigest())


def validate_bucket_name(name):
    # See: https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html
    if len(name) < 3:
        return 'the length of an S3 bucket must be at least 3 characters'
    if len(name) > 63:
        return 'the length of an S3 bucket cannot exceed 63 characters'

    legal_characters = string.ascii_lowercase + ".-" + string.digits
    illegal_characters = [c for c in name if c not in legal_characters]
    if illegal_characters:
        return 'invalid character(s) found in the bucket name'
    if name[-1] not in string.ascii_lowercase + string.digits:
        return 'bucket names must begin and end with a letter or number'
    return None


# Spot special case of fakes3.
def is_fakes3(url):
    """ Return True if endpoint_url has scheme fakes3:// """
    result = False
    if url is not None:
        result = urlparse(url).scheme in ('fakes3', 'fakes3s')
    return result


def parse_fakes3_endpoint(url):
    fakes3 = urlparse(url)
    protocol = "http"
    port = fakes3.port or 80
    if fakes3.scheme == 'fakes3s':
        protocol = "https"
        port = fakes3.port or 443
    endpoint_url = f"{protocol}://{fakes3.hostname}:{to_text(port)}"
    use_ssl = bool(fakes3.scheme == 'fakes3s')
    return {"endpoint": endpoint_url, "use_ssl": use_ssl}


def parse_ceph_endpoint(url):
    ceph = urlparse(url)
    use_ssl = bool(ceph.scheme == 'https')
    return {"endpoint": url, "use_ssl": use_ssl}


def parse_default_endpoint(url, mode, encryption_mode, dualstack, sig_4):
    result = {"endpoint": url}
    config = {}
    if (mode in ('get', 'getstr') and sig_4) or (mode == "put" and encryption_mode == "aws:kms"):
        config["signature_version"] = "s3v4"
    if dualstack:
        config["s3"] = {"use_dualstack_endpoint": True}
    if config != {}:
        result["config"] = Config(**config)
    return result


def s3_conn_params(mode, encryption_mode, dualstack, aws_connect_kwargs, location, ceph, endpoint_url, sig_4=False):
    params = {"conn_type": "client", "resource": "s3", "region": location, **aws_connect_kwargs}
    if ceph:
        endpoint_p = parse_ceph_endpoint(endpoint_url)
    elif is_fakes3(endpoint_url):
        endpoint_p = parse_fakes3_endpoint(endpoint_url)
    else:
        endpoint_p = parse_default_endpoint(endpoint_url, mode, encryption_mode, dualstack, sig_4)

    params.update(endpoint_p)
    return params


def get_s3_connection(module, aws_connect_kwargs, location, ceph, endpoint_url, sig_4=False):
    s3_conn = s3_conn_params(module.params.get("mode"),
                             module.params.get("encryption_mode"),
                             module.params.get("dualstack"),
                             aws_connect_kwargs,
                             location,
                             ceph,
                             endpoint_url,
                             sig_4)
    return boto3_conn(module, **s3_conn)
