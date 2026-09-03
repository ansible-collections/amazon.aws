# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import sys
import warnings
from collections.abc import MutableMapping
from io import BytesIO

import pytest

import ansible.module_utils.basic
import ansible.module_utils.common
from ansible.module_utils.common.text.converters import to_bytes


@pytest.fixture(autouse=True)
def reset_ansible_traceback_cache():
    # ansible-core >= 2.19 decides module-side traceback reporting from the
    # `_ansible_tracebacks_for` module argument and caches the result in a
    # process-global (`_traceback._module_tracebacks_enabled_events`). Reset it
    # around every test so enabling tracebacks in one test does not leak into
    # others. Older cores don't have this module; ignore the ImportError.
    try:
        from ansible.module_utils._internal import _traceback
    except ImportError:
        _traceback = None

    def _reset():
        if _traceback is not None:
            _traceback._module_tracebacks_enabled_events = None

    _reset()
    yield
    _reset()


@pytest.fixture(name="stdin")
def fixture_stdin(mocker, request):
    old_args = ansible.module_utils.basic._ANSIBLE_ARGS
    ansible.module_utils.basic._ANSIBLE_ARGS = None
    old_argv = sys.argv
    sys.argv = ["ansible_unittest"]

    for var in ["_global_warnings", "_global_deprecations"]:
        if hasattr(ansible.module_utils.common.warnings, var):
            vtype = type(getattr(ansible.module_utils.common.warnings, var))
            setattr(ansible.module_utils.common.warnings, var, vtype())
        else:
            # No need to reset the value
            warnings.warn("deprecated")

    if isinstance(request.param, str):
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
    mocker.patch("ansible.module_utils.basic.sys.stdin", mocker.MagicMock())
    mocker.patch("ansible.module_utils.basic.sys.stdin.buffer", fake_stdin)

    yield fake_stdin

    ansible.module_utils.basic._ANSIBLE_ARGS = old_args
    sys.argv = old_argv


@pytest.fixture(name="am")
def fixture_am(stdin, request):
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
