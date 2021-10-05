# (c) 2017 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest

from ansible_collections.amazon.aws.plugins.module_utils.policy import compare_policies


class PolicyUtils(unittest.TestCase):

    # ========================================================
    # Setup some initial data that we can use within our tests
    # ========================================================
    def setUp(self):
        # A pair of simple IAM Trust relationships using bools, the first a
        # native bool the second a quoted string
        self.bool_policy_bool = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    "Action": "sts:AssumeRole",
                    "Condition": {
                        "Bool": {"aws:MultiFactorAuthPresent": True}
                    },
                    "Effect": "Allow",
                    "Principal": {"AWS": "arn:aws:iam::XXXXXXXXXXXX:root"},
                    "Sid": "AssumeRoleWithBoolean"
                }
            ]
        }

        self.bool_policy_string = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    "Action": "sts:AssumeRole",
                    "Condition": {
                        "Bool": {"aws:MultiFactorAuthPresent": "true"}
                    },
                    "Effect": "Allow",
                    "Principal": {"AWS": "arn:aws:iam::XXXXXXXXXXXX:root"},
                    "Sid": "AssumeRoleWithBoolean"
                }
            ]
        }

        # A pair of simple bucket policies using numbers, the first a
        # native int the second a quoted string
        self.numeric_policy_number = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    "Action": "s3:ListBucket",
                    "Condition": {
                        "NumericLessThanEquals": {"s3:max-keys": 15}
                    },
                    "Effect": "Allow",
                    "Resource": "arn:aws:s3:::examplebucket",
                    "Sid": "s3ListBucketWithNumericLimit"
                }
            ]
        }

        self.numeric_policy_string = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    "Action": "s3:ListBucket",
                    "Condition": {
                        "NumericLessThanEquals": {"s3:max-keys": "15"}
                    },
                    "Effect": "Allow",
                    "Resource": "arn:aws:s3:::examplebucket",
                    "Sid": "s3ListBucketWithNumericLimit"
                }
            ]
        }

        self.small_policy_one = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 's3:PutObjectAcl',
                    'Sid': 'AddCannedAcl2',
                    'Resource': 'arn:aws:s3:::test_policy/*',
                    'Effect': 'Allow',
                    'Principal': {'AWS': ['arn:aws:iam::XXXXXXXXXXXX:user/username1', 'arn:aws:iam::XXXXXXXXXXXX:user/username2']}
                }
            ]
        }

        # The same as small_policy_one, except the single resource is in a list and the contents of Statement are jumbled
        self.small_policy_two = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Effect': 'Allow',
                    'Action': 's3:PutObjectAcl',
                    'Principal': {'AWS': ['arn:aws:iam::XXXXXXXXXXXX:user/username1', 'arn:aws:iam::XXXXXXXXXXXX:user/username2']},
                    'Resource': ['arn:aws:s3:::test_policy/*'],
                    'Sid': 'AddCannedAcl2'
                }
            ]
        }

        self.version_policy_missing = {
            'Statement': [
                {
                    'Action': 's3:PutObjectAcl',
                    'Sid': 'AddCannedAcl2',
                    'Resource': 'arn:aws:s3:::test_policy/*',
                    'Effect': 'Allow',
                    'Principal': {'AWS': ['arn:aws:iam::XXXXXXXXXXXX:user/username1', 'arn:aws:iam::XXXXXXXXXXXX:user/username2']}
                }
            ]
        }

        self.version_policy_old = {
            'Version': '2008-10-17',
            'Statement': [
                {
                    'Action': 's3:PutObjectAcl',
                    'Sid': 'AddCannedAcl2',
                    'Resource': 'arn:aws:s3:::test_policy/*',
                    'Effect': 'Allow',
                    'Principal': {'AWS': ['arn:aws:iam::XXXXXXXXXXXX:user/username1', 'arn:aws:iam::XXXXXXXXXXXX:user/username2']}
                }
            ]
        }

        self.version_policy_new = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 's3:PutObjectAcl',
                    'Sid': 'AddCannedAcl2',
                    'Resource': 'arn:aws:s3:::test_policy/*',
                    'Effect': 'Allow',
                    'Principal': {'AWS': ['arn:aws:iam::XXXXXXXXXXXX:user/username1', 'arn:aws:iam::XXXXXXXXXXXX:user/username2']}
                }
            ]
        }

        self.larger_policy_one = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Test",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": [
                            "arn:aws:iam::XXXXXXXXXXXX:user/testuser1",
                            "arn:aws:iam::XXXXXXXXXXXX:user/testuser2"
                        ]
                    },
                    "Action": "s3:PutObjectAcl",
                    "Resource": "arn:aws:s3:::test_policy/*"
                },
                {
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": "arn:aws:iam::XXXXXXXXXXXX:user/testuser2"
                    },
                    "Action": [
                        "s3:PutObject",
                        "s3:PutObjectAcl"
                    ],
                    "Resource": "arn:aws:s3:::test_policy/*"
                }
            ]
        }

        # The same as larger_policy_one, except having a list of length 1 and jumbled contents
        self.larger_policy_two = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Principal": {
                       "AWS": ["arn:aws:iam::XXXXXXXXXXXX:user/testuser2"]
                    },
                    "Effect": "Allow",
                    "Resource": "arn:aws:s3:::test_policy/*",
                    "Action": [
                        "s3:PutObject",
                        "s3:PutObjectAcl"
                    ]
                },
                {
                    "Action": "s3:PutObjectAcl",
                    "Principal": {
                        "AWS": [
                            "arn:aws:iam::XXXXXXXXXXXX:user/testuser1",
                            "arn:aws:iam::XXXXXXXXXXXX:user/testuser2"
                        ]
                    },
                    "Sid": "Test",
                    "Resource": "arn:aws:s3:::test_policy/*",
                    "Effect": "Allow"
                }
            ]
        }

        # Different than larger_policy_two: a different principal is given
        self.larger_policy_three = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Principal": {
                        "AWS": ["arn:aws:iam::XXXXXXXXXXXX:user/testuser2"]
                    },
                    "Effect": "Allow",
                    "Resource": "arn:aws:s3:::test_policy/*",
                    "Action": [
                        "s3:PutObject",
                        "s3:PutObjectAcl"]
                },
                {
                    "Action": "s3:PutObjectAcl",
                    "Principal": {
                        "AWS": [
                            "arn:aws:iam::XXXXXXXXXXXX:user/testuser1",
                            "arn:aws:iam::XXXXXXXXXXXX:user/testuser3"
                        ]
                    },
                    "Sid": "Test",
                    "Resource": "arn:aws:s3:::test_policy/*",
                    "Effect": "Allow"
                }
            ]
        }

        # Minimal policy using wildcarded Principal
        self.wildcard_policy_one = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Principal": {
                        "AWS": ["*"]
                    },
                    "Effect": "Allow",
                    "Resource": "arn:aws:s3:::test_policy/*",
                    "Action": [
                        "s3:PutObject",
                        "s3:PutObjectAcl"]
                }
            ]
        }

        # Minimal policy using wildcarded Principal
        self.wildcard_policy_two = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Principal": "*",
                    "Effect": "Allow",
                    "Resource": "arn:aws:s3:::test_policy/*",
                    "Action": [
                        "s3:PutObject",
                        "s3:PutObjectAcl"]
                }
            ]
        }

    # ========================================================
    #   ec2.compare_policies
    # ========================================================

    def test_compare_small_policies_without_differences(self):
        """ Testing two small policies which are identical except for:
                * The contents of the statement are in different orders
                * The second policy contains a list of length one whereas in the first it is a string
        """
        self.assertFalse(compare_policies(self.small_policy_one, self.small_policy_two))

    def test_compare_large_policies_without_differences(self):
        """ Testing two larger policies which are identical except for:
                * The statements are in different orders
                * The contents of the statements are also in different orders
                * The second contains a list of length one for the Principal whereas in the first it is a string
        """
        self.assertFalse(compare_policies(self.larger_policy_one, self.larger_policy_two))

    def test_compare_larger_policies_with_difference(self):
        """ Testing two larger policies which are identical except for:
                * one different principal
        """
        self.assertTrue(compare_policies(self.larger_policy_two, self.larger_policy_three))

    def test_compare_smaller_policy_with_larger(self):
        """ Testing two policies of different sizes """
        self.assertTrue(compare_policies(self.larger_policy_one, self.small_policy_one))

    def test_compare_boolean_policy_bool_and_string_are_equal(self):
        """ Testing two policies one using a quoted boolean, the other a bool """
        self.assertFalse(compare_policies(self.bool_policy_string, self.bool_policy_bool))

    def test_compare_numeric_policy_number_and_string_are_equal(self):
        """ Testing two policies one using a quoted number, the other an int """
        self.assertFalse(compare_policies(self.numeric_policy_string, self.numeric_policy_number))

    def test_compare_version_policies_defaults_old(self):
        """ Testing that a policy without Version is considered identical to one
        with the 'old' Version (by default)
        """
        self.assertFalse(compare_policies(self.version_policy_old, self.version_policy_missing))
        self.assertTrue(compare_policies(self.version_policy_new, self.version_policy_missing))

    def test_compare_version_policies_default_disabled(self):
        """ Testing that a policy without Version not considered identical when default_version=None
        """
        self.assertFalse(compare_policies(self.version_policy_missing, self.version_policy_missing, default_version=None))
        self.assertTrue(compare_policies(self.version_policy_old, self.version_policy_missing, default_version=None))
        self.assertTrue(compare_policies(self.version_policy_new, self.version_policy_missing, default_version=None))

    def test_compare_version_policies_default_set(self):
        """ Testing that a policy without Version is only considered identical
        when default_version="2008-10-17"
        """
        self.assertFalse(compare_policies(self.version_policy_missing, self.version_policy_missing, default_version="2012-10-17"))
        self.assertTrue(compare_policies(self.version_policy_old, self.version_policy_missing, default_version="2012-10-17"))
        self.assertFalse(compare_policies(self.version_policy_old, self.version_policy_missing, default_version="2008-10-17"))
        self.assertFalse(compare_policies(self.version_policy_new, self.version_policy_missing, default_version="2012-10-17"))
        self.assertTrue(compare_policies(self.version_policy_new, self.version_policy_missing, default_version="2008-10-17"))

    def test_compare_version_policies_with_none(self):
        """ Testing that comparing with no policy works
        """
        self.assertTrue(compare_policies(self.small_policy_one, None))
        self.assertTrue(compare_policies(None, self.small_policy_one))
        self.assertFalse(compare_policies(None, None))

    def test_compare_wildcard_policies_without_differences(self):
        """ Testing two small wildcard policies which are identical except for:
                * Principal: "*" vs Principal: ["AWS": "*"]
        """
        self.assertFalse(compare_policies(self.wildcard_policy_one, self.wildcard_policy_two))
