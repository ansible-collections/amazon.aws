# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
name: aws_account_attribute
author:
  - Sloane Hertel (@s-hertel) <shertel@redhat.com>
extends_documentation_fragment:
- amazon.aws.aws_boto3
- amazon.aws.aws_credentials
- amazon.aws.aws_region

short_description: Look up AWS account attributes.
description:
  - Describes attributes of your AWS account. You can specify one of the listed
    attribute choices or omit it to see all attributes.
options:
  attribute:
    description: The attribute for which to get the value(s).
    choices:
      - supported-platforms
      - default-vpc
      - max-instances
      - vpc-max-security-groups-per-interface
      - max-elastic-ips
      - vpc-max-elastic-ips
      - has-ec2-classic
'''

EXAMPLES = """
vars:
  has_ec2_classic: "{{ lookup('aws_account_attribute', attribute='has-ec2-classic') }}"
  # true | false

  default_vpc_id: "{{ lookup('aws_account_attribute', attribute='default-vpc') }}"
  # vpc-xxxxxxxx | none

  account_details: "{{ lookup('aws_account_attribute', wantlist='true') }}"
  # {'default-vpc': ['vpc-xxxxxxxx'], 'max-elastic-ips': ['5'], 'max-instances': ['20'],
  #  'supported-platforms': ['VPC', 'EC2'], 'vpc-max-elastic-ips': ['5'], 'vpc-max-security-groups-per-interface': ['5']}

"""

RETURN = """
_raw:
  description:
    Returns a boolean when I(attribute) is check_ec2_classic. Otherwise returns the value(s) of the attribute
    (or all attributes if one is not specified).
"""

try:
    import botocore
except ImportError:
    pass  # will be captured by imported HAS_BOTO3

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.plugin_utils.modules import AWSLookupModule


class LookupModule(AWSLookupModule):
    name = 'aws_account_attribute'

    @AWSLookupModule.aws_error_handler('describe account attributes')
    @AWSRetry.jittered_backoff(retries=10)
    def _describe_account_attributes(self, client, **params):
        return client.describe_account_attributes(**params)

    def run(self, terms, variables, **kwargs):
        super(LookupModule, self).run(terms, variables, **kwargs)
        client = self.client('ec2')

        attribute = kwargs.get('attribute')
        params = {'AttributeNames': []}
        check_ec2_classic = False
        if 'has-ec2-classic' == attribute:
            check_ec2_classic = True
            params['AttributeNames'] = ['supported-platforms']
        elif attribute:
            params['AttributeNames'] = [attribute]

        response = self._describe_account_attributes(client, **params)['AccountAttributes']

        if check_ec2_classic:
            attr = response[0]
            return any(value['AttributeValue'] == 'EC2' for value in attr['AttributeValues'])

        if attribute:
            attr = response[0]
            return [value['AttributeValue'] for value in attr['AttributeValues']]

        flattened = {}
        for k_v_dict in response:
            flattened[k_v_dict['AttributeName']] = [value['AttributeValue'] for value in k_v_dict['AttributeValues']]
        return flattened
