# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import re

try:
    import botocore
except ImportError:
    pass  # Modules are responsible for handling this.

from ansible.module_utils._text import to_native

from .arn import parse_aws_arn
from .arn import validate_aws_arn
from .botocore import is_boto3_error_code
from .errors import AWSErrorHandler
from .exceptions import AnsibleAWSError
from .retries import AWSRetry
from .tagging import ansible_dict_to_boto3_tag_list
from .transformation import AnsibleAWSResource
from .transformation import AnsibleAWSResourceList
from .transformation import BotoResource
from .transformation import BotoResourceList
from .transformation import boto3_resource_list_to_ansible_dict
from .transformation import boto3_resource_to_ansible_dict


class AnsibleIAMError(AnsibleAWSError):
    pass


class IAMErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleIAMError

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("NoSuchEntity")


@IAMErrorHandler.deletion_error_handler("detach group policy")
@AWSRetry.jittered_backoff()
def detach_iam_group_policy(client, arn, group):
    client.detach_group_policy(PolicyArn=arn, GroupName=group)
    return True


@IAMErrorHandler.deletion_error_handler("detach role policy")
@AWSRetry.jittered_backoff()
def detach_iam_role_policy(client, arn, role):
    client.detach_role_policy(PolicyArn=arn, RoleName=role)
    return True


@IAMErrorHandler.deletion_error_handler("detach user policy")
@AWSRetry.jittered_backoff()
def detach_iam_user_policy(client, arn, user):
    client.detach_user_policy(PolicyArn=arn, UserName=user)
    return True


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


@IAMErrorHandler.list_error_handler("list policies for role", [])
@AWSRetry.jittered_backoff()
def list_iam_role_policies(client, role_name):
    paginator = client.get_paginator("list_role_policies")
    return paginator.paginate(RoleName=role_name).build_full_result()["PolicyNames"]


@IAMErrorHandler.list_error_handler("list policies attached to role", [])
@AWSRetry.jittered_backoff()
def list_iam_role_attached_policies(client, role_name):
    paginator = client.get_paginator("list_attached_role_policies")
    return paginator.paginate(RoleName=role_name).build_full_result()["AttachedPolicies"]


@IAMErrorHandler.list_error_handler("list users", [])
@AWSRetry.jittered_backoff()
def list_iam_users(client, path=None):
    args = {}
    if path is None:
        args = {"PathPrefix": path}
    paginator = client.get_paginator("list_users")
    return paginator.paginate(**args).build_full_result()["Users"]


@IAMErrorHandler.common_error_handler("list all managed policies")
@AWSRetry.jittered_backoff()
def list_iam_managed_policies(client, **kwargs):
    paginator = client.get_paginator("list_policies")
    return paginator.paginate(**kwargs).build_full_result()["Policies"]


list_managed_policies = list_iam_managed_policies


@IAMErrorHandler.list_error_handler("list entities for policy", [])
@AWSRetry.jittered_backoff()
def list_iam_entities_for_policy(client, arn):
    paginator = client.get_paginator("list_entities_for_policy")
    return paginator.paginate(PolicyArn=arn).build_full_result()


@IAMErrorHandler.list_error_handler("list roles", [])
@AWSRetry.jittered_backoff()
def list_iam_roles(client, path=None):
    args = {}
    if path:
        args["PathPrefix"] = path
    paginator = client.get_paginator("list_roles")
    return paginator.paginate(**args).build_full_result()["Roles"]


@IAMErrorHandler.list_error_handler("list mfa devices", [])
@AWSRetry.jittered_backoff()
def list_iam_mfa_devices(client, user=None):
    args = {}
    if user:
        args["UserName"] = user
    paginator = client.get_paginator("list_mfa_devices")
    return paginator.paginate(**args).build_full_result()["MFADevices"]


@IAMErrorHandler.list_error_handler("get role")
@AWSRetry.jittered_backoff()
def get_iam_role(client, name):
    return client.get_role(RoleName=name)["Role"]


@IAMErrorHandler.list_error_handler("get group")
@AWSRetry.jittered_backoff()
def get_iam_group(client, name):
    paginator = client.get_paginator("get_group")
    return paginator.paginate(GroupName=name).build_full_result()


@IAMErrorHandler.list_error_handler("get access keys for user", [])
@AWSRetry.jittered_backoff()
def get_iam_access_keys(client, user):
    results = client.list_access_keys(UserName=user)
    return normalize_iam_access_keys(results.get("AccessKeyMetadata", []))


@IAMErrorHandler.list_error_handler("get user")
@AWSRetry.jittered_backoff()
def get_iam_user(client, user):
    results = client.get_user(UserName=user)
    return normalize_iam_user(results.get("User", []))


def find_iam_managed_policy_by_name(client, name):
    policies = list_iam_managed_policies(client)
    for policy in policies:
        if policy["PolicyName"] == name:
            return policy
    return None


def get_iam_managed_policy_by_name(client, name):
    # get_policy() requires an ARN, and list_policies() doesn't return all fields, so we need to do both :(
    policy = find_iam_managed_policy_by_name(client, name)
    if policy is None:
        return None
    return get_iam_managed_policy_by_arn(client, policy["Arn"])


@IAMErrorHandler.common_error_handler("get policy")
@AWSRetry.jittered_backoff()
def get_iam_managed_policy_by_arn(client, arn):
    policy = client.get_policy(PolicyArn=arn)["Policy"]
    return policy


@IAMErrorHandler.common_error_handler("list policy versions")
@AWSRetry.jittered_backoff()
def list_iam_managed_policy_versions(client, arn):
    return client.list_policy_versions(PolicyArn=arn)["Versions"]


@IAMErrorHandler.common_error_handler("get policy version")
@AWSRetry.jittered_backoff()
def get_iam_managed_policy_version(client, arn, version):
    return client.get_policy_version(PolicyArn=arn, VersionId=version)["PolicyVersion"]


def convert_managed_policy_names_to_arns(client, policy_names):
    if all(validate_aws_arn(policy, service="iam") for policy in policy_names if policy is not None):
        return policy_names
    allpolicies = {}
    policies = list_iam_managed_policies(client)

    for policy in policies:
        allpolicies[policy["PolicyName"]] = policy["Arn"]
        allpolicies[policy["Arn"]] = policy["Arn"]
    try:
        return [allpolicies[policy] for policy in policy_names if policy is not None]
    except KeyError as e:
        raise AnsibleIAMError(message="Failed to find policy by name:" + str(e), exception=e) from e


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
        except (  # pylint: disable=duplicate-except
            botocore.exceptions.BotoCoreError,
            botocore.exceptions.ClientError,
        ) as e:
            module.fail_json_aws(
                e,
                msg="Failed to get AWS account information, Try allowing sts:GetCallerIdentity or iam:GetUser permissions.",
            )

    if account_id is None or partition is None:
        module.fail_json(
            msg="Failed to get AWS account information, Try allowing sts:GetCallerIdentity or iam:GetUser permissions.",
        )

    return (to_native(account_id), to_native(partition))


@IAMErrorHandler.common_error_handler("create instance profile")
@AWSRetry.jittered_backoff()
def create_iam_instance_profile(client, name, path, tags):
    boto3_tags = ansible_dict_to_boto3_tag_list(tags or {})
    path = path or "/"
    result = client.create_instance_profile(InstanceProfileName=name, Path=path, Tags=boto3_tags)
    return result["InstanceProfile"]


@IAMErrorHandler.deletion_error_handler("delete instance profile")
@AWSRetry.jittered_backoff()
def delete_iam_instance_profile(client, name):
    client.delete_instance_profile(InstanceProfileName=name)
    # Error Handler will return False if the resource didn't exist
    return True


@IAMErrorHandler.common_error_handler("add role to instance profile")
@AWSRetry.jittered_backoff()
def add_role_to_iam_instance_profile(client, profile_name, role_name):
    client.add_role_to_instance_profile(InstanceProfileName=profile_name, RoleName=role_name)
    return True


@IAMErrorHandler.deletion_error_handler("remove role from instance profile")
@AWSRetry.jittered_backoff()
def remove_role_from_iam_instance_profile(client, profile_name, role_name):
    client.remove_role_from_instance_profile(InstanceProfileName=profile_name, RoleName=role_name)
    # Error Handler will return False if the resource didn't exist
    return True


@IAMErrorHandler.list_error_handler("list instance profiles", [])
def list_iam_instance_profiles(client, name=None, prefix=None, role=None):
    """
    Returns a list of IAM instance profiles in boto3 format.
    Profiles need to be converted to Ansible format using normalize_iam_instance_profile before being displayed.

    See also: normalize_iam_instance_profile
    """
    if role:
        return _list_iam_instance_profiles_for_role(client, RoleName=role)
    if name:
        # Unlike the others this returns a single result, make this a list with 1 element.
        return [_get_iam_instance_profiles(client, InstanceProfileName=name)]
    if prefix:
        return _list_iam_instance_profiles(client, PathPrefix=prefix)
    return _list_iam_instance_profiles(client)


@IAMErrorHandler.common_error_handler("tag instance profile")
@AWSRetry.jittered_backoff()
def tag_iam_instance_profile(client, name, tags):
    if not tags:
        return
    boto3_tags = ansible_dict_to_boto3_tag_list(tags or {})
    result = client.tag_instance_profile(InstanceProfileName=name, Tags=boto3_tags)


@IAMErrorHandler.common_error_handler("untag instance profile")
@AWSRetry.jittered_backoff()
def untag_iam_instance_profile(client, name, tags):
    if not tags:
        return
    client.untag_instance_profile(InstanceProfileName=name, TagKeys=tags)


@IAMErrorHandler.common_error_handler("tag managed policy")
@AWSRetry.jittered_backoff()
def tag_iam_policy(client, arn, tags):
    if not tags:
        return
    boto3_tags = ansible_dict_to_boto3_tag_list(tags or {})
    client.tag_policy(PolicyArn=arn, Tags=boto3_tags)


@IAMErrorHandler.common_error_handler("untag managed policy")
@AWSRetry.jittered_backoff()
def untag_iam_policy(client, arn, tags):
    if not tags:
        return
    client.untag_policy(PolicyArn=arn, TagKeys=tags)


def _validate_iam_name(resource_type, name=None):
    if name is None:
        return None
    LENGTHS = {"role": 64, "user": 64}
    regex = r"[\w+=,.@-]+"
    max_length = LENGTHS.get(resource_type, 128)
    if len(name) > max_length:
        return f"Length of {resource_type} name may not exceed {max_length}"
    if not re.fullmatch(regex, name):
        return f"{resource_type} name must match pattern {regex}"
    return None


def _validate_iam_path(resource_type, path=None):
    if path is None:
        return None
    regex = r"\/([\w+=,.@-]+\/)*"
    max_length = 512
    if len(path) > max_length:
        return f"Length of {resource_type} path may not exceed {max_length}"
    if not path.endswith("/") or not path.startswith("/"):
        return f"{resource_type} path must begin and end with /"
    if not re.fullmatch(regex, path):
        return f"{resource_type} path must match pattern {regex}"
    return None


def validate_iam_identifiers(resource_type, name=None, path=None):
    name_problem = _validate_iam_name(resource_type, name)
    if name_problem:
        return name_problem
    path_problem = _validate_iam_path(resource_type, path)
    if path_problem:
        return path_problem

    return None


def normalize_iam_mfa_device(device: BotoResource) -> AnsibleAWSResource:
    """Converts IAM MFA Device from the CamelCase boto3 format to the snake_case Ansible format"""
    # MFA Devices don't support Tags (as of 1.34.52)
    return boto3_resource_to_ansible_dict(device)


def normalize_iam_mfa_devices(devices: BotoResourceList) -> AnsibleAWSResourceList:
    """Converts a list of IAM MFA Devices from the CamelCase boto3 format to the snake_case Ansible format"""
    # MFA Devices don't support Tags (as of 1.34.52)
    return boto3_resource_list_to_ansible_dict(devices)


def normalize_iam_user(user: BotoResource) -> AnsibleAWSResource:
    """Converts IAM users from the CamelCase boto3 format to the snake_case Ansible format"""
    return boto3_resource_to_ansible_dict(user)


def normalize_iam_policy(policy: BotoResource) -> AnsibleAWSResource:
    """Converts IAM policies from the CamelCase boto3 format to the snake_case Ansible format"""
    return boto3_resource_to_ansible_dict(policy)


def normalize_iam_group(group: BotoResource) -> AnsibleAWSResource:
    """Converts IAM Groups from the CamelCase boto3 format to the snake_case Ansible format"""
    # Groups don't support Tags (as of 1.34.52)
    return boto3_resource_to_ansible_dict(group, force_tags=False)


def normalize_iam_access_key(access_key: BotoResource) -> AnsibleAWSResource:
    """Converts IAM access keys from the CamelCase boto3 format to the snake_case Ansible format"""
    # Access Keys don't support Tags (as of 1.34.52)
    return boto3_resource_to_ansible_dict(access_key, force_tags=False)


def normalize_iam_access_keys(access_keys: BotoResourceList) -> AnsibleAWSResourceList:
    """Converts a list of IAM access keys from the CamelCase boto3 format to the snake_case Ansible format"""
    # Access Keys don't support Tags (as of 1.34.52)
    if not access_keys:
        return access_keys
    access_keys = boto3_resource_list_to_ansible_dict(access_keys, force_tags=False)
    return sorted(access_keys, key=lambda d: d.get("create_date", None))


def normalize_iam_instance_profile(profile: BotoResource) -> AnsibleAWSResource:
    """
    Converts a boto3 format IAM instance profile into "Ansible" format
    """
    transforms = {"Roles": _normalize_iam_roles}
    transformed_profile = boto3_resource_to_ansible_dict(profile, nested_transforms=transforms)
    return transformed_profile


def normalize_iam_role(role: BotoResource, _v7_compat: bool = False) -> AnsibleAWSResource:
    """
    Converts a boto3 format IAM instance role into "Ansible" format

    _v7_compat is deprecated and will be removed in release after 2026-05-01 DO NOT USE.
    """
    transforms = {"InstanceProfiles": _normalize_iam_instance_profiles}
    ignore_list = ["AssumeRolePolicyDocument"]
    transformed_role = boto3_resource_to_ansible_dict(role, nested_transforms=transforms, ignore_list=ignore_list)
    if _v7_compat and role.get("AssumeRolePolicyDocument"):
        transformed_role["assume_role_policy_document_raw"] = role["AssumeRolePolicyDocument"]
    return transformed_role


def _normalize_iam_instance_profiles(profiles: BotoResourceList) -> AnsibleAWSResourceList:
    if not profiles:
        return profiles
    return [normalize_iam_instance_profile(p) for p in profiles]


def _normalize_iam_roles(roles: BotoResourceList) -> AnsibleAWSResourceList:
    if not roles:
        return roles
    return [normalize_iam_role(r) for r in roles]
