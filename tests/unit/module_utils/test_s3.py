#
# (c) 2021 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.amazon.aws.tests.unit.compat.mock import MagicMock
from ansible_collections.amazon.aws.plugins.module_utils import s3


def test_validate_bucket_name():
    module = MagicMock()

    assert s3.validate_bucket_name(module, "docexamplebucket1") is True
    assert not module.fail_json.called
    assert s3.validate_bucket_name(module, "log-delivery-march-2020") is True
    assert not module.fail_json.called
    assert s3.validate_bucket_name(module, "my-hosted-content") is True
    assert not module.fail_json.called

    assert s3.validate_bucket_name(module, "docexamplewebsite.com") is True
    assert not module.fail_json.called
    assert s3.validate_bucket_name(module, "www.docexamplewebsite.com") is True
    assert not module.fail_json.called
    assert s3.validate_bucket_name(module, "my.example.s3.bucket") is True
    assert not module.fail_json.called
    assert s3.validate_bucket_name(module, "doc") is True
    assert not module.fail_json.called

    module.fail_json.reset_mock()
    s3.validate_bucket_name(module, "doc_example_bucket")
    assert module.fail_json.called

    module.fail_json.reset_mock()
    s3.validate_bucket_name(module, "DocExampleBucket")
    assert module.fail_json.called
    module.fail_json.reset_mock()
    s3.validate_bucket_name(module, "doc-example-bucket-")
    assert module.fail_json.called
    s3.validate_bucket_name(module, "my")
    assert module.fail_json.called
