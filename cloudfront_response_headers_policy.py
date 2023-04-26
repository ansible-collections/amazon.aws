#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
version_added: 3.2.0
module: cloudfront_response_headers_policy

short_description: Create, update and delete response headers policies to be used in a Cloudfront distribution

description:
  - Create, update and delete response headers policies to be used in a Cloudfront distribution for inserting custom headers
  - See docs at U(https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudfront.html#CloudFront.Client.create_response_headers_policy)

author:
  - Stefan Horning (@stefanhorning)

options:
    state:
      description: Decides if the named policy should be absent or present
      choices:
        - present
        - absent
      default: present
      type: str
    name:
      description: Name of the policy
      required: true
      type: str
    comment:
      description: Description of the policy
      required: false
      type: str
    cors_config:
      description: CORS header config block
      required: false
      default: {}
      type: dict
    security_headers_config:
      description: Security headers config block. For headers suchs as XSS-Protection, Content-Security-Policy or Strict-Transport-Security
      required: false
      default: {}
      type: dict
    custom_headers_config:
      description: Custom headers config block. Define your own list of headers and values as a list
      required: false
      default: {}
      type: dict

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Creationg a Cloudfront header policy using all predefined header features and a custom header for demonstration
  community.aws.cloudfront_response_headers_policy:
    name: my-header-policy
    comment: My header policy for all the headers
    cors_config:
      access_control_allow_origins:
        items:
          - 'https://foo.com/bar'
          - 'https://bar.com/foo'
      access_control_allow_headers:
        items:
          - 'X-Session-Id'
      access_control_allow_methods:
        items:
          - GET
          - OPTIONS
          - HEAD
      access_control_allow_credentials: true
      access_control_expose_headers:
        items:
          - 'X-Session-Id'
      access_control_max_age_sec: 1800
      origin_override: true
    security_headers_config:
      xss_protection:
        protection: true
        report_uri: 'https://my.report-uri.com/foo/bar'
        override: true
      frame_options:
        frame_option: 'SAMEORIGIN'
        override: true
      referrer_policy:
        referrer_policy: 'same-origin'
        override: true
      content_security_policy:
        content_security_policy: "frame-ancestors 'none'; report-uri https://my.report-uri.com/r/d/csp/enforce;"
        override: true
      content_type_options:
        override: true
      strict_transport_security:
        include_subdomains: true
        preload: true
        access_control_max_age_sec: 63072000
        override: true
    custom_headers_config:
      items:
        - { header: 'X-Test-Header', value: 'Foo', override: true }
    state: present

- name: Delete header policy
  community.aws.cloudfront_response_headers_policy:
    name: my-header-policy
    state: absent
"""

RETURN = r"""
response_headers_policy:
    description: The policy's information
    returned: success
    type: complex
    contains:
      id:
        description: ID of the policy
        returned: always
        type: str
        sample: '10a45b52-630e-4b7c-77c6-205f06df0462'
      last_modified_time:
        description: Timestamp of last modification of policy
        returned: always
        type: str
        sample: '2022-02-04T13:23:27.304000+00:00'
      response_headers_policy_config:
        description: The response headers config dict containing all the headers configured
        returned: always
        type: complex
        contains:
          name:
            description: Name of the policy
            type: str
            returned: always
            sample: my-header-policy
"""

import datetime

try:
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
except ImportError:
    pass  # caught by imported AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


class CloudfrontResponseHeadersPolicyService(object):
    def __init__(self, module):
        self.module = module
        self.client = module.client("cloudfront")
        self.check_mode = module.check_mode

    def find_response_headers_policy(self, name):
        try:
            policies = self.client.list_response_headers_policies()["ResponseHeadersPolicyList"]["Items"]

            for policy in policies:
                if policy["ResponseHeadersPolicy"]["ResponseHeadersPolicyConfig"]["Name"] == name:
                    policy_id = policy["ResponseHeadersPolicy"]["Id"]
                    # as the list_ request does not contain the Etag (which we need), we need to do another get_ request here
                    matching_policy = self.client.get_response_headers_policy(Id=policy["ResponseHeadersPolicy"]["Id"])
                    break
                else:
                    matching_policy = None

            return matching_policy
        except (ClientError, BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error fetching policy information")

    def create_response_header_policy(self, name, comment, cors_config, security_headers_config, custom_headers_config):
        cors_config = snake_dict_to_camel_dict(cors_config, capitalize_first=True)
        security_headers_config = snake_dict_to_camel_dict(security_headers_config, capitalize_first=True)

        # Little helper for turning xss_protection into XSSProtection and not into XssProtection
        if "XssProtection" in security_headers_config:
            security_headers_config["XSSProtection"] = security_headers_config.pop("XssProtection")

        custom_headers_config = snake_dict_to_camel_dict(custom_headers_config, capitalize_first=True)

        config = {
            "Name": name,
            "Comment": comment,
            "CorsConfig": self.insert_quantities(cors_config),
            "SecurityHeadersConfig": security_headers_config,
            "CustomHeadersConfig": self.insert_quantities(custom_headers_config),
        }

        config = {k: v for k, v in config.items() if v}

        matching_policy = self.find_response_headers_policy(name)

        changed = False

        if self.check_mode:
            self.module.exit_json(changed=True, response_headers_policy=camel_dict_to_snake_dict(config))

        if matching_policy is None:
            try:
                result = self.client.create_response_headers_policy(ResponseHeadersPolicyConfig=config)
                changed = True
            except (ClientError, BotoCoreError) as e:
                self.module.fail_json_aws(e, msg="Error creating policy")
        else:
            policy_id = matching_policy["ResponseHeadersPolicy"]["Id"]
            etag = matching_policy["ETag"]
            try:
                result = self.client.update_response_headers_policy(
                    Id=policy_id, IfMatch=etag, ResponseHeadersPolicyConfig=config
                )

                changed_time = result["ResponseHeadersPolicy"]["LastModifiedTime"]
                seconds = 3  # threshhold for returned timestamp age
                seconds_ago = datetime.datetime.now(changed_time.tzinfo) - datetime.timedelta(0, seconds)

                # consider change made by this execution of the module if returned timestamp was very recent
                if changed_time > seconds_ago:
                    changed = True
            except (ClientError, BotoCoreError) as e:
                self.module.fail_json_aws(e, msg="Updating creating policy")

        self.module.exit_json(changed=changed, **camel_dict_to_snake_dict(result))

    def delete_response_header_policy(self, name):
        matching_policy = self.find_response_headers_policy(name)

        if matching_policy is None:
            self.module.exit_json(msg="Didn't find a matching policy by that name, not deleting")
        else:
            policy_id = matching_policy["ResponseHeadersPolicy"]["Id"]
            etag = matching_policy["ETag"]
            if self.check_mode:
                result = {}
            else:
                try:
                    result = self.client.delete_response_headers_policy(Id=policy_id, IfMatch=etag)
                except (ClientError, BotoCoreError) as e:
                    self.module.fail_json_aws(e, msg="Error deleting policy")

            self.module.exit_json(changed=True, **camel_dict_to_snake_dict(result))

    # Inserts a Quantity field into dicts with a list ('Items')
    @staticmethod
    def insert_quantities(dict_with_items):
        # Items on top level case
        if "Items" in dict_with_items and isinstance(dict_with_items["Items"], list):
            dict_with_items["Quantity"] = len(dict_with_items["Items"])

        # Items on second level case
        for k, v in dict_with_items.items():
            if isinstance(v, dict) and "Items" in v:
                v["Quantity"] = len(v["Items"])

        return dict_with_items


def main():
    argument_spec = dict(
        name=dict(required=True, type="str"),
        comment=dict(type="str"),
        cors_config=dict(type="dict", default=dict()),
        security_headers_config=dict(type="dict", default=dict()),
        custom_headers_config=dict(type="dict", default=dict()),
        state=dict(choices=["present", "absent"], type="str", default="present"),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    name = module.params.get("name")
    comment = module.params.get("comment", "")
    cors_config = module.params.get("cors_config")
    security_headers_config = module.params.get("security_headers_config")
    custom_headers_config = module.params.get("custom_headers_config")
    state = module.params.get("state")

    service = CloudfrontResponseHeadersPolicyService(module)

    if state == "absent":
        service.delete_response_header_policy(name)
    else:
        service.create_response_header_policy(
            name, comment, cors_config, security_headers_config, custom_headers_config
        )


if __name__ == "__main__":
    main()
