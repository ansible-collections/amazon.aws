#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: backup_tag_info
version_added: 6.0.0
short_description: List tags on AWS Backup resources
description:
    - List tags on AWS backup resources such as backup plan, backup vault, and recovery point.
    - Resources are referenced using ARN.
author:
    - Mandar Vijay Kulkarni (@mandar242)
options:
  resource:
    description:
      - The Amazon Resource Name (ARN) of the backup resource.
    required: true
    type: str

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: List tags on a resource
  amazon.aws.backup_tag_info:
    resource: "{{ backup_resource_arn }}"
"""

RETURN = r"""
tags:
  description: A dict containing the tags on the resource.
  returned: always
  type: dict
"""

from ansible_collections.amazon.aws.plugins.module_utils.backup import get_backup_resource_tags
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule


def main():
    argument_spec = dict(
        resource=dict(required=True, type="str"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    backup_client = module.client("backup")

    current_tags = get_backup_resource_tags(module, backup_client, module.params["resource"])

    module.exit_json(changed=False, tags=current_tags)


if __name__ == "__main__":
    main()
