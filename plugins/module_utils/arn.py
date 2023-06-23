# -*- coding: utf-8 -*-

#  Copyright 2017 Michael De La Rue | Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import re


def validate_aws_arn(
    arn, partition=None, service=None, region=None, account_id=None, resource=None, resource_type=None, resource_id=None
):
    details = parse_aws_arn(arn)

    if not details:
        return False

    if partition and details.get("partition") != partition:
        return False
    if service and details.get("service") != service:
        return False
    if region and details.get("region") != region:
        return False
    if account_id and details.get("account_id") != account_id:
        return False
    if resource and details.get("resource") != resource:
        return False
    if resource_type and details.get("resource_type") != resource_type:
        return False
    if resource_id and details.get("resource_id") != resource_id:
        return False

    return True


def parse_aws_arn(arn):
    """
    Based on https://docs.aws.amazon.com/IAM/latest/UserGuide/reference-arns.html

    The following are the general formats for ARNs.
        arn:partition:service:region:account-id:resource-id
        arn:partition:service:region:account-id:resource-type/resource-id
        arn:partition:service:region:account-id:resource-type:resource-id
    The specific formats depend on the resource.
    The ARNs for some resources omit the Region, the account ID, or both the Region and the account ID.

    Note: resource_type handling is very naive, for complex cases it may be necessary to use
    "resource" directly instead of resource_type, this will include the resource type and full ID,
    including all paths.
    """
    m = re.search(r"arn:(aws(-([a-z\-]+))?):([\w-]+):([a-z0-9\-]*):(\d*|aws|aws-managed):(.*)", arn)
    if m is None:
        return None
    result = dict()
    result.update(dict(partition=m.group(1)))
    result.update(dict(service=m.group(4)))
    result.update(dict(region=m.group(5)))
    result.update(dict(account_id=m.group(6)))
    result.update(dict(resource=m.group(7)))

    m2 = re.search(r"^(.*?)[:/](.+)$", m.group(7))
    if m2 is None:
        result.update(dict(resource_type=None, resource_id=m.group(7)))
    else:
        result.update(dict(resource_type=m2.group(1), resource_id=m2.group(2)))

    return result


# An implementation of this used was originally in ec2.py, however Outposts
# aren't specific to the EC2 service
def is_outpost_arn(arn):
    """
    Validates that the ARN is for an AWS Outpost


    API Specification Document:
    https://docs.aws.amazon.com/outposts/latest/APIReference/API_Outpost.html
    """
    details = parse_aws_arn(arn)

    if not details:
        return False

    service = details.get("service") or ""
    if service.lower() != "outposts":
        return False
    resource = details.get("resource") or ""
    if not re.match("^outpost/op-[a-f0-9]{17}$", resource):
        return False

    return True
