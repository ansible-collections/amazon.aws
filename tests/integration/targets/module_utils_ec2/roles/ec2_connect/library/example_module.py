#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# A bare-minimum Ansible Module based on AnsibleAWSModule used for testing some
# of the core behaviour around AWS/Boto3 connection details

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


try:
    import boto.ec2
except ImportError:
    pass

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ec2_connect


def main():
    module = AnsibleAWSModule(
        argument_spec={},
        supports_check_mode=True,
        check_boto3=False,
    )

    try:
        client = ec2_connect(module)
    except boto.exception.NoAuthHandlerFound as e:
        module.fail_json_aws(e, msg='Failed to get connection')

    filters = {'name': 'amzn2-ami-hvm-2.0.202006*-x86_64-gp2'}

    try:
        images = client.get_all_images(image_ids=[], filters=filters, owners=['amazon'], executable_by=[])
    except boto.exception.BotoServerError as e:
        module.fail_json_aws(e, msg='Fail JSON AWS')

    images_out = []
    for image in images:
        images_out.append(image.id)

    # Return something, just because we can.
    module.exit_json(
        changed=False,
        images=images_out)


if __name__ == '__main__':
    main()
