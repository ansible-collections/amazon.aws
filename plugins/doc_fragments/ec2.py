# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Ansible, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # EC2 only documentation fragment
    DOCUMENTATION = r'''
options:
    region:
        description:
          - The AWS region to use.
          - For global services such as IAM, Route53 and CloudFront, I(region)
            is ignored.
          - The C(AWS_REGION) or C(EC2_REGION) environment variables may also
            be used.
          - See the Amazon AWS documentation for more information
            U(http://docs.aws.amazon.com/general/latest/gr/rande.html#ec2_region).
          - The C(ec2_region) alias has been deprecated and will be removed in
            a release after 2024-12-01
          - Support for the C(EC2_REGION) environment variable has been
            deprecated and will be removed in a release after 2024-12-01.
        type: str
        aliases: [ aws_region, ec2_region ]
'''
