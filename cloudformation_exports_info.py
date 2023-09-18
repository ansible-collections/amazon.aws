#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
module: cloudformation_exports_info
short_description: Read a value from CloudFormation Exports
version_added: 1.0.0
description:
  - Module retrieves a value from CloudFormation Exports
author:
  - "Michael Moyle (@mmoyle)"
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.
- name: Get Exports
  community.aws.cloudformation_exports_info: {}
  register: cf_exports
- ansible.builtin.debug:
    msg: "{{ cf_exports }}"
"""

RETURN = r"""
export_items:
    description: A dictionary of Exports items names and values.
    returned: Always
    type: dict
"""

try:
    from botocore.exceptions import ClientError
    from botocore.exceptions import BotoCoreError
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


@AWSRetry.exponential_backoff()
def list_exports(cloudformation_client):
    """Get Exports Names and Values and return in dictionary"""
    list_exports_paginator = cloudformation_client.get_paginator("list_exports")
    exports = list_exports_paginator.paginate().build_full_result()["Exports"]
    export_items = dict()

    for item in exports:
        export_items[item["Name"]] = item["Value"]

    return export_items


def main():
    argument_spec = dict()
    result = dict(changed=False, original_message="")

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)
    cloudformation_client = module.client("cloudformation")

    try:
        result["export_items"] = list_exports(cloudformation_client)

    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e)

    result.update()
    module.exit_json(**result)


if __name__ == "__main__":
    main()
