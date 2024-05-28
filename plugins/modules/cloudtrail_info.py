#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: cloudtrail_info
version_added: 5.0.0
short_description: Gather information about trails in AWS Cloud Trail
description:
  - Gather information about trails in AWS CloudTrail.
author: "Gomathi Selvi Srinivasan (@GomathiselviS)"
options:
  trail_names:
    type: list
    elements: str
    default: []
    description:
      - Specifies a list of trail names, trail ARNs, or both, of the trails to describe.
      - If an empty list is specified, information for the trail in the current region is returned.
  include_shadow_trails:
    type: bool
    default: true
    description: Specifies whether to include shadow trails in the response.
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather information about all trails
- amazon.aws.cloudtrail_info:

# Gather information about a particular trail
- amazon.aws.cloudtrail_info:
    trail_names:
      - arn:aws:cloudtrail:us-east-2:123456789012:trail/MyTrail
"""

RETURN = r"""
trail_list:
    description: List of trail objects. Each element consists of a dict with all the information related to that cloudtrail.
    type: list
    elements: dict
    returned: always
    contains:
        name:
            description: Name of the trail.
            type: str
            sample: "MyTrail"
        s3_bucket_name:
            description: Name of the Amazon S3 bucket into which CloudTrail delivers the trail files.
            type: str
            sample: "aws-cloudtrail-logs-xxxx"
        s3_key_prefix:
            description: Amazon S3 key prefix that comes after the name of the bucket that is designated for log file delivery.
            type: str
            sample: "xxxx"
        sns_topic_arn:
            description: ARN of the Amazon SNS topic that CloudTrail uses to send notifications when log files are delivered.
            type: str
            sample: "arn:aws:sns:us-east-2:123456789012:MyTopic"
        include_global_service_events:
            description: If True, AWS API calls from AWS global services such as IAM are included.
            type: bool
            sample: true
        is_multi_region_trail:
            description: Specifies whether the trail exists only in one region or exists in all regions.
            type: bool
            sample: true
        home_region:
            description: The region in which the trail was created.
            type: str
            sample: "us-east-1"
        trail_arn:
            description: Specifies the ARN of the trail.
            type: str
            sample: "arn:aws:cloudtrail:us-east-2:123456789012:trail/MyTrail"
        log_file_validation_enabled:
            description: Specifies whether log file validation is enabled.
            type: bool
            sample: true
        cloud_watch_logs_log_group_arn:
            description: Specifies an ARN, that represents the log group to which CloudTrail logs will be delivered.
            type: str
            sample: "arn:aws:sns:us-east-2:123456789012:Mylog"
        cloud_watch_logs_role_arn:
            description: Specifies the role for the CloudWatch Logs endpoint to assume to write to a user's log group.
            type: str
            sample: "arn:aws:sns:us-east-2:123456789012:Mylog"
        kms_key_id:
            description: Specifies the KMS key ID that encrypts the logs delivered by CloudTrail.
            type: str
            sample: "arn:aws:kms:us-east-2:123456789012:key/12345678-1234-1234-1234-123456789012"
        has_custom_event_selectors:
            description: Specifies if the trail has custom event selectors.
            type: bool
            sample: true
        has_insight_selectors:
            description: Specifies whether a trail has insight types specified in an InsightSelector list.
            type: bool
            sample: true
        is_organization_trail:
            description: Specifies whether the trail is an organization trail.
            type: bool
            sample: true
        is_logging:
            description: Whether the CloudTrail is currently logging AWS API calls.
            type: bool
            sample: true
        latest_delivery_error:
            description: Displays any Amazon S3 error that CloudTrail encountered when attempting to deliver log files to the designated bucket.
            type: str
        latest_notification_attempt_time:
            description: Specifies the date and time that CloudTrail last attempt to deliver a notification.
            type: str
        latest_notification_attempt_succeeded:
            description: Specifies the date and time that CloudTrail last successful attempt to deliver a notification.
            type: str
        latest_notification_error:
            description: Displays any Amazon SNS error that CloudTrail encountered when attempting to send a notification.
            type: str
        latest_delivery_attempt_succeeded:
            description: Specifies the date and time that CloudTrail last successful attempt to deliver log files to an account's Amazon S3 bucket.
            type: str
        latest_delivery_attempt_time:
            description: Specifies the date and time that CloudTrail last attempt to deliver log files to an account's Amazon S3 bucket.
            type: str
        latest_delivery_time:
            description: Specifies the date and time that CloudTrail last delivered log files to an account's Amazon S3 bucket.
            type: str
        start_logging_time:
            description: Specifies the most recent date and time when CloudTrail started recording API calls for an AWS account.
            type: str
        stop_logging_time:
            description: Specifies the most recent date and time when CloudTrail stopped recording API calls for an AWS account.
            type: str
        latest_cloud_watch_logs_delivery_error:
            description: Displays any CloudWatch Logs error that CloudTrail encountered when attempting to deliver logs to CloudWatch Logs.
            type: str
        latest_cloud_watch_logs_delivery_time:
            description: Displays the most recent date and time when CloudTrail delivered logs to CloudWatch Logs.
            type: str
        latest_digest_delivery_time:
            description: Specifies the date and time that CloudTrail last delivered a digest file to an account's Amazon S3 bucket.
            type: str
        latest_digest_delivery_error:
            description: Displays any Amazon S3 error that CloudTrail encountered when attempting to deliver a digest file to the designated bucket.
            type: str
        resource_id:
            description: Specifies the ARN of the resource.
            type: str
        tags:
            description: Any tags assigned to the cloudtrail.
            type: dict
            returned: always
            sample: "{ 'my_tag_key': 'my_tag_value' }"
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import boto3_tag_list_to_ansible_dict


def get_trails(connection, module):
    all_trails = []
    try:
        result = connection.get_paginator("list_trails")
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to get the trails.")
    for trail in result.paginate():
        all_trails.extend(list_cloud_trails(trail))
    return all_trails


def list_cloud_trails(trail_dict):
    return [x["TrailARN"] for x in trail_dict["Trails"]]


def get_trail_detail(connection, module):
    output = {}
    trail_name_list = module.params.get("trail_names")
    include_shadow_trails = module.params.get("include_shadow_trails")
    if not trail_name_list:
        trail_name_list = get_trails(connection, module)
    try:
        result = connection.describe_trails(
            trailNameList=trail_name_list, includeShadowTrails=include_shadow_trails, aws_retry=True
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to get the trails.")
    # Turn the boto3 result in to ansible_friendly_snaked_names
    snaked_cloud_trail = []
    for cloud_trail in result["trailList"]:
        try:
            status_dict = connection.get_trail_status(Name=cloud_trail["TrailARN"], aws_retry=True)
            cloud_trail.update(status_dict)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to get the trail status")
        try:
            tag_list = connection.list_tags(ResourceIdList=[cloud_trail["TrailARN"]])
            for tag_dict in tag_list["ResourceTagList"]:
                cloud_trail.update(tag_dict)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.warn(f"Failed to get the trail tags - {e}")
        snaked_cloud_trail.append(camel_dict_to_snake_dict(cloud_trail))

    # Turn the boto3 result in to ansible friendly tag dictionary
    for tr in snaked_cloud_trail:
        if "tags_list" in tr:
            tr["tags"] = boto3_tag_list_to_ansible_dict(tr["tags_list"], "key", "value")
            del tr["tags_list"]
        if "response_metadata" in tr:
            del tr["response_metadata"]
    output["trail_list"] = snaked_cloud_trail
    return output


def main():
    argument_spec = dict(
        trail_names=dict(type="list", elements="str", default=[]),
        include_shadow_trails=dict(type="bool", default=True),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    try:
        connection = module.client("cloudtrail", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")
    result = get_trail_detail(connection, module)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
