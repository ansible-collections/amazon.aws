# -*- coding: utf-8 -*-

#  Copyright 2017 Michael De La Rue | Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import re


def parse_aws_arn(arn):
    """
    The following are the general formats for ARNs.
        arn:partition:service:region:account-id:resource-id
        arn:partition:service:region:account-id:resource-type/resource-id
        arn:partition:service:region:account-id:resource-type:resource-id
    The specific formats depend on the resource.
    The ARNs for some resources omit the Region, the account ID, or both the Region and the account ID.
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
