#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# A bare-minimum Ansible Module based on AnsibleAWSModule used for testing some
# of the core behaviour around variables

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict

def main():
    module = AnsibleAWSModule(
        argument_spec={},
        supports_check_mode=True,
    )

    client = module.client('sts')

    try:
        caller_info = client.get_caller_identity()
        caller_info.pop('ResponseMetadata', None)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to retrieve caller identity')

    # Return something, just because we can.
    module.exit_json(
        changed=False,
        **camel_dict_to_snake_dict(caller_info))


if __name__ == '__main__':
    main()
