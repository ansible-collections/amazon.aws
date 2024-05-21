#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: iam_instance_profile_info
version_added: 6.2.0
short_description: gather information on IAM instance profiles
description:
  - Gathers information about IAM instance profiles.
author:
  - Mark Chappell (@tremble)
options:
  name:
    description:
      - Name of an instance profile to search for.
      - Mutually exclusive with I(prefix).
    aliases:
      - instance_profile_name
    type: str
  path_prefix:
    description:
      - The path prefix for filtering the results.
      - Mutually exclusive with I(name).
    aliases: ["path", "prefix"]
    type: str

extends_documentation_fragment:
    - amazon.aws.common.modules
    - amazon.aws.region.modules
    - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Find all existing IAM instance profiles
  amazon.aws.iam_instance_profile_info:
  register: result

- name: Describe a single instance profile
  amazon.aws.iam_instance_profile_info:
    name: MyIAMProfile
  register: result

- name: Find all IAM instance profiles starting with /some/path/
  amazon.aws.iam_instance_profile_info:
    prefile: /some/path/
  register: result
"""

RETURN = r"""
iam_instance_profiles:
  description: List of IAM instance profiles
  returned: always
  type: complex
  contains:
    arn:
      description: Amazon Resource Name for the instance profile.
      returned: always
      type: str
      sample: arn:aws:iam::123456789012:instance-profile/AnsibleTestProfile
    create_date:
      description: Date instance profile was created.
      returned: always
      type: str
      sample: '2023-01-12T11:18:29+00:00'
    instance_profile_id:
      description: Amazon Identifier for the instance profile.
      returned: always
      type: str
      sample: AROA12345EXAMPLE54321
    instance_profile_name:
      description: Name of instance profile.
      returned: always
      type: str
      sample: AnsibleTestEC2Policy
    path:
      description: Path of instance profile.
      returned: always
      type: str
      sample: /
    roles:
      description: List of roles associated with this instance profile.
      returned: always
      type: list
      sample: []
"""

from ansible_collections.amazon.aws.plugins.module_utils.iam import AnsibleIAMError
from ansible_collections.amazon.aws.plugins.module_utils.iam import list_iam_instance_profiles
from ansible_collections.amazon.aws.plugins.module_utils.iam import normalize_iam_instance_profile
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def describe_iam_instance_profiles(module, client):
    name = module.params["name"]
    prefix = module.params["path_prefix"]
    profiles = []
    profiles = list_iam_instance_profiles(client, name=name, prefix=prefix)

    return [normalize_iam_instance_profile(p) for p in profiles]


def main():
    """
    Module action handler
    """
    argument_spec = dict(
        name=dict(aliases=["instance_profile_name"]),
        path_prefix=dict(aliases=["path", "prefix"]),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[["name", "path_prefix"]],
    )

    client = module.client("iam", retry_decorator=AWSRetry.jittered_backoff())
    try:
        module.exit_json(changed=False, iam_instance_profiles=describe_iam_instance_profiles(module, client))
    except AnsibleIAMError as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
