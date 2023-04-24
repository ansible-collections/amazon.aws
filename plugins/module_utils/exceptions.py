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


class AnsibleBotocoreError(AnsibleAWSError):
    pass
