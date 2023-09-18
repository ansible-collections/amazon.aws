#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: route53
version_added: 1.0.0
short_description: add or delete entries in Amazons Route 53 DNS service
description:
     - Creates and deletes DNS records in Amazons Route 53 service.
options:
  state:
    description:
      - Specifies the state of the resource record. As of Ansible 2.4, the I(command) option has been changed
        to I(state) as default and the choices C(present) and C(absent) have been added, but I(command) still works as well.
    required: true
    aliases: [ 'command' ]
    choices: [ 'present', 'absent', 'get', 'create', 'delete' ]
    type: str
  zone:
    description:
      - The DNS zone to modify.
      - This is a required parameter, if parameter I(hosted_zone_id) is not supplied.
    type: str
  hosted_zone_id:
    description:
      - The Hosted Zone ID of the DNS zone to modify.
      - This is a required parameter, if parameter I(zone) is not supplied.
    type: str
  record:
    description:
      - The full DNS record to create or delete.
    required: true
    type: str
  ttl:
    description:
      - The TTL, in second, to give the new record.
    default: 3600
    type: int
  type:
    description:
      - The type of DNS record to create.
    required: true
    choices: [ 'A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'CAA', 'NS', 'SOA' ]
    type: str
  alias:
    description:
      - Indicates if this is an alias record.
      - Defaults to C(false).
    type: bool
  alias_hosted_zone_id:
    description:
      - The hosted zone identifier.
    type: str
  alias_evaluate_target_health:
    description:
      - Whether or not to evaluate an alias target health. Useful for aliases to Elastic Load Balancers.
    type: bool
    default: false
  value:
    description:
      - The new value when creating a DNS record.  YAML lists or multiple comma-spaced values are allowed for non-alias records.
      - When deleting a record all values for the record must be specified or Route 53 will not delete it.
    type: list
    elements: str
  overwrite:
    description:
      - Whether an existing record should be overwritten on create if values do not match.
    type: bool
  retry_interval:
    description:
      - In the case that Route 53 is still servicing a prior request, this module will wait and try again after this many seconds.
        If you have many domain names, the default of C(500) seconds may be too long.
    default: 500
    type: int
  private_zone:
    description:
      - If set to C(true), the private zone matching the requested name within the domain will be used if there are both public and private zones.
      - The default is to use the public zone.
    type: bool
    default: false
  identifier:
    description:
      - Have to be specified for Weighted, latency-based and failover resource record sets only.
        An identifier that differentiates among multiple resource record sets that have the same combination of DNS name and type.
    type: str
  weight:
    description:
      - Weighted resource record sets only. Among resource record sets that
        have the same combination of DNS name and type, a value that
        determines what portion of traffic for the current resource record set
        is routed to the associated location.
    type: int
  region:
    description:
      - Latency-based resource record sets only Among resource record sets
        that have the same combination of DNS name and type, a value that
        determines which region this should be associated with for the
        latency-based routing
    type: str
  health_check:
    description:
      - Health check to associate with this record
    type: str
  failover:
    description:
      - Failover resource record sets only. Whether this is the primary or
        secondary resource record set. Allowed values are PRIMARY and SECONDARY
    type: str
    choices: ['SECONDARY', 'PRIMARY']
  vpc_id:
    description:
      - "When used in conjunction with private_zone: true, this will only modify records in the private hosted zone attached to this VPC."
      - This allows you to have multiple private hosted zones, all with the same name, attached to different VPCs.
    type: str
  wait:
    description:
      - Wait until the changes have been replicated to all Amazon Route 53 DNS servers.
    type: bool
    default: false
  wait_timeout:
    description:
      - How long to wait for the changes to be replicated, in seconds.
    default: 300
    type: int
author:
- Bruce Pennypacker (@bpennypacker)
- Mike Buzzetti (@jimbydamonk)
extends_documentation_fragment:
- amazon.aws.aws

'''

RETURN = r'''
nameservers:
  description: Nameservers associated with the zone.
  returned: when state is 'get'
  type: list
  sample:
  - ns-1036.awsdns-00.org.
  - ns-516.awsdns-00.net.
  - ns-1504.awsdns-00.co.uk.
  - ns-1.awsdns-00.com.
set:
  description: Info specific to the resource record.
  returned: when state is 'get'
  type: complex
  contains:
    alias:
      description: Whether this is an alias.
      returned: always
      type: bool
      sample: false
    failover:
      description: Whether this is the primary or secondary resource record set.
      returned: always
      type: str
      sample: PRIMARY
    health_check:
      description: health_check associated with this record.
      returned: always
      type: str
    identifier:
      description: An identifier that differentiates among multiple resource record sets that have the same combination of DNS name and type.
      returned: always
      type: str
    record:
      description: Domain name for the record set.
      returned: always
      type: str
      sample: new.foo.com.
    region:
      description: Which region this should be associated with for latency-based routing.
      returned: always
      type: str
      sample: us-west-2
    ttl:
      description: Resource record cache TTL.
      returned: always
      type: str
      sample: '3600'
    type:
      description: Resource record set type.
      returned: always
      type: str
      sample: A
    value:
      description: Record value.
      returned: always
      type: str
      sample: 52.43.18.27
    values:
      description: Record Values.
      returned: always
      type: list
      sample:
      - 52.43.18.27
    weight:
      description: Weight of the record.
      returned: always
      type: str
      sample: '3'
    zone:
      description: Zone this record set belongs to.
      returned: always
      type: str
      sample: foo.bar.com.
'''

EXAMPLES = r'''
- name: Add new.foo.com as an A record with 3 IPs and wait until the changes have been replicated
  community.aws.route53:
    state: present
    zone: foo.com
    record: new.foo.com
    type: A
    ttl: 7200
    value: 1.1.1.1,2.2.2.2,3.3.3.3
    wait: yes

- name: Update new.foo.com as an A record with a list of 3 IPs and wait until the changes have been replicated
  community.aws.route53:
    state: present
    zone: foo.com
    record: new.foo.com
    type: A
    ttl: 7200
    value:
      - 1.1.1.1
      - 2.2.2.2
      - 3.3.3.3
    wait: yes

- name: Retrieve the details for new.foo.com
  community.aws.route53:
    state: get
    zone: foo.com
    record: new.foo.com
    type: A
  register: rec

- name: Delete new.foo.com A record using the results from the get command
  community.aws.route53:
    state: absent
    zone: foo.com
    record: "{{ rec.set.record }}"
    ttl: "{{ rec.set.ttl }}"
    type: "{{ rec.set.type }}"
    value: "{{ rec.set.value }}"

# Add an AAAA record.  Note that because there are colons in the value
# that the IPv6 address must be quoted. Also shows using the old form command=create.
- name: Add an AAAA record
  community.aws.route53:
    command: create
    zone: foo.com
    record: localhost.foo.com
    type: AAAA
    ttl: 7200
    value: "::1"

# For more information on SRV records see:
# https://en.wikipedia.org/wiki/SRV_record
- name: Add a SRV record with multiple fields for a service on port 22222
  community.aws.route53:
    state: present
    zone: foo.com
    record: "_example-service._tcp.foo.com"
    type: SRV
    value: "0 0 22222 host1.foo.com,0 0 22222 host2.foo.com"

# Note that TXT and SPF records must be surrounded
# by quotes when sent to Route 53:
- name: Add a TXT record.
  community.aws.route53:
    state: present
    zone: foo.com
    record: localhost.foo.com
    type: TXT
    ttl: 7200
    value: '"bar"'

- name: Add an alias record that points to an Amazon ELB
  community.aws.route53:
    state: present
    zone: foo.com
    record: elb.foo.com
    type: A
    value: "{{ elb_dns_name }}"
    alias: True
    alias_hosted_zone_id: "{{ elb_zone_id }}"

- name: Retrieve the details for elb.foo.com
  community.aws.route53:
    state: get
    zone: foo.com
    record: elb.foo.com
    type: A
  register: rec

- name: Delete an alias record using the results from the get command
  community.aws.route53:
    state: absent
    zone: foo.com
    record: "{{ rec.set.record }}"
    ttl: "{{ rec.set.ttl }}"
    type: "{{ rec.set.type }}"
    value: "{{ rec.set.value }}"
    alias: True
    alias_hosted_zone_id: "{{ rec.set.alias_hosted_zone_id }}"

- name: Add an alias record that points to an Amazon ELB and evaluates it health
  community.aws.route53:
    state: present
    zone: foo.com
    record: elb.foo.com
    type: A
    value: "{{ elb_dns_name }}"
    alias: True
    alias_hosted_zone_id: "{{ elb_zone_id }}"
    alias_evaluate_target_health: True

- name: Add an AAAA record with Hosted Zone ID
  community.aws.route53:
    state: present
    zone: foo.com
    hosted_zone_id: Z2AABBCCDDEEFF
    record: localhost.foo.com
    type: AAAA
    ttl: 7200
    value: "::1"

- name: Use a routing policy to distribute traffic
  community.aws.route53:
    state: present
    zone: foo.com
    record: www.foo.com
    type: CNAME
    value: host1.foo.com
    ttl: 30
    # Routing policy
    identifier: "host1@www"
    weight: 100
    health_check: "d994b780-3150-49fd-9205-356abdd42e75"

- name: Add a CAA record (RFC 6844)
  community.aws.route53:
    state: present
    zone: example.com
    record: example.com
    type: CAA
    value:
      - 0 issue "ca.example.net"
      - 0 issuewild ";"
      - 0 iodef "mailto:security@example.com"

'''

import time
import distutils.version

try:
    import boto
    import boto.ec2
    from boto.route53 import Route53Connection
    from boto.route53.record import Record, ResourceRecordSets
    from boto.route53.status import Status
except ImportError:
    pass  # Handled by HAS_BOTO

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import get_aws_connection_info
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import HAS_BOTO


MINIMUM_BOTO_VERSION = '2.28.0'
WAIT_RETRY_SLEEP = 5  # how many seconds to wait between propagation status polls


class TimeoutError(Exception):
    pass


def get_zone_id_by_name(conn, module, zone_name, want_private, want_vpc_id):
    """Finds a zone by name or zone_id"""
    for zone in invoke_with_throttling_retries(conn.get_zones):
        # only save this zone id if the private status of the zone matches
        # the private_zone_in boolean specified in the params
        private_zone = module.boolean(zone.config.get('PrivateZone', False))
        if private_zone == want_private and zone.name == zone_name:
            if want_vpc_id:
                # NOTE: These details aren't available in other boto methods, hence the necessary
                # extra API call
                hosted_zone = invoke_with_throttling_retries(conn.get_hosted_zone, zone.id)
                zone_details = hosted_zone['GetHostedZoneResponse']
                # this is to deal with this boto bug: https://github.com/boto/boto/pull/2882
                if isinstance(zone_details['VPCs'], dict):
                    if zone_details['VPCs']['VPC']['VPCId'] == want_vpc_id:
                        return zone.id
                else:  # Forward compatibility for when boto fixes that bug
                    if want_vpc_id in [v['VPCId'] for v in zone_details['VPCs']]:
                        return zone.id
            else:
                return zone.id
    return None


def commit(changes, retry_interval, wait, wait_timeout):
    """Commit changes, but retry PriorRequestNotComplete errors."""
    result = None
    retry = 10
    while True:
        try:
            retry -= 1
            result = changes.commit()
            break
        except boto.route53.exception.DNSServerError as e:
            code = e.body.split("<Code>")[1]
            code = code.split("</Code>")[0]
            if code != 'PriorRequestNotComplete' or retry < 0:
                raise e
            time.sleep(float(retry_interval))

    if wait:
        timeout_time = time.time() + wait_timeout
        connection = changes.connection
        change = result['ChangeResourceRecordSetsResponse']['ChangeInfo']
        status = Status(connection, change)
        while status.status != 'INSYNC' and time.time() < timeout_time:
            time.sleep(WAIT_RETRY_SLEEP)
            status.update()
        if time.time() >= timeout_time:
            raise TimeoutError()
        return result


# Shamelessly copied over from https://git.io/vgmDG
IGNORE_CODE = 'Throttling'
MAX_RETRIES = 5


def invoke_with_throttling_retries(function_ref, *argv, **kwargs):
    retries = 0
    while True:
        try:
            retval = function_ref(*argv, **kwargs)
            return retval
        except boto.exception.BotoServerError as e:
            if e.code != IGNORE_CODE or retries == MAX_RETRIES:
                raise e
        time.sleep(5 * (2**retries))
        retries += 1


def decode_name(name):
    # Due to a bug in either AWS or Boto, "special" characters are returned as octals, preventing round
    # tripping of things like * and @.
    return name.encode().decode('unicode_escape')


def to_dict(rset, zone_in, zone_id):
    record = dict()
    record['zone'] = zone_in
    record['type'] = rset.type
    record['record'] = decode_name(rset.name)
    record['ttl'] = str(rset.ttl)
    record['identifier'] = rset.identifier
    record['weight'] = rset.weight
    record['region'] = rset.region
    record['failover'] = rset.failover
    record['health_check'] = rset.health_check
    record['hosted_zone_id'] = zone_id
    if rset.alias_dns_name:
        record['alias'] = True
        record['value'] = rset.alias_dns_name
        record['values'] = [rset.alias_dns_name]
        record['alias_hosted_zone_id'] = rset.alias_hosted_zone_id
        record['alias_evaluate_target_health'] = rset.alias_evaluate_target_health
    else:
        record['alias'] = False
        record['value'] = ','.join(sorted(rset.resource_records))
        record['values'] = sorted(rset.resource_records)
    return record


def main():
    argument_spec = dict(
        state=dict(type='str', required=True, choices=['absent', 'create', 'delete', 'get', 'present'], aliases=['command']),
        zone=dict(type='str'),
        hosted_zone_id=dict(type='str'),
        record=dict(type='str', required=True),
        ttl=dict(type='int', default=3600),
        type=dict(type='str', required=True, choices=['A', 'AAAA', 'CAA', 'CNAME', 'MX', 'NS', 'PTR', 'SOA', 'SPF', 'SRV', 'TXT']),
        alias=dict(type='bool'),
        alias_hosted_zone_id=dict(type='str'),
        alias_evaluate_target_health=dict(type='bool', default=False),
        value=dict(type='list', elements='str'),
        overwrite=dict(type='bool'),
        retry_interval=dict(type='int', default=500),
        private_zone=dict(type='bool', default=False),
        identifier=dict(type='str'),
        weight=dict(type='int'),
        region=dict(type='str'),
        health_check=dict(type='str'),
        failover=dict(type='str', choices=['PRIMARY', 'SECONDARY']),
        vpc_id=dict(type='str'),
        wait=dict(type='bool', default=False),
        wait_timeout=dict(type='int', default=300),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[['zone', 'hosted_zone_id']],
        # If alias is True then you must specify alias_hosted_zone as well
        required_together=[['alias', 'alias_hosted_zone_id']],
        # state=present, absent, create, delete THEN value is required
        required_if=(
            ('state', 'present', ['value']),
            ('state', 'create', ['value']),
            ('state', 'absent', ['value']),
            ('state', 'delete', ['value']),
        ),
        # failover, region and weight are mutually exclusive
        mutually_exclusive=[('failover', 'region', 'weight')],
        # failover, region and weight require identifier
        required_by=dict(
            failover=('identifier',),
            region=('identifier',),
            weight=('identifier',),
        ),
        check_boto3=False,
    )

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    if distutils.version.StrictVersion(boto.__version__) < distutils.version.StrictVersion(MINIMUM_BOTO_VERSION):
        module.fail_json(msg='Found boto in version %s, but >= %s is required' % (boto.__version__, MINIMUM_BOTO_VERSION))

    if module.params['state'] in ('present', 'create'):
        command_in = 'create'
    elif module.params['state'] in ('absent', 'delete'):
        command_in = 'delete'
    elif module.params['state'] == 'get':
        command_in = 'get'

    zone_in = (module.params.get('zone') or '').lower()
    hosted_zone_id_in = module.params.get('hosted_zone_id')
    ttl_in = module.params.get('ttl')
    record_in = module.params.get('record').lower()
    type_in = module.params.get('type')
    value_in = module.params.get('value') or []
    alias_in = module.params.get('alias')
    alias_hosted_zone_id_in = module.params.get('alias_hosted_zone_id')
    alias_evaluate_target_health_in = module.params.get('alias_evaluate_target_health')
    retry_interval_in = module.params.get('retry_interval')

    if module.params['vpc_id'] is not None:
        private_zone_in = True
    else:
        private_zone_in = module.params.get('private_zone')

    identifier_in = module.params.get('identifier')
    weight_in = module.params.get('weight')
    region_in = module.params.get('region')
    health_check_in = module.params.get('health_check')
    failover_in = module.params.get('failover')
    vpc_id_in = module.params.get('vpc_id')
    wait_in = module.params.get('wait')
    wait_timeout_in = module.params.get('wait_timeout')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module)

    if zone_in[-1:] != '.':
        zone_in += "."

    if record_in[-1:] != '.':
        record_in += "."

    if command_in == 'create' or command_in == 'delete':
        if alias_in and len(value_in) != 1:
            module.fail_json(msg="parameter 'value' must contain a single dns name for alias records")
        if (weight_in is None and region_in is None and failover_in is None) and identifier_in is not None:
            module.fail_json(msg="You have specified identifier which makes sense only if you specify one of: weight, region or failover.")

    # connect to the route53 endpoint
    try:
        conn = Route53Connection(**aws_connect_kwargs)
    except boto.exception.BotoServerError as e:
        module.fail_json(msg=e.error_message)

    # Find the named zone ID
    zone_id = hosted_zone_id_in or get_zone_id_by_name(conn, module, zone_in, private_zone_in, vpc_id_in)

    # Verify that the requested zone is already defined in Route53
    if zone_id is None:
        errmsg = "Zone %s does not exist in Route53" % (zone_in or hosted_zone_id_in)
        module.fail_json(msg=errmsg)

    record = {}

    found_record = False
    wanted_rset = Record(name=record_in, type=type_in, ttl=ttl_in,
                         identifier=identifier_in, weight=weight_in,
                         region=region_in, health_check=health_check_in,
                         failover=failover_in)
    for v in value_in:
        if alias_in:
            wanted_rset.set_alias(alias_hosted_zone_id_in, v, alias_evaluate_target_health_in)
        else:
            wanted_rset.add_value(v)

    need_to_sort_records = (type_in == 'CAA')

    # Sort records for wanted_rset if necessary (keep original list)
    unsorted_records = wanted_rset.resource_records
    if need_to_sort_records:
        wanted_rset.resource_records = sorted(unsorted_records)

    sets = invoke_with_throttling_retries(conn.get_all_rrsets, zone_id, name=record_in,
                                          type=type_in, identifier=identifier_in)
    sets_iter = iter(sets)
    while True:
        try:
            rset = invoke_with_throttling_retries(next, sets_iter)
        except StopIteration:
            break
        # Need to save this changes in rset, because of comparing rset.to_xml() == wanted_rset.to_xml() in next block
        rset.name = decode_name(rset.name)

        if identifier_in is not None:
            identifier_in = str(identifier_in)

        if rset.type == type_in and rset.name.lower() == record_in.lower() and rset.identifier == identifier_in:
            if need_to_sort_records:
                # Sort records
                rset.resource_records = sorted(rset.resource_records)
            found_record = True
            record = to_dict(rset, zone_in, zone_id)
            if command_in == 'create' and rset.to_xml() == wanted_rset.to_xml():
                module.exit_json(changed=False)

        # We need to look only at the first rrset returned by the above call,
        # so break here. The returned elements begin with the one matching our
        # requested name, type, and identifier, if such an element exists,
        # followed by all others that come after it in alphabetical order.
        # Therefore, if the first set does not match, no subsequent set will
        # match either.
        break

    if command_in == 'get':
        if type_in == 'NS':
            ns = record.get('values', [])
        else:
            # Retrieve name servers associated to the zone.
            z = invoke_with_throttling_retries(conn.get_zone, zone_in)
            ns = invoke_with_throttling_retries(z.get_nameservers)

        module.exit_json(changed=False, set=record, nameservers=ns)

    if command_in == 'delete' and not found_record:
        module.exit_json(changed=False)

    changes = ResourceRecordSets(conn, zone_id)

    if command_in == 'create' or command_in == 'delete':
        if command_in == 'create' and found_record:
            if not module.params['overwrite']:
                module.fail_json(msg="Record already exists with different value. Set 'overwrite' to replace it")
            command = 'UPSERT'
        else:
            command = command_in.upper()
        # Restore original order of records
        wanted_rset.resource_records = unsorted_records
        changes.add_change_record(command, wanted_rset)

    if not module.check_mode:
        try:
            invoke_with_throttling_retries(commit, changes, retry_interval_in, wait_in, wait_timeout_in)
        except boto.route53.exception.DNSServerError as e:
            txt = e.body.split("<Message>")[1]
            txt = txt.split("</Message>")[0]
            if "but it already exists" in txt:
                module.exit_json(changed=False)
            else:
                module.fail_json(msg=txt)
        except TimeoutError:
            module.fail_json(msg='Timeout waiting for changes to replicate')

    module.exit_json(
        changed=True,
        diff=dict(
            before=record,
            after=to_dict(wanted_rset, zone_in, zone_id) if command != 'delete' else {},
        ),
    )


if __name__ == '__main__':
    main()
