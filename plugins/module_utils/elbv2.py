# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import traceback
from copy import deepcopy

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass

from .ec2 import AWSRetry
from .ec2 import ansible_dict_to_boto3_tag_list
from .ec2 import boto3_tag_list_to_ansible_dict
from .ec2 import get_ec2_security_group_ids_from_names
from .elb_utils import convert_tg_name_to_arn
from .elb_utils import get_elb
from .elb_utils import get_elb_listener
from .waiters import get_waiter


def _simple_forward_config_arn(config, parent_arn):
    config = deepcopy(config)

    stickiness = config.pop('TargetGroupStickinessConfig', {'Enabled': False})
    # Stickiness options set, non default value
    if stickiness != {'Enabled': False}:
        return False

    target_groups = config.pop('TargetGroups', [])

    # non-default config left over, probably invalid
    if config:
        return False
    # Multiple TGS, not simple
    if len(target_groups) > 1:
        return False

    if not target_groups:
        # with no TGs defined, but an ARN set, this is one of the minimum possible configs
        return parent_arn or False

    target_group = target_groups[0]
    # We don't care about the weight with a single TG
    target_group.pop('Weight', None)

    target_group_arn = target_group.pop('TargetGroupArn', None)

    # non-default config left over
    if target_group:
        return False

    # We didn't find an ARN
    if not (target_group_arn or parent_arn):
        return False

    # Only one
    if not parent_arn:
        return target_group_arn
    if not target_group_arn:
        return parent_arn

    if parent_arn != target_group_arn:
        return False

    return target_group_arn


# ForwardConfig may be optional if we've got a single TargetGroupArn entry
def _prune_ForwardConfig(action):
    """
    Drops a redundant ForwardConfig where TargetGroupARN has already been set.
    (So we can perform comparisons)
    """
    if action.get('Type', "") != 'forward':
        return action
    if "ForwardConfig" not in action:
        return action

    parent_arn = action.get('TargetGroupArn', None)
    arn = _simple_forward_config_arn(action["ForwardConfig"], parent_arn)
    if not arn:
        return action

    # Remove the redundant ForwardConfig
    newAction = action.copy()
    del newAction["ForwardConfig"]
    newAction["TargetGroupArn"] = arn
    return newAction


# the AWS api won't return the client secret, so we'll have to remove it
# or the module will always see the new and current actions as different
# and try to apply the same config
def _prune_secret(action):
    if action['Type'] != 'authenticate-oidc':
        return action

    action['AuthenticateOidcConfig'].pop('ClientSecret', None)
    if action['AuthenticateOidcConfig'].get('UseExistingClientSecret', False):
        action['AuthenticateOidcConfig'].pop('UseExistingClientSecret')

    return action


def _sort_actions(actions):
    return sorted(actions, key=lambda x: x.get('Order', 0))


class ElasticLoadBalancerV2(object):

    def __init__(self, connection, module):

        self.connection = connection
        self.module = module
        self.changed = False
        self.new_load_balancer = False
        self.scheme = module.params.get("scheme")
        self.name = module.params.get("name")
        self.subnet_mappings = module.params.get("subnet_mappings")
        self.subnets = module.params.get("subnets")
        self.deletion_protection = module.params.get("deletion_protection")
        self.elb_ip_addr_type = module.params.get("ip_address_type")
        self.wait = module.params.get("wait")

        if module.params.get("tags") is not None:
            self.tags = ansible_dict_to_boto3_tag_list(module.params.get("tags"))
        else:
            self.tags = None

        self.purge_tags = module.params.get("purge_tags")

        self.elb = get_elb(connection, module, self.name)
        if self.elb is not None:
            self.elb_attributes = self.get_elb_attributes()
            self.elb_ip_addr_type = self.get_elb_ip_address_type()
            self.elb['tags'] = self.get_elb_tags()
        else:
            self.elb_attributes = None

    def wait_for_ip_type(self, elb_arn, ip_type):
        """
        Wait for load balancer to reach 'active' status

        :param elb_arn: The load balancer ARN
        :return:
        """

        if not self.wait:
            return

        waiter_names = {
            'ipv4': 'load_balancer_ip_address_type_ipv4',
            'dualstack': 'load_balancer_ip_address_type_dualstack',
        }
        if ip_type not in waiter_names:
            return

        try:
            waiter = get_waiter(self.connection, waiter_names.get(ip_type))
            waiter.wait(LoadBalancerArns=[elb_arn])
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e)

    def wait_for_status(self, elb_arn):
        """
        Wait for load balancer to reach 'active' status

        :param elb_arn: The load balancer ARN
        :return:
        """

        if not self.wait:
            return

        try:
            waiter = get_waiter(self.connection, 'load_balancer_available')
            waiter.wait(LoadBalancerArns=[elb_arn])
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e)

    def wait_for_deletion(self, elb_arn):
        """
        Wait for load balancer to reach 'active' status

        :param elb_arn: The load balancer ARN
        :return:
        """

        if not self.wait:
            return

        try:
            waiter = get_waiter(self.connection, 'load_balancers_deleted')
            waiter.wait(LoadBalancerArns=[elb_arn])
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e)

    def get_elb_attributes(self):
        """
        Get load balancer attributes

        :return:
        """

        try:
            attr_list = AWSRetry.jittered_backoff()(
                self.connection.describe_load_balancer_attributes
            )(LoadBalancerArn=self.elb['LoadBalancerArn'])['Attributes']

            elb_attributes = boto3_tag_list_to_ansible_dict(attr_list)
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e)

        # Replace '.' with '_' in attribute key names to make it more Ansibley
        return dict((k.replace('.', '_'), v) for k, v in elb_attributes.items())

    def get_elb_ip_address_type(self):
        """
        Retrieve load balancer ip address type using describe_load_balancers

        :return:
        """

        return self.elb.get('IpAddressType', None)

    def update_elb_attributes(self):
        """
        Update the elb_attributes parameter
        :return:
        """
        self.elb_attributes = self.get_elb_attributes()

    def get_elb_tags(self):
        """
        Get load balancer tags

        :return:
        """

        try:
            return AWSRetry.jittered_backoff()(
                self.connection.describe_tags
            )(ResourceArns=[self.elb['LoadBalancerArn']])['TagDescriptions'][0]['Tags']
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e)

    def delete_tags(self, tags_to_delete):
        """
        Delete elb tags

        :return:
        """

        try:
            AWSRetry.jittered_backoff()(
                self.connection.remove_tags
            )(ResourceArns=[self.elb['LoadBalancerArn']], TagKeys=tags_to_delete)
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e)

        self.changed = True

    def modify_tags(self):
        """
        Modify elb tags

        :return:
        """

        try:
            AWSRetry.jittered_backoff()(
                self.connection.add_tags
            )(ResourceArns=[self.elb['LoadBalancerArn']], Tags=self.tags)
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e)

        self.changed = True

    def delete(self):
        """
        Delete elb
        :return:
        """

        try:
            AWSRetry.jittered_backoff()(
                self.connection.delete_load_balancer
            )(LoadBalancerArn=self.elb['LoadBalancerArn'])
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e)

        self.wait_for_deletion(self.elb['LoadBalancerArn'])

        self.changed = True

    def compare_subnets(self):
        """
        Compare user subnets with current ELB subnets

        :return: bool True if they match otherwise False
        """

        subnet_mapping_id_list = []
        subnet_mappings = []

        # Check if we're dealing with subnets or subnet_mappings
        if self.subnets is not None:
            # Convert subnets to subnet_mappings format for comparison
            for subnet in self.subnets:
                subnet_mappings.append({'SubnetId': subnet})

        if self.subnet_mappings is not None:
            # Use this directly since we're comparing as a mapping
            subnet_mappings = self.subnet_mappings

        # Build a subnet_mapping style struture of what's currently
        # on the load balancer
        for subnet in self.elb['AvailabilityZones']:
            this_mapping = {'SubnetId': subnet['SubnetId']}
            for address in subnet.get('LoadBalancerAddresses', []):
                if 'AllocationId' in address:
                    this_mapping['AllocationId'] = address['AllocationId']
                    break

            subnet_mapping_id_list.append(this_mapping)

        return set(frozenset(mapping.items()) for mapping in subnet_mapping_id_list) == set(frozenset(mapping.items()) for mapping in subnet_mappings)

    def modify_subnets(self):
        """
        Modify elb subnets to match module parameters
        :return:
        """

        try:
            AWSRetry.jittered_backoff()(
                self.connection.set_subnets
            )(LoadBalancerArn=self.elb['LoadBalancerArn'], Subnets=self.subnets)
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e)

        self.changed = True

    def update(self):
        """
        Update the elb from AWS
        :return:
        """

        self.elb = get_elb(self.connection, self.module, self.module.params.get("name"))
        self.elb['tags'] = self.get_elb_tags()

    def modify_ip_address_type(self, ip_addr_type):
        """
        Modify ELB ip address type
        :return:
        """
        if ip_addr_type is None:
            return
        if self.elb_ip_addr_type == ip_addr_type:
            return

        try:
            AWSRetry.jittered_backoff()(
                self.connection.set_ip_address_type
            )(LoadBalancerArn=self.elb['LoadBalancerArn'], IpAddressType=ip_addr_type)
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e)

        self.changed = True
        self.wait_for_ip_type(self.elb['LoadBalancerArn'], ip_addr_type)

    def _elb_create_params(self):
        # Required parameters
        params = dict()
        params['Name'] = self.name
        params['Type'] = self.type

        # Other parameters
        if self.elb_ip_addr_type is not None:
            params['IpAddressType'] = self.elb_ip_addr_type
        if self.subnets is not None:
            params['Subnets'] = self.subnets
        if self.subnet_mappings is not None:
            params['SubnetMappings'] = self.subnet_mappings
        if self.tags:
            params['Tags'] = self.tags
        # Scheme isn't supported for GatewayLBs, so we won't add it here, even though we don't
        # support them yet.

        return params

    def create_elb(self):
        """
        Create a load balancer
        :return:
        """

        params = self._elb_create_params()

        try:
            self.elb = AWSRetry.jittered_backoff()(self.connection.create_load_balancer)(**params)['LoadBalancers'][0]
            self.changed = True
            self.new_load_balancer = True
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e)

        self.wait_for_status(self.elb['LoadBalancerArn'])


class ApplicationLoadBalancer(ElasticLoadBalancerV2):

    def __init__(self, connection, connection_ec2, module):
        """

        :param connection: boto3 connection
        :param module: Ansible module
        """
        super(ApplicationLoadBalancer, self).__init__(connection, module)

        self.connection_ec2 = connection_ec2

        # Ansible module parameters specific to ALBs
        self.type = 'application'
        if module.params.get('security_groups') is not None:
            try:
                self.security_groups = AWSRetry.jittered_backoff()(
                    get_ec2_security_group_ids_from_names
                )(module.params.get('security_groups'), self.connection_ec2, boto3=True)
            except ValueError as e:
                self.module.fail_json(msg=str(e), exception=traceback.format_exc())
            except (BotoCoreError, ClientError) as e:
                self.module.fail_json_aws(e)
        else:
            self.security_groups = module.params.get('security_groups')
        self.access_logs_enabled = module.params.get("access_logs_enabled")
        self.access_logs_s3_bucket = module.params.get("access_logs_s3_bucket")
        self.access_logs_s3_prefix = module.params.get("access_logs_s3_prefix")
        self.idle_timeout = module.params.get("idle_timeout")
        self.http2 = module.params.get("http2")
        self.http_desync_mitigation_mode = module.params.get("http_desync_mitigation_mode")
        self.http_drop_invalid_header_fields = module.params.get("http_drop_invalid_header_fields")
        self.http_x_amzn_tls_version_and_cipher_suite = module.params.get("http_x_amzn_tls_version_and_cipher_suite")
        self.http_xff_client_port = module.params.get("http_xff_client_port")
        self.waf_fail_open = module.params.get("waf_fail_open")

        if self.elb is not None and self.elb['Type'] != 'application':
            self.module.fail_json(msg="The load balancer type you are trying to manage is not application. Try elb_network_lb module instead.")

    def _elb_create_params(self):
        params = super()._elb_create_params()

        if self.security_groups is not None:
            params['SecurityGroups'] = self.security_groups
        params['Scheme'] = self.scheme

        return params

    def compare_elb_attributes(self):
        """
        Compare user attributes with current ELB attributes
        :return: bool True if they match otherwise False
        """

        update_attributes = []
        if self.access_logs_enabled is not None and str(self.access_logs_enabled).lower() != self.elb_attributes['access_logs_s3_enabled']:
            update_attributes.append({'Key': 'access_logs.s3.enabled', 'Value': str(self.access_logs_enabled).lower()})
        if self.access_logs_s3_bucket is not None and self.access_logs_s3_bucket != self.elb_attributes['access_logs_s3_bucket']:
            update_attributes.append({'Key': 'access_logs.s3.bucket', 'Value': self.access_logs_s3_bucket})
        if self.access_logs_s3_prefix is not None and self.access_logs_s3_prefix != self.elb_attributes['access_logs_s3_prefix']:
            update_attributes.append({'Key': 'access_logs.s3.prefix', 'Value': self.access_logs_s3_prefix})
        if self.deletion_protection is not None and str(self.deletion_protection).lower() != self.elb_attributes['deletion_protection_enabled']:
            update_attributes.append({'Key': 'deletion_protection.enabled', 'Value': str(self.deletion_protection).lower()})
        if self.idle_timeout is not None and str(self.idle_timeout) != self.elb_attributes['idle_timeout_timeout_seconds']:
            update_attributes.append({'Key': 'idle_timeout.timeout_seconds', 'Value': str(self.idle_timeout)})
        if self.http2 is not None and str(self.http2).lower() != self.elb_attributes['routing_http2_enabled']:
            update_attributes.append({'Key': 'routing.http2.enabled', 'Value': str(self.http2).lower()})
        if self.http_desync_mitigation_mode is not None and str(self.http_desync_mitigation_mode).lower() != \
                self.elb_attributes['routing_http_desync_mitigation_mode']:
            update_attributes.append({'Key': 'routing.http.desync_mitigation_mode', 'Value': str(self.http_desync_mitigation_mode).lower()})
        if self.http_drop_invalid_header_fields is not None and str(self.http_drop_invalid_header_fields).lower() != \
                self.elb_attributes['routing_http_drop_invalid_header_fields_enabled']:
            update_attributes.append({'Key': 'routing.http.drop_invalid_header_fields.enabled', 'Value': str(self.http_drop_invalid_header_fields).lower()})
        if self.http_x_amzn_tls_version_and_cipher_suite is not None and str(self.http_x_amzn_tls_version_and_cipher_suite).lower() != \
                self.elb_attributes['routing_http_x_amzn_tls_version_and_cipher_suite_enabled']:
            update_attributes.append({'Key': 'routing.http.x_amzn_tls_version_and_cipher_suite.enabled',
                                      'Value': str(self.http_x_amzn_tls_version_and_cipher_suite).lower()})
        if self.http_xff_client_port is not None and str(self.http_xff_client_port).lower() != \
                self.elb_attributes['routing_http_xff_client_port_enabled']:
            update_attributes.append({'Key': 'routing.http.xff_client_port.enabled', 'Value': str(self.http_xff_client_port).lower()})
        if self.waf_fail_open is not None and str(self.waf_fail_open).lower() != \
                self.elb_attributes['waf_fail_open_enabled']:
            update_attributes.append({'Key': 'waf.fail_open.enabled', 'Value': str(self.waf_fail_open).lower()})

        if update_attributes:
            return False
        else:
            return True

    def modify_elb_attributes(self):
        """
        Update Application ELB attributes if required

        :return:
        """

        update_attributes = []

        if self.access_logs_enabled is not None and str(self.access_logs_enabled).lower() != self.elb_attributes['access_logs_s3_enabled']:
            update_attributes.append({'Key': 'access_logs.s3.enabled', 'Value': str(self.access_logs_enabled).lower()})
        if self.access_logs_s3_bucket is not None and self.access_logs_s3_bucket != self.elb_attributes['access_logs_s3_bucket']:
            update_attributes.append({'Key': 'access_logs.s3.bucket', 'Value': self.access_logs_s3_bucket})
        if self.access_logs_s3_prefix is not None and self.access_logs_s3_prefix != self.elb_attributes['access_logs_s3_prefix']:
            update_attributes.append({'Key': 'access_logs.s3.prefix', 'Value': self.access_logs_s3_prefix})
        if self.deletion_protection is not None and str(self.deletion_protection).lower() != self.elb_attributes['deletion_protection_enabled']:
            update_attributes.append({'Key': 'deletion_protection.enabled', 'Value': str(self.deletion_protection).lower()})
        if self.idle_timeout is not None and str(self.idle_timeout) != self.elb_attributes['idle_timeout_timeout_seconds']:
            update_attributes.append({'Key': 'idle_timeout.timeout_seconds', 'Value': str(self.idle_timeout)})
        if self.http2 is not None and str(self.http2).lower() != self.elb_attributes['routing_http2_enabled']:
            update_attributes.append({'Key': 'routing.http2.enabled', 'Value': str(self.http2).lower()})
        if self.http_desync_mitigation_mode is not None and str(self.http_desync_mitigation_mode).lower() != \
                self.elb_attributes['routing_http_desync_mitigation_mode']:
            update_attributes.append({'Key': 'routing.http.desync_mitigation_mode', 'Value': str(self.http_desync_mitigation_mode).lower()})
        if self.http_drop_invalid_header_fields is not None and str(self.http_drop_invalid_header_fields).lower() != \
                self.elb_attributes['routing_http_drop_invalid_header_fields_enabled']:
            update_attributes.append({'Key': 'routing.http.drop_invalid_header_fields.enabled', 'Value': str(self.http_drop_invalid_header_fields).lower()})
        if self.http_x_amzn_tls_version_and_cipher_suite is not None and str(self.http_x_amzn_tls_version_and_cipher_suite).lower() != \
                self.elb_attributes['routing_http_x_amzn_tls_version_and_cipher_suite_enabled']:
            update_attributes.append({'Key': 'routing.http.x_amzn_tls_version_and_cipher_suite.enabled',
                                      'Value': str(self.http_x_amzn_tls_version_and_cipher_suite).lower()})
        if self.http_xff_client_port is not None and str(self.http_xff_client_port).lower() != \
                self.elb_attributes['routing_http_xff_client_port_enabled']:
            update_attributes.append({'Key': 'routing.http.xff_client_port.enabled', 'Value': str(self.http_xff_client_port).lower()})
        if self.waf_fail_open is not None and str(self.waf_fail_open).lower() != \
                self.elb_attributes['waf_fail_open_enabled']:
            update_attributes.append({'Key': 'waf.fail_open.enabled', 'Value': str(self.waf_fail_open).lower()})

        if update_attributes:
            try:
                AWSRetry.jittered_backoff()(
                    self.connection.modify_load_balancer_attributes
                )(LoadBalancerArn=self.elb['LoadBalancerArn'], Attributes=update_attributes)
                self.changed = True
            except (BotoCoreError, ClientError) as e:
                # Something went wrong setting attributes. If this ELB was created during this task, delete it to leave a consistent state
                if self.new_load_balancer:
                    AWSRetry.jittered_backoff()(self.connection.delete_load_balancer)(LoadBalancerArn=self.elb['LoadBalancerArn'])
                self.module.fail_json_aws(e)

    def compare_security_groups(self):
        """
        Compare user security groups with current ELB security groups

        :return: bool True if they match otherwise False
        """

        if set(self.elb['SecurityGroups']) != set(self.security_groups):
            return False
        else:
            return True

    def modify_security_groups(self):
        """
        Modify elb security groups to match module parameters
        :return:
        """

        try:
            AWSRetry.jittered_backoff()(
                self.connection.set_security_groups
            )(LoadBalancerArn=self.elb['LoadBalancerArn'], SecurityGroups=self.security_groups)
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e)

        self.changed = True


class NetworkLoadBalancer(ElasticLoadBalancerV2):

    def __init__(self, connection, connection_ec2, module):

        """

        :param connection: boto3 connection
        :param module: Ansible module
        """
        super(NetworkLoadBalancer, self).__init__(connection, module)

        self.connection_ec2 = connection_ec2

        # Ansible module parameters specific to NLBs
        self.type = 'network'
        self.cross_zone_load_balancing = module.params.get('cross_zone_load_balancing')

        if self.elb is not None and self.elb['Type'] != 'network':
            self.module.fail_json(msg="The load balancer type you are trying to manage is not network. Try elb_application_lb module instead.")

    def _elb_create_params(self):
        params = super()._elb_create_params()

        params['Scheme'] = self.scheme

        return params

    def modify_elb_attributes(self):
        """
        Update Network ELB attributes if required

        :return:
        """

        update_attributes = []

        if self.cross_zone_load_balancing is not None and str(self.cross_zone_load_balancing).lower() != \
                self.elb_attributes['load_balancing_cross_zone_enabled']:
            update_attributes.append({'Key': 'load_balancing.cross_zone.enabled', 'Value': str(self.cross_zone_load_balancing).lower()})
        if self.deletion_protection is not None and str(self.deletion_protection).lower() != self.elb_attributes['deletion_protection_enabled']:
            update_attributes.append({'Key': 'deletion_protection.enabled', 'Value': str(self.deletion_protection).lower()})

        if update_attributes:
            try:
                AWSRetry.jittered_backoff()(
                    self.connection.modify_load_balancer_attributes
                )(LoadBalancerArn=self.elb['LoadBalancerArn'], Attributes=update_attributes)
                self.changed = True
            except (BotoCoreError, ClientError) as e:
                # Something went wrong setting attributes. If this ELB was created during this task, delete it to leave a consistent state
                if self.new_load_balancer:
                    AWSRetry.jittered_backoff()(self.connection.delete_load_balancer)(LoadBalancerArn=self.elb['LoadBalancerArn'])
                self.module.fail_json_aws(e)

    def modify_subnets(self):
        """
        Modify elb subnets to match module parameters (unsupported for NLB)
        :return:
        """

        self.module.fail_json(msg='Modifying subnets and elastic IPs is not supported for Network Load Balancer')


class ELBListeners(object):

    def __init__(self, connection, module, elb_arn):

        self.connection = connection
        self.module = module
        self.elb_arn = elb_arn
        listeners = module.params.get("listeners")
        if listeners is not None:
            # Remove suboption argspec defaults of None from each listener
            listeners = [dict((x, listener_dict[x]) for x in listener_dict if listener_dict[x] is not None) for listener_dict in listeners]
        self.listeners = self._ensure_listeners_default_action_has_arn(listeners)
        self.current_listeners = self._get_elb_listeners()
        self.purge_listeners = module.params.get("purge_listeners")
        self.changed = False

    def update(self):
        """
        Update the listeners for the ELB

        :return:
        """
        self.current_listeners = self._get_elb_listeners()

    def _get_elb_listeners(self):
        """
        Get ELB listeners

        :return:
        """

        try:
            listener_paginator = self.connection.get_paginator('describe_listeners')
            return (AWSRetry.jittered_backoff()(listener_paginator.paginate)(LoadBalancerArn=self.elb_arn).build_full_result())['Listeners']
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e)

    def _ensure_listeners_default_action_has_arn(self, listeners):
        """
        If a listener DefaultAction has been passed with a Target Group Name instead of ARN, lookup the ARN and
        replace the name.

        :param listeners: a list of listener dicts
        :return: the same list of dicts ensuring that each listener DefaultActions dict has TargetGroupArn key. If a TargetGroupName key exists, it is removed.
        """

        if not listeners:
            listeners = []

        fixed_listeners = []
        for listener in listeners:
            fixed_actions = []
            for action in listener['DefaultActions']:
                if 'TargetGroupName' in action:
                    action['TargetGroupArn'] = convert_tg_name_to_arn(self.connection,
                                                                      self.module,
                                                                      action['TargetGroupName'])
                    del action['TargetGroupName']
                fixed_actions.append(action)
            listener['DefaultActions'] = fixed_actions
            fixed_listeners.append(listener)

        return fixed_listeners

    def compare_listeners(self):
        """

        :return:
        """
        listeners_to_modify = []
        listeners_to_delete = []
        listeners_to_add = deepcopy(self.listeners)

        # Check each current listener port to see if it's been passed to the module
        for current_listener in self.current_listeners:
            current_listener_passed_to_module = False
            for new_listener in self.listeners[:]:
                new_listener['Port'] = int(new_listener['Port'])
                if current_listener['Port'] == new_listener['Port']:
                    current_listener_passed_to_module = True
                    # Remove what we match so that what is left can be marked as 'to be added'
                    listeners_to_add.remove(new_listener)
                    modified_listener = self._compare_listener(current_listener, new_listener)
                    if modified_listener:
                        modified_listener['Port'] = current_listener['Port']
                        modified_listener['ListenerArn'] = current_listener['ListenerArn']
                        listeners_to_modify.append(modified_listener)
                    break

            # If the current listener was not matched against passed listeners and purge is True, mark for removal
            if not current_listener_passed_to_module and self.purge_listeners:
                listeners_to_delete.append(current_listener['ListenerArn'])

        return listeners_to_add, listeners_to_modify, listeners_to_delete

    def _compare_listener(self, current_listener, new_listener):
        """
        Compare two listeners.

        :param current_listener:
        :param new_listener:
        :return:
        """

        modified_listener = {}

        # Port
        if current_listener['Port'] != new_listener['Port']:
            modified_listener['Port'] = new_listener['Port']

        # Protocol
        if current_listener['Protocol'] != new_listener['Protocol']:
            modified_listener['Protocol'] = new_listener['Protocol']

        # If Protocol is HTTPS, check additional attributes
        if current_listener['Protocol'] == 'HTTPS' and new_listener['Protocol'] == 'HTTPS':
            # Cert
            if current_listener['SslPolicy'] != new_listener['SslPolicy']:
                modified_listener['SslPolicy'] = new_listener['SslPolicy']
            if current_listener['Certificates'][0]['CertificateArn'] != new_listener['Certificates'][0]['CertificateArn']:
                modified_listener['Certificates'] = []
                modified_listener['Certificates'].append({})
                modified_listener['Certificates'][0]['CertificateArn'] = new_listener['Certificates'][0]['CertificateArn']
        elif current_listener['Protocol'] != 'HTTPS' and new_listener['Protocol'] == 'HTTPS':
            modified_listener['SslPolicy'] = new_listener['SslPolicy']
            modified_listener['Certificates'] = []
            modified_listener['Certificates'].append({})
            modified_listener['Certificates'][0]['CertificateArn'] = new_listener['Certificates'][0]['CertificateArn']

        # Default action

        # Check proper rule format on current listener
        if len(current_listener['DefaultActions']) > 1:
            for action in current_listener['DefaultActions']:
                if 'Order' not in action:
                    self.module.fail_json(msg="'Order' key not found in actions. "
                                              "installed version of botocore does not support "
                                              "multiple actions, please upgrade botocore to version "
                                              "1.10.30 or higher")

        # If the lengths of the actions are the same, we'll have to verify that the
        # contents of those actions are the same
        if len(current_listener['DefaultActions']) == len(new_listener['DefaultActions']):
            current_actions_sorted = _sort_actions(current_listener['DefaultActions'])
            new_actions_sorted = _sort_actions(new_listener['DefaultActions'])

            new_actions_sorted_no_secret = [_prune_secret(i) for i in new_actions_sorted]

            if [_prune_ForwardConfig(i) for i in current_actions_sorted] != [_prune_ForwardConfig(i) for i in new_actions_sorted_no_secret]:
                modified_listener['DefaultActions'] = new_listener['DefaultActions']
        # If the action lengths are different, then replace with the new actions
        else:
            modified_listener['DefaultActions'] = new_listener['DefaultActions']

        if modified_listener:
            return modified_listener
        else:
            return None


class ELBListener(object):

    def __init__(self, connection, module, listener, elb_arn):
        """

        :param connection:
        :param module:
        :param listener:
        :param elb_arn:
        """

        self.connection = connection
        self.module = module
        self.listener = listener
        self.elb_arn = elb_arn

    def add(self):

        try:
            # Rules is not a valid parameter for create_listener
            if 'Rules' in self.listener:
                self.listener.pop('Rules')
            AWSRetry.jittered_backoff()(self.connection.create_listener)(LoadBalancerArn=self.elb_arn, **self.listener)
        except (BotoCoreError, ClientError) as e:
            if '"Order", must be one of: Type, TargetGroupArn' in str(e):
                self.module.fail_json(msg="installed version of botocore does not support "
                                          "multiple actions, please upgrade botocore to version "
                                          "1.10.30 or higher")
            else:
                self.module.fail_json_aws(e)

    def modify(self):

        try:
            # Rules is not a valid parameter for modify_listener
            if 'Rules' in self.listener:
                self.listener.pop('Rules')
            AWSRetry.jittered_backoff()(self.connection.modify_listener)(**self.listener)
        except (BotoCoreError, ClientError) as e:
            if '"Order", must be one of: Type, TargetGroupArn' in str(e):
                self.module.fail_json(msg="installed version of botocore does not support "
                                          "multiple actions, please upgrade botocore to version "
                                          "1.10.30 or higher")
            else:
                self.module.fail_json_aws(e)

    def delete(self):

        try:
            AWSRetry.jittered_backoff()(self.connection.delete_listener)(ListenerArn=self.listener)
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e)


class ELBListenerRules(object):

    def __init__(self, connection, module, elb_arn, listener_rules, listener_port):

        self.connection = connection
        self.module = module
        self.elb_arn = elb_arn
        self.rules = self._ensure_rules_action_has_arn(listener_rules)
        self.changed = False

        # Get listener based on port so we can use ARN
        self.current_listener = get_elb_listener(connection, module, elb_arn, listener_port)
        self.listener_arn = self.current_listener['ListenerArn']
        self.rules_to_add = deepcopy(self.rules)
        self.rules_to_modify = []
        self.rules_to_delete = []

        # If the listener exists (i.e. has an ARN) get rules for the listener
        if 'ListenerArn' in self.current_listener:
            self.current_rules = self._get_elb_listener_rules()
        else:
            self.current_rules = []

    def _ensure_rules_action_has_arn(self, rules):
        """
        If a rule Action has been passed with a Target Group Name instead of ARN, lookup the ARN and
        replace the name.

        :param rules: a list of rule dicts
        :return: the same list of dicts ensuring that each rule Actions dict has TargetGroupArn key. If a TargetGroupName key exists, it is removed.
        """

        fixed_rules = []
        for rule in rules:
            fixed_actions = []
            for action in rule['Actions']:
                if 'TargetGroupName' in action:
                    action['TargetGroupArn'] = convert_tg_name_to_arn(self.connection, self.module, action['TargetGroupName'])
                    del action['TargetGroupName']
                fixed_actions.append(action)
            rule['Actions'] = fixed_actions
            fixed_rules.append(rule)

        return fixed_rules

    def _get_elb_listener_rules(self):

        try:
            return AWSRetry.jittered_backoff()(self.connection.describe_rules)(ListenerArn=self.current_listener['ListenerArn'])['Rules']
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e)

    def _compare_condition(self, current_conditions, condition):
        """

        :param current_conditions:
        :param condition:
        :return:
        """

        condition_found = False

        for current_condition in current_conditions:
            # host-header: current_condition includes both HostHeaderConfig AND Values while
            # condition can be defined with either HostHeaderConfig OR Values. Only use
            # HostHeaderConfig['Values'] comparison if both conditions includes HostHeaderConfig.
            if current_condition.get('HostHeaderConfig') and condition.get('HostHeaderConfig'):
                if (current_condition['Field'] == condition['Field'] and
                        sorted(current_condition['HostHeaderConfig']['Values']) == sorted(condition['HostHeaderConfig']['Values'])):
                    condition_found = True
                    break
            elif current_condition.get('HttpHeaderConfig'):
                if (current_condition['Field'] == condition['Field'] and
                        sorted(current_condition['HttpHeaderConfig']['Values']) == sorted(condition['HttpHeaderConfig']['Values']) and
                        current_condition['HttpHeaderConfig']['HttpHeaderName'] == condition['HttpHeaderConfig']['HttpHeaderName']):
                    condition_found = True
                    break
            elif current_condition.get('HttpRequestMethodConfig'):
                if (current_condition['Field'] == condition['Field'] and
                        sorted(current_condition['HttpRequestMethodConfig']['Values']) == sorted(condition['HttpRequestMethodConfig']['Values'])):
                    condition_found = True
                    break
            # path-pattern: current_condition includes both PathPatternConfig AND Values while
            # condition can be defined with either PathPatternConfig OR Values. Only use
            # PathPatternConfig['Values'] comparison if both conditions includes PathPatternConfig.
            elif current_condition.get('PathPatternConfig') and condition.get('PathPatternConfig'):
                if (current_condition['Field'] == condition['Field'] and
                        sorted(current_condition['PathPatternConfig']['Values']) == sorted(condition['PathPatternConfig']['Values'])):
                    condition_found = True
                    break
            elif current_condition.get('QueryStringConfig'):
                # QueryString Values is not sorted as it is the only list of dicts (not strings).
                if (current_condition['Field'] == condition['Field'] and
                        current_condition['QueryStringConfig']['Values'] == condition['QueryStringConfig']['Values']):
                    condition_found = True
                    break
            elif current_condition.get('SourceIpConfig'):
                if (current_condition['Field'] == condition['Field'] and
                        sorted(current_condition['SourceIpConfig']['Values']) == sorted(condition['SourceIpConfig']['Values'])):
                    condition_found = True
                    break
            # Not all fields are required to have Values list nested within a *Config dict
            # e.g. fields host-header/path-pattern can directly list Values
            elif current_condition['Field'] == condition['Field'] and sorted(current_condition['Values']) == sorted(condition['Values']):
                condition_found = True
                break

        return condition_found

    def _compare_rule(self, current_rule, new_rule):
        """

        :return:
        """

        modified_rule = {}

        # Priority
        if int(current_rule['Priority']) != int(new_rule['Priority']):
            modified_rule['Priority'] = new_rule['Priority']

        # Actions

        # Check proper rule format on current listener
        if len(current_rule['Actions']) > 1:
            for action in current_rule['Actions']:
                if 'Order' not in action:
                    self.module.fail_json(msg="'Order' key not found in actions. "
                                              "installed version of botocore does not support "
                                              "multiple actions, please upgrade botocore to version "
                                              "1.10.30 or higher")

        # If the lengths of the actions are the same, we'll have to verify that the
        # contents of those actions are the same
        if len(current_rule['Actions']) == len(new_rule['Actions']):
            # if actions have just one element, compare the contents and then update if
            # they're different
            current_actions_sorted = _sort_actions(current_rule['Actions'])
            new_actions_sorted = _sort_actions(new_rule['Actions'])

            new_actions_sorted_no_secret = [_prune_secret(i) for i in new_actions_sorted]

            if [_prune_ForwardConfig(i) for i in current_actions_sorted] != [_prune_ForwardConfig(i) for i in new_actions_sorted_no_secret]:
                modified_rule['Actions'] = new_rule['Actions']
        # If the action lengths are different, then replace with the new actions
        else:
            modified_rule['Actions'] = new_rule['Actions']

        # Conditions
        modified_conditions = []
        for condition in new_rule['Conditions']:
            if not self._compare_condition(current_rule['Conditions'], condition):
                modified_conditions.append(condition)

        if modified_conditions:
            modified_rule['Conditions'] = modified_conditions

        return modified_rule

    def compare_rules(self):
        """

        :return:
        """

        rules_to_modify = []
        rules_to_delete = []
        rules_to_add = deepcopy(self.rules)

        for current_rule in self.current_rules:
            current_rule_passed_to_module = False
            for new_rule in self.rules[:]:
                if current_rule['Priority'] == str(new_rule['Priority']):
                    current_rule_passed_to_module = True
                    # Remove what we match so that what is left can be marked as 'to be added'
                    rules_to_add.remove(new_rule)
                    modified_rule = self._compare_rule(current_rule, new_rule)
                    if modified_rule:
                        modified_rule['Priority'] = int(current_rule['Priority'])
                        modified_rule['RuleArn'] = current_rule['RuleArn']
                        modified_rule['Actions'] = new_rule['Actions']
                        modified_rule['Conditions'] = new_rule['Conditions']
                        rules_to_modify.append(modified_rule)
                    break

            # If the current rule was not matched against passed rules, mark for removal
            if not current_rule_passed_to_module and not current_rule['IsDefault']:
                rules_to_delete.append(current_rule['RuleArn'])

        return rules_to_add, rules_to_modify, rules_to_delete


class ELBListenerRule(object):

    def __init__(self, connection, module, rule, listener_arn):

        self.connection = connection
        self.module = module
        self.rule = rule
        self.listener_arn = listener_arn
        self.changed = False

    def create(self):
        """
        Create a listener rule

        :return:
        """

        try:
            self.rule['ListenerArn'] = self.listener_arn
            self.rule['Priority'] = int(self.rule['Priority'])
            AWSRetry.jittered_backoff()(self.connection.create_rule)(**self.rule)
        except (BotoCoreError, ClientError) as e:
            if '"Order", must be one of: Type, TargetGroupArn' in str(e):
                self.module.fail_json(msg="installed version of botocore does not support "
                                          "multiple actions, please upgrade botocore to version "
                                          "1.10.30 or higher")
            else:
                self.module.fail_json_aws(e)

        self.changed = True

    def modify(self):
        """
        Modify a listener rule

        :return:
        """

        try:
            del self.rule['Priority']
            AWSRetry.jittered_backoff()(self.connection.modify_rule)(**self.rule)
        except (BotoCoreError, ClientError) as e:
            if '"Order", must be one of: Type, TargetGroupArn' in str(e):
                self.module.fail_json(msg="installed version of botocore does not support "
                                          "multiple actions, please upgrade botocore to version "
                                          "1.10.30 or higher")
            else:
                self.module.fail_json_aws(e)

        self.changed = True

    def delete(self):
        """
        Delete a listener rule

        :return:
        """

        try:
            AWSRetry.jittered_backoff()(self.connection.delete_rule)(RuleArn=self.rule['RuleArn'])
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e)

        self.changed = True
