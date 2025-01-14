#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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
  - In release 5.0.0 the O(s3_url) parameter was merged into the O(endpoint_url) parameter,
    O(s3_url) remains as an alias for O(endpoint_url).
  - For Walrus O(endpoint_url) should be set to the FQDN of the endpoint with neither scheme nor path.
  - Support for the E(S3_URL) environment variable has been
    deprecated and will be removed in a release after 2024-12-01, please use the O(endpoint_url) parameter
    or the E(AWS_URL) environment variable.
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
from typing import Iterator
from typing import List
from typing import Tuple

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.basic import to_text
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict
from ansible.module_utils.six import string_types

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.policy import compare_policies
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.s3 import get_s3_bucket_location
from ansible_collections.amazon.aws.plugins.module_utils.s3 import list_bucket_inventory_configurations
from ansible_collections.amazon.aws.plugins.module_utils.s3 import s3_extra_params
from ansible_collections.amazon.aws.plugins.module_utils.s3 import validate_bucket_name
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict


def handle_bucket_versioning(s3_client, module: AnsibleAWSModule, name: str) -> Tuple[bool, dict]:
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
    versioning_changed = False
    versioning_status = {}

    try:
        versioning_status = get_bucket_versioning(s3_client, name)
    except is_boto3_error_code(["NotImplemented", "XNotImplemented"]) as e:
        if versioning is not None:
            module.fail_json_aws(e, msg="Bucket versioning is not supported by the current S3 Endpoint")
    except is_boto3_error_code("AccessDenied") as e:
        if versioning is not None:
            module.fail_json_aws(e, msg="Failed to get bucket versioning")
        module.warn("AccessDenied fetching bucket versioning")
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to get bucket versioning")
    else:
        if versioning is not None:
            required_versioning = None
            if versioning and versioning_status.get("Status") != "Enabled":
                required_versioning = "Enabled"
            elif not versioning and versioning_status.get("Status") == "Enabled":
                required_versioning = "Suspended"

            if required_versioning:
                try:
                    put_bucket_versioning(s3_client, name, required_versioning)
                    versioning_changed = True
                except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                    module.fail_json_aws(e, msg="Failed to update bucket versioning")

                versioning_status = wait_versioning_is_applied(module, s3_client, name, required_versioning)

        versioning_result = {
            "Versioning": versioning_status.get("Status", "Disabled"),
            "MfaDelete": versioning_status.get("MFADelete", "Disabled"),
        }
        # This output format is there to ensure compatibility with previous versions of the module
    return versioning_changed, versioning_result


def handle_bucket_requester_pays(s3_client, module: AnsibleAWSModule, name: str) -> Tuple[bool, dict]:
    """
    Manage requester pays setting for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        module (AnsibleAWSModule): The Ansible module object.
        name (str): The name of the bucket to handle requester pays setting for.
    Returns:
        A tuple containing a boolean indicating whether requester pays setting
        was changed and a dictionary containing the updated requester pays status.
    """

    requester_pays = module.params.get("requester_pays")
    requester_pays_changed = False
    requester_pays_status = {}

    try:
        requester_pays_status = get_bucket_request_payment(s3_client, name)
    except is_boto3_error_code(["NotImplemented", "XNotImplemented"]) as e:
        if requester_pays is not None:
            module.fail_json_aws(e, msg="Bucket request payment is not supported by the current S3 Endpoint")
    except is_boto3_error_code("AccessDenied") as e:
        if requester_pays is not None:
            module.fail_json_aws(e, msg="Failed to get bucket request payment")
        module.warn("AccessDenied fetching bucket request payment")
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to get bucket request payment")
    else:
        if requester_pays is not None:
            payer = "Requester" if requester_pays else "BucketOwner"
            if requester_pays_status != payer:
                put_bucket_request_payment(s3_client, name, payer)
                requester_pays_status = wait_payer_is_applied(module, s3_client, name, payer, should_fail=False)
                if requester_pays_status is None:
                    # We have seen that it happens quite a lot of times that the put request was not taken into
                    # account, so we retry one more time
                    put_bucket_request_payment(s3_client, name, payer)
                    requester_pays_status = wait_payer_is_applied(module, s3_client, name, payer, should_fail=True)
                requester_pays_changed = True
    return requester_pays_changed, requester_pays


def handle_bucket_public_access_config(s3_client, module: AnsibleAWSModule, name: str) -> Tuple[bool, dict]:
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
    public_access_changed = False
    public_access_result = {}
    current_public_access = {}

    try:
        current_public_access = get_bucket_public_access(s3_client, name)
    except is_boto3_error_code(["NotImplemented", "XNotImplemented"]) as e:
        if public_access is not None:
            module.fail_json_aws(e, msg="Bucket public access settings are not supported by the current S3 Endpoint")
    except is_boto3_error_code("AccessDenied") as e:
        if public_access is not None:
            module.fail_json_aws(e, msg="Failed to get bucket public access configuration")
        module.warn("AccessDenied fetching bucket public access settings")
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to get bucket public access configuration")
    else:
        # -- Create / Update public access block
        if public_access is not None:
            camel_public_block = snake_dict_to_camel_dict(public_access, capitalize_first=True)

            if current_public_access == camel_public_block:
                public_access_result = current_public_access
            else:
                put_bucket_public_access(s3_client, name, camel_public_block)
                public_access_changed = True
                public_access_result = camel_public_block

        # -- Delete public access block
        if delete_public_access:
            if current_public_access == {}:
                public_access_result = current_public_access
            else:
                delete_bucket_public_access(s3_client, name)
                public_access_changed = True
                public_access_result = {}

    # Return the result
    return public_access_changed, public_access_result


def handle_bucket_policy(s3_client, module: AnsibleAWSModule, name: str) -> Tuple[bool, dict]:
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
    policy_changed = False
    current_policy = None

    try:
        current_policy = get_bucket_policy(s3_client, name)
    except is_boto3_error_code(["NotImplemented", "XNotImplemented"]) as e:
        if policy is not None:
            module.fail_json_aws(e, msg="Bucket policy is not supported by the current S3 Endpoint")
    except is_boto3_error_code("AccessDenied") as e:
        if policy is not None:
            module.fail_json_aws(e, msg="Failed to get bucket policy")
        module.warn("AccessDenied fetching bucket policy")
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to get bucket policy")
    else:
        if policy is not None:
            if isinstance(policy, string_types):
                policy = json.loads(policy)

            if not policy and current_policy:
                try:
                    delete_bucket_policy(s3_client, name)
                except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                    module.fail_json_aws(e, msg="Failed to delete bucket policy")
                current_policy = wait_policy_is_applied(module, s3_client, name, policy)
                policy_changed = True
            elif compare_policies(current_policy, policy):
                try:
                    put_bucket_policy(s3_client, name, policy)
                except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                    module.fail_json_aws(e, msg="Failed to update bucket policy")
                current_policy = wait_policy_is_applied(module, s3_client, name, policy, should_fail=False)
                if current_policy is None:
                    # As for request payement, it happens quite a lot of times that the put request was not taken into
                    # account, so we retry one more time
                    put_bucket_policy(s3_client, name, policy)
                    current_policy = wait_policy_is_applied(module, s3_client, name, policy, should_fail=True)
                policy_changed = True

    return policy_changed, current_policy


def handle_bucket_tags(s3_client, module: AnsibleAWSModule, name: str) -> Tuple[bool, dict]:
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
    purge_tags = module.params.get("purge_tags")
    bucket_tags_changed = False
    current_tags_dict = None

    try:
        current_tags_dict = get_current_bucket_tags_dict(s3_client, name)
    except is_boto3_error_code(["NotImplemented", "XNotImplemented"]) as e:
        if tags is not None:
            module.fail_json_aws(e, msg="Bucket tagging is not supported by the current S3 Endpoint")
    except is_boto3_error_code("AccessDenied") as e:
        if tags is not None:
            module.fail_json_aws(e, msg="Failed to get bucket tags")
        module.warn("AccessDenied fetching bucket tags")
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to get bucket tags")
    else:
        if tags is not None:
            # Tags are always returned as text
            tags = dict((to_text(k), to_text(v)) for k, v in tags.items())
            if not purge_tags:
                # Ensure existing tags that aren't updated by desired tags remain
                current_copy = current_tags_dict.copy()
                current_copy.update(tags)
                tags = current_copy
            if current_tags_dict != tags:
                if tags:
                    try:
                        put_bucket_tagging(s3_client, name, tags)
                    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                        module.fail_json_aws(e, msg="Failed to update bucket tags")
                else:
                    if purge_tags:
                        try:
                            delete_bucket_tagging(s3_client, name)
                        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                            module.fail_json_aws(e, msg="Failed to delete bucket tags")
                current_tags_dict = wait_tags_are_applied(module, s3_client, name, tags)
                bucket_tags_changed = True

    return bucket_tags_changed, current_tags_dict


def handle_bucket_encryption(s3_client, module: AnsibleAWSModule, name: str) -> Tuple[bool, dict]:
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
    encryption_changed = False
    current_encryption = None

    try:
        current_encryption = get_bucket_encryption(s3_client, name)
    except is_boto3_error_code(["NotImplemented", "XNotImplemented"]) as e:
        if encryption is not None:
            module.fail_json_aws(e, msg="Bucket encryption is not supported by the current S3 Endpoint")
    except is_boto3_error_code("AccessDenied") as e:
        if encryption is not None:
            module.fail_json_aws(e, msg="Failed to get bucket encryption settings")
        module.warn("AccessDenied fetching bucket encryption settings")
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to get bucket encryption settings")
    else:
        if encryption is not None:
            current_encryption_algorithm = current_encryption.get("SSEAlgorithm") if current_encryption else None
            current_encryption_key = current_encryption.get("KMSMasterKeyID") if current_encryption else None
            if encryption == "none":
                if current_encryption_algorithm is not None:
                    try:
                        delete_bucket_encryption(s3_client, name)
                    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                        module.fail_json_aws(e, msg="Failed to delete bucket encryption")
                    current_encryption = wait_encryption_is_applied(module, s3_client, name, None)
                    encryption_changed = True
            else:
                if (encryption != current_encryption_algorithm) or (
                    encryption == "aws:kms" and current_encryption_key != encryption_key_id
                ):
                    expected_encryption = {"SSEAlgorithm": encryption}
                    if encryption == "aws:kms" and encryption_key_id is not None:
                        expected_encryption.update({"KMSMasterKeyID": encryption_key_id})
                    current_encryption = put_bucket_encryption_with_retry(module, s3_client, name, expected_encryption)
                    encryption_changed = True

        if bucket_key_enabled is not None:
            current_encryption_algorithm = current_encryption.get("SSEAlgorithm") if current_encryption else None
            if current_encryption_algorithm == "aws:kms":
                if get_bucket_key(s3_client, name) != bucket_key_enabled:
                    expected_encryption = bool(bucket_key_enabled)
                    current_encryption = put_bucket_key_with_retry(module, s3_client, name, expected_encryption)
                    encryption_changed = True

    return encryption_changed, current_encryption


def handle_bucket_ownership(s3_client, module: AnsibleAWSModule, name: str) -> Tuple[bool, dict]:
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
    bucket_ownership_changed = False
    bucket_ownership_result = {}

    try:
        bucket_ownership = get_bucket_ownership_cntrl(s3_client, name)
        bucket_ownership_result = bucket_ownership
    except KeyError as e:
        # Some non-AWS providers appear to return policy documents that aren't
        # compatible with AWS, cleanly catch KeyError so users can continue to use
        # other features.
        if delete_object_ownership or object_ownership is not None:
            module.fail_json_aws(e, msg="Failed to get bucket object ownership settings")
    except is_boto3_error_code(["NotImplemented", "XNotImplemented"]) as e:
        if delete_object_ownership or object_ownership is not None:
            module.fail_json_aws(e, msg="Bucket object ownership is not supported by the current S3 Endpoint")
    except is_boto3_error_code("AccessDenied") as e:
        if delete_object_ownership or object_ownership is not None:
            module.fail_json_aws(e, msg="Failed to get bucket object ownership settings")
        module.warn("AccessDenied fetching bucket object ownership settings")
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to get bucket object ownership settings")
    else:
        if delete_object_ownership:
            # delete S3 buckect ownership
            if bucket_ownership is not None:
                delete_bucket_ownership(s3_client, name)
                bucket_ownership_changed = True
                bucket_ownership_result = None
        elif object_ownership is not None:
            # update S3 bucket ownership
            if bucket_ownership != object_ownership:
                put_bucket_ownership(s3_client, name, object_ownership)
                bucket_ownership_changed = True
                bucket_ownership_result = object_ownership

    return bucket_ownership_changed, bucket_ownership_result


def handle_bucket_acl(s3_client, module: AnsibleAWSModule, name: str) -> Tuple[bool, dict]:
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
    bucket_acl_changed = False
    bucket_acl_result = {}

    if acl:
        try:
            s3_client.put_bucket_acl(Bucket=name, ACL=acl)
            bucket_acl_result = acl
            bucket_acl_changed = True
        except KeyError as e:
            # Some non-AWS providers appear to return policy documents that aren't
            # compatible with AWS, cleanly catch KeyError so users can continue to use
            # other features.
            module.fail_json_aws(e, msg="Failed to get bucket acl block")
        except is_boto3_error_code(["NotImplemented", "XNotImplemented"]) as e:
            module.fail_json_aws(e, msg="Bucket ACLs ar not supported by the current S3 Endpoint")
        except is_boto3_error_code("AccessDenied") as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Access denied trying to update bucket ACL")
        except (
            botocore.exceptions.BotoCoreError,
            botocore.exceptions.ClientError,
        ) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Failed to update bucket ACL")

    return bucket_acl_changed, bucket_acl_result


def handle_bucket_object_lock(s3_client, module: AnsibleAWSModule, name: str) -> dict:
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
    object_lock_result = {}

    try:
        object_lock_status = get_bucket_object_lock_enabled(s3_client, name)
        object_lock_result = object_lock_status
    except is_boto3_error_code(["NotImplemented", "XNotImplemented"]):
        if object_lock_enabled is not None:
            module.fail_json(msg="Fetching bucket object lock state is not supported")
    except is_boto3_error_code("ObjectLockConfigurationNotFoundError"):  # pylint: disable=duplicate-except
        if object_lock_enabled:
            module.fail_json(msg="Enabling object lock for existing buckets is not supported")
        object_lock_result = False
    except is_boto3_error_code("AccessDenied"):  # pylint: disable=duplicate-except
        if object_lock_enabled is not None:
            module.fail_json(msg="Permission denied fetching object lock state for bucket")
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to fetch bucket object lock state")
    else:
        if object_lock_status is not None:
            if not object_lock_enabled and object_lock_status:
                module.fail_json(msg="Disabling object lock for existing buckets is not supported")
            if object_lock_enabled and not object_lock_status:
                module.fail_json(msg="Enabling object lock for existing buckets is not supported")

    return object_lock_result


def handle_bucket_accelerate(s3_client, module: AnsibleAWSModule, name: str) -> Tuple[bool, bool]:
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
    accelerate_enabled_result = False
    accelerate_enabled_changed = False

    try:
        accelerate_status = get_bucket_accelerate_status(s3_client, name)
        accelerate_enabled_result = accelerate_status
    except is_boto3_error_code(["NotImplemented", "XNotImplemented"]) as e:
        if accelerate_enabled is not None:
            module.fail_json_aws(e, msg="Fetching bucket transfer acceleration state is not supported")
    except is_boto3_error_code(["UnsupportedArgument", "MethodNotAllowed"]):  # pylint: disable=duplicate-except
        # - Transfer Acceleration is not available in AWS GovCloud (US) and throws UnsupportedArgument.
        # https://docs.aws.amazon.com/govcloud-us/latest/UserGuide/govcloud-s3.html#govcloud-S3-diffs
        # - Transfer Acceleration is not available in some AWS regions and throws MethodNotAllowed
        # https://docs.aws.amazon.com/AmazonS3/latest/userguide/transfer-acceleration.html
        module.warn("Tranfer acceleration is not available in S3 bucket region.")
        accelerate_enabled_result = False
    except is_boto3_error_code("AccessDenied") as e:  # pylint: disable=duplicate-except
        if accelerate_enabled is not None:
            module.fail_json_aws(e, msg="Permission denied fetching transfer acceleration for bucket")
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to fetch bucket transfer acceleration state")
    else:
        if accelerate_enabled is not None:
            try:
                if not accelerate_enabled and accelerate_status:
                    delete_bucket_accelerate_configuration(s3_client, name)
                    accelerate_enabled_changed = True
                    accelerate_enabled_result = False
                if accelerate_enabled and not accelerate_status:
                    put_bucket_accelerate_configuration(s3_client, name)
                    accelerate_enabled_changed = True
                    accelerate_enabled_result = True
            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                module.fail_json_aws(e, msg="Failed to update bucket transfer acceleration")
    return accelerate_enabled_changed, accelerate_enabled_result


def handle_bucket_object_lock_retention(s3_client, module: AnsibleAWSModule, name: str) -> Tuple[bool, dict]:
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
    object_lock_default_retention_result = {}
    object_lock_default_retention_changed = False

    try:
        if object_lock_enabled:
            object_lock_configuration_status = get_object_lock_configuration(s3_client, name)
        else:
            object_lock_configuration_status = {}
    except is_boto3_error_code(["NotImplemented", "XNotImplemented"]) as e:
        if object_lock_default_retention is not None:
            module.fail_json_aws(e, msg="Fetching bucket object lock default retention is not supported")
    except is_boto3_error_code("AccessDenied") as e:  # pylint: disable=duplicate-except
        if object_lock_default_retention is not None:
            module.fail_json_aws(e, msg="Permission denied fetching object lock default retention for bucket")
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to fetch bucket object lock default retention state")
    else:
        if not object_lock_default_retention and object_lock_configuration_status != {}:
            module.fail_json(msg="Removing object lock default retention is not supported")
        if object_lock_default_retention is not None:
            conf = snake_dict_to_camel_dict(object_lock_default_retention, capitalize_first=True)
            conf = {k: v for k, v in conf.items() if v}  # remove keys with None value
            try:
                if object_lock_default_retention and object_lock_configuration_status != conf:
                    put_object_lock_configuration(s3_client, name, conf)
                    object_lock_default_retention_changed = True
                    object_lock_default_retention_result = object_lock_default_retention
                else:
                    object_lock_default_retention_result = object_lock_default_retention
            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
                module.fail_json_aws(e, msg="Failed to update bucket object lock default retention")

    return object_lock_default_retention_changed, object_lock_default_retention_result


def handle_bucket_inventory(s3_client, module: AnsibleAWSModule, name: str) -> Tuple[bool, dict]:
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
    results = []
    bucket_changed = False

    if declared_inventories is None:
        return (False, results)

    try:
        present_inventories = {i["Id"]: i for i in list_bucket_inventory_configurations(s3_client, name)}
    except is_boto3_error_code(["NotImplemented", "XNotImplemented"]) as e:
        if declared_inventories is not None:
            module.fail_json_aws(e, msg="Fetching bucket inventories is not supported")
    except is_boto3_error_code("AccessDenied") as e:  # pylint: disable=duplicate-except
        if declared_inventories is not None:
            module.fail_json_aws(e, msg="Permission denied fetching bucket inventories")
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to fetch bucket inventories")

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
            try:
                put_bucket_inventory(s3_client, name, declared_inventory_api)
                bucket_changed = True
            except is_boto3_error_code("InvalidS3DestinationBucket") as e:
                module.fail_json_aws(e, msg="Invalid destination bucket ARN")
            except (
                botocore.exceptions.BotoCoreError,
                botocore.exceptions.ClientError,
            ) as e:  # pylint: disable=duplicate-except
                module.fail_json_aws(e, msg="Failed to set bucket inventory setting")

        results.append(declared_inventory_api)

    for inventory_id in present_inventories.keys():
        try:
            delete_bucket_inventory(s3_client, name, inventory_id)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed to delete bucket inventory")
        bucket_changed = True

    return bucket_changed, results


def create_or_update_bucket(s3_client, module: AnsibleAWSModule):
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
    name = module.params.get("name")
    object_lock_enabled = module.params.get("object_lock_enabled")
    location = get_s3_bucket_location(module)

    changed = False
    result = {}

    try:
        bucket_is_present = bucket_exists(s3_client, name)
    except botocore.exceptions.EndpointConnectionError as e:
        module.fail_json_aws(e, msg=f"Invalid endpoint provided: {to_text(e)}")
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to check bucket presence")

    if not bucket_is_present:
        try:
            bucket_changed = create_bucket(s3_client, name, location, object_lock_enabled)
            s3_client.get_waiter("bucket_exists").wait(Bucket=name)
            changed = changed or bucket_changed
        except botocore.exceptions.WaiterError as e:
            module.fail_json_aws(e, msg="An error occurred waiting for the bucket to become available")
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed while creating bucket")

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
    bucket_acl_changed, bucket_acl_result = handle_bucket_acl(s3_client, module, name)
    result["acl"] = bucket_acl_result

    # -- Object Lock
    bucket_object_lock_result = handle_bucket_object_lock(s3_client, module, name)
    result["object_lock_enabled"] = bucket_object_lock_result

    # -- Transfer Acceleration
    bucket_accelerate_changed, bucket_accelerate_result = handle_bucket_accelerate(s3_client, module, name)
    result["accelerate_enabled"] = bucket_accelerate_result

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


def bucket_exists(s3_client, bucket_name: str) -> bool:
    """
    Checks if a given bucket exists in an AWS S3 account.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the bucket to check for existence.
    Returns:
        True if the bucket exists, False otherwise.
    """
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return True
    except is_boto3_error_code("404"):
        return False


@AWSRetry.exponential_backoff(max_delay=120)
def create_bucket(s3_client, bucket_name: str, location: str, object_lock_enabled: bool = False) -> bool:
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
    try:
        params = {"Bucket": bucket_name}

        configuration = {}
        if location not in ("us-east-1", None):
            configuration["LocationConstraint"] = location

        if configuration:
            params["CreateBucketConfiguration"] = configuration

        if object_lock_enabled is not None:
            params["ObjectLockEnabledForBucket"] = object_lock_enabled

        s3_client.create_bucket(**params)

        return True
    except is_boto3_error_code("BucketAlreadyOwnedByYou"):
        # We should never get here since we check the bucket presence before calling the create_or_update_bucket
        # method. However, the AWS Api sometimes fails to report bucket presence, so we catch this exception
        return False


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_object_lock_configuration(s3_client, bucket_name):
    """
    Get the object lock default retention configuration for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        Object lock default retention configuration dictionary.
    """
    result = s3_client.get_object_lock_configuration(Bucket=bucket_name)
    return result.get("ObjectLockConfiguration", {}).get("Rule", {}).get("DefaultRetention", {})


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_object_lock_configuration(s3_client, bucket_name, object_lock_default_retention):
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


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_bucket_accelerate_configuration(s3_client, bucket_name):
    """
    Enable transfer accelerate for the S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        None
    """
    s3_client.put_bucket_accelerate_configuration(Bucket=bucket_name, AccelerateConfiguration={"Status": "Enabled"})


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def delete_bucket_accelerate_configuration(s3_client, bucket_name):
    """
    Disable transfer accelerate for the S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        None
    """

    s3_client.put_bucket_accelerate_configuration(Bucket=bucket_name, AccelerateConfiguration={"Status": "Suspended"})


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_bucket_accelerate_status(s3_client, bucket_name) -> bool:
    """
    Get transfer accelerate status of the S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        Transfer accelerate status of the S3 bucket.
    """
    accelerate_configuration = s3_client.get_bucket_accelerate_configuration(Bucket=bucket_name)
    return accelerate_configuration.get("Status") == "Enabled"


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_bucket_inventory(s3_client, bucket_name: str, inventory: dict) -> None:
    """
    Set inventory settings for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        tags (dict): A dictionary containing the inventory settings to be set on the bucket.
    Returns:
        None
    """
    s3_client.put_bucket_inventory_configuration(
        Bucket=bucket_name, InventoryConfiguration=inventory, Id=inventory.get("Id")
    )


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_bucket_tagging(s3_client, bucket_name: str, tags: dict):
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


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def delete_bucket_inventory(s3_client, bucket_name: str, inventory_id: str) -> None:
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


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_bucket_policy(s3_client, bucket_name: str, policy: dict):
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


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def delete_bucket_policy(s3_client, bucket_name: str):
    """
    Delete the policy for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        None
    """
    s3_client.delete_bucket_policy(Bucket=bucket_name)


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_bucket_policy(s3_client, bucket_name: str) -> str:
    """
    Get the policy for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        Current bucket policy.
    """
    try:
        current_policy_string = s3_client.get_bucket_policy(Bucket=bucket_name).get("Policy")
        if not current_policy_string:
            return None
        current_policy = json.loads(current_policy_string)
    except is_boto3_error_code("NoSuchBucketPolicy"):
        return None

    return current_policy


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_bucket_request_payment(s3_client, bucket_name: str, payer: str):
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


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_bucket_request_payment(s3_client, bucket_name: str) -> str:
    """
    Get the request payment configuration for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        Payer of the download and request fees.
    """
    return s3_client.get_bucket_request_payment(Bucket=bucket_name).get("Payer")


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_bucket_versioning(s3_client, bucket_name: str) -> dict:
    """
    Get the versioning configuration for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        Returns the versioning state of a bucket.
    """
    return s3_client.get_bucket_versioning(Bucket=bucket_name)


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_bucket_versioning(s3_client, bucket_name: str, required_versioning: str):
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


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_bucket_object_lock_enabled(s3_client, bucket_name: str) -> bool:
    """
    Retrieve the object lock configuration status for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        True if object lock is enabled for the bucket, False otherwise.
    """
    object_lock_configuration = s3_client.get_object_lock_configuration(Bucket=bucket_name)
    return object_lock_configuration["ObjectLockConfiguration"]["ObjectLockEnabled"] == "Enabled"


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_bucket_encryption(s3_client, bucket_name: str) -> dict:
    """
    Retrieve the encryption configuration for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        Encryption configuration of the bucket.
    """
    try:
        result = s3_client.get_bucket_encryption(Bucket=bucket_name)
        return (
            result.get("ServerSideEncryptionConfiguration", {})
            .get("Rules", [])[0]
            .get("ApplyServerSideEncryptionByDefault")
        )
    except is_boto3_error_code("ServerSideEncryptionConfigurationNotFoundError"):
        return None
    except (IndexError, KeyError):
        return None


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def get_bucket_key(s3_client, bucket_name: str) -> bool:
    """
    Retrieve the status of server-side encryption for an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        Whether or not if server-side encryption is enabled for the bucket.
    """
    try:
        result = s3_client.get_bucket_encryption(Bucket=bucket_name)
        return result.get("ServerSideEncryptionConfiguration", {}).get("Rules", [])[0].get("BucketKeyEnabled")
    except is_boto3_error_code("ServerSideEncryptionConfigurationNotFoundError"):
        return None
    except (IndexError, KeyError):
        return None


def put_bucket_encryption_with_retry(module: AnsibleAWSModule, s3_client, name: str, expected_encryption: dict) -> dict:
    """
    Set the encryption configuration for an S3 bucket with retry logic.
    Parameters:
        module (AnsibleAWSModule): The Ansible module object.
        s3_client (boto3.client): The Boto3 S3 client object.
        name (str): The name of the S3 bucket.
        expected_encryption (dict): A dictionary containing the expected encryption configuration.
    Returns:
        Updated encryption configuration of the bucket.
    """
    max_retries = 3
    for retries in range(1, max_retries + 1):
        try:
            put_bucket_encryption(s3_client, name, expected_encryption)
        except (
            botocore.exceptions.BotoCoreError,
            botocore.exceptions.ClientError,
        ) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Failed to set bucket encryption")
        current_encryption = wait_encryption_is_applied(
            module, s3_client, name, expected_encryption, should_fail=(retries == max_retries), retries=5
        )
        if current_encryption == expected_encryption:
            return current_encryption

    # We shouldn't get here, the only time this should happen is if
    # current_encryption != expected_encryption and retries == max_retries
    # Which should use module.fail_json and fail out first.
    module.fail_json(
        msg="Failed to apply bucket encryption",
        current=current_encryption,
        expected=expected_encryption,
        retries=retries,
    )


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_bucket_encryption(s3_client, bucket_name: str, encryption: dict) -> None:
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


def put_bucket_key_with_retry(module: AnsibleAWSModule, s3_client, name: str, expected_encryption: bool) -> dict:
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
        try:
            put_bucket_key(s3_client, name, expected_encryption)
        except (
            botocore.exceptions.BotoCoreError,
            botocore.exceptions.ClientError,
        ) as e:  # pylint: disable=duplicate-except
            module.fail_json_aws(e, msg="Failed to set bucket Key")
        current_encryption = wait_bucket_key_is_applied(
            module, s3_client, name, expected_encryption, should_fail=(retries == max_retries), retries=5
        )
        if current_encryption == expected_encryption:
            return current_encryption

    # We shouldn't get here, the only time this should happen is if
    # current_encryption != expected_encryption and retries == max_retries
    # Which should use module.fail_json and fail out first.
    module.fail_json(
        msg="Failed to set bucket key", current=current_encryption, expected=expected_encryption, retries=retries
    )


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_bucket_key(s3_client, bucket_name: str, encryption: bool) -> None:
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
    encryption_status = s3_client.get_bucket_encryption(Bucket=bucket_name)
    encryption_status["ServerSideEncryptionConfiguration"]["Rules"][0]["BucketKeyEnabled"] = encryption
    s3_client.put_bucket_encryption(
        Bucket=bucket_name, ServerSideEncryptionConfiguration=encryption_status["ServerSideEncryptionConfiguration"]
    )


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def delete_bucket_tagging(s3_client, bucket_name: str) -> None:
    """
    Delete the tagging configuration of an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        None
    """
    s3_client.delete_bucket_tagging(Bucket=bucket_name)


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def delete_bucket_encryption(s3_client, bucket_name: str) -> None:
    """
    Delete the encryption configuration of an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        None
    """
    s3_client.delete_bucket_encryption(Bucket=bucket_name)


@AWSRetry.exponential_backoff(max_delay=240, catch_extra_error_codes=["OperationAborted"])
def delete_bucket(s3_client, bucket_name: str) -> None:
    """
    Delete an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        None
    """
    try:
        s3_client.delete_bucket(Bucket=bucket_name)
    except is_boto3_error_code("NoSuchBucket"):
        # This means bucket should have been in a deleting state when we checked it existence
        # We just ignore the error
        pass


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def put_bucket_public_access(s3_client, bucket_name: str, public_acces: dict) -> None:
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


@AWSRetry.exponential_backoff(max_delay=120, catch_extra_error_codes=["NoSuchBucket", "OperationAborted"])
def delete_bucket_public_access(s3_client, bucket_name: str) -> None:
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
def delete_bucket_ownership(s3_client, bucket_name: str) -> None:
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
def put_bucket_ownership(s3_client, bucket_name: str, target: str) -> None:
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
    module: AnsibleAWSModule, s3_client, bucket_name: str, expected_policy: dict, should_fail: bool = True
) -> dict:
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
        try:
            current_policy = get_bucket_policy(s3_client, bucket_name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed to get bucket policy")

        if compare_policies(current_policy, expected_policy):
            time.sleep(5)
        else:
            return current_policy
    if should_fail:
        module.fail_json(
            msg="Bucket policy failed to apply in the expected time",
            requested_policy=expected_policy,
            live_policy=current_policy,
        )
    else:
        return None


def wait_payer_is_applied(
    module: AnsibleAWSModule, s3_client, bucket_name: str, expected_payer: bool, should_fail=True
) -> str:
    """
    Wait for the requester pays setting to be applied to an S3 bucket.
    Parameters:
        module (AnsibleAWSModule): The Ansible module object.
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        expected_payer (bool): The expected status of the requester pays setting.
        should_fail (bool): Flag indicating whether to fail if the setting is not applied within the expected time. Default is True.
    Returns:
        The current status of the requester pays setting applied to the bucket.
    """
    for dummy in range(0, 12):
        try:
            requester_pays_status = get_bucket_request_payment(s3_client, bucket_name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed to get bucket request payment")
        if requester_pays_status != expected_payer:
            time.sleep(5)
        else:
            return requester_pays_status
    if should_fail:
        module.fail_json(
            msg="Bucket request payment failed to apply in the expected time",
            requested_status=expected_payer,
            live_status=requester_pays_status,
        )
    else:
        return None


def wait_encryption_is_applied(
    module: AnsibleAWSModule, s3_client, bucket_name: str, expected_encryption: dict, should_fail=True, retries=12
) -> dict:
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
        try:
            encryption = get_bucket_encryption(s3_client, bucket_name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed to get updated encryption for bucket")
        if encryption != expected_encryption:
            time.sleep(5)
        else:
            return encryption

    if should_fail:
        module.fail_json(
            msg="Bucket encryption failed to apply in the expected time",
            requested_encryption=expected_encryption,
            live_encryption=encryption,
        )

    return encryption


def wait_bucket_key_is_applied(
    module: AnsibleAWSModule, s3_client, bucket_name: str, expected_encryption: bool, should_fail=True, retries=12
) -> bool:
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
    for dummy in range(0, retries):
        try:
            encryption = get_bucket_key(s3_client, bucket_name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed to get updated encryption for bucket")
        if encryption != expected_encryption:
            time.sleep(5)
        else:
            return encryption

    if should_fail:
        module.fail_json(
            msg="Bucket Key failed to apply in the expected time",
            requested_encryption=expected_encryption,
            live_encryption=encryption,
        )
    return encryption


def wait_versioning_is_applied(
    module: AnsibleAWSModule, s3_client, bucket_name: str, required_versioning: dict
) -> dict:
    """
    Wait for the versioning setting to be applied to an S3 bucket.
    Parameters:
        module (AnsibleAWSModule): The Ansible module object.
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        required_versioning (dict): The required versioning status.
    Returns:
        The current versioning status applied to the bucket.
    """
    for dummy in range(0, 24):
        try:
            versioning_status = get_bucket_versioning(s3_client, bucket_name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed to get updated versioning for bucket")
        if versioning_status.get("Status") != required_versioning:
            time.sleep(8)
        else:
            return versioning_status
    module.fail_json(
        msg="Bucket versioning failed to apply in the expected time",
        requested_versioning=required_versioning,
        live_versioning=versioning_status,
    )


def wait_tags_are_applied(module: AnsibleAWSModule, s3_client, bucket_name: str, expected_tags_dict: dict) -> dict:
    """
    Wait for the tags to be applied to an S3 bucket.
    Parameters:
        module (AnsibleAWSModule): The Ansible module object.
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
        expected_tags_dict (dict): The expected tags dictionary.
    Returns:
        The current tags dictionary applied to the bucket.
    """
    for dummy in range(0, 12):
        try:
            current_tags_dict = get_current_bucket_tags_dict(s3_client, bucket_name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed to get bucket policy")
        if current_tags_dict != expected_tags_dict:
            time.sleep(5)
        else:
            return current_tags_dict
    module.fail_json(
        msg="Bucket tags failed to apply in the expected time",
        requested_tags=expected_tags_dict,
        live_tags=current_tags_dict,
    )


def get_current_bucket_tags_dict(s3_client, bucket_name: str) -> dict:
    """
    Get the current tags applied to an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        The current tags dictionary applied to the bucket.
    """
    try:
        current_tags = s3_client.get_bucket_tagging(Bucket=bucket_name).get("TagSet")
    except is_boto3_error_code("NoSuchTagSet"):
        return {}
    # The Ceph S3 API returns a different error code to AWS
    except is_boto3_error_code("NoSuchTagSetError"):  # pylint: disable=duplicate-except
        return {}

    return boto3_tag_list_to_ansible_dict(current_tags)


def get_bucket_public_access(s3_client, bucket_name: str) -> dict:
    """
    Get current public access block configuration for a bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
        The current public access block configuration for the bucket.
    """
    try:
        bucket_public_access_block = s3_client.get_public_access_block(Bucket=bucket_name)
        return bucket_public_access_block["PublicAccessBlockConfiguration"]
    except is_boto3_error_code("NoSuchPublicAccessBlockConfiguration"):
        return {}


def get_bucket_ownership_cntrl(s3_client, bucket_name: str) -> str:
    """
    Get the current bucket ownership controls.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        bucket_name (str): The name of the S3 bucket.
    Returns:
      The object ownership rule
    """
    try:
        bucket_ownership = s3_client.get_bucket_ownership_controls(Bucket=bucket_name)
        return bucket_ownership["OwnershipControls"]["Rules"][0]["ObjectOwnership"]
    except is_boto3_error_code(["OwnershipControlsNotFoundError", "NoSuchOwnershipControls"]):
        return None


def paginated_list(s3_client, **pagination_params) -> Iterator[List[str]]:
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


def paginated_versions_list(s3_client, **pagination_params) -> Iterator[List[Tuple[str, str]]]:
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


def delete_objects(s3_client, module: AnsibleAWSModule, name: str) -> None:
    """
    Delete objects from an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        module (AnsibleAWSModule): The Ansible module object.
        name (str): The name of the S3 bucket.
    Returns:
        None
    """
    try:
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
                    module.fail_json(
                        msg=(f"Could not empty bucket before deleting. Could not delete objects: {objects_to_delete}"),
                        errors=resp["Errors"],
                        response=resp,
                    )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed while deleting bucket")


def destroy_bucket(s3_client, module: AnsibleAWSModule) -> None:
    """
    This function destroys an S3 bucket.
    Parameters:
        s3_client (boto3.client): The Boto3 S3 client object.
        module (AnsibleAWSModule): The Ansible module object.
    Returns:
        None
    """
    force = module.params.get("force")
    name = module.params.get("name")
    try:
        bucket_is_present = bucket_exists(s3_client, name)
    except botocore.exceptions.EndpointConnectionError as e:
        module.fail_json_aws(e, msg=f"Invalid endpoint provided: {to_text(e)}")
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to check bucket presence")

    if not bucket_is_present:
        module.exit_json(changed=False)

    if force:
        # if there are contents then we need to delete them (including versions) before we can delete the bucket
        try:
            delete_objects(s3_client, module, name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed while deleting objects")

    try:
        delete_bucket(s3_client, name)
        s3_client.get_waiter("bucket_not_exists").wait(Bucket=name, WaiterConfig=dict(Delay=5, MaxAttempts=60))
    except botocore.exceptions.WaiterError as e:
        module.fail_json_aws(e, msg="An error occurred waiting for the bucket to be deleted.")
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to delete bucket")

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
        object_lock_default_retention="object_lock_enabled",
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

    if state == "present":
        create_or_update_bucket(s3_client, module)
    elif state == "absent":
        destroy_bucket(s3_client, module)


if __name__ == "__main__":
    main()
