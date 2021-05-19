#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: ec2_vpc_dhcp_option
version_added: 1.0.0
short_description: Manages DHCP Options, and can ensure the DHCP options for the given VPC match what's
  requested
description:
  - This module removes, or creates DHCP option sets, and can associate them to a VPC.
    Optionally, a new DHCP Options set can be created that converges a VPC's existing
    DHCP option set with values provided.
    When dhcp_options_id is provided, the module will
    1. remove (with state='absent')
    2. ensure tags are applied (if state='present' and tags are provided
    3. attach it to a VPC (if state='present' and a vpc_id is provided.
    If any of the optional values are missing, they will either be treated
    as a no-op (i.e., inherit what already exists for the VPC)
    To remove existing options while inheriting, supply an empty value
    (e.g. set ntp_servers to [] if you want to remove them from the VPC's options)
    Most of the options should be self-explanatory.
author: "Joel Thompson (@joelthompson)"
options:
  domain_name:
    description:
      - The domain name to set in the DHCP option sets
    type: str
  dns_servers:
    description:
      - A list of hosts to set the DNS servers for the VPC to. (Should be a
        list of IP addresses rather than host names.)
    type: list
    elements: str
  ntp_servers:
    description:
      - List of hosts to advertise as NTP servers for the VPC.
    type: list
    elements: str
  netbios_name_servers:
    description:
      - List of hosts to advertise as NetBIOS servers.
    type: list
    elements: str
  netbios_node_type:
    description:
      - NetBIOS node type to advertise in the DHCP options.
        The AWS recommendation is to use 2 (when using netbios name services)
        U(https://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/VPC_DHCP_Options.html)
    type: int
  vpc_id:
    description:
      - VPC ID to associate with the requested DHCP option set.
        If no vpc id is provided, and no matching option set is found then a new
        DHCP option set is created.
    type: str
  delete_old:
    description:
      - Whether to delete the old VPC DHCP option set when associating a new one.
        This is primarily useful for debugging/development purposes when you
        want to quickly roll back to the old option set. Note that this setting
        will be ignored, and the old DHCP option set will be preserved, if it
        is in use by any other VPC. (Otherwise, AWS will return an error.)
    type: bool
    default: 'yes'
  inherit_existing:
    description:
      - For any DHCP options not specified in these parameters, whether to
        inherit them from the options set already applied to vpc_id, or to
        reset them to be empty.
    type: bool
    default: 'no'
  tags:
    description:
      - Tags to be applied to a VPC options set if a new one is created, or
        if the resource_id is provided. (options must match)
    aliases: [ 'resource_tags']
    type: dict
  purge_tags:
    description:
      - Remove tags not listed in I(tags).
    type: bool
    default: true
    version_added: 2.0.0
  dhcp_options_id:
    description:
      - The resource_id of an existing DHCP options set.
        If this is specified, then it will override other settings, except tags
        (which will be updated to match)
    type: str
  state:
    description:
      - create/assign or remove the DHCP options.
        If state is set to absent, then a DHCP options set matched either
        by id, or tags and options will be removed if possible.
    default: present
    choices: [ 'absent', 'present' ]
    type: str
extends_documentation_fragment:
- amazon.aws.aws
- amazon.aws.ec2
'''

RETURN = """
changed:
    description: Whether the dhcp options were changed
    type: bool
    returned: always
dhcp_options:
    description: The DHCP options created, associated or found
    returned: when available
    type: dict
    contains:
        dhcp_configurations:
            description: The DHCP configuration for the option set
            type: list
            sample:
              - '{"key": "ntp-servers", "values": [{"value": "10.0.0.2" , "value": "10.0.1.2"}]}'
              - '{"key": "netbios-name-servers", "values": [{value": "10.0.0.1"}, {"value": "10.0.1.1" }]}'
        dhcp_options_id:
            description: The aws resource id of the primary DCHP options set created or found
            type: str
            sample: "dopt-0955331de6a20dd07"
        owner_id:
            description: The ID of the AWS account that owns the DHCP options set.
            type: str
            sample: 012345678912
        tags:
            description: The tags to be applied to a DHCP options set
            type: list
            sample:
              - '{"Key": "CreatedBy", "Value": "ansible-test"}'
              - '{"Key": "Collection", "Value": "amazon.aws"}'
dhcp_options_id:
    description: The aws resource id of the primary DCHP options set created, found or removed
    type: str
    returned: when available
dhcp_config:
    description: The boto2-style DHCP options created, associated or found
    returned: when available
    type: dict
    contains:
      domain-name-servers:
        description: The IP addresses of up to four domain name servers, or AmazonProvidedDNS.
        returned: when available
        type: list
        sample:
          - 10.0.0.1
          - 10.0.1.1
      domain-name:
        description: The domain name for hosts in the DHCP option sets
        returned: when available
        type: list
        sample:
          - "my.example.com"
      ntp-servers:
        description: The IP addresses of up to four Network Time Protocol (NTP) servers.
        returned: when available
        type: list
        sample:
          - 10.0.0.1
          - 10.0.1.1
      netbios-name-servers:
        description: The IP addresses of up to four NetBIOS name servers.
        returned: when available
        type: list
        sample:
          - 10.0.0.1
          - 10.0.1.1
      netbios-node-type:
        description: The NetBIOS node type (1, 2, 4, or 8).
        returned: when available
        type: str
        sample: 2
"""

EXAMPLES = """
# Completely overrides the VPC DHCP options associated with VPC vpc-123456 and deletes any existing
# DHCP option set that may have been attached to that VPC.
- amazon.aws.ec2_vpc_dhcp_option:
    domain_name: "foo.example.com"
    region: us-east-1
    dns_servers:
        - 10.0.0.1
        - 10.0.1.1
    ntp_servers:
        - 10.0.0.2
        - 10.0.1.2
    netbios_name_servers:
        - 10.0.0.1
        - 10.0.1.1
    netbios_node_type: 2
    vpc_id: vpc-123456
    delete_old: True
    inherit_existing: False


# Ensure the DHCP option set for the VPC has 10.0.0.4 and 10.0.1.4 as the specified DNS servers, but
# keep any other existing settings. Also, keep the old DHCP option set around.
- amazon.aws.ec2_vpc_dhcp_option:
    region: us-east-1
    dns_servers:
      - "{{groups['dns-primary']}}"
      - "{{groups['dns-secondary']}}"
    vpc_id: vpc-123456
    inherit_existing: True
    delete_old: False


## Create a DHCP option set with 4.4.4.4 and 8.8.8.8 as the specified DNS servers, with tags
## but do not assign to a VPC
- amazon.aws.ec2_vpc_dhcp_option:
    region: us-east-1
    dns_servers:
      - 4.4.4.4
      - 8.8.8.8
    tags:
      Name: google servers
      Environment: Test

## Delete a DHCP options set that matches the tags and options specified
- amazon.aws.ec2_vpc_dhcp_option:
    region: us-east-1
    dns_servers:
      - 4.4.4.4
      - 8.8.8.8
    tags:
      Name: google servers
      Environment: Test
    state: absent

## Associate a DHCP options set with a VPC by ID
- amazon.aws.ec2_vpc_dhcp_option:
    region: us-east-1
    dhcp_options_id: dopt-12345678
    vpc_id: vpc-123456

"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ..module_utils.core import AnsibleAWSModule
from ..module_utils.core import is_boto3_error_code
from ..module_utils.ec2 import AWSRetry
from ..module_utils.ec2 import ansible_dict_to_boto3_tag_list
from ..module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ..module_utils.ec2 import camel_dict_to_snake_dict
from ..module_utils.ec2 import compare_aws_tags
from ..module_utils.ec2 import normalize_ec2_vpc_dhcp_config


def ensure_tags(client, module, dhcp_options_id, tags, purge_tags):
    changed = False
    tags_to_unset = False
    tags_to_set = False

    if module.check_mode and dhcp_options_id is None:
        # We can't describe tags without an option id, we might get here when creating a new option set in check_mode
        return changed

    current_tags = boto3_tag_list_to_ansible_dict(client.describe_tags(aws_retry=True, Filters=[{'Name': 'resource-id', 'Values': [dhcp_options_id]}])['Tags'])

    if tags:
        tags_to_set, tags_to_unset = compare_aws_tags(current_tags, tags, purge_tags=purge_tags)
    if purge_tags and not tags:
        tags_to_unset = current_tags

    if tags_to_unset:
        changed = True
        if not module.check_mode:
            try:
                client.delete_tags(aws_retry=True, Resources=[dhcp_options_id], Tags=[dict(Key=tagkey) for tagkey in tags_to_unset])
            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                module.fail_json_aws(e, msg="Unable to delete tags {0}".format(tags_to_unset))

    if tags_to_set:
        changed = True
        if not module.check_mode:
            try:
                client.create_tags(aws_retry=True, Resources=[dhcp_options_id], Tags=ansible_dict_to_boto3_tag_list(tags_to_set))
            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                module.fail_json_aws(e, msg="Unable to add tags {0}".format(tags_to_set))

    return changed


def fetch_dhcp_options_for_vpc(client, module, vpc_id):
    try:
        vpcs = client.describe_vpcs(aws_retry=True, VpcIds=[vpc_id])['Vpcs']
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Unable to describe vpc {0}".format(vpc_id))

    if len(vpcs) != 1:
        return None
    try:
        dhcp_options = client.describe_dhcp_options(aws_retry=True, DhcpOptionsIds=[vpcs[0]['DhcpOptionsId']])
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Unable to describe dhcp option {0}".format(vpcs[0]['DhcpOptionsId']))

    if len(dhcp_options['DhcpOptions']) != 1:
        return None
    return dhcp_options['DhcpOptions'][0]['DhcpConfigurations'], dhcp_options['DhcpOptions'][0]['DhcpOptionsId']


def remove_dhcp_options_by_id(client, module, dhcp_options_id):
    changed = False
    # First, check if this dhcp option is associated to any other vpcs
    try:
        associations = client.describe_vpcs(aws_retry=True, Filters=[{'Name': 'dhcp-options-id', 'Values': [dhcp_options_id]}])
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Unable to describe VPC associations for dhcp option id {0}".format(dhcp_options_id))
    if len(associations['Vpcs']) > 0:
        return changed

    changed = True
    if not module.check_mode:
        try:
            client.delete_dhcp_options(aws_retry=True, DhcpOptionsId=dhcp_options_id)
        except is_boto3_error_code('InvalidDhcpOptionsID.NotFound'):
            return False
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Unable to delete dhcp option {0}".format(dhcp_options_id))

    return changed


def match_dhcp_options(client, module, new_config):
    """
    Returns a DhcpOptionsId if the module parameters match; else None
    Filter by tags, if any are specified
    """
    try:
        all_dhcp_options = client.describe_dhcp_options(aws_retry=True)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Unable to describe dhcp options")

    for dopts in all_dhcp_options['DhcpOptions']:
        if module.params['tags']:
            # If we were given tags, try to match on them
            boto_tags = ansible_dict_to_boto3_tag_list(module.params['tags'])
            if dopts['DhcpConfigurations'] == new_config and dopts['Tags'] == boto_tags:
                return True, dopts['DhcpOptionsId']
        elif dopts['DhcpConfigurations'] == new_config:
            return True, dopts['DhcpOptionsId']

    return False, None


def create_dhcp_config(module):
    """
    Convert provided parameters into a DhcpConfigurations list that conforms to what the API returns:
    https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeDhcpOptions.html
        [{'Key': 'domain-name',
         'Values': [{'Value': 'us-west-2.compute.internal'}]},
        {'Key': 'domain-name-servers',
         'Values': [{'Value': 'AmazonProvidedDNS'}]},
         ...],
    """
    new_config = []
    params = module.params
    if params['domain_name'] is not None:
        new_config.append({'Key': 'domain-name', 'Values': [{'Value': params['domain_name']}]})
    if params['dns_servers'] is not None:
        dns_server_list = []
        for server in params['dns_servers']:
            dns_server_list.append({'Value': server})
        new_config.append({'Key': 'domain-name-servers', 'Values': dns_server_list})
    if params['ntp_servers'] is not None:
        ntp_server_list = []
        for server in params['ntp_servers']:
            ntp_server_list.append({'Value': server})
        new_config.append({'Key': 'ntp-servers', 'Values': ntp_server_list})
    if params['netbios_name_servers'] is not None:
        netbios_server_list = []
        for server in params['netbios_name_servers']:
            netbios_server_list.append({'Value': server})
        new_config.append({'Key': 'netbios-name-servers', 'Values': netbios_server_list})
    if params['netbios_node_type'] is not None:
        new_config.append({'Key': 'netbios-node-type', 'Values': params['netbios_node_type']})

    return new_config


def create_dhcp_option_set(client, module, new_config):
    """
    A CreateDhcpOptions object looks different than the object we create in create_dhcp_config()
    This is the only place we use it, so create it now
    https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_CreateDhcpOptions.html
    We have to do this after inheriting any existing_config, so we need to start with the object
    that we made in create_dhcp_config().
    normalize_config() gives us the nicest format to work with for this.
    """
    changed = True
    desired_config = normalize_ec2_vpc_dhcp_config(new_config)
    create_config = []
    for option in ['domain-name', 'domain-name-servers', 'ntp-servers', 'netbios-name-servers']:
        if desired_config.get(option):
            create_config.append({'Key': option, 'Values': desired_config[option]})
    if desired_config.get('netbios-node-type'):
        # We need to listify this one
        create_config.append({'Key': 'netbios-node-type', 'Values': [desired_config['netbios-node-type']]})

    try:
        if not module.check_mode:
            dhcp_options = client.create_dhcp_options(aws_retry=True, DhcpConfigurations=create_config)
            return changed, dhcp_options['DhcpOptions']['DhcpOptionsId']
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Unable to create dhcp option set")

    return changed, None


def find_opt_index(config, option):
    return (next((i for i, item in enumerate(config) if item["Key"] == option), None))


def inherit_dhcp_config(existing_config, new_config):
    """
    Compare two DhcpConfigurations lists and apply existing options to unset parameters

    If there's an existing option config and the new option is not set or it's none,
    inherit the existing config.
    The configs are unordered lists of dicts with non-unique keys, so we have to find
    the right list index for a given config option first.
    """
    changed = False
    for option in ['domain-name', 'domain-name-servers', 'ntp-servers',
                   'netbios-name-servers', 'netbios-node-type']:
        existing_index = find_opt_index(existing_config, option)
        new_index = find_opt_index(new_config, option)
        # `if existing_index` evaluates to False on index 0, so be very specific and verbose
        if existing_index is not None and new_index is None:
            new_config.append(existing_config[existing_index])
            changed = True

    return changed, new_config


def get_dhcp_options_info(client, module, dhcp_options_id):
    # Return boto3-style details, consistent with the _info module

    if module.check_mode and dhcp_options_id is None:
        # We can't describe without an option id, we might get here when creating a new option set in check_mode
        return None

    try:
        dhcp_option_info = client.describe_dhcp_options(aws_retry=True, DhcpOptionsIds=[dhcp_options_id])
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Unable to describe dhcp options")

    dhcp_options_set = dhcp_option_info['DhcpOptions'][0]
    dhcp_option_info = {'DhcpOptionsId': dhcp_options_set['DhcpOptionsId'],
                        'DhcpConfigurations': dhcp_options_set['DhcpConfigurations'],
                        'Tags': boto3_tag_list_to_ansible_dict(dhcp_options_set.get('Tags', [{'Value': '', 'Key': 'Name'}]))}
    return camel_dict_to_snake_dict(dhcp_option_info, ignore_list=['Tags'])


def associate_options(client, module, vpc_id, dhcp_options_id):
    try:
        if not module.check_mode:
            client.associate_dhcp_options(aws_retry=True, DhcpOptionsId=dhcp_options_id, VpcId=vpc_id)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Unable to associate dhcp option {0} to VPC {1}".format(dhcp_options_id, vpc_id))


def main():
    argument_spec = dict(
        dhcp_options_id=dict(type='str', default=None),
        domain_name=dict(type='str', default=None),
        dns_servers=dict(type='list', elements='str', default=None),
        ntp_servers=dict(type='list', elements='str', default=None),
        netbios_name_servers=dict(type='list', elements='str', default=None),
        netbios_node_type=dict(type='int', default=None),
        vpc_id=dict(type='str', default=None),
        delete_old=dict(type='bool', default=True),
        inherit_existing=dict(type='bool', default=False),
        tags=dict(type='dict', default=None, aliases=['resource_tags']),
        purge_tags=dict(default=True, type='bool'),
        state=dict(type='str', default='present', choices=['present', 'absent'])
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        check_boto3=False,
        supports_check_mode=True
    )

    vpc_id = module.params['vpc_id']
    delete_old = module.params['delete_old']
    inherit_existing = module.params['inherit_existing']
    tags = module.params['tags']
    purge_tags = module.params['purge_tags']
    state = module.params['state']
    dhcp_options_id = module.params['dhcp_options_id']

    found = False
    changed = False
    new_config = create_dhcp_config(module)
    existing_config = None
    existing_id = None

    client = module.client('ec2', retry_decorator=AWSRetry.jittered_backoff())

    module.deprecate("The 'new_config' return key is deprecated and will be replaced by 'dhcp_config'. Both values are returned for now.",
                     date='2022-12-01', collection_name='amazon.aws')
    if state == 'absent':
        if not dhcp_options_id:
            # Look up the option id first by matching the supplied options
            dhcp_options_id = match_dhcp_options(client, module, new_config)
        changed = remove_dhcp_options_by_id(client, module, dhcp_options_id)
        module.exit_json(changed=changed, new_options={}, dhcp_options={})

    if not dhcp_options_id:
        # If we were given a vpc_id then we need to look at the configuration on that
        if vpc_id:
            existing_config, existing_id = fetch_dhcp_options_for_vpc(client, module, vpc_id)
            # if we've been asked to inherit existing options, do that now
            if inherit_existing and existing_config:
                changed, new_config = inherit_dhcp_config(existing_config, new_config)
            # Do the vpc's dhcp options already match what we're asked for? if so we are done
            if existing_config:
                if new_config == existing_config:
                    dhcp_options_id = existing_id
                    if tags or purge_tags:
                        tags_changed = ensure_tags(client, module, dhcp_options_id, tags, purge_tags)
                        changed = changed or tags_changed
                    return_config = normalize_ec2_vpc_dhcp_config(new_config)
                    results = get_dhcp_options_info(client, module, dhcp_options_id)
                    module.exit_json(changed=changed, new_options=return_config, dhcp_options_id=dhcp_options_id, dhcp_options=results)
        # If no vpc_id was given, or the options don't match then look for an existing set using tags
        found, dhcp_options_id = match_dhcp_options(client, module, new_config)

    else:
        # Now let's cover the case where there are existing options that we were told about by id
        # If a dhcp_options_id was supplied we don't look at options inside, just set tags (if given)
        try:
            # Preserve the boto2 module's behaviour of checking if the option set exists first,
            # and return the same error message if it does not
            dhcp_options = client.describe_dhcp_options(aws_retry=True, DhcpOptionsIds=[dhcp_options_id])
            # If that didn't fail, then we know the option ID exists
            found = True
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="a dhcp_options_id was supplied, but does not exist")

    if not found:
        # If we still don't have an options ID, create it
        changed, dhcp_options_id = create_dhcp_option_set(client, module, new_config)

    if tags or purge_tags:
        # q('tags? ', module.params['dbg'])
        tags_changed = ensure_tags(client, module, dhcp_options_id, tags, purge_tags)
        changed = (changed or tags_changed)

    # If we were given a vpc_id, then attach the options we now have to that before we finish
    if vpc_id:
        associate_options(client, module, vpc_id, dhcp_options_id)
        changed = (changed or True)

    if delete_old and existing_id:
        remove_dhcp_options_by_id(client, module, existing_id)

    return_config = normalize_ec2_vpc_dhcp_config(new_config)
    results = get_dhcp_options_info(client, module, dhcp_options_id)
    module.exit_json(changed=changed, new_options=return_config, dhcp_options_id=dhcp_options_id, dhcp_options=results, dhcp_config=return_config)


if __name__ == '__main__':
    main()
