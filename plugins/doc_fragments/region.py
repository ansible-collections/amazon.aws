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
      - The C(AWS_REGION) environment variable may also be used.
      - See the Amazon AWS documentation for more information
        U(http://docs.aws.amazon.com/general/latest/gr/rande.html#ec2_region).
    type: str
    aliases: [ aws_region ]
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
    aliases: [ aws_region ]
    env:
      - name: AWS_REGION
"""
