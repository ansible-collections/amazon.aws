#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: test_s3_upload_multipart
short_description: Create object using multipart upload
description:
  - This module is used to create object into S3 bucket using multipart upload.
  - Multipart upload allows to upload a single object as a set of parts.
  - This module is exclusively used to test collection `amazon.aws`.
options:
  bucket:
    description:
      - Bucket name.
    required: true
    type: str
  object:
    description:
      - Key name of the object.
    type: str
    required: true
  part_size:
    description:
      - Part size in MB.
    type: int
    default: 10
  parts:
    description:
      - Number of parts.
    type: int
    default: 6
author:
  - "Aubin Bikouo (@abikouo)"
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""


try:
    import boto3
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

import random
import string

from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.s3 import s3_extra_params


def generate_content(length):
    return "".join([random.choice(string.ascii_letters + string.digits) for i in range(length)])


def updload_parts(s3, parts, part_size, **kwargs):
    multiparts = []
    for part_id in range(1, parts + 1):
        response = s3.upload_part(
            Body=str.encode(generate_content(part_size * 1024 * 1024)), PartNumber=part_id, **kwargs
        )

        multiparts.append(
            {
                "PartNumber": part_id,
                "ETag": response.get("ETag"),
            }
        )
    return multiparts


def main():
    argument_spec = dict(
        bucket=dict(required=True),
        object=dict(required=True),
        parts=dict(type="int", default=6),
        part_size=dict(type="int", default=10),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    bucket = module.params.get("bucket")
    object_key = module.params.get("object")
    part_size = module.params.get("part_size")
    parts = module.params.get("parts")

    extra_params = s3_extra_params(module.params)
    retry_decorator = AWSRetry.jittered_backoff()
    try:
        s3 = module.client("s3", retry_decorator=retry_decorator, **extra_params)
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
        boto3.exceptions.Boto3Error,
    ) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    # create multipart upload
    response = s3.create_multipart_upload(Bucket=bucket, Key=object_key)
    upload_id = response.get("UploadId")

    # upload parts
    upload_params = {
        "Bucket": bucket,
        "Key": object_key,
        "UploadId": upload_id,
    }

    multiparts = updload_parts(s3, parts, part_size, **upload_params)

    # complete the upload
    response = s3.complete_multipart_upload(
        Bucket=bucket,
        Key=object_key,
        MultipartUpload={"Parts": multiparts},
        UploadId=upload_id,
    )

    response.pop("ResponseMetadata", None)
    module.exit_json(changed=True, s3_object=snake_dict_to_camel_dict(response))


if __name__ == "__main__":
    main()
