# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: aws_ec2
    short_description: EC2 inventory source
    extends_documentation_fragment:
    - inventory_cache
    - constructed
    - amazon.aws.aws_boto3
    - amazon.aws.aws_credentials

    description:
        - Get inventory hosts from Amazon Web Services EC2.
        - Uses a YAML configuration file that ends with C(aws_ec2.{yml|yaml}).
    notes:
        - If no credentials are provided and the control node has an associated IAM instance profile then the
          role will be used for authentication.
    author:
        - Sloane Hertel (@s-hertel)
    options:
        plugin:
            description: Token that ensures this is a source file for the plugin.
            required: True
            choices: ['aws_ec2', 'amazon.aws.aws_ec2']
        iam_role_arn:
          description: The ARN of the IAM role to assume to perform the inventory lookup. You should still provide AWS
              credentials with enough privilege to perform the AssumeRole action.
        regions:
          description:
              - A list of regions in which to describe EC2 instances.
              - If empty (the default) default this will include all regions, except possibly restricted ones like us-gov-west-1 and cn-north-1.
          type: list
          elements: str
          default: []
        hostnames:
          description:
              - A list in order of precedence for hostname variables.
          type: list
          elements: dict
          default: []
          suboptions:
            name:
                description:
                    - Name of the host.
                    - Can be one of the options specified in U(http://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html#options).
                    - To use tags as hostnames use the syntax tag:Name=Value to use the hostname Name_Value, or tag:Name to use the value of the Name tag.
                    - If value provided does not exist in the above options, it will be used as a literal string.
                type: str
                required: True
            prefix:
                description:
                    - Prefix to prepend to I(name). Same options as I(name).
                    - If I(prefix) is specified, final hostname will be I(prefix) +  I(separator) + I(name).
                type: str
                default: ''
                required: False
            separator:
                description:
                    - Value to separate I(prefix) and I(name) when I(prefix) is specified.
                type: str
                default: '_'
                required: False
        filters:
          description:
              - A dictionary of filter value pairs.
              - Available filters are listed here U(http://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html#options).
          type: dict
          default: {}
        include_filters:
          description:
              - A list of filters. Any instances matching at least one of the filters are included in the result.
              - Available filters are listed here U(http://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html#options).
              - Every entry in this list triggers a search query. As such, from a performance point of view, it's better to
                keep the list as short as possible.
          type: list
          elements: dict
          default: []
          version_added: 1.5.0
        exclude_filters:
          description:
              - A list of filters. Any instances matching one of the filters are excluded from the result.
              - The filters from C(exclude_filters) take priority over the C(include_filters) and C(filters) keys
              - Available filters are listed here U(http://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html#options).
              - Every entry in this list triggers a search query. As such, from a performance point of view, it's better to
                keep the list as short as possible.
          type: list
          elements: dict
          default: []
          version_added: 1.5.0
        include_extra_api_calls:
          description:
              - Add two additional API calls for every instance to include 'persistent' and 'events' host variables.
              - Spot instances may be persistent and instances may have associated events.
          type: bool
          default: False
        strict_permissions:
          description:
              - By default if a 403 (Forbidden) error code is encountered this plugin will fail.
              - You can set this option to False in the inventory config file which will allow 403 errors to be gracefully skipped.
          type: bool
          default: True
        use_contrib_script_compatible_sanitization:
          description:
            - By default this plugin is using a general group name sanitization to create safe and usable group names for use in Ansible.
              This option allows you to override that, in efforts to allow migration from the old inventory script and
              matches the sanitization of groups when the script's ``replace_dash_in_groups`` option is set to ``False``.
              To replicate behavior of ``replace_dash_in_groups = True`` with constructed groups,
              you will need to replace hyphens with underscores via the regex_replace filter for those entries.
            - For this to work you should also turn off the TRANSFORM_INVALID_GROUP_CHARS setting,
              otherwise the core engine will just use the standard sanitization on top.
            - This is not the default as such names break certain functionality as not all characters are valid Python identifiers
              which group names end up being used as.
          type: bool
          default: False
        use_contrib_script_compatible_ec2_tag_keys:
          description:
            - Expose the host tags with ec2_tag_TAGNAME keys like the old ec2.py inventory script.
            - The use of this feature is discouraged and we advise to migrate to the new ``tags`` structure.
          type: bool
          default: False
          version_added: 1.5.0
        hostvars_prefix:
          description:
            - The prefix for host variables names coming from AWS.
          type: str
          version_added: 3.1.0
        hostvars_suffix:
          description:
            - The suffix for host variables names coming from AWS.
          type: str
          version_added: 3.1.0
'''

EXAMPLES = '''
# Minimal example using environment vars or instance role credentials
# Fetch all hosts in us-east-1, the hostname is the public DNS if it exists, otherwise the private IP address
plugin: aws_ec2
regions:
  - us-east-1

# Example using filters, ignoring permission errors, and specifying the hostname precedence
plugin: aws_ec2
# The values for profile, access key, secret key and token can be hardcoded like:
boto_profile: aws_profile
# or you could use Jinja as:
# boto_profile: "{{ lookup('env', 'AWS_PROFILE') | default('aws_profile', true) }}"
# Populate inventory with instances in these regions
regions:
  - us-east-1
  - us-east-2
filters:
  # All instances with their `Environment` tag set to `dev`
  tag:Environment: dev
  # All dev and QA hosts
  tag:Environment:
    - dev
    - qa
  instance.group-id: sg-xxxxxxxx
# Ignores 403 errors rather than failing
strict_permissions: False
# Note: I(hostnames) sets the inventory_hostname. To modify ansible_host without modifying
# inventory_hostname use compose (see example below).
hostnames:
  - tag:Name=Tag1,Name=Tag2  # Return specific hosts only
  - tag:CustomDNSName
  - dns-name
  - name: 'tag:Name=Tag1,Name=Tag2'
  - name: 'private-ip-address'
    separator: '_'
    prefix: 'tag:Name'
  - name: 'test_literal' # Using literal values for hostname
    separator: '-'       # Hostname will be aws-test_literal
    prefix: 'aws'

# Example using constructed features to create groups and set ansible_host
plugin: aws_ec2
regions:
  - us-east-1
  - us-west-1
# keyed_groups may be used to create custom groups
strict: False
keyed_groups:
  # Add e.g. x86_64 hosts to an arch_x86_64 group
  - prefix: arch
    key: 'architecture'
  # Add hosts to tag_Name_Value groups for each Name/Value tag pair
  - prefix: tag
    key: tags
  # Add hosts to e.g. instance_type_z3_tiny
  - prefix: instance_type
    key: instance_type
  # Create security_groups_sg_abcd1234 group for each SG
  - key: 'security_groups|json_query("[].group_id")'
    prefix: 'security_groups'
  # Create a group for each value of the Application tag
  - key: tags.Application
    separator: ''
  # Create a group per region e.g. aws_region_us_east_2
  - key: placement.region
    prefix: aws_region
  # Create a group (or groups) based on the value of a custom tag "Role" and add them to a metagroup called "project"
  - key: tags['Role']
    prefix: foo
    parent_group: "project"
# Set individual variables with compose
compose:
  # Use the private IP address to connect to the host
  # (note: this does not modify inventory_hostname, which is set via I(hostnames))
  ansible_host: private_ip_address

# Example using include_filters and exclude_filters to compose the inventory.
plugin: aws_ec2
regions:
  - us-east-1
  - us-west-1
include_filters:
- tag:Name:
  - 'my_second_tag'
- tag:Name:
  - 'my_third_tag'
exclude_filters:
- tag:Name:
  - 'my_first_tag'

# Example using groups to assign the running hosts to a group based on vpc_id
plugin: aws_ec2
boto_profile: aws_profile
# Populate inventory with instances in these regions
regions:
  - us-east-2
filters:
  # All instances with their state as `running`
  instance-state-name: running
keyed_groups:
  - prefix: tag
    key: tags
compose:
  ansible_host: public_dns_name
groups:
  libvpc: vpc_id == 'vpc-####'
# Define prefix and suffix for host variables coming from AWS.
plugin: aws_ec2
regions:
  - us-east-1
hostvars_prefix: 'aws_'
hostvars_suffix: '_ec2'
'''

import re

try:
    import boto3
    import botocore
except ImportError:
    pass  # will be captured by imported HAS_BOTO3

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native
from ansible.module_utils._text import to_text
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.plugins.inventory import Cacheable
from ansible.plugins.inventory import Constructable
from ansible.template import Templar

from ansible_collections.amazon.aws.plugins.module_utils.ec2 import HAS_BOTO3
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import camel_dict_to_snake_dict
from ansible_collections.amazon.aws.plugins.module_utils.core import is_boto3_error_code


# The mappings give an array of keys to get from the filter name to the value
# returned by boto3's EC2 describe_instances method.

instance_meta_filter_to_boto_attr = {
    'group-id': ('Groups', 'GroupId'),
    'group-name': ('Groups', 'GroupName'),
    'network-interface.attachment.instance-owner-id': ('OwnerId',),
    'owner-id': ('OwnerId',),
    'requester-id': ('RequesterId',),
    'reservation-id': ('ReservationId',),
}

instance_data_filter_to_boto_attr = {
    'affinity': ('Placement', 'Affinity'),
    'architecture': ('Architecture',),
    'availability-zone': ('Placement', 'AvailabilityZone'),
    'block-device-mapping.attach-time': ('BlockDeviceMappings', 'Ebs', 'AttachTime'),
    'block-device-mapping.delete-on-termination': ('BlockDeviceMappings', 'Ebs', 'DeleteOnTermination'),
    'block-device-mapping.device-name': ('BlockDeviceMappings', 'DeviceName'),
    'block-device-mapping.status': ('BlockDeviceMappings', 'Ebs', 'Status'),
    'block-device-mapping.volume-id': ('BlockDeviceMappings', 'Ebs', 'VolumeId'),
    'client-token': ('ClientToken',),
    'dns-name': ('PublicDnsName',),
    'host-id': ('Placement', 'HostId'),
    'hypervisor': ('Hypervisor',),
    'iam-instance-profile.arn': ('IamInstanceProfile', 'Arn'),
    'image-id': ('ImageId',),
    'instance-id': ('InstanceId',),
    'instance-lifecycle': ('InstanceLifecycle',),
    'instance-state-code': ('State', 'Code'),
    'instance-state-name': ('State', 'Name'),
    'instance-type': ('InstanceType',),
    'instance.group-id': ('SecurityGroups', 'GroupId'),
    'instance.group-name': ('SecurityGroups', 'GroupName'),
    'ip-address': ('PublicIpAddress',),
    'kernel-id': ('KernelId',),
    'key-name': ('KeyName',),
    'launch-index': ('AmiLaunchIndex',),
    'launch-time': ('LaunchTime',),
    'monitoring-state': ('Monitoring', 'State'),
    'network-interface.addresses.private-ip-address': ('NetworkInterfaces', 'PrivateIpAddress'),
    'network-interface.addresses.primary': ('NetworkInterfaces', 'PrivateIpAddresses', 'Primary'),
    'network-interface.addresses.association.public-ip': ('NetworkInterfaces', 'PrivateIpAddresses', 'Association', 'PublicIp'),
    'network-interface.addresses.association.ip-owner-id': ('NetworkInterfaces', 'PrivateIpAddresses', 'Association', 'IpOwnerId'),
    'network-interface.association.public-ip': ('NetworkInterfaces', 'Association', 'PublicIp'),
    'network-interface.association.ip-owner-id': ('NetworkInterfaces', 'Association', 'IpOwnerId'),
    'network-interface.association.allocation-id': ('ElasticGpuAssociations', 'ElasticGpuId'),
    'network-interface.association.association-id': ('ElasticGpuAssociations', 'ElasticGpuAssociationId'),
    'network-interface.attachment.attachment-id': ('NetworkInterfaces', 'Attachment', 'AttachmentId'),
    'network-interface.attachment.instance-id': ('InstanceId',),
    'network-interface.attachment.device-index': ('NetworkInterfaces', 'Attachment', 'DeviceIndex'),
    'network-interface.attachment.status': ('NetworkInterfaces', 'Attachment', 'Status'),
    'network-interface.attachment.attach-time': ('NetworkInterfaces', 'Attachment', 'AttachTime'),
    'network-interface.attachment.delete-on-termination': ('NetworkInterfaces', 'Attachment', 'DeleteOnTermination'),
    'network-interface.availability-zone': ('Placement', 'AvailabilityZone'),
    'network-interface.description': ('NetworkInterfaces', 'Description'),
    'network-interface.group-id': ('NetworkInterfaces', 'Groups', 'GroupId'),
    'network-interface.group-name': ('NetworkInterfaces', 'Groups', 'GroupName'),
    'network-interface.ipv6-addresses.ipv6-address': ('NetworkInterfaces', 'Ipv6Addresses', 'Ipv6Address'),
    'network-interface.mac-address': ('NetworkInterfaces', 'MacAddress'),
    'network-interface.network-interface-id': ('NetworkInterfaces', 'NetworkInterfaceId'),
    'network-interface.owner-id': ('NetworkInterfaces', 'OwnerId'),
    'network-interface.private-dns-name': ('NetworkInterfaces', 'PrivateDnsName'),
    # 'network-interface.requester-id': (),
    'network-interface.requester-managed': ('NetworkInterfaces', 'Association', 'IpOwnerId'),
    'network-interface.status': ('NetworkInterfaces', 'Status'),
    'network-interface.source-dest-check': ('NetworkInterfaces', 'SourceDestCheck'),
    'network-interface.subnet-id': ('NetworkInterfaces', 'SubnetId'),
    'network-interface.vpc-id': ('NetworkInterfaces', 'VpcId'),
    'placement-group-name': ('Placement', 'GroupName'),
    'platform': ('Platform',),
    'private-dns-name': ('PrivateDnsName',),
    'private-ip-address': ('PrivateIpAddress',),
    'product-code': ('ProductCodes', 'ProductCodeId'),
    'product-code.type': ('ProductCodes', 'ProductCodeType'),
    'ramdisk-id': ('RamdiskId',),
    'reason': ('StateTransitionReason',),
    'root-device-name': ('RootDeviceName',),
    'root-device-type': ('RootDeviceType',),
    'source-dest-check': ('SourceDestCheck',),
    'spot-instance-request-id': ('SpotInstanceRequestId',),
    'state-reason-code': ('StateReason', 'Code'),
    'state-reason-message': ('StateReason', 'Message'),
    'subnet-id': ('SubnetId',),
    'tag': ('Tags',),
    'tag-key': ('Tags',),
    'tag-value': ('Tags',),
    'tenancy': ('Placement', 'Tenancy'),
    'virtualization-type': ('VirtualizationType',),
    'vpc-id': ('VpcId',),
}


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):

    NAME = 'amazon.aws.aws_ec2'

    def __init__(self):
        super(InventoryModule, self).__init__()

        self.group_prefix = 'aws_ec2_'

        # credentials
        self.boto_profile = None
        self.aws_secret_access_key = None
        self.aws_access_key_id = None
        self.aws_security_token = None
        self.iam_role_arn = None

    def _compile_values(self, obj, attr):
        '''
            :param obj: A list or dict of instance attributes
            :param attr: A key
            :return The value(s) found via the attr
        '''
        if obj is None:
            return

        temp_obj = []

        if isinstance(obj, list) or isinstance(obj, tuple):
            for each in obj:
                value = self._compile_values(each, attr)
                if value:
                    temp_obj.append(value)
        else:
            temp_obj = obj.get(attr)

        has_indexes = any([isinstance(temp_obj, list), isinstance(temp_obj, tuple)])
        if has_indexes and len(temp_obj) == 1:
            return temp_obj[0]

        return temp_obj

    def _get_boto_attr_chain(self, filter_name, instance):
        '''
            :param filter_name: The filter
            :param instance: instance dict returned by boto3 ec2 describe_instances()
        '''
        allowed_filters = sorted(list(instance_data_filter_to_boto_attr.keys()) + list(instance_meta_filter_to_boto_attr.keys()))

        # If filter not in allow_filters -> use it as a literal string
        if filter_name not in allowed_filters:
            return filter_name

        if filter_name in instance_data_filter_to_boto_attr:
            boto_attr_list = instance_data_filter_to_boto_attr[filter_name]
        else:
            boto_attr_list = instance_meta_filter_to_boto_attr[filter_name]

        instance_value = instance
        for attribute in boto_attr_list:
            instance_value = self._compile_values(instance_value, attribute)
        return instance_value

    def _get_credentials(self):
        '''
            :return A dictionary of boto client credentials
        '''
        boto_params = {}
        for credential in (('aws_access_key_id', self.aws_access_key_id),
                           ('aws_secret_access_key', self.aws_secret_access_key),
                           ('aws_session_token', self.aws_security_token)):
            if credential[1]:
                boto_params[credential[0]] = credential[1]

        return boto_params

    def _get_connection(self, credentials, region='us-east-1'):
        try:
            connection = boto3.session.Session(profile_name=self.boto_profile).client('ec2', region, **credentials)
        except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError) as e:
            if self.boto_profile:
                try:
                    connection = boto3.session.Session(profile_name=self.boto_profile).client('ec2', region)
                except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError) as e:
                    raise AnsibleError("Insufficient credentials found: %s" % to_native(e))
            else:
                raise AnsibleError("Insufficient credentials found: %s" % to_native(e))
        return connection

    def _boto3_assume_role(self, credentials, region=None):
        """
        Assume an IAM role passed by iam_role_arn parameter

        :return: a dict containing the credentials of the assumed role
        """

        iam_role_arn = self.iam_role_arn

        try:
            sts_connection = boto3.session.Session(profile_name=self.boto_profile).client('sts', region, **credentials)
            sts_session = sts_connection.assume_role(RoleArn=iam_role_arn, RoleSessionName='ansible_aws_ec2_dynamic_inventory')
            return dict(
                aws_access_key_id=sts_session['Credentials']['AccessKeyId'],
                aws_secret_access_key=sts_session['Credentials']['SecretAccessKey'],
                aws_session_token=sts_session['Credentials']['SessionToken']
            )
        except botocore.exceptions.ClientError as e:
            raise AnsibleError("Unable to assume IAM role: %s" % to_native(e))

    def _boto3_conn(self, regions):
        '''
            :param regions: A list of regions to create a boto3 client

            Generator that yields a boto3 client and the region
        '''

        credentials = self._get_credentials()
        iam_role_arn = self.iam_role_arn

        if not regions:
            try:
                # as per https://boto3.amazonaws.com/v1/documentation/api/latest/guide/ec2-example-regions-avail-zones.html
                client = self._get_connection(credentials)
                resp = client.describe_regions()
                regions = [x['RegionName'] for x in resp.get('Regions', [])]
            except botocore.exceptions.NoRegionError:
                # above seems to fail depending on boto3 version, ignore and lets try something else
                pass
            except is_boto3_error_code('UnauthorizedOperation') as e:  # pylint: disable=duplicate-except
                if iam_role_arn is not None:
                    try:
                        # Describe regions assuming arn role
                        assumed_credentials = self._boto3_assume_role(credentials)
                        client = self._get_connection(assumed_credentials)
                        resp = client.describe_regions()
                        regions = [x['RegionName'] for x in resp.get('Regions', [])]
                    except botocore.exceptions.NoRegionError:
                        # above seems to fail depending on boto3 version, ignore and lets try something else
                        pass
                else:
                    raise AnsibleError("Unauthorized operation: %s" % to_native(e))

        # fallback to local list hardcoded in boto3 if still no regions
        if not regions:
            session = boto3.Session()
            regions = session.get_available_regions('ec2')

        # I give up, now you MUST give me regions
        if not regions:
            raise AnsibleError('Unable to get regions list from available methods, you must specify the "regions" option to continue.')

        for region in regions:
            connection = self._get_connection(credentials, region)
            try:
                if iam_role_arn is not None:
                    assumed_credentials = self._boto3_assume_role(credentials, region)
                else:
                    assumed_credentials = credentials
                connection = boto3.session.Session(profile_name=self.boto_profile).client('ec2', region, **assumed_credentials)
            except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError) as e:
                if self.boto_profile:
                    try:
                        connection = boto3.session.Session(profile_name=self.boto_profile).client('ec2', region)
                    except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError) as e:
                        raise AnsibleError("Insufficient credentials found: %s" % to_native(e))
                else:
                    raise AnsibleError("Insufficient credentials found: %s" % to_native(e))
            yield connection, region

    def _get_instances_by_region(self, regions, filters, strict_permissions):
        '''
           :param regions: a list of regions in which to describe instances
           :param filters: a list of boto3 filter dictionaries
           :param strict_permissions: a boolean determining whether to fail or ignore 403 error codes
           :return A list of instance dictionaries
        '''
        all_instances = []

        for connection, region in self._boto3_conn(regions):
            try:
                # By default find non-terminated/terminating instances
                if not any(f['Name'] == 'instance-state-name' for f in filters):
                    filters.append({'Name': 'instance-state-name', 'Values': ['running', 'pending', 'stopping', 'stopped']})
                paginator = connection.get_paginator('describe_instances')
                reservations = paginator.paginate(Filters=filters).build_full_result().get('Reservations')
                instances = []
                for r in reservations:
                    new_instances = r['Instances']
                    for instance in new_instances:
                        instance.update(self._get_reservation_details(r))
                        if self.get_option('include_extra_api_calls'):
                            instance.update(self._get_event_set_and_persistence(connection, instance['InstanceId'], instance.get('SpotInstanceRequestId')))
                    instances.extend(new_instances)
            except botocore.exceptions.ClientError as e:
                if e.response['ResponseMetadata']['HTTPStatusCode'] == 403 and not strict_permissions:
                    instances = []
                else:
                    raise AnsibleError("Failed to describe instances: %s" % to_native(e))
            except botocore.exceptions.BotoCoreError as e:
                raise AnsibleError("Failed to describe instances: %s" % to_native(e))

            all_instances.extend(instances)

        return all_instances

    def _get_reservation_details(self, reservation):
        return {
            'OwnerId': reservation['OwnerId'],
            'RequesterId': reservation.get('RequesterId', ''),
            'ReservationId': reservation['ReservationId']
        }

    def _get_event_set_and_persistence(self, connection, instance_id, spot_instance):
        host_vars = {'Events': '', 'Persistent': False}
        try:
            kwargs = {'InstanceIds': [instance_id]}
            host_vars['Events'] = connection.describe_instance_status(**kwargs)['InstanceStatuses'][0].get('Events', '')
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            if not self.get_option('strict_permissions'):
                pass
            else:
                raise AnsibleError("Failed to describe instance status: %s" % to_native(e))
        if spot_instance:
            try:
                kwargs = {'SpotInstanceRequestIds': [spot_instance]}
                host_vars['Persistent'] = bool(
                    connection.describe_spot_instance_requests(**kwargs)['SpotInstanceRequests'][0].get('Type') == 'persistent'
                )
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                if not self.get_option('strict_permissions'):
                    pass
                else:
                    raise AnsibleError("Failed to describe spot instance requests: %s" % to_native(e))
        return host_vars

    def _get_tag_hostname(self, preference, instance):
        tag_hostnames = preference.split('tag:', 1)[1]
        if ',' in tag_hostnames:
            tag_hostnames = tag_hostnames.split(',')
        else:
            tag_hostnames = [tag_hostnames]
        tags = boto3_tag_list_to_ansible_dict(instance.get('Tags', []))
        for v in tag_hostnames:
            if '=' in v:
                tag_name, tag_value = v.split('=')
                if tags.get(tag_name) == tag_value:
                    return to_text(tag_name) + "_" + to_text(tag_value)
            else:
                tag_value = tags.get(v)
                if tag_value:
                    return to_text(tag_value)
        return None

    def _get_hostname(self, instance, hostnames):
        '''
            :param instance: an instance dict returned by boto3 ec2 describe_instances()
            :param hostnames: a list of hostname destination variables in order of preference
            :return the preferred identifer for the host
        '''
        if not hostnames:
            hostnames = ['dns-name', 'private-dns-name']

        hostname = None
        for preference in hostnames:
            if isinstance(preference, dict):
                if 'name' not in preference:
                    raise AnsibleError("A 'name' key must be defined in a hostnames dictionary.")
                hostname = self._get_hostname(instance, [preference["name"]])
                hostname_from_prefix = self._get_hostname(instance, [preference["prefix"]])
                separator = preference.get("separator", "_")
                if hostname and hostname_from_prefix and 'prefix' in preference:
                    hostname = hostname_from_prefix + separator + hostname
            elif preference.startswith('tag:'):
                hostname = self._get_tag_hostname(preference, instance)
            else:
                hostname = self._get_boto_attr_chain(preference, instance)
            if hostname:
                break
        if hostname:
            if ':' in to_text(hostname):
                return self._sanitize_group_name((to_text(hostname)))
            else:
                return to_text(hostname)

    def _query(self, regions, include_filters, exclude_filters, strict_permissions):
        '''
            :param regions: a list of regions to query
            :param include_filters: a list of boto3 filter dictionaries
            :param exclude_filters: a list of boto3 filter dictionaries
            :param strict_permissions: a boolean determining whether to fail or ignore 403 error codes

        '''
        instances = []
        ids_to_ignore = []
        for filter in exclude_filters:
            for i in self._get_instances_by_region(
                    regions,
                    ansible_dict_to_boto3_filter_list(filter),
                    strict_permissions):
                ids_to_ignore.append(i['InstanceId'])
        for filter in include_filters:
            for i in self._get_instances_by_region(
                    regions,
                    ansible_dict_to_boto3_filter_list(filter),
                    strict_permissions):
                if i['InstanceId'] not in ids_to_ignore:
                    instances.append(i)
                    ids_to_ignore.append(i['InstanceId'])

        instances = sorted(instances, key=lambda x: x['InstanceId'])

        return {'aws_ec2': instances}

    def _populate(self, groups, hostnames):
        for group in groups:
            group = self.inventory.add_group(group)
            self._add_hosts(hosts=groups[group], group=group, hostnames=hostnames)
            self.inventory.add_child('all', group)

    def _add_hosts(self, hosts, group, hostnames):
        '''
            :param hosts: a list of hosts to be added to a group
            :param group: the name of the group to which the hosts belong
            :param hostnames: a list of hostname destination variables in order of preference
        '''
        for host in hosts:
            hostname = self._get_hostname(host, hostnames)

            host = camel_dict_to_snake_dict(host, ignore_list=['Tags'])
            host['tags'] = boto3_tag_list_to_ansible_dict(host.get('tags', []))

            if self.get_option('use_contrib_script_compatible_ec2_tag_keys'):
                for k, v in host['tags'].items():
                    host["ec2_tag_%s" % k] = v

            # Allow easier grouping by region
            host['placement']['region'] = host['placement']['availability_zone'][:-1]

            if not hostname:
                continue
            self.inventory.add_host(hostname, group=group)
            hostvars_prefix = self.get_option("hostvars_prefix")
            hostvars_suffix = self.get_option("hostvars_suffix")
            new_vars = dict()
            for hostvar, hostval in host.items():
                if hostvars_prefix:
                    hostvar = hostvars_prefix + hostvar
                if hostvars_suffix:
                    hostvar = hostvar + hostvars_suffix
                new_vars[hostvar] = hostval
                self.inventory.set_variable(hostname, hostvar, hostval)
            host.update(new_vars)

            # Use constructed if applicable

            strict = self.get_option('strict')

            # Composed variables
            self._set_composite_vars(self.get_option('compose'), host, hostname, strict=strict)

            # Complex groups based on jinja2 conditionals, hosts that meet the conditional are added to group
            self._add_host_to_composed_groups(self.get_option('groups'), host, hostname, strict=strict)

            # Create groups based on variable values and add the corresponding hosts to it
            self._add_host_to_keyed_groups(self.get_option('keyed_groups'), host, hostname, strict=strict)

    def _set_credentials(self, loader):
        '''
            :param config_data: contents of the inventory config file
        '''

        t = Templar(loader=loader)
        credentials = {}

        for credential_type in ['aws_profile', 'aws_access_key', 'aws_secret_key', 'aws_security_token', 'iam_role_arn']:
            if t.is_template(self.get_option(credential_type)):
                credentials[credential_type] = t.template(variable=self.get_option(credential_type), disable_lookups=False)
            else:
                credentials[credential_type] = self.get_option(credential_type)

        self.boto_profile = credentials['aws_profile']
        self.aws_access_key_id = credentials['aws_access_key']
        self.aws_secret_access_key = credentials['aws_secret_key']
        self.aws_security_token = credentials['aws_security_token']
        self.iam_role_arn = credentials['iam_role_arn']

        if not self.boto_profile and not (self.aws_access_key_id and self.aws_secret_access_key):
            session = botocore.session.get_session()
            try:
                credentials = session.get_credentials().get_frozen_credentials()
            except AttributeError:
                pass
            else:
                self.aws_access_key_id = credentials.access_key
                self.aws_secret_access_key = credentials.secret_key
                self.aws_security_token = credentials.token

        if not self.boto_profile and not (self.aws_access_key_id and self.aws_secret_access_key):
            raise AnsibleError("Insufficient boto credentials found. Please provide them in your "
                               "inventory configuration file or set them as environment variables.")

    def verify_file(self, path):
        '''
            :param loader: an ansible.parsing.dataloader.DataLoader object
            :param path: the path to the inventory config file
            :return the contents of the config file
        '''
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('aws_ec2.yml', 'aws_ec2.yaml')):
                return True
        self.display.debug("aws_ec2 inventory filename must end with 'aws_ec2.yml' or 'aws_ec2.yaml'")
        return False

    def build_include_filters(self):
        if self.get_option('filters'):
            return [self.get_option('filters')] + self.get_option('include_filters')
        elif self.get_option('include_filters'):
            return self.get_option('include_filters')
        else:  # no filter
            return [{}]

    def parse(self, inventory, loader, path, cache=True):

        super(InventoryModule, self).parse(inventory, loader, path)

        if not HAS_BOTO3:
            raise AnsibleError('The ec2 dynamic inventory plugin requires boto3 and botocore.')

        self._read_config_data(path)

        if self.get_option('use_contrib_script_compatible_sanitization'):
            self._sanitize_group_name = self._legacy_script_compatible_group_sanitization

        self._set_credentials(loader)

        # get user specifications
        regions = self.get_option('regions')
        include_filters = self.build_include_filters()
        exclude_filters = self.get_option('exclude_filters')
        hostnames = self.get_option('hostnames')
        strict_permissions = self.get_option('strict_permissions')

        cache_key = self.get_cache_key(path)
        # false when refresh_cache or --flush-cache is used
        if cache:
            # get the user-specified directive
            cache = self.get_option('cache')

        # Generate inventory
        cache_needs_update = False
        if cache:
            try:
                results = self._cache[cache_key]
            except KeyError:
                # if cache expires or cache file doesn't exist
                cache_needs_update = True

        if not cache or cache_needs_update:
            results = self._query(regions, include_filters, exclude_filters, strict_permissions)

        self._populate(results, hostnames)

        # If the cache has expired/doesn't exist or if refresh_inventory/flush cache is used
        # when the user is using caching, update the cached inventory
        if cache_needs_update or (not cache and self.get_option('cache')):
            self._cache[cache_key] = results

    @staticmethod
    def _legacy_script_compatible_group_sanitization(name):

        # note that while this mirrors what the script used to do, it has many issues with unicode and usability in python
        regex = re.compile(r"[^A-Za-z0-9\_\-]")

        return regex.sub('_', name)
