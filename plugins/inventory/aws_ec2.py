# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
name: aws_ec2
short_description: EC2 inventory source
extends_documentation_fragment:
  - inventory_cache
  - constructed
  - amazon.aws.boto3
  - amazon.aws.common.plugins
  - amazon.aws.region.plugins
  - amazon.aws.assume_role.plugins
description:
  - Get inventory hosts from Amazon Web Services EC2.
  - "The inventory file is a YAML configuration file and must end with C(aws_ec2.{yml|yaml}). Example: C(my_inventory.aws_ec2.yml)."
notes:
  - If no credentials are provided and the control node has an associated IAM instance profile then the
    role will be used for authentication.
author:
  - Sloane Hertel (@s-hertel)
options:
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
  allow_duplicated_hosts:
    description:
      - By default, the first name that matches an entry of the I(hostnames) list is returned.
      - Turn this flag on if you don't mind having duplicated entries in the inventory
        and you want to get all the hostnames that match.
    type: bool
    default: False
    version_added: 5.0.0
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
      - The I(include_extra_api_calls) option had been deprecated and will be removed in release 6.0.0.
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
  use_ssm_inventory:
    description:
      - Add SSM inventory information into hostvars.
    type: bool
    default: False
    version_added: 6.0.0
"""

EXAMPLES = r"""
# Minimal example using environment vars or instance role credentials
# Fetch all hosts in us-east-1, the hostname is the public DNS if it exists, otherwise the private IP address
plugin: amazon.aws.aws_ec2
regions:
  - us-east-1

# Example using filters, ignoring permission errors, and specifying the hostname precedence
plugin: amazon.aws.aws_ec2
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

# Returns all the hostnames for a given instance
allow_duplicated_hosts: False

# Example using constructed features to create groups and set ansible_host
plugin: amazon.aws.aws_ec2
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
plugin: amazon.aws.aws_ec2
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
plugin: amazon.aws.aws_ec2
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
plugin: amazon.aws.aws_ec2
regions:
  - us-east-1
hostvars_prefix: 'aws_'
hostvars_suffix: '_ec2'
"""

import re

try:
    import botocore
except ImportError:
    pass  # will be captured by imported HAS_BOTO3

from ansible.module_utils._text import to_text
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict


from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.transformation import ansible_dict_to_boto3_filter_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.plugin_utils.inventory import AWSInventoryBase


# The mappings give an array of keys to get from the filter name to the value
# returned by boto3's EC2 describe_instances method.

instance_meta_filter_to_boto_attr = {
    "group-id": ("Groups", "GroupId"),
    "group-name": ("Groups", "GroupName"),
    "network-interface.attachment.instance-owner-id": ("OwnerId",),
    "owner-id": ("OwnerId",),
    "requester-id": ("RequesterId",),
    "reservation-id": ("ReservationId",),
}

instance_data_filter_to_boto_attr = {
    "affinity": ("Placement", "Affinity"),
    "architecture": ("Architecture",),
    "availability-zone": ("Placement", "AvailabilityZone"),
    "block-device-mapping.attach-time": ("BlockDeviceMappings", "Ebs", "AttachTime"),
    "block-device-mapping.delete-on-termination": ("BlockDeviceMappings", "Ebs", "DeleteOnTermination"),
    "block-device-mapping.device-name": ("BlockDeviceMappings", "DeviceName"),
    "block-device-mapping.status": ("BlockDeviceMappings", "Ebs", "Status"),
    "block-device-mapping.volume-id": ("BlockDeviceMappings", "Ebs", "VolumeId"),
    "client-token": ("ClientToken",),
    "dns-name": ("PublicDnsName",),
    "host-id": ("Placement", "HostId"),
    "hypervisor": ("Hypervisor",),
    "iam-instance-profile.arn": ("IamInstanceProfile", "Arn"),
    "image-id": ("ImageId",),
    "instance-id": ("InstanceId",),
    "instance-lifecycle": ("InstanceLifecycle",),
    "instance-state-code": ("State", "Code"),
    "instance-state-name": ("State", "Name"),
    "instance-type": ("InstanceType",),
    "instance.group-id": ("SecurityGroups", "GroupId"),
    "instance.group-name": ("SecurityGroups", "GroupName"),
    "ip-address": ("PublicIpAddress",),
    "kernel-id": ("KernelId",),
    "key-name": ("KeyName",),
    "launch-index": ("AmiLaunchIndex",),
    "launch-time": ("LaunchTime",),
    "monitoring-state": ("Monitoring", "State"),
    "network-interface.addresses.private-ip-address": ("NetworkInterfaces", "PrivateIpAddress"),
    "network-interface.addresses.primary": ("NetworkInterfaces", "PrivateIpAddresses", "Primary"),
    "network-interface.addresses.association.public-ip": (
        "NetworkInterfaces",
        "PrivateIpAddresses",
        "Association",
        "PublicIp",
    ),
    "network-interface.addresses.association.ip-owner-id": (
        "NetworkInterfaces",
        "PrivateIpAddresses",
        "Association",
        "IpOwnerId",
    ),
    "network-interface.association.public-ip": ("NetworkInterfaces", "Association", "PublicIp"),
    "network-interface.association.ip-owner-id": ("NetworkInterfaces", "Association", "IpOwnerId"),
    "network-interface.association.allocation-id": ("ElasticGpuAssociations", "ElasticGpuId"),
    "network-interface.association.association-id": ("ElasticGpuAssociations", "ElasticGpuAssociationId"),
    "network-interface.attachment.attachment-id": ("NetworkInterfaces", "Attachment", "AttachmentId"),
    "network-interface.attachment.instance-id": ("InstanceId",),
    "network-interface.attachment.device-index": ("NetworkInterfaces", "Attachment", "DeviceIndex"),
    "network-interface.attachment.status": ("NetworkInterfaces", "Attachment", "Status"),
    "network-interface.attachment.attach-time": ("NetworkInterfaces", "Attachment", "AttachTime"),
    "network-interface.attachment.delete-on-termination": ("NetworkInterfaces", "Attachment", "DeleteOnTermination"),
    "network-interface.availability-zone": ("Placement", "AvailabilityZone"),
    "network-interface.description": ("NetworkInterfaces", "Description"),
    "network-interface.group-id": ("NetworkInterfaces", "Groups", "GroupId"),
    "network-interface.group-name": ("NetworkInterfaces", "Groups", "GroupName"),
    "network-interface.ipv6-addresses.ipv6-address": ("NetworkInterfaces", "Ipv6Addresses", "Ipv6Address"),
    "network-interface.mac-address": ("NetworkInterfaces", "MacAddress"),
    "network-interface.network-interface-id": ("NetworkInterfaces", "NetworkInterfaceId"),
    "network-interface.owner-id": ("NetworkInterfaces", "OwnerId"),
    "network-interface.private-dns-name": ("NetworkInterfaces", "PrivateDnsName"),
    # 'network-interface.requester-id': (),
    "network-interface.requester-managed": ("NetworkInterfaces", "Association", "IpOwnerId"),
    "network-interface.status": ("NetworkInterfaces", "Status"),
    "network-interface.source-dest-check": ("NetworkInterfaces", "SourceDestCheck"),
    "network-interface.subnet-id": ("NetworkInterfaces", "SubnetId"),
    "network-interface.vpc-id": ("NetworkInterfaces", "VpcId"),
    "placement-group-name": ("Placement", "GroupName"),
    "platform": ("Platform",),
    "private-dns-name": ("PrivateDnsName",),
    "private-ip-address": ("PrivateIpAddress",),
    "product-code": ("ProductCodes", "ProductCodeId"),
    "product-code.type": ("ProductCodes", "ProductCodeType"),
    "ramdisk-id": ("RamdiskId",),
    "reason": ("StateTransitionReason",),
    "root-device-name": ("RootDeviceName",),
    "root-device-type": ("RootDeviceType",),
    "source-dest-check": ("SourceDestCheck",),
    "spot-instance-request-id": ("SpotInstanceRequestId",),
    "state-reason-code": ("StateReason", "Code"),
    "state-reason-message": ("StateReason", "Message"),
    "subnet-id": ("SubnetId",),
    "tag": ("Tags",),
    "tag-key": ("Tags",),
    "tag-value": ("Tags",),
    "tenancy": ("Placement", "Tenancy"),
    "virtualization-type": ("VirtualizationType",),
    "vpc-id": ("VpcId",),
}


def _get_tag_hostname(preference, instance):
    tag_hostnames = preference.split("tag:", 1)[1]
    if "," in tag_hostnames:
        tag_hostnames = tag_hostnames.split(",")
    else:
        tag_hostnames = [tag_hostnames]

    tags = boto3_tag_list_to_ansible_dict(instance.get("Tags", []))
    tag_values = []
    for v in tag_hostnames:
        if "=" in v:
            tag_name, tag_value = v.split("=")
            if tags.get(tag_name) == tag_value:
                tag_values.append(to_text(tag_name) + "_" + to_text(tag_value))
        else:
            tag_value = tags.get(v)
            if tag_value:
                tag_values.append(to_text(tag_value))
    return tag_values


def _prepare_host_vars(
    original_host_vars,
    hostvars_prefix=None,
    hostvars_suffix=None,
    use_contrib_script_compatible_ec2_tag_keys=False,
):
    host_vars = camel_dict_to_snake_dict(original_host_vars, ignore_list=["Tags"])
    host_vars["tags"] = boto3_tag_list_to_ansible_dict(original_host_vars.get("Tags", []))

    # Allow easier grouping by region
    host_vars["placement"]["region"] = host_vars["placement"]["availability_zone"][:-1]

    if use_contrib_script_compatible_ec2_tag_keys:
        for k, v in host_vars["tags"].items():
            host_vars[f"ec2_tag_{k}"] = v

    if hostvars_prefix or hostvars_suffix:
        for hostvar, hostval in host_vars.copy().items():
            del host_vars[hostvar]
            if hostvars_prefix:
                hostvar = hostvars_prefix + hostvar
            if hostvars_suffix:
                hostvar = hostvar + hostvars_suffix
            host_vars[hostvar] = hostval

    return host_vars


def _compile_values(obj, attr):
    """
    :param obj: A list or dict of instance attributes
    :param attr: A key
    :return The value(s) found via the attr
    """
    if obj is None:
        return

    temp_obj = []

    if isinstance(obj, list) or isinstance(obj, tuple):
        for each in obj:
            value = _compile_values(each, attr)
            if value:
                temp_obj.append(value)
    else:
        temp_obj = obj.get(attr)

    has_indexes = any([isinstance(temp_obj, list), isinstance(temp_obj, tuple)])
    if has_indexes and len(temp_obj) == 1:
        return temp_obj[0]

    return temp_obj


def _get_boto_attr_chain(filter_name, instance):
    """
    :param filter_name: The filter
    :param instance: instance dict returned by boto3 ec2 describe_instances()
    """
    allowed_filters = sorted(
        list(instance_data_filter_to_boto_attr.keys()) + list(instance_meta_filter_to_boto_attr.keys())
    )

    # If filter not in allow_filters -> use it as a literal string
    if filter_name not in allowed_filters:
        return filter_name

    if filter_name in instance_data_filter_to_boto_attr:
        boto_attr_list = instance_data_filter_to_boto_attr[filter_name]
    else:
        boto_attr_list = instance_meta_filter_to_boto_attr[filter_name]

    instance_value = instance
    for attribute in boto_attr_list:
        instance_value = _compile_values(instance_value, attribute)
    return instance_value


def _describe_ec2_instances(connection, filters):
    paginator = connection.get_paginator("describe_instances")
    return paginator.paginate(Filters=filters).build_full_result()


def _get_ssm_information(client, filters):
    paginator = client.get_paginator("get_inventory")
    return paginator.paginate(Filters=filters).build_full_result()


class InventoryModule(AWSInventoryBase):
    NAME = "amazon.aws.aws_ec2"
    INVENTORY_FILE_SUFFIXES = ("aws_ec2.yml", "aws_ec2.yaml")

    def __init__(self):
        super().__init__()

        self.group_prefix = "aws_ec2_"

    def _get_instances_by_region(self, regions, filters, strict_permissions):
        """
        :param regions: a list of regions in which to describe instances
        :param filters: a list of boto3 filter dictionaries
        :param strict_permissions: a boolean determining whether to fail or ignore 403 error codes
        :return A list of instance dictionaries
        """
        all_instances = []
        # By default find non-terminated/terminating instances
        if not any(f["Name"] == "instance-state-name" for f in filters):
            filters.append({"Name": "instance-state-name", "Values": ["running", "pending", "stopping", "stopped"]})

        for connection, _region in self.all_clients("ec2"):
            try:
                reservations = _describe_ec2_instances(connection, filters).get("Reservations")
                instances = []
                for r in reservations:
                    new_instances = r["Instances"]
                    reservation_details = {
                        "OwnerId": r["OwnerId"],
                        "RequesterId": r.get("RequesterId", ""),
                        "ReservationId": r["ReservationId"],
                    }
                    for instance in new_instances:
                        instance.update(reservation_details)
                    instances.extend(new_instances)
            except is_boto3_error_code("UnauthorizedOperation") as e:
                if not strict_permissions:
                    continue
                self.fail_aws("Failed to describe instances", exception=e)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                self.fail_aws("Failed to describe instances", exception=e)

            all_instances.extend(instances)

        return all_instances

    def _sanitize_hostname(self, hostname):
        if ":" in to_text(hostname):
            return self._sanitize_group_name(to_text(hostname))
        else:
            return to_text(hostname)

    def _get_preferred_hostname(self, instance, hostnames):
        """
        :param instance: an instance dict returned by boto3 ec2 describe_instances()
        :param hostnames: a list of hostname destination variables in order of preference
        :return the preferred identifer for the host
        """
        if not hostnames:
            hostnames = ["dns-name", "private-dns-name"]

        hostname = None
        for preference in hostnames:
            if isinstance(preference, dict):
                if "name" not in preference:
                    self.fail_aws("A 'name' key must be defined in a hostnames dictionary.")
                hostname = self._get_preferred_hostname(instance, [preference["name"]])
                hostname_from_prefix = None
                if "prefix" in preference:
                    hostname_from_prefix = self._get_preferred_hostname(instance, [preference["prefix"]])
                separator = preference.get("separator", "_")
                if hostname and hostname_from_prefix and "prefix" in preference:
                    hostname = hostname_from_prefix + separator + hostname
            elif preference.startswith("tag:"):
                tags = _get_tag_hostname(preference, instance)
                hostname = tags[0] if tags else None
            else:
                hostname = _get_boto_attr_chain(preference, instance)
            if hostname:
                break
        if hostname:
            return self._sanitize_hostname(hostname)

    def _get_all_hostnames(self, instance, hostnames):
        """
        :param instance: an instance dict returned by boto3 ec2 describe_instances()
        :param hostnames: a list of hostname destination variables
        :return all the candidats matching the expectation
        """
        if not hostnames:
            hostnames = ["dns-name", "private-dns-name"]

        hostname = None
        hostname_list = []
        for preference in hostnames:
            if isinstance(preference, dict):
                if "name" not in preference:
                    self.fail_aws("A 'name' key must be defined in a hostnames dictionary.")
                hostname = self._get_all_hostnames(instance, [preference["name"]])
                hostname_from_prefix = None
                if "prefix" in preference:
                    hostname_from_prefix = self._get_all_hostnames(instance, [preference["prefix"]])
                separator = preference.get("separator", "_")
                if hostname and hostname_from_prefix and "prefix" in preference:
                    hostname = hostname_from_prefix[0] + separator + hostname[0]
            elif preference.startswith("tag:"):
                hostname = _get_tag_hostname(preference, instance)
            else:
                hostname = _get_boto_attr_chain(preference, instance)

            if hostname:
                if isinstance(hostname, list):
                    for host in hostname:
                        hostname_list.append(self._sanitize_hostname(host))
                elif isinstance(hostname, str):
                    hostname_list.append(self._sanitize_hostname(hostname))

        return hostname_list

    def _query(self, regions, include_filters, exclude_filters, strict_permissions, use_ssm_inventory):
        """
        :param regions: a list of regions to query
        :param include_filters: a list of boto3 filter dictionaries
        :param exclude_filters: a list of boto3 filter dictionaries
        :param strict_permissions: a boolean determining whether to fail or ignore 403 error codes

        """
        instances = []
        ids_to_ignore = []
        for filter in exclude_filters:
            for i in self._get_instances_by_region(
                regions,
                ansible_dict_to_boto3_filter_list(filter),
                strict_permissions,
            ):
                ids_to_ignore.append(i["InstanceId"])
        for filter in include_filters:
            for i in self._get_instances_by_region(
                regions,
                ansible_dict_to_boto3_filter_list(filter),
                strict_permissions,
            ):
                if i["InstanceId"] not in ids_to_ignore:
                    instances.append(i)
                    ids_to_ignore.append(i["InstanceId"])

        instances = sorted(instances, key=lambda x: x["InstanceId"])

        if use_ssm_inventory and instances:
            for connection, _region in self.all_clients("ssm"):
                self._add_ssm_information(connection, instances)

        return {"aws_ec2": instances}

    def _add_ssm_information(self, connection, instances):
        filters = [{"Key": "AWS:InstanceInformation.InstanceId", "Values": [x["InstanceId"] for x in instances]}]
        result = _get_ssm_information(connection, filters)
        for entity in result.get("Entities", []):
            for x in instances:
                if x["InstanceId"] == entity["Id"]:
                    content = entity.get("Data", {}).get("AWS:InstanceInformation", {}).get("Content", [])
                    if content:
                        x["SsmInventory"] = content[0]
                    break

    def _populate(
        self,
        groups,
        hostnames,
        allow_duplicated_hosts=False,
        hostvars_prefix=None,
        hostvars_suffix=None,
        use_contrib_script_compatible_ec2_tag_keys=False,
    ):
        for group in groups:
            group = self.inventory.add_group(group)
            self._add_hosts(
                hosts=groups[group],
                group=group,
                hostnames=hostnames,
                allow_duplicated_hosts=allow_duplicated_hosts,
                hostvars_prefix=hostvars_prefix,
                hostvars_suffix=hostvars_suffix,
                use_contrib_script_compatible_ec2_tag_keys=use_contrib_script_compatible_ec2_tag_keys,
            )
            self.inventory.add_child("all", group)

    def iter_entry(
        self,
        hosts,
        hostnames,
        allow_duplicated_hosts=False,
        hostvars_prefix=None,
        hostvars_suffix=None,
        use_contrib_script_compatible_ec2_tag_keys=False,
    ):
        for host in hosts:
            if allow_duplicated_hosts:
                hostname_list = self._get_all_hostnames(host, hostnames)
            else:
                hostname_list = [self._get_preferred_hostname(host, hostnames)]
            if not hostname_list or hostname_list[0] is None:
                continue

            host_vars = _prepare_host_vars(
                host,
                hostvars_prefix,
                hostvars_suffix,
                use_contrib_script_compatible_ec2_tag_keys,
            )
            for name in hostname_list:
                yield to_text(name), host_vars

    def _add_hosts(
        self,
        hosts,
        group,
        hostnames,
        allow_duplicated_hosts=False,
        hostvars_prefix=None,
        hostvars_suffix=None,
        use_contrib_script_compatible_ec2_tag_keys=False,
    ):
        """
        :param hosts: a list of hosts to be added to a group
        :param group: the name of the group to which the hosts belong
        :param hostnames: a list of hostname destination variables in order of preference
        :param bool allow_duplicated_hosts: if true, accept same host with different names
        :param str hostvars_prefix: starts the hostvars variable name with this prefix
        :param str hostvars_suffix: ends the hostvars variable name with this suffix
        :param bool use_contrib_script_compatible_ec2_tag_keys: transform the host name with the legacy naming system
        """

        for name, host_vars in self.iter_entry(
            hosts,
            hostnames,
            allow_duplicated_hosts=allow_duplicated_hosts,
            hostvars_prefix=hostvars_prefix,
            hostvars_suffix=hostvars_suffix,
            use_contrib_script_compatible_ec2_tag_keys=use_contrib_script_compatible_ec2_tag_keys,
        ):
            self.inventory.add_host(name, group=group)
            for k, v in host_vars.items():
                self.inventory.set_variable(name, k, v)

            # Use constructed if applicable

            strict = self.get_option("strict")

            # Composed variables
            self._set_composite_vars(self.get_option("compose"), host_vars, name, strict=strict)

            # Complex groups based on jinja2 conditionals, hosts that meet the conditional are added to group
            self._add_host_to_composed_groups(self.get_option("groups"), host_vars, name, strict=strict)

            # Create groups based on variable values and add the corresponding hosts to it
            self._add_host_to_keyed_groups(self.get_option("keyed_groups"), host_vars, name, strict=strict)

    def build_include_filters(self):
        result = self.get_option("include_filters")
        if self.get_option("filters"):
            result = [self.get_option("filters")] + result
        return result or [{}]

    def parse(self, inventory, loader, path, cache=True):
        super().parse(inventory, loader, path, cache=cache)

        if self.get_option("use_contrib_script_compatible_sanitization"):
            self._sanitize_group_name = self._legacy_script_compatible_group_sanitization

        # get user specifications
        regions = self.get_option("regions")
        include_filters = self.build_include_filters()
        exclude_filters = self.get_option("exclude_filters")
        hostnames = self.get_option("hostnames")
        strict_permissions = self.get_option("strict_permissions")
        allow_duplicated_hosts = self.get_option("allow_duplicated_hosts")

        hostvars_prefix = self.get_option("hostvars_prefix")
        hostvars_suffix = self.get_option("hostvars_suffix")
        use_contrib_script_compatible_ec2_tag_keys = self.get_option("use_contrib_script_compatible_ec2_tag_keys")
        use_ssm_inventory = self.get_option("use_ssm_inventory")

        if self.get_option("include_extra_api_calls"):
            self.display.deprecate(
                "The include_extra_api_calls option has been deprecated and will be removed in release 6.0.0.",
                date="2024-09-01",
                collection_name="amazon.aws",
            )

        result_was_cached, results = self.get_cached_result(path, cache)

        if not result_was_cached:
            results = self._query(regions, include_filters, exclude_filters, strict_permissions, use_ssm_inventory)

        self._populate(
            results,
            hostnames,
            allow_duplicated_hosts=allow_duplicated_hosts,
            hostvars_prefix=hostvars_prefix,
            hostvars_suffix=hostvars_suffix,
            use_contrib_script_compatible_ec2_tag_keys=use_contrib_script_compatible_ec2_tag_keys,
        )

        self.update_cached_result(path, cache, results)

    @staticmethod
    def _legacy_script_compatible_group_sanitization(name):
        # note that while this mirrors what the script used to do, it has many issues with unicode and usability in python
        regex = re.compile(r"[^A-Za-z0-9\_\-]")

        return regex.sub("_", name)
