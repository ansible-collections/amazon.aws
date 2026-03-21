# -*- coding: utf-8 -*-

# (c) 2016 James Turner <turnerjsm@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
name: aws_service_ip_ranges
author:
  - James Turner (!UNKNOWN) <turnerjsm@gmail.com>
requirements:
  - must have public internet connectivity
short_description: Look up the IP ranges for services provided in AWS such as EC2 and S3
description:
  - AWS publishes IP ranges used on the public internet by EC2, S3, CloudFront, CodeBuild, Route53, and Route53 Health Checking.
  - This module produces a list of all the ranges (by default) or can narrow down the list to the specified region or service.
options:
  service:
    description:
      - The service to filter ranges by.
      - Options include V(EC2), V(S3), V(CLOUDFRONT), V(CODEBUILD), V(ROUTE53), V(ROUTE53_HEALTHCHECKS).
  region:
    description:
      - The AWS region to narrow the ranges to. Examples include V(us-east-1), V(eu-west-2), V(ap-southeast-1).
  ipv6_prefixes:
    description:
      - When O(ipv6_prefixes=true) the lookup will return ipv6 addresses instead of ipv4 addresses.
    version_added: 2.1.0
"""

EXAMPLES = r"""
vars:
  ec2_ranges: "{{ lookup('aws_service_ip_ranges', region='ap-southeast-2', service='EC2', wantlist=True) }}"
tasks:
  - name: "use list return option and iterate as a loop"
    ansible.builtin.debug: msg="{% for cidr in ec2_ranges %}{{ cidr }} {% endfor %}"
  # "52.62.0.0/15 52.64.0.0/17 52.64.128.0/17 52.65.0.0/16 52.95.241.0/24 52.95.255.16/28 54.66.0.0/16 "

  - name: "Pull S3 IP ranges, and print the default return style"
    ansible.builtin.debug: msg="{{ lookup('aws_service_ip_ranges', region='us-east-1', service='S3') }}"
  # "52.92.16.0/20,52.216.0.0/15,54.231.0.0/17"
"""

RETURN = r"""
_raw:
  description: Comma-separated list of CIDR ranges.
"""

import json

import ansible.module_utils.six.moves.urllib.error
import ansible.module_utils.urls
from ansible.errors import AnsibleLookupError
from ansible.module_utils._text import to_native
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):
    def _determine_prefix_labels(self, use_ipv6):
        """
        Determine the JSON field names for IP prefix data.

        Args:
            use_ipv6: Boolean indicating whether to use IPv6 prefixes

        Returns:
            Tuple of (prefixes_label, ip_prefix_label)
        """
        if use_ipv6:
            return ("ipv6_prefixes", "ipv6_prefix")
        else:
            return ("prefixes", "ip_prefix")

    def _fetch_ip_ranges(self, prefixes_label):
        """
        Fetch and parse IP ranges from AWS.

        Args:
            prefixes_label: The JSON field name to extract from the response

        Returns:
            List of IP range dictionaries from AWS

        Raises:
            AnsibleLookupError: If fetching or parsing fails
        """
        try:
            resp = ansible.module_utils.urls.open_url("https://ip-ranges.amazonaws.com/ip-ranges.json")
            amazon_response = json.load(resp)[prefixes_label]
        except getattr(json.decoder, "JSONDecodeError", ValueError) as e:
            # on Python 3+, json.decoder.JSONDecodeError is raised for bad
            # JSON. On 2.x it's a ValueError
            raise AnsibleLookupError(f"Could not decode AWS IP ranges: {to_native(e)}")
        except ansible.module_utils.six.moves.urllib.error.HTTPError as e:
            raise AnsibleLookupError(f"Received HTTP error while pulling IP ranges: {to_native(e)}")
        except ansible.module_utils.urls.SSLValidationError as e:
            raise AnsibleLookupError(f"Error validating the server's certificate for: {to_native(e)}")
        except ansible.module_utils.six.moves.urllib.error.URLError as e:
            raise AnsibleLookupError(f"Failed look up IP range service: {to_native(e)}")
        except ansible.module_utils.urls.ConnectionError as e:
            raise AnsibleLookupError(f"Error connecting to IP range service: {to_native(e)}")
        return amazon_response

    def _filter_by_region(self, ip_ranges, region):
        """
        Filter IP ranges by AWS region.

        Args:
            ip_ranges: Iterator or list of IP range dictionaries
            region: AWS region string to filter by

        Returns:
            Generator of IP ranges matching the region
        """
        return (item for item in ip_ranges if item["region"] == region)

    def _filter_by_service(self, ip_ranges, service):
        """
        Filter IP ranges by AWS service.

        Args:
            ip_ranges: Iterator or list of IP range dictionaries
            service: AWS service name to filter by (case-insensitive)

        Returns:
            Generator of IP ranges matching the service
        """
        service_upper = str.upper(service)
        return (item for item in ip_ranges if item["service"] == service_upper)

    def _extract_ip_addresses(self, ip_ranges, ip_prefix_label):
        """
        Extract IP address strings from IP range dictionaries.

        Args:
            ip_ranges: Iterator or list of IP range dictionaries
            ip_prefix_label: The field name containing the IP prefix

        Returns:
            List of IP address/CIDR strings
        """
        return [item[ip_prefix_label] for item in ip_ranges]

    def run(self, terms, variables, **kwargs):
        prefixes_label, ip_prefix_label = self._determine_prefix_labels(kwargs.get("ipv6_prefixes", False))

        amazon_response = self._fetch_ip_ranges(prefixes_label)

        if "region" in kwargs:
            amazon_response = self._filter_by_region(amazon_response, kwargs["region"])
        if "service" in kwargs:
            amazon_response = self._filter_by_service(amazon_response, kwargs["service"])

        iprange = self._extract_ip_addresses(amazon_response, ip_prefix_label)
        return iprange
