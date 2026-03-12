# -*- coding: utf-8 -*-
# Copyright: Ansible Project
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest

try:
    import botocore.exceptions

    HAS_BOTOCORE = True
except ImportError:
    HAS_BOTOCORE = False

from ansible_collections.amazon.aws.plugins.module_utils.botocore import boto_exception

if not HAS_BOTOCORE:
    pytestmark = pytest.mark.skip("test_boto_exception.py requires botocore")


class TestBotoException:
    """Test suite for boto_exception() function."""

    def test_client_error_with_message(self):
        """Test ClientError which has message attribute."""
        error = botocore.exceptions.ClientError(
            {
                "Error": {"Code": "AccessDenied", "Message": "Access denied to resource"},
                "ResponseMetadata": {"RequestId": "01234567-89ab-cdef-0123-456789abcdef"},
            },
            "GetObject",
        )

        result = boto_exception(error)

        assert "Access denied to resource" in result

    def test_no_credentials_error(self):
        """Test NoCredentialsError without special message attributes."""
        error = botocore.exceptions.NoCredentialsError()

        result = boto_exception(error)

        assert "<class 'Exception'>" in result or "Exception" in result

    def test_generic_exception(self):
        """Test generic Exception without error_message or message attributes."""
        error = Exception("Generic exception occurred")

        result = boto_exception(error)

        assert "Generic exception occurred" in result
