#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---

version_added: 1.0.0
module: cloudfront_origin_access_identity

short_description: Create, update and delete origin access identities for a
                   CloudFront distribution

description:
  - Allows for easy creation, updating and deletion of origin access
    identities.

author:
  - Willem van Ketwich (@wilvk)

options:
    state:
      description: If the named resource should exist.
      choices:
        - present
        - absent
      default: present
      type: str
    origin_access_identity_id:
      description:
        - The origin_access_identity_id of the CloudFront distribution.
      required: false
      type: str
    comment:
      description:
        - A comment to describe the CloudFront origin access identity.
      required: false
      type: str
    caller_reference:
      description:
        - A unique identifier to reference the origin access identity by.
      required: false
      type: str

notes:
  - Does not support check mode.

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""

- name: create an origin access identity
  community.aws.cloudfront_origin_access_identity:
    state: present
    caller_reference: this is an example reference
    comment: this is an example comment

- name: update an existing origin access identity using caller_reference as an identifier
  community.aws.cloudfront_origin_access_identity:
     origin_access_identity_id: E17DRN9XUOAHZX
     caller_reference: this is an example reference
     comment: this is a new comment

- name: delete an existing origin access identity using caller_reference as an identifier
  community.aws.cloudfront_origin_access_identity:
     state: absent
     caller_reference: this is an example reference
     comment: this is a new comment

"""

RETURN = r"""
cloud_front_origin_access_identity:
  description: The origin access identity's information.
  returned: always
  type: complex
  contains:
    cloud_front_origin_access_identity_config:
      description: describes a url specifying the origin access identity.
      returned: always
      type: complex
      contains:
        caller_reference:
          description: a caller reference for the oai
          returned: always
          type: str
        comment:
          description: a comment describing the oai
          returned: always
          type: str
    id:
      description: a unique identifier of the oai
      returned: always
      type: str
    s3_canonical_user_id:
      description: the canonical user ID of the user who created the oai
      returned: always
      type: str
e_tag:
  description: The current version of the origin access identity created.
  returned: always
  type: str
location:
  description: The fully qualified URI of the new origin access identity just created.
  returned: when initially created
  type: str

"""

import datetime

try:
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError
except ImportError:
    pass  # caught by imported AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.cloudfront_facts import CloudFrontFactsServiceManager

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


class CloudFrontOriginAccessIdentityServiceManager(object):
    """
    Handles CloudFront origin access identity service calls to aws
    """

    def __init__(self, module):
        self.module = module
        self.client = module.client("cloudfront")

    def create_origin_access_identity(self, caller_reference, comment):
        try:
            return self.client.create_cloud_front_origin_access_identity(
                CloudFrontOriginAccessIdentityConfig={"CallerReference": caller_reference, "Comment": comment}
            )
        except (ClientError, BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error creating cloud front origin access identity.")

    def delete_origin_access_identity(self, origin_access_identity_id, e_tag):
        try:
            result = self.client.delete_cloud_front_origin_access_identity(Id=origin_access_identity_id, IfMatch=e_tag)
            return result, True
        except (ClientError, BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error deleting Origin Access Identity.")

    def update_origin_access_identity(self, caller_reference, comment, origin_access_identity_id, e_tag):
        changed = False
        new_config = {"CallerReference": caller_reference, "Comment": comment}

        try:
            current_config = self.client.get_cloud_front_origin_access_identity_config(Id=origin_access_identity_id)[
                "CloudFrontOriginAccessIdentityConfig"
            ]
        except (ClientError, BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error getting Origin Access Identity config.")

        if new_config != current_config:
            changed = True

        try:
            # If the CallerReference is a value already sent in a previous identity request
            # the returned value is that of the original request
            result = self.client.update_cloud_front_origin_access_identity(
                CloudFrontOriginAccessIdentityConfig=new_config,
                Id=origin_access_identity_id,
                IfMatch=e_tag,
            )
        except (ClientError, BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error updating Origin Access Identity.")

        return result, changed


class CloudFrontOriginAccessIdentityValidationManager(object):
    """
    Manages CloudFront Origin Access Identities
    """

    def __init__(self, module):
        self.module = module
        self.__cloudfront_facts_mgr = CloudFrontFactsServiceManager(module)

    def describe_origin_access_identity(self, origin_access_identity_id, fail_if_missing=True):
        try:
            return self.__cloudfront_facts_mgr.get_origin_access_identity(
                id=origin_access_identity_id, fail_if_error=False
            )
        except is_boto3_error_code("NoSuchCloudFrontOriginAccessIdentity") as e:  # pylint: disable=duplicate-except
            if fail_if_missing:
                self.module.fail_json_aws(e, msg="Error getting etag from origin_access_identity.")
            return {}
        except (ClientError, BotoCoreError) as e:  # pylint: disable=duplicate-except
            self.module.fail_json_aws(e, msg="Error getting etag from origin_access_identity.")

    def validate_etag_from_origin_access_identity_id(self, origin_access_identity_id, fail_if_missing):
        oai = self.describe_origin_access_identity(origin_access_identity_id, fail_if_missing)
        if oai is not None:
            return oai.get("ETag")

    def validate_origin_access_identity_id_from_caller_reference(self, caller_reference):
        origin_access_identities = self.__cloudfront_facts_mgr.list_origin_access_identities()
        origin_origin_access_identity_ids = [oai.get("Id") for oai in origin_access_identities]
        for origin_access_identity_id in origin_origin_access_identity_ids:
            oai_config = self.__cloudfront_facts_mgr.get_origin_access_identity_config(id=origin_access_identity_id)
            temp_caller_reference = oai_config.get("CloudFrontOriginAccessIdentityConfig").get("CallerReference")
            if temp_caller_reference == caller_reference:
                return origin_access_identity_id

    def validate_comment(self, comment):
        if comment is None:
            return "origin access identity created by Ansible with datetime " + datetime.datetime.now().strftime(
                "%Y-%m-%dT%H:%M:%S.%f"
            )
        return comment

    def validate_caller_reference_from_origin_access_identity_id(self, origin_access_identity_id, caller_reference):
        if caller_reference is None:
            if origin_access_identity_id is None:
                return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
            oai = self.describe_origin_access_identity(origin_access_identity_id, fail_if_missing=True)
            origin_access_config = oai.get("CloudFrontOriginAccessIdentity", {}).get(
                "CloudFrontOriginAccessIdentityConfig", {}
            )
            return origin_access_config.get("CallerReference")
        return caller_reference


def main():
    argument_spec = dict(
        state=dict(choices=["present", "absent"], default="present"),
        origin_access_identity_id=dict(),
        caller_reference=dict(),
        comment=dict(),
    )

    result = {}
    e_tag = None
    changed = False

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=False)
    service_mgr = CloudFrontOriginAccessIdentityServiceManager(module)
    validation_mgr = CloudFrontOriginAccessIdentityValidationManager(module)

    state = module.params.get("state")
    caller_reference = module.params.get("caller_reference")

    comment = module.params.get("comment")
    origin_access_identity_id = module.params.get("origin_access_identity_id")

    if origin_access_identity_id is None and caller_reference is not None:
        origin_access_identity_id = validation_mgr.validate_origin_access_identity_id_from_caller_reference(
            caller_reference
        )

    if state == "present":
        comment = validation_mgr.validate_comment(comment)
        caller_reference = validation_mgr.validate_caller_reference_from_origin_access_identity_id(
            origin_access_identity_id, caller_reference
        )
        if origin_access_identity_id is not None:
            e_tag = validation_mgr.validate_etag_from_origin_access_identity_id(origin_access_identity_id, True)
            # update cloudfront origin access identity
            result, changed = service_mgr.update_origin_access_identity(
                caller_reference, comment, origin_access_identity_id, e_tag
            )
        else:
            # create cloudfront origin access identity
            result = service_mgr.create_origin_access_identity(caller_reference, comment)
            changed = True
    else:
        e_tag = validation_mgr.validate_etag_from_origin_access_identity_id(origin_access_identity_id, False)
        if e_tag:
            result, changed = service_mgr.delete_origin_access_identity(origin_access_identity_id, e_tag)

    result.pop("ResponseMetadata", None)

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(result))


if __name__ == "__main__":
    main()
