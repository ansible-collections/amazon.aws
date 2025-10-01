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

from functools import cmp_to_key

from ansible.module_utils._text import to_text


def _canonify_root_arn(arn):
    # There are multiple ways to specifiy delegation of access to an account
    # https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_principal.html#principal-accounts
    if arn.startswith("arn:aws:iam::") and arn.endswith(":root"):
        arn = arn.split(":")[4]
    return arn


def _canonify_policy_dict_item(item, key):
    """
    Converts special cases where there are multiple ways to write the same thing into a single form
    """
    # There are multiple ways to specify anonymous principals
    # https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_principal.html#principal-anonymous
    if key in ["NotPrincipal", "Principal"]:
        if item == "*":
            return {"AWS": "*"}
    return item


def _tuplify_list(element):
    if isinstance(element, list):
        return tuple(element)
    return element


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
    [('Statement',  ((('Action', ('s3:PutObjectAcl',)),
                      ('Effect', ('Allow',)),
                      ('Principal', ('AWS', (('arn:aws:iam::XXXXXXXXXXXX:user/username1',), ('arn:aws:iam::XXXXXXXXXXXX:user/username2',)))),
                      ('Resource', ('arn:aws:s3:::test_policy/*',)), ('Sid', ('AddCannedAcl2',)))),
     ('Version', ('2012-10-17',)))]

    """
    # Amazon will automatically convert bool and int to strings for us
    if isinstance(policy, bool):
        return tuple([str(policy).lower()])
    elif isinstance(policy, int):
        return tuple([str(policy)])

    if isinstance(policy, list):
        for each in policy:
            hashed_policy = _hashable_policy(each, [])
            tupleified = _tuplify_list(hashed_policy)
            policy_list.append(tupleified)
    elif isinstance(policy, str) or isinstance(policy, bytes):
        policy = to_text(policy)
        # convert root account ARNs to just account IDs
        policy = _canonify_root_arn(policy)
        return [policy]
    elif isinstance(policy, dict):
        # Sort the keys to ensure a consistent order for later comparison
        sorted_keys = list(policy.keys())
        sorted_keys.sort()
        for key in sorted_keys:
            # Converts special cases to a consistent form
            element = _canonify_policy_dict_item(policy[key], key)
            hashed_policy = _hashable_policy(element, [])
            tupleified = _tuplify_list(hashed_policy)
            policy_list.append((key, tupleified))
    # ensure we aren't returning deeply nested structures of length 1
    if len(policy_list) == 1 and isinstance(policy_list[0], tuple):
        policy_list = policy_list[0]
    if isinstance(policy_list, list):
        policy_list.sort(key=cmp_to_key(_py3cmp))
    return policy_list


def _py3cmp(a, b):
    """Python 2 can sort lists of mixed types. Strings < tuples. Without this function this fails on Python 3."""
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
        str_ind = to_text(e).find("str")
        tup_ind = to_text(e).find("tuple")
        if -1 not in (str_ind, tup_ind):
            if str_ind < tup_ind:
                return -1
            elif tup_ind < str_ind:
                return 1
        raise


def compare_policies(current_policy, new_policy, default_version="2008-10-17"):
    """Compares the existing policy and the updated policy
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
