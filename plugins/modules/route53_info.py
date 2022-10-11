#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
module: route53_info
short_description: Retrieves route53 details using AWS methods
version_added: 5.0.0
description:
  - Gets various details related to Route53 zone, record set or health check details.
  - This module was originally added to C(community.aws) in release 1.0.0.
options:
  query:
    description:
      - Specifies the query action to take.
    required: True
    choices: [
            'change',
            'checker_ip_range',
            'health_check',
            'hosted_zone',
            'record_sets',
            'reusable_delegation_set',
            ]
    type: str
  change_id:
    description:
      - The ID of the change batch request.
      - The value that you specify here is the value that
        ChangeResourceRecordSets returned in the Id element
        when you submitted the request.
      - Required if I(query=change).
    required: false
    type: str
  hosted_zone_id:
    description:
      - The Hosted Zone ID of the DNS zone.
      - Required if I(query) is set to I(hosted_zone) and I(hosted_zone_method) is set to I(details).
      - Required if I(query) is set to I(record_sets).
    required: false
    type: str
  max_items:
    description:
      - Maximum number of items to return for various get/list requests.
    required: false
    type: int
  next_marker:
    description:
      - "Some requests such as list_command: hosted_zones will return a maximum
        number of entries - EG 100 or the number specified by I(max_items).
        If the number of entries exceeds this maximum another request can be sent
        using the NextMarker entry from the first response to get the next page
        of results."
    required: false
    type: str
  delegation_set_id:
    description:
      - The DNS Zone delegation set ID.
    required: false
    type: str
  start_record_name:
    description:
      - "The first name in the lexicographic ordering of domain names that you want
        the list_command: record_sets to start listing from."
    required: false
    type: str
  type:
    description:
      - The type of DNS record.
    required: false
    choices: [ 'A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'CAA', 'NS', 'NAPTR', 'SOA', 'DS' ]
    type: str
  dns_name:
    description:
      - The first name in the lexicographic ordering of domain names that you want
        the list_command to start listing from.
    required: false
    type: str
  resource_id:
    description:
      - The ID/s of the specified resource/s.
      - Required if I(query=health_check) and I(health_check_method=tags).
      - Required if I(query=hosted_zone) and I(hosted_zone_method=tags).
    required: false
    aliases: ['resource_ids']
    type: list
    elements: str
  health_check_id:
    description:
      - The ID of the health check.
      - Required if C(query) is set to C(health_check) and
        C(health_check_method) is set to C(details) or C(status) or C(failure_reason).
    required: false
    type: str
  hosted_zone_method:
    description:
      - "This is used in conjunction with query: hosted_zone.
        It allows for listing details, counts or tags of various
        hosted zone details."
    required: false
    choices: [
        'details',
        'list',
        'list_by_name',
        'count',
        'tags',
        ]
    default: 'list'
    type: str
  health_check_method:
    description:
      - "This is used in conjunction with query: health_check.
        It allows for listing details, counts or tags of various
        health check details."
    required: false
    choices: [
        'list',
        'details',
        'status',
        'failure_reason',
        'count',
        'tags',
        ]
    default: 'list'
    type: str
author:
  - Karen Cheng (@Etherdaemon)
extends_documentation_fragment:
  - amazon.aws.aws
  - amazon.aws.ec2
  - amazon.aws.boto3

'''

EXAMPLES = r'''
# Simple example of listing all hosted zones
- name: List all hosted zones
  amazon.aws.route53_info:
    query: hosted_zone
  register: hosted_zones

# Getting a count of hosted zones
- name: Return a count of all hosted zones
  amazon.aws.route53_info:
    query: hosted_zone
    hosted_zone_method: count
  register: hosted_zone_count

- name: List the first 20 resource record sets in a given hosted zone
  amazon.aws.route53_info:
    profile: account_name
    query: record_sets
    hosted_zone_id: ZZZ1111112222
    max_items: 20
  register: record_sets

- name: List first 20 health checks
  amazon.aws.route53_info:
    query: health_check
    health_check_method: list
    max_items: 20
  register: health_checks

- name: Get health check last failure_reason
  amazon.aws.route53_info:
    query: health_check
    health_check_method: failure_reason
    health_check_id: 00000000-1111-2222-3333-12345678abcd
  register: health_check_failure_reason

- name: Retrieve reusable delegation set details
  amazon.aws.route53_info:
    query: reusable_delegation_set
    delegation_set_id: delegation id
  register: delegation_sets

- name: setup of example for using next_marker
  amazon.aws.route53_info:
    query: hosted_zone
    max_items: 1
  register: first_info

- name: example for using next_marker
  amazon.aws.route53_info:
    query: hosted_zone
    next_marker: "{{ first_info.NextMarker }}"
    max_items: 1
  when: "{{ 'NextMarker' in first_info }}"

- name: retrieve host entries starting with host1.workshop.test.io
  block:
    - name: grab zone id
      amazon.aws.route53_zone:
        zone: "test.io"
      register: AWSINFO

    - name: grab Route53 record information
      amazon.aws.route53_info:
        type: A
        query: record_sets
        hosted_zone_id: "{{ AWSINFO.zone_id }}"
        start_record_name: "host1.workshop.test.io"
      register: RECORDS
'''

RETURN = r'''
resource_record_sets:
    description: A list of resource record sets returned by list_resource_record_sets in boto3.
    returned: when I(query=record_sets)
    type: list
    elements: dict
    contains:
        name:
            description: The name of a record in the specified hosted zone.
            type: str
            sample: 'www.example.com'
        type:
            description: The DNS record type.
            type: str
            sample: 'A'
        ttl:
            description: The resource record cache time to live (TTL), in seconds.
            type: int
            sample: 60
        set_identifier:
            description: An identifier that differentiates among multiple resource record sets that have the same combination of name and type.
            type: str
            sample: 'abcd'
        resource_records:
            description: Information about the resource records.
            type: list
            elements: dict
            contains:
                value:
                    description: The current or new DNS record value.
                    type: str
                    sample: 'ns-12.awsdns-34.com.'
        geo_location:
            description: The specified geographic location for which the Route53 responds to based on location.
            type: dict
            elements: str
            contains:
                continent_code:
                    description: The two-letter code for the continent.
                    type: str
                    sample: 'NA'
                country_code:
                    description: The two-letter code for a country.
                    type: str
                    sample: 'US'
                subdivision_code:
                    description: The two-letter code for a state of the United States
                    type: str
                    sample: 'NY'
    version_added: 4.0.0
    version_added_collection: community.aws
hosted_zones:
    description: A list of hosted zones returned by list_hosted_zones in boto3.
    returned: when I(query=hosted_zone)
    type: list
    elements: dict
    contains:
        id:
            description: The ID of the hosted zone assigned by Amazon Route53 to the hosted zone at the creation time.
            type: str
            sample: '/hostedzone/Z01234567AB1234567890'
        name:
            description: The name of the domain.
            type: str
            sample: 'example.io'
        resource_record_set_count:
            description: The number of resource record sets in the hosted zone.
            type: int
            sample: 3
        caller_reference:
            description: The value specified for CallerReference at the time of hosted zone creation.
            type: str
            sample: '01d0db12-x0x9-12a3-1234-0z000z00zz0z'
        config:
            description: A dict that contains Comment and PrivateZone elements.
            type: dict
            contains:
                comment:
                    description: Any comments that included about in the hosted zone.
                    type: str
                    sample: 'HostedZone created by Route53 Registrar'
                private_zone:
                    description: A value that indicates whether this is a private hosted zone or not.
                    type: bool
                    sample: false
    version_added: 4.0.0
    version_added_collection: community.aws
health_checks:
    description: A list of Route53 health checks returned by list_health_checks in boto3.
    type: list
    elements: dict
    returned: when I(query=health_check)
    contains:
        id:
            description: The identifier that Amazon Route53 assigned to the health check at the time of creation.
            type: str
            sample: '12345cdc-2cc4-1234-bed2-123456abc1a2'
        health_check_version:
            description: The version of the health check.
            type: str
            sample: 1
        caller_reference:
            description: A unique string that you specified when you created the health check.
            type: str
            sample: '01d0db12-x0x9-12a3-1234-0z000z00zz0z'
        health_check_config:
            description: A dict that contains detailed information about one health check.
            type: dict
            contains:
                disabled:
                    description: Whether Route53 should stop performing health checks on a endpoint.
                    type: bool
                    sample: false
                enable_sni:
                    description: Whether Route53 should send value of FullyQualifiedDomainName to endpoint in client_hello message during TLS negotiation.
                    type: bool
                    sample: true
                failure_threshold:
                    description: The number of consecutive health checks that an endpoint must pass/fail for Route53 to change current status of endpoint.
                    type: int
                    sample: 3
                fully_qualified_domain_name:
                    description: The fully qualified DNS name of the endpoint on which Route53 performs health checks.
                    type: str
                    sample: 'hello'
                inverted:
                    description: Whether Route53 should invert the status of a health check.
                    type: bool
                    sample: false
                ip_address:
                    description: The IPv4/IPv6 IP address of the endpoint that Route53 should perform health checks on.
                    type: str
                    sample: 192.0.2.44
                measure_latency:
                    description: Whether Route53 should measure latency between health checkers in multiple AWS regions and the endpoint.
                    type: bool
                    sample: false
                port:
                    description: The port of the endpoint that Route53 should perform health checks on.
                    type: int
                    sample: 80
                request_interval:
                    description: The number of seconds between the time that Route53 gets a response from endpoint and the next health check request.
                    type: int
                    sample: 30
                resource_path:
                    description: The path that Route53 requests when performing health checks.
                    type: str
                    sample: '/welcome.html'
                search_string:
                    description: The string that Route53 uses to search for in the response body from specified resource.
                    type: str
                    sample: 'test-string-to-match'
                type:
                    description: The type of the health check.
                    type: str
                    sample: HTTPS
    version_added: 4.0.0
    version_added_collection: community.aws
checker_ip_ranges:
    description: A list of IP ranges in CIDR format for Amazon Route 53 health checkers.
    returned: when I(query=checker_ip_range)
    type: list
    elements: str
    version_added: 4.1.0
    version_added_collection: community.aws
delegation_sets:
    description: A list of dicts that contains information about the reusable delegation set.
    returned: when I(query=reusable_delegation_set)
    type: list
    elements: dict
    version_added: 4.1.0
    version_added_collection: community.aws
health_check:
    description: A dict of Route53 health check details returned by get_health_check_status in boto3.
    type: dict
    returned: when I(query=health_check) and I(health_check_method=details)
    contains:
        id:
            description: The identifier that Amazon Route53 assigned to the health check at the time of creation.
            type: str
            sample: '12345cdc-2cc4-1234-bed2-123456abc1a2'
        health_check_version:
            description: The version of the health check.
            type: str
            sample: 1
        caller_reference:
            description: A unique string that you specified when you created the health check.
            type: str
            sample: '01d0db12-x0x9-12a3-1234-0z000z00zz0z'
        health_check_config:
            description: A dict that contains detailed information about one health check.
            type: dict
            contains:
                disabled:
                    description: Whether Route53 should stop performing health checks on a endpoint.
                    type: bool
                    sample: false
                enable_sni:
                    description: Whether Route53 should send value of FullyQualifiedDomainName to endpoint in client_hello message during TLS negotiation.
                    type: bool
                    sample: true
                failure_threshold:
                    description: The number of consecutive health checks that an endpoint must pass/fail for Route53 to change current status of endpoint.
                    type: int
                    sample: 3
                fully_qualified_domain_name:
                    description: The fully qualified DNS name of the endpoint on which Route53 performs health checks.
                    type: str
                    sample: 'hello'
                inverted:
                    description: Whether Route53 should invert the status of a health check.
                    type: bool
                    sample: false
                ip_address:
                    description: The IPv4/IPv6 IP address of the endpoint that Route53 should perform health checks on.
                    type: str
                    sample: 192.0.2.44
                measure_latency:
                    description: Whether Route53 should measure latency between health checkers in multiple AWS regions and the endpoint.
                    type: bool
                    sample: false
                port:
                    description: The port of the endpoint that Route53 should perform health checks on.
                    type: int
                    sample: 80
                request_interval:
                    description: The number of seconds between the time that Route53 gets a response from endpoint and the next health check request.
                    type: int
                    sample: 30
                resource_path:
                    description: The path that Route53 requests when performing health checks.
                    type: str
                    sample: '/welcome.html'
                search_string:
                    description: The string that Route53 uses to search for in the response body from specified resource.
                    type: str
                    sample: 'test-string-to-match'
                type:
                    description: The type of the health check.
                    type: str
                    sample: HTTPS
    version_added: 4.1.0
    version_added_collection: community.aws
ResourceRecordSets:
    description: A deprecated CamelCased list of resource record sets returned by list_resource_record_sets in boto3. \
                 This list contains same elements/parameters as it's snake_cased version mentioned above. \
                 This field is deprecated and will be removed in 6.0.0 version release.
    returned: when I(query=record_sets)
    type: list
    elements: dict
HostedZones:
    description: A deprecated CamelCased list of hosted zones returned by list_hosted_zones in boto3. \
                 This list contains same elements/parameters as it's snake_cased version mentioned above. \
                 This field is deprecated and will be removed in 6.0.0 version release.
    returned: when I(query=hosted_zone)
    type: list
    elements: dict
HealthChecks:
    description: A deprecated CamelCased list of Route53 health checks returned by list_health_checks in boto3. \
                 This list contains same elements/parameters as it's snake_cased version mentioned above. \
                 This field is deprecated and will be removed in 6.0.0 version release.
    type: list
    elements: dict
    returned: when I(query=health_check)
CheckerIpRanges:
    description: A deprecated CamelCased list of IP ranges in CIDR format for Amazon Route 53 health checkers.\
                 This list contains same elements/parameters as it's snake_cased version mentioned abobe. \
                 This field is deprecated and will be removed in 6.0.0 version release.
    type: list
    elements: str
    returned: when I(query=checker_ip_range)
DelegationSets:
    description: A deprecated CamelCased list of dicts that contains information about the reusable delegation set. \
                 This list contains same elements/parameters as it's snake_cased version mentioned above. \
                 This field is deprecated and will be removed in 6.0.0 version release.
    type: list
    elements: dict
    returned: when I(query=reusable_delegation_set)
HealthCheck:
    description: A deprecated CamelCased dict of Route53 health check details returned by get_health_check_status in boto3. \
                 This dict contains same elements/parameters as it's snake_cased version mentioned above. \
                 This field is deprecated and will be removed in 6.0.0 version release.
    type: dict
    returned: when I(query=health_check) and I(health_check_method=details)
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils._text import to_native

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict


# Split out paginator to allow for the backoff decorator to function
@AWSRetry.jittered_backoff()
def _paginated_result(paginator_name, **params):
    paginator = client.get_paginator(paginator_name)
    return paginator.paginate(**params).build_full_result()


def get_hosted_zone():
    params = dict()

    if module.params.get('hosted_zone_id'):
        params['Id'] = module.params.get('hosted_zone_id')
    else:
        module.fail_json(msg="Hosted Zone Id is required")

    return client.get_hosted_zone(**params)


def reusable_delegation_set_details():
    params = dict()

    if not module.params.get('delegation_set_id'):
        if module.params.get('max_items'):
            params['MaxItems'] = str(module.params.get('max_items'))

        if module.params.get('next_marker'):
            params['Marker'] = module.params.get('next_marker')

        results = client.list_reusable_delegation_sets(**params)
    else:
        params['DelegationSetId'] = module.params.get('delegation_set_id')
        results = client.get_reusable_delegation_set(**params)

    results['delegation_sets'] = results['DelegationSets']
    module.deprecate("The 'CamelCase' return values with key 'DelegationSets' is deprecated and \
                    will be replaced by 'snake_case' return values with key 'delegation_sets'. \
                    Both case values are returned for now.",
                     date='2025-01-01', collection_name='amazon.aws')

    return results


def list_hosted_zones():
    params = dict()

    # Set PaginationConfig with max_items
    if module.params.get('max_items'):
        params['PaginationConfig'] = dict(
            MaxItems=module.params.get('max_items')
        )

    if module.params.get('next_marker'):
        params['Marker'] = module.params.get('next_marker')

    if module.params.get('delegation_set_id'):
        params['DelegationSetId'] = module.params.get('delegation_set_id')

    zones = _paginated_result('list_hosted_zones', **params)['HostedZones']
    snaked_zones = [camel_dict_to_snake_dict(zone) for zone in zones]

    module.deprecate("The 'CamelCase' return values with key 'HostedZones' and 'list' are deprecated and \
                    will be replaced by 'snake_case' return values with key 'hosted_zones'. \
                    Both case values are returned for now.",
                     date='2025-01-01', collection_name='amazon.aws')

    return {
        "HostedZones": zones,
        "list": zones,
        "hosted_zones": snaked_zones,
    }


def list_hosted_zones_by_name():
    params = dict()

    if module.params.get('hosted_zone_id'):
        params['HostedZoneId'] = module.params.get('hosted_zone_id')

    if module.params.get('dns_name'):
        params['DNSName'] = module.params.get('dns_name')

    if module.params.get('max_items'):
        params['MaxItems'] = str(module.params.get('max_items'))

    return client.list_hosted_zones_by_name(**params)


def change_details():
    params = dict()

    if module.params.get('change_id'):
        params['Id'] = module.params.get('change_id')
    else:
        module.fail_json(msg="change_id is required")

    results = client.get_change(**params)
    return results


def checker_ip_range_details():
    results = client.get_checker_ip_ranges()
    results['checker_ip_ranges'] = results['CheckerIpRanges']
    module.deprecate("The 'CamelCase' return values with key 'CheckerIpRanges' is deprecated and \
                    will be replaced by 'snake_case' return values with key 'checker_ip_ranges'. \
                    Both case values are returned for now.",
                     date='2025-01-01', collection_name='amazon.aws')

    return results


def get_count():
    if module.params.get('query') == 'health_check':
        results = client.get_health_check_count()
    else:
        results = client.get_hosted_zone_count()

    return results


def get_health_check():
    params = dict()

    if not module.params.get('health_check_id'):
        module.fail_json(msg="health_check_id is required")
    else:
        params['HealthCheckId'] = module.params.get('health_check_id')

    if module.params.get('health_check_method') == 'details':
        results = client.get_health_check(**params)
    elif module.params.get('health_check_method') == 'failure_reason':
        results = client.get_health_check_last_failure_reason(**params)
    elif module.params.get('health_check_method') == 'status':
        results = client.get_health_check_status(**params)

    results['health_check'] = camel_dict_to_snake_dict(results['HealthCheck'])
    module.deprecate("The 'CamelCase' return values with key 'HealthCheck' is deprecated and \
                    will be replaced by 'snake_case' return values with key 'health_check'. \
                    Both case values are returned for now.",
                     date='2025-01-01', collection_name='amazon.aws')

    return results


def get_resource_tags():
    params = dict()

    if module.params.get('resource_id'):
        params['ResourceIds'] = module.params.get('resource_id')
    else:
        module.fail_json(msg="resource_id or resource_ids is required")

    if module.params.get('query') == 'health_check':
        params['ResourceType'] = 'healthcheck'
    else:
        params['ResourceType'] = 'hostedzone'

    return client.list_tags_for_resources(**params)


def list_health_checks():
    params = dict()

    if module.params.get('next_marker'):
        params['Marker'] = module.params.get('next_marker')

    # Set PaginationConfig with max_items
    if module.params.get('max_items'):
        params['PaginationConfig'] = dict(
            MaxItems=module.params.get('max_items')
        )

    health_checks = _paginated_result('list_health_checks', **params)['HealthChecks']
    snaked_health_checks = [camel_dict_to_snake_dict(health_check) for health_check in health_checks]

    module.deprecate("The 'CamelCase' return values with key 'HealthChecks' and 'list' are deprecated and \
                    will be replaced by 'snake_case' return values with key 'health_checks'. \
                    Both case values are returned for now.",
                     date='2025-01-01', collection_name='amazon.aws')

    return {
        "HealthChecks": health_checks,
        "list": health_checks,
        "health_checks": snaked_health_checks,
    }


def record_sets_details():
    params = dict()

    if module.params.get('hosted_zone_id'):
        params['HostedZoneId'] = module.params.get('hosted_zone_id')
    else:
        module.fail_json(msg="Hosted Zone Id is required")

    if module.params.get('start_record_name'):
        params['StartRecordName'] = module.params.get('start_record_name')

    # Check that both params are set if type is applied
    if module.params.get('type') and not module.params.get('start_record_name'):
        module.fail_json(msg="start_record_name must be specified if type is set")

    if module.params.get('type'):
        params['StartRecordType'] = module.params.get('type')

    # Set PaginationConfig with max_items
    if module.params.get('max_items'):
        params['PaginationConfig'] = dict(
            MaxItems=module.params.get('max_items')
        )

    record_sets = _paginated_result('list_resource_record_sets', **params)['ResourceRecordSets']
    snaked_record_sets = [camel_dict_to_snake_dict(record_set) for record_set in record_sets]

    module.deprecate("The 'CamelCase' return values with key 'ResourceRecordSets' and 'list' are deprecated and \
                    will be replaced by 'snake_case' return values with key 'resource_record_sets'. \
                    Both case values are returned for now.",
                     date='2025-01-01', collection_name='amazon.aws')

    return {
        "ResourceRecordSets": record_sets,
        "list": record_sets,
        "resource_record_sets": snaked_record_sets,
    }


def health_check_details():
    health_check_invocations = {
        'list': list_health_checks,
        'details': get_health_check,
        'status': get_health_check,
        'failure_reason': get_health_check,
        'count': get_count,
        'tags': get_resource_tags,
    }

    results = health_check_invocations[module.params.get('health_check_method')]()
    return results


def hosted_zone_details():
    hosted_zone_invocations = {
        'details': get_hosted_zone,
        'list': list_hosted_zones,
        'list_by_name': list_hosted_zones_by_name,
        'count': get_count,
        'tags': get_resource_tags,
    }

    results = hosted_zone_invocations[module.params.get('hosted_zone_method')]()
    return results


def main():
    global module
    global client

    argument_spec = dict(
        query=dict(choices=[
            'change',
            'checker_ip_range',
            'health_check',
            'hosted_zone',
            'record_sets',
            'reusable_delegation_set',
        ], required=True),
        change_id=dict(),
        hosted_zone_id=dict(),
        max_items=dict(type='int'),
        next_marker=dict(),
        delegation_set_id=dict(),
        start_record_name=dict(),
        type=dict(type='str', choices=[
            'A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'CAA', 'NS', 'NAPTR', 'SOA', 'DS'
        ]),
        dns_name=dict(),
        resource_id=dict(type='list', aliases=['resource_ids'], elements='str'),
        health_check_id=dict(),
        hosted_zone_method=dict(choices=[
            'details',
            'list',
            'list_by_name',
            'count',
            'tags'
        ], default='list'),
        health_check_method=dict(choices=[
            'list',
            'details',
            'status',
            'failure_reason',
            'count',
            'tags',
        ], default='list'),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ['hosted_zone_method', 'health_check_method'],
        ],
        check_boto3=False,
    )

    try:
        client = module.client('route53', retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to connect to AWS')

    invocations = {
        'change': change_details,
        'checker_ip_range': checker_ip_range_details,
        'health_check': health_check_details,
        'hosted_zone': hosted_zone_details,
        'record_sets': record_sets_details,
        'reusable_delegation_set': reusable_delegation_set_details,
    }

    results = dict(changed=False)
    try:
        results = invocations[module.params.get('query')]()
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json(msg=to_native(e))

    module.exit_json(**results)


if __name__ == '__main__':
    main()
