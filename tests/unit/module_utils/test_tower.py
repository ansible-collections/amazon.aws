# (c) 2022 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# import pytest

import ansible_collections.amazon.aws.plugins.module_utils.tower as utils_tower

WINDOWS_DOWNLOAD = "Invoke-Expression ((New-Object System.Net.Webclient).DownloadString(" \
    "'https://raw.githubusercontent.com/ansible/ansible/devel/examples/scripts/ConfigureRemotingForAnsible.ps1'))"
EXAMPLE_PASSWORD = 'MY_EXAMPLE_PASSWORD'
WINDOWS_INVOKE = "$admin.PSBase.Invoke('SetPassword', 'MY_EXAMPLE_PASSWORD'"

EXAMPLE_TOWER = "tower.example.com"
EXAMPLE_TEMPLATE = 'My Template'
EXAMPLE_KEY = '123EXAMPLE123'
LINUX_TRIGGER_V1 = 'https://tower.example.com/api/v1/job_templates/My%20Template/callback/'
LINUX_TRIGGER_V2 = 'https://tower.example.com/api/v2/job_templates/My%20Template/callback/'


def test_windows_callback_no_password():
    user_data = utils_tower._windows_callback_script()
    assert WINDOWS_DOWNLOAD in user_data
    assert 'SetPassword' not in user_data


def test_windows_callback_password():
    user_data = utils_tower._windows_callback_script(EXAMPLE_PASSWORD)
    assert WINDOWS_DOWNLOAD in user_data
    assert WINDOWS_INVOKE in user_data


def test_linux_callback_with_name():
    user_data = utils_tower._linux_callback_script(EXAMPLE_TOWER, EXAMPLE_TEMPLATE, EXAMPLE_KEY)
    assert LINUX_TRIGGER_V1 in user_data
    assert LINUX_TRIGGER_V2 in user_data
