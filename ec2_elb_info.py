#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: ec2_elb_info
version_added: 1.0.0
short_description: Gather information about EC2 Elastic Load Balancers in AWS
description:
    - Gather information about EC2 Elastic Load Balancers in AWS
    - This module was called C(ec2_elb_facts) before Ansible 2.9. The usage did not change.
author:
  - "Michael Schultz (@mjschultz)"
  - "Fernando Jose Pando (@nand0p)"
options:
  names:
    description:
      - List of ELB names to gather information about. Pass this option to gather information about a set of ELBs, otherwise, all ELBs are returned.
    type: list
    elements: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2

'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.
# Output format tries to match amazon.aws.ec2_elb_lb module input parameters

- name: Gather information about all ELBs
  community.aws.ec2_elb_info:
  register: elb_info
- ansible.builtin.debug:
    msg: "{{ item.dns_name }}"
  loop: "{{ elb_info.elbs }}"

- name: Gather information about a particular ELB
  community.aws.ec2_elb_info:
    names: frontend-prod-elb
  register: elb_info

- ansible.builtin.debug:
    msg: "{{ elb_info.elbs.0.dns_name }}"

- name: Gather information about a set of ELBs
  community.aws.ec2_elb_info:
    names:
    - frontend-prod-elb
    - backend-prod-elb
  register: elb_info

- ansible.builtin.debug:
    msg: "{{ item.dns_name }}"
  loop: "{{ elb_info.elbs }}"

'''

import traceback

try:
    import boto.ec2.elb
    from boto.ec2.tag import Tag
    from boto.exception import BotoServerError
except ImportError:
    pass  # Handled by ec2.HAS_BOTO

from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import connect_to_aws
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import get_aws_connection_info
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import HAS_BOTO


class ElbInformation(object):
    """Handles ELB information."""

    def __init__(self, module, names, region, **aws_connect_params):

        self.module = module
        self.names = names
        self.region = region
        self.aws_connect_params = aws_connect_params
        self.connection = self._get_elb_connection()

    def _get_tags(self, elbname):
        params = {'LoadBalancerNames.member.1': elbname}
        elb_tags = self.connection.get_list('DescribeTags', params, [('member', Tag)])
        return dict((tag.Key, tag.Value) for tag in elb_tags if hasattr(tag, 'Key'))

    @AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
    def _get_elb_connection(self):
        return connect_to_aws(boto.ec2.elb, self.region, **self.aws_connect_params)

    def _get_elb_listeners(self, listeners):
        listener_list = []

        for listener in listeners:
            listener_dict = {
                'load_balancer_port': listener[0],
                'instance_port': listener[1],
                'protocol': listener[2],
                'instance_protocol': listener[3]
            }

            try:
                ssl_certificate_id = listener[4]
            except IndexError:
                pass
            else:
                if ssl_certificate_id:
                    listener_dict['ssl_certificate_id'] = ssl_certificate_id

            listener_list.append(listener_dict)

        return listener_list

    def _get_health_check(self, health_check):
        protocol, port_path = health_check.target.split(':')
        try:
            port, path = port_path.split('/', 1)
            path = '/{0}'.format(path)
        except ValueError:
            port = port_path
            path = None

        health_check_dict = {
            'ping_protocol': protocol.lower(),
            'ping_port': int(port),
            'response_timeout': health_check.timeout,
            'interval': health_check.interval,
            'unhealthy_threshold': health_check.unhealthy_threshold,
            'healthy_threshold': health_check.healthy_threshold,
        }

        if path:
            health_check_dict['ping_path'] = path
        return health_check_dict

    @AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
    def _get_elb_info(self, elb):
        elb_info = {
            'name': elb.name,
            'zones': elb.availability_zones,
            'dns_name': elb.dns_name,
            'canonical_hosted_zone_name': elb.canonical_hosted_zone_name,
            'canonical_hosted_zone_name_id': elb.canonical_hosted_zone_name_id,
            'hosted_zone_name': elb.canonical_hosted_zone_name,
            'hosted_zone_id': elb.canonical_hosted_zone_name_id,
            'instances': [instance.id for instance in elb.instances],
            'listeners': self._get_elb_listeners(elb.listeners),
            'scheme': elb.scheme,
            'security_groups': elb.security_groups,
            'health_check': self._get_health_check(elb.health_check),
            'subnets': elb.subnets,
            'instances_inservice': [],
            'instances_inservice_count': 0,
            'instances_outofservice': [],
            'instances_outofservice_count': 0,
            'instances_inservice_percent': 0.0,
            'tags': self._get_tags(elb.name)
        }

        if elb.vpc_id:
            elb_info['vpc_id'] = elb.vpc_id

        if elb.instances:
            instance_health = self.connection.describe_instance_health(elb.name)
            elb_info['instances_inservice'] = [inst.instance_id for inst in instance_health if inst.state == 'InService']
            elb_info['instances_inservice_count'] = len(elb_info['instances_inservice'])
            elb_info['instances_outofservice'] = [inst.instance_id for inst in instance_health if inst.state == 'OutOfService']
            elb_info['instances_outofservice_count'] = len(elb_info['instances_outofservice'])
            try:
                elb_info['instances_inservice_percent'] = (
                    float(elb_info['instances_inservice_count']) /
                    float(elb_info['instances_inservice_count'] + elb_info['instances_outofservice_count'])
                ) * 100.
            except ZeroDivisionError:
                elb_info['instances_inservice_percent'] = 0.
        return elb_info

    def list_elbs(self):
        elb_array, token = [], None
        get_elb_with_backoff = AWSRetry.backoff(tries=5, delay=5, backoff=2.0)(self.connection.get_all_load_balancers)
        while True:
            all_elbs = get_elb_with_backoff(marker=token)
            token = all_elbs.next_marker

            if all_elbs:
                if self.names:
                    for existing_lb in all_elbs:
                        if existing_lb.name in self.names:
                            elb_array.append(existing_lb)
                else:
                    elb_array.extend(all_elbs)
            else:
                break

            if token is None:
                break

        return list(map(self._get_elb_info, elb_array))


def main():
    argument_spec = dict(
        names={'default': [], 'type': 'list', 'elements': 'str'}
    )
    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True)
    if module._name == 'ec2_elb_facts':
        module.deprecate("The 'ec2_elb_facts' module has been renamed to 'ec2_elb_info'", date='2021-12-01', collection_name='community.aws')

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    try:
        region, ec2_url, aws_connect_params = get_aws_connection_info(module)
        if not region:
            module.fail_json(msg="region must be specified")

        names = module.params['names']
        elb_information = ElbInformation(
            module, names, region, **aws_connect_params)

        ec2_info_result = dict(changed=False,
                               elbs=elb_information.list_elbs())

    except BotoServerError as err:
        module.fail_json(msg="{0}: {1}".format(err.error_code, err.error_message),
                         exception=traceback.format_exc())

    module.exit_json(**ec2_info_result)


if __name__ == '__main__':
    main()
