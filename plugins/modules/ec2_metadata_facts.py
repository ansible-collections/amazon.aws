#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: ec2_metadata_facts
version_added: 1.0.0
short_description: Gathers facts (instance metadata) about remote hosts within EC2
author:
    - Silviu Dicu (@silviud)
    - Vinay Dandekar (@roadmapper)
description:
    - This module fetches data from the instance metadata endpoint in EC2 as per
      U(https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html).
    - The module must be called from within the EC2 instance itself.
    - The module is configured to utilize the session oriented Instance Metadata Service v2 (IMDSv2)
      U(https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html).
    - If the HttpEndpoint parameter
      U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_ModifyInstanceMetadataOptions.html#API_ModifyInstanceMetadataOptions_RequestParameters)
      is set to disabled for the EC2 instance, the module will return an error while retrieving a session token.
notes:
    - Parameters to filter on ec2_metadata_facts may be added later.
options:
    metadata_token_ttl_seconds:
        description:
            - Specify a value for the C(X-aws-ec2-metadata-token-ttl-seconds) header.
            - Value must be between V(1) and V(21600).
        type: int
        default: 60
        version_added: 8.2.0
"""

EXAMPLES = r"""
# Gather EC2 metadata facts
- amazon.aws.ec2_metadata_facts:

# Set a bigger value for X-aws-ec2-metadata-token-ttl-seconds header
- amazon.aws.ec2_metadata_facts:
    metadata_token_ttl_seconds: 240

- debug:
    msg: "This instance is a t1.micro"
  when: ansible_ec2_instance_type == "t1.micro"
"""

RETURN = r"""
ansible_facts:
    description: Dictionary of new facts representing discovered properties of the EC2 instance.
    returned: changed
    type: complex
    contains:
        ansible_ec2_ami_id:
            description: The AMI ID used to launch the instance.
            type: str
            sample: "ami-XXXXXXXX"
        ansible_ec2_ami_launch_index:
            description:
                - If you started more than one instance at the same time, this value indicates the order in which the instance was launched.
                - The value of the first instance launched is 0.
            type: str
            sample: "0"
        ansible_ec2_ami_manifest_path:
            description:
                - The path to the AMI manifest file in Amazon S3.
                - If you used an Amazon EBS-backed AMI to launch the instance, the returned result is unknown.
            type: str
            sample: "(unknown)"
        ansible_ec2_ancestor_ami_ids:
            description:
                - The AMI IDs of any instances that were rebundled to create this AMI.
                - This value will only exist if the AMI manifest file contained an ancestor-amis key.
            type: str
            sample: "(unknown)"
        ansible_ec2_block_device_mapping_ami:
            description: The virtual device that contains the root/boot file system.
            type: str
            sample: "/dev/sda1"
        ansible_ec2_block_device_mapping_ebsN:
            description:
                - The virtual devices associated with Amazon EBS volumes, if any are present.
                - Amazon EBS volumes are only available in metadata if they were present at launch time or when the instance was last started.
                - The N indicates the index of the Amazon EBS volume (such as ebs1 or ebs2).
            type: str
            sample: "/dev/xvdb"
        ansible_ec2_block_device_mapping_ephemeralN:
            description: The virtual devices associated with ephemeral devices, if any are present. The N indicates the index of the ephemeral volume.
            type: str
            sample: "/dev/xvdc"
        ansible_ec2_block_device_mapping_root:
            description:
                - The virtual devices or partitions associated with the root devices, or partitions on the virtual device,
                  where the root (/ or C) file system is associated with the given instance.
            type: str
            sample: "/dev/sda1"
        ansible_ec2_block_device_mapping_swap:
            description: The virtual devices associated with swap. Not always present.
            type: str
            sample: "/dev/sda2"
        ansible_ec2_fws_instance_monitoring:
            description: "Value showing whether the customer has enabled detailed one-minute monitoring in CloudWatch."
            type: str
            sample: "enabled"
        ansible_ec2_hostname:
            description:
                - The private IPv4 DNS hostname of the instance.
                - In cases where multiple network interfaces are present, this refers to the eth0 device (the device for which the device number is 0).
            type: str
            sample: "ip-10-0-0-1.ec2.internal"
        ansible_ec2_iam_info:
            description:
                - If there is an IAM role associated with the instance, contains information about the last time the instance profile was updated,
                  including the instance's LastUpdated date, InstanceProfileArn, and InstanceProfileId. Otherwise, not present.
            type: complex
            sample: ""
            contains:
                LastUpdated:
                    description: The last time which InstanceProfile is associated with the Instance changed.
                    type: str
                InstanceProfileArn:
                    description: The ARN of the InstanceProfile associated with the Instance.
                    type: str
                InstanceProfileId:
                    description: The Id of the InstanceProfile associated with the Instance.
                    type: str
        ansible_ec2_iam_info_instanceprofilearn:
            description: The IAM instance profile ARN.
            type: str
            sample: "arn:aws:iam::123456789012:instance-profile/role_name"
        ansible_ec2_iam_info_instanceprofileid:
            description: IAM instance profile ID.
            type: str
            sample: ""
        ansible_ec2_iam_info_lastupdated:
            description: IAM info last updated time.
            type: str
            sample: "2017-05-12T02:42:27Z"
        ansible_ec2_iam_instance_profile_role:
            description: IAM instance role.
            type: str
            sample: "role_name"
        ansible_ec2_iam_security_credentials_role_name:
            description:
                - If there is an IAM role associated with the instance, role-name is the name of the role,
                  and role-name contains the temporary security credentials associated with the role. Otherwise, not present.
            type: str
            sample: ""
        ansible_ec2_iam_security_credentials_role_name_accesskeyid:
            description: IAM role access key ID.
            type: str
            sample: ""
        ansible_ec2_iam_security_credentials_role_name_code:
            description: IAM code.
            type: str
            sample: "Success"
        ansible_ec2_iam_security_credentials_role_name_expiration:
            description: IAM role credentials expiration time.
            type: str
            sample: "2017-05-12T09:11:41Z"
        ansible_ec2_iam_security_credentials_role_name_lastupdated:
            description: IAM role last updated time.
            type: str
            sample: "2017-05-12T02:40:44Z"
        ansible_ec2_iam_security_credentials_role_name_secretaccesskey:
            description: IAM role secret access key.
            type: str
            sample: ""
        ansible_ec2_iam_security_credentials_role_name_token:
            description: IAM role token.
            type: str
            sample: ""
        ansible_ec2_iam_security_credentials_role_name_type:
            description: IAM role type.
            type: str
            sample: "AWS-HMAC"
        ansible_ec2_instance_action:
            description: Notifies the instance that it should reboot in preparation for bundling.
            type: str
            sample: "none"
        ansible_ec2_instance_id:
            description: The ID of this instance.
            type: str
            sample: "i-XXXXXXXXXXXXXXXXX"
        ansible_ec2_instance_identity_document:
            description: JSON containing instance attributes, such as instance-id, private IP address, etc.
            type: str
            sample: ""
        ansible_ec2_instance_identity_document_accountid:
            description: ""
            type: str
            sample: "123456789012"
        ansible_ec2_instance_identity_document_architecture:
            description: Instance system architecture.
            type: str
            sample: "x86_64"
        ansible_ec2_instance_identity_document_availabilityzone:
            description: The Availability Zone in which the instance launched.
            type: str
            sample: "us-east-1a"
        ansible_ec2_instance_identity_document_billingproducts:
            description: Billing products for this instance.
            type: str
            sample: ""
        ansible_ec2_instance_identity_document_devpayproductcodes:
            description: Product codes for the launched AMI.
            type: str
            sample: ""
        ansible_ec2_instance_identity_document_imageid:
            description: The AMI ID used to launch the instance.
            type: str
            sample: "ami-01234567"
        ansible_ec2_instance_identity_document_instanceid:
            description: The ID of this instance.
            type: str
            sample: "i-0123456789abcdef0"
        ansible_ec2_instance_identity_document_instancetype:
            description: The type of instance.
            type: str
            sample: "m4.large"
        ansible_ec2_instance_identity_document_kernelid:
            description: The ID of the kernel launched with this instance, if applicable.
            type: str
            sample: ""
        ansible_ec2_instance_identity_document_pendingtime:
            description: The instance pending time.
            type: str
            sample: "2017-05-11T20:51:20Z"
        ansible_ec2_instance_identity_document_privateip:
            description:
                - The private IPv4 address of the instance.
                - In cases where multiple network interfaces are present, this refers to the eth0 device (the device for which the device number is 0).
            type: str
            sample: "10.0.0.1"
        ansible_ec2_instance_identity_document_ramdiskid:
            description: The ID of the RAM disk specified at launch time, if applicable.
            type: str
            sample: ""
        ansible_ec2_instance_identity_document_region:
            description: The Region in which the instance launched.
            type: str
            sample: "us-east-1"
        ansible_ec2_instance_identity_document_version:
            description: Identity document version.
            type: str
            sample: "2010-08-31"
        ansible_ec2_instance_identity_pkcs7:
            description: Used to verify the document's authenticity and content against the signature.
            type: str
            sample: ""
        ansible_ec2_instance_identity_rsa2048:
            description: Used to verify the document's authenticity and content against the signature.
            type: str
            sample: ""
        ansible_ec2_instance_identity_signature:
            description: Data that can be used by other parties to verify its origin and authenticity.
            type: str
            sample: ""
        ansible_ec2_instance_life_cycle:
            description: The purchasing option of the instance.
            type: str
            sample: "on-demand"
        ansible_ec2_instance_tags:
            description:
                - The dict of tags for the instance.
                - Returns empty dict if access to tags (InstanceMetadataTags) in instance metadata is not enabled.
            type: dict
            sample: {"tagKey1": "tag value 1", "tag_key2": "tag value 2"}
            version_added: 9.1.0
        ansible_ec2_instance_tags_keys:
            description:
                - The list of tags keys of the instance.
                - Returns empty list if access to tags (InstanceMetadataTags) in instance metadata is not enabled.
            type: list
            elements: str
            sample: ["tagKey1", "tag_key2"]
            version_added: 5.5.0
        ansible_ec2_instance_type:
            description: The type of the instance.
            type: str
            sample: "m4.large"
        ansible_ec2_local_hostname:
            description:
                - The private IPv4 DNS hostname of the instance.
                - In cases where multiple network interfaces are present, this refers to the eth0 device (the device for which the device number is 0).
            type: str
            sample: "ip-10-0-0-1.ec2.internal"
        ansible_ec2_local_ipv4:
            description:
                - The private IPv4 address of the instance.
                - In cases where multiple network interfaces are present, this refers to the eth0 device (the device for which the device number is 0).
            type: str
            sample: "10.0.0.1"
        ansible_ec2_mac:
            description:
                - The instance's media access control (MAC) address.
                - In cases where multiple network interfaces are present, this refers to the eth0 device (the device for which the device number is 0).
            type: str
            sample: "00:11:22:33:44:55"
        ansible_ec2_metrics_vhostmd:
            description: Metrics; no longer available.
            type: str
            sample: ""
        ansible_ec2_network_interfaces_macs_mac_address_device_number:
            description:
                - The unique device number associated with that interface. The device number corresponds to the device name;
                  for example, a device-number of 2 is for the eth2 device.
                - This category corresponds to the DeviceIndex and device-index fields that are used by the Amazon EC2 API and the EC2 commands for the AWS CLI.
            type: str
            sample: "0"
        ansible_ec2_network_interfaces_macs_mac_address_interface_id:
            description: The elastic network interface ID.
            type: str
            sample: "eni-12345678"
        ansible_ec2_network_interfaces_macs_mac_address_ipv4_associations_ip_address:
            description: The private IPv4 addresses that are associated with each public-ip address and assigned to that interface.
            type: str
            sample: ""
        ansible_ec2_network_interfaces_macs_mac_address_ipv6s:
            description: The IPv6 addresses associated with the interface. Returned only for instances launched into a VPC.
            type: str
            sample: ""
        ansible_ec2_network_interfaces_macs_mac_address_local_hostname:
            description: The interface's local hostname.
            type: str
            sample: ""
        ansible_ec2_network_interfaces_macs_mac_address_local_ipv4s:
            description: The private IPv4 addresses associated with the interface.
            type: str
            sample: ""
        ansible_ec2_network_interfaces_macs_mac_address_mac:
            description: The instance's MAC address.
            type: str
            sample: "00:11:22:33:44:55"
        ansible_ec2_network_interfaces_macs_mac_address_owner_id:
            description:
                - The ID of the owner of the network interface.
                - In multiple-interface environments, an interface can be attached by a third party, such as Elastic Load Balancing.
                - Traffic on an interface is always billed to the interface owner.
            type: str
            sample: "123456789012"
        ansible_ec2_network_interfaces_macs_mac_address_public_hostname:
            description:
                - The interface's public DNS (IPv4). If the instance is in a VPC,
                  this category is only returned if the enableDnsHostnames attribute is set to true.
            type: str
            sample: "ec2-1-2-3-4.compute-1.amazonaws.com"
        ansible_ec2_network_interfaces_macs_mac_address_public_ipv4s:
            description: The Elastic IP addresses associated with the interface. There may be multiple IPv4 addresses on an instance.
            type: str
            sample: "1.2.3.4"
        ansible_ec2_network_interfaces_macs_mac_address_security_group_ids:
            description: The IDs of the security groups to which the network interface belongs. Returned only for instances launched into a VPC.
            type: str
            sample: "sg-01234567,sg-01234568"
        ansible_ec2_network_interfaces_macs_mac_address_security_groups:
            description: Security groups to which the network interface belongs. Returned only for instances launched into a VPC.
            type: str
            sample: "secgroup1,secgroup2"
        ansible_ec2_network_interfaces_macs_mac_address_subnet_id:
            description: The ID of the subnet in which the interface resides. Returned only for instances launched into a VPC.
            type: str
            sample: "subnet-01234567"
        ansible_ec2_network_interfaces_macs_mac_address_subnet_ipv4_cidr_block:
            description: The IPv4 CIDR block of the subnet in which the interface resides. Returned only for instances launched into a VPC.
            type: str
            sample: "10.0.1.0/24"
        ansible_ec2_network_interfaces_macs_mac_address_subnet_ipv6_cidr_blocks:
            description: The IPv6 CIDR block of the subnet in which the interface resides. Returned only for instances launched into a VPC.
            type: str
            sample: ""
        ansible_ec2_network_interfaces_macs_mac_address_vpc_id:
            description: The ID of the VPC in which the interface resides. Returned only for instances launched into a VPC.
            type: str
            sample: "vpc-0123456"
        ansible_ec2_network_interfaces_macs_mac_address_vpc_ipv4_cidr_block:
            description: The IPv4 CIDR block of the VPC in which the interface resides. Returned only for instances launched into a VPC.
            type: str
            sample: "10.0.0.0/16"
        ansible_ec2_network_interfaces_macs_mac_address_vpc_ipv4_cidr_blocks:
            description: The IPv4 CIDR block of the VPC in which the interface resides. Returned only for instances launched into a VPC.
            type: str
            sample: "10.0.0.0/16"
        ansible_ec2_network_interfaces_macs_mac_address_vpc_ipv6_cidr_blocks:
            description: The IPv6 CIDR block of the VPC in which the interface resides. Returned only for instances launched into a VPC.
            type: str
            sample: ""
        ansible_ec2_placement_availability_zone:
            description: The Availability Zone in which the instance launched.
            type: str
            sample: "us-east-1a"
        ansible_ec2_placement_region:
            description: The Region in which the instance launched.
            type: str
            sample: "us-east-1"
        ansible_ec2_product_codes:
            description: Product codes associated with the instance, if any.
            type: str
            sample: "aw0evgkw8e5c1q413zgy5pjce"
        ansible_ec2_profile:
            description: EC2 instance hardware profile.
            type: str
            sample: "default-hvm"
        ansible_ec2_public_hostname:
            description:
                - The instance's public DNS. If the instance is in a VPC, this category is only returned if the enableDnsHostnames attribute is set to true.
            type: str
            sample: "ec2-1-2-3-4.compute-1.amazonaws.com"
        ansible_ec2_public_ipv4:
            description: The public IPv4 address. If an Elastic IP address is associated with the instance, the value returned is the Elastic IP address.
            type: str
            sample: "1.2.3.4"
        ansible_ec2_public_key:
            description: Public key. Only available if supplied at instance launch time.
            type: str
            sample: ""
        ansible_ec2_ramdisk_id:
            description: The ID of the RAM disk specified at launch time, if applicable.
            type: str
            sample: ""
        ansible_ec2_reservation_id:
            description: The ID of the reservation.
            type: str
            sample: "r-0123456789abcdef0"
        ansible_ec2_security_groups:
            description:
                - The names of the security groups applied to the instance. After launch, you can only change the security groups of instances running in a VPC.
                - Such changes are reflected here and in network/interfaces/macs/mac/security-groups.
            type: str
            sample: "securitygroup1,securitygroup2"
        ansible_ec2_services_domain:
            description: The domain for AWS resources for the region; for example, amazonaws.com for us-east-1.
            type: str
            sample: "amazonaws.com"
        ansible_ec2_services_partition:
            description:
                - The partition that the resource is in. For standard AWS regions, the partition is aws.
                - If you have resources in other partitions, the partition is aws-partitionname.
                - For example, the partition for resources in the China (Beijing) region is aws-cn.
            type: str
            sample: "aws"
        ansible_ec2_spot_termination_time:
            description:
                - The approximate time, in UTC, that the operating system for your Spot instance will receive the shutdown signal.
                - This item is present and contains a time value only if the Spot instance has been marked for termination by Amazon EC2.
                - The termination-time item is not set to a time if you terminated the Spot instance yourself.
            type: str
            sample: "2015-01-05T18:02:00Z"
        ansible_ec2_user_data:
            description: The instance user data.
            type: str
            sample: "#!/bin/bash"
"""

import json
import re
import socket
import time
import zlib

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import quote
from ansible.module_utils.urls import fetch_url

socket.setdefaulttimeout(5)

# The ec2_metadata_facts module is a special case, while we generally dropped support for Python < 3.6
# this module doesn't depend on the SDK and still has valid use cases for folks working with older
# OSes.

# pylint: disable=consider-using-f-string
try:
    json_decode_error = json.JSONDecodeError
except AttributeError:
    json_decode_error = ValueError


class Ec2Metadata:
    ec2_metadata_token_uri = "http://169.254.169.254/latest/api/token"
    ec2_metadata_uri = "http://169.254.169.254/latest/meta-data/"
    ec2_metadata_instance_tags_uri = "http://169.254.169.254/latest/meta-data/tags/instance"
    ec2_sshdata_uri = "http://169.254.169.254/latest/meta-data/public-keys/0/openssh-key"
    ec2_userdata_uri = "http://169.254.169.254/latest/user-data/"
    ec2_dynamicdata_uri = "http://169.254.169.254/latest/dynamic/"

    def __init__(
        self,
        module,
        ec2_metadata_token_uri=None,
        ec2_metadata_uri=None,
        ec2_metadata_instance_tags_uri=None,
        ec2_sshdata_uri=None,
        ec2_userdata_uri=None,
        ec2_dynamicdata_uri=None,
    ):
        self.module = module
        self.uri_token = ec2_metadata_token_uri or self.ec2_metadata_token_uri
        self.uri_meta = ec2_metadata_uri or self.ec2_metadata_uri
        self.uri_instance_tags = ec2_metadata_instance_tags_uri or self.ec2_metadata_instance_tags_uri
        self.uri_user = ec2_userdata_uri or self.ec2_userdata_uri
        self.uri_ssh = ec2_sshdata_uri or self.ec2_sshdata_uri
        self.uri_dynamic = ec2_dynamicdata_uri or self.ec2_dynamicdata_uri
        self._data = {}
        self._token = None
        self._prefix = "ansible_ec2_%s"

    def _decode(self, data):
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            # Decoding as UTF-8 failed, return data without raising an error
            self.module.warn("Decoding user-data as UTF-8 failed, return data as is ignoring any error")
            return data.decode("utf-8", errors="ignore")

    def decode_user_data(self, data):
        is_compressed = False

        # Check if data is compressed using zlib header
        if data.startswith(b"\x78\x9c") or data.startswith(b"\x1f\x8b"):
            is_compressed = True

        if is_compressed:
            # Data is compressed, attempt decompression and decode using UTF-8
            try:
                decompressed = zlib.decompress(data, zlib.MAX_WBITS | 32)
                return self._decode(decompressed)
            except zlib.error:
                # Unable to decompress, return original data
                self.module.warn(
                    "Unable to decompress user-data using zlib, attempt to decode original user-data as UTF-8"
                )
                return self._decode(data)
        else:
            # Data is not compressed, decode using UTF-8
            return self._decode(data)

    def _fetch(self, url):
        encoded_url = quote(url, safe="%/:=&?~#+!$,;'@()*[]")
        headers = {}
        if self._token:
            headers = {"X-aws-ec2-metadata-token": self._token}

        response, info = fetch_url(self.module, encoded_url, headers=headers, force=True)

        if info.get("status") in (401, 403):
            self.module.fail_json(msg="Failed to retrieve metadata from AWS: {0}".format(info["msg"]), response=info)
        elif info.get("status") not in (200, 404):
            time.sleep(3)
            # request went bad, retry once then raise
            self.module.warn("Retrying query to metadata service. First attempt failed: {0}".format(info["msg"]))
            response, info = fetch_url(self.module, encoded_url, headers=headers, force=True)
            if info.get("status") not in (200, 404):
                # fail out now
                self.module.fail_json(
                    msg="Failed to retrieve metadata from AWS: {0}".format(info["msg"]), response=info
                )
        if response and info["status"] < 400:
            data = response.read()
            if "user-data" in encoded_url:
                return to_text(self.decode_user_data(data))
        else:
            data = None
        return to_text(data)

    def _mangle_fields(self, fields, uri, filter_patterns=None):
        filter_patterns = ["public-keys-0"] if filter_patterns is None else filter_patterns

        new_fields = {}
        for key, value in fields.items():
            split_fields = key[len(uri):].split("/")  # fmt: skip
            # Parse out the IAM role name (which is _not_ the same as the instance profile name)
            if (
                len(split_fields) == 3
                and split_fields[0:2] == ["iam", "security-credentials"]
                and ":" not in split_fields[2]
            ):
                new_fields[self._prefix % "iam-instance-profile-role"] = split_fields[2]
            if len(split_fields) > 1 and split_fields[1]:
                new_key = "-".join(split_fields)
                new_fields[self._prefix % new_key] = value
            else:
                new_key = "".join(split_fields)
                new_fields[self._prefix % new_key] = value
        for pattern in filter_patterns:
            for key in dict(new_fields):
                match = re.search(pattern, key)
                if match:
                    new_fields.pop(key)
        return new_fields

    def fetch(self, uri, recurse=True):
        raw_subfields = self._fetch(uri)
        if not raw_subfields:
            return
        subfields = raw_subfields.split("\n")
        for field in subfields:
            if field.endswith("/") and recurse:
                self.fetch(uri + field)
            if uri.endswith("/"):
                new_uri = uri + field
            else:
                new_uri = uri + "/" + field
            if new_uri not in self._data and not new_uri.endswith("/"):
                content = self._fetch(new_uri)
                if field == "security-groups" or field == "security-group-ids":
                    sg_fields = ",".join(content.split("\n"))
                    self._data["%s" % (new_uri)] = sg_fields
                else:
                    try:
                        json_dict = json.loads(content)
                        self._data["%s" % (new_uri)] = content
                        for key, value in json_dict.items():
                            self._data["%s:%s" % (new_uri, key.lower())] = value
                    except (json_decode_error, AttributeError):
                        self._data["%s" % (new_uri)] = content  # not a stringified JSON string

    def fix_invalid_varnames(self, data):
        """Change ':'' and '-' to '_' to ensure valid template variable names"""
        new_data = data.copy()
        for key, value in data.items():
            if ":" in key or "-" in key:
                newkey = re.sub(":|-", "_", key)
                new_data[newkey] = value
                del new_data[key]

        return new_data

    def fetch_session_token(self, uri_token):
        """Used to get a session token for IMDSv2"""
        metadata_token_ttl_seconds = self.module.params.get("metadata_token_ttl_seconds")
        headers = {"X-aws-ec2-metadata-token-ttl-seconds": metadata_token_ttl_seconds}
        response, info = fetch_url(self.module, uri_token, method="PUT", headers=headers, force=True)

        if info.get("status") == 403:
            self.module.fail_json(
                msg="Failed to retrieve metadata token from AWS: {0}".format(info["msg"]), response=info
            )
        elif info.get("status") not in (200, 404):
            time.sleep(3)
            # request went bad, retry once then raise
            self.module.warn("Retrying query to metadata service. First attempt failed: {0}".format(info["msg"]))
            response, info = fetch_url(self.module, uri_token, method="PUT", headers=headers, force=True)
            if info.get("status") not in (200, 404):
                # fail out now
                self.module.fail_json(
                    msg="Failed to retrieve metadata token from AWS: {0}".format(info["msg"]), response=info
                )
        if response:
            token_data = response.read()
        else:
            token_data = None
        return to_text(token_data)

    def get_instance_tags(self, tag_keys, data):
        tags = {}
        for key in tag_keys:
            value = data.get("ansible_ec2_tags_instance_{}".format(key))
            if value is not None:
                tags[key] = value
        return tags

    def run(self):
        self._token = self.fetch_session_token(self.uri_token)  # create session token for IMDS
        self.fetch(self.uri_meta)  # populate _data with metadata
        data = self._mangle_fields(self._data, self.uri_meta)
        data[self._prefix % "user-data"] = self._fetch(self.uri_user)
        data[self._prefix % "public-key"] = self._fetch(self.uri_ssh)

        self._data = {}  # clear out metadata in _data
        self.fetch(self.uri_dynamic)  # populate _data with dynamic data
        dyndata = self._mangle_fields(self._data, self.uri_dynamic)
        data.update(dyndata)
        data = self.fix_invalid_varnames(data)

        instance_tags_keys = self._fetch(self.uri_instance_tags)
        instance_tags_keys = instance_tags_keys.split("\n") if instance_tags_keys != "None" else []
        data[self._prefix % "instance_tags_keys"] = instance_tags_keys

        instance_tags = self.get_instance_tags(instance_tags_keys, data)
        data[self._prefix % "instance_tags"] = instance_tags

        # Maintain old key for backwards compatibility
        if "ansible_ec2_instance_identity_document_region" in data:
            data["ansible_ec2_placement_region"] = data["ansible_ec2_instance_identity_document_region"]
        return data


def main():
    argument_spec = dict(
        metadata_token_ttl_seconds=dict(required=False, default=60, type="int", no_log=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    metadata_token_ttl_seconds = module.params.get("metadata_token_ttl_seconds")

    if metadata_token_ttl_seconds <= 0 or metadata_token_ttl_seconds > 21600:
        module.fail_json(msg="The option 'metadata_token_ttl_seconds' must be set to a value between 1 and 21600.")

    ec2_metadata_facts = Ec2Metadata(module).run()
    ec2_metadata_facts_result = dict(changed=False, ansible_facts=ec2_metadata_facts)

    module.exit_json(**ec2_metadata_facts_result)


if __name__ == "__main__":
    main()
