# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import sys
import warnings
from io import BytesIO

import pytest

import ansible.module_utils.basic
import ansible.module_utils.common
from ansible.module_utils._text import to_bytes
from ansible.module_utils.common._collections_compat import MutableMapping
from ansible.module_utils.six import PY3
from ansible.module_utils.six import string_types


@pytest.fixture
def stdin(mocker, request):
    old_args = ansible.module_utils.basic._ANSIBLE_ARGS
    ansible.module_utils.basic._ANSIBLE_ARGS = None
    old_argv = sys.argv
    sys.argv = ["ansible_unittest"]

    for var in ["_global_warnings", "_global_deprecations"]:
        if hasattr(ansible.module_utils.common.warnings, var):
            setattr(ansible.module_utils.common.warnings, var, [])
        else:
            # No need to reset the value
            warnings.warn("deprecated")

    if isinstance(request.param, string_types):
        args = request.param
    elif isinstance(request.param, MutableMapping):
        if "ANSIBLE_MODULE_ARGS" not in request.param:
            request.param = {"ANSIBLE_MODULE_ARGS": request.param}
        if "_ansible_remote_tmp" not in request.param["ANSIBLE_MODULE_ARGS"]:
            request.param["ANSIBLE_MODULE_ARGS"]["_ansible_remote_tmp"] = "/tmp"
        if "_ansible_keep_remote_files" not in request.param["ANSIBLE_MODULE_ARGS"]:
            request.param["ANSIBLE_MODULE_ARGS"]["_ansible_keep_remote_files"] = False
        args = json.dumps(request.param)
    else:
        raise Exception("Malformed data to the stdin pytest fixture")

    fake_stdin = BytesIO(to_bytes(args, errors="surrogate_or_strict"))
    if PY3:
        mocker.patch("ansible.module_utils.basic.sys.stdin", mocker.MagicMock())
        mocker.patch("ansible.module_utils.basic.sys.stdin.buffer", fake_stdin)
    else:
        mocker.patch("ansible.module_utils.basic.sys.stdin", fake_stdin)

    yield fake_stdin

    ansible.module_utils.basic._ANSIBLE_ARGS = old_args
    sys.argv = old_argv


@pytest.fixture
def am(stdin, request):
    old_args = ansible.module_utils.basic._ANSIBLE_ARGS
    ansible.module_utils.basic._ANSIBLE_ARGS = None
    old_argv = sys.argv
    sys.argv = ["ansible_unittest"]

    argspec = {}
    if hasattr(request, "param"):
        if isinstance(request.param, dict):
            argspec = request.param

    am = ansible.module_utils.basic.AnsibleModule(
        argument_spec=argspec,
    )
    am._name = "ansible_unittest"

    yield am

    ansible.module_utils.basic._ANSIBLE_ARGS = old_args
    sys.argv = old_argv
