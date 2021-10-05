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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from functools import cmp_to_key

from ansible.module_utils._text import to_text
from ansible.module_utils.six import binary_type
from ansible.module_utils.six import string_types


def _hashable_policy(policy, policy_list):
    """
        Takes a policy and returns a list, the contents of which are all hashable and sorted.
        Example input policy:
        {'Version': '2012-10-17',
         'Statement': [{'Action': 's3:PutObjectAcl',
                        'Sid': 'AddCannedAcl2',
                        'Resource': 'arn:aws:s3:::test_policy/*',
                        'Effect': 'Allow',
                        'Principal': {'AWS': ['arn:aws:iam::XXXXXXXXXXXX:user/username1', 'arn:aws:iam::XXXXXXXXXXXX:user/username2']}
                       }]}
        Returned value:
        [('Statement',  ((('Action', (u's3:PutObjectAcl',)),
                          ('Effect', (u'Allow',)),
                          ('Principal', ('AWS', ((u'arn:aws:iam::XXXXXXXXXXXX:user/username1',), (u'arn:aws:iam::XXXXXXXXXXXX:user/username2',)))),
                          ('Resource', (u'arn:aws:s3:::test_policy/*',)), ('Sid', (u'AddCannedAcl2',)))),
         ('Version', (u'2012-10-17',)))]

    """
    # Amazon will automatically convert bool and int to strings for us
    if isinstance(policy, bool):
        return tuple([str(policy).lower()])
    elif isinstance(policy, int):
        return tuple([str(policy)])

    if isinstance(policy, list):
        for each in policy:
            tupleified = _hashable_policy(each, [])
            if isinstance(tupleified, list):
                tupleified = tuple(tupleified)
            policy_list.append(tupleified)
    elif isinstance(policy, string_types) or isinstance(policy, binary_type):
        policy = to_text(policy)
        # convert root account ARNs to just account IDs
        if policy.startswith('arn:aws:iam::') and policy.endswith(':root'):
            policy = policy.split(':')[4]
        return [policy]
    elif isinstance(policy, dict):
        sorted_keys = list(policy.keys())
        sorted_keys.sort()
        for key in sorted_keys:
            element = policy[key]
            # Special case defined in
            # https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_principal.html
            if key in ["NotPrincipal", "Principal"] and policy[key] == "*":
                element = {"AWS": "*"}
            tupleified = _hashable_policy(element, [])
            if isinstance(tupleified, list):
                tupleified = tuple(tupleified)
            policy_list.append((key, tupleified))

    # ensure we aren't returning deeply nested structures of length 1
    if len(policy_list) == 1 and isinstance(policy_list[0], tuple):
        policy_list = policy_list[0]
    if isinstance(policy_list, list):
        policy_list.sort(key=cmp_to_key(_py3cmp))
    return policy_list


def _py3cmp(a, b):
    """ Python 2 can sort lists of mixed types. Strings < tuples. Without this function this fails on Python 3."""
    try:
        if a > b:
            return 1
        elif a < b:
            return -1
        else:
            return 0
    except TypeError as e:
        # check to see if they're tuple-string
        # always say strings are less than tuples (to maintain compatibility with python2)
        str_ind = to_text(e).find('str')
        tup_ind = to_text(e).find('tuple')
        if -1 not in (str_ind, tup_ind):
            if str_ind < tup_ind:
                return -1
            elif tup_ind < str_ind:
                return 1
        raise


def compare_policies(current_policy, new_policy, default_version="2008-10-17"):
    """ Compares the existing policy and the updated policy
        Returns True if there is a difference between policies.
    """
    # https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_version.html
    if default_version:
        if isinstance(current_policy, dict):
            current_policy = current_policy.copy()
            current_policy.setdefault("Version", default_version)
        if isinstance(new_policy, dict):
            new_policy = new_policy.copy()
            new_policy.setdefault("Version", default_version)

    return set(_hashable_policy(new_policy, [])) != set(_hashable_policy(current_policy, []))


def sort_json_policy_dict(policy_dict):

    """ Sort any lists in an IAM JSON policy so that comparison of two policies with identical values but
    different orders will return true
    Args:
        policy_dict (dict): Dict representing IAM JSON policy.
    Basic Usage:
        >>> my_iam_policy = {'Principle': {'AWS':["31","7","14","101"]}
        >>> sort_json_policy_dict(my_iam_policy)
    Returns:
        Dict: Will return a copy of the policy as a Dict but any List will be sorted
        {
            'Principle': {
                'AWS': [ '7', '14', '31', '101' ]
            }
        }
    """

    def value_is_list(my_list):

        checked_list = []
        for item in my_list:
            if isinstance(item, dict):
                checked_list.append(sort_json_policy_dict(item))
            elif isinstance(item, list):
                checked_list.append(value_is_list(item))
            else:
                checked_list.append(item)

        # Sort list. If it's a list of dictionaries, sort by tuple of key-value
        # pairs, since Python 3 doesn't allow comparisons such as `<` between dictionaries.
        checked_list.sort(key=lambda x: sorted(x.items()) if isinstance(x, dict) else x)
        return checked_list

    ordered_policy_dict = {}
    for key, value in policy_dict.items():
        if isinstance(value, dict):
            ordered_policy_dict[key] = sort_json_policy_dict(value)
        elif isinstance(value, list):
            ordered_policy_dict[key] = value_is_list(value)
        else:
            ordered_policy_dict[key] = value

    return ordered_policy_dict
