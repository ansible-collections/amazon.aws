# -*- coding: utf-8 -*-

# (c) 2022 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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


def is_ansible_aws_error_code(code, e=None):
    """Check if the AnsibleAWSError exception is raised by a botocore exception with specific error code.

    Returns AnsibleAWSError if the error code matches, a dummy exception if it does not have an error code or does not match

    Example:
    try:
        describe_instances(connection, InstanceIds=['potato'])
    except is_ansible_aws_error_code('InvalidInstanceID.Malformed'):
        # handle the error for that code case
    except AnsibleAWSError as e:
        # handle the generic error case for all other codes
    """
    from botocore.exceptions import ClientError

    if e is None:
        import sys

        e = sys.exc_info()[1]
    if not isinstance(code, (list, tuple, set)):
        code = [code]
    if (
        isinstance(e, AnsibleAWSError)
        and e.exception
        and isinstance(e.exception, ClientError)
        and e.exception.response["Error"]["Code"] in code
    ):
        return AnsibleAWSError
    return type("NeverEverRaisedException", (Exception,), {})


def is_ansible_aws_error_message(msg, e=None):
    """Check if the AnsibleAWSError exception raised by a botocore exception contains a specific error message.

    Returns AnsibleAWSError if the error code matches, a dummy exception if it does not have an error code or does not match

    Example:
    try:
        describe_vpc_classic_link(connection, VpcIds=[vpc_id])
    except is_ansible_aws_error_message('The functionality you requested is not available in this region.'):
        # handle the error for that error message
    except AnsibleAWSError as e:
        # handle the generic error case for all other codes
    """
    from botocore.exceptions import ClientError

    if e is None:
        import sys

        e = sys.exc_info()[1]
    if (
        isinstance(e, AnsibleAWSError)
        and e.exception
        and isinstance(e.exception, ClientError)
        and msg in e.exception.response["Error"]["Message"]
    ):
        return AnsibleAWSError
    return type("NeverEverRaisedException", (Exception,), {})


class AnsibleBotocoreError(AnsibleAWSError):
    pass
