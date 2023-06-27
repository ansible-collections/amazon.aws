# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from copy import deepcopy

try:
    import botocore
except ImportError:
    pass  # Modules are responsible for handling this.

from ansible.module_utils._text import to_native
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from .arn import parse_aws_arn
from .botocore import is_boto3_error_code
from .exceptions import AnsibleAWSError
from .retries import AWSRetry
from .tagging import ansible_dict_to_boto3_tag_list
from .tagging import boto3_tag_list_to_ansible_dict


class AnsibleIAMError(AnsibleAWSError):
    pass


@AWSRetry.jittered_backoff()
def _tag_iam_instance_profile(client, **kwargs):
    client.tag_instance_profile(**kwargs)


@AWSRetry.jittered_backoff()
def _untag_iam_instance_profile(client, **kwargs):
    client.untag_instance_profile(**kwargs)


@AWSRetry.jittered_backoff()
def _get_iam_instance_profiles(client, **kwargs):
    return client.get_instance_profile(**kwargs)["InstanceProfile"]


@AWSRetry.jittered_backoff()
def _list_iam_instance_profiles(client, **kwargs):
    paginator = client.get_paginator("list_instance_profiles")
    return paginator.paginate(**kwargs).build_full_result()["InstanceProfiles"]


@AWSRetry.jittered_backoff()
def _list_iam_instance_profiles_for_role(client, **kwargs):
    paginator = client.get_paginator("list_instance_profiles_for_role")
    return paginator.paginate(**kwargs).build_full_result()["InstanceProfiles"]


@AWSRetry.jittered_backoff()
def _create_instance_profile(client, **kwargs):
    return client.create_instance_profile(**kwargs)


@AWSRetry.jittered_backoff()
def _delete_instance_profile(client, **kwargs):
    client.delete_instance_profile(**kwargs)


@AWSRetry.jittered_backoff()
def _add_role_to_instance_profile(client, **kwargs):
    client.add_role_to_instance_profile(**kwargs)


@AWSRetry.jittered_backoff()
def _remove_role_from_instance_profile(client, **kwargs):
    client.remove_role_from_instance_profile(**kwargs)


def get_aws_account_id(module):
    """Given an AnsibleAWSModule instance, get the active AWS account ID"""

    return get_aws_account_info(module)[0]


def get_aws_account_info(module):
    """Given an AnsibleAWSModule instance, return the account information
    (account id and partition) we are currently working on

    get_account_info tries too find out the account that we are working
    on.  It's not guaranteed that this will be easy so we try in
    several different ways.  Giving either IAM or STS privileges to
    the account should be enough to permit this.

    Tries:
    - sts:GetCallerIdentity
    - iam:GetUser
    - sts:DecodeAuthorizationMessage
    """
    account_id = None
    partition = None
    try:
        sts_client = module.client("sts", retry_decorator=AWSRetry.jittered_backoff())
        caller_id = sts_client.get_caller_identity(aws_retry=True)
        account_id = caller_id.get("Account")
        partition = caller_id.get("Arn").split(":")[1]
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError):
        try:
            iam_client = module.client("iam", retry_decorator=AWSRetry.jittered_backoff())
            _arn, partition, _service, _reg, account_id, _resource = iam_client.get_user(aws_retry=True)["User"][
                "Arn"
            ].split(":")
        except is_boto3_error_code("AccessDenied") as e:
            try:
                except_msg = to_native(e.message)
            except AttributeError:
                except_msg = to_native(e)
            result = parse_aws_arn(except_msg)
            if result is None or result["service"] != "iam":
                module.fail_json_aws(
                    e,
                    msg="Failed to get AWS account information, Try allowing sts:GetCallerIdentity or iam:GetUser permissions.",
                )
            account_id = result.get("account_id")
            partition = result.get("partition")
        except (
            botocore.exceptions.BotoCoreError,
            botocore.exceptions.ClientError,
        ) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(
                e,
                msg="Failed to get AWS account information, Try allowing sts:GetCallerIdentity or iam:GetUser permissions.",
            )

    if account_id is None or partition is None:
        module.fail_json(
            msg="Failed to get AWS account information, Try allowing sts:GetCallerIdentity or iam:GetUser permissions.",
        )

    return (to_native(account_id), to_native(partition))


def create_iam_instance_profile(client, name, path, tags):
    boto3_tags = ansible_dict_to_boto3_tag_list(tags or {})
    try:
        result = _create_instance_profile(client, InstanceProfileName=name, Path=path, Tags=boto3_tags)
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        raise AnsibleIAMError(message="Unable to create instance profile", exception=e)
    return result["InstanceProfile"]


def delete_iam_instance_profile(client, name):
    try:
        _delete_instance_profile(client, InstanceProfileName=name)
    except is_boto3_error_code("NoSuchEntity"):
        # Deletion already happened.
        return False
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        raise AnsibleIAMError(message="Unable to delete instance profile", exception=e)
    return True


def add_role_to_iam_instance_profile(client, profile_name, role_name):
    try:
        _add_role_to_instance_profile(client, InstanceProfileName=profile_name, RoleName=role_name)
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        raise AnsibleIAMError(
            message="Unable to add role to instance profile",
            exception=e,
            profile_name=profile_name,
            role_name=role_name,
        )
    return True


def remove_role_from_iam_instance_profile(client, profile_name, role_name):
    try:
        _remove_role_from_instance_profile(client, InstanceProfileName=profile_name, RoleName=role_name)
    except is_boto3_error_code("NoSuchEntity"):
        # Deletion already happened.
        return False
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        raise AnsibleIAMError(
            message="Unable to remove role from instance profile",
            exception=e,
            profile_name=profile_name,
            role_name=role_name,
        )
    return True


def list_iam_instance_profiles(client, name=None, prefix=None, role=None):
    """
    Returns a list of IAM instance profiles in boto3 format.
    Profiles need to be converted to Ansible format using normalize_iam_instance_profile before being displayed.

    See also: normalize_iam_instance_profile
    """
    try:
        if role:
            return _list_iam_instance_profiles_for_role(client, RoleName=role)
        if name:
            # Unlike the others this returns a single result, make this a list with 1 element.
            return [_get_iam_instance_profiles(client, InstanceProfileName=name)]
        if prefix:
            return _list_iam_instance_profiles(client, PathPrefix=prefix)
        return _list_iam_instance_profiles(client)
    except is_boto3_error_code("NoSuchEntity"):
        return []
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        raise AnsibleIAMError(message="Unable to list instance profiles", exception=e)


def normalize_iam_instance_profile(profile):
    """
    Converts a boto3 format IAM instance profile into "Ansible" format
    """

    new_profile = camel_dict_to_snake_dict(deepcopy(profile))
    if profile.get("Roles"):
        new_profile["roles"] = [normalize_iam_role(role) for role in profile.get("Roles")]
    if profile.get("Tags"):
        new_profile["tags"] = boto3_tag_list_to_ansible_dict(profile.get("Tags"))
    else:
        new_profile["tags"] = {}
    new_profile["original"] = profile
    return new_profile


def normalize_iam_role(role):
    """
    Converts a boto3 format IAM instance role into "Ansible" format
    """

    new_role = camel_dict_to_snake_dict(deepcopy(role))
    if role.get("InstanceProfiles"):
        new_role["instance_profiles"] = [
            normalize_iam_instance_profile(profile) for profile in role.get("InstanceProfiles")
        ]
    if role.get("AssumeRolePolicyDocument"):
        new_role["assume_role_policy_document"] = role.get("AssumeRolePolicyDocument")
    if role.get("Tags"):
        new_role["tags"] = boto3_tag_list_to_ansible_dict(role.get("Tags"))
    else:
        new_role["tags"] = {}
    new_role["original"] = role
    return new_role


def tag_iam_instance_profile(client, name, tags):
    if not tags:
        return
    boto3_tags = ansible_dict_to_boto3_tag_list(tags or {})
    try:
        result = _tag_iam_instance_profile(client, InstanceProfileName=name, Tags=boto3_tags)
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        raise AnsibleIAMError(message="Unable to tag instance profile", exception=e)


def untag_iam_instance_profile(client, name, tags):
    if not tags:
        return
    try:
        result = _untag_iam_instance_profile(client, InstanceProfileName=name, TagKeys=tags)
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        raise AnsibleIAMError(message="Unable to untag instance profile", exception=e)
