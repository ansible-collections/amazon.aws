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

from ansible.module_utils._text import to_native
from ansible.module_utils._text import to_text
from ansible.module_utils.six import string_types


def boto3_tag_list_to_ansible_dict(tags_list, tag_name_key_name=None, tag_value_key_name=None):
    """Convert a boto3 list of resource tags to a flat dict of key:value pairs
    Args:
        tags_list (list): List of dicts representing AWS tags.
        tag_name_key_name (str): Value to use as the key for all tag keys (useful because boto3 doesn't always use "Key")
        tag_value_key_name (str): Value to use as the key for all tag values (useful because boto3 doesn't always use "Value")
    Basic Usage:
        >>> tags_list = [{'Key': 'MyTagKey', 'Value': 'MyTagValue'}]
        >>> boto3_tag_list_to_ansible_dict(tags_list)
        [
            {
                'Key': 'MyTagKey',
                'Value': 'MyTagValue'
            }
        ]
    Returns:
        Dict: Dict of key:value pairs representing AWS tags
         {
            'MyTagKey': 'MyTagValue',
        }
    """

    if tag_name_key_name and tag_value_key_name:
        tag_candidates = {tag_name_key_name: tag_value_key_name}
    else:
        tag_candidates = {"key": "value", "Key": "Value"}

    # minio seems to return [{}] as an empty tags_list
    if not tags_list or not any(tag for tag in tags_list):
        return {}
    for k, v in tag_candidates.items():
        if k in tags_list[0] and v in tags_list[0]:
            return dict((tag[k], tag[v]) for tag in tags_list)
    raise ValueError(f"Couldn't find tag key (candidates {str(tag_candidates)}) in tag list {str(tags_list)}")


def ansible_dict_to_boto3_tag_list(tags_dict, tag_name_key_name="Key", tag_value_key_name="Value"):
    """Convert a flat dict of key:value pairs representing AWS resource tags to a boto3 list of dicts

    Note: booleans are converted to their Capitalized text form ("True" and "False"), this is
    different to ansible_dict_to_boto3_filter_list because historically we've used "to_text()" and
    AWS stores tags as strings, whereas for things which are actually booleans in AWS are returned
    as lowercase strings in filters.

    Args:
        tags_dict (dict): Dict representing AWS resource tags.
        tag_name_key_name (str): Value to use as the key for all tag keys (useful because boto3 doesn't always use "Key")
        tag_value_key_name (str): Value to use as the key for all tag values (useful because boto3 doesn't always use "Value")
    Basic Usage:
        >>> tags_dict = {'MyTagKey': 'MyTagValue'}
        >>> ansible_dict_to_boto3_tag_list(tags_dict)
        {
            'MyTagKey': 'MyTagValue'
        }
    Returns:
        List: List of dicts containing tag keys and values
        [
            {
                'Key': 'MyTagKey',
                'Value': 'MyTagValue'
            }
        ]
    """

    if not tags_dict:
        return []

    tags_list = []
    for k, v in tags_dict.items():
        tags_list.append({tag_name_key_name: k, tag_value_key_name: to_native(v)})

    return tags_list


def _tag_name_to_filter_key(tag_name):
    return f"tag:{tag_name}"


def ansible_dict_to_tag_filter_dict(tags_dict):
    """Prepends "tag:" to all of the keys (not the values) in a dict
    This is useful when you're then going to build a filter including the tags.

    Note: booleans are converted to their Capitalized text form ("True" and "False"), this is
    different to ansible_dict_to_boto3_filter_list because historically we've used "to_text()" and
    AWS stores tags as strings, whereas for things which are actually booleans in AWS are returned
    as lowercase strings in filters.

    Args:
        tags_dict (dict): Dict representing AWS resource tags.

    Basic Usage:
        >>> filters = ansible_dict_to_boto3_filter_list(ansible_dict_to_tag_filter_dict(tags))

    Returns:
        Dict: A dictionary suitable for passing to ansible_dict_to_boto3_filter_list which can
        also be combined with other common filter parameters.
    """
    if not tags_dict:
        return {}
    return {_tag_name_to_filter_key(k): to_native(v) for k, v in tags_dict.items()}


def boto3_tag_specifications(tags_dict, types=None):
    """Converts a list of resource types and a flat dictionary of key:value pairs representing AWS
    resource tags to a TagSpecification object.

    https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_TagSpecification.html

    Args:
        tags_dict (dict): Dict representing AWS resource tags.
        types (list) A list of resource types to be tagged.
    Basic Usage:
        >>> tags_dict = {'MyTagKey': 'MyTagValue'}
        >>> boto3_tag_specifications(tags_dict, ['instance'])
        [
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'MyTagKey',
                        'Value': 'MyTagValue'
                    }
                ]
            }
        ]
    Returns:
        List: List of dictionaries representing an AWS Tag Specification
    """
    if not tags_dict:
        return None
    specifications = list()
    tag_list = ansible_dict_to_boto3_tag_list(tags_dict)

    if not types:
        specifications.append(dict(Tags=tag_list))
        return specifications

    if isinstance(types, string_types):
        types = [types]

    for type_name in types:
        specifications.append(dict(ResourceType=type_name, Tags=tag_list))

    return specifications


def compare_aws_tags(current_tags_dict, new_tags_dict, purge_tags=True):
    """
    Compare two dicts of AWS tags. Dicts are expected to of been created using 'boto3_tag_list_to_ansible_dict' helper function.
    Two dicts are returned - the first is tags to be set, the second is any tags to remove. Since the AWS APIs differ
    these may not be able to be used out of the box.

    :param current_tags_dict:
    :param new_tags_dict:
    :param purge_tags:
    :return: tag_key_value_pairs_to_set: a dict of key value pairs that need to be set in AWS. If all tags are identical this dict will be empty
    :return: tag_keys_to_unset: a list of key names (type str) that need to be unset in AWS. If no tags need to be unset this list will be empty
    """

    tag_key_value_pairs_to_set = {}
    tag_keys_to_unset = []

    if purge_tags:
        for key in current_tags_dict.keys():
            if key in new_tags_dict:
                continue
            # Amazon have reserved 'aws:*' tags, we should avoid purging them as
            # this probably isn't what people want to do...
            if key.startswith("aws:"):
                continue
            tag_keys_to_unset.append(key)

    for key in set(new_tags_dict.keys()) - set(tag_keys_to_unset):
        if to_text(new_tags_dict[key]) != current_tags_dict.get(key):
            tag_key_value_pairs_to_set[key] = new_tags_dict[key]

    return tag_key_value_pairs_to_set, tag_keys_to_unset
