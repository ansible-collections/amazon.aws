# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from typing import Any
from typing import Dict
from typing import Optional

try:
    from boto3.session import Session
    from botocore.client import Config
except ImportError:
    pass


class AwsConnectionPluginBase:
    def __init__(self) -> None:
        pass

    def _get_boto_client(
        self,
        service: str,
        region_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Gets a boto3 client based on the STS token"""

        aws_access_key_id = self.get_option("access_key_id")
        aws_secret_access_key = self.get_option("secret_access_key")
        aws_session_token = self.get_option("session_token")

        session_args = dict(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name=region_name,
        )
        profile_name = self.get_option("profile")
        if profile_name:
            session_args["profile_name"] = profile_name
        session = Session(**session_args)
        params = {}
        if endpoint_url:
            params["endpoint_url"] = endpoint_url
        if config:
            params["config"] = Config(**config)

        return session.client(service, **params)
