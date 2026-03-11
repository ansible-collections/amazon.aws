#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
---
module: route53_health_check
version_added: 5.0.0
short_description: Manage health checks in Amazons Route 53 DNS service
description:
  - Creates and deletes DNS Health checks in Amazons Route 53 service.
  - Only the O(port), O(resource_path), O(string_match) and O(request_interval) are
    considered when updating existing health checks.
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
      - Defaults to V(true) when creating a new health check.
    type: bool
    version_added: 2.1.0
    version_added_collection: community.aws
  ip_address:
    description:
      - IP address of the end-point to check. Either this or O(fqdn) has to be provided.
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
      - Once health check is created, type can not be changed.
      - The V(CALCULATED) choice was added in 6.3.0.
    choices: [ 'HTTP', 'HTTPS', 'HTTP_STR_MATCH', 'HTTPS_STR_MATCH', 'TCP', 'CALCULATED' ]
    type: str
  child_health_checks:
    description:
      - The child health checks used for a calculated health check.
      - This parameter takes in the child health checks ids.
    type: list
    elements: str
    version_added: 6.3.0
  health_threshold:
    description:
      - The minimum number of healthy child health checks for a calculated health check to be considered healthy.
    default: 1
    type: int
    version_added: 6.3.0
  resource_path:
    description:
      - The path that you want Amazon Route 53 to request when performing
        health checks. The path can be any value for which your endpoint will
        return an HTTP status code of 2xx or 3xx when the endpoint is healthy,
        for example the file /docs/route53-health-check.html.
      - Mutually exclusive with O(type='TCP').
      - The path must begin with a /
      - Maximum 255 characters.
    type: str
  fqdn:
    description:
      - Domain name of the endpoint to check. Either this or O(ip_address) has
        to be provided. When both are given the O(fqdn) is used in the V(Host:)
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
        health check request.
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
      - Used together with O(use_unique_names) to set/make use of O(health_check_name) as a unique identifier.
    type: str
    required: false
    aliases: ['name']
    version_added: 4.1.0
    version_added_collection: community.aws
  use_unique_names:
    description:
      - Used together with O(health_check_name) to set/make use of O(health_check_name) as a unique identifier.
    type: bool
    required: false
    version_added: 4.1.0
    version_added_collection: community.aws
  health_check_id:
    description:
      - ID of the health check to be update or deleted.
      - If provided, a health check can be updated or deleted based on the ID as unique identifier.
    type: str
    required: false
    aliases: ['id']
    version_added: 4.1.0
    version_added_collection: community.aws
  measure_latency:
    description:
      - To enable/disable latency graphs to monitor the latency between health checkers in multiple Amazon Web Services regions and your endpoint.
      - Value of O(measure_latency) is immutable and can not be modified after creating a health check.
        See U(https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/monitoring-health-check-latency.html)
    type: bool
    required: false
    version_added: 5.4.0
author:
  - "zimbatm (@zimbatm)"
notes:
  - Support for O(tags) and O(purge_tags) was added in release 2.1.0.
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: Create a health check for host1.example.com and use it in record
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

- name: Delete health check
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
        enable_sni:
          description: This allows the endpoint to respond to HTTPS health check requests with the applicable SSL/TLS certificate.
          type: bool
          returned: When the health check exists.
          sample: false
        inverted:
          description: Specify whether you want Amazon Route 53 to invert the status of a health check.
          type: bool
          returned: When the health check exists.
          sample: false
        measure_latency:
          description:
          - To enable/disable latency graphs to monitor the latency between health checkers in multiple Amazon Web Services regions and your endpoint.
          type: bool
          returned: When the health check exists.
          sample: false
    tags:
      description: A dictionary representing the tags on the health check.
      type: dict
      returned: When the health check exists.
      sample: '{"my_key": "my_value"}'
"""

import typing
import uuid

if typing.TYPE_CHECKING:
    from typing import Any

    from ansible_collections.amazon.aws.plugins.module_utils.botocore import ClientType

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.route53 import AnsibleRoute53Error
from ansible_collections.amazon.aws.plugins.module_utils.route53 import Route53ErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils.route53 import get_tags
from ansible_collections.amazon.aws.plugins.module_utils.route53 import manage_tags


@Route53ErrorHandler.list_error_handler("list health checks")
@AWSRetry.jittered_backoff()
def _list_health_checks(client: ClientType, **params) -> dict[str, Any]:
    return client.list_health_checks(**params)


@Route53ErrorHandler.deletion_error_handler("delete health check")
@AWSRetry.jittered_backoff()
def _delete_health_check(client: ClientType, check_id: str) -> None:
    # This always returns an empty dict, we don't control the API
    client.delete_health_check(
        HealthCheckId=check_id,
    )


@Route53ErrorHandler.common_error_handler("create health check")
@AWSRetry.jittered_backoff()
def _create_health_check(client: ClientType, caller_ref: str, health_check: dict[str, Any]) -> dict[str, Any]:
    return client.create_health_check(
        CallerReference=caller_ref,
        HealthCheckConfig=health_check,
    )


@Route53ErrorHandler.common_error_handler("update health check")
@AWSRetry.jittered_backoff()
def _update_health_check(client: ClientType, check_id: str, **kwargs) -> dict[str, Any]:
    return client.update_health_check(
        HealthCheckId=check_id,
        **kwargs,
    )


@Route53ErrorHandler.list_error_handler("get health check", default_value=None)
@AWSRetry.jittered_backoff()
def _get_health_check(client: ClientType, check_id: str) -> dict[str, Any] | None:
    return client.get_health_check(
        HealthCheckId=check_id,
    )


def iter_health_checks(client: ClientType):
    """Generator that yields all health checks, handling pagination.

    Args:
        client: The Route53 boto3 client

    Yields:
        Health check dictionaries from AWS API

    Note:
        Because Route53 provides no 'filter' mechanism, using a paginator
        would result in (on average) double the number of API calls and
        can get really slow. Additionally, we can't properly wrap the
        paginator, so retrying means starting from scratch with a paginator.
    """
    results = _list_health_checks(client)
    while True:
        yield from results.get("HealthChecks", [])

        if results.get("IsTruncated", False):
            results = _list_health_checks(client, Marker=results.get("NextMarker"))
        else:
            break


def find_health_check(
    client: ClientType,
    ip_addr: str | None,
    fqdn: str | None,
    hc_type: str,
    request_interval: int,
    port: int | None,
) -> dict[str, Any] | None:
    """Searches for health checks that have the exact same set of immutable values.

    Searches across all health checks for one matching the following immutable values:
    - ip_addr
    - fqdn
    - type (immutable)
    - request_interval
    - port

    Args:
        client: The Route53 boto3 client
        ip_addr: IP address to match
        fqdn: Fully qualified domain name to match
        hc_type: Health check type to match
        request_interval: Request interval to match
        port: Port to match

    Returns:
        Health check dict if found, None otherwise
    """
    for check in iter_health_checks(client):
        config = check.get("HealthCheckConfig")
        if (
            config.get("IPAddress", None) == ip_addr
            and config.get("FullyQualifiedDomainName", None) == fqdn
            and config.get("Type") == hc_type
            and config.get("RequestInterval") == request_interval
            and config.get("Port", None) == port
        ):
            return check

    return None


def get_existing_checks_with_name(client: ClientType) -> dict[str, dict[str, Any]]:
    """Get all health checks that have a Name tag.

    Args:
        client: The Route53 boto3 client

    Returns:
        Dictionary mapping health check names to health check dicts
    """
    health_checks_with_name = {}
    for check in iter_health_checks(client):
        tags = describe_health_check(client, check["Id"])["tags"]
        if "Name" in tags:
            health_checks_with_name[tags["Name"]] = check

    return health_checks_with_name


def delete_health_check(client: ClientType, check_id: str | None, check_mode: bool) -> tuple[bool, str | None]:
    """Delete a health check.

    Args:
        client: The Route53 boto3 client
        check_id: The health check ID to delete
        check_mode: Whether running in check mode

    Returns:
        Tuple of (changed, action)
    """
    if not check_id:
        return False, None

    if check_mode:
        return True, "delete"

    _delete_health_check(client, check_id)

    return True, "delete"


def validate_health_check_creation_params(
    healthcheck_type: str,
    string_match: str | None,
    child_health_checks: list[str] | None,
    health_threshold: int | None,
) -> None:
    """Validate that required parameters are present for health check creation.

    Args:
        healthcheck_type: Health check type
        string_match: Search string for STR_MATCH types
        child_health_checks: List of child health check IDs for CALCULATED type
        health_threshold: Minimum healthy children for CALCULATED type

    Raises:
        AnsibleRoute53Error: If required parameters are missing for the given type
    """
    missing_args = []

    if healthcheck_type in ["HTTP_STR_MATCH", "HTTPS_STR_MATCH"] and not string_match:
        missing_args.append("string_match")

    if healthcheck_type == "CALCULATED":
        if not child_health_checks:
            missing_args.append("child_health_checks")
        if not health_threshold:
            missing_args.append("health_threshold")

    if missing_args:
        raise AnsibleRoute53Error(message=f"missing required arguments for creation: {', '.join(missing_args)}")


def build_health_check_config(
    params: dict[str, Any],
    ip_addr: str | None,
    fqdn: str | None,
    healthcheck_type: str,
    request_interval: int,
    port: int | None,
    child_health_checks: list[str] | None,
    health_threshold: int | None,
) -> dict[str, Any]:
    """Build the health check configuration dictionary.

    Args:
        params: Module parameters dict
        ip_addr: IP address to check
        fqdn: Fully qualified domain name to check
        healthcheck_type: Health check type (HTTP, HTTPS, TCP, CALCULATED, etc.)
        request_interval: Request interval in seconds
        port: Port number to check
        child_health_checks: List of child health check IDs (for CALCULATED type)
        health_threshold: Minimum healthy children threshold (for CALCULATED type)

    Returns:
        Health check configuration dictionary
    """
    health_check = {"Type": healthcheck_type}

    if params.get("disabled") is not None:
        health_check["Disabled"] = params.get("disabled")
    if ip_addr:
        health_check["IPAddress"] = ip_addr
    if fqdn:
        health_check["FullyQualifiedDomainName"] = fqdn
    if port:
        health_check["Port"] = port

    if healthcheck_type in ["HTTP", "HTTPS", "HTTP_STR_MATCH", "HTTPS_STR_MATCH"]:
        resource_path = params.get("resource_path")
        if resource_path:
            health_check["ResourcePath"] = resource_path

    if healthcheck_type in ["HTTP_STR_MATCH", "HTTPS_STR_MATCH"]:
        health_check["SearchString"] = params.get("string_match")

    if healthcheck_type == "CALCULATED":
        health_check["ChildHealthChecks"] = child_health_checks
        health_check["HealthThreshold"] = health_threshold
    else:
        health_check["FailureThreshold"] = params.get("failure_threshold") or 3
        health_check["RequestInterval"] = request_interval

    if params.get("measure_latency") is not None:
        health_check["MeasureLatency"] = params.get("measure_latency")

    return health_check


def create_health_check(
    params: dict[str, Any],
    client: ClientType,
    check_mode: bool,
    ip_addr_in: str | None,
    fqdn_in: str | None,
    type_in: str,
    request_interval_in: int,
    port_in: int | None,
    child_health_checks_in: list[str] | None,
    health_threshold_in: int | None,
) -> tuple[bool, str, str | None]:
    """Create a new health check.

    Args:
        params: Module parameters dict
        client: The Route53 boto3 client
        check_mode: Whether running in check mode
        ip_addr_in: IP address to check
        fqdn_in: Fully qualified domain name to check
        type_in: Health check type
        request_interval_in: Request interval in seconds
        port_in: Port number to check
        child_health_checks_in: List of child health check IDs
        health_threshold_in: Minimum healthy children threshold

    Returns:
        Tuple of (changed, action, check_id)
    """
    # In general, if a request is repeated with the same CallerRef it won't
    # result in a duplicate check appearing.  This means we can safely use our
    # retry decorators
    caller_ref = str(uuid.uuid4())

    validate_health_check_creation_params(
        type_in,
        params.get("string_match"),
        child_health_checks_in,
        health_threshold_in,
    )

    health_check = build_health_check_config(
        params,
        ip_addr_in,
        fqdn_in,
        type_in,
        request_interval_in,
        port_in,
        child_health_checks_in,
        health_threshold_in,
    )

    if check_mode:
        return True, "create", None

    result = _create_health_check(client, caller_ref, health_check)

    check_id = result.get("HealthCheck").get("Id")
    return True, "create", check_id


def build_health_check_changes(params: dict[str, Any], existing_check: dict[str, Any]) -> dict[str, Any]:
    """Build dictionary of changes needed to update a health check.

    Compares the desired parameters against the existing health check configuration
    and returns only the fields that need to be updated.

    Updatable fields:
    - ResourcePath
    - SearchString
    - FailureThreshold
    - Disabled
    - IPAddress (only with health_check_id or use_unique_names)
    - Port (only with health_check_id or use_unique_names)
    - FullyQualifiedDomainName (only with health_check_id or use_unique_names)
    - ChildHealthChecks (only with health_check_id or use_unique_names)
    - HealthThreshold (only with health_check_id or use_unique_names)

    Args:
        params: Module parameters dict with desired state
        existing_check: Existing health check data from AWS API

    Returns:
        Dictionary of changes to apply, empty dict if no changes needed
    """
    changes = {}
    existing_config = existing_check.get("HealthCheckConfig", {})

    # Always updatable fields
    resource_path = params.get("resource_path", None)
    if resource_path and resource_path != existing_config.get("ResourcePath"):
        changes["ResourcePath"] = resource_path

    search_string = params.get("string_match", None)
    if search_string and search_string != existing_config.get("SearchString"):
        changes["SearchString"] = search_string

    type_in = params.get("type", None)
    if type_in != "CALCULATED":
        failure_threshold = params.get("failure_threshold", None)
        if failure_threshold and failure_threshold != existing_config.get("FailureThreshold"):
            changes["FailureThreshold"] = failure_threshold

    disabled = params.get("disabled", None)
    if disabled is not None and disabled != existing_config.get("Disabled"):
        changes["Disabled"] = disabled

    # Immutable fields can only be updated when using health_check_id or use_unique_names
    if params.get("health_check_id") or params.get("use_unique_names"):
        ip_address = params.get("ip_address", None)
        if ip_address is not None and ip_address != existing_config.get("IPAddress"):
            changes["IPAddress"] = ip_address

        port = params.get("port", None)
        if port is not None and port != existing_config.get("Port"):
            changes["Port"] = port

        fqdn = params.get("fqdn", None)
        if fqdn is not None and fqdn != existing_config.get("FullyQualifiedDomainName"):
            changes["FullyQualifiedDomainName"] = fqdn

        if type_in == "CALCULATED":
            child_health_checks = params.get("child_health_checks", None)
            if child_health_checks is not None and child_health_checks != existing_config.get("ChildHealthChecks"):
                changes["ChildHealthChecks"] = child_health_checks

            health_threshold = params.get("health_threshold", None)
            if health_threshold is not None and health_threshold != existing_config.get("HealthThreshold"):
                changes["HealthThreshold"] = health_threshold

    return changes


def update_health_check(
    params: dict[str, Any], client: ClientType, check_mode: bool, existing_check: dict[str, Any]
) -> tuple[bool, str | None, str]:
    """Update an existing health check.

    Args:
        params: Module parameters dict
        client: The Route53 boto3 client
        check_mode: Whether running in check mode
        existing_check: Existing health check data from AWS API

    Returns:
        Tuple of (changed, action, check_id)
    """
    check_id = existing_check.get("Id")
    changes = build_health_check_changes(params, existing_check)

    # No changes needed
    if not changes:
        return False, None, check_id

    if check_mode:
        return True, "update", check_id

    # This makes sure we're starting from the version we think we are...
    version_id = existing_check.get("HealthCheckVersion", 1)
    _update_health_check(client, check_id, HealthCheckVersion=version_id, **changes)

    return True, "update", check_id


def describe_health_check(client: ClientType, check_id: str | None) -> dict[str, Any]:
    """Get detailed information about a health check including tags.

    Args:
        client: The Route53 boto3 client
        check_id: Health check ID to describe

    Returns:
        Dictionary containing health check details and tags, or empty dict if not found
    """
    if not check_id:
        return {}

    result = _get_health_check(client, check_id)
    if not result:
        return {}

    health_check = result.get("HealthCheck", {})
    health_check = camel_dict_to_snake_dict(health_check)
    tags = get_tags(client, "healthcheck", check_id)
    health_check["tags"] = tags
    return health_check


def ensure_absent(module, client: ClientType, port_in: int | None) -> tuple[bool, str | None, None]:
    """Handles deletion of a health check.

    Args:
        module: AnsibleAWSModule instance
        client: The Route53 boto3 client
        port_in: Port number (if applicable)

    Returns:
        Tuple of (changed, action, check_id) where check_id is always None for deletions
    """
    check_id_from_param = module.params.get("health_check_id")

    if check_id_from_param:
        result = _get_health_check(client, check_id_from_param)
        if not result:
            module.exit_json(
                changed=False, msg=f"The specified health check with ID: {check_id_from_param} does not exist"
            )

        changed, action = delete_health_check(client, check_id_from_param, module.check_mode)
        return changed, action, None

    existing_check = find_health_check(
        client,
        module.params.get("ip_address"),
        module.params.get("fqdn"),
        module.params.get("type"),
        module.params.get("request_interval"),
        port_in,
    )

    if not existing_check:
        return False, None, None

    check_id = existing_check.get("Id")
    changed, action = delete_health_check(client, check_id, module.check_mode)
    return changed, action, None


def ensure_present(module, client: ClientType, port_in: int | None) -> tuple[bool, str | None, str | None]:
    """Handles creation and updates of a health check.

    Args:
        module: AnsibleAWSModule instance
        client: The Route53 boto3 client
        port_in: Port number (if applicable)

    Returns:
        Tuple of (changed, action, check_id)
    """
    ip_addr_in = module.params.get("ip_address")
    type_in = module.params.get("type")
    fqdn_in = module.params.get("fqdn")
    request_interval_in = module.params.get("request_interval")
    child_health_checks_in = module.params.get("child_health_checks")
    health_threshold_in = module.params.get("health_threshold")
    health_check_name = module.params.get("health_check_name")
    tags = module.params.get("tags")
    use_unique_names = module.params.get("use_unique_names")
    health_check_id_in = module.params.get("health_check_id")

    # Track if user specified tags - needed to determine purge behavior later
    user_specified_tags = tags is not None

    existing_check = None
    if health_check_id_in:
        result = _get_health_check(client, health_check_id_in)
        if not result:
            raise AnsibleRoute53Error(
                message=f"The specified health check with ID: {health_check_id_in} does not exist"
            )
        existing_check = result["HealthCheck"]
    elif not use_unique_names:
        existing_check = find_health_check(
            client,
            module.params.get("ip_address"),
            module.params.get("fqdn"),
            module.params.get("type"),
            module.params.get("request_interval"),
            port_in,
        )

    if use_unique_names:
        existing_checks_with_name = get_existing_checks_with_name(client)
        if tags is None:
            tags = {}
        tags["Name"] = health_check_name

        if health_check_name in existing_checks_with_name:
            changed, action, check_id = update_health_check(
                module.params, client, module.check_mode, existing_checks_with_name[health_check_name]
            )
        else:
            changed, action, check_id = create_health_check(
                module.params,
                client,
                module.check_mode,
                ip_addr_in,
                fqdn_in,
                type_in,
                request_interval_in,
                port_in,
                child_health_checks_in,
                health_threshold_in,
            )
    elif existing_check:
        changed, action, check_id = update_health_check(module.params, client, module.check_mode, existing_check)
    else:
        changed, action, check_id = create_health_check(
            module.params,
            client,
            module.check_mode,
            ip_addr_in,
            fqdn_in,
            type_in,
            request_interval_in,
            port_in,
            child_health_checks_in,
            health_threshold_in,
        )

    if check_id:
        # When use_unique_names is true and user didn't specify tags,
        # we only want to ensure Name tag exists, not purge other tags
        purge_tags = module.params.get("purge_tags") if user_specified_tags else False
        changed |= manage_tags(client, "healthcheck", check_id, tags, purge_tags, module.check_mode)

    return changed, action, check_id


def validate_parameters(params: dict[str, Any]) -> int | None:
    """Validates module parameters and returns the calculated port.

    Args:
        params: Module parameters dict

    Returns:
        Calculated port number, or None if not applicable

    Raises:
        AnsibleRoute53Error: If parameters are invalid
    """
    if not params.get("health_check_id") and not params.get("type"):
        raise AnsibleRoute53Error(
            message="parameter 'type' is required if not updating or deleting health check by ID."
        )

    type_in = params.get("type")
    string_match_in = params.get("string_match")
    port_in = params.get("port")

    # Default port
    if port_in is None:
        if type_in in ["HTTP", "HTTP_STR_MATCH"]:
            port_in = 80
        elif type_in in ["HTTPS", "HTTPS_STR_MATCH"]:
            port_in = 443

    if string_match_in:
        if type_in not in ["HTTP_STR_MATCH", "HTTPS_STR_MATCH"]:
            raise AnsibleRoute53Error(
                message="parameter 'string_match' argument is only for the HTTP(S)_STR_MATCH types"
            )
        if len(string_match_in) > 255:
            raise AnsibleRoute53Error(message="parameter 'string_match' is limited to 255 characters max")

    return port_in


def main():
    argument_spec = dict(
        state=dict(choices=["present", "absent"], default="present"),
        disabled=dict(type="bool"),
        ip_address=dict(),
        port=dict(type="int"),
        type=dict(choices=["HTTP", "HTTPS", "HTTP_STR_MATCH", "HTTPS_STR_MATCH", "TCP", "CALCULATED"]),
        child_health_checks=dict(type="list", elements="str"),
        health_threshold=dict(type="int", default=1),
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
        ["ip_address", "fqdn", "health_check_id", "child_health_checks"],
    ]

    args_if = [
        ["type", "TCP", ("port",)],
        ["type", "CALCULATED", ("child_health_checks", "health_threshold")],
    ]

    args_required_together = [
        ["use_unique_names", "health_check_name"],
    ]

    args_mutually_exclusive = [
        ["health_check_id", "health_check_name"],
        ["child_health_checks", "ip_address"],
        ["child_health_checks", "port"],
        ["child_health_checks", "fqdn"],
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_one_of=args_one_of,
        required_if=args_if,
        required_together=args_required_together,
        mutually_exclusive=args_mutually_exclusive,
        supports_check_mode=True,
    )

    try:
        port_in = validate_parameters(module.params)

        state_in = module.params.get("state")
        client = module.client("route53", retry_decorator=AWSRetry.jittered_backoff())

        changed = False
        action = None
        check_id = None

        if state_in == "absent":
            changed, action, check_id = ensure_absent(module, client, port_in)
        elif state_in == "present":
            changed, action, check_id = ensure_present(module, client, port_in)

        health_check = describe_health_check(client, check_id)
        health_check["action"] = action
        module.exit_json(
            changed=changed,
            health_check=health_check,
        )
    except AnsibleRoute53Error as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
