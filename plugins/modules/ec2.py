#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: ec2
version_added: 1.0.0
short_description: create, terminate, start or stop an instance in ec2
deprecated:
  removed_in: 4.0.0
  why: The ec2 module is based upon a deprecated version of the AWS SDK.
  alternative: Use M(amazon.aws.ec2_instance).
description:
    - Creates or terminates ec2 instances.
    - >
      Note: This module uses the older boto Python module to interact with the EC2 API.
      M(amazon.aws.ec2) will still receive bug fixes, but no new features.
      Consider using the M(amazon.aws.ec2_instance) module instead.
      If M(amazon.aws.ec2_instance) does not support a feature you need that is available in M(amazon.aws.ec2), please
      file a feature request.
options:
  key_name:
    description:
      - Key pair to use on the instance.
      - The SSH key must already exist in AWS in order to use this argument.
      - Keys can be created / deleted using the M(amazon.aws.ec2_key) module.
    aliases: ['keypair']
    type: str
  id:
    description:
      - Identifier for this instance or set of instances, so that the module will be idempotent with respect to EC2 instances.
      - This identifier is valid for at least 24 hours after the termination of the instance, and should not be reused for another call later on.
      - For details, see the description of client token at U(https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Run_Instance_Idempotency.html).
    type: str
  group:
    description:
      - Security group (or list of groups) to use with the instance.
    aliases: [ 'groups' ]
    type: list
    elements: str
  group_id:
    description:
      - Security group id (or list of ids) to use with the instance.
    type: list
    elements: str
  zone:
    description:
      - AWS availability zone in which to launch the instance.
    aliases: [ 'aws_zone', 'ec2_zone' ]
    type: str
  instance_type:
    description:
      - Instance type to use for the instance, see U(https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-types.html).
      - Required when creating a new instance.
    type: str
    aliases: ['type']
  tenancy:
    description:
      - An instance with a tenancy of C(dedicated) runs on single-tenant hardware and can only be launched into a VPC.
      - Note that to use dedicated tenancy you MUST specify a I(vpc_subnet_id) as well.
      - Dedicated tenancy is not available for EC2 "micro" instances.
    default: default
    choices: [ "default", "dedicated" ]
    type: str
  spot_price:
    description:
      - Maximum spot price to bid. If not set, a regular on-demand instance is requested.
      - A spot request is made with this maximum bid. When it is filled, the instance is started.
    type: str
  spot_type:
    description:
      - The type of spot request.
      - After being interrupted a C(persistent) spot instance will be started once there is capacity to fill the request again.
    default: "one-time"
    choices: [ "one-time", "persistent" ]
    type: str
  image:
    description:
       - I(ami) ID to use for the instance.
       - Required when I(state=present).
    type: str
  kernel:
    description:
      - Kernel eki to use for the instance.
    type: str
  ramdisk:
    description:
      - Ramdisk eri to use for the instance.
    type: str
  wait:
    description:
      - Wait for the instance to reach its desired state before returning.
      - Does not wait for SSH, see the 'wait_for_connection' example for details.
    type: bool
    default: false
  wait_timeout:
    description:
      - How long before wait gives up, in seconds.
    default: 300
    type: int
  spot_wait_timeout:
    description:
      - How long to wait for the spot instance request to be fulfilled. Affects 'Request valid until' for setting spot request lifespan.
    default: 600
    type: int
  count:
    description:
      - Number of instances to launch.
    default: 1
    type: int
  monitoring:
    description:
      - Enable detailed monitoring (CloudWatch) for the instance.
    type: bool
    default: false
  user_data:
    description:
      - Opaque blob of data which is made available to the EC2 instance.
    type: str
  instance_tags:
    description:
      - >
        A hash/dictionary of tags to add to the new instance or for
        instances to start/stop by tag.  For example C({"key":"value"}) or
        C({"key":"value","key2":"value2"}).
    type: dict
  placement_group:
    description:
      - Placement group for the instance when using EC2 Clustered Compute.
    type: str
  vpc_subnet_id:
    description:
      - The subnet ID in which to launch the instance (VPC).
    type: str
  assign_public_ip:
    description:
      - When provisioning within vpc, assign a public IP address. Boto library must be 2.13.0+.
    type: bool
  private_ip:
    description:
      - The private ip address to assign the instance (from the vpc subnet).
    type: str
  instance_profile_name:
    description:
      - Name of the IAM instance profile (i.e. what the EC2 console refers to as an "IAM Role") to use. Boto library must be 2.5.0+.
    type: str
  instance_ids:
    description:
      - "list of instance ids, currently used for states: absent, running, stopped"
    aliases: ['instance_id']
    type: list
    elements: str
  source_dest_check:
    description:
      - Enable or Disable the Source/Destination checks (for NAT instances and Virtual Routers).
        When initially creating an instance the EC2 API defaults this to C(True).
    type: bool
  termination_protection:
    description:
      - Enable or Disable the Termination Protection.
      - Defaults to C(false).
    type: bool
  instance_initiated_shutdown_behavior:
    description:
    - Set whether AWS will Stop or Terminate an instance on shutdown. This parameter is ignored when using instance-store.
      images (which require termination on shutdown).
    default: 'stop'
    choices: [ "stop", "terminate" ]
    type: str
  state:
    description:
      - Create, terminate, start, stop or restart instances.
      - When I(state=absent), I(instance_ids) is required.
      - When I(state=running), I(state=stopped) or I(state=restarted) then either I(instance_ids) or I(instance_tags) is required.
    default: 'present'
    choices: ['absent', 'present', 'restarted', 'running', 'stopped']
    type: str
  volumes:
    description:
      - A list of hash/dictionaries of volumes to add to the new instance.
    type: list
    elements: dict
    suboptions:
      device_name:
        type: str
        required: true
        description:
          - A name for the device (For example C(/dev/sda)).
      delete_on_termination:
        type: bool
        default: false
        description:
          - Whether the volume should be automatically deleted when the instance is terminated.
      ephemeral:
        type: str
        description:
          - Whether the volume should be ephemeral.
          - Data on ephemeral volumes is lost when the instance is stopped.
          - Mutually exclusive with the I(snapshot) parameter.
      encrypted:
        type: bool
        default: false
        description:
          - Whether the volume should be encrypted using the 'aws/ebs' KMS CMK.
      snapshot:
        type: str
        description:
          - The ID of an EBS snapshot to copy when creating the volume.
          - Mutually exclusive with the I(ephemeral) parameter.
      volume_type:
        type: str
        description:
          - The type of volume to create.
          - See U(https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSVolumeTypes.html) for more information on the available volume types.
      volume_size:
        type: int
        description:
          - The size of the volume (in GiB).
      iops:
        type: int
        description:
          - The number of IOPS per second to provision for the volume.
          - Required when I(volume_type=io1).
  ebs_optimized:
    description:
      - Whether instance is using optimized EBS volumes, see U(https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSOptimized.html).
    default: false
    type: bool
  exact_count:
    description:
      - An integer value which indicates how many instances that match the 'count_tag' parameter should be running.
        Instances are either created or terminated based on this value.
    type: int
  count_tag:
    description:
      - Used with I(exact_count) to determine how many nodes based on a specific tag criteria should be running.
        This can be expressed in multiple ways and is shown in the EXAMPLES section.  For instance, one can request 25 servers
        that are tagged with C(class=webserver). The specified tag must already exist or be passed in as the I(instance_tags) option.
    type: raw
  network_interfaces:
    description:
      - A list of existing network interfaces to attach to the instance at launch. When specifying existing network interfaces,
        none of the I(assign_public_ip), I(private_ip), I(vpc_subnet_id), I(group), or I(group_id) parameters may be used. (Those parameters are
        for creating a new network interface at launch.)
    aliases: ['network_interface']
    type: list
    elements: str
  spot_launch_group:
    description:
      - Launch group for spot requests, see U(https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/how-spot-instances-work.html#spot-launch-group).
    type: str
author:
    - "Tim Gerla (@tgerla)"
    - "Lester Wade (@lwade)"
    - "Seth Vidal (@skvidal)"
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
requirements:
- python >= 2.6
- boto

'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Basic provisioning example
- amazon.aws.ec2:
    key_name: mykey
    instance_type: t2.micro
    image: ami-123456
    wait: yes
    group: webserver
    count: 3
    vpc_subnet_id: subnet-29e63245
    assign_public_ip: yes

# Advanced example with tagging and CloudWatch
- amazon.aws.ec2:
    key_name: mykey
    group: databases
    instance_type: t2.micro
    image: ami-123456
    wait: yes
    wait_timeout: 500
    count: 5
    instance_tags:
       db: postgres
    monitoring: yes
    vpc_subnet_id: subnet-29e63245
    assign_public_ip: yes

# Single instance with additional IOPS volume from snapshot and volume delete on termination
- amazon.aws.ec2:
    key_name: mykey
    group: webserver
    instance_type: c3.medium
    image: ami-123456
    wait: yes
    wait_timeout: 500
    volumes:
      - device_name: /dev/sdb
        snapshot: snap-abcdef12
        volume_type: io1
        iops: 1000
        volume_size: 100
        delete_on_termination: true
    monitoring: yes
    vpc_subnet_id: subnet-29e63245
    assign_public_ip: yes

# Single instance with ssd gp2 root volume
- amazon.aws.ec2:
    key_name: mykey
    group: webserver
    instance_type: c3.medium
    image: ami-123456
    wait: yes
    wait_timeout: 500
    volumes:
      - device_name: /dev/xvda
        volume_type: gp2
        volume_size: 8
    vpc_subnet_id: subnet-29e63245
    assign_public_ip: yes
    count_tag:
      Name: dbserver
    exact_count: 1

# Multiple groups example
- amazon.aws.ec2:
    key_name: mykey
    group: ['databases', 'internal-services', 'sshable', 'and-so-forth']
    instance_type: m1.large
    image: ami-6e649707
    wait: yes
    wait_timeout: 500
    count: 5
    instance_tags:
        db: postgres
    monitoring: yes
    vpc_subnet_id: subnet-29e63245
    assign_public_ip: yes

# Multiple instances with additional volume from snapshot
- amazon.aws.ec2:
    key_name: mykey
    group: webserver
    instance_type: m1.large
    image: ami-6e649707
    wait: yes
    wait_timeout: 500
    count: 5
    volumes:
    - device_name: /dev/sdb
      snapshot: snap-abcdef12
      volume_size: 10
    monitoring: yes
    vpc_subnet_id: subnet-29e63245
    assign_public_ip: yes

# Dedicated tenancy example
- amazon.aws.ec2:
    assign_public_ip: yes
    group_id: sg-1dc53f72
    key_name: mykey
    image: ami-6e649707
    instance_type: m1.small
    tenancy: dedicated
    vpc_subnet_id: subnet-29e63245
    wait: yes

# Spot instance example
- amazon.aws.ec2:
    spot_price: 0.24
    spot_wait_timeout: 600
    keypair: mykey
    group_id: sg-1dc53f72
    instance_type: m1.small
    image: ami-6e649707
    wait: yes
    vpc_subnet_id: subnet-29e63245
    assign_public_ip: yes
    spot_launch_group: report_generators
    instance_initiated_shutdown_behavior: terminate

# Examples using pre-existing network interfaces
- amazon.aws.ec2:
    key_name: mykey
    instance_type: t2.small
    image: ami-f005ba11
    network_interface: eni-deadbeef

- amazon.aws.ec2:
    key_name: mykey
    instance_type: t2.small
    image: ami-f005ba11
    network_interfaces: ['eni-deadbeef', 'eni-5ca1ab1e']

# Launch instances, runs some tasks
# and then terminate them

- name: Create a sandbox instance
  hosts: localhost
  gather_facts: False
  vars:
    keypair: my_keypair
    instance_type: m1.small
    security_group: my_securitygroup
    image: my_ami_id
    region: us-east-1
  tasks:
    - name: Launch instance
      amazon.aws.ec2:
         key_name: "{{ keypair }}"
         group: "{{ security_group }}"
         instance_type: "{{ instance_type }}"
         image: "{{ image }}"
         wait: true
         region: "{{ region }}"
         vpc_subnet_id: subnet-29e63245
         assign_public_ip: yes
      register: ec2

    - name: Add new instance to host group
      add_host:
        hostname: "{{ item.public_ip }}"
        groupname: launched
      loop: "{{ ec2.instances }}"

    - name: Wait for SSH to come up
      delegate_to: "{{ item.public_dns_name }}"
      wait_for_connection:
        delay: 60
        timeout: 320
      loop: "{{ ec2.instances }}"

- name: Configure instance(s)
  hosts: launched
  become: True
  gather_facts: True
  roles:
    - my_awesome_role
    - my_awesome_test

- name: Terminate instances
  hosts: localhost
  tasks:
    - name: Terminate instances that were previously launched
      amazon.aws.ec2:
        state: 'absent'
        instance_ids: '{{ ec2.instance_ids }}'

# Start a few existing instances, run some tasks
# and stop the instances

- name: Start sandbox instances
  hosts: localhost
  gather_facts: false
  vars:
    instance_ids:
      - 'i-xxxxxx'
      - 'i-xxxxxx'
      - 'i-xxxxxx'
    region: us-east-1
  tasks:
    - name: Start the sandbox instances
      amazon.aws.ec2:
        instance_ids: '{{ instance_ids }}'
        region: '{{ region }}'
        state: running
        wait: True
        vpc_subnet_id: subnet-29e63245
        assign_public_ip: yes
  roles:
    - do_neat_stuff
    - do_more_neat_stuff

- name: Stop sandbox instances
  hosts: localhost
  gather_facts: false
  vars:
    instance_ids:
      - 'i-xxxxxx'
      - 'i-xxxxxx'
      - 'i-xxxxxx'
    region: us-east-1
  tasks:
    - name: Stop the sandbox instances
      amazon.aws.ec2:
        instance_ids: '{{ instance_ids }}'
        region: '{{ region }}'
        state: stopped
        wait: True
        vpc_subnet_id: subnet-29e63245
        assign_public_ip: yes

#
# Start stopped instances specified by tag
#
- amazon.aws.ec2:
    instance_tags:
        Name: ExtraPower
    state: running

#
# Restart instances specified by tag
#
- amazon.aws.ec2:
    instance_tags:
        Name: ExtraPower
    state: restarted

#
# Enforce that 5 instances with a tag "foo" are running
# (Highly recommended!)
#

- amazon.aws.ec2:
    key_name: mykey
    instance_type: c1.medium
    image: ami-40603AD1
    wait: yes
    group: webserver
    instance_tags:
        foo: bar
    exact_count: 5
    count_tag: foo
    vpc_subnet_id: subnet-29e63245
    assign_public_ip: yes

#
# Enforce that 5 running instances named "database" with a "dbtype" of "postgres"
#

- amazon.aws.ec2:
    key_name: mykey
    instance_type: c1.medium
    image: ami-40603AD1
    wait: yes
    group: webserver
    instance_tags:
        Name: database
        dbtype: postgres
    exact_count: 5
    count_tag:
        Name: database
        dbtype: postgres
    vpc_subnet_id: subnet-29e63245
    assign_public_ip: yes

#
# count_tag complex argument examples
#

    # instances with tag foo
- amazon.aws.ec2:
    count_tag:
        foo:

    # instances with tag foo=bar
- amazon.aws.ec2:
    count_tag:
        foo: bar

    # instances with tags foo=bar & baz
- amazon.aws.ec2:
    count_tag:
        foo: bar
        baz:

    # instances with tags foo & bar & baz=bang
- amazon.aws.ec2:
    count_tag:
        - foo
        - bar
        - baz: bang

'''

RETURN = r'''
changed:
    description: If the EC2 instance has changed.
    type: bool
    returned: always
    sample: true
instances:
    description: The instances.
    type: list
    returned: always
    contains:
        ami_launch_index:
            description: The AMI launch index, which can be used to find this instance in the launch group.
            type: int
            returned: always
            sample: 0
        architecture:
            description: The architecture of the image.
            type: str
            returned: always
            sample: "x86_64"
        block_device_mapping:
            description: Any block device mapping entries for the instance.
            type: dict
            returned: always
            sample: {
                "/dev/xvda": {
                    "delete_on_termination": true,
                    "status": "attached",
                    "volume_id": "vol-06d364586f5550b62"
                }
            }
        dns_name:
            description: The public DNS name assigned to the instance.
            type: str
            returned: always
            sample: "ec2-203-0-113-1.z-2.compute-1.amazonaws.com"
        ebs_optimized:
            description: Indicates whether the instance is optimized for Amazon EBS I/O.
            type: bool
            returned: always
            sample: false
        groups:
            description: One or more security groups.
            type: dict
            returned: always
            sample: {
                "sg-0c6562ab3d435619f": "ansible-test--88312190_setup"
            }
        hypervisor:
            description: The hypervisor type of the instance.
            type: str
            returned: always
            sample: "xen"
        image_id:
            description: The ID of the AMI used to launch the instance.
            type: str
            returned: always
            sample: "ami-0d5eff06f840b45e9"
        instance_id:
            description: The ID of the instance.
            type: str
            returned: always
            sample: "i-0250719204c428be1"
        instance_type:
            description: The instance type.
            type: str
            returned: always
            sample: "t2.micro"
        kernel:
            description: The kernel associated with this instance, if applicable.
            type: str
            returned: always
            sample: ""
        key_name:
            description: The name of the key pair, if this instance was launched with an associated key pair.
            type: str
            returned: always
            sample: "ansible-test-88312190_setup"
        launch_time:
            description: The time the instance was launched.
            type: str
            returned: always
            sample: "2021-05-09T19:30:26.000Z"
        placement:
            description: The location where the instance launched, if applicable.
            type: dict
            returned: always
            sample:  {
                "availability_zone": "us-east-1a",
                "group_name": "",
                "tenancy": "default"
            }
        private_dns_name:
            description: The private DNS hostname name assigned to the instance.
            type: str
            returned: always
            sample: "ip-10-176-1-249.ec2.internal"
        private_ip:
            description: The private IPv4 address assigned to the instance.
            type: str
            returned: always
            sample: "10.176.1.249"
        public_dns_name:
            description: The public DNS name assigned to the instance.
            type: str
            returned: always
            sample: "ec2-203-0-113-1.z-2.compute-1.amazonaws.com"
        public_ip:
            description: The public IPv4 address, or the Carrier IP address assigned to the instance, if applicable.
            type: str
            returned: always
            sample: "203.0.113.1"
        ramdisk:
            description: The RAM disk associated with this instance, if applicable.
            type: str
            returned: always
            sample: ""
        root_device_name:
            description: The device name of the root device volume.
            type: str
            returned: always
            sample: "/dev/xvda"
        root_device_type:
            description: The root device type used by the AMI.
            type: str
            returned: always
            sample: "ebs"
        state:
            description: The current state of the instance.
            type: dict
            returned: always
            sample: {
                "code": 80,
                "name": "stopped"
            }
        tags:
            description: Any tags assigned to the instance.
            type: dict
            returned: always
            sample: {
                "ResourcePrefix": "ansible-test-88312190-integration_tests"
            }
        tenancy:
            description: The tenancy of the instance (if the instance is running in a VPC).
            type: str
            returned: always
            sample: "default"
        virtualization_type:
            description: The virtualization type of the instance.
            type: str
            returned: always
            sample: "hvm"
        monitoring:
            description: The monitoring for the instance.
            type: dict
            returned: always
            sample: {
                "state": "disabled"
            }
        capacity_reservation_specification:
            description: Information about the Capacity Reservation targeting option.
            type: dict
            returned: always
            sample: {
                "capacity_reservation_preference": "open"
            }
        client_token:
            description: The idempotency token you provided when you launched the instance, if applicable.
            type: str
            returned: always
            sample: ""
        cpu_options:
            description: The CPU options for the instance.
            type: dict
            returned: always
            sample: {
                "core_count": 1,
                "threads_per_core": 1
            }
        ena_support:
            description: Specifies whether enhanced networking with ENA is enabled.
            type: bool
            returned: always
            sample: true
        enclave_options:
            description: Indicates whether the instance is enabled for AWS Nitro Enclaves.
            type: dict
            returned: always
            sample: {
                "enabled": false
            }
        hibernation_options:
            description: Indicates whether the instance is enabled for hibernation.
            type: dict
            returned: always
            sample:  {
                "configured": false
            }
        network_interfaces:
            description: The network interfaces for the instance.
            type: list
            returned: always
            sample:  [
                {
                    "attachment": {
                        "attach_time": "2021-05-09T19:30:57+00:00",
                        "attachment_id": "eni-attach-07341f2560be6c8fc",
                        "delete_on_termination": true,
                        "device_index": 0,
                        "network_card_index": 0,
                        "status": "attached"
                    },
                    "description": "",
                    "groups": [
                        {
                            "group_id": "sg-0c6562ab3d435619f",
                            "group_name": "ansible-test-88312190_setup"
                        }
                    ],
                    "interface_type": "interface",
                    "ipv6_addresses": [],
                    "mac_address": "0e:0e:36:60:67:cf",
                    "network_interface_id": "eni-061dee20eba3b445a",
                    "owner_id": "721066863947",
                    "private_dns_name": "ip-10-176-1-178.ec2.internal",
                    "private_ip_address": "10.176.1.178",
                    "private_ip_addresses": [
                        {
                            "primary": true,
                            "private_dns_name": "ip-10-176-1-178.ec2.internal",
                            "private_ip_address": "10.176.1.178"
                        }
                    ],
                    "source_dest_check": true,
                    "status": "in-use",
                    "subnet_id": "subnet-069d3e2eab081955d",
                    "vpc_id": "vpc-0b6879b6ca2e9be2b"
                }
            ]
        vpc_id:
            description: The ID of the VPC in which the instance is running.
            type: str
            returned: always
            sample: "vpc-0b6879b6ca2e9be2b"
        subnet_id:
            description: The ID of the subnet in which the instance is running.
            type: str
            returned: always
            sample: "subnet-069d3e2eab081955d"
        state_transition_reason:
            description: The reason for the most recent state transition. This might be an empty string.
            type: str
            returned: always
            sample: "User initiated (2021-05-09 19:31:28 GMT)"
        state_reason:
            description: The reason for the most recent state transition.
            type: dict
            returned: always
            sample: {
                "code": "Client.UserInitiatedShutdown",
                "message": "Client.UserInitiatedShutdown: User initiated shutdown"
            }
        security_groups:
            description: The security groups for the instance.
            type: list
            returned: always
            sample: [
                {
                    "group_id": "sg-0c6562ab3d435619f",
                    "group_name": "ansible-test-alinas-mbp-88312190_setup"
                }
            ]
        source_dest_check:
            description: Indicates whether source/destination checking is enabled.
            type: bool
            returned: always
            sample: true
        metadata:
            description: The metadata options for the instance.
            type: dict
            returned: always
            sample: {
                "http_endpoint": "enabled",
                "http_put_response_hop_limit": 1,
                "http_tokens": "optional",
                "state": "applied"
            }
'''


import time
import datetime
from ast import literal_eval

try:
    import boto.ec2
    from boto.ec2.blockdevicemapping import BlockDeviceType
    from boto.ec2.blockdevicemapping import BlockDeviceMapping
    from boto.exception import EC2ResponseError
    from boto import connect_ec2_endpoint
    from boto import connect_vpc
except ImportError:
    pass  # Taken care of by ec2.HAS_BOTO

from ansible.module_utils.six import get_function_code
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_bytes
from ansible.module_utils._text import to_text

from ..module_utils.core import AnsibleAWSModule
from ..module_utils.ec2 import HAS_BOTO
from ..module_utils.ec2 import ec2_connect
from ..module_utils.ec2 import get_aws_connection_info
from ..module_utils.version import LooseVersion


def find_running_instances_by_count_tag(module, ec2, vpc, count_tag, zone=None):

    # get reservations for instances that match tag(s) and are in the desired state
    state = module.params.get('state')
    if state not in ['running', 'stopped']:
        state = None
    reservations = get_reservations(module, ec2, vpc, tags=count_tag, state=state, zone=zone)

    instances = []
    for res in reservations:
        if hasattr(res, 'instances'):
            for inst in res.instances:
                if inst.state == 'terminated' or inst.state == 'shutting-down':
                    continue
                instances.append(inst)

    return reservations, instances


def _set_none_to_blank(dictionary):
    result = dictionary
    for k in result:
        if isinstance(result[k], dict):
            result[k] = _set_none_to_blank(result[k])
        elif not result[k]:
            result[k] = ""
    return result


def get_reservations(module, ec2, vpc, tags=None, state=None, zone=None):
    # TODO: filters do not work with tags that have underscores
    filters = dict()

    vpc_subnet_id = module.params.get('vpc_subnet_id')
    vpc_id = None
    if vpc_subnet_id:
        filters.update({"subnet-id": vpc_subnet_id})
        if vpc:
            vpc_id = vpc.get_all_subnets(subnet_ids=[vpc_subnet_id])[0].vpc_id

    if vpc_id:
        filters.update({"vpc-id": vpc_id})

    if tags is not None:

        if isinstance(tags, str):
            try:
                tags = literal_eval(tags)
            except Exception:
                pass

        # if not a string type, convert and make sure it's a text string
        if isinstance(tags, int):
            tags = to_text(tags)

        # if string, we only care that a tag of that name exists
        if isinstance(tags, str):
            filters.update({"tag-key": tags})

        # if list, append each item to filters
        if isinstance(tags, list):
            for x in tags:
                if isinstance(x, dict):
                    x = _set_none_to_blank(x)
                    filters.update(dict(("tag:" + tn, tv) for (tn, tv) in x.items()))
                else:
                    filters.update({"tag-key": x})

        # if dict, add the key and value to the filter
        if isinstance(tags, dict):
            tags = _set_none_to_blank(tags)
            filters.update(dict(("tag:" + tn, tv) for (tn, tv) in tags.items()))

        # lets check to see if the filters dict is empty, if so then stop
        if not filters:
            module.fail_json(msg="Filters based on tag is empty => tags: %s" % (tags))

    if state:
        # http://stackoverflow.com/questions/437511/what-are-the-valid-instancestates-for-the-amazon-ec2-api
        filters.update({'instance-state-name': state})

    if zone:
        filters.update({'availability-zone': zone})

    if module.params.get('id'):
        filters['client-token'] = module.params['id']

    results = ec2.get_all_instances(filters=filters)

    return results


def get_instance_info(inst):
    """
    Retrieves instance information from an instance
    ID and returns it as a dictionary
    """
    instance_info = {'id': inst.id,
                     'ami_launch_index': inst.ami_launch_index,
                     'private_ip': inst.private_ip_address,
                     'private_dns_name': inst.private_dns_name,
                     'public_ip': inst.ip_address,
                     'dns_name': inst.dns_name,
                     'public_dns_name': inst.public_dns_name,
                     'state_code': inst.state_code,
                     'architecture': inst.architecture,
                     'image_id': inst.image_id,
                     'key_name': inst.key_name,
                     'placement': inst.placement,
                     'region': inst.placement[:-1],
                     'kernel': inst.kernel,
                     'ramdisk': inst.ramdisk,
                     'launch_time': inst.launch_time,
                     'instance_type': inst.instance_type,
                     'root_device_type': inst.root_device_type,
                     'root_device_name': inst.root_device_name,
                     'state': inst.state,
                     'hypervisor': inst.hypervisor,
                     'tags': inst.tags,
                     'groups': dict((group.id, group.name) for group in inst.groups),
                     }
    try:
        instance_info['virtualization_type'] = getattr(inst, 'virtualization_type')
    except AttributeError:
        instance_info['virtualization_type'] = None

    try:
        instance_info['ebs_optimized'] = getattr(inst, 'ebs_optimized')
    except AttributeError:
        instance_info['ebs_optimized'] = False

    try:
        bdm_dict = {}
        bdm = getattr(inst, 'block_device_mapping')
        for device_name in bdm.keys():
            bdm_dict[device_name] = {
                'status': bdm[device_name].status,
                'volume_id': bdm[device_name].volume_id,
                'delete_on_termination': bdm[device_name].delete_on_termination
            }
        instance_info['block_device_mapping'] = bdm_dict
    except AttributeError:
        instance_info['block_device_mapping'] = False

    try:
        instance_info['tenancy'] = getattr(inst, 'placement_tenancy')
    except AttributeError:
        instance_info['tenancy'] = 'default'

    return instance_info


def boto_supports_associate_public_ip_address(ec2):
    """
    Check if Boto library has associate_public_ip_address in the NetworkInterfaceSpecification
    class. Added in Boto 2.13.0

    ec2: authenticated ec2 connection object

    Returns:
        True if Boto library accepts associate_public_ip_address argument, else false
    """

    try:
        network_interface = boto.ec2.networkinterface.NetworkInterfaceSpecification()
        getattr(network_interface, "associate_public_ip_address")
        return True
    except AttributeError:
        return False


def boto_supports_profile_name_arg(ec2):
    """
    Check if Boto library has instance_profile_name argument. instance_profile_name has been added in Boto 2.5.0

    ec2: authenticated ec2 connection object

    Returns:
        True if Boto library accept instance_profile_name argument, else false
    """
    run_instances_method = getattr(ec2, 'run_instances')
    return 'instance_profile_name' in get_function_code(run_instances_method).co_varnames


def boto_supports_volume_encryption():
    """
    Check if Boto library supports encryption of EBS volumes (added in 2.29.0)

    Returns:
        True if boto library has the named param as an argument on the request_spot_instances method, else False
    """
    return hasattr(boto, 'Version') and LooseVersion(boto.Version) >= LooseVersion('2.29.0')


def create_block_device(module, ec2, volume):
    # Not aware of a way to determine this programatically
    # http://aws.amazon.com/about-aws/whats-new/2013/10/09/ebs-provisioned-iops-maximum-iops-gb-ratio-increased-to-30-1/
    MAX_IOPS_TO_SIZE_RATIO = 30

    volume_type = volume.get('volume_type')

    if 'snapshot' not in volume and 'ephemeral' not in volume:
        if 'volume_size' not in volume:
            module.fail_json(msg='Size must be specified when creating a new volume or modifying the root volume')
    if 'snapshot' in volume:
        if volume_type == 'io1' and 'iops' not in volume:
            module.fail_json(msg='io1 volumes must have an iops value set')
        if 'iops' in volume:
            snapshot = ec2.get_all_snapshots(snapshot_ids=[volume['snapshot']])[0]
            size = volume.get('volume_size', snapshot.volume_size)
            if int(volume['iops']) > MAX_IOPS_TO_SIZE_RATIO * int(size):
                module.fail_json(msg='IOPS must be at most %d times greater than size' % MAX_IOPS_TO_SIZE_RATIO)
    if 'ephemeral' in volume:
        if 'snapshot' in volume:
            module.fail_json(msg='Cannot set both ephemeral and snapshot')
    if boto_supports_volume_encryption():
        return BlockDeviceType(snapshot_id=volume.get('snapshot'),
                               ephemeral_name=volume.get('ephemeral'),
                               size=volume.get('volume_size'),
                               volume_type=volume_type,
                               delete_on_termination=volume.get('delete_on_termination', False),
                               iops=volume.get('iops'),
                               encrypted=volume.get('encrypted', None))
    else:
        return BlockDeviceType(snapshot_id=volume.get('snapshot'),
                               ephemeral_name=volume.get('ephemeral'),
                               size=volume.get('volume_size'),
                               volume_type=volume_type,
                               delete_on_termination=volume.get('delete_on_termination', False),
                               iops=volume.get('iops'))


def boto_supports_param_in_spot_request(ec2, param):
    """
    Check if Boto library has a <param> in its request_spot_instances() method. For example, the placement_group parameter wasn't added until 2.3.0.

    ec2: authenticated ec2 connection object

    Returns:
        True if boto library has the named param as an argument on the request_spot_instances method, else False
    """
    method = getattr(ec2, 'request_spot_instances')
    return param in get_function_code(method).co_varnames


def await_spot_requests(module, ec2, spot_requests, count):
    """
    Wait for a group of spot requests to be fulfilled, or fail.

    module: Ansible module object
    ec2: authenticated ec2 connection object
    spot_requests: boto.ec2.spotinstancerequest.SpotInstanceRequest object returned by ec2.request_spot_instances
    count: Total number of instances to be created by the spot requests

    Returns:
        list of instance ID's created by the spot request(s)
    """
    spot_wait_timeout = int(module.params.get('spot_wait_timeout'))
    wait_complete = time.time() + spot_wait_timeout

    spot_req_inst_ids = dict()
    while time.time() < wait_complete:
        reqs = ec2.get_all_spot_instance_requests()
        for sirb in spot_requests:
            if sirb.id in spot_req_inst_ids:
                continue
            for sir in reqs:
                if sir.id != sirb.id:
                    continue  # this is not our spot instance
                if sir.instance_id is not None:
                    spot_req_inst_ids[sirb.id] = sir.instance_id
                elif sir.state == 'open':
                    continue  # still waiting, nothing to do here
                elif sir.state == 'active':
                    continue  # Instance is created already, nothing to do here
                elif sir.state == 'failed':
                    module.fail_json(msg="Spot instance request %s failed with status %s and fault %s:%s" % (
                        sir.id, sir.status.code, sir.fault.code, sir.fault.message))
                elif sir.state == 'cancelled':
                    module.fail_json(msg="Spot instance request %s was cancelled before it could be fulfilled." % sir.id)
                elif sir.state == 'closed':
                    # instance is terminating or marked for termination
                    # this may be intentional on the part of the operator,
                    # or it may have been terminated by AWS due to capacity,
                    # price, or group constraints in this case, we'll fail
                    # the module if the reason for the state is anything
                    # other than termination by user. Codes are documented at
                    # https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-bid-status.html
                    if sir.status.code == 'instance-terminated-by-user':
                        # do nothing, since the user likely did this on purpose
                        pass
                    else:
                        spot_msg = "Spot instance request %s was closed by AWS with the status %s and fault %s:%s"
                        module.fail_json(msg=spot_msg % (sir.id, sir.status.code, sir.fault.code, sir.fault.message))

        if len(spot_req_inst_ids) < count:
            time.sleep(5)
        else:
            return list(spot_req_inst_ids.values())
    module.fail_json(msg="wait for spot requests timeout on %s" % time.asctime())


def enforce_count(module, ec2, vpc):

    exact_count = module.params.get('exact_count')
    count_tag = module.params.get('count_tag')
    zone = module.params.get('zone')

    # fail here if the exact count was specified without filtering
    # on a tag, as this may lead to a undesired removal of instances
    if exact_count and count_tag is None:
        module.fail_json(msg="you must use the 'count_tag' option with exact_count")

    reservations, instances = find_running_instances_by_count_tag(module, ec2, vpc, count_tag, zone)

    changed = None
    checkmode = False
    instance_dict_array = []
    changed_instance_ids = None

    if len(instances) == exact_count:
        changed = False
    elif len(instances) < exact_count:
        changed = True
        to_create = exact_count - len(instances)
        if not checkmode:
            (instance_dict_array, changed_instance_ids, changed) \
                = create_instances(module, ec2, vpc, override_count=to_create)

            for inst in instance_dict_array:
                instances.append(inst)
    elif len(instances) > exact_count:
        changed = True
        to_remove = len(instances) - exact_count
        if not checkmode:
            all_instance_ids = sorted([x.id for x in instances])
            remove_ids = all_instance_ids[0:to_remove]

            instances = [x for x in instances if x.id not in remove_ids]

            (changed, instance_dict_array, changed_instance_ids) \
                = terminate_instances(module, ec2, remove_ids)
            terminated_list = []
            for inst in instance_dict_array:
                inst['state'] = "terminated"
                terminated_list.append(inst)
            instance_dict_array = terminated_list

    # ensure all instances are dictionaries
    all_instances = []
    for inst in instances:

        if not isinstance(inst, dict):
            warn_if_public_ip_assignment_changed(module, inst)
            inst = get_instance_info(inst)
        all_instances.append(inst)

    return (all_instances, instance_dict_array, changed_instance_ids, changed)


def create_instances(module, ec2, vpc, override_count=None):
    """
    Creates new instances

    module : AnsibleAWSModule object
    ec2: authenticated ec2 connection object

    Returns:
        A list of dictionaries with instance information
        about the instances that were launched
    """

    key_name = module.params.get('key_name')
    id = module.params.get('id')
    group_name = module.params.get('group')
    group_id = module.params.get('group_id')
    zone = module.params.get('zone')
    instance_type = module.params.get('instance_type')
    tenancy = module.params.get('tenancy')
    spot_price = module.params.get('spot_price')
    spot_type = module.params.get('spot_type')
    image = module.params.get('image')
    if override_count:
        count = override_count
    else:
        count = module.params.get('count')
    monitoring = module.params.get('monitoring')
    kernel = module.params.get('kernel')
    ramdisk = module.params.get('ramdisk')
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))
    spot_wait_timeout = int(module.params.get('spot_wait_timeout'))
    placement_group = module.params.get('placement_group')
    user_data = module.params.get('user_data')
    instance_tags = module.params.get('instance_tags')
    vpc_subnet_id = module.params.get('vpc_subnet_id')
    assign_public_ip = module.boolean(module.params.get('assign_public_ip'))
    private_ip = module.params.get('private_ip')
    instance_profile_name = module.params.get('instance_profile_name')
    volumes = module.params.get('volumes')
    ebs_optimized = module.params.get('ebs_optimized')
    exact_count = module.params.get('exact_count')
    count_tag = module.params.get('count_tag')
    source_dest_check = module.boolean(module.params.get('source_dest_check'))
    termination_protection = module.boolean(module.params.get('termination_protection'))
    network_interfaces = module.params.get('network_interfaces')
    spot_launch_group = module.params.get('spot_launch_group')
    instance_initiated_shutdown_behavior = module.params.get('instance_initiated_shutdown_behavior')

    vpc_id = None
    if vpc_subnet_id:
        if not vpc:
            module.fail_json(msg="region must be specified")
        else:
            vpc_id = vpc.get_all_subnets(subnet_ids=[vpc_subnet_id])[0].vpc_id
    else:
        vpc_id = None

    try:
        # Here we try to lookup the group id from the security group name - if group is set.
        if group_name:
            if vpc_id:
                grp_details = ec2.get_all_security_groups(filters={'vpc_id': vpc_id})
            else:
                grp_details = ec2.get_all_security_groups()
            if isinstance(group_name, string_types):
                group_name = [group_name]
            unmatched = set(group_name).difference(str(grp.name) for grp in grp_details)
            if len(unmatched) > 0:
                module.fail_json(msg="The following group names are not valid: %s" % ', '.join(unmatched))
            group_id = [str(grp.id) for grp in grp_details if str(grp.name) in group_name]
        # Now we try to lookup the group id testing if group exists.
        elif group_id:
            # wrap the group_id in a list if it's not one already
            if isinstance(group_id, string_types):
                group_id = [group_id]
            grp_details = ec2.get_all_security_groups(group_ids=group_id)
            group_name = [grp_item.name for grp_item in grp_details]
    except boto.exception.NoAuthHandlerFound as e:
        module.fail_json_aws(e, msg='Unable to authenticate to AWS')

    # Lookup any instances that much our run id.

    running_instances = []
    count_remaining = int(count)

    if id is not None:
        filter_dict = {'client-token': id, 'instance-state-name': 'running'}
        previous_reservations = ec2.get_all_instances(None, filter_dict)
        for res in previous_reservations:
            for prev_instance in res.instances:
                running_instances.append(prev_instance)
        count_remaining = count_remaining - len(running_instances)

    # Both min_count and max_count equal count parameter. This means the launch request is explicit (we want count, or fail) in how many instances we want.

    if count_remaining == 0:
        changed = False
    else:
        changed = True
        try:
            params = {'image_id': image,
                      'key_name': key_name,
                      'monitoring_enabled': monitoring,
                      'placement': zone,
                      'instance_type': instance_type,
                      'kernel_id': kernel,
                      'ramdisk_id': ramdisk}
            if user_data is not None:
                params['user_data'] = to_bytes(user_data, errors='surrogate_or_strict')

            if ebs_optimized:
                params['ebs_optimized'] = ebs_optimized

            # 'tenancy' always has a default value, but it is not a valid parameter for spot instance request
            if not spot_price:
                params['tenancy'] = tenancy

            if boto_supports_profile_name_arg(ec2):
                params['instance_profile_name'] = instance_profile_name
            else:
                if instance_profile_name is not None:
                    module.fail_json(
                        msg="instance_profile_name parameter requires Boto version 2.5.0 or higher")

            if assign_public_ip is not None:
                if not boto_supports_associate_public_ip_address(ec2):
                    module.fail_json(
                        msg="assign_public_ip parameter requires Boto version 2.13.0 or higher.")
                elif not vpc_subnet_id:
                    module.fail_json(
                        msg="assign_public_ip only available with vpc_subnet_id")

                else:
                    if private_ip:
                        interface = boto.ec2.networkinterface.NetworkInterfaceSpecification(
                            subnet_id=vpc_subnet_id,
                            private_ip_address=private_ip,
                            groups=group_id,
                            associate_public_ip_address=assign_public_ip)
                    else:
                        interface = boto.ec2.networkinterface.NetworkInterfaceSpecification(
                            subnet_id=vpc_subnet_id,
                            groups=group_id,
                            associate_public_ip_address=assign_public_ip)
                    interfaces = boto.ec2.networkinterface.NetworkInterfaceCollection(interface)
                    params['network_interfaces'] = interfaces
            else:
                if network_interfaces:
                    if isinstance(network_interfaces, string_types):
                        network_interfaces = [network_interfaces]
                    interfaces = []
                    for i, network_interface_id in enumerate(network_interfaces):
                        interface = boto.ec2.networkinterface.NetworkInterfaceSpecification(
                            network_interface_id=network_interface_id,
                            device_index=i)
                        interfaces.append(interface)
                    params['network_interfaces'] = \
                        boto.ec2.networkinterface.NetworkInterfaceCollection(*interfaces)
                else:
                    params['subnet_id'] = vpc_subnet_id
                    if vpc_subnet_id:
                        params['security_group_ids'] = group_id
                    else:
                        params['security_groups'] = group_name

            if volumes:
                bdm = BlockDeviceMapping()
                for volume in volumes:
                    if 'device_name' not in volume:
                        module.fail_json(msg='Device name must be set for volume')
                    # Minimum volume size is 1GiB. We'll use volume size explicitly set to 0
                    # to be a signal not to create this volume
                    if 'volume_size' not in volume or int(volume['volume_size']) > 0:
                        bdm[volume['device_name']] = create_block_device(module, ec2, volume)

                params['block_device_map'] = bdm

            # check to see if we're using spot pricing first before starting instances
            if not spot_price:
                if assign_public_ip is not None and private_ip:
                    params.update(
                        dict(
                            min_count=count_remaining,
                            max_count=count_remaining,
                            client_token=id,
                            placement_group=placement_group,
                        )
                    )
                else:
                    params.update(
                        dict(
                            min_count=count_remaining,
                            max_count=count_remaining,
                            client_token=id,
                            placement_group=placement_group,
                            private_ip_address=private_ip,
                        )
                    )

                # For ordinary (not spot) instances, we can select 'stop'
                # (the default) or 'terminate' here.
                params['instance_initiated_shutdown_behavior'] = instance_initiated_shutdown_behavior or 'stop'

                try:
                    res = ec2.run_instances(**params)
                except boto.exception.EC2ResponseError as e:
                    if (params['instance_initiated_shutdown_behavior'] != 'terminate' and
                            "InvalidParameterCombination" == e.error_code):
                        params['instance_initiated_shutdown_behavior'] = 'terminate'
                        res = ec2.run_instances(**params)
                    else:
                        raise

                instids = [i.id for i in res.instances]
                while True:
                    try:
                        ec2.get_all_instances(instids)
                        break
                    except boto.exception.EC2ResponseError as e:
                        if e.error_code == 'InvalidInstanceID.NotFound':
                            # there's a race between start and get an instance
                            continue
                        else:
                            module.fail_json_aws(e)

                # The instances returned through ec2.run_instances above can be in
                # terminated state due to idempotency. See commit 7f11c3d for a complete
                # explanation.
                terminated_instances = [
                    str(instance.id) for instance in res.instances if instance.state == 'terminated'
                ]
                if terminated_instances:
                    module.fail_json(msg="Instances with id(s) %s " % terminated_instances +
                                     "were created previously but have since been terminated - " +
                                     "use a (possibly different) 'instanceid' parameter")

            else:
                if private_ip:
                    module.fail_json(
                        msg='private_ip only available with on-demand (non-spot) instances')
                if boto_supports_param_in_spot_request(ec2, 'placement_group'):
                    params['placement_group'] = placement_group
                elif placement_group:
                    module.fail_json(
                        msg="placement_group parameter requires Boto version 2.3.0 or higher.")

                # You can't tell spot instances to 'stop'; they will always be
                # 'terminate'd. For convenience, we'll ignore the latter value.
                if instance_initiated_shutdown_behavior and instance_initiated_shutdown_behavior != 'terminate':
                    module.fail_json(
                        msg="instance_initiated_shutdown_behavior=stop is not supported for spot instances.")

                if spot_launch_group and isinstance(spot_launch_group, string_types):
                    params['launch_group'] = spot_launch_group

                params.update(dict(
                    count=count_remaining,
                    type=spot_type,
                ))

                # Set spot ValidUntil
                # ValidUntil -> (timestamp). The end date of the request, in
                # UTC format (for example, YYYY -MM -DD T*HH* :MM :SS Z).
                utc_valid_until = (
                    datetime.datetime.utcnow()
                    + datetime.timedelta(seconds=spot_wait_timeout))
                params['valid_until'] = utc_valid_until.strftime('%Y-%m-%dT%H:%M:%S.000Z')

                res = ec2.request_spot_instances(spot_price, **params)

                # Now we have to do the intermediate waiting
                if wait:
                    instids = await_spot_requests(module, ec2, res, count)
                else:
                    instids = []
        except boto.exception.BotoServerError as e:
            module.fail_json_aws(e, msg='Instance creation failed')

        # wait here until the instances are up
        num_running = 0
        wait_timeout = time.time() + wait_timeout
        res_list = ()
        while wait_timeout > time.time() and num_running < len(instids):
            try:
                res_list = ec2.get_all_instances(instids)
            except boto.exception.BotoServerError as e:
                if e.error_code == 'InvalidInstanceID.NotFound':
                    time.sleep(1)
                    continue
                else:
                    raise

            num_running = 0
            for res in res_list:
                num_running += len([i for i in res.instances if i.state == 'running'])
            if len(res_list) <= 0:
                # got a bad response of some sort, possibly due to
                # stale/cached data. Wait a second and then try again
                time.sleep(1)
                continue
            if wait and num_running < len(instids):
                time.sleep(5)
            else:
                break

        if wait and wait_timeout <= time.time():
            # waiting took too long
            module.fail_json(msg="wait for instances running timeout on %s" % time.asctime())

        # We do this after the loop ends so that we end up with one list
        for res in res_list:
            running_instances.extend(res.instances)

        # Enabled by default by AWS
        if source_dest_check is False:
            for inst in res.instances:
                inst.modify_attribute('sourceDestCheck', False)

        # Disabled by default by AWS
        if termination_protection is True:
            for inst in res.instances:
                inst.modify_attribute('disableApiTermination', True)

        # Leave this as late as possible to try and avoid InvalidInstanceID.NotFound
        if instance_tags and instids:
            try:
                ec2.create_tags(instids, instance_tags)
            except boto.exception.EC2ResponseError as e:
                module.fail_json_aws(e, msg='Instance tagging failed')

    instance_dict_array = []
    created_instance_ids = []
    for inst in running_instances:
        inst.update()
        d = get_instance_info(inst)
        created_instance_ids.append(inst.id)
        instance_dict_array.append(d)

    return (instance_dict_array, created_instance_ids, changed)


def terminate_instances(module, ec2, instance_ids):
    """
    Terminates a list of instances

    module: Ansible module object
    ec2: authenticated ec2 connection object
    termination_list: a list of instances to terminate in the form of
      [ {id: <inst-id>}, ..]

    Returns a dictionary of instance information
    about the instances terminated.

    If the instance to be terminated is running
    "changed" will be set to False.

    """

    # Whether to wait for termination to complete before returning
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))

    changed = False
    instance_dict_array = []

    if not isinstance(instance_ids, list) or len(instance_ids) < 1:
        module.fail_json(msg='instance_ids should be a list of instances, aborting')

    terminated_instance_ids = []
    for res in ec2.get_all_instances(instance_ids):
        for inst in res.instances:
            if inst.state == 'running' or inst.state == 'stopped':
                terminated_instance_ids.append(inst.id)
                instance_dict_array.append(get_instance_info(inst))
                try:
                    ec2.terminate_instances([inst.id])
                except EC2ResponseError as e:
                    module.fail_json_aws(e, msg='Unable to terminate instance {0}'.format(inst.id))
                changed = True

    # wait here until the instances are 'terminated'
    if wait:
        num_terminated = 0
        wait_timeout = time.time() + wait_timeout
        while wait_timeout > time.time() and num_terminated < len(terminated_instance_ids):
            response = ec2.get_all_instances(instance_ids=terminated_instance_ids,
                                             filters={'instance-state-name': 'terminated'})
            try:
                num_terminated = sum([len(res.instances) for res in response])
            except Exception as e:
                # got a bad response of some sort, possibly due to
                # stale/cached data. Wait a second and then try again
                time.sleep(1)
                continue

            if num_terminated < len(terminated_instance_ids):
                time.sleep(5)

        # waiting took too long
        if wait_timeout < time.time() and num_terminated < len(terminated_instance_ids):
            module.fail_json(msg="wait for instance termination timeout on %s" % time.asctime())
        # Lets get the current state of the instances after terminating - issue600
        instance_dict_array = []
        for res in ec2.get_all_instances(instance_ids=terminated_instance_ids, filters={'instance-state-name': 'terminated'}):
            for inst in res.instances:
                instance_dict_array.append(get_instance_info(inst))

    return (changed, instance_dict_array, terminated_instance_ids)


def startstop_instances(module, ec2, instance_ids, state, instance_tags):
    """
    Starts or stops a list of existing instances

    module: Ansible module object
    ec2: authenticated ec2 connection object
    instance_ids: The list of instances to start in the form of
      [ {id: <inst-id>}, ..]
    instance_tags: A dict of tag keys and values in the form of
      {key: value, ... }
    state: Intended state ("running" or "stopped")

    Returns a dictionary of instance information
    about the instances started/stopped.

    If the instance was not able to change state,
    "changed" will be set to False.

    Note that if instance_ids and instance_tags are both non-empty,
    this method will process the intersection of the two
    """

    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))
    group_id = module.params.get('group_id')
    group_name = module.params.get('group')
    changed = False
    instance_dict_array = []

    if not isinstance(instance_ids, list) or len(instance_ids) < 1:
        # Fail unless the user defined instance tags
        if not instance_tags:
            module.fail_json(msg='instance_ids should be a list of instances, aborting')

    # To make an EC2 tag filter, we need to prepend 'tag:' to each key.
    # An empty filter does no filtering, so it's safe to pass it to the
    # get_all_instances method even if the user did not specify instance_tags
    filters = {}
    if instance_tags:
        for key, value in instance_tags.items():
            filters["tag:" + key] = value

    filters['instance-state-name'] = ["pending", "running", "stopping", "stopped"]

    if module.params.get('id'):
        filters['client-token'] = module.params['id']
    # Check that our instances are not in the state we want to take

    # Check (and eventually change) instances attributes and instances state
    existing_instances_array = []
    for res in ec2.get_all_instances(instance_ids, filters=filters):
        for inst in res.instances:

            warn_if_public_ip_assignment_changed(module, inst)

            changed = (check_source_dest_attr(module, inst, ec2) or
                       check_termination_protection(module, inst) or changed)

            # Check security groups and if we're using ec2-vpc; ec2-classic security groups may not be modified
            if inst.vpc_id and group_name:
                grp_details = ec2.get_all_security_groups(filters={'vpc_id': inst.vpc_id})
                if isinstance(group_name, string_types):
                    group_name = [group_name]
                unmatched = set(group_name) - set(to_text(grp.name) for grp in grp_details)
                if unmatched:
                    module.fail_json(msg="The following group names are not valid: %s" % ', '.join(unmatched))
                group_ids = [to_text(grp.id) for grp in grp_details if to_text(grp.name) in group_name]
            elif inst.vpc_id and group_id:
                if isinstance(group_id, string_types):
                    group_id = [group_id]
                grp_details = ec2.get_all_security_groups(group_ids=group_id)
                group_ids = [grp_item.id for grp_item in grp_details]
            if inst.vpc_id and (group_name or group_id):
                if set(sg.id for sg in inst.groups) != set(group_ids):
                    changed = inst.modify_attribute('groupSet', group_ids)

            # Check instance state
            if inst.state != state:
                instance_dict_array.append(get_instance_info(inst))
                try:
                    if state == 'running':
                        inst.start()
                    else:
                        inst.stop()
                except EC2ResponseError as e:
                    module.fail_json_aws(e, 'Unable to change state for instance {0}'.format(inst.id))
                changed = True
            existing_instances_array.append(inst.id)

    instance_ids = list(set(existing_instances_array + (instance_ids or [])))
    # Wait for all the instances to finish starting or stopping
    wait_timeout = time.time() + wait_timeout
    while wait and wait_timeout > time.time():
        instance_dict_array = []
        matched_instances = []
        for res in ec2.get_all_instances(instance_ids):
            for i in res.instances:
                if i.state == state:
                    instance_dict_array.append(get_instance_info(i))
                    matched_instances.append(i)
        if len(matched_instances) < len(instance_ids):
            time.sleep(5)
        else:
            break

    if wait and wait_timeout <= time.time():
        # waiting took too long
        module.fail_json(msg="wait for instances running timeout on %s" % time.asctime())

    return (changed, instance_dict_array, instance_ids)


def restart_instances(module, ec2, instance_ids, state, instance_tags):
    """
    Restarts a list of existing instances

    module: Ansible module object
    ec2: authenticated ec2 connection object
    instance_ids: The list of instances to start in the form of
      [ {id: <inst-id>}, ..]
    instance_tags: A dict of tag keys and values in the form of
      {key: value, ... }
    state: Intended state ("restarted")

    Returns a dictionary of instance information
    about the instances.

    If the instance was not able to change state,
    "changed" will be set to False.

    Wait will not apply here as this is a OS level operation.

    Note that if instance_ids and instance_tags are both non-empty,
    this method will process the intersection of the two.
    """

    changed = False
    instance_dict_array = []

    if not isinstance(instance_ids, list) or len(instance_ids) < 1:
        # Fail unless the user defined instance tags
        if not instance_tags:
            module.fail_json(msg='instance_ids should be a list of instances, aborting')

    # To make an EC2 tag filter, we need to prepend 'tag:' to each key.
    # An empty filter does no filtering, so it's safe to pass it to the
    # get_all_instances method even if the user did not specify instance_tags
    filters = {}
    if instance_tags:
        for key, value in instance_tags.items():
            filters["tag:" + key] = value
    if module.params.get('id'):
        filters['client-token'] = module.params['id']

    # Check that our instances are not in the state we want to take

    # Check (and eventually change) instances attributes and instances state
    for res in ec2.get_all_instances(instance_ids, filters=filters):
        for inst in res.instances:

            warn_if_public_ip_assignment_changed(module, inst)

            changed = (check_source_dest_attr(module, inst, ec2) or
                       check_termination_protection(module, inst) or changed)

            # Check instance state
            if inst.state != state:
                instance_dict_array.append(get_instance_info(inst))
                try:
                    inst.reboot()
                except EC2ResponseError as e:
                    module.fail_json_aws(e, msg='Unable to change state for instance {0}'.format(inst.id))
                changed = True

    return (changed, instance_dict_array, instance_ids)


def check_termination_protection(module, inst):
    """
    Check the instance disableApiTermination attribute.

    module: Ansible module object
    inst: EC2 instance object

    returns: True if state changed None otherwise
    """

    termination_protection = module.params.get('termination_protection')

    if (inst.get_attribute('disableApiTermination')['disableApiTermination'] != termination_protection and termination_protection is not None):
        inst.modify_attribute('disableApiTermination', termination_protection)
        return True


def check_source_dest_attr(module, inst, ec2):
    """
    Check the instance sourceDestCheck attribute.

    module: Ansible module object
    inst: EC2 instance object

    returns: True if state changed None otherwise
    """

    source_dest_check = module.params.get('source_dest_check')

    if source_dest_check is not None:
        try:
            if inst.vpc_id is not None and inst.get_attribute('sourceDestCheck')['sourceDestCheck'] != source_dest_check:
                inst.modify_attribute('sourceDestCheck', source_dest_check)
                return True
        except boto.exception.EC2ResponseError as exc:
            # instances with more than one Elastic Network Interface will
            # fail, because they have the sourceDestCheck attribute defined
            # per-interface
            if exc.code == 'InvalidInstanceID':
                for interface in inst.interfaces:
                    if interface.source_dest_check != source_dest_check:
                        ec2.modify_network_interface_attribute(interface.id, "sourceDestCheck", source_dest_check)
                        return True
            else:
                module.fail_json_aws(exc, msg='Failed to handle source_dest_check state for instance {0}'.format(inst.id))


def warn_if_public_ip_assignment_changed(module, instance):
    # This is a non-modifiable attribute.
    assign_public_ip = module.params.get('assign_public_ip')

    # Check that public ip assignment is the same and warn if not
    public_dns_name = getattr(instance, 'public_dns_name', None)
    if (assign_public_ip or public_dns_name) and (not public_dns_name or assign_public_ip is False):
        module.warn("Unable to modify public ip assignment to {0} for instance {1}. "
                    "Whether or not to assign a public IP is determined during instance creation.".format(assign_public_ip, instance.id))


def main():
    argument_spec = dict(
        key_name=dict(aliases=['keypair']),
        id=dict(),
        group=dict(type='list', elements='str', aliases=['groups']),
        group_id=dict(type='list', elements='str'),
        zone=dict(aliases=['aws_zone', 'ec2_zone']),
        instance_type=dict(aliases=['type']),
        spot_price=dict(),
        spot_type=dict(default='one-time', choices=["one-time", "persistent"]),
        spot_launch_group=dict(),
        image=dict(),
        kernel=dict(),
        count=dict(type='int', default='1'),
        monitoring=dict(type='bool', default=False),
        ramdisk=dict(),
        wait=dict(type='bool', default=False),
        wait_timeout=dict(type='int', default=300),
        spot_wait_timeout=dict(type='int', default=600),
        placement_group=dict(),
        user_data=dict(),
        instance_tags=dict(type='dict'),
        vpc_subnet_id=dict(),
        assign_public_ip=dict(type='bool'),
        private_ip=dict(),
        instance_profile_name=dict(),
        instance_ids=dict(type='list', elements='str', aliases=['instance_id']),
        source_dest_check=dict(type='bool', default=None),
        termination_protection=dict(type='bool', default=None),
        state=dict(default='present', choices=['present', 'absent', 'running', 'restarted', 'stopped']),
        instance_initiated_shutdown_behavior=dict(default='stop', choices=['stop', 'terminate']),
        exact_count=dict(type='int', default=None),
        count_tag=dict(type='raw'),
        volumes=dict(type='list', elements='dict',),
        ebs_optimized=dict(type='bool', default=False),
        tenancy=dict(default='default', choices=['default', 'dedicated']),
        network_interfaces=dict(type='list', elements='str', aliases=['network_interface'])
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        check_boto3=False,
        mutually_exclusive=[
            # Can be uncommented when we finish the deprecation cycle.
            # ['group', 'group_id'],
            ['exact_count', 'count'],
            ['exact_count', 'state'],
            ['exact_count', 'instance_ids'],
            ['network_interfaces', 'assign_public_ip'],
            ['network_interfaces', 'group'],
            ['network_interfaces', 'group_id'],
            ['network_interfaces', 'private_ip'],
            ['network_interfaces', 'vpc_subnet_id'],
        ],
    )

    module.deprecate("The 'ec2' module has been deprecated and replaced by the 'ec2_instance' module'",
                     version='4.0.0', collection_name='amazon.aws')

    if module.params.get('group') and module.params.get('group_id'):
        module.deprecate(
            msg='Support for passing both group and group_id has been deprecated. '
            'Currently group_id is ignored, in future passing both will result in an error',
            date='2022-06-01', collection_name='amazon.aws')

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module)
        if module.params.get('region') or not module.params.get('ec2_url'):
            ec2 = ec2_connect(module)
        elif module.params.get('ec2_url'):
            ec2 = connect_ec2_endpoint(ec2_url, **aws_connect_kwargs)

        if 'region' not in aws_connect_kwargs:
            aws_connect_kwargs['region'] = ec2.region

        vpc = connect_vpc(**aws_connect_kwargs)
    except boto.exception.NoAuthHandlerFound as e:
        module.fail_json_aws(e, msg='Failed to get connection')

    tagged_instances = []

    state = module.params['state']

    if state == 'absent':
        instance_ids = module.params['instance_ids']
        if not instance_ids:
            module.fail_json(msg='instance_ids list is required for absent state')

        (changed, instance_dict_array, new_instance_ids) = terminate_instances(module, ec2, instance_ids)

    elif state in ('running', 'stopped'):
        instance_ids = module.params.get('instance_ids')
        instance_tags = module.params.get('instance_tags')
        if not (isinstance(instance_ids, list) or isinstance(instance_tags, dict)):
            module.fail_json(msg='running list needs to be a list of instances or set of tags to run: %s' % instance_ids)

        (changed, instance_dict_array, new_instance_ids) = startstop_instances(module, ec2, instance_ids, state, instance_tags)

    elif state in ('restarted'):
        instance_ids = module.params.get('instance_ids')
        instance_tags = module.params.get('instance_tags')
        if not (isinstance(instance_ids, list) or isinstance(instance_tags, dict)):
            module.fail_json(msg='running list needs to be a list of instances or set of tags to run: %s' % instance_ids)

        (changed, instance_dict_array, new_instance_ids) = restart_instances(module, ec2, instance_ids, state, instance_tags)

    elif state == 'present':
        # Changed is always set to true when provisioning new instances
        if not module.params.get('image'):
            module.fail_json(msg='image parameter is required for new instance')

        if module.params.get('exact_count') is None:
            (instance_dict_array, new_instance_ids, changed) = create_instances(module, ec2, vpc)
        else:
            (tagged_instances, instance_dict_array, new_instance_ids, changed) = enforce_count(module, ec2, vpc)

    # Always return instances in the same order
    if new_instance_ids:
        new_instance_ids.sort()
    if instance_dict_array:
        instance_dict_array.sort(key=lambda x: x['id'])
    if tagged_instances:
        tagged_instances.sort(key=lambda x: x['id'])

    module.exit_json(changed=changed, instance_ids=new_instance_ids, instances=instance_dict_array, tagged_instances=tagged_instances)


if __name__ == '__main__':
    main()
