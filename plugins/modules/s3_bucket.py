#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
---
module: s3_bucket
version_added: 1.0.0
short_description: Manage S3 buckets in AWS, DigitalOcean, Ceph, Walrus, FakeS3 and StorageGRID
description:
  - Manage S3 buckets.
  - Compatible with AWS, DigitalOcean, Ceph, Walrus, FakeS3 and StorageGRID.
  - When using non-AWS services, O(endpoint_url) should be specified.
author:
  - Rob White (@wimnat)
  - Aubin Bikouo (@abikouo)
options:
  force:
    description:
      - When trying to delete a bucket, delete all keys (including versions and delete markers)
        in the bucket first (an S3 bucket must be empty for a successful deletion).
    type: bool
    default: false
  name:
    description:
      - Name of the S3 bucket.
    required: true
    type: str
  policy:
    description:
      - The JSON policy as a string. Set to the string V("null") to force the absence of a policy.
    type: json
  ceph:
    description:
      - Enable API compatibility with Ceph RGW.
      - It takes into account the S3 API subset working with Ceph in order to provide the same module
        behaviour where possible.
      - Requires O(endpoint_url) if O(ceph=true).
    aliases: ['rgw']
    type: bool
    default: false
  requester_pays:
    description:
      - With Requester Pays buckets, the requester instead of the bucket owner pays the cost
        of the request and the data download from the bucket.
    type: bool
  state:
    description:
      - Create or remove the S3 bucket.
    required: false
    default: present
    choices: [ 'present', 'absent' ]
    type: str
  versioning:
    description:
      - Whether versioning is enabled or disabled (note that once versioning is enabled, it can only be suspended).
    type: bool
  encryption:
    description:
      - Describes the default server-side encryption to apply to new objects in the bucket.
        In order to remove the server-side encryption, the encryption needs to be set to 'none' explicitly.
      - "Note: Since January 2023 Amazon S3 doesn't support disabling encryption on S3 buckets."
    choices: [ 'none', 'AES256', 'aws:kms' ]
    type: str
  encryption_key_id:
    description:
      - KMS master key ID to use for the default encryption.
      - If not specified then it will default to the AWS provided KMS key.
      - This parameter is only supported if O(encryption) is V(aws:kms).
    type: str
  bucket_key_enabled:
    description:
      - Enable S3 Bucket Keys for SSE-KMS on new objects.
      - See the AWS documentation for more information
        U(https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-key.html).
      - Bucket Key encryption is only supported if O(encryption=aws:kms).
    required: false
    type: bool
    version_added: 4.1.0
  public_access:
    description:
      - Configure public access block for S3 bucket.
      - This option cannot be used together with O(delete_public_access).
      - |
        Note: At the end of April 2023 Amazon updated the default settings to block public access by
        default.  While the defaults for this module remain unchanged, it is necessary to explicitly
        pass the O(public_access) parameter to enable public access ACLs.
    suboptions:
      block_public_acls:
        description: Sets BlockPublicAcls value.
        type: bool
        default: false
      block_public_policy:
        description: Sets BlockPublicPolicy value.
        type: bool
        default: false
      ignore_public_acls:
        description: Sets IgnorePublicAcls value.
        type: bool
        default: false
      restrict_public_buckets:
        description: Sets RestrictPublicAcls value.
        type: bool
        default: false
    type: dict
    version_added: 1.3.0
  delete_public_access:
    description:
      - Delete public access block configuration from bucket.
      - This option cannot be used together with a O(public_access) definition.
    default: false
    type: bool
    version_added: 1.3.0
  object_ownership:
    description:
      - Allow bucket's ownership controls.
      - V(BucketOwnerEnforced) - ACLs are disabled and no longer affect access permissions to your
        bucket. Requests to set or update ACLs fail. However, requests to read ACLs are supported.
        Bucket owner has full ownership and control. Object writer no longer has full ownership and
        control.
      - V(BucketOwnerPreferred) - Objects uploaded to the bucket change ownership to the bucket owner
        if the objects are uploaded with the bucket-owner-full-control canned ACL.
      - V(ObjectWriter) - The uploading account will own the object
        if the object is uploaded with the bucket-owner-full-control canned ACL.
      - This option cannot be used together with a O(delete_object_ownership) definition.
      - V(BucketOwnerEnforced) has been added in version 3.2.0.
      - "Note: At the end of April 2023 Amazon updated the default setting to V(BucketOwnerEnforced)."
    choices: [ 'BucketOwnerEnforced', 'BucketOwnerPreferred', 'ObjectWriter' ]
    type: str
    version_added: 2.0.0
  object_lock_enabled:
    description:
      - Whether S3 Object Lock to be enabled.
      - Defaults to V(false) when creating a new bucket.
    type: bool
    version_added: 5.3.0
  delete_object_ownership:
    description:
      - Delete bucket's ownership controls.
      - This option cannot be used together with a O(object_ownership) definition.
    default: false
    type: bool
    version_added: 2.0.0
  acl:
    description:
      - The canned ACL to apply to the bucket.
      - If your bucket uses the bucket owner enforced setting for S3 Object Ownership,
        ACLs are disabled and no longer affect permissions.
      - If O(public_access.ignore_public_acls=true) setting O(acl) to a value other than V(private)
        may return success but not have an affect.
    choices: [ 'private', 'public-read', 'public-read-write', 'authenticated-read' ]
    type: str
    version_added: 3.1.0
  validate_bucket_name:
    description:
      - Whether the bucket name should be validated to conform to AWS S3 naming rules.
      - On by default, this may be disabled for S3 backends that do not enforce these rules.
      - See U(https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html).
    type: bool
    version_added: 3.1.0
    default: true
  dualstack:
    description:
      - Enables Amazon S3 Dual-Stack Endpoints, allowing S3 communications using both IPv4 and IPv6.
      - Mutually exclusive with O(endpoint_url).
    type: bool
    default: false
    version_added: 6.0.0
  accelerate_enabled:
    description:
      - Enables Amazon S3 Transfer Acceleration, sent data will be routed to Amazon S3 over an optimized network path.
      - Transfer Acceleration is not available in AWS GovCloud (US).
      - See U(https://docs.aws.amazon.com/govcloud-us/latest/UserGuide/govcloud-s3.html#govcloud-S3-diffs).
    type: bool
    version_added: 8.1.0
  object_lock_default_retention:
    description:
      - Default Object Lock configuration that will be applied by default to
        every new object placed in the specified bucket.
      - O(object_lock_enabled) must be included and set to V(True).
      - Object lock retention policy can't be removed.
    suboptions:
      mode:
        description: Type of retention modes.
        choices: [ "GOVERNANCE", "COMPLIANCE"]
        required: true
        type: str
      days:
        description:
            - The number of days that you want to specify for the default retention period.
            - Mutually exclusive with O(object_lock_default_retention.years).
        type: int
      years:
        description:
            - The number of years that you want to specify for the default retention period.
            - Mutually exclusive with O(object_lock_default_retention.days).
        type: int
    type: dict
    version_added: 8.1.0
  inventory:
    description:
      - Enable S3 Inventory, saving list of the objects and their corresponding
        metadata on a daily or weekly basis for an S3 bucket.
    type: list
    elements: dict
    suboptions:
      destination:
        description: Contains information about where to publish the inventory results.
        type: dict
        required: True
        suboptions:
          account_id:
            description: The account ID that owns the destination S3 bucket. If no account ID is provided, the owner is not validated before exporting data.
            type: str
          bucket:
            description: The Amazon Resource Name (ARN) of the bucket where inventory results will be published.
            type: str
            required: True
          format:
            description: Specifies the output format of the inventory results.
            type: str
            choices: [ 'CSV', 'ORC', 'Parquet' ]
            required: True
          prefix:
            description: The prefix that is prepended to all inventory results.
            type: str
      filter:
        description: The prefix that an object must have to be included in the inventory results.
        type: str
      id:
        description: The ID used to identify the inventory configuration.
        type: str
        required: True
      schedule:
        description: Specifies the schedule for generating inventory results.
        type: str
        choices: [ 'Daily', 'Weekly' ]
        required: True
      included_object_versions:
        description: |
            Object versions to include in the inventory list. If set to All, the list includes all the object versions,
            which adds the version-related fields VersionId, IsLatest, and DeleteMarker to the list. If set to Current,
            the list does not contain these version-related fields.
        type: str
        required: True
        choices: [ 'All', 'Current' ]
      optional_fields:
        description: Contains the optional fields that are included in the inventory results.
        type: list
        elements: str
        choices: [ "Size", "LastModifiedDate", "StorageClass", "ETag",
            "IsMultipartUploaded", "ReplicationStatus", "EncryptionStatus",
            "ObjectLockRetainUntilDate", "ObjectLockMode",
            "ObjectLockLegalHoldStatus", "IntelligentTieringAccessTier",
            "BucketKeyStatus", "ChecksumAlgorithm", "ObjectAccessControlList",
            "ObjectOwner" ]
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3

notes:
  - If C(requestPayment), C(policy), C(tagging) or C(versioning)
    operations/API aren't implemented by the endpoint, module doesn't fail
    if each parameter satisfies the following condition.
    O(requester_pays) is V(false), O(policy), O(tags), and O(versioning) are V(None).
  - For Walrus O(endpoint_url) should be set to the FQDN of the endpoint with neither scheme nor path.
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create a simple S3 bucket
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present

# Create a simple S3 bucket on Ceph Rados Gateway
- amazon.aws.s3_bucket:
    name: mys3bucket
    endpoint_url: http://your-ceph-rados-gateway-server.xxx
    ceph: true

# Remove an S3 bucket and any keys it contains
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: absent
    force: true

# Create a bucket, add a policy from a file, enable requester pays, enable versioning and tag
- amazon.aws.s3_bucket:
    name: mys3bucket
    policy: "{{ lookup('file','policy.json') }}"
    requester_pays: true
    versioning: true
    tags:
      example: tag1
      another: tag2

# Create a simple DigitalOcean Spaces bucket using their provided regional endpoint
- amazon.aws.s3_bucket:
    name: mydobucket
    endpoint_url: 'https://nyc3.digitaloceanspaces.com'

# Create a bucket with AES256 encryption
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present
    encryption: "AES256"

# Create a bucket with aws:kms encryption, KMS key
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present
    encryption: "aws:kms"
    encryption_key_id: "arn:aws:kms:us-east-1:1234/5678example"

# Create a bucket with aws:kms encryption, Bucket key
- amazon.aws.s3_bucket:
    name: mys3bucket
    bucket_key_enabled: true
    encryption: "aws:kms"

# Create a bucket with aws:kms encryption, default key
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present
    encryption: "aws:kms"

# Create a bucket with public policy block configuration
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present
    public_access:
      block_public_acls: true
      ignore_public_acls: true
      ## keys == 'false' can be omitted, undefined keys defaults to 'false'
      # block_public_policy: false
      # restrict_public_buckets: false

# Delete public policy block from bucket
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present
    delete_public_access: true

# Create a bucket with object ownership controls set to ObjectWriter
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present
    object_ownership: ObjectWriter

# Delete onwership controls from bucket
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present
    delete_object_ownership: true

# Delete a bucket policy from bucket
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present
    policy: "null"

# This example grants public-read to everyone on bucket using ACL
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present
    acl: public-read

# Enable transfer acceleration
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present
    accelerate_enabled: true

# Default Object Lock retention
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present
    object_lock_enabled: true
    object_lock_default_retention:
      mode: governance
      days: 1
# Bucket with inventory configuration:
- amazon.aws.s3_bucket:
    name: mys3bucket
    state: present
    inventory:
      - id: mys3bucket-inventory-id
        destination:
          bucket: "arn:aws:s3:::mys3inventorybucket"
        optional_fields:
          - "Size"
        included_object_versions: "All"
        schedule: "Weekly"
"""

RETURN = r"""
encryption:
    description: Server-side encryption of the objects in the S3 bucket.
    type: dict
    returned: when O(state=present)
    sample: {
                "SSEAlgorithm": "AES256"
            }
name:
    description: Bucket name.
    returned: when O(state=present)
    type: str
    sample: "a-testing-bucket-name"
object_ownership:
    description: S3 bucket's ownership controls.
    type: str
    returned: when O(state=present)
    sample: "BucketOwnerPreferred"
object_lock_default_retention:
    description: S3 bucket's object lock retention policy.
    type: dict
    returned: when O(state=present)
    sample: {
        "Days": 1,
        "Mode": "GOVERNANCE",
        "Years": 0,
    }
policy:
    description: S3 bucket's policy.
    type: dict
    returned: when O(state=present)
    sample: {
        "Statement": [
            {
                "Action": "s3:GetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Resource": "arn:aws:s3:::2d3ce10a8210d36d6b4d23b822892074complex/*",
                "Sid": "AddPerm"
            }
        ],
        "Version": "2012-10-17"
    }
requester_pays:
    description: Indicates that the requester was successfully charged for the request.
    type: bool
    returned: when O(state=present)
    sample: true
tags:
    description: S3 bucket's tags.
    type: dict
    returned: when O(state=present)
    sample: {
        "Tag1": "tag1",
        "Tag2": "tag2"
    }
versioning:
    description: S3 bucket's versioning configuration.
    type: dict
    returned: when O(state=present)
    sample: {
        "MfaDelete": "Disabled",
        "Versioning": "Enabled"
    }
    contains:
        MfaDelete:
            description: Specifies whether MFA delete is enabled in the bucket versioning configuration.
            returned: when O(state=presnet) and MfaDelete configured on bucket.
            type: str
        Versioning:
            description: The versioning state of the bucket.
            type: str
            returned: always
acl:
    description: S3 bucket's canned ACL.
    type: dict
    returned: when O(state=present).
    sample: "public-read"
object_lock_enabled:
    description: Whether S3 Object Lock is enabled.
    type: bool
    returned: when O(state=present)
    sample: false
public_access_block:
    description: Bucket public access block configuration.
    returned: when O(state=present)
    type: dict
    sample: {
                "PublicAccessBlockConfiguration": {
                    "BlockPublicAcls": true,
                    "BlockPublicPolicy": true,
                    "IgnorePublicAcls": true,
                    "RestrictPublicBuckets": true
                }
            }
    contains:
        PublicAccessBlockConfiguration:
            description: The PublicAccessBlock configuration currently in effect for this Amazon S3 bucket.
            type: dict
            contains:
                BlockPublicAcls:
                    description: Specifies whether Amazon S3 should block public access control lists (ACLs) for this bucket and objects in this bucket.
                    type: bool
                BlockPublicPolicy:
                    description: Specifies whether Amazon S3 should block public bucket policies for this bucket.
                    type: bool
                IgnorePublicAcls:
                    description: Specifies whether Amazon S3 should ignore public ACLs for this bucket and objects in this bucket.
                    type: bool
                RestrictPublicBuckets:
                    description: Specifies whether Amazon S3 should restrict public bucket policies for this bucket.
                    type: bool
accelerate_enabled:
    description: S3 bucket acceleration status.
    type: bool
    returned: O(state=present)
    sample: true
bucket_inventory:
    description: S3 bucket inventory configuration.
    type: list
    returned: when O(state=present)
    sample: [
        {
            "IsEnabled": true,
            "Id": "9c2a337ba5fd64de777f499441f83093-inventory-target",
            "Destination": {
                "S3BucketDestination": {
                    "Bucket": "arn:aws:s3:::9c2a337ba5fd64de777f499441f83093-inventory-target",
                    "Format": "CSV"
                    }
                },
            "IncludedObjectVersions": "All",
            "Schedule": {
                "Frequency": "Daily"
            },
            "OptionalFields": []
        }
        ]
"""

import json
import time
import typing
from typing import Iterator
from typing import List
from typing import NoReturn
from typing import Optional
from typing import Tuple
from typing import cast

if typing.TYPE_CHECKING:
    from ansible_collections.amazon.aws.plugins.module_utils.botocore import ClientType

from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.policy import compare_policies
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.s3 import AnsibleS3Error
from ansible_collections.amazon.aws.plugins.module_utils.s3 import AnsibleS3PermissionsError
from ansible_collections.amazon.aws.plugins.module_utils.s3 import AnsibleS3SupportError
from ansible_collections.amazon.aws.plugins.module_utils.s3 import S3ErrorHandler
from ansible_collections.amazon.aws.plugins.module_utils.s3 import get_s3_bucket_accelerate_configuration
from ansible_collections.amazon.aws.plugins.module_utils.s3 import get_s3_bucket_acl
from ansible_collections.amazon.aws.plugins.module_utils.s3 import get_s3_bucket_encryption
from ansible_collections.amazon.aws.plugins.module_utils.s3 import get_s3_bucket_location
from ansible_collections.amazon.aws.plugins.module_utils.s3 import get_s3_bucket_ownership_controls
from ansible_collections.amazon.aws.plugins.module_utils.s3 import get_s3_bucket_policy
from ansible_collections.amazon.aws.plugins.module_utils.s3 import get_s3_bucket_public_access_block
from ansible_collections.amazon.aws.plugins.module_utils.s3 import get_s3_bucket_request_payment
from ansible_collections.amazon.aws.plugins.module_utils.s3 import get_s3_bucket_tagging
from ansible_collections.amazon.aws.plugins.module_utils.s3 import get_s3_bucket_versioning
from ansible_collections.amazon.aws.plugins.module_utils.s3 import get_s3_object_lock_configuration
from ansible_collections.amazon.aws.plugins.module_utils.s3 import get_s3_waiter
from ansible_collections.amazon.aws.plugins.module_utils.s3 import head_s3_bucket
from ansible_collections.amazon.aws.plugins.module_utils.s3 import list_bucket_inventory_configurations
from ansible_collections.amazon.aws.plugins.module_utils.s3 import merge_tags
from ansible_collections.amazon.aws.plugins.module_utils.s3 import normalize_s3_bucket_acls
from ansible_collections.amazon.aws.plugins.module_utils.s3 import normalize_s3_bucket_public_access
from ansible_collections.amazon.aws.plugins.module_utils.s3 import normalize_s3_bucket_versioning
from ansible_collections.amazon.aws.plugins.module_utils.s3 import s3_acl_to_name
from ansible_collections.amazon.aws.plugins.module_utils.s3 import s3_extra_params
from ansible_collections.amazon.aws.plugins.module_utils.s3 import validate_bucket_name
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters


def handle_bucket_versioning(s3_client: ClientType, module: AnsibleAWSModule, name: str) -> Tuple[bool, Optional[dict]]:
    """
    Manage versioning for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        module (AnsibleAWSModule): The Ansible module object.
        name (str): The name of the bucket to handle versioning for.
    Returns:
        A tuple containing a boolean indicating whether versioning
        was changed and a dictionary containing the updated versioning status.
    """

    versioning = module.params.get("versioning")
    required_versioning = ""

    try:
        versioning_status = get_s3_bucket_versioning(s3_client, name)
    except (AnsibleS3PermissionsError, AnsibleS3SupportError) as e:
        if versioning is not None:
            raise
        module.warn(e.message)
        return False, None

    if versioning is None:
        return False, normalize_s3_bucket_versioning(versioning_status)

    if versioning and versioning_status.get("Status") != "Enabled":
        required_versioning = "Enabled"
    if not versioning and versioning_status.get("Status") == "Enabled":
        required_versioning = "Suspended"

    if not required_versioning:
        return False, normalize_s3_bucket_versioning(versioning_status)

    put_bucket_versioning(s3_client, name, required_versioning)

    wait_versioning_is_applied(s3_client, name, required_versioning)
    versioning_status = get_s3_bucket_versioning(s3_client, name)
    return True, normalize_s3_bucket_versioning(versioning_status)


def handle_bucket_requester_pays(
    s3_client: ClientType, module: AnsibleAWSModule, name: str
) -> Tuple[bool, Optional[dict]]:
    """
    Manage requester pays setting for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        module (AnsibleAWSModule): The Ansible module object.
        name (str): The name of the bucket to handle requester pays setting for.
    Returns:
        A tuple containing a boolean indicating whether requester pays setting
        was changed and a boolean containing the updated requester pays status.
    """

    requester_pays = module.params.get("requester_pays")

    try:
        requester_pays_status = get_s3_bucket_request_payment(s3_client, name)
    except (AnsibleS3PermissionsError, AnsibleS3SupportError) as e:
        if requester_pays is not None:
            raise
        module.warn(e.message)
        return False, None

    requester_pays_status = bool(requester_pays_status == "Requester")

    if requester_pays is None:
        return False, requester_pays_status
    if requester_pays == requester_pays_status:
        return False, requester_pays_status

    payer = "Requester" if requester_pays else "BucketOwner"
    put_bucket_request_payment(s3_client, name, payer)
    requester_pays_status = wait_payer_is_applied(s3_client, name, payer, should_fail=False)
    if requester_pays_status is None:
        put_bucket_request_payment(s3_client, name, payer)
        requester_pays_status = wait_payer_is_applied(s3_client, name, payer, should_fail=True)

    return True, requester_pays


def handle_bucket_public_access_config(
    s3_client: ClientType, module: AnsibleAWSModule, name: str
) -> Tuple[bool, Optional[dict]]:
    """
    Manage public access configuration for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        module (AnsibleAWSModule): The Ansible module object.
        name (str): The name of the bucket to handle public access configuration for.
    Returns:
        A tuple containing a boolean indicating whether public access configuration
        was changed and a dictionary containing the updated public access configuration.
    """

    public_access = module.params.get("public_access")
    delete_public_access = module.params.get("delete_public_access")

    try:
        current_public_access = get_s3_bucket_public_access_block(s3_client, name)
    except (AnsibleS3PermissionsError, AnsibleS3SupportError) as e:
        if public_access is not None:
            raise
        module.warn(e.message)
        return False, None

    # -- Delete public access block if necessary
    if delete_public_access:
        if not current_public_access:
            return False, None
        delete_s3_bucket_public_access(s3_client, name)
        return True, None

    # -- Create / Update public access block
    # Short circuit comparisons if no change was requested
    if public_access is None:
        return False, normalize_s3_bucket_public_access(current_public_access)

    camel_public_block = snake_dict_to_camel_dict(public_access, capitalize_first=True)
    # No change needed
    if current_public_access == camel_public_block:
        return False, normalize_s3_bucket_public_access(current_public_access)

    # Make a change
    put_s3_bucket_public_access(s3_client, name, camel_public_block)
    return True, normalize_s3_bucket_public_access(camel_public_block)


def handle_bucket_policy(s3_client: ClientType, module: AnsibleAWSModule, name: str) -> Tuple[bool, Optional[dict]]:
    """
    Manage bucket policy for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        module (AnsibleAWSModule): The Ansible module object.
        name (str): The name of the bucket to handle the policy for.
    Returns:
        A tuple containing a boolean indicating whether the bucket policy
        was changed and a dictionary containing the updated bucket policy.
    """

    policy = module.params.get("policy")
    try:
        current_policy = get_s3_bucket_policy(s3_client, name)
    except (AnsibleS3PermissionsError, AnsibleS3SupportError) as e:
        if policy is not None:
            raise
        module.warn(e.message)
        return False, None

    if policy is None:
        return False, current_policy

    if isinstance(policy, str):
        try:
            policy = json.loads(policy)
        except ValueError as e:
            raise AnsibleS3Error(exception=e, message="Unable to parse bucket policy") from e

    if not policy:
        if not current_policy:
            return False, current_policy

        delete_s3_bucket_policy(s3_client, name)
        return True, wait_policy_is_applied(s3_client, name, policy)

    if not compare_policies(current_policy, policy):
        return False, current_policy

    put_s3_bucket_policy(s3_client, name, policy)
    current_policy = wait_policy_is_applied(s3_client, name, policy, should_fail=False)
    if current_policy is None:
        # As for request payement, it happens quite a lot of times that the put request was not taken into
        # account, so we retry one more time
        put_s3_bucket_policy(s3_client, name, policy)
        current_policy = wait_policy_is_applied(s3_client, name, policy, should_fail=True)

    return True, current_policy


def handle_bucket_tags(s3_client: ClientType, module: AnsibleAWSModule, name: str) -> Tuple[bool, Optional[dict]]:
    """
    Manage tags for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        module (AnsibleAWSModule): The Ansible module object.
        name (str): The name of the bucket to handle tags for.
    Returns:
        A tuple containing a boolean indicating whether tags were changed
        and a dictionary containing the updated tags.
    """

    tags = module.params.get("tags")
    purge_tags = cast(bool, module.params.get("purge_tags"))

    try:
        current_tags_dict = get_s3_bucket_tagging(s3_client, name)
    except (AnsibleS3PermissionsError, AnsibleS3SupportError) as e:
        if tags is not None:
            raise
        module.warn(e.message)
        return False, None

    if tags is None:
        return False, current_tags_dict

    updated_tags = merge_tags(current_tags_dict, tags, purge_tags)

    if current_tags_dict == updated_tags:
        return False, current_tags_dict

    if not updated_tags:
        delete_s3_bucket_tagging(s3_client, name)
    else:
        put_s3_bucket_tagging(s3_client, name, updated_tags)
    current_tags_dict = wait_tags_are_applied(s3_client, name, updated_tags)

    return True, updated_tags


def _handle_remove_bucket_encryption(
    s3_client: ClientType, name: str, current_encryption: Optional[dict]
) -> Tuple[bool, Optional[dict]]:
    current_encryption_algorithm = current_encryption.get("SSEAlgorithm") if current_encryption else None

    if current_encryption_algorithm is None:
        return False, current_encryption

    delete_s3_bucket_encryption(s3_client, name)
    current_encryption = wait_encryption_is_applied(s3_client, name, None)

    return True, current_encryption


def _handle_bucket_encryption(
    s3_client: ClientType,
    name: str,
    current_encryption: Optional[dict],
    encryption: Optional[str],
    encryption_key_id: Optional[str],
) -> Tuple[bool, Optional[dict]]:
    if encryption is None:
        return False, current_encryption

    current_encryption_algorithm = cast(dict, current_encryption).get("SSEAlgorithm") if current_encryption else None
    current_encryption_key = cast(dict, current_encryption).get("KMSMasterKeyID") if current_encryption else None

    if encryption == current_encryption_algorithm:
        # Non KMS is simple
        if encryption != "aws:kms":
            return False, current_encryption
        # When working with KMS, we also need to check the Key
        if current_encryption_key == encryption_key_id:
            return False, current_encryption

    expected_encryption = {"SSEAlgorithm": encryption}
    if encryption_key_id is not None:
        expected_encryption["KMSMasterKeyID"] = encryption_key_id

    current_encryption = put_bucket_encryption_with_retry(s3_client, name, expected_encryption)
    return True, current_encryption


def _handle_bucket_key_encryption(
    s3_client: ClientType, name, current_encryption, bucket_key_enabled
) -> Tuple[bool, Optional[dict]]:
    if bucket_key_enabled is None:
        return False, current_encryption

    current_encryption_algorithm = current_encryption.get("SSEAlgorithm") if current_encryption else None

    if current_encryption_algorithm != "aws:kms":
        raise AnsibleS3Error(
            f'Unable to set bucket key: current encryption algorith ("{current_encryption_algorithm}") is not "aws:kms"'
        )

    if get_bucket_key_enabled(s3_client, name) == bucket_key_enabled:
        return False, current_encryption

    expected_encryption = bool(bucket_key_enabled)
    put_bucket_key_with_retry(s3_client, name, expected_encryption)
    return True, get_bucket_encryption(s3_client, name)


def handle_bucket_encryption(s3_client: ClientType, module: AnsibleAWSModule, name: str) -> Tuple[bool, Optional[dict]]:
    """
    Manage encryption settings for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        module (AnsibleAWSModule): The Ansible module object.
        name (str): The name of the bucket to handle encryption for.
    Returns:
        A tuple containing a boolean indicating whether encryption settings
        were changed and a dictionary containing the updated encryption settings.
    """
    encryption = module.params.get("encryption")
    encryption_key_id = module.params.get("encryption_key_id")
    bucket_key_enabled = module.params.get("bucket_key_enabled")

    try:
        current_encryption = get_bucket_encryption(s3_client, name)
    except (AnsibleS3PermissionsError, AnsibleS3SupportError) as e:
        if encryption is not None:
            raise
        module.warn(e.message)
        return False, None

    if encryption == "none":
        return _handle_remove_bucket_encryption(s3_client, name, current_encryption)

    changed, current_encryption = _handle_bucket_encryption(
        s3_client, name, current_encryption, encryption, encryption_key_id
    )
    bk_changed, current_encryption = _handle_bucket_key_encryption(
        s3_client, name, current_encryption, bucket_key_enabled
    )
    changed |= bk_changed
    return changed, current_encryption


def handle_bucket_ownership(s3_client: ClientType, module: AnsibleAWSModule, name: str) -> Tuple[bool, Optional[str]]:
    """
    Manage ownership settings for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        module (AnsibleAWSModule): The Ansible module object.
        name (str): The name of the bucket to handle ownership for.
    Returns:
        A tuple containing a boolean indicating whether ownership settings were changed
        and a dictionary containing the updated ownership settings.
    """

    delete_object_ownership = module.params.get("delete_object_ownership")
    object_ownership = module.params.get("object_ownership")

    try:
        bucket_ownership = get_bucket_ownership_cntrl(s3_client, name)
    except (AnsibleS3PermissionsError, AnsibleS3SupportError) as e:
        if delete_object_ownership or object_ownership is not None:
            raise
        module.warn(e.message)
        return False, None

    if delete_object_ownership:
        if bucket_ownership is None:
            return False, None
        delete_bucket_ownership(s3_client, name)
        return True, None

    if object_ownership is None:
        return False, bucket_ownership
    if bucket_ownership == object_ownership:
        return False, bucket_ownership

    put_bucket_ownership(s3_client, name, object_ownership)
    return True, object_ownership


def handle_bucket_acl(
    s3_client: ClientType, module: AnsibleAWSModule, name: str
) -> Tuple[bool, Optional[str], Optional[dict]]:
    """
    Manage Access Control List (ACL) for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        module (AnsibleAWSModule): The Ansible module object.
        name (str): The name of the bucket to handle ACL for.
    Returns:
        A tuple containing a boolean indicating whether ACL was changed and a dictionary containing the updated ACL.
    """

    acl = module.params.get("acl")

    try:
        bucket_acl = get_s3_bucket_acl(s3_client, name)
        current_name = s3_acl_to_name(bucket_acl)
    except (AnsibleS3PermissionsError, AnsibleS3SupportError) as e:
        if acl is not None:
            raise
        module.warn(e.message)
        return False, None, None

    if acl is None or acl == current_name:
        return False, current_name, bucket_acl

    put_s3_bucket_acl(s3_client, name, acl)
    new_acl = get_s3_bucket_acl(s3_client, name)
    new_name = s3_acl_to_name(new_acl)
    return True, new_name, new_acl


def handle_bucket_object_lock(s3_client: ClientType, module: AnsibleAWSModule, name: str) -> bool:
    """
    Manage object lock configuration for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        module (AnsibleAWSModule): The Ansible module object.
        name (str): The name of the bucket to handle object lock for.
    Returns:
        The updated object lock configuration.
    """

    object_lock_enabled = module.params.get("object_lock_enabled")

    try:
        object_lock_status = get_bucket_object_lock_enabled(s3_client, name)
    except (AnsibleS3PermissionsError, AnsibleS3SupportError) as e:
        if object_lock_enabled is not None:
            raise
        module.warn(e.message)
        return False

    if object_lock_enabled is None:
        return object_lock_status

    if not object_lock_enabled and object_lock_status:
        raise AnsibleS3Error("Disabling object lock for existing buckets is not supported")
    if object_lock_enabled and not object_lock_status:
        raise AnsibleS3Error("Enabling object lock for existing buckets is not supported")

    return object_lock_status


def handle_bucket_accelerate(s3_client: ClientType, module: AnsibleAWSModule, name: str) -> Tuple[bool, Optional[bool]]:
    """
    Manage transfer accelerate for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        module (AnsibleAWSModule): The Ansible module object.
        name (str): The name of the bucket to handle transfer accelerate for.
    Returns:
        A tuple containing a boolean indicating whether transfer accelerate setting was changed
        and a boolean indicating the transfer accelerate status.
    """

    accelerate_enabled = module.params.get("accelerate_enabled")

    try:
        accelerate_status = get_bucket_accelerate_status(s3_client, name)
    except (AnsibleS3PermissionsError, AnsibleS3SupportError) as e:
        if accelerate_enabled is not None:
            raise
        module.warn(e.message)
        return False, None

    if accelerate_enabled is None:
        return False, accelerate_status
    if accelerate_enabled == accelerate_status:
        return False, accelerate_status

    if not accelerate_enabled:
        delete_bucket_accelerate_configuration(s3_client, name)
        return True, False

    put_bucket_accelerate_configuration(s3_client, name)

    return True, True


def handle_bucket_object_lock_retention(
    s3_client: ClientType, module: AnsibleAWSModule, name: str
) -> Tuple[bool, Optional[dict]]:
    """
    Manage object lock retention configuration for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        module (AnsibleAWSModule): The Ansible module object.
        name (str): The name of the bucket to handle object lock for.
    Returns:
        A tuple containing a boolean indicating whether the bucket object lock
        retention configuration was changed and a dictionary containing the change.
    """

    object_lock_enabled = module.params.get("object_lock_enabled")
    object_lock_default_retention = module.params.get("object_lock_default_retention")

    try:
        if object_lock_enabled:
            object_lock_configuration_status = get_object_lock_configuration(s3_client, name)
        else:
            object_lock_configuration_status = {}
    except (AnsibleS3PermissionsError, AnsibleS3SupportError) as e:
        if object_lock_default_retention is not None:
            raise
        module.warn(e.message)
        return False, None

    if object_lock_default_retention is None:
        return False, object_lock_configuration_status

    if not object_lock_default_retention and object_lock_configuration_status:
        raise AnsibleS3Error("Removing object lock default retention is not supported")

    conf = scrub_none_parameters(snake_dict_to_camel_dict(object_lock_default_retention, capitalize_first=True))
    if object_lock_configuration_status == conf:
        return False, object_lock_configuration_status

    put_object_lock_configuration(s3_client, name, conf)
    return True, object_lock_default_retention


def handle_bucket_inventory(s3_client: ClientType, module: AnsibleAWSModule, name: str) -> Tuple[bool, Optional[list]]:
    """
    Manage inventory configuration for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        module (AnsibleAWSModule): The Ansible module object.
        name (str): The name of the bucket to handle inventory for.
    Returns:
        A tuple containing a boolean indicating whether inventory settings were changed
        and a dictionary containing the updated inventory.
    """
    declared_inventories = module.params.get("inventory")

    try:
        current_inventories = list_bucket_inventory_configurations(s3_client, name)
        present_inventories = {i["Id"]: i for i in current_inventories}
    except (AnsibleS3PermissionsError, AnsibleS3SupportError) as e:
        if declared_inventories is not None:
            raise
        module.warn(e.message)
        return False, None

    if declared_inventories is None:
        return (False, current_inventories)

    declared_inventories = cast(list, declared_inventories)
    bucket_changed = False
    results = []

    for declared_inventory in declared_inventories:
        camel_destination = snake_dict_to_camel_dict(declared_inventory.get("destination", {}), True)
        declared_inventory_api = {
            "IsEnabled": True,
            "Id": declared_inventory.get("id"),
            "Destination": {"S3BucketDestination": {k: v for k, v in camel_destination.items() if v is not None}},
            "IncludedObjectVersions": declared_inventory.get("included_object_versions"),
            "Schedule": {"Frequency": declared_inventory.get("schedule")},
            "OptionalFields": [],
        }
        for field in declared_inventory.get("optional_fields", []):
            declared_inventory_api["OptionalFields"].append(field)
        if declared_inventory.get("filter") is not None:
            declared_inventory_api["Filter"] = {"Prefix": declared_inventory.get("filter")}

        present_inventory = present_inventories.pop(declared_inventory_api["Id"], None)

        if declared_inventory_api != present_inventory:
            put_bucket_inventory(s3_client, name, declared_inventory_api)
            bucket_changed = True

        results.append(declared_inventory_api)

    for inventory_id in present_inventories.keys():
        delete_bucket_inventory(s3_client, name, inventory_id)
        bucket_changed = True

    return bucket_changed, results


def create_or_update_bucket(s3_client: ClientType, module: AnsibleAWSModule) -> NoReturn:
    """
    Create or update an S3 bucket along with its associated configurations.
    This function creates a new S3 bucket if it does not already exist, and updates its configurations,
    such as versioning, requester pays, public access block configuration, policy, tags, encryption, bucket ownership,
    ACL, and object lock settings. It returns whether any changes were made and the updated configurations.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        module (AnsibleAWSModule): The Ansible module object.
    Returns:
        None
    """
    name = cast(str, module.params.get("name"))
    object_lock_enabled = module.params.get("object_lock_enabled")
    location = get_s3_bucket_location(module)

    changed = False
    result: dict = {}

    bucket_is_present = bucket_exists(s3_client, name)

    if not bucket_is_present:
        changed = create_bucket(s3_client, name, location, object_lock_enabled)
        waiter = get_s3_waiter(s3_client, "bucket_exists")
        S3ErrorHandler.common_error_handler(f"wait for bucket f{name} to be created")(waiter.wait)(Bucket=name)

    # Versioning
    versioning_changed, versioning_result = handle_bucket_versioning(s3_client, module, name)
    result["versioning"] = versioning_result

    # Requester pays
    requester_pays_changed, requester_pays_result = handle_bucket_requester_pays(s3_client, module, name)
    result["requester_pays"] = requester_pays_result

    # Public access clock configuration
    public_access_config_changed, public_access_config_result = handle_bucket_public_access_config(
        s3_client, module, name
    )
    result["public_access_block"] = public_access_config_result

    # Policy
    policy_changed, current_policy = handle_bucket_policy(s3_client, module, name)
    result["policy"] = current_policy

    # Tags
    tags_changed, current_tags_dict = handle_bucket_tags(s3_client, module, name)
    result["tags"] = current_tags_dict

    # Encryption
    encryption_changed, current_encryption = handle_bucket_encryption(s3_client, module, name)
    result["encryption"] = current_encryption

    # -- Bucket ownership
    bucket_ownership_changed, object_ownership_result = handle_bucket_ownership(s3_client, module, name)
    result["object_ownership"] = object_ownership_result

    # -- Bucket ACL
    bucket_acl_changed, bucket_acl_result, acl_info = handle_bucket_acl(s3_client, module, name)
    result["acl"] = bucket_acl_result
    result["acl_grants"] = normalize_s3_bucket_acls(acl_info)

    # -- Transfer Acceleration
    bucket_accelerate_changed, bucket_accelerate_result = handle_bucket_accelerate(s3_client, module, name)
    result["accelerate_enabled"] = bucket_accelerate_result

    # TODO - MERGE handle_bucket_object_lock and handle_bucket_object_lock_retention
    # -- Object Lock
    bucket_object_lock_result = handle_bucket_object_lock(s3_client, module, name)
    result["object_lock_enabled"] = bucket_object_lock_result

    # -- Object Lock Default Retention
    bucket_object_lock_retention_changed, bucket_object_lock_retention_result = handle_bucket_object_lock_retention(
        s3_client, module, name
    )
    result["object_lock_default_retention"] = bucket_object_lock_retention_result
    # -- Inventory
    bucket_inventory_changed, bucket_inventory_result = handle_bucket_inventory(s3_client, module, name)
    result["bucket_inventory"] = bucket_inventory_result

    # Module exit
    changed = (
        changed
        or versioning_changed
        or requester_pays_changed
        or public_access_config_changed
        or policy_changed
        or tags_changed
        or encryption_changed
        or bucket_ownership_changed
        or bucket_acl_changed
        or bucket_accelerate_changed
        or bucket_object_lock_retention_changed
        or bucket_inventory_changed
    )
    module.exit_json(changed=changed, name=name, **result)


def bucket_exists(s3_client: ClientType, bucket_name: str) -> bool:
    """
    Checks if a given bucket exists in an AWS S3 account.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the bucket to check for existence.
    Returns:
        True if the bucket exists, False otherwise.
    """
    return bool(head_s3_bucket(s3_client, bucket_name))


@S3ErrorHandler.common_error_handler("create S3 bucket")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["OperationAborted"])
def _create_bucket(s3_client: ClientType, **params) -> bool:
    try:
        s3_client.create_bucket(**params)
        return True
    except is_boto3_error_code("BucketAlreadyOwnedByYou"):
        # We should never get here since we check the bucket presence before calling the create_or_update_bucket
        # method. However, the AWS Api sometimes fails to report bucket presence, so we catch this exception
        return False


def create_bucket(
    s3_client: ClientType, bucket_name: str, location: str, object_lock_enabled: Optional[bool] = False
) -> bool:
    """
    Create an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the bucket to create.
        location (str): The AWS region where the bucket should be created. If None, it defaults to "us-east-1".
        object_lock_enabled (bool): Whether to enable object lock for the bucket. Defaults to False.
    Returns:
        True if the bucket was successfully created, False otherwise.
    """
    params: dict = {"Bucket": bucket_name}

    configuration: dict = {}
    if location not in ("us-east-1", None):
        configuration["LocationConstraint"] = location

    if configuration:
        params["CreateBucketConfiguration"] = configuration

    if object_lock_enabled is not None:
        params["ObjectLockEnabledForBucket"] = object_lock_enabled

    return _create_bucket(s3_client, **params)


def get_object_lock_configuration(s3_client: ClientType, bucket_name: str) -> Optional[dict]:
    """
    Get the object lock default retention configuration for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        Object lock default retention configuration dictionary.
    """
    result = get_s3_object_lock_configuration(s3_client, bucket_name)
    return result.get("Rule", {}).get("DefaultRetention", {})


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_object_lock_configuration(s3_client: ClientType, bucket_name: str, object_lock_default_retention: str) -> None:
    """
    Set tags for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        object_lock_default_retention (dict): A dictionary containing the object
        lock default retention configuration to be set on the bucket.
    Returns:
        None
    """
    conf = {"ObjectLockEnabled": "Enabled", "Rule": {"DefaultRetention": object_lock_default_retention}}
    s3_client.put_object_lock_configuration(Bucket=bucket_name, ObjectLockConfiguration=conf)


@S3ErrorHandler.common_error_handler("set bucket acceleration configuration")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_bucket_accelerate_configuration(s3_client: ClientType, bucket_name: str) -> None:
    """
    Enable transfer accelerate for the S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        None
    """
    s3_client.put_bucket_accelerate_configuration(Bucket=bucket_name, AccelerateConfiguration={"Status": "Enabled"})


@S3ErrorHandler.deletion_error_handler("set bucket acceleration configuration")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def delete_bucket_accelerate_configuration(s3_client: ClientType, bucket_name: str) -> None:
    """
    Disable transfer accelerate for the S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        None
    """

    s3_client.put_bucket_accelerate_configuration(Bucket=bucket_name, AccelerateConfiguration={"Status": "Suspended"})


def get_bucket_accelerate_status(s3_client: ClientType, bucket_name: str) -> bool:
    """
    Get transfer accelerate status of the S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        Transfer accelerate status of the S3 bucket.
    """
    accelerate_configuration = get_s3_bucket_accelerate_configuration(s3_client, bucket_name)
    return accelerate_configuration.get("Status") == "Enabled"


@S3ErrorHandler.common_error_handler("set bucket inventory configuration")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_bucket_inventory(s3_client: ClientType, bucket_name: str, inventory: dict) -> None:
    """
    Set inventory settings for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        tags (dict): A dictionary containing the inventory settings to be set on the bucket.
    Returns:
        None
    """
    try:
        s3_client.put_bucket_inventory_configuration(
            Bucket=bucket_name, InventoryConfiguration=inventory, Id=inventory.get("Id")
        )
    except is_boto3_error_code("InvalidS3DestinationBucket") as e:
        raise AnsibleS3Error("Invalid destination bucket ARN") from e


@S3ErrorHandler.common_error_handler("set bucket tagging")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_s3_bucket_tagging(s3_client: ClientType, bucket_name: str, tags: dict) -> None:
    """
    Set tags for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        tags (dict): A dictionary containing the tags to be set on the bucket.
    Returns:
        None
    """
    s3_client.put_bucket_tagging(Bucket=bucket_name, Tagging={"TagSet": ansible_dict_to_boto3_tag_list(tags)})


@S3ErrorHandler.deletion_error_handler("delete bucket inventory configuration")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def delete_bucket_inventory(s3_client: ClientType, bucket_name: str, inventory_id: str) -> None:
    """
    Delete the inventory settings for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        id (str): The ID used to identify the inventory configuration
    Returns:
        None
    """
    s3_client.delete_bucket_inventory_configuration(Bucket=bucket_name, Id=inventory_id)


@S3ErrorHandler.common_error_handler("set bucket policy")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_s3_bucket_policy(s3_client: ClientType, bucket_name: str, policy: dict) -> None:
    """
    Set the policy for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        policy (dict): A dictionary containing the policy to be set on the bucket.
    Returns:
        None
    """
    s3_client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))


@S3ErrorHandler.common_error_handler("set bucket request payment configuration")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_bucket_request_payment(s3_client: ClientType, bucket_name: str, payer: str) -> None:
    """
    Set the request payment configuration for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        payer (str): The entity responsible for charges related to fulfilling the request.
    Returns:
        None
    """
    s3_client.put_bucket_request_payment(Bucket=bucket_name, RequestPaymentConfiguration={"Payer": payer})


@S3ErrorHandler.common_error_handler("set bucket versioning configuation")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_bucket_versioning(s3_client: ClientType, bucket_name: str, required_versioning: str) -> None:
    """
    Set the versioning configuration for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        required_versioning (str): The desired versioning state for the bucket ("Enabled", "Suspended").
    Returns:
        None
    """
    s3_client.put_bucket_versioning(Bucket=bucket_name, VersioningConfiguration={"Status": required_versioning})


def get_bucket_object_lock_enabled(s3_client: ClientType, bucket_name: str) -> bool:
    """
    Retrieve the object lock configuration status for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        True if object lock is enabled for the bucket, False otherwise.
    """
    object_lock_configuration = get_s3_object_lock_configuration(s3_client, bucket_name)
    return object_lock_configuration.get("ObjectLockEnabled") == "Enabled"


def get_bucket_encryption(s3_client: ClientType, bucket_name: str) -> Optional[dict]:
    """
    Retrieve the encryption configuration for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        Encryption configuration of the bucket.
    """
    try:
        result = get_s3_bucket_encryption(s3_client, bucket_name)
        return result.get("Rules", [])[0].get("ApplyServerSideEncryptionByDefault")
    except (IndexError, KeyError):
        return None


def get_bucket_key_enabled(s3_client: ClientType, bucket_name: str) -> Optional[bool]:
    """
    Retrieve the status of server-side encryption for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        Whether or not if server-side encryption is enabled for the bucket.
    """
    try:
        result = get_s3_bucket_encryption(s3_client, bucket_name)
        return result.get("Rules", [])[0].get("BucketKeyEnabled")
    except (IndexError, KeyError):
        return None


def put_bucket_encryption_with_retry(s3_client: ClientType, name: str, expected_encryption: dict) -> dict:
    """
    Set the encryption configuration for an S3 bucket with retry logic.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        name (str): The name of the S3 bucket.
        expected_encryption (dict): A dictionary containing the expected encryption configuration.
    Returns:
        Updated encryption configuration of the bucket.
    """
    max_retries = 3
    for retries in range(1, max_retries + 1):
        put_bucket_encryption(s3_client, name, expected_encryption)
        current_encryption = wait_encryption_is_applied(
            s3_client, name, expected_encryption, should_fail=(retries == max_retries), retries=5
        )
        if current_encryption == expected_encryption:
            return current_encryption

    # We shouldn't get here, the only time this should happen is if
    # current_encryption != expected_encryption and retries == max_retries
    raise AnsibleS3Error("Failed to set bucket encryption configuration")


@S3ErrorHandler.common_error_handler("set bucket encryption")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_bucket_encryption(s3_client: ClientType, bucket_name: str, encryption: dict) -> None:
    """
    Set the encryption configuration for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        encryption (dict): A dictionary containing the encryption configuration.
    Returns:
        None
    """
    server_side_encryption_configuration = {"Rules": [{"ApplyServerSideEncryptionByDefault": encryption}]}
    s3_client.put_bucket_encryption(
        Bucket=bucket_name, ServerSideEncryptionConfiguration=server_side_encryption_configuration
    )


def put_bucket_key_with_retry(s3_client: ClientType, name: str, expected_encryption: bool) -> None:
    """
    Set the status of server-side encryption for an S3 bucket.
    Parameters:
        module (AnsibleAWSModule): The Ansible module object.
        s3_client (boto3.client): The Boto3 S3 client object.
        name (str): The name of the S3 bucket.
        expected_encryption (bool): The expected status of server-side encryption using AWS KMS.
    Returns:
        The updated status of server-side encryption using AWS KMS for the bucket.
    """
    max_retries = 3
    for retries in range(1, max_retries + 1):
        put_bucket_key(s3_client, name, expected_encryption)
        try:
            wait_bucket_key_is_applied(s3_client, name, expected_encryption, retries=5)
            return
        except AnsibleS3Error:
            if retries == max_retries:
                raise
            pass

    # We shouldn't get here, the only time this should happen is if
    # current_encryption != expected_encryption and retries == max_retries
    raise AnsibleS3Error("Failed to set bucket key")


@S3ErrorHandler.common_error_handler("set bucket key based encryption")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_bucket_key(s3_client: ClientType, bucket_name: str, encryption: bool) -> None:
    """
    Set the status of server-side encryption for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        encryption (bool): The status of server-side encryption using AWS KMS.
    Returns:
        None
    """
    # server_side_encryption_configuration ={'Rules': [{'BucketKeyEnabled': encryption}]}
    encryption_status = get_s3_bucket_encryption(s3_client, bucket_name)
    encryption_status["Rules"][0]["BucketKeyEnabled"] = encryption
    s3_client.put_bucket_encryption(Bucket=bucket_name, ServerSideEncryptionConfiguration=encryption_status)


@S3ErrorHandler.deletion_error_handler("delete bucket tagging")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def delete_s3_bucket_tagging(s3_client: ClientType, bucket_name: str) -> None:
    """
    Delete the tagging configuration of an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        None
    """
    s3_client.delete_bucket_tagging(Bucket=bucket_name)


@S3ErrorHandler.deletion_error_handler("delete bucket encryption")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def delete_s3_bucket_encryption(s3_client: ClientType, bucket_name: str) -> None:
    """
    Delete the encryption configuration of an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        None
    """
    s3_client.delete_bucket_encryption(Bucket=bucket_name)


@S3ErrorHandler.deletion_error_handler("delete bucket")
@AWSRetry.jittered_backoff(max_delay=240, catch_extra_error_codes=["OperationAborted"])
def delete_bucket(s3_client: ClientType, bucket_name: str) -> None:
    """
    Delete an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        None
    """
    s3_client.delete_bucket(Bucket=bucket_name)


@S3ErrorHandler.common_error_handler("set public access block configuration")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_s3_bucket_public_access(s3_client: ClientType, bucket_name: str, public_acces: dict) -> None:
    """
    Put new public access block to S3 bucket
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        public_access (dict): The public access block configuration.
    Returns:
        None
    """
    s3_client.put_public_access_block(Bucket=bucket_name, PublicAccessBlockConfiguration=public_acces)


@S3ErrorHandler.common_error_handler("set bucket ACL")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_s3_bucket_acl(s3_client: ClientType, bucket_name: str, acl: str) -> None:
    """
    Applies a canned ACL to an S3 bucket
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        acl (str): The ACL
    Returns:
        None
    """
    s3_client.put_bucket_acl(Bucket=bucket_name, ACL=acl)


@S3ErrorHandler.deletion_error_handler("delete bucket policy")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def delete_s3_bucket_policy(s3_client: ClientType, bucket_name: str) -> None:
    """
    Delete policy from S3 bucket
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        None
    """
    s3_client.delete_bucket_policy(Bucket=bucket_name)


@S3ErrorHandler.deletion_error_handler("delete public access block configuration")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def delete_s3_bucket_public_access(s3_client: ClientType, bucket_name: str) -> None:
    """
    Delete public access block from S3 bucket
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        None
    """
    s3_client.delete_public_access_block(Bucket=bucket_name)


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def delete_bucket_ownership(s3_client: ClientType, bucket_name: str) -> None:
    """
    Delete bucket ownership controls from S3 bucket
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        None
    """
    s3_client.delete_bucket_ownership_controls(Bucket=bucket_name)


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_bucket_ownership(s3_client: ClientType, bucket_name: str, target: str) -> None:
    """
    Put bucket ownership controls for S3 bucket
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        None
    """
    s3_client.put_bucket_ownership_controls(
        Bucket=bucket_name, OwnershipControls={"Rules": [{"ObjectOwnership": target}]}
    )


def wait_policy_is_applied(
    s3_client: ClientType, bucket_name: str, expected_policy: dict, should_fail: bool = True
) -> Optional[dict]:
    """
    Wait for a bucket policy to be applied to an S3 bucket.
    Parameters:
        module (AnsibleAWSModule): The Ansible module object.
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        expected_policy (dict): The expected bucket policy.
        should_fail (bool): Flag indicating whether to fail if the policy is not applied within the expected time. Default is True.
    Returns:
        The current policy applied to the bucket, or None if the policy failed to apply within the expected time.
    """
    for dummy in range(0, 12):
        current_policy = get_s3_bucket_policy(s3_client, bucket_name)
        if not compare_policies(current_policy, expected_policy):
            return current_policy
        time.sleep(5)

    if should_fail:
        raise AnsibleS3Error(message="Bucket policy failed to apply in the expected time")
    return None


def wait_payer_is_applied(
    s3_client: ClientType, bucket_name: str, expected_payer: str, should_fail=True
) -> Optional[str]:
    """
    Wait for the requester pays setting to be applied to an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        expected_payer (bool): The expected status of the requester pays setting.
        should_fail (bool): Flag indicating whether to fail if the setting is not applied within the expected time. Default is True.
    Returns:
        The current status of the requester pays setting applied to the bucket.
    """
    for dummy in range(0, 12):
        requester_pays_status = get_s3_bucket_request_payment(s3_client, bucket_name)
        if requester_pays_status == expected_payer:
            return requester_pays_status
        time.sleep(5)

    if should_fail:
        raise AnsibleS3Error(message="Bucket request payer setting failed to apply in the expected time")
    return None


def wait_encryption_is_applied(
    s3_client: ClientType,
    bucket_name: str,
    expected_encryption: Optional[dict],
    should_fail: bool = True,
    retries: int = 12,
) -> Optional[dict]:
    """
    Wait for the encryption setting to be applied to an S3 bucket.
    Parameters:
        module (AnsibleAWSModule): The Ansible module object.
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        expected_encryption(dict): The expected encryption setting.
        should_fail (bool): Flag indicating whether to fail if the setting is not applied within the expected time. Default is True.
        retries (int): The number of retries to attempt. Default is 12.
    Returns:
        The current encryption setting applied to the bucket.
    """
    for dummy in range(0, retries):
        encryption = get_bucket_encryption(s3_client, bucket_name)
        if encryption != expected_encryption:
            time.sleep(5)
        else:
            return encryption

    if should_fail:
        raise AnsibleS3Error("Bucket encryption failed to apply in the expected time")

    return encryption


def wait_bucket_key_is_applied(
    s3_client: ClientType, bucket_name: str, expected_encryption: bool, retries: int = 12
) -> None:
    """
    Wait for the bucket key setting to be applied to an S3 bucket.
    Parameters:
        module (AnsibleAWSModule): The Ansible module object.
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        expected_encryption (bool): The expected bucket key setting.
        should_fail (bool): Flag indicating whether to fail if the setting is not applied within the expected time. Default is True.
        retries (int): The number of retries to attempt. Default is 12.
    Returns:
        The current bucket key setting applied to the bucket.
    """
    extension = "enabled" if expected_encryption else "disabled"
    waiter_name = f"bucket_key_encryption_{extension}"
    waiter = get_s3_waiter(s3_client, waiter_name)
    S3ErrorHandler.common_error_handler(f"wait for bucket key encryption to be {extension}")(waiter.wait)(
        Bucket=bucket_name
    )


def wait_versioning_is_applied(s3_client: ClientType, bucket_name: str, required_versioning: str) -> None:
    """
    Wait for the versioning setting to be applied to an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        required_versioning (dict): The required versioning status.
    Returns:
        The current versioning status applied to the bucket.
    """
    waiter_name = "bucket_versioning_enabled" if required_versioning == "Enabled" else "bucket_versioning_suspended"
    waiter = get_s3_waiter(s3_client, waiter_name)
    S3ErrorHandler.common_error_handler(f"wait for bucket versioning to be {required_versioning}")(waiter.wait)(
        Bucket=bucket_name
    )


def wait_tags_are_applied(s3_client: ClientType, bucket_name: str, expected_tags_dict: dict) -> dict:
    """
    Wait for the tags to be applied to an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        expected_tags_dict (dict): The expected tags dictionary.
    Returns:
        The current tags dictionary applied to the bucket.
    """
    for dummy in range(0, 12):
        current_tags_dict = get_s3_bucket_tagging(s3_client, bucket_name)
        if current_tags_dict == expected_tags_dict:
            return current_tags_dict
        time.sleep(5)

    raise AnsibleS3Error(message="Bucket tags failed to apply in the expected time")


def get_bucket_ownership_cntrl(s3_client, bucket_name: str) -> Optional[str]:
    """
    Get the current bucket ownership controls.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
      The object ownership rule
    """
    result = get_s3_bucket_ownership_controls(s3_client, bucket_name)
    if not result:
        return None
    try:
        return result["Rules"][0]["ObjectOwnership"]
    except (KeyError, IndexError) as e:
        raise AnsibleS3SupportError(message="Failed to parse bucket object ownership settings") from e


def paginated_list(s3_client: ClientType, **pagination_params) -> Iterator[List[str]]:
    """
    Paginate through the list of objects in an S3 bucket.
    This function yields the keys of objects in the S3 bucket, paginating through the results.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        **pagination_params: Additional parameters to pass to the paginator.
    Yields:
        list: A list of keys of objects in the bucket for each page of results.
    """
    pg = s3_client.get_paginator("list_objects_v2")
    for page in pg.paginate(**pagination_params):
        yield [data["Key"] for data in page.get("Contents", [])]


def paginated_versions_list(s3_client: ClientType, **pagination_params) -> Iterator[List[Tuple[str, str]]]:
    """
    Paginate through the list of object versions in an S3 bucket.
    This function yields the keys and version IDs of object versions in the S3 bucket, paginating through the results.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        **pagination_params: Additional parameters to pass to the paginator.
    Yields:
        list: A list of tuples containing keys and version IDs of object versions in the bucket for each page of results.
    """
    try:
        pg = s3_client.get_paginator("list_object_versions")
        for page in pg.paginate(**pagination_params):
            # We have to merge the Versions and DeleteMarker lists here, as DeleteMarkers can still prevent a bucket deletion
            yield [
                (data["Key"], data["VersionId"]) for data in (page.get("Versions", []) + page.get("DeleteMarkers", []))
            ]
    except is_boto3_error_code("NoSuchBucket"):
        yield []


@S3ErrorHandler.deletion_error_handler("delete objects in bucket")
@AWSRetry.jittered_backoff(max_delay=120, catch_extra_error_codes=["OperationAborted"])
def delete_objects(s3_client: ClientType, module: AnsibleAWSModule, name: str) -> None:
    """
    Delete objects from an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        module (AnsibleAWSModule): The Ansible module object.
        name (str): The name of the S3 bucket.
    Returns:
        None
    """
    for key_version_pairs in paginated_versions_list(s3_client, Bucket=name):
        formatted_keys = [{"Key": key, "VersionId": version} for key, version in key_version_pairs]
        for fk in formatted_keys:
            # remove VersionId from cases where they are `None` so that
            # unversioned objects are deleted using `DeleteObject`
            # rather than `DeleteObjectVersion`, improving backwards
            # compatibility with older IAM policies.
            if not fk.get("VersionId") or fk.get("VersionId") == "null":
                fk.pop("VersionId")
        if formatted_keys:
            resp = s3_client.delete_objects(Bucket=name, Delete={"Objects": formatted_keys})
            if resp.get("Errors"):
                objects_to_delete = ", ".join([k["Key"] for k in resp["Errors"]])
                raise AnsibleS3Error(
                    f"Could not empty bucket before deleting. Could not delete objects: {objects_to_delete}",
                    errors=resp["Errors"],
                )


def destroy_bucket(s3_client: ClientType, module: AnsibleAWSModule) -> None:
    """
    This function destroys an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        module (AnsibleAWSModule): The Ansible module object.
    Returns:
        None
    """
    force = module.params.get("force")
    name = cast(str, module.params.get("name"))
    bucket_is_present = bucket_exists(s3_client, name)

    if not bucket_is_present:
        module.exit_json(changed=False)

    if force:
        # if there are contents then we need to delete them (including versions) before we can delete the bucket
        delete_objects(s3_client, module, name)

    delete_bucket(s3_client, name)
    waiter = get_s3_waiter(s3_client, "bucket_not_exists")
    S3ErrorHandler.deletion_error_handler(f"wait for bucket f{name} to be deleted")(waiter.wait)(Bucket=name)

    module.exit_json(changed=True)


def main():
    argument_spec = dict(
        name=dict(required=True),
        validate_bucket_name=dict(type="bool", default=True),
        dualstack=dict(default=False, type="bool"),
        state=dict(default="present", choices=["present", "absent"]),
        ceph=dict(default=False, type="bool", aliases=["rgw"]),
        # ** Warning **
        # we support non-AWS implementations, only force/purge options should have a
        # default set for any top-level option.  We need to be able to identify
        # unset options where we can ignore NotImplemented exceptions.
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        force=dict(default=False, type="bool"),
        policy=dict(type="json"),
        versioning=dict(type="bool"),
        requester_pays=dict(type="bool"),
        encryption=dict(choices=["none", "AES256", "aws:kms"]),
        encryption_key_id=dict(),
        bucket_key_enabled=dict(type="bool"),
        public_access=dict(
            type="dict",
            options=dict(
                block_public_acls=dict(type="bool", default=False),
                ignore_public_acls=dict(type="bool", default=False),
                block_public_policy=dict(type="bool", default=False),
                restrict_public_buckets=dict(type="bool", default=False),
            ),
        ),
        delete_public_access=dict(type="bool", default=False),
        object_ownership=dict(type="str", choices=["BucketOwnerEnforced", "BucketOwnerPreferred", "ObjectWriter"]),
        delete_object_ownership=dict(type="bool", default=False),
        acl=dict(type="str", choices=["private", "public-read", "public-read-write", "authenticated-read"]),
        accelerate_enabled=dict(type="bool"),
        object_lock_enabled=dict(type="bool"),
        object_lock_default_retention=dict(
            type="dict",
            options=dict(
                mode=dict(type="str", choices=["GOVERNANCE", "COMPLIANCE"], required=True),
                years=dict(type="int"),
                days=dict(type="int"),
            ),
            mutually_exclusive=[("days", "years")],
            required_one_of=[("days", "years")],
        ),
        inventory=dict(
            type="list",
            elements="dict",
            options=dict(
                destination=dict(
                    type="dict",
                    options=dict(
                        account_id=dict(type="str"),
                        bucket=dict(type="str", required=True),
                        format=dict(type="str", choices=["CSV", "ORC", "Parquet"], required=True),
                        prefix=dict(type="str"),
                    ),
                    required=True,
                ),
                filter=dict(type="str"),
                optional_fields=dict(
                    type="list",
                    elements="str",
                    choices=[
                        "Size",
                        "LastModifiedDate",
                        "StorageClass",
                        "ETag",
                        "IsMultipartUploaded",
                        "ReplicationStatus",
                        "EncryptionStatus",
                        "ObjectLockRetainUntilDate",
                        "ObjectLockMode",
                        "ObjectLockLegalHoldStatus",
                        "IntelligentTieringAccessTier",
                        "BucketKeyStatus",
                        "ChecksumAlgorithm",
                        "ObjectAccessControlList",
                        "ObjectOwner",
                    ],
                ),
                id=dict(type="str", required=True),
                schedule=dict(type="str", choices=["Daily", "Weekly"], required=True),
                included_object_versions=dict(type="str", choices=["All", "Current"], required=True),
            ),
        ),
    )

    required_by = dict(
        encryption_key_id=("encryption",),
        object_lock_default_retention=("object_lock_enabled",),
    )

    mutually_exclusive = [
        ["public_access", "delete_public_access"],
        ["delete_object_ownership", "object_ownership"],
        ["dualstack", "endpoint_url"],
    ]

    required_if = [
        ["ceph", True, ["endpoint_url"]],
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_by=required_by,
        required_if=required_if,
        mutually_exclusive=mutually_exclusive,
    )

    # Parameter validation
    encryption = module.params.get("encryption")
    encryption_key_id = module.params.get("encryption_key_id")
    if encryption_key_id is not None and encryption != "aws:kms":
        module.fail_json(
            msg="Only 'aws:kms' is a valid option for encryption parameter when you specify encryption_key_id."
        )

    extra_params = s3_extra_params(module.params)
    retry_decorator = AWSRetry.jittered_backoff(
        max_delay=120,
        catch_extra_error_codes=["NoSuchBucket", "OperationAborted"],
    )
    s3_client = module.client("s3", retry_decorator=retry_decorator, **extra_params)

    if module.params.get("validate_bucket_name"):
        err = validate_bucket_name(module.params["name"])
        if err:
            module.fail_json(msg=err)

    state = module.params.get("state")

    try:
        if state == "present":
            create_or_update_bucket(s3_client, module)
        elif state == "absent":
            destroy_bucket(s3_client, module)
    except AnsibleS3Error as e:
        module.fail_json_aws_error(e)


if __name__ == "__main__":
    main()
