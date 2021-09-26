#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: route53_health_check
version_added: 1.0.0
short_description: Manage health-checks in Amazons Route53 DNS service
description:
  - Creates and deletes DNS Health checks in Amazons Route53 service.
  - Only the port, resource_path, string_match and request_interval are
    considered when updating existing health-checks.
options:
  state:
    description:
      - Specifies the action to take.
    choices: [ 'present', 'absent' ]
    type: str
    default: 'present'
  ip_address:
    description:
      - IP address of the end-point to check. Either this or I(fqdn) has to be provided.
    type: str
  port:
    description:
      - The port on the endpoint on which you want Amazon Route 53 to perform
        health checks. Required for TCP checks.
    type: int
  type:
    description:
      - The type of health check that you want to create, which indicates how
        Amazon Route 53 determines whether an endpoint is healthy.
    required: true
    choices: [ 'HTTP', 'HTTPS', 'HTTP_STR_MATCH', 'HTTPS_STR_MATCH', 'TCP' ]
    type: str
  resource_path:
    description:
      - The path that you want Amazon Route 53 to request when performing
        health checks. The path can be any value for which your endpoint will
        return an HTTP status code of 2xx or 3xx when the endpoint is healthy,
        for example the file /docs/route53-health-check.html.
      - Mutually exclusive with I(type='TCP').
      - The path must begin with a /
      - Maximum 255 characters.
    type: str
  fqdn:
    description:
      - Domain name of the endpoint to check. Either this or I(ip_address) has
        to be provided. When both are given the `fqdn` is used in the `Host:`
        header of the HTTP request.
    type: str
  string_match:
    description:
      - If the check type is HTTP_STR_MATCH or HTTP_STR_MATCH, the string
        that you want Amazon Route 53 to search for in the response body from
        the specified resource. If the string appears in the first 5120 bytes
        of the response body, Amazon Route 53 considers the resource healthy.
    type: str
  request_interval:
    description:
      - The number of seconds between the time that Amazon Route 53 gets a
        response from your endpoint and the time that it sends the next
        health-check request.
    default: 30
    choices: [ 10, 30 ]
    type: int
  failure_threshold:
    description:
      - The number of consecutive health checks that an endpoint must pass or
        fail for Amazon Route 53 to change the current status of the endpoint
        from unhealthy to healthy or vice versa.
      - Will default to C(3) if not specified on creation.
    choices: [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 ]
    type: int
author: "zimbatm (@zimbatm)"
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
'''

EXAMPLES = '''
- name: Create a health-check for host1.example.com and use it in record
  community.aws.route53_health_check:
    state: present
    fqdn: host1.example.com
    type: HTTP_STR_MATCH
    resource_path: /
    string_match: "Hello"
    request_interval: 10
    failure_threshold: 2
  register: my_health_check

- community.aws.route53:
    action: create
    zone: "example.com"
    type: CNAME
    record: "www.example.com"
    value: host1.example.com
    ttl: 30
    # Routing policy
    identifier: "host1@www"
    weight: 100
    health_check: "{{ my_health_check.health_check.id }}"

- name: Delete health-check
  community.aws.route53_health_check:
    state: absent
    fqdn: host1.example.com

'''

import uuid

try:
    import botocore
except ImportError:
    pass  # Handled by HAS_BOTO

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry


def _list_health_checks(**params):
    try:
        results = client.list_health_checks(aws_retry=True, **params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Failed to list health checks')
    return results


def find_health_check(ip_addr, fqdn, hc_type, request_interval, port):
    """Searches for health checks that have the exact same set of immutable values"""

    # In lieu of an Id we perform matches against the following values:
    # - ip_addr
    # - fqdn
    # - type (immutable)
    # - request_interval
    # - port

    # Because the list and route53 provides no 'filter' mechanism,
    # the using a paginator would result in (on average) double the
    # number of API calls and can get really slow.
    # Additionally, we can't properly wrap the paginator, so retrying means
    # starting from scratch with a paginator
    results = _list_health_checks()

    while True:
        for check in results.get('HealthChecks'):
            config = check.get('HealthCheckConfig')
            if (
                config.get('IPAddress', None) == ip_addr and
                config.get('FullyQualifiedDomainName', None) == fqdn and
                config.get('Type') == hc_type and
                config.get('RequestInterval') == request_interval and
                config.get('Port', None) == port
            ):
                return check

        if results.get('IsTruncated', False):
            results = _list_health_checks(Marker=results.get('NextMarker'))
        else:
            return None


def delete_health_check(check_id):
    if not check_id:
        return False, None

    if module.check_mode:
        return True, 'delete'

    try:
        client.delete_health_check(
            aws_retry=True,
            HealthCheckId=check_id,
        )
    except is_boto3_error_code('NoSuchHealthCheck'):
        # Handle the deletion race condition as cleanly as possible
        return False, None
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg='Failed to list health checks')

    return True, 'delete'


def create_health_check(ip_addr_in, fqdn_in, type_in, request_interval_in, port_in):

    # In general, if a request is repeated with the same CallerRef it won't
    # result in a duplicate check appearing.  This means we can safely use our
    # retry decorators
    caller_ref = str(uuid.uuid4())
    missing_args = []

    health_check = dict(
        Type=type_in,
        RequestInterval=request_interval_in,
        Port=port_in,
    )
    if ip_addr_in:
        health_check['IPAddress'] = ip_addr_in
    if fqdn_in:
        health_check['FullyQualifiedDomainName'] = fqdn_in

    if type_in in ['HTTP', 'HTTPS', 'HTTP_STR_MATCH', 'HTTPS_STR_MATCH']:
        resource_path = module.params.get('resource_path')
        # if not resource_path:
        #     missing_args.append('resource_path')
        if resource_path:
            health_check['ResourcePath'] = resource_path
    if type_in in ['HTTP_STR_MATCH', 'HTTPS_STR_MATCH']:
        string_match = module.params.get('string_match')
        if not string_match:
            missing_args.append('string_match')
        health_check['SearchString'] = module.params.get('string_match')

    failure_threshold = module.params.get('failure_threshold')
    if not failure_threshold:
        failure_threshold = 3
    health_check['FailureThreshold'] = failure_threshold

    if missing_args:
        module.fail_json(msg='missing required arguments for creation: {0}'.format(
            ', '.join(missing_args)),
        )

    if module.check_mode:
        return True, 'create', None

    try:
        result = client.create_health_check(
            aws_retry=True,
            CallerReference=caller_ref,
            HealthCheckConfig=health_check,
        )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg='Failed to create health check.', health_check=health_check)

    return True, 'create', result.get('HealthCheck').get('Id')


def update_health_check(existing_check):
    # In theory it's also possible to update the IPAddress, Port and
    # FullyQualifiedDomainName, however, because we use these in lieu of a
    # 'Name' to uniquely identify the health check this isn't currently
    # supported.  If we accepted an ID it would be possible to modify them.

    changes = dict()
    existing_config = existing_check.get('HealthCheckConfig')

    resource_path = module.params.get('resource_path', None)
    if resource_path and resource_path != existing_config.get('ResourcePath'):
        changes['ResourcePath'] = resource_path

    search_string = module.params.get('string_match', None)
    if search_string and search_string != existing_config.get('SearchString'):
        changes['SearchString'] = search_string

    failure_threshold = module.params.get('failure_threshold', None)
    if failure_threshold and failure_threshold != existing_config.get('FailureThreshold'):
        changes['FailureThreshold'] = failure_threshold

    # No changes...
    if not changes:
        return False, None

    if module.check_mode:
        return True, 'update'

    check_id = existing_check.get('Id')
    # This makes sure we're starting from the version we think we are...
    version_id = existing_check.get('HealthCheckVersion', 1)
    try:
        client.update_health_check(
            HealthCheckId=check_id,
            HealthCheckVersion=version_id,
            **changes,
        )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg='Failed to update health check.', id=check_id)

    return True, 'update'


def describe_health_check(id):
    if not id:
        return dict()

    try:
        result = client.get_health_check(
            aws_retry=True,
            HealthCheckId=id,
        )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg='Failed to get health check.', id=id)

    health_check = result.get('HealthCheck', {})
    health_check = camel_dict_to_snake_dict(health_check)
    return health_check


def main():
    argument_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        ip_address=dict(),
        port=dict(type='int'),
        type=dict(required=True, choices=['HTTP', 'HTTPS', 'HTTP_STR_MATCH', 'HTTPS_STR_MATCH', 'TCP']),
        resource_path=dict(),
        fqdn=dict(),
        string_match=dict(),
        request_interval=dict(type='int', choices=[10, 30], default=30),
        failure_threshold=dict(type='int', choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
    )

    args_one_of = [
        ['ip_address', 'fqdn'],
    ]

    args_if = [
        ['type', 'TCP', ('port',)],
    ]

    global module
    global client

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_one_of=args_one_of,
        required_if=args_if,
        supports_check_mode=True,
    )

    state_in = module.params.get('state')
    ip_addr_in = module.params.get('ip_address')
    port_in = module.params.get('port')
    type_in = module.params.get('type')
    resource_path_in = module.params.get('resource_path')
    fqdn_in = module.params.get('fqdn')
    string_match_in = module.params.get('string_match')
    request_interval_in = module.params.get('request_interval')
    failure_threshold_in = module.params.get('failure_threshold')

    # Default port
    if port_in is None:
        if type_in in ['HTTP', 'HTTP_STR_MATCH']:
            port_in = 80
        elif type_in in ['HTTPS', 'HTTPS_STR_MATCH']:
            port_in = 443

    if string_match_in:
        if type_in not in ['HTTP_STR_MATCH', 'HTTPS_STR_MATCH']:
            module.fail_json(msg="parameter 'string_match' argument is only for the HTTP(S)_STR_MATCH types")
        if len(string_match_in) > 255:
            module.fail_json(msg="parameter 'string_match' is limited to 255 characters max")

    client = module.client('route53', retry_decorator=AWSRetry.jittered_backoff())

    changed = False
    action = None
    check_id = None

    existing_check = find_health_check(ip_addr_in, fqdn_in, type_in, request_interval_in, port_in)

    if existing_check:
        check_id = existing_check.get('Id')

    if state_in == 'absent':
        changed, action = delete_health_check(check_id)
        check_id = None
    elif state_in == 'present':
        if existing_check is None:
            changed, action, check_id = create_health_check(ip_addr_in, fqdn_in, type_in, request_interval_in, port_in)
        else:
            changed, action = update_health_check(existing_check)

    health_check = describe_health_check(id=check_id)
    health_check['action'] = action
    module.exit_json(
        changed=changed,
        health_check=health_check,
    )


if __name__ == '__main__':
    main()
