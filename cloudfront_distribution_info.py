#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: cloudfront_distribution_info
version_added: 1.0.0
short_description: Obtain facts about an AWS CloudFront distribution
description:
  - Gets information about an AWS CloudFront distribution.
  - Prior to release 5.0.0 this module was called C(community.aws.cloudfront_info).
    The usage did not change.
author:
  - Willem van Ketwich (@wilvk)
options:
    distribution_id:
        description:
          - The id of the CloudFront distribution. Used with I(distribution), I(distribution_config),
            I(invalidation), I(streaming_distribution), I(streaming_distribution_config), I(list_invalidations).
        required: false
        type: str
    invalidation_id:
        description:
          - The id of the invalidation to get information about.
          - Used with I(invalidation).
        required: false
        type: str
    origin_access_identity_id:
        description:
          - The id of the CloudFront origin access identity to get information about.
        required: false
        type: str
#    web_acl_id:
#        description:
#          - Used with I(list_distributions_by_web_acl_id).
#        required: false
#        type: str
    domain_name_alias:
        description:
          - Can be used instead of I(distribution_id) - uses the aliased CNAME for the CloudFront
            distribution to get the distribution id where required.
        required: false
        type: str
    all_lists:
        description:
          - Get all CloudFront lists that do not require parameters.
        required: false
        default: false
        type: bool
    origin_access_identity:
        description:
          - Get information about an origin access identity.
          - Requires I(origin_access_identity_id) to be specified.
        required: false
        default: false
        type: bool
    origin_access_identity_config:
        description:
          - Get the configuration information about an origin access identity.
          - Requires I(origin_access_identity_id) to be specified.
        required: false
        default: false
        type: bool
    distribution:
        description:
          - Get information about a distribution.
          - Requires I(distribution_id) or I(domain_name_alias) to be specified.
        required: false
        default: false
        type: bool
    distribution_config:
        description:
          - Get the configuration information about a distribution.
          - Requires I(distribution_id) or I(domain_name_alias) to be specified.
        required: false
        default: false
        type: bool
    invalidation:
        description:
          - Get information about an invalidation.
          - Requires I(invalidation_id) to be specified.
        required: false
        default: false
        type: bool
    streaming_distribution:
        description:
          - Get information about a specified RTMP distribution.
          - Requires I(distribution_id) or I(domain_name_alias) to be specified.
        required: false
        default: false
        type: bool
    streaming_distribution_config:
        description:
          - Get the configuration information about a specified RTMP distribution.
          - Requires I(distribution_id) or I(domain_name_alias) to be specified.
        required: false
        default: false
        type: bool
    list_origin_access_identities:
        description:
          - Get a list of CloudFront origin access identities.
          - Requires I(origin_access_identity_id) to be set.
        required: false
        default: false
        type: bool
    list_distributions:
        description:
          - Get a list of CloudFront distributions.
        required: false
        default: false
        type: bool
    list_distributions_by_web_acl_id:
        description:
          - Get a list of distributions using web acl id as a filter.
          - Requires I(web_acl_id) to be set.
        required: false
        default: false
        type: bool
    list_invalidations:
        description:
          - Get a list of invalidations.
          - Requires I(distribution_id) or I(domain_name_alias) to be specified.
        required: false
        default: false
        type: bool
    list_streaming_distributions:
        description:
          - Get a list of streaming distributions.
        required: false
        default: false
        type: bool
    summary:
        description:
          - Returns a summary of all distributions, streaming distributions and origin_access_identities.
          - This is the default behaviour if no option is selected.
        required: false
        default: false
        type: bool

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Get a summary of distributions
  community.aws.cloudfront_distribution_info:
    summary: true
  register: result

- name: Get information about a distribution
  community.aws.cloudfront_distribution_info:
    distribution: true
    distribution_id: my-cloudfront-distribution-id
  register: result_did
- ansible.builtin.debug:
    msg: "{{ result_did['cloudfront']['my-cloudfront-distribution-id'] }}"

- name: Get information about a distribution using the CNAME of the cloudfront distribution.
  community.aws.cloudfront_distribution_info:
    distribution: true
    domain_name_alias: www.my-website.com
  register: result_website
- ansible.builtin.debug:
    msg: "{{ result_website['cloudfront']['www.my-website.com'] }}"

- name: Get all information about an invalidation for a distribution.
  community.aws.cloudfront_distribution_info:
    invalidation: true
    distribution_id: my-cloudfront-distribution-id
    invalidation_id: my-cloudfront-invalidation-id

- name: Get all information about a CloudFront origin access identity.
  community.aws.cloudfront_distribution_info:
    origin_access_identity: true
    origin_access_identity_id: my-cloudfront-origin-access-identity-id

- name: Get all information about lists not requiring parameters (ie. list_origin_access_identities, list_distributions, list_streaming_distributions)
  community.aws.cloudfront_distribution_info:
    origin_access_identity: true
    origin_access_identity_id: my-cloudfront-origin-access-identity-id

- name: Get all information about lists not requiring parameters (ie. list_origin_access_identities, list_distributions, list_streaming_distributions)
  community.aws.cloudfront_distribution_info:
    all_lists: true
"""

RETURN = r"""
origin_access_identity:
    description: Describes the origin access identity information. Requires I(origin_access_identity_id) to be set.
    returned: only if I(origin_access_identity) is true
    type: dict
origin_access_identity_configuration:
    description: Describes the origin access identity information configuration information. Requires I(origin_access_identity_id) to be set.
    returned: only if I(origin_access_identity_configuration) is true
    type: dict
distribution:
    description: >
      Facts about a CloudFront distribution. Requires I(distribution_id) or I(domain_name_alias)
      to be specified. Requires I(origin_access_identity_id) to be set.
    returned: only if distribution is true
    type: dict
distribution_config:
    description: >
      Facts about a CloudFront distribution's config. Requires I(distribution_id) or I(domain_name_alias)
      to be specified.
    returned: only if I(distribution_config) is true
    type: dict
invalidation:
    description: >
      Describes the invalidation information for the distribution. Requires
      I(invalidation_id) to be specified and either I(distribution_id) or I(domain_name_alias.)
    returned: only if invalidation is true
    type: dict
streaming_distribution:
    description: >
      Describes the streaming information for the distribution. Requires
      I(distribution_id) or I(domain_name_alias) to be specified.
    returned: only if I(streaming_distribution) is true
    type: dict
streaming_distribution_config:
    description: >
      Describes the streaming configuration information for the distribution.
      Requires I(distribution_id) or I(domain_name_alias) to be specified.
    returned: only if I(streaming_distribution_config) is true
    type: dict
summary:
    description: Gives a summary of distributions, streaming distributions and origin access identities.
    returned: as default or if summary is true
    type: dict
result:
    description: >
        Result dict not nested under the CloudFront ID to access results of module without the knowledge of that id
        as figuring out the DistributionId is usually the reason one uses this module in the first place.
    returned: always
    type: dict
"""

from ansible_collections.amazon.aws.plugins.module_utils.cloudfront_facts import CloudFrontFactsServiceManager

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule


def set_facts_for_distribution_id_and_alias(details, facts, distribution_id, aliases):
    facts[distribution_id] = details
    # also have a fixed key for accessing results/details returned
    facts["result"] = details
    facts["result"]["DistributionId"] = distribution_id

    for alias in aliases:
        facts[alias] = details
    return facts


def main():
    argument_spec = dict(
        distribution_id=dict(required=False, type="str"),
        invalidation_id=dict(required=False, type="str"),
        origin_access_identity_id=dict(required=False, type="str"),
        domain_name_alias=dict(required=False, type="str"),
        all_lists=dict(required=False, default=False, type="bool"),
        distribution=dict(required=False, default=False, type="bool"),
        distribution_config=dict(required=False, default=False, type="bool"),
        origin_access_identity=dict(required=False, default=False, type="bool"),
        origin_access_identity_config=dict(required=False, default=False, type="bool"),
        invalidation=dict(required=False, default=False, type="bool"),
        streaming_distribution=dict(required=False, default=False, type="bool"),
        streaming_distribution_config=dict(required=False, default=False, type="bool"),
        list_origin_access_identities=dict(required=False, default=False, type="bool"),
        list_distributions=dict(required=False, default=False, type="bool"),
        list_distributions_by_web_acl_id=dict(required=False, default=False, type="bool"),
        list_invalidations=dict(required=False, default=False, type="bool"),
        list_streaming_distributions=dict(required=False, default=False, type="bool"),
        summary=dict(required=False, default=False, type="bool"),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    service_mgr = CloudFrontFactsServiceManager(module)

    distribution_id = module.params.get("distribution_id")
    invalidation_id = module.params.get("invalidation_id")
    origin_access_identity_id = module.params.get("origin_access_identity_id")
    web_acl_id = module.params.get("web_acl_id")
    domain_name_alias = module.params.get("domain_name_alias")
    all_lists = module.params.get("all_lists")
    distribution = module.params.get("distribution")
    distribution_config = module.params.get("distribution_config")
    origin_access_identity = module.params.get("origin_access_identity")
    origin_access_identity_config = module.params.get("origin_access_identity_config")
    invalidation = module.params.get("invalidation")
    streaming_distribution = module.params.get("streaming_distribution")
    streaming_distribution_config = module.params.get("streaming_distribution_config")
    list_origin_access_identities = module.params.get("list_origin_access_identities")
    list_distributions = module.params.get("list_distributions")
    list_distributions_by_web_acl_id = module.params.get("list_distributions_by_web_acl_id")
    list_invalidations = module.params.get("list_invalidations")
    list_streaming_distributions = module.params.get("list_streaming_distributions")
    summary = module.params.get("summary")

    aliases = []
    result = {"cloudfront": {}}
    facts = {}

    require_distribution_id = (
        distribution
        or distribution_config
        or invalidation
        or streaming_distribution
        or streaming_distribution_config
        or list_invalidations
    )

    # set default to summary if no option specified
    summary = summary or not (
        distribution
        or distribution_config
        or origin_access_identity
        or origin_access_identity_config
        or invalidation
        or streaming_distribution
        or streaming_distribution_config
        or list_origin_access_identities
        or list_distributions_by_web_acl_id
        or list_invalidations
        or list_streaming_distributions
        or list_distributions
    )

    # validations
    if require_distribution_id and distribution_id is None and domain_name_alias is None:
        module.fail_json(msg="Error distribution_id or domain_name_alias have not been specified.")
    if invalidation and invalidation_id is None:
        module.fail_json(msg="Error invalidation_id has not been specified.")
    if (origin_access_identity or origin_access_identity_config) and origin_access_identity_id is None:
        module.fail_json(msg="Error origin_access_identity_id has not been specified.")
    if list_distributions_by_web_acl_id and web_acl_id is None:
        module.fail_json(msg="Error web_acl_id has not been specified.")

    # get distribution id from domain name alias
    if require_distribution_id and distribution_id is None:
        distribution_id = service_mgr.get_distribution_id_from_domain_name(domain_name_alias)
        if not distribution_id:
            module.fail_json(msg="Error unable to source a distribution id from domain_name_alias")

    # set appropriate cloudfront id
    if invalidation_id is not None and invalidation:
        facts.update({invalidation_id: {}})
    if origin_access_identity_id and (origin_access_identity or origin_access_identity_config):
        facts.update({origin_access_identity_id: {}})
    if web_acl_id:
        facts.update({web_acl_id: {}})

    # get details based on options
    if distribution:
        facts_to_set = service_mgr.get_distribution(id=distribution_id)
    if distribution_config:
        facts_to_set = service_mgr.get_distribution_config(id=distribution_id)
    if origin_access_identity:
        facts[origin_access_identity_id].update(service_mgr.get_origin_access_identity(id=origin_access_identity_id))
    if origin_access_identity_config:
        facts[origin_access_identity_id].update(
            service_mgr.get_origin_access_identity_config(id=origin_access_identity_id)
        )
    if invalidation:
        facts_to_set = service_mgr.get_invalidation(distribution_id=distribution_id, id=invalidation_id)
        facts[invalidation_id].update(facts_to_set)
    if streaming_distribution:
        facts_to_set = service_mgr.get_streaming_distribution(id=distribution_id)
    if streaming_distribution_config:
        facts_to_set = service_mgr.get_streaming_distribution_config(id=distribution_id)
    if list_invalidations:
        invalidations = service_mgr.list_invalidations(distribution_id=distribution_id) or {}
        facts_to_set = {"invalidations": invalidations}
    if "facts_to_set" in vars():
        aliases = service_mgr.get_aliases_from_distribution_id(distribution_id)
        facts = set_facts_for_distribution_id_and_alias(facts_to_set, facts, distribution_id, aliases)

    # get list based on options
    if all_lists or list_origin_access_identities:
        facts["origin_access_identities"] = service_mgr.list_origin_access_identities() or {}
    if all_lists or list_distributions:
        facts["distributions"] = service_mgr.list_distributions() or {}
    if all_lists or list_streaming_distributions:
        facts["streaming_distributions"] = service_mgr.list_streaming_distributions() or {}
    if list_distributions_by_web_acl_id:
        facts["distributions_by_web_acl_id"] = service_mgr.list_distributions_by_web_acl_id(web_acl_id=web_acl_id) or {}
    if list_invalidations:
        facts["invalidations"] = service_mgr.list_invalidations(distribution_id=distribution_id) or {}

    # default summary option
    if summary:
        facts["summary"] = service_mgr.summary()

    result["changed"] = False
    result["cloudfront"].update(facts)

    module.exit_json(msg="Retrieved CloudFront info.", **result)


if __name__ == "__main__":
    main()
