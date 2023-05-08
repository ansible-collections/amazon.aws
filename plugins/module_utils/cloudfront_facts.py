# -*- coding: utf-8 -*-

# Copyright (c) 2017 Willem van Ketwich
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Author:
#   - Willem van Ketwich <willem@vanketwich.com.au>
#
# Common functionality to be used by the modules:
#   - cloudfront_distribution
#   - cloudfront_invalidation
#   - cloudfront_origin_access_identity

"""
Common cloudfront facts shared between modules
"""

from functools import partial

try:
    import botocore
except ImportError:
    pass

from .retries import AWSRetry
from .tagging import boto3_tag_list_to_ansible_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict


class CloudFrontFactsServiceManagerFailure(Exception):
    pass


def cloudfront_facts_keyed_list_helper(list_to_key):
    result = dict()
    for item in list_to_key:
        distribution_id = item["Id"]
        if "Items" in item["Aliases"]:
            result.update({alias: item for alias in item["Aliases"]["Items"]})
        result.update({distribution_id: item})
    return result


@AWSRetry.jittered_backoff()
def _cloudfront_paginate_build_full_result(client, client_method, **kwargs):
    paginator = client.get_paginator(client_method)
    return paginator.paginate(**kwargs).build_full_result()


class CloudFrontFactsServiceManager:
    """Handles CloudFront Facts Services"""

    CLOUDFRONT_CLIENT_API_MAPPING = {
        "get_distribution": {
            "error": "Error describing distribution",
        },
        "get_distribution_config": {
            "error": "Error describing distribution configuration",
        },
        "get_origin_access_identity": {
            "error": "Error describing origin access identity",
            "client_api": "get_cloud_front_origin_access_identity",
        },
        "get_origin_access_identity_config": {
            "error": "Error describing origin access identity configuration",
            "client_api": "get_cloud_front_origin_access_identity_config",
        },
        "get_streaming_distribution": {
            "error": "Error describing streaming distribution",
        },
        "get_streaming_distribution_config": {
            "error": "Error describing streaming distribution",
        },
        "get_invalidation": {
            "error": "Error describing invalidation",
        },
        "list_distributions_by_web_acl_id": {
            "error": "Error listing distributions by web acl id",
            "post_process": lambda x: cloudfront_facts_keyed_list_helper(
                x.get("DistributionList", {}).get("Items", [])
            ),
        },
    }

    CLOUDFRONT_CLIENT_PAGINATE_API_MAPPING = {
        "list_origin_access_identities": {
            "error": "Error listing cloud front origin access identities",
            "client_api": "list_cloud_front_origin_access_identities",
            "key": "CloudFrontOriginAccessIdentityList",
        },
        "list_distributions": {
            "error": "Error listing distributions",
            "key": "DistributionList",
            "keyed": True,
        },
        "list_invalidations": {"error": "Error listing invalidations", "key": "InvalidationList"},
        "list_streaming_distributions": {
            "error": "Error listing streaming distributions",
            "key": "StreamingDistributionList",
            "keyed": True,
        },
    }

    def __init__(self, module):
        self.module = module
        self.client = module.client("cloudfront", retry_decorator=AWSRetry.jittered_backoff())

    def describe_cloudfront_property(self, client_method, error, post_process, **kwargs):
        fail_if_error = kwargs.pop("fail_if_error", True)
        try:
            method = getattr(self.client, client_method)
            api_kwargs = snake_dict_to_camel_dict(kwargs, capitalize_first=True)
            result = method(aws_retry=True, **api_kwargs)
            result.pop("ResponseMetadata", None)
            if post_process:
                result = post_process(result)
            return result
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            if not fail_if_error:
                raise
            self.module.fail_json_aws(e, msg=error)

    def paginate_list_cloudfront_property(self, client_method, key, default_keyed, error, **kwargs):
        fail_if_error = kwargs.pop("fail_if_error", True)
        try:
            keyed = kwargs.pop("keyed", default_keyed)
            api_kwargs = snake_dict_to_camel_dict(kwargs, capitalize_first=True)
            result = _cloudfront_paginate_build_full_result(self.client, client_method, **api_kwargs)
            items = result.get(key, {}).get("Items", [])
            if keyed:
                items = cloudfront_facts_keyed_list_helper(items)
            return items
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            if not fail_if_error:
                raise
            self.module.fail_json_aws(e, msg=error)

    def __getattr__(self, name):
        if name in self.CLOUDFRONT_CLIENT_API_MAPPING:
            client_method = self.CLOUDFRONT_CLIENT_API_MAPPING[name].get("client_api", name)
            error = self.CLOUDFRONT_CLIENT_API_MAPPING[name].get("error", "")
            post_process = self.CLOUDFRONT_CLIENT_API_MAPPING[name].get("post_process")
            return partial(self.describe_cloudfront_property, client_method, error, post_process)

        elif name in self.CLOUDFRONT_CLIENT_PAGINATE_API_MAPPING:
            client_method = self.CLOUDFRONT_CLIENT_PAGINATE_API_MAPPING[name].get("client_api", name)
            error = self.CLOUDFRONT_CLIENT_PAGINATE_API_MAPPING[name].get("error", "")
            key = self.CLOUDFRONT_CLIENT_PAGINATE_API_MAPPING[name].get("key")
            keyed = self.CLOUDFRONT_CLIENT_PAGINATE_API_MAPPING[name].get("keyed", False)
            return partial(self.paginate_list_cloudfront_property, client_method, key, keyed, error)

        raise CloudFrontFactsServiceManagerFailure(f"Method {name} is not currently supported")

    def summary(self):
        summary_dict = {}
        summary_dict.update(self.summary_get_distribution_list(False))
        summary_dict.update(self.summary_get_distribution_list(True))
        summary_dict.update(self.summary_get_origin_access_identity_list())
        return summary_dict

    def summary_get_origin_access_identity_list(self):
        try:
            origin_access_identities = []
            for origin_access_identity in self.list_origin_access_identities():
                oai_id = origin_access_identity["Id"]
                oai_full_response = self.get_origin_access_identity(oai_id)
                oai_summary = {"Id": oai_id, "ETag": oai_full_response["ETag"]}
                origin_access_identities.append(oai_summary)
            return {"origin_access_identities": origin_access_identities}
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Error generating summary of origin access identities")

    def list_resource_tags(self, resource_arn):
        return self.client.list_tags_for_resource(Resource=resource_arn, aws_retry=True)

    def summary_get_distribution_list(self, streaming=False):
        try:
            list_name = "streaming_distributions" if streaming else "distributions"
            key_list = ["Id", "ARN", "Status", "LastModifiedTime", "DomainName", "Comment", "PriceClass", "Enabled"]
            distribution_list = {list_name: []}
            distributions = (
                self.list_streaming_distributions(keyed=False) if streaming else self.list_distributions(keyed=False)
            )
            for dist in distributions:
                temp_distribution = {k: dist[k] for k in key_list}
                temp_distribution["Aliases"] = list(dist["Aliases"].get("Items", []))
                temp_distribution["ETag"] = self.get_etag_from_distribution_id(dist["Id"], streaming)
                if not streaming:
                    temp_distribution["WebACLId"] = dist["WebACLId"]
                    invalidation_ids = self.get_list_of_invalidation_ids_from_distribution_id(dist["Id"])
                    if invalidation_ids:
                        temp_distribution["Invalidations"] = invalidation_ids
                resource_tags = self.list_resource_tags(dist["ARN"])
                temp_distribution["Tags"] = boto3_tag_list_to_ansible_dict(resource_tags["Tags"].get("Items", []))
                distribution_list[list_name].append(temp_distribution)
            return distribution_list
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Error generating summary of distributions")

    def get_etag_from_distribution_id(self, distribution_id, streaming):
        distribution = {}
        if not streaming:
            distribution = self.get_distribution(id=distribution_id)
        else:
            distribution = self.get_streaming_distribution(id=distribution_id)
        return distribution["ETag"]

    def get_list_of_invalidation_ids_from_distribution_id(self, distribution_id):
        try:
            return list(map(lambda x: x["Id"], self.list_invalidations(distribution_id=distribution_id)))
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Error getting list of invalidation ids")

    def get_distribution_id_from_domain_name(self, domain_name):
        try:
            distribution_id = ""
            distributions = self.list_distributions(keyed=False)
            distributions += self.list_streaming_distributions(keyed=False)
            for dist in distributions:
                if any(str(alias).lower() == domain_name.lower() for alias in dist["Aliases"].get("Items", [])):
                    distribution_id = dist["Id"]
            return distribution_id
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Error getting distribution id from domain name")

    def get_aliases_from_distribution_id(self, distribution_id):
        try:
            distribution = self.get_distribution(id=distribution_id)
            return distribution["Distribution"]["DistributionConfig"]["Aliases"].get("Items", [])
        except botocore.exceptions.ClientError as e:
            self.module.fail_json_aws(e, msg="Error getting list of aliases from distribution_id")
