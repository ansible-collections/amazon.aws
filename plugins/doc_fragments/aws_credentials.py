# -*- coding: utf-8 -*-

# Copyright: (c) 2017,  Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#
# The amazon.aws.aws_credentials docs fragment has been deprecated,
# please migrate to amazon.aws.common.plugins.
#


class ModuleDocFragment:
    # Plugin options for AWS credentials
    DOCUMENTATION = r"""
options:
  aws_profile:
    description: The AWS profile
    type: str
    aliases: [ boto_profile ]
    env:
      - name: AWS_DEFAULT_PROFILE
      - name: AWS_PROFILE
  aws_access_key:
    description: The AWS access key to use.
    type: str
    aliases: [ aws_access_key_id ]
    env:
      - name: EC2_ACCESS_KEY
        deprecated:
          removed_at_date: '2024-12-01'
          collection_name: amazon.aws
          why: 'EC2 in the name implied it was limited to EC2 resources.  However, it is used for all connections.'
          alternatives: AWS_ACCESS_KEY_ID
      - name: AWS_ACCESS_KEY
      - name: AWS_ACCESS_KEY_ID
  aws_secret_key:
    description: The AWS secret key that corresponds to the access key.
    type: str
    aliases: [ aws_secret_access_key ]
    env:
      - name: EC2_SECRET_KEY
        deprecated:
          removed_at_date: '2024-12-01'
          collection_name: amazon.aws
          why: 'EC2 in the name implied it was limited to EC2 resources.  However, it is used for all connections.'
          alternatives: AWS_SECRET_ACCESS_KEY
      - name: AWS_SECRET_KEY
      - name: AWS_SECRET_ACCESS_KEY
  aws_security_token:
    description: The AWS security token if using temporary access and secret keys.
    type: str
    env:
      - name: EC2_SECURITY_TOKEN
        deprecated:
          removed_at_date: '2024-12-01'
          collection_name: amazon.aws
          why: 'EC2 in the name implied it was limited to EC2 resources.  However, it is used for all connections.'
          alternatives: AWS_SESSION_TOKEN
      - name: AWS_SESSION_TOKEN
      - name: AWS_SECURITY_TOKEN
        deprecated:
          removed_at_date: '2024-12-01'
          collection_name: amazon.aws
          why: 'AWS_SECURITY_TOKEN was used for compatibility with the original boto SDK, support for which has been dropped'
          alternatives: AWS_SESSION_TOKEN
"""
