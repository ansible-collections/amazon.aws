# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ..botocore import get_boto3_client_method_parameters
from ..tagging import ansible_dict_to_boto3_tag_list
from .common import get_rds_method_attribute


def arg_spec_to_rds_params(options_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts snake_cased rds module options to CamelCased parameter formats expected by boto3 rds client.

    Does not alter case for keys or values in the following attributes: tags, processor_features.
    Includes special handling of certain boto3 params that do not follow standard CamelCase.

        Parameters:
            options_dict (dict): Snake-cased options for a boto3 rds client method

        Returns:
            camel_options (dct): Options formatted for boto3 rds client
    """
    tags = options_dict.pop("tags")
    has_processor_features = False
    if "processor_features" in options_dict:
        has_processor_features = True
        processor_features = options_dict.pop("processor_features")
    camel_options = snake_dict_to_camel_dict(options_dict, capitalize_first=True)
    aws_replace_keys = (
        ("Db", "DB"),
        ("Iam", "IAM"),
        ("Az", "AZ"),
        ("Ca", "CA"),
        ("PerformanceInsightsKmsKeyId", "PerformanceInsightsKMSKeyId"),
    )
    for key in camel_options.copy():
        for old, new in aws_replace_keys:
            if old in key:
                camel_options[key.replace(old, new)] = camel_options.pop(key)
    camel_options["Tags"] = tags
    if has_processor_features:
        camel_options["ProcessorFeatures"] = processor_features
    return camel_options


def format_rds_client_method_parameters(
    client, module, parameters: Dict[str, Any], method_name: str, format_tags: bool
) -> Dict[str, Any]:
    """
    Returns a dict of parameters validated and formatted for the provided boto3 client method.

    Performs the following parameters checks and updates:
        - Converts parameters supplied as snake_cased module options to CamelCase
        - Ensures that all required parameters for the provided method are present
        - Ensures that only parameters allowed for the provided method are present, removing any that are not relevant
        - Removes parameters with None values
        - If format_tags is True, converts "Tags" param from an Ansible dict to boto3 list of dicts

        Parameters:
            client: boto3 rds client
            module: AnsibleAWSModule
            parameters (dict): Parameter options as provided to module
            method_name (str): boto3 client method for which to validate parameters
            format_tags (bool): Whether to convert tags from an Ansible dict to boto3 list of dicts

        Returns:
            Dict of client parameters formatted for the provided method

        Raises:
            Fails the module if any parameters required by the provided method are not provided in module options
    """
    required_options = get_boto3_client_method_parameters(client, method_name, required=True)
    if any(parameters.get(k) is None for k in required_options):
        method_description = get_rds_method_attribute(method_name, module).operation_description
        module.fail_json(msg=f"To {method_description} requires the parameters: {required_options}")
    options = get_boto3_client_method_parameters(client, method_name)
    parameters = {k: v for k, v in parameters.items() if k in options and v is not None}
    if format_tags and parameters.get("Tags"):
        parameters["Tags"] = ansible_dict_to_boto3_tag_list(parameters["Tags"])

    return parameters


def compare_iam_roles(
    existing_roles: List[Dict[str, str]], target_roles: List[Dict[str, str]], purge_roles: bool
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Returns differences between target and existing IAM roles.

        Parameters:
            existing_roles (list): Existing IAM roles as a list of snake-cased dicts
            target_roles (list): Target IAM roles as a list of snake-cased dicts
            purge_roles (bool): Remove roles not in target_roles if True

        Returns:
            roles_to_add (list): List of IAM roles to add
            roles_to_delete (list): List of IAM roles to delete
    """
    existing_roles = [{k: v for k, v in role.items() if k != "status"} for role in existing_roles]
    roles_to_add = [role for role in target_roles if role not in existing_roles]
    roles_to_remove = [role for role in existing_roles if role not in target_roles] if purge_roles else []
    return roles_to_add, roles_to_remove
