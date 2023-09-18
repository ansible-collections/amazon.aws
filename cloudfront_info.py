#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
---
module: cloudfront_info
version_added: 1.0.0
short_description: Obtain facts about an AWS CloudFront distribution
description:
  - Gets information about an AWS CloudFront distribution.
  - This module was called C(cloudfront_facts) before Ansible 2.9, returning C(ansible_facts).
    Note that the M(community.aws.cloudfront_info) module no longer returns C(ansible_facts)!
requirements:
  - boto3 >= 1.0.0
  - python >= 2.6
author: Willem van Ketwich (@wilvk)
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
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Get a summary of distributions
  community.aws.cloudfront_info:
    summary: true
  register: result

- name: Get information about a distribution
  community.aws.cloudfront_info:
    distribution: true
    distribution_id: my-cloudfront-distribution-id
  register: result_did
- ansible.builtin.debug:
    msg: "{{ result_did['cloudfront']['my-cloudfront-distribution-id'] }}"

- name: Get information about a distribution using the CNAME of the cloudfront distribution.
  community.aws.cloudfront_info:
    distribution: true
    domain_name_alias: www.my-website.com
  register: result_website
- ansible.builtin.debug:
    msg: "{{ result_website['cloudfront']['www.my-website.com'] }}"

# When the module is called as cloudfront_facts, return values are published
# in ansible_facts['cloudfront'][<id>] and can be used as follows.
# Note that this is deprecated and will stop working in Ansible 2.13.
- name: Gather facts
  community.aws.cloudfront_facts:
    distribution: true
    distribution_id: my-cloudfront-distribution-id
- ansible.builtin.debug:
    msg: "{{ ansible_facts['cloudfront']['my-cloudfront-distribution-id'] }}"

- community.aws.cloudfront_facts:
    distribution: true
    domain_name_alias: www.my-website.com
- ansible.builtin.debug:
    msg: "{{ ansible_facts['cloudfront']['www.my-website.com'] }}"

- name: Get all information about an invalidation for a distribution.
  community.aws.cloudfront_info:
    invalidation: true
    distribution_id: my-cloudfront-distribution-id
    invalidation_id: my-cloudfront-invalidation-id

- name: Get all information about a CloudFront origin access identity.
  community.aws.cloudfront_info:
    origin_access_identity: true
    origin_access_identity_id: my-cloudfront-origin-access-identity-id

- name: Get all information about lists not requiring parameters (ie. list_origin_access_identities, list_distributions, list_streaming_distributions)
  community.aws.cloudfront_info:
    origin_access_identity: true
    origin_access_identity_id: my-cloudfront-origin-access-identity-id

- name: Get all information about lists not requiring parameters (ie. list_origin_access_identities, list_distributions, list_streaming_distributions)
  community.aws.cloudfront_info:
    all_lists: true
'''

RETURN = '''
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
'''

from functools import partial
import traceback

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict


class CloudFrontServiceManager:
    """Handles CloudFront Services"""

    def __init__(self, module):
        self.module = module

        try:
            self.client = module.client('cloudfront')
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg='Failed to connect to AWS')

    def get_distribution(self, distribution_id):
        try:
            func = partial(self.client.get_distribution, Id=distribution_id)
            return self.paginated_response(func)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error describing distribution")

    def get_distribution_config(self, distribution_id):
        try:
            func = partial(self.client.get_distribution_config, Id=distribution_id)
            return self.paginated_response(func)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error describing distribution configuration")

    def get_origin_access_identity(self, origin_access_identity_id):
        try:
            func = partial(self.client.get_cloud_front_origin_access_identity, Id=origin_access_identity_id)
            return self.paginated_response(func)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error describing origin access identity")

    def get_origin_access_identity_config(self, origin_access_identity_id):
        try:
            func = partial(self.client.get_cloud_front_origin_access_identity_config, Id=origin_access_identity_id)
            return self.paginated_response(func)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error describing origin access identity configuration")

    def get_invalidation(self, distribution_id, invalidation_id):
        try:
            func = partial(self.client.get_invalidation, DistributionId=distribution_id, Id=invalidation_id)
            return self.paginated_response(func)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error describing invalidation")

    def get_streaming_distribution(self, distribution_id):
        try:
            func = partial(self.client.get_streaming_distribution, Id=distribution_id)
            return self.paginated_response(func)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error describing streaming distribution")

    def get_streaming_distribution_config(self, distribution_id):
        try:
            func = partial(self.client.get_streaming_distribution_config, Id=distribution_id)
            return self.paginated_response(func)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error describing streaming distribution")

    def list_origin_access_identities(self):
        try:
            func = partial(self.client.list_cloud_front_origin_access_identities)
            origin_access_identity_list = self.paginated_response(func, 'CloudFrontOriginAccessIdentityList')
            if origin_access_identity_list['Quantity'] > 0:
                return origin_access_identity_list['Items']
            return {}
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error listing cloud front origin access identities")

    def list_distributions(self, keyed=True):
        try:
            func = partial(self.client.list_distributions)
            distribution_list = self.paginated_response(func, 'DistributionList')
            if distribution_list['Quantity'] == 0:
                return {}
            else:
                distribution_list = distribution_list['Items']
            if not keyed:
                return distribution_list
            return self.keyed_list_helper(distribution_list)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error listing distributions")

    def list_distributions_by_web_acl_id(self, web_acl_id):
        try:
            func = partial(self.client.list_distributions_by_web_acl_id, WebAclId=web_acl_id)
            distribution_list = self.paginated_response(func, 'DistributionList')
            if distribution_list['Quantity'] == 0:
                return {}
            else:
                distribution_list = distribution_list['Items']
            return self.keyed_list_helper(distribution_list)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error listing distributions by web acl id")

    def list_invalidations(self, distribution_id):
        try:
            func = partial(self.client.list_invalidations, DistributionId=distribution_id)
            invalidation_list = self.paginated_response(func, 'InvalidationList')
            if invalidation_list['Quantity'] > 0:
                return invalidation_list['Items']
            return {}
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error listing invalidations")

    def list_streaming_distributions(self, keyed=True):
        try:
            func = partial(self.client.list_streaming_distributions)
            streaming_distribution_list = self.paginated_response(func, 'StreamingDistributionList')
            if streaming_distribution_list['Quantity'] == 0:
                return {}
            else:
                streaming_distribution_list = streaming_distribution_list['Items']
            if not keyed:
                return streaming_distribution_list
            return self.keyed_list_helper(streaming_distribution_list)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error listing streaming distributions")

    def summary(self):
        summary_dict = {}
        summary_dict.update(self.summary_get_distribution_list(False))
        summary_dict.update(self.summary_get_distribution_list(True))
        summary_dict.update(self.summary_get_origin_access_identity_list())
        return summary_dict

    def summary_get_origin_access_identity_list(self):
        try:
            origin_access_identity_list = {'origin_access_identities': []}
            origin_access_identities = self.list_origin_access_identities()
            for origin_access_identity in origin_access_identities:
                oai_id = origin_access_identity['Id']
                oai_full_response = self.get_origin_access_identity(oai_id)
                oai_summary = {'Id': oai_id, 'ETag': oai_full_response['ETag']}
                origin_access_identity_list['origin_access_identities'].append(oai_summary)
            return origin_access_identity_list
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error generating summary of origin access identities")

    def summary_get_distribution_list(self, streaming=False):
        try:
            list_name = 'streaming_distributions' if streaming else 'distributions'
            key_list = ['Id', 'ARN', 'Status', 'LastModifiedTime', 'DomainName', 'Comment', 'PriceClass', 'Enabled']
            distribution_list = {list_name: []}
            distributions = self.list_streaming_distributions(False) if streaming else self.list_distributions(False)
            for dist in distributions:
                temp_distribution = {}
                for key_name in key_list:
                    temp_distribution[key_name] = dist[key_name]
                temp_distribution['Aliases'] = [alias for alias in dist['Aliases'].get('Items', [])]
                temp_distribution['ETag'] = self.get_etag_from_distribution_id(dist['Id'], streaming)
                if not streaming:
                    temp_distribution['WebACLId'] = dist['WebACLId']
                    invalidation_ids = self.get_list_of_invalidation_ids_from_distribution_id(dist['Id'])
                    if invalidation_ids:
                        temp_distribution['Invalidations'] = invalidation_ids
                resource_tags = self.client.list_tags_for_resource(Resource=dist['ARN'])
                temp_distribution['Tags'] = boto3_tag_list_to_ansible_dict(resource_tags['Tags'].get('Items', []))
                distribution_list[list_name].append(temp_distribution)
            return distribution_list
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error generating summary of distributions")
        except Exception as e:
            self.module.fail_json(msg="Error generating summary of distributions - " + str(e),
                                  exception=traceback.format_exc())

    def get_etag_from_distribution_id(self, distribution_id, streaming):
        distribution = {}
        if not streaming:
            distribution = self.get_distribution(distribution_id)
        else:
            distribution = self.get_streaming_distribution(distribution_id)
        return distribution['ETag']

    def get_list_of_invalidation_ids_from_distribution_id(self, distribution_id):
        try:
            invalidation_ids = []
            invalidations = self.list_invalidations(distribution_id)
            for invalidation in invalidations:
                invalidation_ids.append(invalidation['Id'])
            return invalidation_ids
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error getting list of invalidation ids")

    def get_distribution_id_from_domain_name(self, domain_name):
        try:
            distribution_id = ""
            distributions = self.list_distributions(False)
            distributions += self.list_streaming_distributions(False)
            for dist in distributions:
                if 'Items' in dist['Aliases']:
                    for alias in dist['Aliases']['Items']:
                        if str(alias).lower() == domain_name.lower():
                            distribution_id = dist['Id']
                            break
            return distribution_id
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error getting distribution id from domain name")

    def get_aliases_from_distribution_id(self, distribution_id):
        aliases = []
        try:
            distributions = self.list_distributions(False)
            for dist in distributions:
                if dist['Id'] == distribution_id and 'Items' in dist['Aliases']:
                    for alias in dist['Aliases']['Items']:
                        aliases.append(alias)
                    break
            return aliases
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error getting list of aliases from distribution_id")

    def paginated_response(self, func, result_key=""):
        '''
        Returns expanded response for paginated operations.
        The 'result_key' is used to define the concatenated results that are combined from each paginated response.
        '''
        args = dict()
        results = dict()
        loop = True
        while loop:
            response = func(**args)
            if result_key == "":
                result = response
                result.pop('ResponseMetadata', None)
            else:
                result = response.get(result_key)
            results.update(result)
            args['Marker'] = response.get('NextMarker')
            for key in response.keys():
                if key.endswith('List'):
                    args['Marker'] = response[key].get('NextMarker')
                    break
            loop = args['Marker'] is not None
        return results

    def keyed_list_helper(self, list_to_key):
        keyed_list = dict()
        for item in list_to_key:
            distribution_id = item['Id']
            if 'Items' in item['Aliases']:
                aliases = item['Aliases']['Items']
                for alias in aliases:
                    keyed_list.update({alias: item})
            keyed_list.update({distribution_id: item})
        return keyed_list


def set_facts_for_distribution_id_and_alias(details, facts, distribution_id, aliases):
    facts[distribution_id].update(details)
    # also have a fixed key for accessing results/details returned
    facts['result'] = details
    facts['result']['DistributionId'] = distribution_id

    for alias in aliases:
        facts[alias].update(details)
    return facts


def main():
    argument_spec = dict(
        distribution_id=dict(required=False, type='str'),
        invalidation_id=dict(required=False, type='str'),
        origin_access_identity_id=dict(required=False, type='str'),
        domain_name_alias=dict(required=False, type='str'),
        all_lists=dict(required=False, default=False, type='bool'),
        distribution=dict(required=False, default=False, type='bool'),
        distribution_config=dict(required=False, default=False, type='bool'),
        origin_access_identity=dict(required=False, default=False, type='bool'),
        origin_access_identity_config=dict(required=False, default=False, type='bool'),
        invalidation=dict(required=False, default=False, type='bool'),
        streaming_distribution=dict(required=False, default=False, type='bool'),
        streaming_distribution_config=dict(required=False, default=False, type='bool'),
        list_origin_access_identities=dict(required=False, default=False, type='bool'),
        list_distributions=dict(required=False, default=False, type='bool'),
        list_distributions_by_web_acl_id=dict(required=False, default=False, type='bool'),
        list_invalidations=dict(required=False, default=False, type='bool'),
        list_streaming_distributions=dict(required=False, default=False, type='bool'),
        summary=dict(required=False, default=False, type='bool'),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=False)
    is_old_facts = module._name == 'cloudfront_facts'
    if is_old_facts:
        module.deprecate("The 'cloudfront_facts' module has been renamed to 'cloudfront_info', "
                         "and the renamed one no longer returns ansible_facts", date='2021-12-01', collection_name='community.aws')

    service_mgr = CloudFrontServiceManager(module)

    distribution_id = module.params.get('distribution_id')
    invalidation_id = module.params.get('invalidation_id')
    origin_access_identity_id = module.params.get('origin_access_identity_id')
    web_acl_id = module.params.get('web_acl_id')
    domain_name_alias = module.params.get('domain_name_alias')
    all_lists = module.params.get('all_lists')
    distribution = module.params.get('distribution')
    distribution_config = module.params.get('distribution_config')
    origin_access_identity = module.params.get('origin_access_identity')
    origin_access_identity_config = module.params.get('origin_access_identity_config')
    invalidation = module.params.get('invalidation')
    streaming_distribution = module.params.get('streaming_distribution')
    streaming_distribution_config = module.params.get('streaming_distribution_config')
    list_origin_access_identities = module.params.get('list_origin_access_identities')
    list_distributions = module.params.get('list_distributions')
    list_distributions_by_web_acl_id = module.params.get('list_distributions_by_web_acl_id')
    list_invalidations = module.params.get('list_invalidations')
    list_streaming_distributions = module.params.get('list_streaming_distributions')
    summary = module.params.get('summary')

    aliases = []
    result = {'cloudfront': {}}
    facts = {}

    require_distribution_id = (distribution or distribution_config or invalidation or streaming_distribution or
                               streaming_distribution_config or list_invalidations)

    # set default to summary if no option specified
    summary = summary or not (distribution or distribution_config or origin_access_identity or
                              origin_access_identity_config or invalidation or streaming_distribution or streaming_distribution_config or
                              list_origin_access_identities or list_distributions_by_web_acl_id or list_invalidations or
                              list_streaming_distributions or list_distributions)

    # validations
    if require_distribution_id and distribution_id is None and domain_name_alias is None:
        module.fail_json(msg='Error distribution_id or domain_name_alias have not been specified.')
    if (invalidation and invalidation_id is None):
        module.fail_json(msg='Error invalidation_id has not been specified.')
    if (origin_access_identity or origin_access_identity_config) and origin_access_identity_id is None:
        module.fail_json(msg='Error origin_access_identity_id has not been specified.')
    if list_distributions_by_web_acl_id and web_acl_id is None:
        module.fail_json(msg='Error web_acl_id has not been specified.')

    # get distribution id from domain name alias
    if require_distribution_id and distribution_id is None:
        distribution_id = service_mgr.get_distribution_id_from_domain_name(domain_name_alias)
        if not distribution_id:
            module.fail_json(msg='Error unable to source a distribution id from domain_name_alias')

    # set appropriate cloudfront id
    if distribution_id and not list_invalidations:
        facts = {distribution_id: {}}
        aliases = service_mgr.get_aliases_from_distribution_id(distribution_id)
        for alias in aliases:
            facts.update({alias: {}})
        if invalidation_id:
            facts.update({invalidation_id: {}})
    elif distribution_id and list_invalidations:
        facts = {distribution_id: {}}
        aliases = service_mgr.get_aliases_from_distribution_id(distribution_id)
        for alias in aliases:
            facts.update({alias: {}})
    elif origin_access_identity_id:
        facts = {origin_access_identity_id: {}}
    elif web_acl_id:
        facts = {web_acl_id: {}}

    # get details based on options
    if distribution:
        facts_to_set = service_mgr.get_distribution(distribution_id)
    if distribution_config:
        facts_to_set = service_mgr.get_distribution_config(distribution_id)
    if origin_access_identity:
        facts[origin_access_identity_id].update(service_mgr.get_origin_access_identity(origin_access_identity_id))
    if origin_access_identity_config:
        facts[origin_access_identity_id].update(service_mgr.get_origin_access_identity_config(origin_access_identity_id))
    if invalidation:
        facts_to_set = service_mgr.get_invalidation(distribution_id, invalidation_id)
        facts[invalidation_id].update(facts_to_set)
    if streaming_distribution:
        facts_to_set = service_mgr.get_streaming_distribution(distribution_id)
    if streaming_distribution_config:
        facts_to_set = service_mgr.get_streaming_distribution_config(distribution_id)
    if list_invalidations:
        facts_to_set = {'invalidations': service_mgr.list_invalidations(distribution_id)}
    if 'facts_to_set' in vars():
        facts = set_facts_for_distribution_id_and_alias(facts_to_set, facts, distribution_id, aliases)

    # get list based on options
    if all_lists or list_origin_access_identities:
        facts['origin_access_identities'] = service_mgr.list_origin_access_identities()
    if all_lists or list_distributions:
        facts['distributions'] = service_mgr.list_distributions()
    if all_lists or list_streaming_distributions:
        facts['streaming_distributions'] = service_mgr.list_streaming_distributions()
    if list_distributions_by_web_acl_id:
        facts['distributions_by_web_acl_id'] = service_mgr.list_distributions_by_web_acl_id(web_acl_id)
    if list_invalidations:
        facts['invalidations'] = service_mgr.list_invalidations(distribution_id)

    # default summary option
    if summary:
        facts['summary'] = service_mgr.summary()

    result['changed'] = False
    result['cloudfront'].update(facts)
    if is_old_facts:
        module.exit_json(msg="Retrieved CloudFront facts.", ansible_facts=result)
    else:
        module.exit_json(msg="Retrieved CloudFront info.", **result)


if __name__ == '__main__':
    main()
