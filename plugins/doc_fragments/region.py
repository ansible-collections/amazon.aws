# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Ansible, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment:
    # Common configuration for all AWS services
    # Note: If you're updating MODULES, PLUGINS probably needs updating too.

    # Formatted for Modules
    # - modules don't support 'env'
    MODULES = r"""
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
"""

    # Formatted for non-module plugins
    # - modules don't support 'env'
    PLUGINS = r"""
options:
  region:
    description:
      - The AWS region to use.
      - See the Amazon AWS documentation for more information
        U(http://docs.aws.amazon.com/general/latest/gr/rande.html#ec2_region).
    type: str
    aliases: [ aws_region, ec2_region ]
    env:
      - name: AWS_REGION
      - name: EC2_REGION
        deprecated:
          removed_at_date: '2024-12-01'
          collection_name: amazon.aws
          why: 'EC2 in the name implied it was limited to EC2 resources, when it is used for all connections'
          alternatives: AWS_REGION
"""
