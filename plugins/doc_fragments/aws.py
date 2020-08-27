# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Will Thames <will@thames.id.au>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # AWS only documentation fragment
    DOCUMENTATION = r'''
options:
  debug_botocore_endpoint_logs:
    description:
      - Use a botocore.endpoint logger to parse the unique (rather than total) "resource:action" API calls made during a task, outputing
        the set to the resource_actions key in the task results. Use the aws_resource_action callback to output to total list made during
        a playbook. The ANSIBLE_DEBUG_BOTOCORE_LOGS environment variable may also be used.
    type: bool
    default: 'no'
  ec2_url:
    description:
      - Url to use to connect to EC2 or your Eucalyptus cloud (by default the module will use EC2 endpoints).
        Ignored for modules where region is required. Must be specified for all other modules if region is not used.
        If not set then the value of the EC2_URL environment variable, if any, is used.
    type: str
    aliases: [ aws_endpoint_url, endpoint_url ]
  aws_secret_key:
    description:
      - AWS secret key. If not set then the value of the AWS_SECRET_ACCESS_KEY, AWS_SECRET_KEY, or EC2_SECRET_KEY environment variable is used.
      - If I(profile) is set this parameter is ignored.
      - Passing the I(aws_secret_key) and I(profile) options at the same time has been deprecated
        and the options will be made mutually exclusive after 2022-06-01.
    type: str
    aliases: [ ec2_secret_key, secret_key ]
  aws_access_key:
    description:
      - AWS access key. If not set then the value of the AWS_ACCESS_KEY_ID, AWS_ACCESS_KEY or EC2_ACCESS_KEY environment variable is used.
      - If I(profile) is set this parameter is ignored.
      - Passing the I(aws_access_key) and I(profile) options at the same time has been deprecated
        and the options will be made mutually exclusive after 2022-06-01.
    type: str
    aliases: [ ec2_access_key, access_key ]
  security_token:
    description:
      - AWS STS security token. If not set then the value of the AWS_SECURITY_TOKEN or EC2_SECURITY_TOKEN environment variable is used.
      - If I(profile) is set this parameter is ignored.
      - Passing the I(security_token) and I(profile) options at the same time has been deprecated
        and the options will be made mutually exclusive after 2022-06-01.
    type: str
    aliases: [ aws_security_token, access_token ]
  aws_ca_bundle:
    description:
      - "The location of a CA Bundle to use when validating SSL certificates."
      - "Only used for boto3 based modules."
      - "Note: The CA Bundle is read 'module' side and may need to be explicitly copied from the controller if not run locally."
    type: path
  validate_certs:
    description:
      - When set to "no", SSL certificates will not be validated for boto versions >= 2.6.0.
    type: bool
    default: yes
  profile:
    description:
      - Uses a boto profile. Only works with boto >= 2.24.0.
      - Using I(profile) will override I(aws_access_key), I(aws_secret_key) and I(security_token)
        and support for passing them at the same time as I(profile) has been deprecated.
      - I(aws_access_key), I(aws_secret_key) and I(security_token) will be made mutually exclusive with I(profile) after 2022-06-01.
    type: str
    aliases: [ aws_profile ]
  aws_config:
    description:
      - A dictionary to modify the botocore configuration.
      - Parameters can be found at U(https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html#botocore.config.Config).
      - Only the 'user_agent' key is used for boto modules. See U(http://boto.cloudhackers.com/en/latest/boto_config_tut.html#boto) for more boto configuration.
    type: dict
requirements:
  - python >= 2.6
  - boto
notes:
  - If parameters are not set within the module, the following
    environment variables can be used in decreasing order of precedence
    C(AWS_URL) or C(EC2_URL),
    C(AWS_PROFILE) or C(AWS_DEFAULT_PROFILE),
    C(AWS_ACCESS_KEY_ID) or C(AWS_ACCESS_KEY) or C(EC2_ACCESS_KEY),
    C(AWS_SECRET_ACCESS_KEY) or C(AWS_SECRET_KEY) or C(EC2_SECRET_KEY),
    C(AWS_SECURITY_TOKEN) or C(EC2_SECURITY_TOKEN),
    C(AWS_REGION) or C(EC2_REGION),
    C(AWS_CA_BUNDLE)
  - Ansible uses the boto configuration file (typically ~/.boto) if no
    credentials are provided. See https://boto.readthedocs.io/en/latest/boto_config_tut.html
  - C(AWS_REGION) or C(EC2_REGION) can be typically be used to specify the
    AWS region, when required, but this can also be configured in the boto config file
'''
