#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# A bare-minimum Ansible Module based on AnsibleAWSModule used for testing some
# of the core behaviour around AWS/Boto3 connection details

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.waiters import get_waiter


def main():
    argument_spec = dict(
        client=dict(required=True, type='str'),
        waiter_name=dict(required=True, type='str'),
        with_decorator=dict(required=False, type='bool', default=False),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    decorator = None
    if module.params.get('with_decorator'):
        decorator = AWSRetry.jittered_backoff()

    client = module.client(module.params.get('client'), retry_decorator=decorator)
    waiter = get_waiter(client, module.params.get('waiter_name'))

    module.exit_json(changed=False, waiter_attributes=dir(waiter))


if __name__ == '__main__':
    main()
