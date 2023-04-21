# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import string
import textwrap

from ansible.module_utils._text import to_native
from ansible.module_utils.six.moves.urllib import parse as urlparse


def _windows_callback_script(passwd=None):
    script_url = (
        "https://raw.githubusercontent.com/ansible/ansible/devel/examples/scripts/ConfigureRemotingForAnsible.ps1"
    )
    if passwd is not None:
        passwd = passwd.replace("'", "''")
        script_tpl = """\
        <powershell>
        $admin = [adsi]('WinNT://./administrator, user')
        $admin.PSBase.Invoke('SetPassword', '${PASS}')
        Invoke-Expression ((New-Object System.Net.Webclient).DownloadString('${SCRIPT}'))
        </powershell>
        """
    else:
        script_tpl = """\
        <powershell>
        $admin = [adsi]('WinNT://./administrator, user')
        Invoke-Expression ((New-Object System.Net.Webclient).DownloadString('${SCRIPT}'))
        </powershell>
        """

    tpl = string.Template(textwrap.dedent(script_tpl))
    return tpl.safe_substitute(PASS=passwd, SCRIPT=script_url)


def _linux_callback_script(tower_address, template_id, host_config_key):
    template_id = urlparse.quote(template_id)
    tower_address = urlparse.quote(tower_address)
    host_config_key = host_config_key.replace("'", "'\"'\"'")

    script_tpl = """\
    #!/bin/bash
    set -x

    retry_attempts=10
    attempt=0
    while [[ $attempt -lt $retry_attempts ]]
    do
      status_code=$(curl --max-time 10 -v -k -s -i \
        --data 'host_config_key=${host_config_key}' \
        'https://${tower_address}/api/v2/job_templates/${template_id}/callback/' \
        | head -n 1 \
        | awk '{print $2}')
      if [[ $status_code == 404 ]]
        then
        status_code=$(curl --max-time 10 -v -k -s -i \
          --data 'host_config_key=${host_config_key}' \
          'https://${tower_address}/api/v1/job_templates/${template_id}/callback/' \
          | head -n 1 \
          | awk '{print $2}')
        # fall back to using V1 API for Tower 3.1 and below, since v2 API will always 404
      fi
      if [[ $status_code == 201 ]]
        then
        exit 0
      fi
      attempt=$(( attempt + 1 ))
      echo "$${status_code} received... retrying in 1 minute. (Attempt $${attempt})"
      sleep 60
    done
    exit 1
    """
    tpl = string.Template(textwrap.dedent(script_tpl))
    return tpl.safe_substitute(tower_address=tower_address, template_id=template_id, host_config_key=host_config_key)


def tower_callback_script(tower_address, job_template_id, host_config_key, windows, passwd):
    if windows:
        return to_native(_windows_callback_script(passwd=passwd))
    return _linux_callback_script(tower_address, job_template_id, host_config_key)
