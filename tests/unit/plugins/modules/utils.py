import json
import unittest
from unittest.mock import patch

from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes

cur_context = None


def set_module_args(args):
    global cur_context

    if "_ansible_remote_tmp" not in args:
        args["_ansible_remote_tmp"] = "/tmp"
    if "_ansible_keep_remote_files" not in args:
        args["_ansible_keep_remote_files"] = False

    # Clean up any previous context manager if it exists
    if cur_context is not None:
        try:
            cur_context.__exit__(None, None, None)
        except Exception:
            pass
        cur_context = None

    # Try to use the newer patch_module_args
    try:
        from ansible.module_utils.testing import patch_module_args

        cur_context = patch_module_args(args)
        cur_context.__enter__()
    except ImportError:
        # Fall back to original behavior for older Ansible versions
        serialized_args = json.dumps({"ANSIBLE_MODULE_ARGS": args})
        basic._ANSIBLE_ARGS = to_bytes(serialized_args)


class AnsibleExitJson(Exception):
    pass


class AnsibleFailJson(Exception):
    pass


def exit_json(*args, **kwargs):
    if "changed" not in kwargs:
        kwargs["changed"] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    kwargs["failed"] = True
    raise AnsibleFailJson(kwargs)


class ModuleTestCase(unittest.TestCase):
    def setUp(self):
        self.mock_module = patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)
        self.mock_module.start()
        self.mock_sleep = patch("time.sleep")
        self.mock_sleep.start()
        set_module_args({})
        self.addCleanup(self.mock_module.stop)
        self.addCleanup(self.mock_sleep.stop)
