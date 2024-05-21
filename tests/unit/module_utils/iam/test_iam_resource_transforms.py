# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


import dateutil

from ansible_collections.amazon.aws.plugins.module_utils.iam import normalize_iam_access_key
from ansible_collections.amazon.aws.plugins.module_utils.iam import normalize_iam_access_keys
from ansible_collections.amazon.aws.plugins.module_utils.iam import normalize_iam_group
from ansible_collections.amazon.aws.plugins.module_utils.iam import normalize_iam_instance_profile
from ansible_collections.amazon.aws.plugins.module_utils.iam import normalize_iam_mfa_device
from ansible_collections.amazon.aws.plugins.module_utils.iam import normalize_iam_mfa_devices
from ansible_collections.amazon.aws.plugins.module_utils.iam import normalize_iam_policy
from ansible_collections.amazon.aws.plugins.module_utils.iam import normalize_iam_role
from ansible_collections.amazon.aws.plugins.module_utils.iam import normalize_iam_user

# The various normalize_ functions are based upon ..transformation.boto3_resource_to_ansible_dict
# As such these tests will be relatively light touch.

example_date1_txt = "2020-12-30T00:00:00.000Z"
example_date2_txt = "2021-04-26T01:23:58.000Z"
example_date1_iso = "2020-12-30T00:00:00+00:00"
example_date2_iso = "2021-04-26T01:23:58+00:00"
example_date1 = dateutil.parser.parse(example_date1_txt)
example_date2 = dateutil.parser.parse(example_date2_txt)


class TestIamResourceToAnsibleDict:
    def setup_method(self):
        pass

    def test_normalize_iam_mfa_device(self):
        INPUT = {
            "UserName": "ExampleUser",
            "SerialNumber": "arn:aws:iam::123456789012:mfa/ExampleUser",
            "EnableDate": example_date1,
        }
        OUTPUT = {
            "user_name": "ExampleUser",
            "serial_number": "arn:aws:iam::123456789012:mfa/ExampleUser",
            "enable_date": example_date1_iso,
            "tags": {},
        }

        assert OUTPUT == normalize_iam_mfa_device(INPUT)

    def test_normalize_iam_mfa_devices(self):
        INPUT = [
            {
                "UserName": "ExampleUser",
                "SerialNumber": "arn:aws:iam::123456789012:mfa/ExampleUser",
                "EnableDate": example_date1,
            }
        ]
        OUTPUT = [
            {
                "user_name": "ExampleUser",
                "serial_number": "arn:aws:iam::123456789012:mfa/ExampleUser",
                "enable_date": example_date1_iso,
                "tags": {},
            }
        ]

        assert OUTPUT == normalize_iam_mfa_devices(INPUT)

    def test_normalize_iam_user(self):
        INPUT = {
            "Path": "/MyPath/",
            "UserName": "ExampleUser",
            "UserId": "AIDU12345EXAMPLE12345",
            "Arn": "arn:aws:iam::123456789012:user/MyPath/ExampleUser",
            "CreateDate": example_date1,
            "PasswordLastUsed": example_date2,
            "PermissionsBoundary": {
                "PermissionsBoundaryType": "PermissionsBoundaryPolicy",
                "PermissionsBoundaryArn": "arn:aws:iam::123456789012:policy/ExamplePolicy",
            },
            "Tags": [
                {"Key": "MyKey", "Value": "Example Value"},
            ],
        }

        OUTPUT = {
            "path": "/MyPath/",
            "user_name": "ExampleUser",
            "user_id": "AIDU12345EXAMPLE12345",
            "arn": "arn:aws:iam::123456789012:user/MyPath/ExampleUser",
            "create_date": example_date1_iso,
            "password_last_used": example_date2_iso,
            "permissions_boundary": {
                "permissions_boundary_type": "PermissionsBoundaryPolicy",
                "permissions_boundary_arn": "arn:aws:iam::123456789012:policy/ExamplePolicy",
            },
            "tags": {"MyKey": "Example Value"},
        }

        assert OUTPUT == normalize_iam_user(INPUT)

    def test_normalize_iam_policy(self):
        INPUT = {
            "PolicyName": "AnsibleIntegratation-CI-ApplicationServices",
            "PolicyId": "ANPA12345EXAMPLE12345",
            "Arn": "arn:aws:iam::123456789012:policy/AnsibleIntegratation-CI-ApplicationServices",
            "Path": "/examples/",
            "DefaultVersionId": "v6",
            "AttachmentCount": 2,
            "PermissionsBoundaryUsageCount": 0,
            "IsAttachable": True,
            "CreateDate": example_date1,
            "UpdateDate": example_date2,
            "Tags": [
                {"Key": "MyKey", "Value": "Example Value"},
            ],
        }

        OUTPUT = {
            "policy_name": "AnsibleIntegratation-CI-ApplicationServices",
            "policy_id": "ANPA12345EXAMPLE12345",
            "arn": "arn:aws:iam::123456789012:policy/AnsibleIntegratation-CI-ApplicationServices",
            "path": "/examples/",
            "default_version_id": "v6",
            "attachment_count": 2,
            "permissions_boundary_usage_count": 0,
            "is_attachable": True,
            "create_date": example_date1_iso,
            "update_date": example_date2_iso,
            "tags": {"MyKey": "Example Value"},
        }

        assert OUTPUT == normalize_iam_policy(INPUT)

    def test_normalize_iam_group(self):
        INPUT = {
            "Users": [
                {
                    "Path": "/",
                    "UserName": "ansible_test",
                    "UserId": "AIDA12345EXAMPLE12345",
                    "Arn": "arn:aws:iam::123456789012:user/ansible_test",
                    "CreateDate": example_date1,
                    "PasswordLastUsed": example_date2,
                }
            ],
            "Group": {
                "Path": "/",
                "GroupName": "ansible-integration-ci",
                "GroupId": "AGPA01234EXAMPLE01234",
                "Arn": "arn:aws:iam::123456789012:group/ansible-integration-ci",
                "CreateDate": example_date1,
            },
            "AttachedPolicies": [
                {
                    "PolicyName": "AnsibleIntegratation-CI-Paas",
                    "PolicyArn": "arn:aws:iam::123456789012:policy/AnsibleIntegratation-CI-Paas",
                },
                {
                    "PolicyName": "AnsibleIntegratation-CI-ApplicationServices",
                    "PolicyArn": "arn:aws:iam::123456789012:policy/AnsibleIntegratation-CI-ApplicationServices",
                },
            ],
        }

        OUTPUT = {
            "users": [
                {
                    "path": "/",
                    "user_name": "ansible_test",
                    "user_id": "AIDA12345EXAMPLE12345",
                    "arn": "arn:aws:iam::123456789012:user/ansible_test",
                    "create_date": example_date1_iso,
                    "password_last_used": example_date2_iso,
                }
            ],
            "group": {
                "path": "/",
                "group_name": "ansible-integration-ci",
                "group_id": "AGPA01234EXAMPLE01234",
                "arn": "arn:aws:iam::123456789012:group/ansible-integration-ci",
                "create_date": example_date1_iso,
            },
            "attached_policies": [
                {
                    "policy_name": "AnsibleIntegratation-CI-Paas",
                    "policy_arn": "arn:aws:iam::123456789012:policy/AnsibleIntegratation-CI-Paas",
                },
                {
                    "policy_name": "AnsibleIntegratation-CI-ApplicationServices",
                    "policy_arn": "arn:aws:iam::123456789012:policy/AnsibleIntegratation-CI-ApplicationServices",
                },
            ],
        }

        assert OUTPUT == normalize_iam_group(INPUT)

    def test_normalize_access_key(self):
        INPUT = {
            "UserName": "ansible_test",
            "AccessKeyId": "AKIA12345EXAMPLE1234",
            "Status": "Active",
            "CreateDate": example_date1,
        }

        OUTPUT = {
            "user_name": "ansible_test",
            "access_key_id": "AKIA12345EXAMPLE1234",
            "status": "Active",
            "create_date": example_date1_iso,
        }

        assert OUTPUT == normalize_iam_access_key(INPUT)

    def test_normalize_access_keys(self):
        INPUT = [
            {
                "UserName": "ansible_test",
                "AccessKeyId": "AKIA12345EXAMPLE1234",
                "Status": "Active",
                "CreateDate": example_date1,
            },
            {
                "UserName": "ansible_test",
                "AccessKeyId": "AKIA01234EXAMPLE4321",
                "Status": "Active",
                "CreateDate": example_date2,
            },
        ]

        OUTPUT = [
            {
                "access_key_id": "AKIA12345EXAMPLE1234",
                "create_date": example_date1_iso,
                "status": "Active",
                "user_name": "ansible_test",
            },
            {
                "access_key_id": "AKIA01234EXAMPLE4321",
                "create_date": example_date2_iso,
                "status": "Active",
                "user_name": "ansible_test",
            },
        ]

        assert OUTPUT == normalize_iam_access_keys(INPUT)

        # Switch order to test that they're sorted by Creation Date
        INPUT = [
            {
                "UserName": "ansible_test",
                "AccessKeyId": "AKIA12345EXAMPLE1234",
                "Status": "Active",
                "CreateDate": example_date2,
            },
            {
                "UserName": "ansible_test",
                "AccessKeyId": "AKIA01234EXAMPLE4321",
                "Status": "Active",
                "CreateDate": example_date1,
            },
        ]

        OUTPUT = [
            {
                "access_key_id": "AKIA01234EXAMPLE4321",
                "create_date": example_date1_iso,
                "status": "Active",
                "user_name": "ansible_test",
            },
            {
                "access_key_id": "AKIA12345EXAMPLE1234",
                "create_date": example_date2_iso,
                "status": "Active",
                "user_name": "ansible_test",
            },
        ]

        assert OUTPUT == normalize_iam_access_keys(INPUT)

    def test_normalize_role(self):
        INPUT = {
            "Arn": "arn:aws:iam::123456789012:role/ansible-test-76640355",
            "AssumeRolePolicyDocument": {
                "Statement": [
                    {"Action": "sts:AssumeRole", "Effect": "Deny", "Principal": {"Service": "ec2.amazonaws.com"}}
                ],
                "Version": "2012-10-17",
            },
            "CreateDate": example_date1,
            "Description": "Ansible Test Role (updated) ansible-test-76640355",
            "InlinePolicies": ["inline-policy-a", "inline-policy-b"],
            "InstanceProfiles": [
                {
                    "Arn": "arn:aws:iam::123456789012:instance-profile/ansible-test-76640355",
                    "CreateDate": example_date2,
                    "InstanceProfileId": "AIPA12345EXAMPLE12345",
                    "InstanceProfileName": "ansible-test-76640355",
                    "Path": "/",
                    "Roles": [
                        {
                            "Arn": "arn:aws:iam::123456789012:role/ansible-test-76640355",
                            "AssumeRolePolicyDocument": {
                                "Statement": [
                                    {
                                        "Action": "sts:AssumeRole",
                                        "Effect": "Deny",
                                        "Principal": {"Service": "ec2.amazonaws.com"},
                                    }
                                ],
                                "Version": "2012-10-17",
                            },
                            "CreateDate": example_date1,
                            "Path": "/",
                            "RoleId": "AROA12345EXAMPLE12345",
                            "RoleName": "ansible-test-76640355",
                            # XXX Bug in iam_role_info - Tags should have been in here.
                            "Tags": [{"Key": "TagB", "Value": "ValueB"}],
                        }
                    ],
                    "Tags": [{"Key": "TagA", "Value": "Value A"}],
                }
            ],
            "ManagedPolicies": [
                {
                    "PolicyArn": "arn:aws:iam::123456789012:policy/ansible-test-76640355",
                    "PolicyName": "ansible-test-76640355",
                }
            ],
            "MaxSessionDuration": 43200,
            "Path": "/",
            "RoleId": "AROA12345EXAMPLE12345",
            "RoleLastUsed": {},
            "RoleName": "ansible-test-76640355",
            "Tags": [{"Key": "TagB", "Value": "ValueB"}],
        }

        OUTPUT = {
            "arn": "arn:aws:iam::123456789012:role/ansible-test-76640355",
            "assume_role_policy_document": {
                "Statement": [
                    {"Action": "sts:AssumeRole", "Effect": "Deny", "Principal": {"Service": "ec2.amazonaws.com"}}
                ],
                "Version": "2012-10-17",
            },
            "create_date": example_date1_iso,
            "description": "Ansible Test Role (updated) ansible-test-76640355",
            "inline_policies": ["inline-policy-a", "inline-policy-b"],
            "instance_profiles": [
                {
                    "arn": "arn:aws:iam::123456789012:instance-profile/ansible-test-76640355",
                    "create_date": example_date2_iso,
                    "instance_profile_id": "AIPA12345EXAMPLE12345",
                    "instance_profile_name": "ansible-test-76640355",
                    "path": "/",
                    "roles": [
                        {
                            "arn": "arn:aws:iam::123456789012:role/ansible-test-76640355",
                            "assume_role_policy_document": {
                                "Statement": [
                                    {
                                        "Action": "sts:AssumeRole",
                                        "Effect": "Deny",
                                        "Principal": {"Service": "ec2.amazonaws.com"},
                                    }
                                ],
                                "Version": "2012-10-17",
                            },
                            "create_date": example_date1_iso,
                            "path": "/",
                            "role_id": "AROA12345EXAMPLE12345",
                            "role_name": "ansible-test-76640355",
                            "tags": {"TagB": "ValueB"},
                        }
                    ],
                    "tags": {"TagA": "Value A"},
                }
            ],
            "managed_policies": [
                {
                    "policy_arn": "arn:aws:iam::123456789012:policy/ansible-test-76640355",
                    "policy_name": "ansible-test-76640355",
                }
            ],
            "max_session_duration": 43200,
            "path": "/",
            "role_id": "AROA12345EXAMPLE12345",
            "role_last_used": {},
            "role_name": "ansible-test-76640355",
            "tags": {"TagB": "ValueB"},
        }

        assert OUTPUT == normalize_iam_role(INPUT)

    def test_normalize_role_compat(self):
        INPUT = {
            "Arn": "arn:aws:iam::123456789012:role/ansible-test-76640355",
            "AssumeRolePolicyDocument": {
                "Statement": [
                    {"Action": "sts:AssumeRole", "Effect": "Deny", "Principal": {"Service": "ec2.amazonaws.com"}}
                ],
                "Version": "2012-10-17",
            },
            "CreateDate": example_date1,
            "Description": "Ansible Test Role (updated) ansible-test-76640355",
            "InlinePolicies": ["inline-policy-a", "inline-policy-b"],
            "InstanceProfiles": [
                {
                    "Arn": "arn:aws:iam::123456789012:instance-profile/ansible-test-76640355",
                    "CreateDate": example_date2,
                    "InstanceProfileId": "AIPA12345EXAMPLE12345",
                    "InstanceProfileName": "ansible-test-76640355",
                    "Path": "/",
                    "Roles": [
                        {
                            "Arn": "arn:aws:iam::123456789012:role/ansible-test-76640355",
                            "AssumeRolePolicyDocument": {
                                "Statement": [
                                    {
                                        "Action": "sts:AssumeRole",
                                        "Effect": "Deny",
                                        "Principal": {"Service": "ec2.amazonaws.com"},
                                    }
                                ],
                                "Version": "2012-10-17",
                            },
                            "CreateDate": example_date1,
                            "Path": "/",
                            "RoleId": "AROA12345EXAMPLE12345",
                            "RoleName": "ansible-test-76640355",
                            # XXX Bug in iam_role_info - Tags should have been in here.
                            "Tags": [{"Key": "TagB", "Value": "ValueB"}],
                        }
                    ],
                    "Tags": [{"Key": "TagA", "Value": "Value A"}],
                }
            ],
            "ManagedPolicies": [
                {
                    "PolicyArn": "arn:aws:iam::123456789012:policy/ansible-test-76640355",
                    "PolicyName": "ansible-test-76640355",
                }
            ],
            "MaxSessionDuration": 43200,
            "Path": "/",
            "RoleId": "AROA12345EXAMPLE12345",
            "RoleLastUsed": {},
            "RoleName": "ansible-test-76640355",
            "Tags": [{"Key": "TagB", "Value": "ValueB"}],
        }

        OUTPUT = {
            "arn": "arn:aws:iam::123456789012:role/ansible-test-76640355",
            "assume_role_policy_document": {
                "Statement": [
                    {"Action": "sts:AssumeRole", "Effect": "Deny", "Principal": {"Service": "ec2.amazonaws.com"}}
                ],
                "Version": "2012-10-17",
            },
            "assume_role_policy_document_raw": {
                "Statement": [
                    {"Action": "sts:AssumeRole", "Effect": "Deny", "Principal": {"Service": "ec2.amazonaws.com"}}
                ],
                "Version": "2012-10-17",
            },
            "create_date": example_date1_iso,
            "description": "Ansible Test Role (updated) ansible-test-76640355",
            "inline_policies": ["inline-policy-a", "inline-policy-b"],
            "instance_profiles": [
                {
                    "arn": "arn:aws:iam::123456789012:instance-profile/ansible-test-76640355",
                    "create_date": example_date2_iso,
                    "instance_profile_id": "AIPA12345EXAMPLE12345",
                    "instance_profile_name": "ansible-test-76640355",
                    "path": "/",
                    "roles": [
                        {
                            "arn": "arn:aws:iam::123456789012:role/ansible-test-76640355",
                            "assume_role_policy_document": {
                                "Statement": [
                                    {
                                        "Action": "sts:AssumeRole",
                                        "Effect": "Deny",
                                        "Principal": {"Service": "ec2.amazonaws.com"},
                                    }
                                ],
                                "Version": "2012-10-17",
                            },
                            "create_date": example_date1_iso,
                            "path": "/",
                            "role_id": "AROA12345EXAMPLE12345",
                            "role_name": "ansible-test-76640355",
                            "tags": {"TagB": "ValueB"},
                        }
                    ],
                    "tags": {"TagA": "Value A"},
                }
            ],
            "managed_policies": [
                {
                    "policy_arn": "arn:aws:iam::123456789012:policy/ansible-test-76640355",
                    "policy_name": "ansible-test-76640355",
                }
            ],
            "max_session_duration": 43200,
            "path": "/",
            "role_id": "AROA12345EXAMPLE12345",
            "role_last_used": {},
            "role_name": "ansible-test-76640355",
            "tags": {"TagB": "ValueB"},
        }

        assert OUTPUT == normalize_iam_role(INPUT, _v7_compat=True)

    def test_normalize_instance_profile(self):
        INPUT = {
            "Arn": "arn:aws:iam::123456789012:instance-profile/ansible-test-40050922/ansible-test-40050922",
            "CreateDate": example_date1,
            "InstanceProfileId": "AIPA12345EXAMPLE12345",
            "InstanceProfileName": "ansible-test-40050922",
            "Path": "/ansible-test-40050922/",
            "Roles": [
                {
                    "Arn": "arn:aws:iam::123456789012:role/ansible-test-40050922/ansible-test-40050922",
                    "AssumeRolePolicyDocument": {
                        "Statement": [
                            {
                                "Action": "sts:AssumeRole",
                                "Effect": "Deny",
                                "Principal": {"Service": "ec2.amazonaws.com"},
                            }
                        ],
                        "Version": "2012-10-17",
                    },
                    "CreateDate": example_date2,
                    "Path": "/ansible-test-40050922/",
                    "RoleId": "AROA12345EXAMPLE12345",
                    "RoleName": "ansible-test-40050922",
                    "Tags": [{"Key": "TagC", "Value": "ValueC"}],
                }
            ],
            "Tags": [
                {"Key": "Key with Spaces", "Value": "Value with spaces"},
                {"Key": "snake_case_key", "Value": "snake_case_value"},
                {"Key": "CamelCaseKey", "Value": "CamelCaseValue"},
                {"Key": "pascalCaseKey", "Value": "pascalCaseValue"},
            ],
        }

        OUTPUT = {
            "arn": "arn:aws:iam::123456789012:instance-profile/ansible-test-40050922/ansible-test-40050922",
            "create_date": "2020-12-30T00:00:00+00:00",
            "instance_profile_id": "AIPA12345EXAMPLE12345",
            "instance_profile_name": "ansible-test-40050922",
            "path": "/ansible-test-40050922/",
            "roles": [
                {
                    "arn": "arn:aws:iam::123456789012:role/ansible-test-40050922/ansible-test-40050922",
                    "assume_role_policy_document": {
                        "Statement": [
                            {
                                "Action": "sts:AssumeRole",
                                "Effect": "Deny",
                                "Principal": {"Service": "ec2.amazonaws.com"},
                            }
                        ],
                        "Version": "2012-10-17",
                    },
                    "create_date": "2021-04-26T01:23:58+00:00",
                    "path": "/ansible-test-40050922/",
                    "role_id": "AROA12345EXAMPLE12345",
                    "role_name": "ansible-test-40050922",
                    "tags": {"TagC": "ValueC"},
                }
            ],
            "tags": {
                "CamelCaseKey": "CamelCaseValue",
                "Key with Spaces": "Value with spaces",
                "pascalCaseKey": "pascalCaseValue",
                "snake_case_key": "snake_case_value",
            },
        }

        assert OUTPUT == normalize_iam_instance_profile(INPUT)
