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
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict


def main():
    module = AnsibleAWSModule(
        argument_spec={},
        supports_check_mode=True,
    )

    decorator = AWSRetry.jittered_backoff()
    client = module.client('ec2', retry_decorator=decorator)

    filters = ansible_dict_to_boto3_filter_list({'name': 'amzn2-ami-hvm-2.0.202006*-x86_64-gp2'})

    try:
        images = client.describe_images(aws_retry=True, ImageIds=[], Filters=filters, Owners=['amazon'], ExecutableUsers=[])
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Fail JSON AWS')

    # Return something, just because we can.
    module.exit_json(
        changed=False,
        **camel_dict_to_snake_dict(images))


if __name__ == '__main__':
    main()
