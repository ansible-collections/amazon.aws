#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: cloudtrail
version_added: 5.0.0
short_description: manage CloudTrail create, delete, update
description:
  - Creates, deletes, or updates CloudTrail configuration. Ensures logging is also enabled.
  - This module was originally added to C(community.aws) in release 1.0.0.
author:
  - Ansible Core Team
  - Ted Timmons (@tedder)
  - Daniel Shepherd (@shepdelacreme)
options:
  state:
    description:
      - Add or remove CloudTrail configuration.
      - 'The following states have been preserved for backwards compatibility: I(state=enabled) and I(state=disabled).'
      - I(state=enabled) is equivalet to I(state=present).
      - I(state=disabled) is equivalet to I(state=absent).
    type: str
    choices: ['present', 'absent', 'enabled', 'disabled']
    default: present
  name:
    description:
      - Name for the CloudTrail.
      - Names are unique per-region unless the CloudTrail is a multi-region trail, in which case it is unique per-account.
    type: str
    default: default
  enable_logging:
    description:
      - Start or stop the CloudTrail logging. If stopped the trail will be paused and will not record events or deliver log files.
    default: true
    type: bool
  s3_bucket_name:
    description:
      - An existing S3 bucket where CloudTrail will deliver log files.
      - This bucket should exist and have the proper policy.
      - See U(https://docs.aws.amazon.com/awscloudtrail/latest/userguide/aggregating_logs_regions_bucket_policy.html).
      - Required when I(state=present).
    type: str
  s3_key_prefix:
    description:
      - S3 Key prefix for delivered log files. A trailing slash is not necessary and will be removed.
    type: str
  is_multi_region_trail:
    description:
      - Specify whether the trail belongs only to one region or exists in all regions.
    default: false
    type: bool
  enable_log_file_validation:
    description:
      - Specifies whether log file integrity validation is enabled.
      - CloudTrail will create a hash for every log file delivered and produce a signed digest file that can be used to ensure log files have not been tampered.
    type: bool
    aliases: [ "log_file_validation_enabled" ]
  include_global_events:
    description:
      - Record API calls from global services such as IAM and STS.
    default: true
    type: bool
    aliases: [ "include_global_service_events" ]
  sns_topic_name:
    description:
      - SNS Topic name to send notifications to when a log file is delivered.
    type: str
  cloudwatch_logs_role_arn:
    description:
      - Specifies a full ARN for an IAM role that assigns the proper permissions for CloudTrail to create and write to the log group.
      - See U(https://docs.aws.amazon.com/awscloudtrail/latest/userguide/send-cloudtrail-events-to-cloudwatch-logs.html).
      - Required when C(cloudwatch_logs_log_group_arn).
    type: str
  cloudwatch_logs_log_group_arn:
    description:
      - A full ARN specifying a valid CloudWatch log group to which CloudTrail logs will be delivered. The log group should already exist.
      - See U(https://docs.aws.amazon.com/awscloudtrail/latest/userguide/send-cloudtrail-events-to-cloudwatch-logs.html).
      - Required when C(cloudwatch_logs_role_arn).
    type: str
  kms_key_id:
    description:
      - Specifies the KMS key ID to use to encrypt the logs delivered by CloudTrail. This also has the effect of enabling log file encryption.
      - The value can be an alias name prefixed by "alias/", a fully specified ARN to an alias, a fully specified ARN to a key, or a globally unique identifier.
      - Encryption can be disabled by setting I(kms_key_id="").
      - See U(https://docs.aws.amazon.com/awscloudtrail/latest/userguide/encrypting-cloudtrail-log-files-with-aws-kms.html).
    type: str
notes:
  - The I(purge_tags) option was added in release 4.0.0

extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.tags
  - amazon.aws.boto3
"""

EXAMPLES = r"""
- name: create single region cloudtrail
  amazon.aws.cloudtrail:
    state: present
    name: default
    s3_bucket_name: mylogbucket
    s3_key_prefix: cloudtrail
    region: us-east-1

- name: create multi-region trail with validation and tags
  amazon.aws.cloudtrail:
    state: present
    name: default
    s3_bucket_name: mylogbucket
    region: us-east-1
    is_multi_region_trail: true
    enable_log_file_validation: true
    cloudwatch_logs_role_arn: "arn:aws:iam::123456789012:role/CloudTrail_CloudWatchLogs_Role"
    cloudwatch_logs_log_group_arn: "arn:aws:logs:us-east-1:123456789012:log-group:CloudTrail/DefaultLogGroup:*"
    kms_key_id: "alias/MyAliasName"
    tags:
      environment: dev
      Name: default

- name: show another valid kms_key_id
  amazon.aws.cloudtrail:
    state: present
    name: default
    s3_bucket_name: mylogbucket
    kms_key_id: "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"
    # simply "12345678-1234-1234-1234-123456789012" would be valid too.

- name: pause logging the trail we just created
  amazon.aws.cloudtrail:
    state: present
    name: default
    enable_logging: false
    s3_bucket_name: mylogbucket
    region: us-east-1
    is_multi_region_trail: true
    enable_log_file_validation: true
    tags:
      environment: dev
      Name: default

- name: delete a trail
  amazon.aws.cloudtrail:
    state: absent
    name: default
"""

RETURN = r"""
exists:
    description: whether the resource exists
    returned: always
    type: bool
    sample: true
trail:
    description: CloudTrail resource details
    returned: always
    type: complex
    sample: hash/dictionary of values
    contains:
        trail_arn:
            description: Full ARN of the CloudTrail resource
            returned: success
            type: str
            sample: arn:aws:cloudtrail:us-east-1:123456789012:trail/default
        name:
            description: Name of the CloudTrail resource
            returned: success
            type: str
            sample: default
        is_logging:
            description: Whether logging is turned on or paused for the Trail
            returned: success
            type: bool
            sample: True
        s3_bucket_name:
            description: S3 bucket name where log files are delivered
            returned: success
            type: str
            sample: myBucket
        s3_key_prefix:
            description: Key prefix in bucket where log files are delivered (if any)
            returned: success when present
            type: str
            sample: myKeyPrefix
        log_file_validation_enabled:
            description: Whether log file validation is enabled on the trail
            returned: success
            type: bool
            sample: true
        include_global_service_events:
            description: Whether global services (IAM, STS) are logged with this trail
            returned: success
            type: bool
            sample: true
        is_multi_region_trail:
            description: Whether the trail applies to all regions or just one
            returned: success
            type: bool
            sample: true
        has_custom_event_selectors:
            description: Whether any custom event selectors are used for this trail.
            returned: success
            type: bool
            sample: False
        home_region:
            description: The home region where the trail was originally created and must be edited.
            returned: success
            type: str
            sample: us-east-1
        sns_topic_name:
            description: The SNS topic name where log delivery notifications are sent.
            returned: success when present
            type: str
            sample: myTopic
        sns_topic_arn:
            description: Full ARN of the SNS topic where log delivery notifications are sent.
            returned: success when present
            type: str
            sample: arn:aws:sns:us-east-1:123456789012:topic/myTopic
        cloud_watch_logs_log_group_arn:
            description: Full ARN of the CloudWatch Logs log group where events are delivered.
            returned: success when present
            type: str
            sample: arn:aws:logs:us-east-1:123456789012:log-group:CloudTrail/DefaultLogGroup:*
        cloud_watch_logs_role_arn:
            description: Full ARN of the IAM role that CloudTrail assumes to deliver events.
            returned: success when present
            type: str
            sample: arn:aws:iam::123456789012:role/CloudTrail_CloudWatchLogs_Role
        kms_key_id:
            description: Full ARN of the KMS Key used to encrypt log files.
            returned: success when present
            type: str
            sample: arn:aws:kms::123456789012:key/12345678-1234-1234-1234-123456789012
        tags:
            description: hash/dictionary of tags applied to this resource
            returned: success
            type: dict
            sample: {'environment': 'dev', 'Name': 'default'}
"""

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.tagging import ansible_dict_to_boto3_tag_list
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags


def get_kms_key_aliases(module, client, keyId):
    """
    get list of key aliases

    module : AnsibleAWSModule object
    client : boto3 client connection object for kms
    keyId : keyId to get aliases for
    """
    try:
        key_resp = client.list_aliases(KeyId=keyId)
    except (BotoCoreError, ClientError):
        # Don't fail here, just return [] to maintain backwards compat
        # in case user doesn't have kms:ListAliases permissions
        return []

    return key_resp["Aliases"]


def create_trail(module, client, ct_params):
    """
    Creates a CloudTrail

    module : AnsibleAWSModule object
    client : boto3 client connection object
    ct_params : The parameters for the Trail to create
    """
    resp = {}
    try:
        resp = client.create_trail(**ct_params)
    except (BotoCoreError, ClientError) as err:
        module.fail_json_aws(err, msg="Failed to create Trail")

    return resp


def tag_trail(module, client, tags, trail_arn, curr_tags=None, purge_tags=True):
    """
    Creates, updates, removes tags on a CloudTrail resource

    module : AnsibleAWSModule object
    client : boto3 client connection object
    tags : Dict of tags converted from ansible_dict to boto3 list of dicts
    trail_arn : The ARN of the CloudTrail to operate on
    curr_tags : Dict of the current tags on resource, if any
    dry_run : true/false to determine if changes will be made if needed
    """

    if tags is None:
        return False

    curr_tags = curr_tags or {}

    tags_to_add, tags_to_remove = compare_aws_tags(curr_tags, tags, purge_tags=purge_tags)
    if not tags_to_add and not tags_to_remove:
        return False

    if module.check_mode:
        return True

    if tags_to_remove:
        remove = {k: curr_tags[k] for k in tags_to_remove}
        tags_to_remove = ansible_dict_to_boto3_tag_list(remove)
        try:
            client.remove_tags(ResourceId=trail_arn, TagsList=tags_to_remove)
        except (BotoCoreError, ClientError) as err:
            module.fail_json_aws(err, msg="Failed to remove tags from Trail")

    if tags_to_add:
        tags_to_add = ansible_dict_to_boto3_tag_list(tags_to_add)
        try:
            client.add_tags(ResourceId=trail_arn, TagsList=tags_to_add)
        except (BotoCoreError, ClientError) as err:
            module.fail_json_aws(err, msg="Failed to add tags to Trail")

    return True


def get_tag_list(keys, tags):
    """
    Returns a list of dicts with tags to act on
    keys : set of keys to get the values for
    tags : the dict of tags to turn into a list
    """
    tag_list = []
    for k in keys:
        tag_list.append({"Key": k, "Value": tags[k]})

    return tag_list


def set_logging(module, client, name, action):
    """
    Starts or stops logging based on given state

    module : AnsibleAWSModule object
    client : boto3 client connection object
    name : The name or ARN of the CloudTrail to operate on
    action : start or stop
    """
    if action == "start":
        try:
            client.start_logging(Name=name)
            return client.get_trail_status(Name=name)
        except (BotoCoreError, ClientError) as err:
            module.fail_json_aws(err, msg="Failed to start logging")
    elif action == "stop":
        try:
            client.stop_logging(Name=name)
            return client.get_trail_status(Name=name)
        except (BotoCoreError, ClientError) as err:
            module.fail_json_aws(err, msg="Failed to stop logging")
    else:
        module.fail_json(msg="Unsupported logging action")


def get_trail_facts(module, client, name):
    """
    Describes existing trail in an account

    module : AnsibleAWSModule object
    client : boto3 client connection object
    name : Name of the trail
    """
    # get Trail info
    try:
        trail_resp = client.describe_trails(trailNameList=[name])
    except (BotoCoreError, ClientError) as err:
        module.fail_json_aws(err, msg="Failed to describe Trail")

    # Now check to see if our trail exists and get status and tags
    if len(trail_resp["trailList"]):
        trail = trail_resp["trailList"][0]
        try:
            status_resp = client.get_trail_status(Name=trail["Name"])
            tags_list = client.list_tags(ResourceIdList=[trail["TrailARN"]])
        except (BotoCoreError, ClientError) as err:
            module.fail_json_aws(err, msg="Failed to describe Trail")

        trail["IsLogging"] = status_resp["IsLogging"]
        trail["tags"] = boto3_tag_list_to_ansible_dict(tags_list["ResourceTagList"][0]["TagsList"])
        # Check for non-existent values and populate with None
        optional_vals = set(
            [
                "S3KeyPrefix",
                "SnsTopicName",
                "SnsTopicARN",
                "CloudWatchLogsLogGroupArn",
                "CloudWatchLogsRoleArn",
                "KmsKeyId",
            ]
        )
        for v in optional_vals - set(trail.keys()):
            trail[v] = None
        return trail

    else:
        # trail doesn't exist return None
        return None


def delete_trail(module, client, trail_arn):
    """
    Delete a CloudTrail

    module : AnsibleAWSModule object
    client : boto3 client connection object
    trail_arn : Full CloudTrail ARN
    """
    try:
        client.delete_trail(Name=trail_arn)
    except (BotoCoreError, ClientError) as err:
        module.fail_json_aws(err, msg="Failed to delete Trail")


def update_trail(module, client, ct_params):
    """
    Delete a CloudTrail

    module : AnsibleAWSModule object
    client : boto3 client connection object
    ct_params : The parameters for the Trail to update
    """
    try:
        client.update_trail(**ct_params)
    except (BotoCoreError, ClientError) as err:
        module.fail_json_aws(err, msg="Failed to update Trail")


def main():
    argument_spec = dict(
        state=dict(default="present", choices=["present", "absent", "enabled", "disabled"]),
        name=dict(default="default"),
        enable_logging=dict(default=True, type="bool"),
        s3_bucket_name=dict(),
        s3_key_prefix=dict(no_log=False),
        sns_topic_name=dict(),
        is_multi_region_trail=dict(default=False, type="bool"),
        enable_log_file_validation=dict(type="bool", aliases=["log_file_validation_enabled"]),
        include_global_events=dict(default=True, type="bool", aliases=["include_global_service_events"]),
        cloudwatch_logs_role_arn=dict(),
        cloudwatch_logs_log_group_arn=dict(),
        kms_key_id=dict(),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(default=True, type="bool"),
    )

    required_if = [("state", "present", ["s3_bucket_name"]), ("state", "enabled", ["s3_bucket_name"])]
    required_together = [("cloudwatch_logs_role_arn", "cloudwatch_logs_log_group_arn")]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_together=required_together,
        required_if=required_if,
    )

    # collect parameters
    if module.params["state"] in ("present", "enabled"):
        state = "present"
    elif module.params["state"] in ("absent", "disabled"):
        state = "absent"
    tags = module.params["tags"]
    purge_tags = module.params["purge_tags"]
    enable_logging = module.params["enable_logging"]
    ct_params = dict(
        Name=module.params["name"],
        S3BucketName=module.params["s3_bucket_name"],
        IncludeGlobalServiceEvents=module.params["include_global_events"],
        IsMultiRegionTrail=module.params["is_multi_region_trail"],
    )

    if module.params["s3_key_prefix"]:
        ct_params["S3KeyPrefix"] = module.params["s3_key_prefix"].rstrip("/")

    if module.params["sns_topic_name"]:
        ct_params["SnsTopicName"] = module.params["sns_topic_name"]

    if module.params["cloudwatch_logs_role_arn"]:
        ct_params["CloudWatchLogsRoleArn"] = module.params["cloudwatch_logs_role_arn"]

    if module.params["cloudwatch_logs_log_group_arn"]:
        ct_params["CloudWatchLogsLogGroupArn"] = module.params["cloudwatch_logs_log_group_arn"]

    if module.params["enable_log_file_validation"] is not None:
        ct_params["EnableLogFileValidation"] = module.params["enable_log_file_validation"]

    if module.params["kms_key_id"] is not None:
        ct_params["KmsKeyId"] = module.params["kms_key_id"]

    client = module.client("cloudtrail")
    region = module.region

    results = dict(changed=False, exists=False)

    # Get existing trail facts
    trail = get_trail_facts(module, client, ct_params["Name"])

    # If the trail exists set the result exists variable
    if trail is not None:
        results["exists"] = True
        initial_kms_key_id = trail.get("KmsKeyId")

    if state == "absent" and results["exists"]:
        # If Trail exists go ahead and delete
        results["changed"] = True
        results["exists"] = False
        results["trail"] = dict()
        if not module.check_mode:
            delete_trail(module, client, trail["TrailARN"])

    elif state == "present" and results["exists"]:
        # If Trail exists see if we need to update it
        do_update = False
        for key in ct_params:
            tkey = str(key)
            # boto3 has inconsistent parameter naming so we handle it here
            if key == "EnableLogFileValidation":
                tkey = "LogFileValidationEnabled"
            # We need to make an empty string equal None
            if ct_params.get(key) == "":
                val = None
            else:
                val = ct_params.get(key)
            if val != trail.get(tkey):
                do_update = True
                if tkey != "KmsKeyId":
                    # We'll check if the KmsKeyId casues changes later since
                    # user could've provided a key alias, alias arn, or key id
                    # and trail['KmsKeyId'] is always a key arn
                    results["changed"] = True
                # If we are in check mode copy the changed values to the trail facts in result output to show what would change.
                if module.check_mode:
                    trail.update({tkey: ct_params.get(key)})

        if not module.check_mode and do_update:
            update_trail(module, client, ct_params)
            trail = get_trail_facts(module, client, ct_params["Name"])

        # Determine if KmsKeyId changed
        if not module.check_mode:
            if initial_kms_key_id != trail.get("KmsKeyId"):
                results["changed"] = True
        else:
            new_key = ct_params.get("KmsKeyId")
            if initial_kms_key_id != new_key:
                # Assume changed for a moment
                results["changed"] = True

                # However, new_key could be a key id, alias arn, or alias name
                # that maps back to the key arn in initial_kms_key_id. So check
                # all aliases for a match.
                initial_aliases = get_kms_key_aliases(module, module.client("kms"), initial_kms_key_id)
                for a in initial_aliases:
                    if a["AliasName"] == new_key or a["AliasArn"] == new_key or a["TargetKeyId"] == new_key:
                        results["changed"] = False

        # Check if we need to start/stop logging
        if enable_logging and not trail["IsLogging"]:
            results["changed"] = True
            trail["IsLogging"] = True
            if not module.check_mode:
                set_logging(module, client, name=ct_params["Name"], action="start")
        if not enable_logging and trail["IsLogging"]:
            results["changed"] = True
            trail["IsLogging"] = False
            if not module.check_mode:
                set_logging(module, client, name=ct_params["Name"], action="stop")

        # Check if we need to update tags on resource
        tags_changed = tag_trail(
            module, client, tags=tags, trail_arn=trail["TrailARN"], curr_tags=trail["tags"], purge_tags=purge_tags
        )
        if tags_changed:
            updated_tags = dict()
            if not purge_tags:
                updated_tags = trail["tags"]
            updated_tags.update(tags)
            results["changed"] = True
            trail["tags"] = updated_tags

        # Populate trail facts in output
        results["trail"] = camel_dict_to_snake_dict(trail, ignore_list=["tags"])

    elif state == "present" and not results["exists"]:
        # Trail doesn't exist just go create it
        results["changed"] = True
        results["exists"] = True
        if not module.check_mode:
            if tags:
                ct_params["TagsList"] = ansible_dict_to_boto3_tag_list(tags)
            # If we aren't in check_mode then actually create it
            created_trail = create_trail(module, client, ct_params)
            # Get the trail status
            try:
                status_resp = client.get_trail_status(Name=created_trail["Name"])
            except (BotoCoreError, ClientError) as err:
                module.fail_json_aws(err, msg="Failed to fetch Trail statuc")
            # Set the logging state for the trail to desired value
            if enable_logging and not status_resp["IsLogging"]:
                set_logging(module, client, name=ct_params["Name"], action="start")
            if not enable_logging and status_resp["IsLogging"]:
                set_logging(module, client, name=ct_params["Name"], action="stop")
            # Get facts for newly created Trail
            trail = get_trail_facts(module, client, ct_params["Name"])

        # If we are in check mode create a fake return structure for the newly minted trail
        if module.check_mode:
            acct_id = "123456789012"
            try:
                sts_client = module.client("sts")
                acct_id = sts_client.get_caller_identity()["Account"]
            except (BotoCoreError, ClientError):
                pass
            trail = dict()
            trail.update(ct_params)
            if "EnableLogFileValidation" not in ct_params:
                ct_params["EnableLogFileValidation"] = False
            trail["EnableLogFileValidation"] = ct_params["EnableLogFileValidation"]
            trail.pop("EnableLogFileValidation")
            fake_arn = "arn:aws:cloudtrail:" + region + ":" + acct_id + ":trail/" + ct_params["Name"]
            trail["HasCustomEventSelectors"] = False
            trail["HomeRegion"] = region
            trail["TrailARN"] = fake_arn
            trail["IsLogging"] = enable_logging
            trail["tags"] = tags
        # Populate trail facts in output
        results["trail"] = camel_dict_to_snake_dict(trail, ignore_list=["tags"])

    module.exit_json(**results)


if __name__ == "__main__":
    main()
