# -*- coding: utf-8 -*-

# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


try:
    import botocore
except ImportError:
    pass  # Handled by HAS_BOTO3


def get_backup_resource_tags(module, backup_client):
    resource = module.params.get("resource")
    try:
        response = backup_client.list_tags(ResourceArn=resource)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to list tags on the resource {0}".format(resource))

    return response["Tags"]
