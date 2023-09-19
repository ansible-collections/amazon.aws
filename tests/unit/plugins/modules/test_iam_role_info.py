#
# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest
from botocore.exceptions import BotoCoreError

from unittest.mock import MagicMock, call, patch
from ansible_collections.amazon.aws.plugins.modules import iam_role_info


mod_list_iam_roles = "ansible_collections.amazon.aws.plugins.modules.iam_role_info.list_iam_roles_with_backoff"
mod_list_iam_role_policies = (
    "ansible_collections.amazon.aws.plugins.modules.iam_role_info.list_iam_role_policies_with_backoff"
)
mod_list_iam_attached_policies = (
    "ansible_collections.amazon.aws.plugins.modules.iam_role_info.list_iam_attached_role_policies_with_backoff"
)
mod_list_iam_instance_profiles_for_role = (
    "ansible_collections.amazon.aws.plugins.modules.iam_role_info.list_iam_instance_profiles_for_role_with_backoff"
)
mod_boto3_tag_list_to_ansible_dict = (
    "ansible_collections.amazon.aws.plugins.modules.iam_role_info.boto3_tag_list_to_ansible_dict"
)
mod_normalize_role = "ansible_collections.amazon.aws.plugins.modules.iam_role_info.normalize_role"
mod_normalize_profile = "ansible_collections.amazon.aws.plugins.modules.iam_role_info.normalize_profile"
mod_camel_dict_to_snake_dict = "ansible_collections.amazon.aws.plugins.modules.iam_role_info.camel_dict_to_snake_dict"
mod_get_role = "ansible_collections.amazon.aws.plugins.modules.iam_role_info.get_role"
mod_describe_iam_role = "ansible_collections.amazon.aws.plugins.modules.iam_role_info.describe_iam_role"


def raise_botocore_exception():
    return BotoCoreError(error="failed", operation="Unexpected error while calling botocore api")


@pytest.mark.parametrize("list_iam_policies_status", [True, False])
@pytest.mark.parametrize("list_iam_attached_policies_status", [True, False])
@pytest.mark.parametrize("list_iam_instance_profiles_for_role_status", [True, False])
@patch(mod_list_iam_role_policies)
@patch(mod_list_iam_attached_policies)
@patch(mod_list_iam_instance_profiles_for_role)
@patch(mod_boto3_tag_list_to_ansible_dict)
def test_describe_iam_role_with_iam_policies_error(
    m_boto3_tag_list_to_ansible_dict,
    m_list_iam_instance_profiles_for_role,
    m_list_iam_attached_policies,
    m_list_iam_role_policies,
    list_iam_policies_status,
    list_iam_attached_policies_status,
    list_iam_instance_profiles_for_role_status,
):
    client = MagicMock()
    module = MagicMock()
    module.fail_json_aws.side_effect = SystemExit(1)

    iam_policies = {
        "PolicyNames": [
            "policy-1",
        ]
    }
    iam_attached_policies = {
        "AttachedPolicies": [
            {"PolicyName": "policy-1", "PolicyArn": "iam:policy:arn:xxx:xxx:xxx"},
        ]
    }
    iam_instance_profiles = {"InstanceProfiles": ["instance-profile-1"]}

    has_failure = False
    if list_iam_policies_status:
        m_list_iam_role_policies.return_value = iam_policies
    else:
        has_failure = True
        m_list_iam_role_policies.side_effect = raise_botocore_exception()

    if list_iam_attached_policies_status:
        m_list_iam_attached_policies.return_value = iam_attached_policies
    else:
        has_failure = True
        m_list_iam_attached_policies.side_effect = raise_botocore_exception()
    module.fail_json_aws.side_effect = SystemExit(1)

    if list_iam_instance_profiles_for_role_status:
        m_list_iam_instance_profiles_for_role.return_value = iam_instance_profiles
    else:
        has_failure = True
        m_list_iam_instance_profiles_for_role.side_effect = raise_botocore_exception()
    module.fail_json_aws.side_effect = SystemExit(1)

    m_boto3_tag_list_to_ansible_dict.side_effect = lambda x: x

    role_name = "ansible-test-role"
    role_tags = {
        "Environment": "Dev",
        "Phase": "Units",
    }
    test_role = {
        "RoleName": role_name,
        "Tags": role_tags,
    }

    if has_failure:
        with pytest.raises(SystemExit):
            iam_role_info.describe_iam_role(module, client, test_role)
        module.fail_json_aws.assert_called_once()
        # validate that each function has at most 1 call
        assert m_list_iam_role_policies.call_count <= 1
        assert m_list_iam_attached_policies.call_count <= 1
        assert m_list_iam_instance_profiles_for_role.call_count <= 1
        # validate function call with expected parameters
        if m_list_iam_role_policies.call_count == 1:
            m_list_iam_role_policies.assert_called_once_with(client, role_name)
        if m_list_iam_attached_policies.call_count == 1:
            m_list_iam_attached_policies.assert_called_once_with(client, role_name)
        if m_list_iam_instance_profiles_for_role.call_count == 1:
            m_list_iam_instance_profiles_for_role.assert_called_once_with(client, role_name)
    else:
        # Everything went well
        expected_role = {
            "RoleName": role_name,
            "InlinePolicies": iam_policies,
            "ManagedPolicies": iam_attached_policies,
            "InstanceProfiles": iam_instance_profiles,
            "tags": role_tags,
        }
        assert expected_role == iam_role_info.describe_iam_role(module, client, test_role)
        m_list_iam_role_policies.assert_called_once_with(client, role_name)
        m_list_iam_attached_policies.assert_called_once_with(client, role_name)
        m_list_iam_instance_profiles_for_role.assert_called_once_with(client, role_name)
        m_boto3_tag_list_to_ansible_dict.assert_called_once_with(role_tags)


@patch(mod_normalize_role)
@patch(mod_camel_dict_to_snake_dict)
def test_normalize_profile(m_camel_dict_to_snake_dict, m_normalize_role):
    m_camel_dict_to_snake_dict.side_effect = lambda x: {k.lower(): d for k,d in x.items()}
    m_normalize_role.side_effect = lambda x: {"RoleName": x}

    profile = {"Roles": ["role-1", "role-2"]}
    expected = {"roles": [{"RoleName": "role-1"}, {"RoleName": "role-2"}]}
    assert expected == iam_role_info.normalize_profile(profile)
    m_camel_dict_to_snake_dict.assert_called_once_with(profile)
    m_normalize_role.assert_has_calls([call("role-1"), call("role-2")])


@patch(mod_normalize_profile)
@patch(mod_camel_dict_to_snake_dict)
def test_normalize_role(m_camel_dict_to_snake_dict, m_normalize_profile):
    m_camel_dict_to_snake_dict.side_effect = lambda x, **kwargs: {k.lower() if k not in kwargs.get("ignore_list") else k: d for k,d in x.items()}
    m_normalize_profile.side_effect = lambda x: x

    role_policy_document = {
        "Statement": [{"Action": "sts:AssumeRole", "Effect": "Deny", "Principal": {"Service": "ec2.amazonaws.com"}}],
        "Version": "2012-10-17",
    }
    role_tags = {
        "Environment": "Dev",
        "Phase": "Units",
    }
    role = {
        "AssumeRolePolicyDocument": role_policy_document,
        "tags": role_tags,
        "InstanceProfiles": [
            "profile-1",
            "profile-2",
        ],
    }
    expected = {
        "AssumeRolePolicyDocument": role_policy_document,
        "assume_role_policy_document": role_policy_document,
        "assume_role_policy_document_raw": role_policy_document,
        "tags": role_tags,
        "instanceprofiles": [
            "profile-1",
            "profile-2",
        ],
        "instance_profiles": [
            "profile-1",
            "profile-2",
        ],
    }

    assert expected == iam_role_info.normalize_role(role)
    m_camel_dict_to_snake_dict.assert_called_once_with(role, ignore_list=["tags", "AssumeRolePolicyDocument"])
    m_normalize_profile.assert_has_calls([call("profile-1"), call("profile-2")])


@patch(mod_get_role)
@patch(mod_list_iam_roles)
@patch(mod_normalize_role)
@patch(mod_describe_iam_role)
def test_describe_iam_roles_with_name(m_describe_iam_role, m_normalize_role, m_list_iam_roles, m_get_role):
    role_name = "ansible-test-role"

    client = MagicMock()
    module = MagicMock()
    module.params = {
        "name": role_name,
        "path_prefix": "path prefix",
    }

    m_get_role.return_value = [{"RoleName": role_name}]
    expected = {"role_name": role_name, "instance_profiles": ["profile-1", "profile-2"]}
    m_describe_iam_role.return_value = expected
    m_normalize_role.return_value = expected

    assert [expected] == iam_role_info.describe_iam_roles(module, client)
    m_get_role.assert_called_once_with(module, client, role_name)
    m_list_iam_roles.assert_not_called()

    m_describe_iam_role.assert_called_once_with(module, client, {"RoleName": role_name})
    m_normalize_role.assert_called_once_with(expected)


@pytest.mark.parametrize(
    "path_prefix",
    [
        "ansible-prefix",
        "ansible-prefix/",
        "/ansible-prefix",
        "/ansible-prefix/",
    ],
)
@patch(mod_get_role)
@patch(mod_list_iam_roles)
@patch(mod_normalize_role)
@patch(mod_describe_iam_role)
def test_describe_iam_roles_with_path_prefix(
    m_describe_iam_role, m_normalize_role, m_list_iam_roles, m_get_role, path_prefix
):
    client = MagicMock()
    role = MagicMock()
    module = MagicMock()
    module.params = {
        "name": None,
        "path_prefix": path_prefix,
    }

    m_list_iam_roles.return_value = {"Roles": [role]}

    m_describe_iam_role.side_effect = lambda m, c, r: r
    m_normalize_role.side_effect = lambda x: x

    assert [role] == iam_role_info.describe_iam_roles(module, client)
    m_get_role.assert_not_called()
    m_list_iam_roles.assert_called_once_with(client, PathPrefix="/ansible-prefix/")

    m_describe_iam_role.assert_called_once_with(module, client, role)
    m_normalize_role.assert_called_once_with(role)
