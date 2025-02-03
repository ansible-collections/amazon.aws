# -*- coding: utf-8 -*-
#
# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

from ansible_collections.amazon.aws.plugins.module_utils import s3


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
