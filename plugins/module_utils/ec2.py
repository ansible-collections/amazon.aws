# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


"""
This module adds helper functions for various EC2 specific services.

It also includes a large number of imports for functions which historically
lived here.  Most of these functions were not specific to EC2, they ended
up in this module because "that's where the AWS code was" (originally).
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re

from ansible.module_utils.ansible_release import __version__
from ansible.module_utils.six import string_types
from ansible.module_utils.six import integer_types
# Used to live here, moved into ansible.module_utils.common.dict_transformations
from ansible.module_utils.common.dict_transformations import _camel_to_snake  # pylint: disable=unused-import
from ansible.module_utils.common.dict_transformations import _snake_to_camel  # pylint: disable=unused-import
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict  # pylint: disable=unused-import
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict  # pylint: disable=unused-import

# Used to live here, moved into # ansible_collections.amazon.aws.plugins.module_utils.arn
from .arn import is_outpost_arn as is_outposts_arn  # pylint: disable=unused-import

# Used to live here, moved into ansible_collections.amazon.aws.plugins.module_utils.botocore
from .botocore import HAS_BOTO3  # pylint: disable=unused-import
from .botocore import boto3_conn  # pylint: disable=unused-import
from .botocore import boto3_inventory_conn  # pylint: disable=unused-import
from .botocore import boto_exception  # pylint: disable=unused-import
from .botocore import get_aws_region  # pylint: disable=unused-import
from .botocore import get_aws_connection_info  # pylint: disable=unused-import

from .botocore import paginated_query_with_retries

# Used to live here, moved into ansible_collections.amazon.aws.plugins.module_utils.botocore
from .core import AnsibleAWSError  # pylint: disable=unused-import

# Used to live here, moved into ansible_collections.amazon.aws.plugins.module_utils.modules
# The names have been changed in .modules to better reflect their applicability.
from .modules import _aws_common_argument_spec as aws_common_argument_spec  # pylint: disable=unused-import
from .modules import aws_argument_spec as ec2_argument_spec  # pylint: disable=unused-import

# Used to live here, moved into ansible_collections.amazon.aws.plugins.module_utils.tagging
from .tagging import ansible_dict_to_boto3_tag_list  # pylint: disable=unused-import
from .tagging import boto3_tag_list_to_ansible_dict  # pylint: disable=unused-import
from .tagging import compare_aws_tags  # pylint: disable=unused-import

# Used to live here, moved into ansible_collections.amazon.aws.plugins.module_utils.transformation
from .transformation import ansible_dict_to_boto3_filter_list  # pylint: disable=unused-import
from .transformation import map_complex_type  # pylint: disable=unused-import

# Used to live here, moved into # ansible_collections.amazon.aws.plugins.module_utils.policy
from .policy import _py3cmp as py3cmp  # pylint: disable=unused-import
from .policy import compare_policies  # pylint: disable=unused-import
from .policy import sort_json_policy_dict  # pylint: disable=unused-import

# Used to live here, moved into # ansible_collections.amazon.aws.plugins.module_utils.retries
from .retries import AWSRetry  # pylint: disable=unused-import

try:
    import botocore
except ImportError:
    pass  # Handled by HAS_BOTO3


def get_ec2_security_group_ids_from_names(sec_group_list, ec2_connection, vpc_id=None, boto3=None):

    """ Return list of security group IDs from security group names. Note that security group names are not unique
     across VPCs.  If a name exists across multiple VPCs and no VPC ID is supplied, all matching IDs will be returned. This
     will probably lead to a boto exception if you attempt to assign both IDs to a resource so ensure you wrap the call in
     a try block
     """

    def get_sg_name(sg, boto3=None):
        return str(sg['GroupName'])

    def get_sg_id(sg, boto3=None):
        return str(sg['GroupId'])

    sec_group_id_list = []

    if isinstance(sec_group_list, string_types):
        sec_group_list = [sec_group_list]

    # Get all security groups
    if vpc_id:
        filters = [
            {
                'Name': 'vpc-id',
                'Values': [
                    vpc_id,
                ]
            }
        ]
        all_sec_groups = ec2_connection.describe_security_groups(Filters=filters)['SecurityGroups']
    else:
        all_sec_groups = ec2_connection.describe_security_groups()['SecurityGroups']

    unmatched = set(sec_group_list).difference(str(get_sg_name(all_sg, boto3)) for all_sg in all_sec_groups)
    sec_group_name_list = list(set(sec_group_list) - set(unmatched))

    if len(unmatched) > 0:
        # If we have unmatched names that look like an ID, assume they are
        sec_group_id_list[:] = [sg for sg in unmatched if re.match('sg-[a-fA-F0-9]+$', sg)]
        still_unmatched = [sg for sg in unmatched if not re.match('sg-[a-fA-F0-9]+$', sg)]
        if len(still_unmatched) > 0:
            raise ValueError("The following group names are not valid: %s" % ', '.join(still_unmatched))

    sec_group_id_list += [get_sg_id(all_sg) for all_sg in all_sec_groups if get_sg_name(all_sg) in sec_group_name_list]

    return sec_group_id_list


def add_ec2_tags(client, module, resource_id, tags_to_set, retry_codes=None):
    """
    Sets Tags on an EC2 resource.

    :param client: an EC2 boto3 client
    :param module: an AnsibleAWSModule object
    :param resource_id: the identifier for the resource
    :param tags_to_set: A dictionary of key/value pairs to set
    :param retry_codes: additional boto3 error codes to trigger retries
    """

    if not tags_to_set:
        return False
    if module.check_mode:
        return True

    if not retry_codes:
        retry_codes = []

    try:
        tags_to_add = ansible_dict_to_boto3_tag_list(tags_to_set)
        AWSRetry.jittered_backoff(retries=10, catch_extra_error_codes=retry_codes)(
            client.create_tags
        )(
            Resources=[resource_id], Tags=tags_to_add
        )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Unable to add tags {0} to {1}".format(tags_to_set, resource_id))
    return True


def remove_ec2_tags(client, module, resource_id, tags_to_unset, retry_codes=None):
    """
    Removes Tags from an EC2 resource.

    :param client: an EC2 boto3 client
    :param module: an AnsibleAWSModule object
    :param resource_id: the identifier for the resource
    :param tags_to_unset: a list of tag keys to removes
    :param retry_codes: additional boto3 error codes to trigger retries
    """

    if not tags_to_unset:
        return False
    if module.check_mode:
        return True

    if not retry_codes:
        retry_codes = []

    tags_to_remove = [dict(Key=tagkey) for tagkey in tags_to_unset]

    try:
        AWSRetry.jittered_backoff(retries=10, catch_extra_error_codes=retry_codes)(
            client.delete_tags
        )(
            Resources=[resource_id], Tags=tags_to_remove
        )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Unable to delete tags {0} from {1}".format(tags_to_unset, resource_id))
    return True


def describe_ec2_tags(client, module, resource_id, resource_type=None, retry_codes=None):
    """
    Performs a paginated search of EC2 resource tags.

    :param client: an EC2 boto3 client
    :param module: an AnsibleAWSModule object
    :param resource_id: the identifier for the resource
    :param resource_type: the type of the resource
    :param retry_codes: additional boto3 error codes to trigger retries
    """
    filters = {'resource-id': resource_id}
    if resource_type:
        filters['resource-type'] = resource_type
    filters = ansible_dict_to_boto3_filter_list(filters)

    if not retry_codes:
        retry_codes = []

    try:
        retry_decorator = AWSRetry.jittered_backoff(retries=10, catch_extra_error_codes=retry_codes)
        results = paginated_query_with_retries(client, 'describe_tags', retry_decorator=retry_decorator,
                                               Filters=filters)
        return boto3_tag_list_to_ansible_dict(results.get('Tags', None))
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to describe tags for EC2 Resource: {0}".format(resource_id))


def ensure_ec2_tags(client, module, resource_id, resource_type=None, tags=None, purge_tags=True, retry_codes=None):
    """
    Updates the tags on an EC2 resource.

    To remove all tags the tags parameter must be explicitly set to an empty dictionary.

    :param client: an EC2 boto3 client
    :param module: an AnsibleAWSModule object
    :param resource_id: the identifier for the resource
    :param resource_type: the type of the resource
    :param tags: the Tags to apply to the resource
    :param purge_tags: whether tags missing from the tag list should be removed
    :param retry_codes: additional boto3 error codes to trigger retries
    :return: changed: returns True if the tags are changed
    """

    if tags is None:
        return False

    if not retry_codes:
        retry_codes = []

    changed = False
    current_tags = describe_ec2_tags(client, module, resource_id, resource_type, retry_codes)

    tags_to_set, tags_to_unset = compare_aws_tags(current_tags, tags, purge_tags)

    if purge_tags and not tags:
        tags_to_unset = current_tags

    changed |= remove_ec2_tags(client, module, resource_id, tags_to_unset, retry_codes)
    changed |= add_ec2_tags(client, module, resource_id, tags_to_set, retry_codes)

    return changed


def normalize_ec2_vpc_dhcp_config(option_config):
    """
    The boto2 module returned a config dict, but boto3 returns a list of dicts
    Make the data we return look like the old way, so we don't break users.
    This is also much more user-friendly.
    boto3:
        'DhcpConfigurations': [
            {'Key': 'domain-name', 'Values': [{'Value': 'us-west-2.compute.internal'}]},
            {'Key': 'domain-name-servers', 'Values': [{'Value': 'AmazonProvidedDNS'}]},
            {'Key': 'netbios-name-servers', 'Values': [{'Value': '1.2.3.4'}, {'Value': '5.6.7.8'}]},
            {'Key': 'netbios-node-type', 'Values': [1]},
            {'Key': 'ntp-servers', 'Values': [{'Value': '1.2.3.4'}, {'Value': '5.6.7.8'}]}
        ],
    The module historically returned:
        "new_options": {
            "domain-name": "ec2.internal",
            "domain-name-servers": ["AmazonProvidedDNS"],
            "netbios-name-servers": ["10.0.0.1", "10.0.1.1"],
            "netbios-node-type": "1",
            "ntp-servers": ["10.0.0.2", "10.0.1.2"]
        },
    """
    config_data = {}

    if len(option_config) == 0:
        # If there is no provided config, return the empty dictionary
        return config_data

    for config_item in option_config:
        # Handle single value keys
        if config_item['Key'] == 'netbios-node-type':
            if isinstance(config_item['Values'], integer_types):
                config_data['netbios-node-type'] = str((config_item['Values']))
            elif isinstance(config_item['Values'], list):
                config_data['netbios-node-type'] = str((config_item['Values'][0]['Value']))
        # Handle actual lists of values
        for option in ['domain-name', 'domain-name-servers', 'ntp-servers', 'netbios-name-servers']:
            if config_item['Key'] == option:
                config_data[option] = [val['Value'] for val in config_item['Values']]

    return config_data
