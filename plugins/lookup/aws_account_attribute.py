# -*- coding: utf-8 -*-

# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
name: aws_account_attribute
author:
  - Sloane Hertel (@s-hertel) <shertel@redhat.com>
short_description: Look up AWS account attributes
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
extends_documentation_fragment:
  - amazon.aws.boto3
  - amazon.aws.common.plugins
  - amazon.aws.region.plugins
"""

EXAMPLES = r"""
vars:
  has_ec2_classic: "{{ lookup('aws_account_attribute', attribute='has-ec2-classic') }}"
  # true | false

  default_vpc_id: "{{ lookup('aws_account_attribute', attribute='default-vpc') }}"
  # vpc-xxxxxxxx | none

  account_details: "{{ lookup('aws_account_attribute', wantlist='true') }}"
  # {'default-vpc': ['vpc-xxxxxxxx'], 'max-elastic-ips': ['5'], 'max-instances': ['20'],
  #  'supported-platforms': ['VPC', 'EC2'], 'vpc-max-elastic-ips': ['5'], 'vpc-max-security-groups-per-interface': ['5']}
"""

RETURN = r"""
_raw:
  description:
    - Returns a boolean when O(attribute=check_ec2_classic). Otherwise returns the value(s) of the attribute
      (or all attributes if one is not specified).
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AWSLookupBase

from ansible.errors import AnsibleLookupError
from ansible.module_utils._text import to_native

from ansible_collections.amazon.aws.plugins.plugin_utils.lookup import AWSLookupBase


class LookupModule(AWSLookupBase):
    _SERVICE = "ec2"

    def _build_api_params(self, attribute):
        """
        Build API parameters for describe_account_attributes call.

        Args:
            attribute: The attribute name to query, or None for all attributes

        Returns:
            Tuple of (params dict, check_ec2_classic boolean)
        """
        params = {"AttributeNames": []}
        check_ec2_classic = False

        if attribute == "has-ec2-classic":
            check_ec2_classic = True
            params["AttributeNames"] = ["supported-platforms"]
        elif attribute:
            params["AttributeNames"] = [attribute]

        return params, check_ec2_classic

    def _process_response_for_ec2_classic(self, response):
        """
        Process response to check if account has EC2-Classic support.

        Args:
            response: List of account attributes from AWS API

        Returns:
            Boolean indicating if EC2-Classic is supported
        """
        attr = response[0]
        return any(value["AttributeValue"] == "EC2" for value in attr["AttributeValues"])

    def _process_response_for_attribute(self, response):
        """
        Process response to extract values for a specific attribute.

        Args:
            response: List of account attributes from AWS API

        Returns:
            List of attribute values
        """
        attr = response[0]
        return [value["AttributeValue"] for value in attr["AttributeValues"]]

    def _process_response_for_all_attributes(self, response):
        """
        Process response to extract all account attributes as a dictionary.

        Args:
            response: List of account attributes from AWS API

        Returns:
            Dictionary mapping attribute names to lists of values
        """
        flattened = {}
        for k_v_dict in response:
            flattened[k_v_dict["AttributeName"]] = [value["AttributeValue"] for value in k_v_dict["AttributeValues"]]
        return flattened

    def run(self, terms, variables, **kwargs):
        super().run(terms, variables, **kwargs)

        attribute = kwargs.get("attribute")
        params, check_ec2_classic = self._build_api_params(attribute)

        try:
            response = self._describe_account_attributes(**params)["AccountAttributes"]
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            raise AnsibleLookupError(f"Failed to describe account attributes: {to_native(e)}")

        if check_ec2_classic:
            return [self._process_response_for_ec2_classic(response)]

        if attribute:
            return self._process_response_for_attribute(response)

        return [self._process_response_for_all_attributes(response)]

    def _describe_account_attributes(self, **params):
        """Describe EC2 account attributes"""
        return self.aws_client.describe_account_attributes(aws_retry=True, **params)
