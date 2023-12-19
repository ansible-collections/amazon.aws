#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_vpc_dhcp_option
version_added: 1.0.0
short_description: Manages DHCP Options, and can ensure the DHCP options for the given VPC match what's
  requested
description:
  - This module removes, or creates DHCP option sets, and can associate them to a VPC.
  - Optionally, a new DHCP Options set can be created that converges a VPC's existing
    DHCP option set with values provided.
  - When dhcp_options_id is provided, the module will
    1. remove (with state='absent')
    2. ensure tags are applied (if state='present' and tags are provided
    3. attach it to a VPC (if state='present' and a vpc_id is provided.
  - If any of the optional values are missing, they will either be treated
    as a no-op (i.e., inherit what already exists for the VPC)
  - To remove existing options while inheriting, supply an empty value
    (e.g. set ntp_servers to [] if you want to remove them from the VPC's options)
author:
  - "Joel Thompson (@joelthompson)"
options:
  domain_name:
    description:
      - The domain name to set in the DHCP option sets.
    type: str
  dns_servers:
    description:
      - A list of IP addresses to set the DNS servers for the VPC to.
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
      - If no VPC ID is provided, and no matching option set is found then a new
        DHCP option set is created.
    type: str
  delete_old:
    description:
      - Whether to delete the old VPC DHCP option set when associating a new one.
      - This is primarily useful for debugging/development purposes when you
        want to quickly roll back to the old option set. Note that this setting
        will be ignored, and the old DHCP option set will be preserved, if it
        is in use by any other VPC. (Otherwise, AWS will return an error.)
    type: bool
    default: true
  inherit_existing:
    description:
      - For any DHCP options not specified in these parameters, whether to
        inherit them from the options set already applied to I(vpc_id), or to
        reset them to be empty.
    type: bool
    default: false
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
notes:
  - Support for I(purge_tags) was added in release 2.0.0.
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

RETURN = r"""
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

EXAMPLES = r"""
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
    delete_old: true
    inherit_existing: false

# Ensure the DHCP option set for the VPC has 10.0.0.4 and 10.0.1.4 as the specified DNS servers, but
# keep any other existing settings. Also, keep the old DHCP option set around.
- amazon.aws.ec2_vpc_dhcp_option:
    region: us-east-1
    dns_servers:
      - "{{groups['dns-primary']}}"
      - "{{groups['dns-secondary']}}"
    vpc_id: vpc-123456
    inherit_existing: true
    delete_old: false

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

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import ensure_ec2_tags
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import normalize_ec2_vpc_dhcp_config
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_specifications


def fetch_dhcp_options_for_vpc(client, module, vpc_id):
    try:
        vpcs = client.describe_vpcs(aws_retry=True, VpcIds=[vpc_id])["Vpcs"]
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg=f"Unable to describe vpc {vpc_id}")

    if len(vpcs) != 1:
        return None
    try:
        dhcp_options = client.describe_dhcp_options(aws_retry=True, DhcpOptionsIds=[vpcs[0]["DhcpOptionsId"]])
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg=f"Unable to describe dhcp option {vpcs[0]['DhcpOptionsId']}")

    if len(dhcp_options["DhcpOptions"]) != 1:
        return None
    return dhcp_options["DhcpOptions"][0]["DhcpConfigurations"], dhcp_options["DhcpOptions"][0]["DhcpOptionsId"]


def remove_dhcp_options_by_id(client, module, dhcp_options_id):
    changed = False
    # First, check if this dhcp option is associated to any other vpcs
    try:
        associations = client.describe_vpcs(
            aws_retry=True, Filters=[{"Name": "dhcp-options-id", "Values": [dhcp_options_id]}]
        )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg=f"Unable to describe VPC associations for dhcp option id {dhcp_options_id}")
    if len(associations["Vpcs"]) > 0:
        return changed

    changed = True
    if not module.check_mode:
        try:
            client.delete_dhcp_options(aws_retry=True, DhcpOptionsId=dhcp_options_id)
        except is_boto3_error_code("InvalidDhcpOptionsID.NotFound"):
            return False
        except (
            botocore.exceptions.BotoCoreError,
            botocore.exceptions.ClientError,
        ) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg=f"Unable to delete dhcp option {dhcp_options_id}")

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

    for dopts in all_dhcp_options["DhcpOptions"]:
        if module.params["tags"]:
            # If we were given tags, try to match on them
            boto_tags = ansible_dict_to_boto3_tag_list(module.params["tags"])
            if dopts["DhcpConfigurations"] == new_config and dopts["Tags"] == boto_tags:
                return True, dopts["DhcpOptionsId"]
        elif dopts["DhcpConfigurations"] == new_config:
            return True, dopts["DhcpOptionsId"]

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
    if params["domain_name"] is not None:
        new_config.append({"Key": "domain-name", "Values": [{"Value": params["domain_name"]}]})
    if params["dns_servers"] is not None:
        dns_server_list = []
        for server in params["dns_servers"]:
            dns_server_list.append({"Value": server})
        new_config.append({"Key": "domain-name-servers", "Values": dns_server_list})
    if params["ntp_servers"] is not None:
        ntp_server_list = []
        for server in params["ntp_servers"]:
            ntp_server_list.append({"Value": server})
        new_config.append({"Key": "ntp-servers", "Values": ntp_server_list})
    if params["netbios_name_servers"] is not None:
        netbios_server_list = []
        for server in params["netbios_name_servers"]:
            netbios_server_list.append({"Value": server})
        new_config.append({"Key": "netbios-name-servers", "Values": netbios_server_list})
    if params["netbios_node_type"] is not None:
        new_config.append({"Key": "netbios-node-type", "Values": params["netbios_node_type"]})

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
    tags_list = []

    for option in ["domain-name", "domain-name-servers", "ntp-servers", "netbios-name-servers"]:
        if desired_config.get(option):
            create_config.append({"Key": option, "Values": desired_config[option]})
    if desired_config.get("netbios-node-type"):
        # We need to listify this one
        create_config.append({"Key": "netbios-node-type", "Values": [desired_config["netbios-node-type"]]})

    if module.params.get("tags"):
        tags_list = boto3_tag_specifications(module.params["tags"], ["dhcp-options"])

    try:
        if not module.check_mode:
            dhcp_options = client.create_dhcp_options(
                aws_retry=True, DhcpConfigurations=create_config, TagSpecifications=tags_list
            )
            return changed, dhcp_options["DhcpOptions"]["DhcpOptionsId"]
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Unable to create dhcp option set")

    return changed, None


def find_opt_index(config, option):
    return next((i for i, item in enumerate(config) if item["Key"] == option), None)


def inherit_dhcp_config(existing_config, new_config):
    """
    Compare two DhcpConfigurations lists and apply existing options to unset parameters

    If there's an existing option config and the new option is not set or it's none,
    inherit the existing config.
    The configs are unordered lists of dicts with non-unique keys, so we have to find
    the right list index for a given config option first.
    """
    changed = False
    for option in ["domain-name", "domain-name-servers", "ntp-servers", "netbios-name-servers", "netbios-node-type"]:
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
        dhcp_option_info = AWSRetry.jittered_backoff(catch_extra_error_codes=["InvalidDhcpOptionID.NotFound"])(
            client.describe_dhcp_options,
        )(
            DhcpOptionsIds=[dhcp_options_id],
        )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Unable to describe dhcp options")

    dhcp_options_set = dhcp_option_info["DhcpOptions"][0]
    dhcp_option_info = {
        "DhcpOptionsId": dhcp_options_set["DhcpOptionsId"],
        "DhcpConfigurations": dhcp_options_set["DhcpConfigurations"],
        "Tags": boto3_tag_list_to_ansible_dict(dhcp_options_set.get("Tags", [{"Value": "", "Key": "Name"}])),
    }
    return camel_dict_to_snake_dict(dhcp_option_info, ignore_list=["Tags"])


def associate_options(client, module, vpc_id, dhcp_options_id):
    try:
        if not module.check_mode:
            client.associate_dhcp_options(aws_retry=True, DhcpOptionsId=dhcp_options_id, VpcId=vpc_id)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg=f"Unable to associate dhcp option {dhcp_options_id} to VPC {vpc_id}")


def main():
    argument_spec = dict(
        dhcp_options_id=dict(type="str", default=None),
        domain_name=dict(type="str", default=None),
        dns_servers=dict(type="list", elements="str", default=None),
        ntp_servers=dict(type="list", elements="str", default=None),
        netbios_name_servers=dict(type="list", elements="str", default=None),
        netbios_node_type=dict(type="int", default=None),
        vpc_id=dict(type="str", default=None),
        delete_old=dict(type="bool", default=True),
        inherit_existing=dict(type="bool", default=False),
        tags=dict(type="dict", default=None, aliases=["resource_tags"]),
        purge_tags=dict(default=True, type="bool"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, check_boto3=False, supports_check_mode=True)

    vpc_id = module.params["vpc_id"]
    delete_old = module.params["delete_old"]
    inherit_existing = module.params["inherit_existing"]
    tags = module.params["tags"]
    purge_tags = module.params["purge_tags"]
    state = module.params["state"]
    dhcp_options_id = module.params["dhcp_options_id"]

    found = False
    changed = False
    new_config = create_dhcp_config(module)
    existing_config = None
    existing_id = None

    client = module.client("ec2", retry_decorator=AWSRetry.jittered_backoff())

    if state == "absent":
        if not dhcp_options_id:
            # Look up the option id first by matching the supplied options
            dhcp_options_id = match_dhcp_options(client, module, new_config)
        changed = remove_dhcp_options_by_id(client, module, dhcp_options_id)
        module.exit_json(changed=changed, dhcp_options={}, dhcp_config={})

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
                        changed |= ensure_ec2_tags(
                            client,
                            module,
                            dhcp_options_id,
                            resource_type="dhcp-options",
                            tags=tags,
                            purge_tags=purge_tags,
                        )
                    return_config = normalize_ec2_vpc_dhcp_config(new_config)
                    results = get_dhcp_options_info(client, module, dhcp_options_id)
                    module.exit_json(
                        changed=changed,
                        dhcp_options_id=dhcp_options_id,
                        dhcp_options=results,
                        dhcp_config=return_config,
                    )
        # If no vpc_id was given, or the options don't match then look for an existing set using tags
        found, dhcp_options_id = match_dhcp_options(client, module, new_config)

    else:
        # Now let's cover the case where there are existing options that we were told about by id
        # If a dhcp_options_id was supplied we don't look at options inside, just set tags (if given)
        try:
            # Preserve the boto2 module's behaviour of checking if the option set exists first,
            # and return the same error message if it does not
            client.describe_dhcp_options(aws_retry=True, DhcpOptionsIds=[dhcp_options_id])
            # If that didn't fail, then we know the option ID exists
            found = True
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="a dhcp_options_id was supplied, but does not exist")

    if not found:
        # If we still don't have an options ID, create it
        changed, dhcp_options_id = create_dhcp_option_set(client, module, new_config)
    else:
        if tags or purge_tags:
            changed |= ensure_ec2_tags(
                client, module, dhcp_options_id, resource_type="dhcp-options", tags=tags, purge_tags=purge_tags
            )

    # If we were given a vpc_id, then attach the options we now have to that before we finish
    if vpc_id:
        associate_options(client, module, vpc_id, dhcp_options_id)
        changed = changed or True

    if delete_old and existing_id:
        remove_dhcp_options_by_id(client, module, existing_id)

    return_config = normalize_ec2_vpc_dhcp_config(new_config)
    results = get_dhcp_options_info(client, module, dhcp_options_id)
    module.exit_json(changed=changed, dhcp_options_id=dhcp_options_id, dhcp_options=results, dhcp_config=return_config)


if __name__ == "__main__":
    main()
