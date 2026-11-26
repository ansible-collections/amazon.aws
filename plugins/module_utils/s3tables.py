# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from .botocore import is_boto3_error_code
from .errors import AWSErrorHandler
from .exceptions import AnsibleAWSError
from .retries import AWSRetry


class AnsibleS3TablesError(AnsibleAWSError):
    pass


class S3TablesErrorHandler(AWSErrorHandler):
    _CUSTOM_EXCEPTION = AnsibleS3TablesError

    @classmethod
    def _is_missing(cls):
        return is_boto3_error_code("NotFoundException")


@S3TablesErrorHandler.list_error_handler("list table buckets", [])
@AWSRetry.jittered_backoff()
def list_table_buckets(client, **params: Dict[str, Any]) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("list_table_buckets")
    return paginator.paginate(**params).build_full_result()["tableBuckets"]


def find_table_bucket(client, name: str) -> Optional[Dict[str, Any]]:
    """Find a table bucket by its exact name, using a prefix-filtered, paginated list_table_buckets."""
    for bucket in list_table_buckets(client, prefix=name):
        if bucket["name"] == name:
            return bucket
    return None


@S3TablesErrorHandler.list_error_handler("get table bucket {table_bucket_arn}", None)
@AWSRetry.jittered_backoff()
def get_table_bucket(client, table_bucket_arn: str) -> Optional[Dict[str, Any]]:
    return client.get_table_bucket(tableBucketARN=table_bucket_arn)


@S3TablesErrorHandler.common_error_handler("create table bucket {name}")
@AWSRetry.jittered_backoff()
def create_table_bucket(client, name: str, **params: Dict[str, Any]) -> str:
    return client.create_table_bucket(name=name, **params)["arn"]


@S3TablesErrorHandler.deletion_error_handler("delete table bucket {table_bucket_arn}")
@AWSRetry.jittered_backoff()
def delete_table_bucket(client, table_bucket_arn: str) -> bool:
    client.delete_table_bucket(tableBucketARN=table_bucket_arn)
    return True


@S3TablesErrorHandler.list_error_handler("list tags for resource {resource_arn}", {})
@AWSRetry.jittered_backoff()
def list_tags_for_resource(client, resource_arn: str) -> Dict[str, str]:
    return client.list_tags_for_resource(resourceArn=resource_arn)["tags"]


@S3TablesErrorHandler.common_error_handler("tag resource {resource_arn}")
@AWSRetry.jittered_backoff()
def tag_resource(client, resource_arn: str, tags: Dict[str, str]) -> bool:
    client.tag_resource(resourceArn=resource_arn, tags=tags)
    return True


@S3TablesErrorHandler.common_error_handler("untag resource {resource_arn}")
@AWSRetry.jittered_backoff()
def untag_resource(client, resource_arn: str, tag_keys: List[str]) -> bool:
    client.untag_resource(resourceArn=resource_arn, tagKeys=tag_keys)
    return True


@S3TablesErrorHandler.list_error_handler("get table bucket encryption {table_bucket_arn}", None)
@AWSRetry.jittered_backoff()
def get_table_bucket_encryption(client, table_bucket_arn: str) -> Optional[Dict[str, Any]]:
    return client.get_table_bucket_encryption(tableBucketARN=table_bucket_arn)["encryptionConfiguration"]


@S3TablesErrorHandler.common_error_handler("put table bucket encryption {table_bucket_arn}")
@AWSRetry.jittered_backoff()
def put_table_bucket_encryption(client, table_bucket_arn: str, encryption_configuration: Dict[str, Any]) -> bool:
    client.put_table_bucket_encryption(
        tableBucketARN=table_bucket_arn, encryptionConfiguration=encryption_configuration
    )
    return True


@S3TablesErrorHandler.list_error_handler("list tables for table bucket {table_bucket_arn}", [])
@AWSRetry.jittered_backoff()
def list_table_summaries(client, table_bucket_arn: str) -> List[Dict[str, Any]]:
    paginator = client.get_paginator("list_tables")
    return paginator.paginate(tableBucketARN=table_bucket_arn).build_full_result()["tables"]
