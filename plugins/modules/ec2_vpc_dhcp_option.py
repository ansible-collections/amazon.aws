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

requirements:
    - boto
'''

RETURN = """
new_options:
    description: The DHCP options created, associated or found
    returned: when appropriate
    type: dict
    sample:
      domain-name-servers:
        - 10.0.0.1
        - 10.0.1.1
      netbois-name-servers:
        - 10.0.0.1
        - 10.0.1.1
      netbios-node-type: 2
      domain-name: "my.example.com"
dhcp_options_id:
    description: The aws resource id of the primary DCHP options set created, found or removed
    type: str
    returned: when available
changed:
    description: Whether the dhcp options were changed
    type: bool
    returned: always
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

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ..module_utils.core import AnsibleAWSModule
from ..module_utils.core import is_boto3_error_code
from ..module_utils.ec2 import AWSRetry
from ..module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ..module_utils.ec2 import ansible_dict_to_boto3_tag_list
from ..module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ..module_utils.ec2 import compare_aws_tags


def ensure_tags(client, module, dhcp_options_id, tags):
    changed = False
    current_tags = boto3_tag_list_to_ansible_dict(client.describe_tags(Filters=[{'Name': 'resource-id', 'Values': [dhcp_options_id]}])['Tags'])
    tags_to_set, tags_to_unset = compare_aws_tags(current_tags, tags, purge_tags=True)

    if tags_to_unset:
        changed = True
        if not module.check_mode:
            try:
                client.delete_tags(aws_retry=True, Resources=[dhcp_options_id], Tags=ansible_dict_to_boto3_tag_list(tags_to_unset))
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

    if len(vpcs) != 1 or vpcs[0]['IsDefault']:
        return None
    try:
        dhcp_options = client.describe_dhcp_options(aws_retry=True, DhcpOptionsIds=[vpcs[0]['DhcpOptionsId']])
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Unable to describe dhcp option {0}".format(vpcs[0]['DhcpOptionsId']))

    if len(dhcp_options) != 1:
        return None
    return dhcp_options['DhcpOptions'][0]


def remove_dhcp_options_by_id(client, module, dhcp_options_id):
    changed = False
    try:
        option_exists = client.describe_dhcp_options(aws_retry=True, DhcpOptionsIds=[dhcp_options_id])['DhcpOptions']
    except is_boto3_error_code('InvalidDhcpOptionID.NotFound'):
        return False
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Unable to describe dhcp option {0}".format(dhcp_options_id))

    if len(option_exists['DhcpOptions']) > 0:
        changed = True
        if not module.check_mode:
            try:
                client.delete_dhcp_options(aws_retry=True, DhcpOptionsId=dhcp_options_id)
            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                module.fail_json_aws(e, msg="Unable to delete dhcp option {0}".format(dhcp_options_id))

    return changed


def match_dhcp_options(client, module, new_config):
    """
    Returns a DhcpOptionsId if the module parameters match; else None
    Filter by tags, if any are specified
    """
    # TODO: I was trying to repurpose this to search by tags like in
    #  https://github.com/ansible-collections/amazon.aws/blob/main/plugins/modules/ec2_vpc_dhcp_option.py#L344
    #  Needs more testing
    try:
        all_dhcp_options = client.describe_dhcp_options(aws_retry=True)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Unable to describe dhcp options")

    for dopts in all_dhcp_options['DhcpOptions']:
        if module.params['tags']:
            # If we were given tags, try to match on them
            # TODO this feels like the wrong place entirely to do this
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
        new_config.append({'Key': 'netbios-node-type', 'Values': netbios_server_list})
    if params['netbios_node_type'] is not None:
        new_config.append({'Key': 'netbios_node_type', 'Values': params['netbios_node_type']})

    return new_config


def create_dhcp_option_set(client, module):
    changed = True
    """
    A CreateDhcpOptions object looks different that the object we create in create_dhcp_config()
    This is the only place we use it, so create it now
    https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_CreateDhcpOptions.html
    """
    new_config = []
    if module.params['dns_servers'] is not None:
        new_config.append({'Key': 'domain-name-servers', 'Values': module.params['dns_servers']})
    if module.params['netbios_name_servers'] is not None:
        new_config.append({'Key': 'netbios-name-servers', 'Values': module.params['netbios_name_servers']})
    if module.params['ntp_servers'] is not None:
        new_config.append({'Key': 'ntp-servers', 'Values': module.params['ntp_servers']})
    if module.params['domain_name'] is not None:
        new_config.append({'Key': 'domain-name', 'Values': [module.params['domain_name']]})
    if module.params['netbios_node_type'] is not None:
        new_config.append({'Key': 'netbios-node-type', 'Values': module.params['netbios_node_type']})
        # if module.params[option] is not None:
        #     create_dhcp_options.append({'Key': option, 'Value': module.params[option]})
    try:
        if not module.check_mode:
            dhcp_options = client.create_dhcp_options(aws_retry=True, DhcpConfigurations=new_config)
            return changed, dhcp_options['DhcpOptions']['DhcpOptionsId']
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Unable to create dhcp option set")

    return changed, None


def find_opt_index(config, option):
    # TODO: I don't like this but I guess it works?
    return (next((i for i, item in enumerate(config) if item["Key"] == option), None))


def inherit_dhcp_config(existing_config, new_config):
    # Compare two DhcpConfigurations lists and apply existing options to unset parameters
    """
    If there's an existing option and the new option is not an empty list, and
    both, the new option is not set or it's none
    set new to existing
    """
    changed = False
    for option in ['domain-name', 'domain-name-servers', 'ntp-servers',
                   'netbios-name-servers', 'netbios-node-type']:
        existing_index = find_opt_index(existing_config, option)
        new_index = find_opt_index(new_config, option)
        # if existing_index and new_index:
        #     if existing_config[existing_index]['Value'] != new_config[new_index]['Value']:
        #         new_config[new_index]['Value'] = existing_config[existing_index]['Value']
        if existing_config and not new_index:
            new_config.append(existing_config[existing_index])
            changed = True

    return changed, new_config


def normalize_config(option_config):
    """
    The config dictionary looked very different in boto2 vs boto3
    Make the data we return look like the old way, so we don't break users
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
            "netbios-name-servers": [10.0.0.1", "10.0.1.1"],
            "netbios-node-type": "1",
            "ntp-servers": [10.0.0.2", "10.0.1.2"]
        },
    And all keys were returned by the module.
    """
    config_data = {
            "domain-name": None,
            "domain-name-servers": None,
            "netbios-name-servers": None,
            "netbios-node-type": None,
            "ntp-servers": None
        }
    if len(option_config) == 0:
        # If there is no provided config, return the empty dictionary
        return config_data
    else:
        option_config = option_config[0]
    for option in ['domain-name', 'netbios-node-type']:
        # Handle single value keys (boto3 returns them as a single item list)
        if option_config['Key'] == option:
            config_data[option] = (option_config['Values'][0], None)
    for option in ['domain-name-servers', 'ntp-servers', 'netbios-name-servers']:
        # Handle actual list options
        if option_config['Key'] == option:
            config_data[option] = [val['Value'] for val in option_config['Values']]

    return config_data


def associate_options(client, module, vpc_id, dhcp_options_id):
    changed = True
    try:
        if not module.check_mode:
            client.associate_dhcp_options(DhcpOptionsId=dhcp_options_id, VpcId=vpc_id)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Unable to associate dhcp option {0} to VPC {1}".format(dhcp_options_id, vpc_id))
    return changed


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
    state = module.params['state']
    dhcp_options_id = module.params['dhcp_options_id']

    new_config = create_dhcp_config(module)
    existing_options = None
    found = False

    client = module.client('ec2', retry_decorator=AWSRetry.jittered_backoff())

    if state == 'absent':
        if not dhcp_options_id:
            # Look up the option id first by matching the supplied options
            dhcp_options_id = match_dhcp_options(client, module, new_config)
        changed = remove_dhcp_options_by_id(client, module, dhcp_options_id)
        module.exit_json(changed=changed, new_options={})

    if not dhcp_options_id:
        # If we were given a vpc_id then we need to look at the configuration on that
        if vpc_id:
            existing_options = fetch_dhcp_options_for_vpc(client, module, vpc_id)
            # if we've been asked to inherit existing options, do that now
            if inherit_existing and existing_options:
                changed, new_config = inherit_dhcp_config(existing_options['DhcpConfigurations'], new_config)
                # Do the vpc's dhcp options already match what we're asked for? if so we are done
            if new_config == existing_options['DhcpConfigurations']:
                dhcp_options_id = existing_options['DhcpOptionsId']
                # TODO: this needs more testing
                return_config = normalize_config(new_config[0])
                module.exit_json(changed=changed, new_options=return_config, dhcp_options_id=dhcp_options_id)
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

    if tags:
        changed = ensure_tags(client, module, dhcp_options_id, tags)

    # If we were given a vpc_id, then attach the options we now have to that before we finish
    if vpc_id:
        changed = associate_options(client, module, vpc_id, dhcp_options_id)

    if delete_old and existing_options:
        changed = remove_dhcp_options_by_id(client, module, existing_options)

    return_config = normalize_config(new_config)
    module.exit_json(changed=changed, new_options=return_config, dhcp_options_id=dhcp_options_id)


if __name__ == '__main__':
    main()
