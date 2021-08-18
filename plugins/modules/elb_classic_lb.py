#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: elb_classic_lb
version_added: 1.0.0
description:
  - Creates, updates or destroys an Amazon Elastic Load Balancer (ELB).
  - This module was renamed from M(ec2_elb_lb) to M(elb_classic_lb) in version
    2.0.0 of the amazon.aws collection.
short_description: creates, updates or destroys an Amazon ELB.
author:
  - "Jim Dalton (@jsdalton)"
options:
  state:
    description:
      - Create or destroy the ELB.
    type: str
    choices: [ absent, present ]
    required: true
  name:
    description:
      - The name of the ELB.
    type: str
    required: true
  listeners:
    description:
      - List of ports/protocols for this ELB to listen on (see examples).
      - Required when I(state=present) and the ELB doesn't exist.
    type: list
    elements: dict
    suboptions:
      load_balancer_port:
        description:
          - The port on which the load balancer will listen.
        type: int
        required: True
      instance_port:
        description:
          - The port on which the instance is listening.
        type: int
        required: True
      ssl_certificate_id:
        description:
          - The Amazon Resource Name (ARN) of the SSL certificate.
        type: str
      protocol:
        description:
          - The transport protocol to use for routing.
          - Valid values are C(HTTP), C(HTTPS), C(TCP), or C(SSL).
        type: str
        required: True
      instance_protocol:
        description:
          - The protocol to use for routing traffic to instances.
          - Valid values are C(HTTP), C(HTTPS), C(TCP), or C(SSL),
        type: str
  purge_listeners:
    description:
      - Purge existing listeners on ELB that are not found in listeners.
    type: bool
    default: true
  instance_ids:
    description:
      - List of instance ids to attach to this ELB.
    type: list
    elements: str
  purge_instance_ids:
    description:
      - Purge existing instance ids on ELB that are not found in I(instance_ids).
    type: bool
    default: false
  zones:
    description:
      - List of availability zones to enable on this ELB.
      - Mutually exclusive with I(subnets).
    type: list
    elements: str
  purge_zones:
    description:
      - Purge existing availability zones on ELB that are not found in I(zones).
    type: bool
    default: false
  security_group_ids:
    description:
      - A list of security groups to apply to the ELB.
    type: list
    elements: str
  security_group_names:
    description:
      - A list of security group names to apply to the ELB.
    type: list
    elements: str
  health_check:
    description:
      - An associative array of health check configuration settings (see examples).
    type: dict
  access_logs:
    description:
      - An associative array of access logs configuration settings (see examples).
    type: dict
  subnets:
    description:
      - A list of VPC subnets to use when creating the ELB.
      - Mutually exclusive with I(zones).
    type: list
    elements: str
  purge_subnets:
    description:
      - Purge existing subnets on the ELB that are not found in I(subnets).
      - Because it is not permitted to add multiple subnets from the same
        availability zone, subnets to be purged will be removed before new
        subnets are added.  This may cause a brief outage if you try to replace
        all subnets at once.
    type: bool
    default: false
  scheme:
    description:
      - The scheme to use when creating the ELB.
      - For a private VPC-visible ELB use C(internal).
      - If you choose to update your scheme with a different value the ELB will be destroyed and
        recreated.
      - Defaults to I(scheme=internet-facing).
    type: str
    choices: ["internal", "internet-facing"]
  connection_draining_timeout:
    description:
      - Wait a specified timeout allowing connections to drain before terminating an instance.
    type: int
  idle_timeout:
    description:
      - ELB connections from clients and to servers are timed out after this amount of time.
    type: int
  cross_az_load_balancing:
    description:
      - Distribute load across all configured Availability Zones.
      - Defaults to C(false).
    type: bool
  stickiness:
    description:
      - An associative array of stickiness policy settings. Policy will be applied to all listeners (see examples).
    type: dict
  wait:
    description:
      - When creating or deleting (not updating) an ELB, if I(wait=True)
        Ansible will wait for both the load balancer and related network interfaces
        to finish creating/deleting.
    type: bool
    default: false
  wait_timeout:
    description:
      - Used in conjunction with wait. Number of seconds to wait for the ELB to be terminated.
      - A maximum of 600 seconds (10 minutes) is allowed.
    type: int
    default: 60
  tags:
    description:
      - An associative array of tags. To delete all tags, supply an empty dict (C({})).
    type: dict

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
'''

EXAMPLES = """
# Note: None of these examples set aws_access_key, aws_secret_key, or region.
# It is assumed that their matching environment variables are set.

# Basic provisioning example (non-VPC)

- amazon.aws.elb_classic_lb:
    name: "test-please-delete"
    state: present
    zones:
      - us-east-1a
      - us-east-1d
    listeners:
      - protocol: http # options are http, https, ssl, tcp
        load_balancer_port: 80
        instance_port: 80
        proxy_protocol: True
      - protocol: https
        load_balancer_port: 443
        instance_protocol: http # optional, defaults to value of protocol setting
        instance_port: 80
        # ssl certificate required for https or ssl
        ssl_certificate_id: "arn:aws:iam::123456789012:server-certificate/company/servercerts/ProdServerCert"

# Internal ELB example

- amazon.aws.elb_classic_lb:
    name: "test-vpc"
    scheme: internal
    state: present
    instance_ids:
      - i-abcd1234
    purge_instance_ids: true
    subnets:
      - subnet-abcd1234
      - subnet-1a2b3c4d
    listeners:
      - protocol: http # options are http, https, ssl, tcp
        load_balancer_port: 80
        instance_port: 80

# Configure a health check and the access logs
- amazon.aws.elb_classic_lb:
    name: "test-please-delete"
    state: present
    zones:
      - us-east-1d
    listeners:
      - protocol: http
        load_balancer_port: 80
        instance_port: 80
    health_check:
        ping_protocol: http # options are http, https, ssl, tcp
        ping_port: 80
        ping_path: "/index.html" # not required for tcp or ssl
        response_timeout: 5 # seconds
        interval: 30 # seconds
        unhealthy_threshold: 2
        healthy_threshold: 10
    access_logs:
        interval: 5 # minutes (defaults to 60)
        s3_location: "my-bucket" # This value is required if access_logs is set
        s3_prefix: "logs"

# Ensure ELB is gone
- amazon.aws.elb_classic_lb:
    name: "test-please-delete"
    state: absent

# Ensure ELB is gone and wait for check (for default timeout)
- amazon.aws.elb_classic_lb:
    name: "test-please-delete"
    state: absent
    wait: yes

# Ensure ELB is gone and wait for check with timeout value
- amazon.aws.elb_classic_lb:
    name: "test-please-delete"
    state: absent
    wait: yes
    wait_timeout: 600

# Normally, this module will purge any listeners that exist on the ELB
# but aren't specified in the listeners parameter. If purge_listeners is
# false it leaves them alone
- amazon.aws.elb_classic_lb:
    name: "test-please-delete"
    state: present
    zones:
      - us-east-1a
      - us-east-1d
    listeners:
      - protocol: http
        load_balancer_port: 80
        instance_port: 80
    purge_listeners: no

# Normally, this module will leave availability zones that are enabled
# on the ELB alone. If purge_zones is true, then any extraneous zones
# will be removed
- amazon.aws.elb_classic_lb:
    name: "test-please-delete"
    state: present
    zones:
      - us-east-1a
      - us-east-1d
    listeners:
      - protocol: http
        load_balancer_port: 80
        instance_port: 80
    purge_zones: yes

# Creates a ELB and assigns a list of subnets to it.
- amazon.aws.elb_classic_lb:
    state: present
    name: 'New ELB'
    security_group_ids: 'sg-123456, sg-67890'
    subnets: 'subnet-123456,subnet-67890'
    purge_subnets: yes
    listeners:
      - protocol: http
        load_balancer_port: 80
        instance_port: 80

# Create an ELB with connection draining, increased idle timeout and cross availability
# zone load balancing
- amazon.aws.elb_classic_lb:
    name: "New ELB"
    state: present
    connection_draining_timeout: 60
    idle_timeout: 300
    cross_az_load_balancing: "yes"
    zones:
      - us-east-1a
      - us-east-1d
    listeners:
      - protocol: http
        load_balancer_port: 80
        instance_port: 80

# Create an ELB with load balancer stickiness enabled
- amazon.aws.elb_classic_lb:
    name: "New ELB"
    state: present
    zones:
      - us-east-1a
      - us-east-1d
    listeners:
      - protocol: http
        load_balancer_port: 80
        instance_port: 80
    stickiness:
      type: loadbalancer
      enabled: yes
      expiration: 300

# Create an ELB with application stickiness enabled
- amazon.aws.elb_classic_lb:
    name: "New ELB"
    state: present
    zones:
      - us-east-1a
      - us-east-1d
    listeners:
      - protocol: http
        load_balancer_port: 80
        instance_port: 80
    stickiness:
      type: application
      enabled: yes
      cookie: SESSIONID

# Create an ELB and add tags
- amazon.aws.elb_classic_lb:
    name: "New ELB"
    state: present
    zones:
      - us-east-1a
      - us-east-1d
    listeners:
      - protocol: http
        load_balancer_port: 80
        instance_port: 80
    tags:
      Name: "New ELB"
      stack: "production"
      client: "Bob"

# Delete all tags from an ELB
- amazon.aws.elb_classic_lb:
    name: "New ELB"
    state: present
    zones:
      - us-east-1a
      - us-east-1d
    listeners:
      - protocol: http
        load_balancer_port: 80
        instance_port: 80
    tags: {}
"""

# import time

try:
    import botocore
except ImportError:
    pass  # Taken care of by AnsibleAWSModule

from ..module_utils.core import AnsibleAWSModule
from ..module_utils.core import is_boto3_error_code
from ..module_utils.core import scrub_none_parameters
from ..module_utils.ec2 import AWSRetry
from ..module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ..module_utils.ec2 import camel_dict_to_snake_dict
from ..module_utils.ec2 import snake_dict_to_camel_dict

# from ..module_utils.ec2 import get_ec2_security_group_ids_from_names
from ..module_utils.waiters import get_waiter


class ElbManager(object):
    """Handles ELB creation and destruction"""

    def __init__(self, module):

        self.module = module

        self.name = module.params['name']
        self.listeners = module.params['listeners']
        self.purge_listeners = module.params['purge_listeners']
        self.instance_ids = module.params['instance_ids']
        self.purge_instance_ids = module.params['purge_instance_ids']
        self.zones = module.params['zones']
        self.purge_zones = module.params['purge_zones']
        self.health_check = module.params['health_check']
        self.access_logs = module.params['access_logs']
        self.subnets = module.params['subnets']
        self.purge_subnets = module.params['purge_subnets']
        self.scheme = module.params['scheme']
        self.connection_draining_timeout = module.params['connection_draining_timeout']
        self.idle_timeout = module.params['idle_timeout']
        self.cross_az_load_balancing = module.params['cross_az_load_balancing']
        self.stickiness = module.params['stickiness']
        self.wait = module.params['wait']
        self.wait_timeout = module.params['wait_timeout']
        self.tags = module.params['tags']

        self.changed = False
        self.status = 'gone'

        retry_decorator = AWSRetry.jittered_backoff()
        self.client = self.module.client('elb', retry_decorator=retry_decorator)
        self.ec2_client = self.module.client('ec2', retry_decorator=retry_decorator)

        security_group_names = module.params['security_group_names']
        self.security_group_ids = module.params['security_group_ids']

        try:
            self.elb = self._get_elb()
        except (botocore.exceptions.ClientException, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg='Unable to describe load balancer')

        self.validate_params()

#        if security_group_names:
#            try:
#                ec2 = module.client('ec2')
#                security_group_ids = _get_ec2_security_group_ids_from_names(
#                    security_group_names, ec2, vpc_id=vpc_id)
#            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
#                module.fail_json_aws(e, msg="Failed to convert security group names to IDs")

    # We have a number of complex parameters which can't be validated by
    # AnsibleModule or are only required if the ELB doesn't exist.
    def validate_params(self):
        pass

    # Pass check_mode down through to the module
    @property
    def check_mode(self):
        return self.module.check_mode

    def _get_elb(self):
        try:
            elbs = self._describe_loadbalancer(self.name)
        except is_boto3_error_code('LoadBalancerNotFound'):
            return None

        # Shouldn't happen, but Amazon could change the rules on us...
        if len(elbs) > 1:
            self.module.fail_json('Found multiple ELBs with name {0}'.format(self.name))

        self.status = 'exists' if self.status == 'gone' else self.status

        return elbs[0]

    def _delete_elb(self):
        # True if succeeds, exception raised if not
        try:
            if not self.check_mode:
                self.client.delete_load_balancer(aws_retry=True, LoadBalancerName=self.name)
            self.changed = True
            self.status = 'deleted'
        except is_boto3_error_code('LoadBalancerNotFound'):
            pass

    def _create_elb(self):
        listeners = list(self._format_listener(l) for l in self.listeners)
        if not self.scheme:
            self.scheme = 'internet-facing'
        params = dict(
            LoadBalancerName=self.name,
            AvailabilityZones=self.zones,
            SecurityGroups=self.security_group_ids,
            Subnets=self.subnets,
            Listeners=listeners,
            Scheme=self.scheme)
        params = scrub_none_parameters(params)

        if not self.check_mode:
            self.client.create_load_balancer(aws_retry=True, **params)
            # create_load_balancer only returns the DNS name
            self.elb = self._get_elb()
        self.changed = True
        self.status = 'created'

    def _format_listener(self, listener, inject_protocol=False):
        """Formats listener into the format needed by the
        ELB API"""

        listener = scrub_none_parameters(listener)
        for protocol in ['protocol', 'instance_protocol']:
            if protocol in listener:
                listener[protocol] = listener[protocol].upper()

        if inject_protocol and 'instance_protocol' not in listener:
            listener['instance_protocol'] = listener['protocol']

        return snake_dict_to_camel_dict(listener, True)

    def ensure_ok(self):
        """Create the ELB"""
        if not self.elb:
            try:
                self._create_elb()
            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                self.module.fail_json_aws(e, msg="Failed to create load balancer")
            self._wait_created()

        # Some attributes are configured on creation, others need to be updated
        # after creation.  Skip updates for those set on creation
        else:
            if self._check_scheme():
                # XXX We should probably set 'None' parameters based on the
                # current state prior to deletion

                # the only way to change the scheme is by recreating the resource
                self.ensure_gone()
                # We need to wait for it to be gone-gone
                self._wait_gone(True)
                try:
                    self._create_elb()
                except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                    self.module.fail_json_aws(e, msg="Failed to recreate load balancer")
            else:
                self._set_subnets()
                self._set_zones()
                self._set_security_groups()
                self._set_elb_listeners()

#        self._set_health_check()
#        # boto has introduced support for some ELB attributes in
#        # different versions, so we check first before trying to
#        # set them to avoid errors
#        if self._check_attribute_support('connection_draining'):
#            self._set_connection_draining_timeout()
#        if self._check_attribute_support('connecting_settings'):
#            self._set_idle_timeout()
#        if self._check_attribute_support('cross_zone_load_balancing'):
#            self._set_cross_az_load_balancing()
#        if self._check_attribute_support('access_log'):
#            self._set_access_log()
#        # add sticky options
#        self.select_stickiness_policy()
#
#        # ensure backend server policies are correct
#        self._set_backend_policies()
#        # set/remove instance ids
#        self._set_instance_ids()
#
#        self._set_tags()

    def ensure_gone(self):
        """Destroy the ELB"""
        if self.elb:
            try:
                self._delete_elb()
            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                self.module.fail_json_aws(e, msg="Failed to delete load balancer")
        self._wait_gone()

    def _wait_gone(self, wait=None):
        if not wait and not self.wait:
            return
        try:
            elb_removed = self._wait_for_elb_removed()
            # Unfortunately even though the ELB itself is removed quickly
            # the interfaces take longer so reliant security groups cannot
            # be deleted until the interface has registered as removed.
            elb_interface_removed = self._wait_for_elb_interface_removed()
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed while waiting for load balancer deletion")

    def _wait_created(self, wait=False):
        if not wait and not self.wait:
            return
        try:
            self._wait_for_elb_created()
            # Can take longer than creation
            self._wait_for_elb_interface_created()
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed while waiting for load balancer deletion")

    def get_info(self):
        try:
            check_elb = self._get_elb()
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to get load balancer")

        if not check_elb:
            return dict(
                name=self.name,
                status=self.status,
                region=self.module.region
            )

        policies = check_elb.get('Policies', {})
        try:
            lb_cookie_policy = policies['LBCookieStickinessPolicies'][0]['PolicyName']
        except (KeyError, IndexError):
            lb_cookie_policy = None
        try:
            app_cookie_policy = policies['AppCookieStickinessPolicies'][0]['PolicyName']
        except (KeyError, IndexError):
            app_cookie_policy = None

        instances = check_elb.get('Instances', [])
        instance_ids = list(i['InstanceId'] for i in instances)

        health_check = camel_dict_to_snake_dict(check_elb.get('HealthCheck', {}))

        info = dict(
            name=check_elb.get('LoadBalancerName'),
            dns_name=check_elb.get('DNSName'),
            zones=check_elb.get('AvailabilityZones'),
            security_group_ids=check_elb.get('SecurityGroups'),
            status=self.status,
            subnets=check_elb.get('Subnets'),
            scheme=check_elb.get('Scheme'),
            hosted_zone_name=check_elb.get('CanonicalHostedZoneName'),
            hosted_zone_id=check_elb.get('CanonicalHostedZoneNameID'),
            lb_cookie_policy=lb_cookie_policy,
            app_cookie_policy=app_cookie_policy,
            # XXX TODO
            # proxy_policy=self._get_proxy_protocol_policy(),
            # backends=self._get_backend_policies(),
            instances=instance_ids,
            out_of_service_count=0,
            in_service_count=0,
            unknown_instance_state_count=0,
            region=self.module.region,
            health_check=health_check,
        )

        info['instance_health'] = []
        if info['instances']:
            try:
                health = self.client.describe_instance_health(aws_retry=True, LoadBalancerName=self.name)['InstanceStates']
                info['instance_health'] = camel_dict_to_snake_dict(health)
            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                self.module.warn('Failed to fetch instance health')

        # instance state counts: InService or OutOfService
        if info['instance_health']:
            for instance_state in info['instance_health']:
                if instance_state['state'] == "InService":
                    info['in_service_count'] += 1
                elif instance_state['state'] == "OutOfService":
                    info['out_of_service_count'] += 1
                else:
                    info['unknown_instance_state_count'] += 1

        listeners = check_elb.get('ListenerDescriptions', [])
        if listeners:
            info['listeners'] = list(
                self._api_listener_as_tuple(l['Listener']) for l in listeners
            )
        else:
            info['listeners'] = []

        # if self._check_attribute_support('connection_draining'):
        #     info['connection_draining_timeout'] = int(self.elb_conn.get_lb_attribute(self.name, 'ConnectionDraining').timeout)

        # if self._check_attribute_support('connecting_settings'):
        #     info['idle_timeout'] = self.elb_conn.get_lb_attribute(self.name, 'ConnectingSettings').idle_timeout

        # if self._check_attribute_support('cross_zone_load_balancing'):
        #     is_cross_az_lb_enabled = self.elb_conn.get_lb_attribute(self.name, 'CrossZoneLoadBalancing')
        #     if is_cross_az_lb_enabled:
        #         info['cross_az_load_balancing'] = 'yes'
        #     else:
        #         info['cross_az_load_balancing'] = 'no'

        # # return stickiness info?

        # info['tags'] = self.tags

        return info

    def _wait_for_elb_created(self):
        if self.check_mode:
            return True

        delay = 10
        max_attempts = (self.wait_timeout // delay)
        waiter = get_waiter(self.client, 'load_balancer_created')

        try:
            waiter.wait(
                WaiterConfig={'Delay': delay, 'MaxAttempts': max_attempts},
                LoadBalancerNames=[self.name],
            )
        except botocore.exceptions.WaiterError as e:
            self.module.fail_json_aws(e, 'Timeout waiting for ELB removal')

        return True

    def _wait_for_elb_interface_created(self):
        if self.check_mode:
            return True
        delay = 10
        max_attempts = (self.wait_timeout // delay)
        waiter = get_waiter(self.ec2_client, 'network_interface_available')

        filters = ansible_dict_to_boto3_filter_list(
            {'requester-id': 'amazon-elb',
             'description': 'ELB {0}'.format(self.name)}
        )

        try:
            waiter.wait(
                WaiterConfig={'Delay': delay, 'MaxAttempts': max_attempts},
                Filters=filters,
            )
        except botocore.exceptions.WaiterError as e:
            self.module.fail_json_aws(e, 'Timeout waiting for ELB Interface removal')

        return True

    def _wait_for_elb_removed(self):
        if self.check_mode:
            return True

        delay = 10
        max_attempts = (self.wait_timeout // delay)
        waiter = get_waiter(self.client, 'load_balancer_deleted')

        try:
            waiter.wait(
                WaiterConfig={'Delay': delay, 'MaxAttempts': max_attempts},
                LoadBalancerNames=[self.name],
            )
        except botocore.exceptions.WaiterError as e:
            self.module.fail_json_aws(e, 'Timeout waiting for ELB removal')

        return True

    def _wait_for_elb_interface_removed(self):
        if self.check_mode:
            return True

        delay = 10
        max_attempts = (self.wait_timeout // delay)
        waiter = get_waiter(self.ec2_client, 'network_interface_deleted')

        filters = ansible_dict_to_boto3_filter_list(
            {'requester-id': 'amazon-elb',
             'description': 'ELB {0}'.format(self.name)}
        )

        try:
            waiter.wait(
                WaiterConfig={'Delay': delay, 'MaxAttempts': max_attempts},
                Filters=filters,
            )
        except botocore.exceptions.WaiterError as e:
            self.module.fail_json_aws(e, 'Timeout waiting for ELB Interface removal')

        return True

    def _create_elb_listeners(self, listeners):
        """Takes a list of listener definitions and creates them"""
        if not listeners:
            return False
        self.changed = True
        if self.check_mode:
            return True

        self.changed = self.client.create_load_balancer_listeners(
            aws_retry=True,
            LoadBalancerName=self.name,
            Listeners=listeners,
        )
        return True

    def _delete_elb_listeners(self, ports):
        """Takes a list of listener ports and deletes them from the ELB"""
        if not ports:
            return False
        self.changed = True
        if self.check_mode:
            return True

        self.changed = self.client.delete_load_balancer_listeners(
            aws_retry=True,
            LoadBalancerName=self.name,
            LoadBalancerPorts=ports,
        )
        return True

    def _set_elb_listeners(self):
        """
        Creates listeners specified by self.listeners; overwrites existing
        listeners on these ports; removes extraneous listeners
        """

        if not self.listeners:
            return False

        # We can't use sets here: dicts aren't hashable, so convert to the boto3
        # format and use a generator to filter
        new_listeners = list(self._format_listener(l, True) for l in self.listeners)
        existing_listeners = list(l['Listener'] for l in self.elb['ListenerDescriptions'])
        listeners_to_remove = list(l for l in existing_listeners if l not in new_listeners)
        listeners_to_add = list(l for l in new_listeners if l not in existing_listeners)

        changed = False

        if self.purge_listeners:
            ports_to_remove = list(l['LoadBalancerPort'] for l in listeners_to_remove)
        else:
            old_ports = set(l['LoadBalancerPort'] for l in listeners_to_remove)
            new_ports = set(l['LoadBalancerPort'] for l in listeners_to_add)
            # If we're not purging, then we need to remove Listeners
            # where the full definition doesn't match, but the port does
            ports_to_remove = list(old_ports & new_ports)

        # Update is a delete then add, so do the deletion first
        try:
            changed |= self._delete_elb_listeners(ports_to_remove)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to remove listeners from load balancer")
        try:
            changed |= self._create_elb_listeners(listeners_to_add)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to remove listeners from load balancer")

        return changed

    def _api_listener_as_tuple(self, listener):
        """Adds ssl_certificate_id to ELB API tuple if present"""
        base_tuple = [
            listener.get('LoadBalancerPort'),
            listener.get('InstancePort'),
            listener.get('Protocol'),
            listener.get('InstanceProtocol'),
        ]
        if listener.get('SSLCertificateId', False):
            base_tuple.append(listener.get('SSLCertificateId'))
        return tuple(base_tuple)

    def _attach_subnets(self, subnets):
        if not subnets:
            return False
        self.changed = True
        if self.check_mode:
            return True
        self.client.attach_load_balancer_to_subnets(
            aws_retry=True,
            LoadBalancerName=self.name,
            Subnets=subnets)
        return True

    def _detach_subnets(self, subnets):
        if not subnets:
            return False
        self.changed = True
        if self.check_mode:
            return True
        self.client.detach_load_balancer_from_subnets(
            aws_retry=True,
            LoadBalancerName=self.name,
            Subnets=subnets)
        return True

    def _set_subnets(self):
        """Determine which subnets need to be attached or detached on the ELB"""
        # Subnets parameter not set, nothing to change
        if self.subnets is None:
            return False

        changed = False

        if self.purge_subnets:
            subnets_to_detach = list(set(self.elb['Subnets']) - set(self.subnets))
        else:
            subnets_to_detach = list()
        subnets_to_attach = list(set(self.subnets) - set(self.elb['Subnets']))

        # You can't add multiple subnets from the same AZ.  Remove first, then
        # add.
        try:
            changed |= self._detach_subnets(subnets_to_detach)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to detach subnets from load balancer")
        try:
            changed |= self._attach_subnets(subnets_to_attach)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to attach subnets to load balancer")

        return changed

    def _check_scheme(self):
        """Determine if the current scheme is different than the scheme of the ELB"""
        if self.scheme:
            if self.elb['Scheme'] != self.scheme:
                return True
        return False

    def _enable_zones(self, zones):
        if not zones:
            return False
        self.changed = True
        if self.check_mode:
            return True

        try:
            self.client.enable_availability_zones_for_load_balancer(
                aws_retry=True,
                LoadBalancerName=self.name,
                AvailabilityZones=zones,
            )
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg='Failed to enable zones for load balancer')
        return True

    def _disable_zones(self, zones):
        if not zones:
            return False
        self.changed = True
        if self.check_mode:
            return True

        try:
            self.client.disable_availability_zones_for_load_balancer(
                aws_retry=True,
                LoadBalancerName=self.name,
                AvailabilityZones=zones,
            )
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg='Failed to disable zones for load balancer')
        return True

    def _set_zones(self):
        """Determine which zones need to be enabled or disabled on the ELB"""
        # zones parameter not set, nothing to changeA
        if self.zones is None:
            return False

        changed = False

        if self.purge_zones:
            zones_to_disable = list(set(self.elb['AvailabilityZones']) - set(self.zones))
        else:
            zones_to_disable = list()
        zones_to_enable = list(set(self.zones) - set(self.elb['AvailabilityZones']))

        # Add before we remove to reduce the chance of an outage if someone
        # replaces all zones at once
        try:
            changed |= self._enable_zones(zones_to_enable)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to enable zone on load balancer")
        try:
            changed |= self._disable_zones(zones_to_disable)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to attach zone to load balancer")

        return changed

    def _set_security_groups(self):
        if not self.security_group_ids:
            return False
        # Security Group Names should already by converted to IDs by this point.
        if set(self.elb['SecurityGroups']) == set(self.security_group_ids):
            return False

        self.changed = True

        if self.check_mode:
            return True

        try:
            self.client.apply_security_groups_to_load_balancer(
                aws_retry=True,
                LoadBalancerName=self.name,
                SecurityGroups=self.security_group_ids,
            )
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to apply security groups to load balancer")
        return True

#    def _set_health_check(self):
#        """Set health check values on ELB as needed"""
#        if self.health_check:
#            # This just makes it easier to compare each of the attributes
#            # and look for changes. Keys are attributes of the current
#            # health_check; values are desired values of new health_check
#            health_check_config = {
#                "target": self._get_health_check_target(),
#                "timeout": self.health_check['response_timeout'],
#                "interval": self.health_check['interval'],
#                "unhealthy_threshold": self.health_check['unhealthy_threshold'],
#                "healthy_threshold": self.health_check['healthy_threshold'],
#            }
#
#            update_health_check = False
#
#            # The health_check attribute is *not* set on newly created
#            # ELBs! So we have to create our own.
#            if not self.elb.health_check:
#                self.elb.health_check = HealthCheck()
#
#            for attr, desired_value in health_check_config.items():
#                if getattr(self.elb.health_check, attr) != desired_value:
#                    setattr(self.elb.health_check, attr, desired_value)
#                    update_health_check = True
#
#            if update_health_check:
#                self.elb.configure_health_check(self.elb.health_check)
#                self.changed = True
#
#    def _check_attribute_support(self, attr):
#        return hasattr(boto.ec2.elb.attributes.LbAttributes(), attr)
#
#    def _set_cross_az_load_balancing(self):
#        attributes = self.elb.get_attributes()
#        if self.cross_az_load_balancing:
#            if not attributes.cross_zone_load_balancing.enabled:
#                self.changed = True
#            attributes.cross_zone_load_balancing.enabled = True
#        else:
#            if attributes.cross_zone_load_balancing.enabled:
#                self.changed = True
#            attributes.cross_zone_load_balancing.enabled = False
#        self.elb_conn.modify_lb_attribute(self.name, 'CrossZoneLoadBalancing',
#                                          attributes.cross_zone_load_balancing.enabled)
#
#    def _set_access_log(self):
#        attributes = self.elb.get_attributes()
#        if self.access_logs:
#            if 's3_location' not in self.access_logs:
#                self.module.fail_json(msg='s3_location information required')
#
#            access_logs_config = {
#                "enabled": True,
#                "s3_bucket_name": self.access_logs['s3_location'],
#                "s3_bucket_prefix": self.access_logs.get('s3_prefix', ''),
#                "emit_interval": self.access_logs.get('interval', 60),
#            }
#
#            update_access_logs_config = False
#            for attr, desired_value in access_logs_config.items():
#                if getattr(attributes.access_log, attr) != desired_value:
#                    setattr(attributes.access_log, attr, desired_value)
#                    update_access_logs_config = True
#            if update_access_logs_config:
#                self.elb_conn.modify_lb_attribute(self.name, 'AccessLog', attributes.access_log)
#                self.changed = True
#        elif attributes.access_log.enabled:
#            attributes.access_log.enabled = False
#            self.changed = True
#            self.elb_conn.modify_lb_attribute(self.name, 'AccessLog', attributes.access_log)
#
#    def _set_connection_draining_timeout(self):
#        attributes = self.elb.get_attributes()
#        if self.connection_draining_timeout is not None:
#            if not attributes.connection_draining.enabled or \
#                    attributes.connection_draining.timeout != self.connection_draining_timeout:
#                self.changed = True
#            attributes.connection_draining.enabled = True
#            attributes.connection_draining.timeout = self.connection_draining_timeout
#            self.elb_conn.modify_lb_attribute(self.name, 'ConnectionDraining', attributes.connection_draining)
#        else:
#            if attributes.connection_draining.enabled:
#                self.changed = True
#            attributes.connection_draining.enabled = False
#            self.elb_conn.modify_lb_attribute(self.name, 'ConnectionDraining', attributes.connection_draining)
#
#    def _set_idle_timeout(self):
#        attributes = self.elb.get_attributes()
#        if self.idle_timeout is not None:
#            if attributes.connecting_settings.idle_timeout != self.idle_timeout:
#                self.changed = True
#            attributes.connecting_settings.idle_timeout = self.idle_timeout
#            self.elb_conn.modify_lb_attribute(self.name, 'ConnectingSettings', attributes.connecting_settings)
#
#    def _policy_name(self, policy_type):
#        return 'ec2-elb-lb-{0}'.format(to_native(policy_type, errors='surrogate_or_strict'))
#
#    def _create_policy(self, policy_param, policy_meth, policy):
#        getattr(self.elb_conn, policy_meth)(policy_param, self.elb.name, policy)
#
#    def _delete_policy(self, elb_name, policy):
#        self.elb_conn.delete_lb_policy(elb_name, policy)
#
#    def _update_policy(self, policy_param, policy_meth, policy_attr, policy):
#        self._delete_policy(self.elb.name, policy)
#        self._create_policy(policy_param, policy_meth, policy)
#
#    def _set_listener_policy(self, listeners_dict, policy=None):
#        policy = [] if policy is None else policy
#
#        for listener_port in listeners_dict:
#            if listeners_dict[listener_port].startswith('HTTP'):
#                self.elb_conn.set_lb_policies_of_listener(self.elb.name, listener_port, policy)
#
#    def _set_stickiness_policy(self, elb_info, listeners_dict, policy, **policy_attrs):
#        for p in getattr(elb_info.policies, policy_attrs['attr']):
#            if str(p.__dict__['policy_name']) == str(policy[0]):
#                if str(p.__dict__[policy_attrs['dict_key']]) != str(policy_attrs['param_value'] or 0):
#                    self._set_listener_policy(listeners_dict)
#                    self._update_policy(policy_attrs['param_value'], policy_attrs['method'], policy_attrs['attr'], policy[0])
#                    self.changed = True
#                break
#        else:
#            self._create_policy(policy_attrs['param_value'], policy_attrs['method'], policy[0])
#            self.changed = True
#
#        self._set_listener_policy(listeners_dict, policy)
#
#    def select_stickiness_policy(self):
#        if self.stickiness:
#
#            if 'cookie' in self.stickiness and 'expiration' in self.stickiness:
#                self.module.fail_json(msg='\'cookie\' and \'expiration\' can not be set at the same time')
#
#            elb_info = self.elb_conn.get_all_load_balancers(self.elb.name)[0]
#            d = {}
#            for listener in elb_info.listeners:
#                d[listener[0]] = listener[2]
#            listeners_dict = d
#
#            if self.stickiness['type'] == 'loadbalancer':
#                policy = []
#                policy_type = 'LBCookieStickinessPolicyType'
#
#                if self.module.boolean(self.stickiness['enabled']):
#
#                    if 'expiration' not in self.stickiness:
#                        self.module.fail_json(msg='expiration must be set when type is loadbalancer')
#
#                    try:
#                        expiration = self.stickiness['expiration'] if int(self.stickiness['expiration']) else None
#                    except ValueError:
#                        self.module.fail_json(msg='expiration must be set to an integer')
#
#                    policy_attrs = {
#                        'type': policy_type,
#                        'attr': 'lb_cookie_stickiness_policies',
#                        'method': 'create_lb_cookie_stickiness_policy',
#                        'dict_key': 'cookie_expiration_period',
#                        'param_value': expiration
#                    }
#                    policy.append(self._policy_name(policy_attrs['type']))
#
#                    self._set_stickiness_policy(elb_info, listeners_dict, policy, **policy_attrs)
#                elif not self.module.boolean(self.stickiness['enabled']):
#                    if len(elb_info.policies.lb_cookie_stickiness_policies):
#                        if elb_info.policies.lb_cookie_stickiness_policies[0].policy_name == self._policy_name(policy_type):
#                            self.changed = True
#                    else:
#                        self.changed = False
#                    self._set_listener_policy(listeners_dict)
#                    self._delete_policy(self.elb.name, self._policy_name(policy_type))
#
#            elif self.stickiness['type'] == 'application':
#                policy = []
#                policy_type = 'AppCookieStickinessPolicyType'
#                if self.module.boolean(self.stickiness['enabled']):
#
#                    if 'cookie' not in self.stickiness:
#                        self.module.fail_json(msg='cookie must be set when type is application')
#
#                    policy_attrs = {
#                        'type': policy_type,
#                        'attr': 'app_cookie_stickiness_policies',
#                        'method': 'create_app_cookie_stickiness_policy',
#                        'dict_key': 'cookie_name',
#                        'param_value': self.stickiness['cookie']
#                    }
#                    policy.append(self._policy_name(policy_attrs['type']))
#                    self._set_stickiness_policy(elb_info, listeners_dict, policy, **policy_attrs)
#                elif not self.module.boolean(self.stickiness['enabled']):
#                    if len(elb_info.policies.app_cookie_stickiness_policies):
#                        if elb_info.policies.app_cookie_stickiness_policies[0].policy_name == self._policy_name(policy_type):
#                            self.changed = True
#                    self._set_listener_policy(listeners_dict)
#                    self._delete_policy(self.elb.name, self._policy_name(policy_type))
#
#            else:
#                self._set_listener_policy(listeners_dict)
#
#    def _get_backend_policies(self):
#        """Get a list of backend policies"""
#        policies = []
#        if self.elb.backends is not None:
#            for backend in self.elb.backends:
#                if backend.policies is not None:
#                    for policy in backend.policies:
#                        policies.append(str(backend.instance_port) + ':' + policy.policy_name)
#
#        return policies
#
#    def _set_backend_policies(self):
#        """Sets policies for all backends"""
#        ensure_proxy_protocol = False
#        replace = []
#        backend_policies = self._get_backend_policies()
#
#        # Find out what needs to be changed
#        for listener in self.listeners:
#            want = False
#
#            if 'proxy_protocol' in listener and listener['proxy_protocol']:
#                ensure_proxy_protocol = True
#                want = True
#
#            if str(listener['instance_port']) + ':ProxyProtocol-policy' in backend_policies:
#                if not want:
#                    replace.append({'port': listener['instance_port'], 'policies': []})
#            elif want:
#                replace.append({'port': listener['instance_port'], 'policies': ['ProxyProtocol-policy']})
#
#        # enable or disable proxy protocol
#        if ensure_proxy_protocol:
#            self._set_proxy_protocol_policy()
#
#        # Make the backend policies so
#        for item in replace:
#            self.elb_conn.set_lb_policies_of_backend_server(self.elb.name, item['port'], item['policies'])
#            self.changed = True
#
#    def _get_proxy_protocol_policy(self):
#        """Find out if the elb has a proxy protocol enabled"""
#        if self.elb.policies is not None and self.elb.policies.other_policies is not None:
#            for policy in self.elb.policies.other_policies:
#                if policy.policy_name == 'ProxyProtocol-policy':
#                    return policy.policy_name
#
#        return None
#
#    def _set_proxy_protocol_policy(self):
#        """Install a proxy protocol policy if needed"""
#        proxy_policy = self._get_proxy_protocol_policy()
#
#        if proxy_policy is None:
#            self.elb_conn.create_lb_policy(
#                self.elb.name, 'ProxyProtocol-policy', 'ProxyProtocolPolicyType', {'ProxyProtocol': True}
#            )
#            self.changed = True
#
#        # TODO: remove proxy protocol policy if not needed anymore? There is no side effect to leaving it there
#
#    def _diff_list(self, a, b):
#        """Find the entries in list a that are not in list b"""
#        b = set(b)
#        return [aa for aa in a if aa not in b]
#
#    def _get_instance_ids(self):
#        """Get the current list of instance ids installed in the elb"""
#        instances = []
#        if self.elb.instances is not None:
#            for instance in self.elb.instances:
#                instances.append(instance.id)
#
#        return instances
#
#    def _set_instance_ids(self):
#        """Register or deregister instances from an lb instance"""
#        assert_instances = self.instance_ids or []
#
#        has_instances = self._get_instance_ids()
#
#        add_instances = self._diff_list(assert_instances, has_instances)
#        if add_instances:
#            self.elb_conn.register_instances(self.elb.name, add_instances)
#            self.changed = True
#
#        if self.purge_instance_ids:
#            remove_instances = self._diff_list(has_instances, assert_instances)
#            if remove_instances:
#                self.elb_conn.deregister_instances(self.elb.name, remove_instances)
#                self.changed = True
#
#    def _set_tags(self):
#        """Add/Delete tags"""
#        if self.tags is None:
#            return
#
#        params = {'LoadBalancerNames.member.1': self.name}
#
#        tagdict = dict()
#
#        # get the current list of tags from the ELB, if ELB exists
#        if self.elb:
#            current_tags = self.elb_conn.get_list('DescribeTags', params,
#                                                  [('member', Tag)])
#            tagdict = dict((tag.Key, tag.Value) for tag in current_tags
#                           if hasattr(tag, 'Key'))
#
#        # Add missing tags
#        dictact = dict(set(self.tags.items()) - set(tagdict.items()))
#        if dictact:
#            for i, key in enumerate(dictact):
#                params['Tags.member.%d.Key' % (i + 1)] = key
#                params['Tags.member.%d.Value' % (i + 1)] = dictact[key]
#
#            self.elb_conn.make_request('AddTags', params)
#            self.changed = True
#
#        # Remove extra tags
#        dictact = dict(set(tagdict.items()) - set(self.tags.items()))
#        if dictact:
#            for i, key in enumerate(dictact):
#                params['Tags.member.%d.Key' % (i + 1)] = key
#
#            self.elb_conn.make_request('RemoveTags', params)
#            self.changed = True
#
#    def _get_health_check_target(self):
#        """Compose target string from healthcheck parameters"""
#        protocol = self.health_check['ping_protocol'].upper()
#        path = ""
#
#        if protocol in ['HTTP', 'HTTPS'] and 'ping_path' in self.health_check:
#            path = self.health_check['ping_path']
#
#        return "%s:%s%s" % (protocol, self.health_check['ping_port'], path)

#    def _validate_listeners(listeners):
#        if listeners is None:
#            return True
#        return all(ElbManager.validate_listener(listener) for listener in listeners)
#
#    def _validate_listener(listener):
#        if listener is None:
#            return False
#        if "instance_protocol" in listener:
#            if not ElbManager.validate_protocol(listener['instance_protocol'])
#                return False
#        return ElbManager.validate_protocol(listener['protocol'])
#
#    def _validate_protocol(protocol):
#        if protocol is None:
#            return True
#        return protocol.upper() in ['HTTP', 'HTTPS', 'TCP', 'SSL']

    @AWSRetry.jittered_backoff()
    def _describe_loadbalancer(self, lb_name):
        paginator = self.client.get_paginator('describe_load_balancers')
        return paginator.paginate(LoadBalancerNames=[lb_name]).build_full_result()['LoadBalancerDescriptions']


# def _get_vpc_from_subnets(module, ec2_client, subnets):
#     if not subnets:
#         return None
#
#     subnet_details = _describe_subnets(ec2_client, subnets)
#     vpc_ids = set(subnet['VpcId'] for subnet in subnet_details)
#
#     if not vpc_ids:
#         return None
#     if length(vpc_ids) > 1:
#         module.fail_json("Subnets for an ELB may not span multiple VPCs",
#             subnets=subnet_details, vpc_ids=vpc_ids)
#     vpc_id = vpc_ids.pop()
#
# @AWSRetry.jittered_backoff()
# def _describe_subnets(ec2, subnet_ids):
#     paginator = ec2.get_paginator('describe_subnets')
#     return paginator.paginate(SubnetIds=subnet_ids).build_full_result()['Subnets']
#
# @AWSRetry.jittered_backoff()
# def _get_ec2_security_group_ids_from_names(**params):
#     return get_ec2_security_group_ids_from_names(**params)

def main():

    listeners_spec = dict(
        load_balancer_port=dict(required=True, type='int'),
        instance_port=dict(required=True, type='int'),
        ssl_certificate_id=dict(required=False, type='str'),
        # It would be good to use choice, but we're case insensitive
        protocol=dict(required=True, type='str'),
        instance_protocol=dict(required=False, type='str'),
    )

    argument_spec = dict(
        state=dict(required=True, choices=['present', 'absent']),
        name=dict(required=True),
        listeners=dict(type='list', elements='dict', options=listeners_spec),
        purge_listeners=dict(default=True, type='bool'),
        instance_ids=dict(type='list', elements='str'),
        purge_instance_ids=dict(default=False, type='bool'),
        zones=dict(type='list', elements='str'),
        purge_zones=dict(default=False, type='bool'),
        security_group_ids=dict(type='list', elements='str'),
        security_group_names=dict(type='list', elements='str'),
        health_check=dict(type='dict'),
        subnets=dict(type='list', elements='str'),
        purge_subnets=dict(default=False, type='bool'),
        scheme=dict(choices=['internal', 'internet-facing']),
        connection_draining_timeout=dict(type='int'),
        idle_timeout=dict(type='int'),
        cross_az_load_balancing=dict(type='bool'),
        stickiness=dict(type='dict'),
        access_logs=dict(type='dict'),
        wait=dict(default=False, type='bool'),
        wait_timeout=dict(default=60, type='int'),
        tags=dict(type='dict'),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ['security_group_ids', 'security_group_names'],
            ['zones', 'subnets'],
        ],
        # XXX Need to cover this in validation, we need these for *creation* but
        # not update / delete
        # required_if=[
        #     ['state', 'present', ['listeners']],
        #     ['state', 'present', ['zones', 'subnets'], True],
        # ],
        supports_check_mode=True,
    )

    wait_timeout = module.params['wait_timeout']
    state = module.params['state']

    if wait_timeout > 600:
        module.fail_json(msg='wait_timeout maximum is 600 seconds')

    elb_man = ElbManager(module)

    if state == 'present':
        elb_man.ensure_ok()
        # boto3 style
        lb = camel_dict_to_snake_dict(elb_man.elb or {})
        # original boto style
        elb = elb_man.get_info()
        ec2_result = dict(elb=elb, load_balancer=lb)
    elif state == 'absent':
        elb_man.ensure_gone()
        # original boto style
        elb = elb_man.get_info()
        ec2_result = dict(elb=elb)

    module.exit_json(changed=elb_man.changed, **ec2_result)


if __name__ == '__main__':
    main()
