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
  - This module was renamed from C(amazon.aws.ec2_elb_lb) to M(amazon.aws.elb_classic_lb) in version
    2.1.0 of the amazon.aws collection.
short_description: Creates, updates or destroys an Amazon ELB
author:
  - "Jim Dalton (@jsdalton)"
  - "Mark Chappell (@tremble)"
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
      - The name of an ELB must be less than 32 characters and unique per-region per-account.
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
      proxy_protocol:
        description:
          - Enable proxy protocol for the listener.
          - Beware, ELB controls for the proxy protocol are based on the
            I(instance_port).  If you have multiple listeners talking to
            the same I(instance_port), this will affect all of them.
        type: bool
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
      - A dictionary of health check configuration settings (see examples).
    type: dict
    suboptions:
      ping_protocol:
        description:
        - The protocol which the ELB health check will use when performing a
          health check.
        - Valid values are C('HTTP'), C('HTTPS'), C('TCP') and C('SSL').
        required: true
        type: str
      ping_path:
        description:
        - The URI path which the ELB health check will query when performing a
          health check.
        - Required when I(ping_protocol=HTTP) or I(ping_protocol=HTTPS).
        required: false
        type: str
      ping_port:
        description:
        - The TCP port to which the ELB will connect when performing a
          health check.
        required: true
        type: int
      interval:
        description:
        - The approximate interval, in seconds, between health checks of an individual instance.
        required: true
        type: int
      timeout:
        description:
        - The amount of time, in seconds, after which no response means a failed health check.
        aliases: ['response_timeout']
        required: true
        type: int
      unhealthy_threshold:
        description:
        - The number of consecutive health check failures required before moving
          the instance to the Unhealthy state.
        required: true
        type: int
      healthy_threshold:
        description:
        - The number of consecutive health checks successes required before moving
          the instance to the Healthy state.
        required: true
        type: int
  access_logs:
    description:
      - A dictionary of access logs configuration settings (see examples).
    type: dict
    suboptions:
      enabled:
        description:
        - When set to C(True) will configure delivery of access logs to an S3
          bucket.
        - When set to C(False) will disable delivery of access logs.
        required: false
        type: bool
        default: true
      s3_location:
        description:
        - The S3 bucket to deliver access logs to.
        - See U(https://docs.aws.amazon.com/elasticloadbalancing/latest/classic/enable-access-logs.html)
          for more information about the necessary S3 bucket policies.
        - Required when I(enabled=True).
        required: false
        type: str
      s3_prefix:
        description:
        - Where in the S3 bucket to deliver the logs.
        - If the prefix is not provided or set to C(""), the log is placed at the root level of the bucket.
        required: false
        type: str
        default: ""
      interval:
        description:
        - The interval for publishing the access logs to S3.
        required: false
        type: int
        default: 60
        choices: [ 5, 60 ]
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
        a new ELB created.
      - Defaults to I(scheme=internet-facing).
    type: str
    choices: ["internal", "internet-facing"]
  connection_draining_timeout:
    description:
      - Wait a specified timeout allowing connections to drain before terminating an instance.
      - Set to C(0) to disable connection draining.
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
      - A dictionary of stickiness policy settings.
      - Policy will be applied to all listeners (see examples).
    type: dict
    suboptions:
      type:
        description:
          - The type of stickiness policy to apply.
          - Required if I(enabled=true).
          - Ignored if I(enabled=false).
        required: false
        type: 'str'
        choices: ['application','loadbalancer']
      enabled:
        description:
          - When I(enabled=false) session stickiness will be disabled for all listeners.
        required: false
        type: bool
        default: true
      cookie:
        description:
          - The name of the application cookie used for stickiness.
          - Required if I(enabled=true) and I(type=application).
          - Ignored if I(enabled=false).
        required: false
        type: str
      expiration:
        description:
          - The time period, in seconds, after which the cookie should be considered stale.
          - If this parameter is not specified, the stickiness session lasts for the duration of the browser session.
          - Ignored if I(enabled=false).
        required: false
        type: int
  wait:
    description:
      - When creating, deleting, or adding instances to an ELB, if I(wait=true)
        Ansible will wait for both the load balancer and related network interfaces
        to finish creating/deleting.
      - Support for waiting when adding instances was added in release 2.1.0.
    type: bool
    default: false
  wait_timeout:
    description:
      - Used in conjunction with wait. Number of seconds to wait for the ELB to be terminated.
      - A maximum of 600 seconds (10 minutes) is allowed.
    type: int
    default: 180

notes:
- The ec2_elb fact previously set by this module was deprecated in release 2.1.0 and since release
  4.0.0 is no longer set.
- Support for I(purge_tags) was added in release 2.1.0.

extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
- amazon.aws.tags
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

RETURN = '''
elb:
  description: Load Balancer attributes
  returned: always
  type: dict
  contains:
    app_cookie_policy:
      description: The name of the policy used to control if the ELB is using a application cookie stickiness policy.
      type: str
      sample: ec2-elb-lb-AppCookieStickinessPolicyType
      returned: when state is not 'absent'
    backends:
      description: A description of the backend policy applied to the ELB (instance-port:policy-name).
      type: str
      sample: 8181:ProxyProtocol-policy
      returned: when state is not 'absent'
    connection_draining_timeout:
      description: The maximum time, in seconds, to keep the existing connections open before deregistering the instances.
      type: int
      sample: 25
      returned: when state is not 'absent'
    cross_az_load_balancing:
      description: Either C('yes') if cross-AZ load balancing is enabled, or C('no') if cross-AZ load balancing is disabled.
      type: str
      sample: 'yes'
      returned: when state is not 'absent'
    dns_name:
      description: The DNS name of the ELB.
      type: str
      sample: internal-ansible-test-935c585850ac-1516306744.us-east-1.elb.amazonaws.com
      returned: when state is not 'absent'
    health_check:
      description: A dictionary describing the health check used for the ELB.
      type: dict
      returned: when state is not 'absent'
      contains:
        healthy_threshold:
          description: The number of consecutive successful health checks before marking an instance as healthy.
          type: int
          sample: 2
        interval:
          description: The time, in seconds, between each health check.
          type: int
          sample: 10
        target:
          description: The Protocol, Port, and for HTTP(S) health checks the path tested by the health check.
          type: str
          sample: TCP:22
        timeout:
          description: The time, in seconds, after which an in progress health check is considered failed due to a timeout.
          type: int
          sample: 5
        unhealthy_threshold:
          description: The number of consecutive failed health checks before marking an instance as unhealthy.
          type: int
          sample: 2
    hosted_zone_id:
      description: The ID of the Amazon Route 53 hosted zone for the load balancer.
      type: str
      sample: Z35SXDOTRQ7X7K
      returned: when state is not 'absent'
    hosted_zone_name:
      description: The DNS name of the load balancer when using a custom hostname.
      type: str
      sample: 'ansible-module.example'
      returned: when state is not 'absent'
    idle_timeout:
      description: The length of of time before an idle connection is dropped by the ELB.
      type: int
      sample: 50
      returned: when state is not 'absent'
    in_service_count:
      description: The number of instances attached to the ELB in an in-service state.
      type: int
      sample: 1
      returned: when state is not 'absent'
    instance_health:
      description: A list of dictionaries describing the health of each instance attached to the ELB.
      type: list
      elements: dict
      returned: when state is not 'absent'
      contains:
        description:
          description: A human readable description of why the instance is not in service.
          type: str
          sample: N/A
          returned: when state is not 'absent'
        instance_id:
          description: The ID of the instance.
          type: str
          sample: i-03dcc8953a03d6435
          returned: when state is not 'absent'
        reason_code:
          description: A code describing why the instance is not in service.
          type: str
          sample: N/A
          returned: when state is not 'absent'
        state:
          description: The current service state of the instance.
          type: str
          sample: InService
          returned: when state is not 'absent'
    instances:
      description: A list of the IDs of instances attached to the ELB.
      type: list
      elements: str
      sample: ['i-03dcc8953a03d6435']
      returned: when state is not 'absent'
    lb_cookie_policy:
      description: The name of the policy used to control if the ELB is using a cookie stickiness policy.
      type: str
      sample: ec2-elb-lb-LBCookieStickinessPolicyType
      returned: when state is not 'absent'
    listeners:
      description:
      - A list of lists describing the listeners attached to the ELB.
      - The nested list contains the listener port, the instance port, the listener protoco, the instance port,
        and where appropriate the ID of the SSL certificate for the port.
      type: list
      elements: list
      sample: [[22, 22, 'TCP', 'TCP'], [80, 8181, 'HTTP', 'HTTP']]
      returned: when state is not 'absent'
    name:
      description: The name of the ELB.  This name is unique per-region, per-account.
      type: str
      sample: ansible-test-935c585850ac
      returned: when state is not 'absent'
    out_of_service_count:
      description: The number of instances attached to the ELB in an out-of-service state.
      type: int
      sample: 0
      returned: when state is not 'absent'
    proxy_policy:
      description: The name of the policy used to control if the ELB operates using the Proxy protocol.
      type: str
      sample: ProxyProtocol-policy
      returned: when the proxy protocol policy exists.
    region:
      description: The AWS region in which the ELB is running.
      type: str
      sample: us-east-1
      returned: always
    scheme:
      description: Whether the ELB is an C('internal') or a C('internet-facing') load balancer.
      type: str
      sample: internal
      returned: when state is not 'absent'
    security_group_ids:
      description: A list of the IDs of the Security Groups attached to the ELB.
      type: list
      elements: str
      sample: ['sg-0c12ebd82f2fb97dc', 'sg-01ec7378d0c7342e6']
      returned: when state is not 'absent'
    status:
      description: A minimal description of the current state of the ELB.  Valid values are C('exists'), C('gone'), C('deleted'), C('created').
      type: str
      sample: exists
      returned: always
    subnets:
      description: A list of the subnet IDs attached to the ELB.
      type: list
      elements: str
      sample: ['subnet-00d9d0f70c7e5f63c', 'subnet-03fa5253586b2d2d5']
      returned: when state is not 'absent'
    tags:
      description: A dictionary describing the tags attached to the ELB.
      type: dict
      sample: {'Name': 'ansible-test-935c585850ac', 'ExampleTag': 'Example Value'}
      returned: when state is not 'absent'
    unknown_instance_state_count:
      description: The number of instances attached to the ELB in an unknown state.
      type: int
      sample: 0
      returned: when state is not 'absent'
    zones:
      description: A list of the AWS regions in which the ELB is running.
      type: list
      elements: str
      sample: ['us-east-1b', 'us-east-1a']
      returned: when state is not 'absent'
'''

try:
    import botocore
except ImportError:
    pass  # Taken care of by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.core import scrub_none_parameters
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import compare_aws_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import get_ec2_security_group_ids_from_names
from ansible_collections.amazon.aws.plugins.module_utils.waiters import get_waiter


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
        self.purge_tags = module.params['purge_tags']

        self.changed = False
        self.status = 'gone'

        retry_decorator = AWSRetry.jittered_backoff()
        self.client = self.module.client('elb', retry_decorator=retry_decorator)
        self.ec2_client = self.module.client('ec2', retry_decorator=retry_decorator)

        security_group_names = module.params['security_group_names']
        self.security_group_ids = module.params['security_group_ids']

        self._update_descriptions()

        if security_group_names:
            # Use the subnets attached to the VPC to find which VPC we're in and
            # limit the search
            if self.elb.get('Subnets', None):
                subnets = set(self.elb.get('Subnets') + list(self.subnets or []))
            else:
                subnets = set(self.subnets)
            if subnets:
                vpc_id = self._get_vpc_from_subnets(subnets)
            else:
                vpc_id = None
            try:
                self.security_group_ids = self._get_ec2_security_group_ids_from_names(
                    sec_group_list=security_group_names, vpc_id=vpc_id)
            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                module.fail_json_aws(e, msg="Failed to convert security group names to IDs, try using security group IDs rather than names")

    def _update_descriptions(self):
        try:
            self.elb = self._get_elb()
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg='Unable to describe load balancer')
        try:
            self.elb_attributes = self._get_elb_attributes()
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg='Unable to describe load balancer attributes')
        try:
            self.elb_policies = self._get_elb_policies()
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg='Unable to describe load balancer policies')
        try:
            self.elb_health = self._get_elb_instance_health()
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg='Unable to describe load balancer instance health')

    # We have a number of complex parameters which can't be validated by
    # AnsibleModule or are only required if the ELB doesn't exist.
    def validate_params(self, state=None):
        problem_found = False
        # Validate that protocol is one of the permitted values
        problem_found |= self._validate_listeners(self.listeners)
        problem_found |= self._validate_health_check(self.health_check)
        problem_found |= self._validate_stickiness(self.stickiness)
        if state == 'present':
            # When creating a new ELB
            problem_found |= self._validate_creation_requirements()
        problem_found |= self._validate_access_logs(self.access_logs)

    # Pass check_mode down through to the module
    @property
    def check_mode(self):
        return self.module.check_mode

    def _get_elb_policies(self):
        try:
            attributes = self.client.describe_load_balancer_policies(LoadBalancerName=self.name)
        except is_boto3_error_code(['LoadBalancerNotFound', 'LoadBalancerAttributeNotFoundException']):
            return {}
        except is_boto3_error_code('AccessDenied'):  # pylint: disable=duplicate-except
            # Be forgiving if we can't see the attributes
            # Note: This will break idempotency if someone has set but not describe
            self.module.warn('Access Denied trying to describe load balancer policies')
            return {}
        return attributes['PolicyDescriptions']

    def _get_elb_instance_health(self):
        try:
            instance_health = self.client.describe_instance_health(LoadBalancerName=self.name)
        except is_boto3_error_code(['LoadBalancerNotFound', 'LoadBalancerAttributeNotFoundException']):
            return []
        except is_boto3_error_code('AccessDenied'):  # pylint: disable=duplicate-except
            # Be forgiving if we can't see the attributes
            # Note: This will break idempotency if someone has set but not describe
            self.module.warn('Access Denied trying to describe instance health')
            return []
        return instance_health['InstanceStates']

    def _get_elb_attributes(self):
        try:
            attributes = self.client.describe_load_balancer_attributes(LoadBalancerName=self.name)
        except is_boto3_error_code(['LoadBalancerNotFound', 'LoadBalancerAttributeNotFoundException']):
            return {}
        except is_boto3_error_code('AccessDenied'):  # pylint: disable=duplicate-except
            # Be forgiving if we can't see the attributes
            # Note: This will break idempotency if someone has set but not describe
            self.module.warn('Access Denied trying to describe load balancer attributes')
            return {}
        return attributes['LoadBalancerAttributes']

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
            return False
        return True

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
        if self.tags:
            params['Tags'] = ansible_dict_to_boto3_tag_list(self.tags)

        if not self.check_mode:
            self.client.create_load_balancer(aws_retry=True, **params)
            # create_load_balancer only returns the DNS name
            self.elb = self._get_elb()
        self.changed = True
        self.status = 'created'
        return True

    def _format_listener(self, listener, inject_protocol=False):
        """Formats listener into the format needed by the
        ELB API"""

        listener = scrub_none_parameters(listener)

        for protocol in ['protocol', 'instance_protocol']:
            if protocol in listener:
                listener[protocol] = listener[protocol].upper()

        if inject_protocol and 'instance_protocol' not in listener:
            listener['instance_protocol'] = listener['protocol']

        # Remove proxy_protocol, it has to be handled as a policy
        listener.pop('proxy_protocol', None)

        ssl_id = listener.pop('ssl_certificate_id', None)

        formatted_listener = snake_dict_to_camel_dict(listener, True)
        if ssl_id:
            formatted_listener['SSLCertificateId'] = ssl_id

        return formatted_listener

    def _format_healthcheck_target(self):
        """Compose target string from healthcheck parameters"""
        protocol = self.health_check['ping_protocol'].upper()
        path = ""

        if protocol in ['HTTP', 'HTTPS'] and 'ping_path' in self.health_check:
            path = self.health_check['ping_path']

        return "%s:%s%s" % (protocol, self.health_check['ping_port'], path)

    def _format_healthcheck(self):
        return dict(
            Target=self._format_healthcheck_target(),
            Timeout=self.health_check['timeout'],
            Interval=self.health_check['interval'],
            UnhealthyThreshold=self.health_check['unhealthy_threshold'],
            HealthyThreshold=self.health_check['healthy_threshold'],
        )

    def ensure_ok(self):
        """Create the ELB"""
        if not self.elb:
            try:
                self._create_elb()
            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                self.module.fail_json_aws(e, msg="Failed to create load balancer")
            try:
                self.elb_attributes = self._get_elb_attributes()
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                self.module.fail_json_aws(e, msg='Unable to describe load balancer attributes')
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
                try:
                    self.elb_attributes = self._get_elb_attributes()
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    self.module.fail_json_aws(e, msg='Unable to describe load balancer attributes')
            else:
                self._set_subnets()
                self._set_zones()
                self._set_security_groups()
                self._set_elb_listeners()
                self._set_tags()

        self._set_health_check()
        self._set_elb_attributes()
        self._set_backend_policies()
        self._set_stickiness_policies()
        self._set_instance_ids()

#        if self._check_attribute_support('access_log'):
#            self._set_access_log()

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

    def get_load_balancer(self):
        self._update_descriptions()
        elb = dict(self.elb or {})
        if not elb:
            return {}

        elb['LoadBalancerAttributes'] = self.elb_attributes
        elb['LoadBalancerPolicies'] = self.elb_policies
        load_balancer = camel_dict_to_snake_dict(elb)
        try:
            load_balancer['tags'] = self._get_tags()
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to get load balancer tags")

        return load_balancer

    def get_info(self):
        self._update_descriptions()

        if not self.elb:
            return dict(
                name=self.name,
                status=self.status,
                region=self.module.region
            )
        check_elb = dict(self.elb)
        check_elb_attrs = dict(self.elb_attributes or {})
        check_policies = check_elb.get('Policies', {})
        try:
            lb_cookie_policy = check_policies['LBCookieStickinessPolicies'][0]['PolicyName']
        except (KeyError, IndexError):
            lb_cookie_policy = None
        try:
            app_cookie_policy = check_policies['AppCookieStickinessPolicies'][0]['PolicyName']
        except (KeyError, IndexError):
            app_cookie_policy = None

        health_check = camel_dict_to_snake_dict(check_elb.get('HealthCheck', {}))

        backend_policies = list()
        for port, policies in self._get_backend_policies().items():
            for policy in policies:
                backend_policies.append("{0}:{1}".format(port, policy))

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
            proxy_policy=self._get_proxy_protocol_policy(),
            backends=backend_policies,
            instances=self._get_instance_ids(),
            out_of_service_count=0,
            in_service_count=0,
            unknown_instance_state_count=0,
            region=self.module.region,
            health_check=health_check,
        )

        instance_health = camel_dict_to_snake_dict(dict(InstanceHealth=self.elb_health))
        info.update(instance_health)

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

        try:
            info['connection_draining_timeout'] = check_elb_attrs['ConnectionDraining']['Timeout']
        except KeyError:
            pass
        try:
            info['idle_timeout'] = check_elb_attrs['ConnectionSettings']['IdleTimeout']
        except KeyError:
            pass
        try:
            is_enabled = check_elb_attrs['CrossZoneLoadBalancing']['Enabled']
            info['cross_az_load_balancing'] = 'yes' if is_enabled else 'no'
        except KeyError:
            pass

        # # return stickiness info?

        try:
            info['tags'] = self._get_tags()
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to get load balancer tags")

        return info

    @property
    def _waiter_config(self):
        delay = min(10, self.wait_timeout)
        max_attempts = (self.wait_timeout // delay)
        return {'Delay': delay, 'MaxAttempts': max_attempts}

    def _wait_for_elb_created(self):
        if self.check_mode:
            return True

        waiter = get_waiter(self.client, 'load_balancer_created')

        try:
            waiter.wait(
                WaiterConfig=self._waiter_config,
                LoadBalancerNames=[self.name],
            )
        except botocore.exceptions.WaiterError as e:
            self.module.fail_json_aws(e, 'Timeout waiting for ELB removal')

        return True

    def _wait_for_elb_interface_created(self):
        if self.check_mode:
            return True
        waiter = get_waiter(self.ec2_client, 'network_interface_available')

        filters = ansible_dict_to_boto3_filter_list(
            {'requester-id': 'amazon-elb',
             'description': 'ELB {0}'.format(self.name)}
        )

        try:
            waiter.wait(
                WaiterConfig=self._waiter_config,
                Filters=filters,
            )
        except botocore.exceptions.WaiterError as e:
            self.module.fail_json_aws(e, 'Timeout waiting for ELB Interface removal')

        return True

    def _wait_for_elb_removed(self):
        if self.check_mode:
            return True

        waiter = get_waiter(self.client, 'load_balancer_deleted')

        try:
            waiter.wait(
                WaiterConfig=self._waiter_config,
                LoadBalancerNames=[self.name],
            )
        except botocore.exceptions.WaiterError as e:
            self.module.fail_json_aws(e, 'Timeout waiting for ELB removal')

        return True

    def _wait_for_elb_interface_removed(self):
        if self.check_mode:
            return True

        waiter = get_waiter(self.ec2_client, 'network_interface_deleted')

        filters = ansible_dict_to_boto3_filter_list(
            {'requester-id': 'amazon-elb',
             'description': 'ELB {0}'.format(self.name)}
        )

        try:
            waiter.wait(
                WaiterConfig=self._waiter_config,
                Filters=filters,
            )
        except botocore.exceptions.WaiterError as e:
            self.module.fail_json_aws(e, 'Timeout waiting for ELB Interface removal')

        return True

    def _wait_for_instance_state(self, waiter_name, instances):
        if not instances:
            return False

        if self.check_mode:
            return True

        waiter = get_waiter(self.client, waiter_name)

        instance_list = list(dict(InstanceId=instance) for instance in instances)

        try:
            waiter.wait(
                WaiterConfig=self._waiter_config,
                LoadBalancerName=self.name,
                Instances=instance_list,
            )
        except botocore.exceptions.WaiterError as e:
            self.module.fail_json_aws(e, 'Timeout waiting for ELB Instance State')

        return True

    def _create_elb_listeners(self, listeners):
        """Takes a list of listener definitions and creates them"""
        if not listeners:
            return False
        self.changed = True
        if self.check_mode:
            return True

        self.client.create_load_balancer_listeners(
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

        self.client.delete_load_balancer_listeners(
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

    def _set_health_check(self):
        if not self.health_check:
            return False

        """Set health check values on ELB as needed"""
        health_check_config = self._format_healthcheck()

        if health_check_config == self.elb['HealthCheck']:
            return False

        self.changed = True
        if self.check_mode:
            return True
        try:
            self.client.configure_health_check(
                aws_retry=True,
                LoadBalancerName=self.name,
                HealthCheck=health_check_config,
            )
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to apply healthcheck to load balancer")

        return True

    def _set_elb_attributes(self):
        attributes = {}
        if self.cross_az_load_balancing is not None:
            attr = dict(Enabled=self.cross_az_load_balancing)
            if not self.elb_attributes.get('CrossZoneLoadBalancing', None) == attr:
                attributes['CrossZoneLoadBalancing'] = attr

        if self.idle_timeout is not None:
            attr = dict(IdleTimeout=self.idle_timeout)
            if not self.elb_attributes.get('ConnectionSettings', None) == attr:
                attributes['ConnectionSettings'] = attr

        if self.connection_draining_timeout is not None:
            curr_attr = dict(self.elb_attributes.get('ConnectionDraining', {}))
            if self.connection_draining_timeout == 0:
                attr = dict(Enabled=False)
                curr_attr.pop('Timeout', None)
            else:
                attr = dict(Enabled=True, Timeout=self.connection_draining_timeout)
            if not curr_attr == attr:
                attributes['ConnectionDraining'] = attr

        if self.access_logs is not None:
            curr_attr = dict(self.elb_attributes.get('AccessLog', {}))
            # For disabling we only need to compare and pass 'Enabled'
            if not self.access_logs.get('enabled'):
                curr_attr = dict(Enabled=curr_attr.get('Enabled', False))
                attr = dict(Enabled=self.access_logs.get('enabled'))
            else:
                attr = dict(
                    Enabled=True,
                    S3BucketName=self.access_logs['s3_location'],
                    S3BucketPrefix=self.access_logs.get('s3_prefix', ''),
                    EmitInterval=self.access_logs.get('interval', 60),
                )
            if not curr_attr == attr:
                attributes['AccessLog'] = attr

        if not attributes:
            return False

        self.changed = True
        if self.check_mode:
            return True

        try:
            self.client.modify_load_balancer_attributes(
                aws_retry=True,
                LoadBalancerName=self.name,
                LoadBalancerAttributes=attributes
            )
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to apply load balancer attrbutes")

    def _proxy_policy_name(self):
        return 'ProxyProtocol-policy'

    def _policy_name(self, policy_type):
        return 'ec2-elb-lb-{0}'.format(policy_type)

    def _get_listener_policies(self):
        """Get a list of listener policies mapped to the LoadBalancerPort"""
        if not self.elb:
            return {}
        listener_descriptions = self.elb.get('ListenerDescriptions', [])
        policies = {l['LoadBalancerPort']: l['PolicyNames'] for l in listener_descriptions}
        return policies

    def _set_listener_policies(self, port, policies):
        self.changed = True
        if self.check_mode:
            return True

        try:
            self.client.set_load_balancer_policies_of_listener(
                aws_retry=True,
                LoadBalancerName=self.name,
                LoadBalancerPort=port,
                PolicyNames=list(policies),
            )
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to set load balancer listener policies",
                                      port=port, policies=policies)

        return True

    def _get_stickiness_policies(self):
        """Get a list of AppCookieStickinessPolicyType and LBCookieStickinessPolicyType policies"""
        return list(p['PolicyName'] for p in self.elb_policies if p['PolicyTypeName'] in ['AppCookieStickinessPolicyType', 'LBCookieStickinessPolicyType'])

    def _get_app_stickness_policy_map(self):
        """Get a mapping of App Cookie Stickiness policy names to their definitions"""
        policies = self.elb.get('Policies', {}).get('AppCookieStickinessPolicies', [])
        return {p['PolicyName']: p for p in policies}

    def _get_lb_stickness_policy_map(self):
        """Get a mapping of LB Cookie Stickiness policy names to their definitions"""
        policies = self.elb.get('Policies', {}).get('LBCookieStickinessPolicies', [])
        return {p['PolicyName']: p for p in policies}

    def _purge_stickiness_policies(self):
        """Removes all stickiness policies from all Load Balancers"""
        # Used when purging stickiness policies or updating a policy (you can't
        # update a policy while it's connected to a Listener)
        stickiness_policies = set(self._get_stickiness_policies())
        listeners = self.elb['ListenerDescriptions']
        changed = False
        for listener in listeners:
            port = listener['Listener']['LoadBalancerPort']
            policies = set(listener['PolicyNames'])
            new_policies = set(policies - stickiness_policies)
            if policies != new_policies:
                changed |= self._set_listener_policies(port, new_policies)

        return changed

    def _set_stickiness_policies(self):
        if self.stickiness is None:
            return False

        # Make sure that the list of policies and listeners is up to date, we're
        # going to make changes to all listeners
        self._update_descriptions()

        if not self.stickiness['enabled']:
            return self._purge_stickiness_policies()

        if self.stickiness['type'] == 'loadbalancer':
            policy_name = self._policy_name('LBCookieStickinessPolicyType')
            expiration = self.stickiness.get('expiration')
            if not expiration:
                expiration = 0
            policy_description = dict(
                PolicyName=policy_name,
                CookieExpirationPeriod=expiration,
            )
            existing_policies = self._get_lb_stickness_policy_map()
            add_method = self.client.create_lb_cookie_stickiness_policy
        elif self.stickiness['type'] == 'application':
            policy_name = self._policy_name('AppCookieStickinessPolicyType')
            policy_description = dict(
                PolicyName=policy_name,
                CookieName=self.stickiness.get('cookie', 0)
            )
            existing_policies = self._get_app_stickness_policy_map()
            add_method = self.client.create_app_cookie_stickiness_policy
        else:
            # We shouldn't get here...
            self.module.fail_json(
                msg='Unknown stickiness policy {0}'.format(
                    self.stickiness['type']
                )
            )

        changed = False
        # To update a policy we need to delete then re-add, and we can only
        # delete if the policy isn't attached to a listener
        if policy_name in existing_policies:
            if existing_policies[policy_name] != policy_description:
                changed |= self._purge_stickiness_policies()

        if changed:
            self._update_descriptions()

        changed |= self._set_stickiness_policy(
            method=add_method,
            description=policy_description,
            existing_policies=existing_policies,
        )

        listeners = self.elb['ListenerDescriptions']
        for listener in listeners:
            changed |= self._set_lb_stickiness_policy(
                listener=listener,
                policy=policy_name
            )
        return changed

    def _delete_loadbalancer_policy(self, policy_name):
        self.changed = True
        if self.check_mode:
            return True

        try:
            self.client.delete_load_balancer_policy(
                LoadBalancerName=self.name,
                PolicyName=policy_name,
            )
        except is_boto3_error_code('InvalidConfigurationRequest'):
            # Already deleted
            return False
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
            self.module.fail_json_aws(e, msg="Failed to load balancer policy {0}".format(policy_name))
        return True

    def _set_stickiness_policy(self, method, description, existing_policies=None):
        changed = False
        if existing_policies:
            policy_name = description['PolicyName']
            if policy_name in existing_policies:
                if existing_policies[policy_name] == description:
                    return False
                if existing_policies[policy_name] != description:
                    changed |= self._delete_loadbalancer_policy(policy_name)

        self.changed = True
        changed = True

        if self.check_mode:
            return changed

        # This needs to be in place for comparisons, but not passed to the
        # method.
        if not description.get('CookieExpirationPeriod', None):
            description.pop('CookieExpirationPeriod', None)

        try:
            method(
                aws_retry=True,
                LoadBalancerName=self.name,
                **description
            )
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to create load balancer stickiness policy",
                                      description=description)
        return changed

    def _set_lb_stickiness_policy(self, listener, policy):
        port = listener['Listener']['LoadBalancerPort']
        stickiness_policies = set(self._get_stickiness_policies())
        changed = False

        policies = set(listener['PolicyNames'])
        new_policies = list(policies - stickiness_policies)
        new_policies.append(policy)

        if policies != set(new_policies):
            changed |= self._set_listener_policies(port, new_policies)

        return changed

    def _get_backend_policies(self):
        """Get a list of backend policies mapped to the InstancePort"""
        if not self.elb:
            return {}
        server_descriptions = self.elb.get('BackendServerDescriptions', [])
        policies = {b['InstancePort']: b['PolicyNames'] for b in server_descriptions}
        return policies

    def _get_proxy_protocol_policy(self):
        """Returns the name of the name of the ProxyPolicy if created"""
        all_proxy_policies = self._get_proxy_policies()
        if not all_proxy_policies:
            return None
        if len(all_proxy_policies) == 1:
            return all_proxy_policies[0]
        return all_proxy_policies

    def _get_proxy_policies(self):
        """Get a list of ProxyProtocolPolicyType policies"""
        return list(p['PolicyName'] for p in self.elb_policies if p['PolicyTypeName'] == 'ProxyProtocolPolicyType')

    def _get_policy_map(self):
        """Get a mapping of Policy names to their definitions"""
        return {p['PolicyName']: p for p in self.elb_policies}

    def _set_backend_policies(self):
        """Sets policies for all backends"""
        # Currently only supports setting ProxyProtocol policies
        if not self.listeners:
            return False

        ensure_proxy_protocol = False
        backend_policies = self._get_backend_policies()
        proxy_policies = set(self._get_proxy_policies())

        proxy_ports = dict()
        for listener in self.listeners:
            proxy_protocol = listener.get('proxy_protocol', None)
            # Only look at the listeners for which proxy_protocol is defined
            if proxy_protocol is None:
                next
            instance_port = listener.get('instance_port')
            if proxy_ports.get(instance_port, None) is not None:
                if proxy_ports[instance_port] != proxy_protocol:
                    self.module.fail_json_aws(
                        'proxy_protocol set to conflicting values for listeners'
                        ' on port {0}'.format(instance_port))
            proxy_ports[instance_port] = proxy_protocol

        if not proxy_ports:
            return False

        changed = False

        # If anyone's set proxy_protocol to true, make sure we have our policy
        # in place.
        proxy_policy_name = self._proxy_policy_name()
        if any(proxy_ports.values()):
            changed |= self._set_proxy_protocol_policy(proxy_policy_name)

        for port in proxy_ports:
            current_policies = set(backend_policies.get(port, []))
            new_policies = list(current_policies - proxy_policies)
            if proxy_ports[port]:
                new_policies.append(proxy_policy_name)

            changed |= self._set_backend_policy(port, new_policies)

        return changed

    def _set_backend_policy(self, port, policies):
        backend_policies = self._get_backend_policies()
        current_policies = set(backend_policies.get(port, []))

        if current_policies == set(policies):
            return False

        self.changed = True

        if self.check_mode:
            return True

        try:
            self.client.set_load_balancer_policies_for_backend_server(
                aws_retry=True,
                LoadBalancerName=self.name,
                InstancePort=port,
                PolicyNames=policies,
            )
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to set load balancer backend policies",
                                      port=port, policies=policies)

        return True

    def _set_proxy_protocol_policy(self, policy_name):
        """Install a proxy protocol policy if needed"""
        policy_map = self._get_policy_map()

        policy_attributes = [dict(AttributeName='ProxyProtocol', AttributeValue='true')]

        proxy_policy = dict(
            PolicyName=policy_name,
            PolicyTypeName='ProxyProtocolPolicyType',
            PolicyAttributeDescriptions=policy_attributes,
        )

        existing_policy = policy_map.get(policy_name)
        if proxy_policy == existing_policy:
            return False

        if existing_policy is not None:
            self.module.fail_json(
                msg="Unable to configure ProxyProtocol policy. "
                    "Policy with name {0} already exists and doesn't match.".format(policy_name),
                policy=proxy_policy, existing_policy=existing_policy,
            )

        proxy_policy['PolicyAttributes'] = proxy_policy.pop('PolicyAttributeDescriptions')
        proxy_policy['LoadBalancerName'] = self.name
        self.changed = True

        if self.check_mode:
            return True

        try:
            self.client.create_load_balancer_policy(
                aws_retry=True,
                **proxy_policy
            )
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to create load balancer policy", policy=proxy_policy)

        return True

    def _get_instance_ids(self):
        """Get the current list of instance ids installed in the elb"""
        elb = self.elb or {}
        return list(i['InstanceId'] for i in elb.get('Instances', []))

    def _change_instances(self, method, instances):
        if not instances:
            return False

        self.changed = True
        if self.check_mode:
            return True

        instance_id_list = list({'InstanceId': i} for i in instances)
        try:
            method(
                aws_retry=True,
                LoadBalancerName=self.name,
                Instances=instance_id_list,
            )
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to change instance registration",
                                      instances=instance_id_list, name=self.name)
        return True

    def _set_instance_ids(self):
        """Register or deregister instances from an lb instance"""
        new_instances = self.instance_ids or []
        existing_instances = self._get_instance_ids()

        instances_to_add = set(new_instances) - set(existing_instances)
        if self.purge_instance_ids:
            instances_to_remove = set(existing_instances) - set(new_instances)
        else:
            instances_to_remove = []

        changed = False

        changed |= self._change_instances(self.client.register_instances_with_load_balancer,
                                          instances_to_add)
        if self.wait:
            self._wait_for_instance_state('instance_in_service', list(instances_to_add))
        changed |= self._change_instances(self.client.deregister_instances_from_load_balancer,
                                          instances_to_remove)
        if self.wait:
            self._wait_for_instance_state('instance_deregistered', list(instances_to_remove))

        return changed

    def _get_tags(self):
        tags = self.client.describe_tags(aws_retry=True,
                                         LoadBalancerNames=[self.name])
        if not tags:
            return {}
        try:
            tags = tags['TagDescriptions'][0]['Tags']
        except (KeyError, TypeError):
            return {}
        return boto3_tag_list_to_ansible_dict(tags)

    def _add_tags(self, tags_to_set):
        if not tags_to_set:
            return False
        self.changed = True
        if self.check_mode:
            return True
        tags_to_add = ansible_dict_to_boto3_tag_list(tags_to_set)
        self.client.add_tags(LoadBalancerNames=[self.name], Tags=tags_to_add)
        return True

    def _remove_tags(self, tags_to_unset):
        if not tags_to_unset:
            return False
        self.changed = True
        if self.check_mode:
            return True
        tags_to_remove = [dict(Key=tagkey) for tagkey in tags_to_unset]
        self.client.remove_tags(LoadBalancerNames=[self.name], Tags=tags_to_remove)
        return True

    def _set_tags(self):
        """Add/Delete tags"""
        if self.tags is None:
            return False

        try:
            current_tags = self._get_tags()
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to get load balancer tags")

        tags_to_set, tags_to_unset = compare_aws_tags(current_tags, self.tags,
                                                      self.purge_tags)

        changed = False
        try:
            changed |= self._remove_tags(tags_to_unset)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to remove load balancer tags")
        try:
            changed |= self._add_tags(tags_to_set)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to add load balancer tags")

        return changed

    def _validate_stickiness(self, stickiness):
        problem_found = False
        if not stickiness:
            return problem_found
        if not stickiness['enabled']:
            return problem_found
        if stickiness['type'] == 'application':
            if not stickiness.get('cookie'):
                problem_found = True
                self.module.fail_json(
                    msg='cookie must be specified when stickiness type is "application"',
                    stickiness=stickiness,
                )
            if stickiness.get('expiration'):
                self.warn(
                    msg='expiration is ignored when stickiness type is "application"',)
        if stickiness['type'] == 'loadbalancer':
            if stickiness.get('cookie'):
                self.warn(
                    msg='cookie is ignored when stickiness type is "loadbalancer"',)
        return problem_found

    def _validate_access_logs(self, access_logs):
        problem_found = False
        if not access_logs:
            return problem_found
        if not access_logs['enabled']:
            return problem_found
        if not access_logs.get('s3_location', None):
            problem_found = True
            self.module.fail_json(
                msg='s3_location must be provided when access_logs.state is "present"')
        return problem_found

    def _validate_creation_requirements(self):
        if self.elb:
            return False
        problem_found = False
        if not self.subnets and not self.zones:
            problem_found = True
            self.module.fail_json(
                msg='One of subnets or zones must be provided when creating an ELB')
        if not self.listeners:
            problem_found = True
            self.module.fail_json(
                msg='listeners must be provided when creating an ELB')
        return problem_found

    def _validate_listeners(self, listeners):
        if not listeners:
            return False
        return any(self._validate_listener(listener) for listener in listeners)

    def _validate_listener(self, listener):
        problem_found = False
        if not listener:
            return problem_found
        for protocol in ['instance_protocol', 'protocol']:
            value = listener.get(protocol, None)
            problem = self._validate_protocol(value)
            problem_found |= problem
            if problem:
                self.module.fail_json(
                    msg='Invalid protocol ({0}) in listener'.format(value),
                    listener=listener)
        return problem_found

    def _validate_health_check(self, health_check):
        if not health_check:
            return False
        protocol = health_check['ping_protocol']
        if self._validate_protocol(protocol):
            self.module.fail_json(
                msg='Invalid protocol ({0}) defined in health check'.format(protocol),
                health_check=health_check,)
        if protocol.upper() in ['HTTP', 'HTTPS']:
            if not health_check['ping_path']:
                self.module.fail_json(
                    msg='For HTTP and HTTPS health checks a ping_path must be provided',
                    health_check=health_check,)
        return False

    def _validate_protocol(self, protocol):
        if not protocol:
            return False
        return protocol.upper() not in ['HTTP', 'HTTPS', 'TCP', 'SSL']

    @AWSRetry.jittered_backoff()
    def _describe_loadbalancer(self, lb_name):
        paginator = self.client.get_paginator('describe_load_balancers')
        return paginator.paginate(LoadBalancerNames=[lb_name]).build_full_result()['LoadBalancerDescriptions']

    def _get_vpc_from_subnets(self, subnets):
        if not subnets:
            return None

        subnet_details = self._describe_subnets(list(subnets))
        vpc_ids = set(subnet['VpcId'] for subnet in subnet_details)

        if not vpc_ids:
            return None
        if len(vpc_ids) > 1:
            self.module.fail_json("Subnets for an ELB may not span multiple VPCs",
                                  subnets=subnet_details, vpc_ids=vpc_ids)
        return vpc_ids.pop()

    @AWSRetry.jittered_backoff()
    def _describe_subnets(self, subnet_ids):
        paginator = self.ec2_client.get_paginator('describe_subnets')
        return paginator.paginate(SubnetIds=subnet_ids).build_full_result()['Subnets']

    #  Wrap it so we get the backoff
    @AWSRetry.jittered_backoff()
    def _get_ec2_security_group_ids_from_names(self, **params):
        return get_ec2_security_group_ids_from_names(ec2_connection=self.ec2_client, **params)


def main():

    access_log_spec = dict(
        enabled=dict(required=False, type='bool', default=True),
        s3_location=dict(required=False, type='str'),
        s3_prefix=dict(required=False, type='str', default=""),
        interval=dict(required=False, type='int', default=60, choices=[5, 60]),
    )

    stickiness_spec = dict(
        type=dict(required=False, type='str', choices=['application', 'loadbalancer']),
        enabled=dict(required=False, type='bool', default=True),
        cookie=dict(required=False, type='str'),
        expiration=dict(required=False, type='int')
    )

    healthcheck_spec = dict(
        ping_protocol=dict(required=True, type='str'),
        ping_path=dict(required=False, type='str'),
        ping_port=dict(required=True, type='int'),
        interval=dict(required=True, type='int'),
        timeout=dict(aliases=['response_timeout'], required=True, type='int'),
        unhealthy_threshold=dict(required=True, type='int'),
        healthy_threshold=dict(required=True, type='int'),
    )

    listeners_spec = dict(
        load_balancer_port=dict(required=True, type='int'),
        instance_port=dict(required=True, type='int'),
        ssl_certificate_id=dict(required=False, type='str'),
        protocol=dict(required=True, type='str'),
        instance_protocol=dict(required=False, type='str'),
        proxy_protocol=dict(required=False, type='bool'),
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
        health_check=dict(type='dict', options=healthcheck_spec),
        subnets=dict(type='list', elements='str'),
        purge_subnets=dict(default=False, type='bool'),
        scheme=dict(choices=['internal', 'internet-facing']),
        connection_draining_timeout=dict(type='int'),
        idle_timeout=dict(type='int'),
        cross_az_load_balancing=dict(type='bool'),
        stickiness=dict(type='dict', options=stickiness_spec),
        access_logs=dict(type='dict', options=access_log_spec),
        wait=dict(default=False, type='bool'),
        wait_timeout=dict(default=180, type='int'),
        tags=dict(type='dict', aliases=['resource_tags']),
        purge_tags=dict(default=True, type='bool'),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ['security_group_ids', 'security_group_names'],
            ['zones', 'subnets'],
        ],
        supports_check_mode=True,
    )

    wait_timeout = module.params['wait_timeout']
    state = module.params['state']

    if wait_timeout > 600:
        module.fail_json(msg='wait_timeout maximum is 600 seconds')

    elb_man = ElbManager(module)
    elb_man.validate_params(state)

    if state == 'present':
        elb_man.ensure_ok()
        # original boto style
        elb = elb_man.get_info()
        # boto3 style
        lb = elb_man.get_load_balancer()
        ec2_result = dict(elb=elb, load_balancer=lb)
    elif state == 'absent':
        elb_man.ensure_gone()
        # original boto style
        elb = elb_man.get_info()
        ec2_result = dict(elb=elb)

    module.exit_json(
        changed=elb_man.changed,
        **ec2_result,
    )


if __name__ == '__main__':
    main()
