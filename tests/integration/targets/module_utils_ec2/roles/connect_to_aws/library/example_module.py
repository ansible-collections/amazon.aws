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
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import connect_to_aws
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import get_aws_connection_info


def main():
    module = AnsibleAWSModule(
        argument_spec={},
        supports_check_mode=True,
        check_boto3=False,
    )

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)
    if not region:
        module.fail_json(msg="Fail JSON: No Region")

    try:
        client = connect_to_aws(boto.ec2, region, **aws_connect_params)
    except boto.exception.NoAuthHandlerFound as e:
        module.fail_json_aws(e, msg='No Authentication Handler Found')
    except AnsibleAWSError as e:
        module.fail_json_aws(e, msg='Fail JSON AWS')

    filters = {'name': 'amzn2-ami-hvm-2.0.202006*-x86_64-gp2'}

    try:
        images = client.get_all_images(image_ids=[], filters=filters, owners=['amazon'], executable_by=[])
    except (boto.exception.BotoServerError, AnsibleAWSError) as e:
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
