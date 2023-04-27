#
# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


import pytest

try:
    import botocore
except ImportError:
    # Handled by HAS_BOTO3
    pass

from ansible_collections.amazon.aws.plugins.module_utils.cloudfront_facts import (
    CloudFrontFactsServiceManager,
    CloudFrontFactsServiceManagerFailure,
    cloudfront_facts_keyed_list_helper,
)
from unittest.mock import MagicMock, patch, call


MODULE_NAME = "ansible_collections.amazon.aws.plugins.module_utils.cloudfront_facts"
MOCK_CLOUDFRONT_FACTS_KEYED_LIST_HELPER = MODULE_NAME + ".cloudfront_facts_keyed_list_helper"


@pytest.fixture()
def cloudfront_facts_service():
    module = MagicMock()
    cloudfront_facts = CloudFrontFactsServiceManager(module)

    cloudfront_facts.module = MagicMock()
    cloudfront_facts.module.fail_json_aws.side_effect = SystemExit(1)

    cloudfront_facts.client = MagicMock()

    return cloudfront_facts


def raise_botocore_error(operation="getCloudFront"):
    return botocore.exceptions.ClientError(
        {
            "Error": {"Code": "AccessDenied", "Message": "User: Unauthorized operation"},
            "ResponseMetadata": {"RequestId": "01234567-89ab-cdef-0123-456789abcdef"},
        },
        operation,
    )


def test_unsupported_api(cloudfront_facts_service):
    with pytest.raises(CloudFrontFactsServiceManagerFailure) as err:
        cloudfront_facts_service._unsupported_api()
        assert "Method _unsupported_api is not currently supported" in err


def test_get_distribution(cloudfront_facts_service):
    cloudfront_facts = MagicMock()
    cloudfront_id = MagicMock()
    cloudfront_facts_service.client.get_distribution.return_value = cloudfront_facts

    assert cloudfront_facts == cloudfront_facts_service.get_distribution(id=cloudfront_id)
    cloudfront_facts_service.client.get_distribution.assert_called_with(Id=cloudfront_id, aws_retry=True)


def test_get_distribution_failure(cloudfront_facts_service):
    cloudfront_id = MagicMock()
    cloudfront_facts_service.client.get_distribution.side_effect = raise_botocore_error()

    with pytest.raises(SystemExit):
        cloudfront_facts_service.get_distribution(id=cloudfront_id)
        cloudfront_facts_service.client.get_distribution.assert_called_with(Id=cloudfront_id, aws_retry=True)


def test_get_distribution_fail_if_error(cloudfront_facts_service):
    cloudfront_id = MagicMock()
    cloudfront_facts_service.client.get_distribution.side_effect = raise_botocore_error()

    with pytest.raises(botocore.exceptions.ClientError):
        cloudfront_facts_service.get_distribution(id=cloudfront_id, fail_if_error=False)
        cloudfront_facts_service.client.get_distribution.assert_called_with(Id=cloudfront_id, aws_retry=True)


def test_get_invalidation(cloudfront_facts_service):
    cloudfront_facts = MagicMock()
    cloudfront_id = MagicMock()
    distribution_id = MagicMock()
    cloudfront_facts_service.client.get_invalidation.return_value = cloudfront_facts

    assert cloudfront_facts == cloudfront_facts_service.get_invalidation(
        distribution_id=distribution_id, id=cloudfront_id
    )
    cloudfront_facts_service.client.get_invalidation.assert_called_with(
        DistributionId=distribution_id, Id=cloudfront_id, aws_retry=True
    )


def test_get_invalidation_failure(cloudfront_facts_service):
    cloudfront_id = MagicMock()
    distribution_id = MagicMock()
    cloudfront_facts_service.client.get_invalidation.side_effect = raise_botocore_error()

    with pytest.raises(SystemExit):
        cloudfront_facts_service.get_invalidation(distribution_id=distribution_id, id=cloudfront_id)


@patch(MOCK_CLOUDFRONT_FACTS_KEYED_LIST_HELPER)
def test_list_distributions_by_web_acl_id(m_cloudfront_facts_keyed_list_helper, cloudfront_facts_service):
    web_acl_id = MagicMock()
    distribution_webacl = {"DistributionList": {"Items": [f"webacl_{int(d)}" for d in range(10)]}}
    cloudfront_facts_service.client.list_distributions_by_web_acl_id.return_value = distribution_webacl
    m_cloudfront_facts_keyed_list_helper.return_value = distribution_webacl["DistributionList"]["Items"]

    result = cloudfront_facts_service.list_distributions_by_web_acl_id(web_acl_id=web_acl_id)
    assert distribution_webacl["DistributionList"]["Items"] == result
    cloudfront_facts_service.client.list_distributions_by_web_acl_id.assert_called_with(
        WebAclId=web_acl_id, aws_retry=True
    )
    m_cloudfront_facts_keyed_list_helper.assert_called_with(distribution_webacl["DistributionList"]["Items"])


@patch(MOCK_CLOUDFRONT_FACTS_KEYED_LIST_HELPER)
@patch(MODULE_NAME + "._cloudfront_paginate_build_full_result")
def test_list_origin_access_identities(
    m_cloudfront_paginate_build_full_result, m_cloudfront_facts_keyed_list_helper, cloudfront_facts_service
):
    items = [f"item_{int(d)}" for d in range(10)]
    result = {"CloudFrontOriginAccessIdentityList": {"Items": items}}

    m_cloudfront_paginate_build_full_result.return_value = result
    assert items == cloudfront_facts_service.list_origin_access_identities()
    m_cloudfront_facts_keyed_list_helper.assert_not_called()


@patch(MOCK_CLOUDFRONT_FACTS_KEYED_LIST_HELPER)
@patch(MODULE_NAME + "._cloudfront_paginate_build_full_result")
def test_list_distributions(
    m_cloudfront_paginate_build_full_result, m_cloudfront_facts_keyed_list_helper, cloudfront_facts_service
):
    items = [f"item_{int(d)}" for d in range(10)]
    result = {"DistributionList": {"Items": items}}

    m_cloudfront_paginate_build_full_result.return_value = result
    m_cloudfront_facts_keyed_list_helper.return_value = items

    assert items == cloudfront_facts_service.list_distributions()
    m_cloudfront_facts_keyed_list_helper.assert_called_with(items)


@patch(MOCK_CLOUDFRONT_FACTS_KEYED_LIST_HELPER)
@patch(MODULE_NAME + "._cloudfront_paginate_build_full_result")
def test_list_invalidations(
    m_cloudfront_paginate_build_full_result, m_cloudfront_facts_keyed_list_helper, cloudfront_facts_service
):
    items = [f"item_{int(d)}" for d in range(10)]
    result = {"InvalidationList": {"Items": items}}
    distribution_id = MagicMock()

    m_cloudfront_paginate_build_full_result.return_value = result
    m_cloudfront_facts_keyed_list_helper.return_value = items

    assert items == cloudfront_facts_service.list_invalidations(distribution_id=distribution_id)
    m_cloudfront_facts_keyed_list_helper.assert_not_called()
    m_cloudfront_paginate_build_full_result.assert_called_with(
        cloudfront_facts_service.client, "list_invalidations", DistributionId=distribution_id
    )


@pytest.mark.parametrize("fail_if_error", [True, False])
@patch(MODULE_NAME + "._cloudfront_paginate_build_full_result")
def test_list_invalidations_failure(m_cloudfront_paginate_build_full_result, cloudfront_facts_service, fail_if_error):
    distribution_id = MagicMock()
    m_cloudfront_paginate_build_full_result.side_effect = raise_botocore_error()

    if fail_if_error:
        with pytest.raises(SystemExit):
            cloudfront_facts_service.list_invalidations(distribution_id=distribution_id, fail_if_error=fail_if_error)
    else:
        with pytest.raises(botocore.exceptions.ClientError):
            cloudfront_facts_service.list_invalidations(distribution_id=distribution_id, fail_if_error=fail_if_error)
    m_cloudfront_paginate_build_full_result.assert_called_with(
        cloudfront_facts_service.client, "list_invalidations", DistributionId=distribution_id
    )


@pytest.mark.parametrize(
    "list_to_key,expected",
    [
        ([], {}),
        (
            [{"Id": "id_1", "Aliases": {}}, {"Id": "id_2", "Aliases": {"Items": ["alias_1", "alias_2"]}}],
            {
                "id_1": {"Id": "id_1", "Aliases": {}},
                "id_2": {"Id": "id_2", "Aliases": {"Items": ["alias_1", "alias_2"]}},
                "alias_1": {"Id": "id_2", "Aliases": {"Items": ["alias_1", "alias_2"]}},
                "alias_2": {"Id": "id_2", "Aliases": {"Items": ["alias_1", "alias_2"]}},
            },
        ),
    ],
)
def test_cloudfront_facts_keyed_list_helper(list_to_key, expected):
    assert expected == cloudfront_facts_keyed_list_helper(list_to_key)


@pytest.mark.parametrize(
    "distribution,expected",
    [
        ({"Distribution": {"DistributionConfig": {"Aliases": {"Items": ["item_1", "item_2"]}}}}, ["item_1", "item_2"]),
        ({"Distribution": {"DistributionConfig": {"Aliases": {}}}}, []),
    ],
)
def test_get_aliases_from_distribution_id(cloudfront_facts_service, distribution, expected):
    distribution_id = MagicMock()

    cloudfront_facts_service.get_distribution = MagicMock()
    cloudfront_facts_service.get_distribution.return_value = distribution
    assert expected == cloudfront_facts_service.get_aliases_from_distribution_id(distribution_id)


def test_get_aliases_from_distribution_id_failure(cloudfront_facts_service):
    distribution_id = MagicMock()

    cloudfront_facts_service.get_distribution = MagicMock()
    cloudfront_facts_service.get_distribution.side_effect = raise_botocore_error()

    with pytest.raises(SystemExit):
        cloudfront_facts_service.get_aliases_from_distribution_id(distribution_id)
        cloudfront_facts_service.get_distribution.assert_called_once_with(id=distribution_id)


@pytest.mark.parametrize(
    "distributions,streaming_distributions,domain_name,expected",
    [
        ([], [], MagicMock(), ""),
        ([{"Aliases": {"Items": ["domain_01", "domain_02"]}, "Id": "id-01"}], [], "domain01", ""),
        ([{"Aliases": {"Items": ["domain_01", "domain_02"]}, "Id": "id-01"}], [], "domain_01", "id-01"),
        ([{"Aliases": {"Items": ["domain_01", "domain_02"]}, "Id": "id-01"}], [], "DOMAIN_01", "id-01"),
        ([{"Aliases": {"Items": ["domain_01", "domain_02"]}, "Id": "id-01"}], [], "domain_02", "id-01"),
        ([], [{"Aliases": {"Items": ["domain_01", "domain_02"]}, "Id": "stream-01"}], "DOMAIN", ""),
        ([], [{"Aliases": {"Items": ["domain_01", "domain_02"]}, "Id": "stream-01"}], "DOMAIN_01", "stream-01"),
        ([], [{"Aliases": {"Items": ["domain_01", "domain_02"]}, "Id": "stream-01"}], "domain_01", "stream-01"),
        ([], [{"Aliases": {"Items": ["domain_01", "domain_02"]}, "Id": "stream-01"}], "domain_02", "stream-01"),
        (
            [{"Aliases": {"Items": ["domain_01", "domain_02"]}, "Id": "id-01"}],
            [{"Aliases": {"Items": ["domain_01", "domain_02"]}, "Id": "stream-01"}],
            "domain_01",
            "stream-01",
        ),
    ],
)
def test_get_distribution_id_from_domain_name(
    cloudfront_facts_service, distributions, streaming_distributions, domain_name, expected
):
    cloudfront_facts_service.list_distributions = MagicMock()
    cloudfront_facts_service.list_streaming_distributions = MagicMock()

    cloudfront_facts_service.list_distributions.return_value = distributions
    cloudfront_facts_service.list_streaming_distributions.return_value = streaming_distributions

    assert expected == cloudfront_facts_service.get_distribution_id_from_domain_name(domain_name)

    cloudfront_facts_service.list_distributions.assert_called_once_with(keyed=False)
    cloudfront_facts_service.list_streaming_distributions.assert_called_once_with(keyed=False)


@pytest.mark.parametrize("streaming", [True, False])
def test_get_etag_from_distribution_id(cloudfront_facts_service, streaming):
    distribution = {"ETag": MagicMock()}
    streaming_distribution = {"ETag": MagicMock()}

    distribution_id = MagicMock()

    cloudfront_facts_service.get_distribution = MagicMock()
    cloudfront_facts_service.get_distribution.return_value = distribution

    cloudfront_facts_service.get_streaming_distribution = MagicMock()
    cloudfront_facts_service.get_streaming_distribution.return_value = streaming_distribution

    expected = distribution if not streaming else streaming_distribution

    assert expected["ETag"] == cloudfront_facts_service.get_etag_from_distribution_id(distribution_id, streaming)
    if not streaming:
        cloudfront_facts_service.get_distribution.assert_called_once_with(id=distribution_id)
    else:
        cloudfront_facts_service.get_streaming_distribution.assert_called_once_with(id=distribution_id)


@pytest.mark.parametrize(
    "invalidations, expected",
    [
        ([], []),
        ([{"Id": "id-01"}], ["id-01"]),
        ([{"Id": "id-01"}, {"Id": "id-02"}], ["id-01", "id-02"]),
    ],
)
def test_get_list_of_invalidation_ids_from_distribution_id(cloudfront_facts_service, invalidations, expected):
    cloudfront_facts_service.list_invalidations = MagicMock()
    cloudfront_facts_service.list_invalidations.return_value = invalidations

    distribution_id = MagicMock()
    assert expected == cloudfront_facts_service.get_list_of_invalidation_ids_from_distribution_id(distribution_id)
    cloudfront_facts_service.list_invalidations.assert_called_with(distribution_id=distribution_id)


def test_get_list_of_invalidation_ids_from_distribution_id_failure(cloudfront_facts_service):
    cloudfront_facts_service.list_invalidations = MagicMock()
    cloudfront_facts_service.list_invalidations.side_effect = raise_botocore_error()

    distribution_id = MagicMock()
    with pytest.raises(SystemExit):
        cloudfront_facts_service.get_list_of_invalidation_ids_from_distribution_id(distribution_id)


@pytest.mark.parametrize("streaming", [True, False])
@pytest.mark.parametrize(
    "distributions, expected",
    [
        ([], []),
        (
            [
                {
                    "Id": "id_1",
                    "Aliases": {"Items": ["item_1", "item_2"]},
                    "WebACLId": "webacl_1",
                    "ARN": "arn:ditribution:us-east-1:1",
                    "Status": "available",
                    "LastModifiedTime": "11102022120000",
                    "DomainName": "domain_01.com",
                    "Comment": "This is the first distribution",
                    "PriceClass": "low",
                    "Enabled": "False",
                    "Tags": {"Items": [{"Name": "tag1", "Value": "distribution1"}]},
                    "ETag": "abcdefgh",
                    "_ids": [],
                },
                {
                    "Id": "id_2",
                    "Aliases": {"Items": ["item_20"]},
                    "WebACLId": "webacl_2",
                    "ARN": "arn:ditribution:us-west:2",
                    "Status": "active",
                    "LastModifiedTime": "11102022200000",
                    "DomainName": "another_domain_name.com",
                    "Comment": "This is the second distribution",
                    "PriceClass": "High",
                    "Enabled": "True",
                    "Tags": {
                        "Items": [
                            {"Name": "tag2", "Value": "distribution2"},
                            {"Name": "another_tag", "Value": "item 2"},
                        ]
                    },
                    "ETag": "ABCDEFGH",
                    "_ids": ["invalidation_1", "invalidation_2"],
                },
            ],
            [
                {
                    "Id": "id_1",
                    "ARN": "arn:ditribution:us-east-1:1",
                    "Status": "available",
                    "LastModifiedTime": "11102022120000",
                    "DomainName": "domain_01.com",
                    "Comment": "This is the first distribution",
                    "PriceClass": "low",
                    "Enabled": "False",
                    "Aliases": ["item_1", "item_2"],
                    "ETag": "abcdefgh",
                    "WebACLId": "webacl_1",
                    "Tags": [{"Name": "tag1", "Value": "distribution1"}],
                },
                {
                    "Id": "id_2",
                    "ARN": "arn:ditribution:us-west:2",
                    "Status": "active",
                    "LastModifiedTime": "11102022200000",
                    "DomainName": "another_domain_name.com",
                    "Comment": "This is the second distribution",
                    "PriceClass": "High",
                    "Enabled": "True",
                    "Aliases": ["item_20"],
                    "ETag": "ABCDEFGH",
                    "WebACLId": "webacl_2",
                    "Invalidations": ["invalidation_1", "invalidation_2"],
                    "Tags": [{"Name": "tag2", "Value": "distribution2"}, {"Name": "another_tag", "Value": "item 2"}],
                },
            ],
        ),
    ],
)
@patch(MODULE_NAME + ".boto3_tag_list_to_ansible_dict")
def test_summary_get_distribution_list(
    m_boto3_tag_list_to_ansible_dict, cloudfront_facts_service, streaming, distributions, expected
):
    m_boto3_tag_list_to_ansible_dict.side_effect = lambda x: x

    cloudfront_facts_service.list_streaming_distributions = MagicMock()
    cloudfront_facts_service.list_streaming_distributions.return_value = distributions

    cloudfront_facts_service.list_distributions = MagicMock()
    cloudfront_facts_service.list_distributions.return_value = distributions

    cloudfront_facts_service.get_etag_from_distribution_id = MagicMock()
    cloudfront_facts_service.get_etag_from_distribution_id.side_effect = lambda id, stream: [
        x["ETag"] for x in distributions if x["Id"] == id
    ][0]

    cloudfront_facts_service.get_list_of_invalidation_ids_from_distribution_id = MagicMock()
    cloudfront_facts_service.get_list_of_invalidation_ids_from_distribution_id.side_effect = lambda id: [
        x["_ids"] for x in distributions if x["Id"] == id
    ][0]

    cloudfront_facts_service.list_resource_tags = MagicMock()
    cloudfront_facts_service.list_resource_tags.side_effect = lambda arn: {
        "Tags": x["Tags"] for x in distributions if x["ARN"] == arn
    }

    key_name = "streaming_distributions"
    if not streaming:
        key_name = "distributions"

    if streaming:
        expected = list(map(lambda x: {k: x[k] for k in x if k not in ("WebACLId", "Invalidations")}, expected))
    assert {key_name: expected} == cloudfront_facts_service.summary_get_distribution_list(streaming)


@pytest.mark.parametrize("streaming", [True, False])
def test_summary_get_distribution_list_failure(cloudfront_facts_service, streaming):
    cloudfront_facts_service.list_streaming_distributions = MagicMock()
    cloudfront_facts_service.list_streaming_distributions.side_effect = raise_botocore_error()

    cloudfront_facts_service.list_distributions = MagicMock()
    cloudfront_facts_service.list_distributions.side_effect = raise_botocore_error()

    with pytest.raises(SystemExit):
        cloudfront_facts_service.summary_get_distribution_list(streaming)


def test_summary(cloudfront_facts_service):
    cloudfront_facts_service.summary_get_distribution_list = MagicMock()
    cloudfront_facts_service.summary_get_distribution_list.side_effect = lambda x: (
        {"called_with_true": True} if x else {"called_with_false": False}
    )

    cloudfront_facts_service.summary_get_origin_access_identity_list = MagicMock()
    cloudfront_facts_service.summary_get_origin_access_identity_list.return_value = {
        "origin_access_ids": ["access_1", "access_2"]
    }

    expected = {"called_with_true": True, "called_with_false": False, "origin_access_ids": ["access_1", "access_2"]}

    assert expected == cloudfront_facts_service.summary()

    cloudfront_facts_service.summary_get_origin_access_identity_list.assert_called_once()
    cloudfront_facts_service.summary_get_distribution_list.assert_has_calls([call(True), call(False)], any_order=True)


@pytest.mark.parametrize(
    "origin_access_identities,expected",
    [
        ([], []),
        (
            [
                {"Id": "some_id", "response": {"state": "active", "ETag": "some_Etag"}},
                {"Id": "another_id", "response": {"ETag": "another_Etag"}},
            ],
            [{"Id": "some_id", "ETag": "some_Etag"}, {"Id": "another_id", "ETag": "another_Etag"}],
        ),
    ],
)
def test_summary_get_origin_access_identity_list(cloudfront_facts_service, origin_access_identities, expected):
    cloudfront_facts_service.list_origin_access_identities = MagicMock()
    cloudfront_facts_service.list_origin_access_identities.return_value = origin_access_identities
    cloudfront_facts_service.get_origin_access_identity = MagicMock()
    cloudfront_facts_service.get_origin_access_identity.side_effect = lambda x: [
        o["response"] for o in origin_access_identities if o["Id"] == x
    ][0]

    assert {"origin_access_identities": expected} == cloudfront_facts_service.summary_get_origin_access_identity_list()


def test_summary_get_origin_access_identity_list_failure(cloudfront_facts_service):
    cloudfront_facts_service.list_origin_access_identities = MagicMock()
    cloudfront_facts_service.list_origin_access_identities.side_effect = raise_botocore_error()

    with pytest.raises(SystemExit):
        cloudfront_facts_service.summary_get_origin_access_identity_list()
