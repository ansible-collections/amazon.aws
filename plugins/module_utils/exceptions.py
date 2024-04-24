# -*- coding: utf-8 -*-

# (c) 2022 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from typing import List
from typing import Union

from ansible.module_utils._text import to_native


class AnsibleAWSError(Exception):
    def __str__(self):
        if self.exception and self.message:
            return f"{self.message}: {to_native(self.exception)}"

        return super().__str__()

    def __init__(self, message=None, exception=None, **kwargs):
        if not message and not exception:
            super().__init__()
        elif not message:
            super().__init__(exception)
        else:
            super().__init__(message)

        self.exception = exception
        self.message = message

        # In places where passing more information to module.fail_json would be helpful
        # store the extra info.  Other plugin types have to raise the correct exception
        # such as AnsibleLookupError, so can't easily consume this.
        self.kwargs = kwargs or {}

    def is_boto3_error_code(self, code: Union[str, List[str]]) -> bool:
        """Check if the botocore exception is raised by a specific error code."""
        from botocore.exceptions import ClientError

        if not isinstance(code, list):
            code = [code]
        return (
            self.exception
            and isinstance(self.exception, ClientError)
            and self.exception.response["Error"]["Code"] in code
        )

    def is_boto3_error_message(self, msg: str) -> bool:
        """Check if the botocore exception contains a specific error message."""
        from botocore.exceptions import ClientError

        return (
            self.exception
            and isinstance(self.exception, ClientError)
            and msg in self.exception.response["Error"]["Message"]
        )


class AnsibleBotocoreError(AnsibleAWSError):
    pass
