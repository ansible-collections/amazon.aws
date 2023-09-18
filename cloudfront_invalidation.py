#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---

version_added: 1.0.0
module: cloudfront_invalidation

short_description: create invalidations for AWS CloudFront distributions
description:
  - Allows for invalidation of a batch of paths for a CloudFront distribution.

author:
  - Willem van Ketwich (@wilvk)

options:
    distribution_id:
      description:
        - The ID of the CloudFront distribution to invalidate paths for. Can be specified instead of the alias.
      required: false
      type: str
    alias:
      description:
        - The alias of the CloudFront distribution to invalidate paths for. Can be specified instead of distribution_id.
      required: false
      type: str
    caller_reference:
      description:
        - A unique reference identifier for the invalidation paths.
        - Defaults to current datetime stamp.
      required: false
      default:
      type: str
    target_paths:
      description:
        - A list of paths on the distribution to invalidate. Each path should begin with C(/). Wildcards are allowed. eg. C(/foo/bar/*)
      required: true
      type: list
      elements: str

notes:
  - does not support check mode

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""

- name: create a batch of invalidations using a distribution_id for a reference
  community.aws.cloudfront_invalidation:
    distribution_id: E15BU8SDCGSG57
    caller_reference: testing 123
    target_paths:
      - /testpathone/test1.css
      - /testpathtwo/test2.js
      - /testpaththree/test3.ss

- name: create a batch of invalidations using an alias as a reference and one path using a wildcard match
  community.aws.cloudfront_invalidation:
    alias: alias.test.com
    caller_reference: testing 123
    target_paths:
      - /testpathone/test4.css
      - /testpathtwo/test5.js
      - /testpaththree/*

"""

RETURN = r"""
invalidation:
  description: The invalidation's information.
  returned: always
  type: complex
  contains:
    create_time:
      description: The date and time the invalidation request was first made.
      returned: always
      type: str
      sample: '2018-02-01T15:50:41.159000+00:00'
    id:
      description: The identifier for the invalidation request.
      returned: always
      type: str
      sample: I2G9MOWJZFV612
    invalidation_batch:
      description: The current invalidation information for the batch request.
      returned: always
      type: complex
      contains:
        caller_reference:
          description: The value used to uniquely identify an invalidation request.
          returned: always
          type: str
          sample: testing 123
        paths:
          description: A dict that contains information about the objects that you want to invalidate.
          returned: always
          type: complex
          contains:
            items:
              description: A list of the paths that you want to invalidate.
              returned: always
              type: list
              sample:
              - /testpathtwo/test2.js
              - /testpathone/test1.css
              - /testpaththree/test3.ss
            quantity:
              description: The number of objects that you want to invalidate.
              returned: always
              type: int
              sample: 3
    status:
      description: The status of the invalidation request.
      returned: always
      type: str
      sample: Completed
location:
  description: The fully qualified URI of the distribution and invalidation batch request.
  returned: always
  type: str
  sample: https://cloudfront.amazonaws.com/2017-03-25/distribution/E1ZID6KZJECZY7/invalidation/I2G9MOWJZFV622
"""

import datetime

try:
    import botocore
except ImportError:
    pass  # caught by imported AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_message
from ansible_collections.amazon.aws.plugins.module_utils.cloudfront_facts import CloudFrontFactsServiceManager

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


class CloudFrontInvalidationServiceManager(object):
    """
    Handles CloudFront service calls to AWS for invalidations
    """

    def __init__(self, module, cloudfront_facts_mgr):
        self.module = module
        self.client = module.client("cloudfront")
        self.__cloudfront_facts_mgr = cloudfront_facts_mgr

    def create_invalidation(self, distribution_id, invalidation_batch):
        current_invalidation_response = self.get_invalidation(distribution_id, invalidation_batch["CallerReference"])
        try:
            response = self.client.create_invalidation(
                DistributionId=distribution_id, InvalidationBatch=invalidation_batch
            )
            response.pop("ResponseMetadata", None)
            if current_invalidation_response:
                return response, False
            else:
                return response, True
        except is_boto3_error_message(
            "Your request contains a caller reference that was used for a previous invalidation "
            "batch for the same distribution."
        ):
            self.module.warn(
                "InvalidationBatch target paths are not modifiable. "
                "To make a new invalidation please update caller_reference."
            )
            return current_invalidation_response, False
        except (
            botocore.exceptions.ClientError,
            botocore.exceptions.BotoCoreError,
        ) as e:  # pylint: disable=duplicate-except
            self.module.fail_json_aws(e, msg="Error creating CloudFront invalidations.")

    def get_invalidation(self, distribution_id, caller_reference):
        # find all invalidations for the distribution
        invalidations = self.__cloudfront_facts_mgr.list_invalidations(distribution_id=distribution_id)

        # check if there is an invalidation with the same caller reference
        for invalidation in invalidations:
            invalidation_info = self.__cloudfront_facts_mgr.get_invalidation(
                distribution_id=distribution_id, id=invalidation["Id"]
            )
            if invalidation_info.get("InvalidationBatch", {}).get("CallerReference") == caller_reference:
                invalidation_info.pop("ResponseMetadata", None)
                return invalidation_info
        return {}


class CloudFrontInvalidationValidationManager(object):
    """
    Manages CloudFront validations for invalidation batches
    """

    def __init__(self, module, cloudfront_facts_mgr):
        self.module = module
        self.__cloudfront_facts_mgr = cloudfront_facts_mgr

    def validate_distribution_id(self, distribution_id, alias):
        try:
            if distribution_id is None and alias is None:
                self.module.fail_json(msg="distribution_id or alias must be specified")
            if distribution_id is None:
                distribution_id = self.__cloudfront_facts_mgr.get_distribution_id_from_domain_name(alias)
            return distribution_id
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error validating parameters.")

    def create_aws_list(self, invalidation_batch):
        aws_list = {}
        aws_list["Quantity"] = len(invalidation_batch)
        aws_list["Items"] = invalidation_batch
        return aws_list

    def validate_invalidation_batch(self, invalidation_batch, caller_reference):
        try:
            if caller_reference is not None:
                valid_caller_reference = caller_reference
            else:
                valid_caller_reference = datetime.datetime.now().isoformat()
            valid_invalidation_batch = {
                "paths": self.create_aws_list(invalidation_batch),
                "caller_reference": valid_caller_reference,
            }
            return valid_invalidation_batch
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error validating invalidation batch.")


def main():
    argument_spec = dict(
        caller_reference=dict(),
        distribution_id=dict(),
        alias=dict(),
        target_paths=dict(required=True, type="list", elements="str"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec, supports_check_mode=False, mutually_exclusive=[["distribution_id", "alias"]]
    )

    cloudfront_facts_mgr = CloudFrontFactsServiceManager(module)
    validation_mgr = CloudFrontInvalidationValidationManager(module, cloudfront_facts_mgr)
    service_mgr = CloudFrontInvalidationServiceManager(module, cloudfront_facts_mgr)

    caller_reference = module.params.get("caller_reference")
    distribution_id = module.params.get("distribution_id")
    alias = module.params.get("alias")
    target_paths = module.params.get("target_paths")

    result = {}

    distribution_id = validation_mgr.validate_distribution_id(distribution_id, alias)
    valid_target_paths = validation_mgr.validate_invalidation_batch(target_paths, caller_reference)
    valid_pascal_target_paths = snake_dict_to_camel_dict(valid_target_paths, True)
    result, changed = service_mgr.create_invalidation(distribution_id, valid_pascal_target_paths)

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(result))


if __name__ == "__main__":
    main()
