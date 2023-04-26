#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: accessanalyzer_validate_policy_info
version_added: 5.0.0
short_description: Performs validation of IAM policies
description:
  - Requests the validation of a policy and returns a list of findings.
options:
  policy:
    description:
      - A properly json formatted policy.
    type: json
    aliases: ['policy_document']
    required: true
  locale:
    description:
      - The locale to use for localizing the findings.
      - Supported locales include C(DE), C(EN), C(ES), C(FR), C(IT), C(JA), C(KO), C(PT_BR),
        C(ZH_CN) and C(ZH_TW).
      - For more information about supported locales see the AWS Documentation
        C(https://docs.aws.amazon.com/access-analyzer/latest/APIReference/API_ValidatePolicy.html)
    type: str
    required: false
    default: 'EN'
  policy_type:
    description:
      - The type of policy to validate.
      - C(identity) policies grant permissions to IAM principals, including both managed and inline
        policies for IAM roles, users, and groups.
      - C(resource) policies policies grant permissions on AWS resources, including trust policies
        for IAM roles and bucket policies for S3 buckets.
    type: str
    choices: ['identity', 'resource', 'service_control']
    default: 'identity'
    required: false
  resource_type:
    description:
      - The type of resource to attach to your resource policy.
      - Ignored unless I(policy_type=resource).
      - Supported resource types include C(AWS::S3::Bucket), C(AWS::S3::AccessPoint),
        C(AWS::S3::MultiRegionAccessPoint) and C(AWS::S3ObjectLambda::AccessPoint)
      - For resource types not supported as valid values, IAM Access Analyzer runs policy checks
        that apply to all resource policies.
      - For more information about supported locales see the AWS Documentation
        C(https://docs.aws.amazon.com/access-analyzer/latest/APIReference/API_ValidatePolicy.html)
    type: str
    required: false
  results_filter:
    description:
      - Filter the findings and limit them to specific finding types.
    type: list
    elements: str
    choices: ['error', 'security', 'suggestion', 'warning']
    required: false
author:
  - Mark Chappell (@tremble)
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Validate a policy
- name: Validate a simple IAM policy
  community.aws.accessanalyzer_validate_policy_info:
    policy: "{{ lookup('template', 'managed_policy.json.j2') }}"
"""

RETURN = r"""
findings:
  description: The list of findings in a policy returned by IAM Access Analyzer based on its suite of policy checks.
  returned: success
  type: list
  elements: dict
  contains:
    finding_details:
      description:
        - A localized message describing the finding.
      type: str
      returned: success
      sample: 'Resource ARN does not match the expected ARN format. Update the resource portion of the ARN.'
    finding_type:
      description:
        - The severity of the finding.
      type: str
      returned: success
      sample: 'ERROR'
    issue_code:
      description:
        - An identifier for the type of issue found.
      type: str
      returned: success
      sample: 'INVALID_ARN_RESOURCE'
    learn_more_link:
      description:
        - A link to additional information about the finding type.
      type: str
      returned: success
      sample: 'https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-reference-policy-checks.html'
    locations:
      description:
        - The location of the item resulting in the recommendations.
      type: list
      returned: success
      elements: dict
      contains:
        path:
          description: A path in a policy, represented as a sequence of path elements.
          type: list
          elements: dict
          returned: success
          sample: [{"value": "Statement"}, {"index": 0}, {"value": "Resource"}, {"index": 0}]
        span:
          description:
            - Where in the policy the finding refers to.
            - Note - when using lookups or passing dictionaries to I(policy) the policy string may be
              converted to a single line of JSON, changing th column, line and offset values.
          type: dict
          contains:
            start:
              description: The start position of the span.
              type: dict
              returned: success
              contains:
                column:
                  description: The column of the position, starting from C(0).
                  type: int
                  returned: success
                line:
                  description: The line of the position, starting from C(1).
                  type: int
                  returned: success
                offset:
                  description: The offset within the policy that corresponds to the position, starting from C(0).
                  type: int
                  returned: success
            end:
              description: The end position of the span.
              type: dict
              returned: success
              contains:
                column:
                  description: The column of the position, starting from C(0).
                  type: int
                  returned: success
                line:
                  description: The line of the position, starting from C(1).
                  type: int
                  returned: success
                offset:
                  description: The offset within the policy that corresponds to the position, starting from C(0).
                  type: int
                  returned: success
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def filter_findings(findings, type_filter):
    if not type_filter:
        return findings

    # Convert type_filter to the findingType strings returned by the API
    filter_map = dict(error="ERROR", security="SECURITY_WARNING", suggestion="SUGGESTION", warning="WARNING")
    allowed_types = [filter_map[t] for t in type_filter]

    filtered_results = [f for f in findings if f.get("findingType", None) in allowed_types]
    return filtered_results


def main():
    # Botocore only supports specific values for locale and resource_type, however the supported
    # values are likely to be expanded, let's avoid hard coding limits which might not hold true in
    # the long term...
    argument_spec = dict(
        policy=dict(required=True, type="json", aliases=["policy_document"]),
        locale=dict(required=False, type="str", default="EN"),
        policy_type=dict(
            required=False, type="str", default="identity", choices=["identity", "resource", "service_control"]
        ),
        resource_type=dict(required=False, type="str"),
        results_filter=dict(
            required=False, type="list", elements="str", choices=["error", "security", "suggestion", "warning"]
        ),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    policy_type_map = dict(
        identity="IDENTITY_POLICY", resource="RESOURCE_POLICY", service_control="SERVICE_CONTROL_POLICY"
    )

    policy = module.params.get("policy")
    policy_type = policy_type_map[module.params.get("policy_type")]
    locale = module.params.get("locale").upper()
    resource_type = module.params.get("resource_type")
    results_filter = module.params.get("results_filter")

    try:
        client = module.client("accessanalyzer", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    params = dict(locale=locale, policyDocument=policy, policyType=policy_type)
    if policy_type == "RESOURCE_POLICY" and resource_type:
        params["policyType"] = resource_type

    results = client.validate_policy(aws_retry=True, **params)

    findings = filter_findings(results.get("findings", []), results_filter)
    results["findings"] = findings

    results = camel_dict_to_snake_dict(results)

    module.exit_json(changed=False, **results)


if __name__ == "__main__":
    main()
