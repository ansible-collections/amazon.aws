# -*- coding: utf-8 -*-

# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from copy import deepcopy
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Union

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.six import integer_types
from ansible.module_utils.six import string_types

from .botocore import normalize_boto3_result
from .tagging import boto3_tag_list_to_ansible_dict

BotoResource = Union[None, Mapping[str, Any]]
BotoResourceList = Union[None, Sequence[Mapping[str, Any]]]
AnsibleAWSResource = Union[None, Mapping[str, Any]]
AnsibleAWSResourceList = Union[None, Sequence[Mapping[str, Any]]]


def ansible_dict_to_boto3_filter_list(filters_dict):
    """Convert an Ansible dict of filters to list of dicts that boto3 can use
    Args:
        filters_dict (dict): Dict of AWS filters.
    Basic Usage:
        >>> filters = {'some-aws-id': 'i-01234567'}
        >>> ansible_dict_to_boto3_filter_list(filters)
        {
            'some-aws-id': 'i-01234567'
        }
    Returns:
        List: List of AWS filters and their values
        [
            {
                'Name': 'some-aws-id',
                'Values': [
                    'i-01234567',
                ]
            }
        ]
    """

    filters_list = []
    for k, v in filters_dict.items():
        filter_dict = {"Name": k}
        if isinstance(v, bool):
            filter_dict["Values"] = [str(v).lower()]
        elif isinstance(v, integer_types):
            filter_dict["Values"] = [str(v)]
        elif isinstance(v, string_types):
            filter_dict["Values"] = [v]
        else:
            filter_dict["Values"] = v

        filters_list.append(filter_dict)

    return filters_list


def map_complex_type(complex_type, type_map):
    """
    Allows to cast elements within a dictionary to a specific type
    Example of usage:

    DEPLOYMENT_CONFIGURATION_TYPE_MAP = {
        'maximum_percent': 'int',
        'minimum_healthy_percent': 'int'
    }

    deployment_configuration = map_complex_type(module.params['deployment_configuration'],
                                                DEPLOYMENT_CONFIGURATION_TYPE_MAP)

    This ensures all keys within the root element are casted and valid integers
    """

    if complex_type is None:
        return
    new_type = type(complex_type)()
    if isinstance(complex_type, dict):
        for key in complex_type:
            if key in type_map:
                if isinstance(type_map[key], list):
                    new_type[key] = map_complex_type(complex_type[key], type_map[key][0])
                else:
                    new_type[key] = map_complex_type(complex_type[key], type_map[key])
            else:
                new_type[key] = complex_type[key]
    elif isinstance(complex_type, list):
        for i in range(len(complex_type)):
            new_type.append(map_complex_type(complex_type[i], type_map))
    elif type_map:
        return globals()["__builtins__"][type_map](complex_type)
    return new_type


def scrub_none_parameters(parameters, descend_into_lists=True):
    """
    Iterate over a dictionary removing any keys that have a None value

    Reference: https://github.com/ansible-collections/community.aws/issues/251
    Credit: https://medium.com/better-programming/how-to-remove-null-none-values-from-a-dictionary-in-python-1bedf1aab5e4

    :param descend_into_lists: whether or not to descend in to lists to continue to remove None values
    :param parameters: parameter dict
    :return: parameter dict with all keys = None removed
    """

    clean_parameters = {}

    for k, v in parameters.items():
        if isinstance(v, dict):
            clean_parameters[k] = scrub_none_parameters(v, descend_into_lists=descend_into_lists)
        elif descend_into_lists and isinstance(v, list):
            clean_parameters[k] = [
                scrub_none_parameters(vv, descend_into_lists=descend_into_lists) if isinstance(vv, dict) else vv
                for vv in v
            ]
        elif v is not None:
            clean_parameters[k] = v

    return clean_parameters


def _perform_nested_transforms(
    resource: Mapping[str, Any],
    nested_transforms: Optional[Mapping[str, Callable]],
) -> Mapping[str, Any]:
    if not nested_transforms:
        return resource

    for k, transform in nested_transforms.items():
        if k in resource:
            resource[k] = transform(resource[k])

    return resource


def boto3_resource_to_ansible_dict(
    resource: BotoResource,
    transform_tags: bool = True,
    force_tags: bool = True,
    normalize: bool = True,
    ignore_list: Optional[Sequence[str]] = None,
    nested_transforms: Optional[Mapping[str, Callable]] = None,
) -> AnsibleAWSResource:
    """
    Transforms boto3-style (CamelCase) resource to the ansible-style (snake_case).

    :param resource: a dictionary representing the resource
    :param transform_tags: whether or not to perform "tag list" to "dictionary" conversion on the "Tags" key
    :param normalize: whether resources should be passed through .botocore.normalize_boto3_result
    :param ignore_list: a list of keys, the contents of which should not be transformed
    :param nested_transforms: a mapping of keys to Callable, the Callable will only be passed the value for the key
                              in the resource dictionary
    :return: dictionary representing the transformed resource
    """
    if not resource:
        return resource
    ignore_list = ignore_list or []
    nested_transforms = nested_transforms or {}

    transformed_resource = deepcopy(resource)
    if normalize:
        transformed_resource = normalize_boto3_result(transformed_resource)
    transformed_resource = _perform_nested_transforms(transformed_resource, nested_transforms)
    ignore_list = [*ignore_list, *nested_transforms]
    camel_resource = camel_dict_to_snake_dict(transformed_resource, ignore_list=ignore_list)
    if transform_tags and "Tags" in resource:
        camel_resource["tags"] = boto3_tag_list_to_ansible_dict(resource["Tags"])
    if force_tags and "Tags" not in resource:
        camel_resource["tags"] = {}

    return camel_resource


def boto3_resource_list_to_ansible_dict(
    resource_list: BotoResourceList,
    transform_tags: bool = True,
    force_tags: bool = True,
    normalize: bool = True,
    ignore_list: Optional[Sequence[str]] = None,
    nested_transforms: Optional[Mapping[str, Callable]] = None,
) -> AnsibleAWSResourceList:
    """
    Transforms a list of boto3-style (CamelCase) resources to the ansible-style (snake_case).

    :param resource_list: a list of dictionaries representing the resources
    :param transform_tags: whether or not to perform "tag list" to "dictionary" conversion on the "Tags" key
    :param normalize: whether resources should be passed through .botocore.normalize_boto3_result()
    :param ignore_list: a list of keys, the contents of which should not be transformed
    :param nested_transforms: a mapping of keys to Callable, the Callable will only be passed the value for the key
                              in the resource dictionary
    :return: list of dictionaries representing the transformed resources
    """
    if not resource_list:
        return resource_list
    return [
        boto3_resource_to_ansible_dict(resource, transform_tags, force_tags, normalize, ignore_list, nested_transforms)
        for resource in resource_list
    ]


def sanitize_filters_to_boto3_filter_list(
    filters: Dict[str, Any], ignore_keys: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Replace filter key underscores with dashes, for compatibility and transform ansible dict
    into boto3 filter list.

    :param filters: Ansible module params filters.
    :param ignore_keys: A list of keys to ignore.
    :return: Sanitized filters
    """
    sanitized_filters = deepcopy(filters)
    for k, v in filters.items():
        if ignore_keys and any((k.startswith(x) for x in ignore_keys)):
            continue
        if "_" in k:
            sanitized_filters[k.replace("_", "-")] = v
            del sanitized_filters[k]
    return ansible_dict_to_boto3_filter_list(sanitized_filters)
