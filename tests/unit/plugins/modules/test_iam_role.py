#
# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest
from botocore.exceptions import BotoCoreError, WaiterError, ClientError

from unittest.mock import MagicMock, call, patch, ANY
from ansible_collections.amazon.aws.plugins.modules import iam_role


mod__list_policies = "ansible_collections.amazon.aws.plugins.modules.iam_role._list_policies"
mod__wait_iam_role = "ansible_collections.amazon.aws.plugins.modules.iam_role._wait_iam_role"
mod_validate_aws_arn = "ansible_collections.amazon.aws.plugins.modules.iam_role.validate_aws_arn"
mod_get_inline_policy_list = "ansible_collections.amazon.aws.plugins.modules.iam_role.get_inline_policy_list"
mod_ansible_dict_to_boto3_tag_list = (
    "ansible_collections.amazon.aws.plugins.modules.iam_role.ansible_dict_to_boto3_tag_list"
)
mod_generate_create_params = "ansible_collections.amazon.aws.plugins.modules.iam_role.generate_create_params"
mod_get_role_with_backoff = "ansible_collections.amazon.aws.plugins.modules.iam_role.get_role_with_backoff"
mod_remove_instance_profiles = "ansible_collections.amazon.aws.plugins.modules.iam_role.remove_instance_profiles"
mod_update_managed_policies = "ansible_collections.amazon.aws.plugins.modules.iam_role.update_managed_policies"
mod_remove_inline_policies = "ansible_collections.amazon.aws.plugins.modules.iam_role.remove_inline_policies"
mod_get_role = "ansible_collections.amazon.aws.plugins.modules.iam_role.get_role"
mod_list_instance_profiles_for_role = (
    "ansible_collections.amazon.aws.plugins.modules.iam_role.list_instance_profiles_for_role"
)
mod_remove_role_from_instance_profile = (
    "ansible_collections.amazon.aws.plugins.modules.iam_role.remove_role_from_instance_profile"
)
mod_delete_instance_profile = "ansible_collections.amazon.aws.plugins.modules.iam_role.delete_instance_profile"
mod_create_instance_profile = "ansible_collections.amazon.aws.plugins.modules.iam_role.create_instance_profile"
mod_add_role_to_instance_profile = (
    "ansible_collections.amazon.aws.plugins.modules.iam_role.add_role_to_instance_profile"
)
mod_convert_friendly_names_to_arns = (
    "ansible_collections.amazon.aws.plugins.modules.iam_role.convert_friendly_names_to_arns"
)


@patch(mod__wait_iam_role)
def test_wait_iam_exists_check_mode_or_parameter_not_set(m__wait_iam_role):
    module = MagicMock()
    client = MagicMock()

    module.check_mode = False
    module.params = {"wait_timeout": 10}

    m__wait_iam_role.side_effect = SystemExit(1)

    # Test with module parameter not set
    iam_role.wait_iam_exists(module, client)
    m__wait_iam_role.assert_not_called()

    # Test with check_mode=true
    module.check_mode = True
    iam_role.wait_iam_exists(module, client)
    m__wait_iam_role.assert_not_called()


@patch(mod__wait_iam_role)
def test_wait_iam_exists_waiter_error(m__wait_iam_role):
    module = MagicMock()
    client = MagicMock()

    role_name = "ansible-test-role"
    module.fail_json_aws.side_effect = SystemExit(1)
    module.check_mode = False
    wait_timeout = 10
    module.params = {"name": role_name, "wait": True, "wait_timeout": wait_timeout}
    waiter_err = WaiterError(
        name="IAMCreationError",
        reason="Waiter encountered an unexpected error",
        last_response=None,
    )
    m__wait_iam_role.side_effect = waiter_err

    with pytest.raises(SystemExit):
        iam_role.wait_iam_exists(module, client)
    m__wait_iam_role.assert_called_once_with(client, role_name, wait_timeout)
    module.fail_json_aws.assert_called_once_with(waiter_err, msg="Timeout while waiting on IAM role creation")


@patch(mod__list_policies)
@patch(mod_validate_aws_arn)
def test_convert_friendly_names_to_arns_with_valid_iam_arn(m_validate_aws_arn, m__list_policies):
    m_validate_aws_arn.side_effect = lambda *ag, **kw: True
    m__list_policies.side_effect = SystemExit(1)

    module = MagicMock()
    client = MagicMock()
    policy_names = [None, "policy-1"]

    assert iam_role.convert_friendly_names_to_arns(module, client, policy_names) == policy_names
    m_validate_aws_arn.assert_called_once_with("policy-1", service="iam")
    m__list_policies.assert_not_called()


@pytest.mark.parametrize(
    "policy_names",
    [
        ["AWSEC2SpotServiceRolePolicy", "AllowXRayPutTraceSegments"],
        ["AWSEC2SpotServiceRolePolicy", "AllowXRayPutTraceSegments", "ThisPolicyDoesNotExists"],
    ],
)
@patch(mod__list_policies)
@patch(mod_validate_aws_arn)
def test_convert_friendly_names_to_arns(m_validate_aws_arn, m__list_policies, policy_names):
    m_validate_aws_arn.side_effect = lambda *ag, **kw: False
    module = MagicMock()
    module.fail_json_aws.side_effect = SystemExit(1)
    client = MagicMock()

    test_policies = [
        {
            "Arn": "arn:aws:iam::aws:policy/aws-service-role/AWSEC2SpotServiceRolePolicy",
            "PolicyName": "AWSEC2SpotServiceRolePolicy",
        },
        {
            "Arn": "arn:aws:iam::aws:policy/aws-service-role/AWSServiceRoleForAmazonEKSNodegroup",
            "PolicyName": "AWSServiceRoleForAmazonEKSNodegroup",
        },
        {
            "Arn": "arn:aws:iam::966509639900:policy/AllowXRayPutTraceSegments",
            "PolicyName": "AllowXRayPutTraceSegments",
        },
    ]
    test_policies_names = [policy["PolicyName"] for policy in test_policies]
    m__list_policies.return_value = test_policies
    if any(policy not in test_policies_names for policy in policy_names if policy is not None):
        with pytest.raises(SystemExit):
            iam_role.convert_friendly_names_to_arns(module, client, policy_names)
        module.fail_json_aws.assert_called_once_with(ANY, msg="Couldn't find policy")
    else:

        def _get_policy_arn(policy):
            for item in test_policies:
                if item.get("PolicyName") == policy:
                    return item.get("Arn")

        expected = [_get_policy_arn(policy) for policy in policy_names if policy is not None]
        assert iam_role.convert_friendly_names_to_arns(module, client, policy_names) == expected
    m__list_policies.assert_called_once_with(client)


def test_attach_policies():
    module = MagicMock()
    client = MagicMock()

    module.fail_json_aws.side_effect = SystemExit(1)
    role_name = "ansible-test-role"

    # Test: check_mode=true and policies_to_attach = []
    module.check_mode = True
    assert not iam_role.attach_policies(module, client, [], role_name)
    client.attach_role_policy.assert_not_called()

    # Test: check_mode=true and policies_to_attach != []
    module.check_mode = True
    assert iam_role.attach_policies(module, client, ["policy-1", "policy-2", "policy-3"], role_name)
    client.attach_role_policy.assert_not_called()

    # Test: check_mode=false and policies_to_attach != []
    module.check_mode = False
    assert iam_role.attach_policies(module, client, ["policy-1", "policy-2", "policy-3"], role_name)
    client.attach_role_policy.assert_has_calls(
        [
            call(RoleName=role_name, PolicyArn="policy-1", aws_retry=True),
            call(RoleName=role_name, PolicyArn="policy-2", aws_retry=True),
            call(RoleName=role_name, PolicyArn="policy-3", aws_retry=True),
        ]
    )

    # Test: client.attach_role_policy raised botocore exception
    error = BotoCoreError(error="AttachRolePolicy", operation="Failed to attach policy to IAM role")
    client.attach_role_policy.side_effect = error
    with pytest.raises(SystemExit):
        iam_role.attach_policies(module, client, ["policy-1", "policy-2", "policy-3"], role_name)
    module.fail_json_aws.assert_called_once_with(error, msg=f"Unable to attach policy policy-1 to role {role_name}")


def test_remove_policies():
    module = MagicMock()
    client = MagicMock()

    module.fail_json_aws.side_effect = SystemExit(1)
    role_name = "ansible-test-role"

    # Test: check_mode=true and policies_to_remove = []
    module.check_mode = True
    assert not iam_role.remove_policies(module, client, [], role_name)
    client.detach_role_policy.assert_not_called()

    # Test: check_mode=true and policies_to_remove != []
    module.check_mode = True
    assert iam_role.remove_policies(module, client, ["policy-1", "policy-2", "policy-3"], role_name)
    client.detach_role_policy.assert_not_called()

    # Test: check_mode=false and policies_to_attach != []
    module.check_mode = False
    assert iam_role.remove_policies(module, client, ["policy-1", "policy-2", "policy-3"], role_name)
    client.detach_role_policy.assert_has_calls(
        [
            call(RoleName=role_name, PolicyArn="policy-1", aws_retry=True),
            call(RoleName=role_name, PolicyArn="policy-2", aws_retry=True),
            call(RoleName=role_name, PolicyArn="policy-3", aws_retry=True),
        ]
    )

    # Test: client.attach_role_policy raised botocore exception
    error = BotoCoreError(error="DetachRolePolicy", operation="Failed to detach policy to IAM role")
    client.detach_role_policy.side_effect = error
    with pytest.raises(SystemExit):
        iam_role.remove_policies(module, client, ["policy-1", "policy-2", "policy-3"], role_name)
    module.fail_json_aws.assert_called_once_with(error, msg=f"Unable to detach policy policy-1 from {role_name}")

    # Test: client.attach_role_policy raised botocore error 'NoSuchEntityException'
    nosuch_entity_err = ClientError(
        {"Error": {"Code": "NoSuchEntityException"}},
        "DetachRolePolicy",
    )
    client.detach_role_policy.side_effect = (
        lambda *args, **kw: nosuch_entity_err if kw.get("PolicyArn") == "policy-2" else True
    )
    assert iam_role.remove_policies(module, client, ["policy-1", "policy-2", "policy-3"], role_name)
    client.detach_role_policy.assert_has_calls(
        [
            call(RoleName=role_name, PolicyArn="policy-1", aws_retry=True),
            call(RoleName=role_name, PolicyArn="policy-2", aws_retry=True),
            call(RoleName=role_name, PolicyArn="policy-3", aws_retry=True),
        ]
    )


@patch(mod_get_inline_policy_list)
def test_remove_inline_policies(m_get_inline_policy_list):
    role_name = "ansible-test-role"
    module = MagicMock()
    client = MagicMock()

    m_get_inline_policy_list.return_value = ["policy-1", "policy-2", "policy-3"]
    nosuch_entity_err = ClientError(
        {"Error": {"Code": "NoSuchEntityException"}},
        "DetachRolePolicy",
    )
    client.detach_role_policy.side_effect = (
        lambda *args, **kw: nosuch_entity_err if kw.get("PolicyArn") == "policy-2" else True
    )
    iam_role.remove_inline_policies(module, client, role_name)
    client.delete_role_policy.assert_has_calls(
        [
            call(RoleName=role_name, PolicyName="policy-1", aws_retry=True),
            call(RoleName=role_name, PolicyName="policy-2", aws_retry=True),
            call(RoleName=role_name, PolicyName="policy-3", aws_retry=True),
        ]
    )


@patch(mod_ansible_dict_to_boto3_tag_list)
def test_generate_create_params(m_ansible_dict_to_boto3_tag_list):
    module = MagicMock()
    path = MagicMock()
    name = MagicMock()
    policy_document = MagicMock()
    description = MagicMock()
    max_session_duration = MagicMock()
    boundary = MagicMock()
    tags = MagicMock()
    module.params = {
        "path": path,
        "name": name,
        "assume_role_policy_document": policy_document,
        "description": description,
        "max_session_duration": max_session_duration,
        "boundary": boundary,
        "tags": tags,
    }
    expected = {
        "Path": path,
        "RoleName": name,
        "AssumeRolePolicyDocument": policy_document,
        "Description": description,
        "MaxSessionDuration": max_session_duration,
        "PermissionsBoundary": boundary,
        "Tags": tags,
    }

    m_ansible_dict_to_boto3_tag_list.return_value = tags
    assert iam_role.generate_create_params(module) == expected
    m_ansible_dict_to_boto3_tag_list.assert_called_once_with(tags)


@patch(mod_get_role_with_backoff)
@patch(mod_generate_create_params)
def test_create_basic_role_check_mode(m_generate_create_params, m_get_role_with_backoff):
    module = MagicMock()
    module.exit_json.side_effect = SystemExit(1)
    module.fail_json_aws.side_effect = SystemExit(1)
    client = MagicMock()

    module.check_mode = True
    with pytest.raises(SystemExit):
        iam_role.create_basic_role(module, client)
    m_generate_create_params.assert_not_called()
    m_get_role_with_backoff.assert_not_called()


@patch(mod_get_role_with_backoff)
@patch(mod_generate_create_params)
def test_create_basic_role_with_create_role_error(m_generate_create_params, m_get_role_with_backoff):
    role_name = "ansible-test-role"
    params = {
        "RoleName": role_name,
        "Tags": {
            "Phase": "dev",
            "ansible-test": "units",
        },
    }
    m_generate_create_params.return_value = params

    module = MagicMock()
    module.fail_json_aws.side_effect = SystemExit(1)
    client = MagicMock()

    module.check_mode = False
    create_role_error = BotoCoreError(error="failed", operation="Not enough permission to create role")
    client.create_role.side_effect = create_role_error
    with pytest.raises(SystemExit):
        iam_role.create_basic_role(module, client)
    module.fail_json_aws.assert_called_once_with(create_role_error, msg="Unable to create role")
    m_get_role_with_backoff.assert_not_called()


@patch(mod_get_role_with_backoff)
@patch(mod_generate_create_params)
def test_create_basic_role_with_get_role_error(m_generate_create_params, m_get_role_with_backoff):
    role_name = "ansible-test-role"
    params = {
        "RoleName": role_name,
        "Tags": {
            "Phase": "dev",
            "ansible-test": "units",
        },
    }
    m_generate_create_params.return_value = params
    module = MagicMock()
    module.fail_json_aws.side_effect = SystemExit(1)
    client = MagicMock()

    module.check_mode = False
    client.create_role.return_value = {
        "RoleName": role_name,
    }
    error = BotoCoreError(error="failed", operation="Unable to get role")
    m_get_role_with_backoff.side_effect = error
    with pytest.raises(SystemExit):
        iam_role.create_basic_role(module, client)
    module.fail_json_aws.assert_called_once_with(error, msg="Unable to create role")
    client.create_role.assert_called_once_with(aws_retry=True, **params)


@patch(mod_get_role_with_backoff)
@patch(mod_generate_create_params)
def test_create_basic_role(m_generate_create_params, m_get_role_with_backoff):
    role_name = "ansible-test-role"
    params = {
        "RoleName": role_name,
        "Tags": {
            "Phase": "dev",
            "ansible-test": "units",
        },
    }
    m_generate_create_params.return_value = params
    module = MagicMock()
    module.fail_json_aws.side_effect = SystemExit(1)
    client = MagicMock()

    module.check_mode = False
    client.create_role.return_value = {
        "RoleName": role_name,
    }
    role = {
        "RoleName": role_name,
        "Description": "Role created for ansible unit testing",
        "Tags": {
            "Phase": "dev",
            "ansible-test": "units",
        },
    }
    m_get_role_with_backoff.return_value = role
    assert iam_role.create_basic_role(module, client) == role
    client.create_role.assert_called_once_with(aws_retry=True, **params)
    m_get_role_with_backoff.assert_called_once_with(module, client, role_name)


@patch(mod_update_managed_policies)
@patch(mod_remove_inline_policies)
@patch(mod_remove_instance_profiles)
@patch(mod_get_role)
def test_destroy_role_unexisting_role(
    m_get_role, m_remove_instance_profiles, m_remove_inline_policies, m_update_managed_policies
):
    module = MagicMock()
    client = MagicMock()

    role_name = "ansible-test-role"
    module.params = {"name": role_name}
    module.check_mode = False
    module.exit_json.side_effect = SystemExit(1)
    m_get_role.return_value = None

    with pytest.raises(SystemExit):
        iam_role.destroy_role(module, client)
    m_get_role.assert_called_once_with(module, client, role_name)
    module.exit_json.assert_called_once_with(changed=False)
    m_remove_instance_profiles.assert_not_called()
    m_remove_inline_policies.assert_not_called()
    m_update_managed_policies.assert_not_called()


@patch(mod_update_managed_policies)
@patch(mod_remove_inline_policies)
@patch(mod_remove_instance_profiles)
@patch(mod_get_role)
def test_destroy_role_check_mode(
    m_get_role, m_remove_instance_profiles, m_remove_inline_policies, m_update_managed_policies
):
    module = MagicMock()
    client = MagicMock()

    role_name = "ansible-test-role"
    module.params = {"name": role_name}
    module.check_mode = True
    module.exit_json.side_effect = SystemExit(1)
    m_get_role.return_value = MagicMock()

    with pytest.raises(SystemExit):
        iam_role.destroy_role(module, client)
    m_get_role.assert_called_once_with(module, client, role_name)
    module.exit_json.assert_called_once_with(changed=True)
    m_remove_instance_profiles.assert_not_called()
    m_remove_inline_policies.assert_not_called()
    m_update_managed_policies.assert_not_called()


@patch(mod_update_managed_policies)
@patch(mod_remove_inline_policies)
@patch(mod_remove_instance_profiles)
@patch(mod_get_role)
def test_destroy_role(m_get_role, m_remove_instance_profiles, m_remove_inline_policies, m_update_managed_policies):
    module = MagicMock()
    client = MagicMock()

    role_name = "ansible-test-role"
    module.params = {"name": role_name}
    module.check_mode = False
    module.exit_json.side_effect = SystemExit(1)
    m_get_role.return_value = MagicMock()

    with pytest.raises(SystemExit):
        iam_role.destroy_role(module, client)
    m_get_role.assert_called_once_with(module, client, role_name)
    module.exit_json.assert_called_once_with(changed=True)
    m_remove_instance_profiles.assert_called_once_with(module, client, role_name)
    m_remove_inline_policies.assert_called_once_with(module, client, role_name)
    m_update_managed_policies.assert_called_once_with(module, client, role_name, [], True)


@patch(mod_update_managed_policies)
@patch(mod_remove_inline_policies)
@patch(mod_remove_instance_profiles)
@patch(mod_get_role)
def test_destroy_role_with_deletion_error(
    m_get_role, m_remove_instance_profiles, m_remove_inline_policies, m_update_managed_policies
):
    module = MagicMock()
    client = MagicMock()

    role_name = "ansible-test-role"
    module.params = {"name": role_name}
    module.check_mode = False
    module.exit_json.side_effect = SystemExit(1)
    module.fail_json_aws.side_effect = SystemExit(1)
    m_get_role.return_value = MagicMock()

    error = BotoCoreError(error="failed", operation="Unable to get role")
    client.delete_role.side_effect = error

    with pytest.raises(SystemExit):
        iam_role.destroy_role(module, client)
    m_get_role.assert_called_once_with(module, client, role_name)
    module.exit_json.assert_not_called()
    module.fail_json_aws.assert_called_once_with(error, msg="Unable to delete role")
    m_remove_instance_profiles.assert_called_once_with(module, client, role_name)
    m_remove_inline_policies.assert_called_once_with(module, client, role_name)
    m_update_managed_policies.assert_called_once_with(module, client, role_name, [], True)


@patch(mod_list_instance_profiles_for_role)
@patch(mod_remove_role_from_instance_profile)
@patch(mod_delete_instance_profile)
def test_remove_instance_profiles_check_mode(
    m_delete_instance_profile, m_remove_role_from_instance_profile, m_list_instance_profiles_for_role
):
    module = MagicMock()
    client = MagicMock()

    role_name = "ansible-test-role"
    module.check_mode = True
    iam_role.remove_instance_profiles(module, client, role_name)
    for m_func in (m_delete_instance_profile, m_remove_role_from_instance_profile, m_list_instance_profiles_for_role):
        m_func.assert_not_called()


@pytest.mark.parametrize("delete_profiles", [True, False])
@patch(mod_list_instance_profiles_for_role)
@patch(mod_remove_role_from_instance_profile)
@patch(mod_delete_instance_profile)
def test_remove_instance_profiles_with_delete_profile(
    m_delete_instance_profile, m_remove_role_from_instance_profile, m_list_instance_profiles_for_role, delete_profiles
):
    module = MagicMock()
    client = MagicMock()

    module.params = {"delete_instance_profile": delete_profiles}
    module.check_mode = False
    role_name = "ansible-test-role"
    instance_profiles = [
        {"InstanceProfileName": "instance_profile_1"},
        {"InstanceProfileName": "instance_profile_2"},
        {"InstanceProfileName": role_name},
    ]
    m_list_instance_profiles_for_role.return_value = instance_profiles
    iam_role.remove_instance_profiles(module, client, role_name)
    m_list_instance_profiles_for_role.assert_called_once_with(module, client, role_name)
    m_remove_role_from_instance_profile.assert_has_calls(
        [call(module, client, role_name, profile["InstanceProfileName"]) for profile in instance_profiles],
        any_order=True,
    )
    if delete_profiles:
        m_delete_instance_profile.assert_called_once_with(module, client, role_name)
    else:
        m_delete_instance_profile.assert_not_called()


@patch(mod_list_instance_profiles_for_role)
@patch(mod_create_instance_profile)
@patch(mod_add_role_to_instance_profile)
def test_create_instance_profiles_with_existing_profile(
    m_add_role_to_instance_profile, m_create_instance_profile, m_list_instance_profiles_for_role
):
    module = MagicMock()
    client = MagicMock()
    path = MagicMock()

    role_name = "ansible-test-role"
    m_list_instance_profiles_for_role.return_value = [{"InstanceProfileName": role_name}]
    assert not iam_role.create_instance_profiles(module, client, role_name, path)
    m_add_role_to_instance_profile.assert_not_called()
    m_create_instance_profile.assert_not_called()


@patch(mod_list_instance_profiles_for_role)
@patch(mod_create_instance_profile)
@patch(mod_add_role_to_instance_profile)
def test_create_instance_profiles_check_mode(
    m_add_role_to_instance_profile, m_create_instance_profile, m_list_instance_profiles_for_role
):
    module = MagicMock()
    client = MagicMock()
    path = MagicMock()

    module.check_mode = True
    role_name = "ansible-test-role"
    m_list_instance_profiles_for_role.return_value = [{"InstanceProfileName": "instance-profile-1"}]
    assert iam_role.create_instance_profiles(module, client, role_name, path)
    m_add_role_to_instance_profile.assert_not_called()
    m_create_instance_profile.assert_not_called()


@patch(mod_list_instance_profiles_for_role)
@patch(mod_create_instance_profile)
@patch(mod_add_role_to_instance_profile)
def test_create_instance_profiles(
    m_add_role_to_instance_profile, m_create_instance_profile, m_list_instance_profiles_for_role
):
    module = MagicMock()
    client = MagicMock()
    path = MagicMock()

    module.check_mode = False
    role_name = "ansible-test-role"
    m_list_instance_profiles_for_role.return_value = [{"InstanceProfileName": "instance-profile-1"}]
    assert iam_role.create_instance_profiles(module, client, role_name, path)
    m_add_role_to_instance_profile.assert_called_once_with(module, client, role_name)
    m_create_instance_profile.assert_called_once_with(module, client, role_name, path)
