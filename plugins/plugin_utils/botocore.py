# -*- coding: utf-8 -*-

# (c) 2022 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

try:
    import boto3
    import botocore
except ImportError:
    pass  # will be captured by imported HAS_BOTO3


import typing
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import Union

if typing.TYPE_CHECKING:
    from typing_extensions import TypeAlias

    from .base import AWSPluginBase

    ClientType: TypeAlias = botocore.client.BaseClient
    ResourceType: TypeAlias = boto3.resources.base.ServiceResource
    BotoConn = Union[ClientType, ResourceType, Tuple[ClientType, ResourceType]]

from ansible.module_utils.basic import to_native

from ansible_collections.amazon.aws.plugins.module_utils.botocore import _aws_connection_info
from ansible_collections.amazon.aws.plugins.module_utils.botocore import _aws_region
from ansible_collections.amazon.aws.plugins.module_utils.botocore import _boto3_conn
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleBotocoreError


def boto3_conn(
    plugin: AWSPluginBase,
    conn_type: str,
    resource: Optional[str] = None,
    region: Optional[str] = None,
    endpoint: Optional[str] = None,
    **params,
) -> BotoConn:
    """
    Builds a boto3 resource/client connection cleanly wrapping the most common failures.
    Handles:
        ValueError, botocore.exceptions.BotoCoreError
    """

    try:
        return _boto3_conn(conn_type=conn_type, resource=resource, region=region, endpoint=endpoint, **params)
    except ValueError as e:
        plugin.fail_aws("Couldn't connect to AWS", exception=e)
    except botocore.exceptions.NoRegionError:
        plugin.fail_aws(
            f"The {plugin.ansible_name} plugin requires a region and none was found in configuration, "  # pyright: ignore[reportAttributeAccessIssue]
            "environment variables or module parameters"
        )
    except botocore.exceptions.BotoCoreError as e:
        plugin.fail_aws("Couldn't connect to AWS", exception=e)


def get_aws_connection_info(plugin: AWSPluginBase) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
    try:
        return _aws_connection_info(plugin.get_options())  # pyright: ignore[reportAttributeAccessIssue]
    except AnsibleBotocoreError as e:
        plugin.fail_aws(to_native(e))


def get_aws_region(plugin: AWSPluginBase) -> Optional[str]:
    try:
        return _aws_region(plugin.get_options())  # pyright: ignore[reportAttributeAccessIssue]
    except AnsibleBotocoreError as e:
        plugin.fail_aws(to_native(e))
