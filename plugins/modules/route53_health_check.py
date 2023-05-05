#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: route53_health_check
version_added: 5.0.0
short_description: Manage health-checks in Amazons Route53 DNS service
description:
  - Creates and deletes DNS Health checks in Amazons Route53 service.
  - Only the port, resource_path, string_match and request_interval are
    considered when updating existing health-checks.
  - This module was originally added to C(community.aws) in release 1.0.0.
options:
  state:
    description:
      - Specifies the action to take.
    choices: [ 'present', 'absent' ]
    type: str
    default: 'present'
  disabled:
    description:
      - Stops Route 53 from performing health checks.
      - See the AWS documentation for more details on the exact implications.
        U(https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/health-checks-creating-values.html)
      - Defaults to C(true) when creating a new health check.
    type: bool
    version_added: 2.1.0
    version_added_collection: community.aws
  ip_address:
    description:
      - IP address of the end-point to check. Either this or I(fqdn) has to be provided.
      - IP addresses must be publicly routable.
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
      - Once health_check is created, type can not be changed.
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
        to be provided. When both are given the I(fqdn) is used in the C(Host:)
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
  health_check_name:
    description:
      - Name of the Health Check.
      - Used together with I(use_unique_names) to set/make use of I(health_check_name) as a unique identifier.
    type: str
    required: False
    aliases: ['name']
    version_added: 4.1.0
    version_added_collection: community.aws
  use_unique_names:
    description:
      - Used together with I(health_check_name) to set/make use of I(health_check_name) as a unique identifier.
    type: bool
    required: False
    version_added: 4.1.0
    version_added_collection: community.aws
  health_check_id:
    description:
      - ID of the health check to be update or deleted.
      - If provided, a health check can be updated or deleted based on the ID as unique identifier.
    type: str
    required: False
    aliases: ['id']
    version_added: 4.1.0
    version_added_collection: community.aws
  measure_latency:
    description:
      - To enable/disable latency graphs to monitor the latency between health checkers in multiple Amazon Web Services regions and your endpoint.
      - Value of I(measure_latency) is immutable and can not be modified after creating a health check.
        See U(https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/monitoring-health-check-latency.html)
    type: bool
    required: False
    version_added: 5.4.0
author:
  - "zimbatm (@zimbatm)"
notes:
  - Support for I(tags) and I(purge_tags) was added in release 2.1.0.
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Create a health-check for host1.example.com and use it in record
  amazon.aws.route53_health_check:
    state: present
    fqdn: host1.example.com
    type: HTTP_STR_MATCH
    resource_path: /
    string_match: "Hello"
    request_interval: 10
    failure_threshold: 2
  register: my_health_check

- amazon.aws.route53:
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

- name: create a simple health check with health_check_name as unique identifier
  amazon.aws.route53_health_check:
    state: present
    health_check_name: ansible
    fqdn: ansible.com
    port: 443
    type: HTTPS
    use_unique_names: true

- name: create a TCP health check with latency graphs enabled
  amazon.aws.route53_health_check:
    state: present
    health_check_name: ansible
    fqdn: ansible.com
    port: 443
    type: HTTPS
    use_unique_names: true
    measure_latency: true

- name: Delete health-check
  amazon.aws.route53_health_check:
    state: absent
    fqdn: host1.example.com

- name: Update Health check by ID - update ip_address
  amazon.aws.route53_health_check:
    id: 12345678-abcd-abcd-abcd-0fxxxxxxxxxx
    ip_address: 1.2.3.4

- name: Update Health check by ID - update port
  amazon.aws.route53_health_check:
    id: 12345678-abcd-abcd-abcd-0fxxxxxxxxxx
    ip_address: 8080

- name: Delete Health check by ID
  amazon.aws.route53_health_check:
    state: absent
    id: 12345678-abcd-abcd-abcd-0fxxxxxxxxxx
"""

RETURN = r"""
health_check:
  description: Information about the health check.
  returned: success
  type: dict
  contains:
    action:
      description: The action performed by the module.
      type: str
      returned: When a change is or would be made.
      sample: 'updated'
    id:
      description: The Unique ID assigned by AWS to the health check.
      type: str
      returned: When the health check exists.
      sample: 50ec8a13-9623-4c66-9834-dd8c5aedc9ba
    health_check_version:
      description: The version number of the health check.
      type: int
      returned: When the health check exists.
      sample: 14
    health_check_config:
      description:
        - Detailed information about the health check.
        - May contain additional values from Route 53 health check
          features not yet supported by this module.
      type: dict
      returned: When the health check exists.
      contains:
        type:
          description: The type of the health check.
          type: str
          returned: When the health check exists.
          sample: 'HTTPS_STR_MATCH'
        failure_threshold:
          description:
            - The number of consecutive health checks that an endpoint must pass or fail for Amazon Route 53 to
              change the current status of the endpoint from unhealthy to healthy or vice versa.
          type: int
          returned: When the health check exists.
          sample: 3
        fully_qualified_domain_name:
          description: The FQDN configured for the health check to test.
          type: str
          returned: When the health check exists and an FQDN is configured.
          sample: 'updated'
        ip_address:
          description: The IPv4 or IPv6 IP address of the endpoint to be queried.
          type: str
          returned: When the health check exists and a specific IP address is configured.
          sample: ''
        port:
          description: The port on the endpoint that the health check will query.
          type: str
          returned: When the health check exists.
          sample: 'updated'
        request_interval:
          description: The number of seconds between health check queries.
          type: int
          returned: When the health check exists.
          sample: 30
        resource_path:
          description: The URI path to query when performing an HTTP/HTTPS based health check.
          type: str
          returned: When the health check exists and a resource path has been configured.
          sample: '/healthz'
        search_string:
          description: A string that must be present in the response for a health check to be considered successful.
          type: str
          returned: When the health check exists and a search string has been configured.
          sample: 'ALIVE'
        disabled:
          description: Whether the health check has been disabled or not.
          type: bool
          returned: When the health check exists.
          sample: false
    tags:
      description: A dictionary representing the tags on the health check.
      type: dict
      returned: When the health check exists.
      sample: '{"my_key": "my_value"}'
"""

import uuid

try:
    import botocore
except ImportError:
    pass  # Handled by HAS_BOTO

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.route53 import get_tags
from ansible_collections.amazon.aws.plugins.module_utils.route53 import manage_tags


def _list_health_checks(**params):
    try:
        results = client.list_health_checks(aws_retry=True, **params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to list health checks")
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
        for check in results.get("HealthChecks"):
            config = check.get("HealthCheckConfig")
            if (
                config.get("IPAddress", None) == ip_addr
                and config.get("FullyQualifiedDomainName", None) == fqdn
                and config.get("Type") == hc_type
                and config.get("RequestInterval") == request_interval
                and config.get("Port", None) == port
            ):
                return check

        if results.get("IsTruncated", False):
            results = _list_health_checks(Marker=results.get("NextMarker"))
        else:
            return None


def get_existing_checks_with_name():
    results = _list_health_checks()
    health_checks_with_name = {}
    while True:
        for check in results.get("HealthChecks"):
            if "Name" in describe_health_check(check["Id"])["tags"]:
                check_name = describe_health_check(check["Id"])["tags"]["Name"]
                health_checks_with_name[check_name] = check
        if results.get("IsTruncated", False):
            results = _list_health_checks(Marker=results.get("NextMarker"))
        else:
            return health_checks_with_name


def delete_health_check(check_id):
    if not check_id:
        return False, None

    if module.check_mode:
        return True, "delete"

    try:
        client.delete_health_check(
            aws_retry=True,
            HealthCheckId=check_id,
        )
    except is_boto3_error_code("NoSuchHealthCheck"):
        # Handle the deletion race condition as cleanly as possible
        return False, None
    except (
        botocore.exceptions.ClientError,
        botocore.exceptions.BotoCoreError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to list health checks")

    return True, "delete"


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
    if module.params.get("disabled") is not None:
        health_check["Disabled"] = module.params.get("disabled")
    if ip_addr_in:
        health_check["IPAddress"] = ip_addr_in
    if fqdn_in:
        health_check["FullyQualifiedDomainName"] = fqdn_in

    if type_in in ["HTTP", "HTTPS", "HTTP_STR_MATCH", "HTTPS_STR_MATCH"]:
        resource_path = module.params.get("resource_path")
        # if not resource_path:
        #     missing_args.append('resource_path')
        if resource_path:
            health_check["ResourcePath"] = resource_path
    if type_in in ["HTTP_STR_MATCH", "HTTPS_STR_MATCH"]:
        string_match = module.params.get("string_match")
        if not string_match:
            missing_args.append("string_match")
        health_check["SearchString"] = module.params.get("string_match")

    failure_threshold = module.params.get("failure_threshold")
    if not failure_threshold:
        failure_threshold = 3
    health_check["FailureThreshold"] = failure_threshold

    if module.params.get("measure_latency") is not None:
        health_check["MeasureLatency"] = module.params.get("measure_latency")

    if missing_args:
        module.fail_json(
            msg=f"missing required arguments for creation: {', '.join(missing_args)}",
        )

    if module.check_mode:
        return True, "create", None

    try:
        result = client.create_health_check(
            aws_retry=True,
            CallerReference=caller_ref,
            HealthCheckConfig=health_check,
        )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to create health check.", health_check=health_check)

    check_id = result.get("HealthCheck").get("Id")
    return True, "create", check_id


def update_health_check(existing_check):
    # It's possible to update following parameters
    # - ResourcePath
    # - SearchString
    # - FailureThreshold
    # - Disabled
    # - IPAddress
    # - Port
    # - FullyQualifiedDomainName

    changes = dict()
    existing_config = existing_check.get("HealthCheckConfig")
    check_id = existing_check.get("Id")

    resource_path = module.params.get("resource_path", None)
    if resource_path and resource_path != existing_config.get("ResourcePath"):
        changes["ResourcePath"] = resource_path

    search_string = module.params.get("string_match", None)
    if search_string and search_string != existing_config.get("SearchString"):
        changes["SearchString"] = search_string

    failure_threshold = module.params.get("failure_threshold", None)
    if failure_threshold and failure_threshold != existing_config.get("FailureThreshold"):
        changes["FailureThreshold"] = failure_threshold

    disabled = module.params.get("disabled", None)
    if disabled is not None and disabled != existing_config.get("Disabled"):
        changes["Disabled"] = module.params.get("disabled")

    # If updating based on Health Check ID or health_check_name, we can update
    if module.params.get("health_check_id") or module.params.get("use_unique_names"):
        ip_address = module.params.get("ip_address", None)
        if ip_address is not None and ip_address != existing_config.get("IPAddress"):
            changes["IPAddress"] = module.params.get("ip_address")

        port = module.params.get("port", None)
        if port is not None and port != existing_config.get("Port"):
            changes["Port"] = module.params.get("port")

        fqdn = module.params.get("fqdn", None)
        if fqdn is not None and fqdn != existing_config.get("FullyQualifiedDomainName"):
            changes["FullyQualifiedDomainName"] = module.params.get("fqdn")

    # No changes...
    if not changes:
        return False, None, check_id
    if module.check_mode:
        return True, "update", check_id

    # This makes sure we're starting from the version we think we are...
    version_id = existing_check.get("HealthCheckVersion", 1)
    try:
        client.update_health_check(
            HealthCheckId=check_id,
            HealthCheckVersion=version_id,
            **changes,
        )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to update health check.", id=check_id)

    return True, "update", check_id


def describe_health_check(id):
    if not id:
        return dict()

    try:
        result = client.get_health_check(
            aws_retry=True,
            HealthCheckId=id,
        )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to get health check.", id=id)

    health_check = result.get("HealthCheck", {})
    health_check = camel_dict_to_snake_dict(health_check)
    tags = get_tags(module, client, "healthcheck", id)
    health_check["tags"] = tags
    return health_check


def main():
    argument_spec = dict(
        state=dict(choices=["present", "absent"], default="present"),
        disabled=dict(type="bool"),
        ip_address=dict(),
        port=dict(type="int"),
        type=dict(choices=["HTTP", "HTTPS", "HTTP_STR_MATCH", "HTTPS_STR_MATCH", "TCP"]),
        resource_path=dict(),
        fqdn=dict(),
        string_match=dict(),
        request_interval=dict(type="int", choices=[10, 30], default=30),
        failure_threshold=dict(type="int", choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        health_check_id=dict(type="str", aliases=["id"], required=False),
        health_check_name=dict(type="str", aliases=["name"], required=False),
        use_unique_names=dict(type="bool", required=False),
        measure_latency=dict(type="bool", required=False),
    )

    args_one_of = [
        ["ip_address", "fqdn", "health_check_id"],
    ]

    args_if = [
        ["type", "TCP", ("port",)],
    ]

    args_required_together = [
        ["use_unique_names", "health_check_name"],
    ]

    args_mutually_exclusive = [
        ["health_check_id", "health_check_name"],
    ]

    global module
    global client

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_one_of=args_one_of,
        required_if=args_if,
        required_together=args_required_together,
        mutually_exclusive=args_mutually_exclusive,
        supports_check_mode=True,
    )

    if not module.params.get("health_check_id") and not module.params.get("type"):
        module.fail_json(msg="parameter 'type' is required if not updating or deleting health check by ID.")

    state_in = module.params.get("state")
    ip_addr_in = module.params.get("ip_address")
    port_in = module.params.get("port")
    type_in = module.params.get("type")
    fqdn_in = module.params.get("fqdn")
    string_match_in = module.params.get("string_match")
    request_interval_in = module.params.get("request_interval")
    health_check_name = module.params.get("health_check_name")
    tags = module.params.get("tags")
    purge_tags = module.params.get("purge_tags")

    # Default port
    if port_in is None:
        if type_in in ["HTTP", "HTTP_STR_MATCH"]:
            port_in = 80
        elif type_in in ["HTTPS", "HTTPS_STR_MATCH"]:
            port_in = 443

    if string_match_in:
        if type_in not in ["HTTP_STR_MATCH", "HTTPS_STR_MATCH"]:
            module.fail_json(msg="parameter 'string_match' argument is only for the HTTP(S)_STR_MATCH types")
        if len(string_match_in) > 255:
            module.fail_json(msg="parameter 'string_match' is limited to 255 characters max")

    client = module.client("route53", retry_decorator=AWSRetry.jittered_backoff())

    changed = False
    action = None
    check_id = None

    # If update or delete Health Check based on ID
    update_delete_by_id = False
    if module.params.get("health_check_id"):
        update_delete_by_id = True
        id_to_update_delete = module.params.get("health_check_id")
        try:
            existing_check = client.get_health_check(HealthCheckId=id_to_update_delete)["HealthCheck"]
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.exit_json(
                changed=False, msg=f"The specified health check with ID: {id_to_update_delete} does not exist"
            )
    else:
        existing_check = find_health_check(ip_addr_in, fqdn_in, type_in, request_interval_in, port_in)
        if existing_check:
            check_id = existing_check.get("Id")

    # Delete Health Check
    if state_in == "absent":
        if update_delete_by_id:
            changed, action = delete_health_check(id_to_update_delete)
        else:
            changed, action = delete_health_check(check_id)
        check_id = None

    # Create Health Check
    elif state_in == "present":
        if existing_check is None and not module.params.get("use_unique_names") and not update_delete_by_id:
            changed, action, check_id = create_health_check(ip_addr_in, fqdn_in, type_in, request_interval_in, port_in)

        # Update Health Check
        else:
            # If health_check_name is a unique identifier
            if module.params.get("use_unique_names"):
                existing_checks_with_name = get_existing_checks_with_name()
                if tags is None:
                    purge_tags = False
                    tags = {}
                tags["Name"] = health_check_name

                # update the health_check if another health check with same name exists
                if health_check_name in existing_checks_with_name:
                    changed, action, check_id = update_health_check(existing_checks_with_name[health_check_name])
                else:
                    # create a new health_check if another health check with same name does not exists
                    changed, action, check_id = create_health_check(
                        ip_addr_in, fqdn_in, type_in, request_interval_in, port_in
                    )

            else:
                changed, action, check_id = update_health_check(existing_check)

        if check_id:
            changed |= manage_tags(module, client, "healthcheck", check_id, tags, purge_tags)

    health_check = describe_health_check(id=check_id)
    health_check["action"] = action
    module.exit_json(
        changed=changed,
        health_check=health_check,
    )


if __name__ == "__main__":
    main()
