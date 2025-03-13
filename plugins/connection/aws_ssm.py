# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Pat Sharkey <psharkey@cleo.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Based on the ssh connection plugin by Michael DeHaan


DOCUMENTATION = r"""
name: aws_ssm
author:
  - Pat Sharkey (@psharkey) <psharkey@cleo.com>
  - HanumanthaRao MVL (@hanumantharaomvl) <hanumanth@flux7.com>
  - Gaurav Ashtikar (@gau1991) <gaurav.ashtikar@flux7.com>

short_description: connect to EC2 instances via AWS Systems Manager
description:
  - This connection plugin allows Ansible to execute tasks on an EC2 instance via an AWS SSM Session.
notes:
  - The C(community.aws.aws_ssm) connection plugin does not support using the ``remote_user`` and
    ``ansible_user`` variables to configure the remote user.  The ``become_user`` parameter should
    be used to configure which user to run commands as.  Remote commands will often default to
    running as the ``ssm-agent`` user, however this will also depend on how SSM has been configured.
  - This plugin requires an S3 bucket to send files to/from the remote instance. This is required even for modules
    which do not explicitly send files (such as the C(shell) or C(command) modules), because Ansible sends over the C(.py) files of the module itself, via S3.
  - Files sent via S3 will be named in S3 with the EC2 host ID (e.g. C(i-123abc/)) as the prefix.
  - The files in S3 will be deleted by the end of the playbook run. If the play is terminated ungracefully, the files may remain in the bucket.
    If the bucket has versioning enabled, the files will remain in version history. If your tasks involve sending secrets to/from the remote instance
    (e.g. within a C(shell) command, or a SQL password in the C(community.postgresql.postgresql_query) module) then those passwords will be included in
    plaintext in those files in S3 indefinitely, visible to anyone with access to that bucket. Therefore it is recommended to use a bucket with versioning
    disabled/suspended.
  - The files in S3 will be deleted even if the C(keep_remote_files) setting is C(true).

requirements:
  - The remote EC2 instance must be running the AWS Systems Manager Agent (SSM Agent).
    U(https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-getting-started.html)
  - The control machine must have the AWS session manager plugin installed.
    U(https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)
  - The remote EC2 Linux instance must have curl installed.
  - The remote EC2 Linux instance and the controller both need network connectivity to S3.
  - The remote instance does not require IAM credentials for S3. This module will generate a presigned URL for S3 from the controller,
    and then will pass that URL to the target over SSM, telling the target to download/upload from S3 with C(curl).
  - The controller requires IAM permissions to upload, download and delete files from the specified S3 bucket. This includes
    `s3:GetObject`, `s3:PutObject`, `s3:ListBucket`, `s3:DeleteObject` and `s3:GetBucketLocation`.

options:
  access_key_id:
    description: The STS access key to use when connecting via session-manager.
    vars:
    - name: ansible_aws_ssm_access_key_id
    env:
    - name: AWS_ACCESS_KEY_ID
    version_added: 1.3.0
  secret_access_key:
    description: The STS secret key to use when connecting via session-manager.
    vars:
    - name: ansible_aws_ssm_secret_access_key
    env:
    - name: AWS_SECRET_ACCESS_KEY
    version_added: 1.3.0
  session_token:
    description: The STS session token to use when connecting via session-manager.
    vars:
    - name: ansible_aws_ssm_session_token
    env:
    - name: AWS_SESSION_TOKEN
    version_added: 1.3.0
  instance_id:
    description: The EC2 instance ID.
    vars:
    - name: ansible_aws_ssm_instance_id
  region:
    description: The region the EC2 instance is located.
    vars:
    - name: ansible_aws_ssm_region
    env:
    - name: AWS_REGION
    - name: AWS_DEFAULT_REGION
    default: 'us-east-1'
  bucket_name:
    description: The name of the S3 bucket used for file transfers.
    vars:
    - name: ansible_aws_ssm_bucket_name
  bucket_endpoint_url:
    description: The S3 endpoint URL of the bucket used for file transfers.
    vars:
    - name: ansible_aws_ssm_bucket_endpoint_url
    version_added: 5.3.0
  plugin:
    description:
    - This defines the location of the session-manager-plugin binary.
    - Support for environment variable was added in version 9.1.0.
    - The plugin will first check the V('/usr/local/bin/session-manager-plugin') as the default path of the SSM plugin
      if this does not exist, it will find the session-manager-plugin from the PATH environment variable. Added in version 9.1.0.
    vars:
    - name: ansible_aws_ssm_plugin
    env:
    - name: AWS_SESSION_MANAGER_PLUGIN
  profile:
    description: Sets AWS profile to use.
    vars:
    - name: ansible_aws_ssm_profile
    env:
    - name: AWS_PROFILE
    version_added: 1.5.0
  reconnection_retries:
    description: Number of attempts to connect.
    default: 3
    type: integer
    vars:
    - name: ansible_aws_ssm_retries
  ssm_timeout:
    description: Connection timeout seconds.
    default: 60
    type: integer
    vars:
    - name: ansible_aws_ssm_timeout
  bucket_sse_mode:
    description: Server-side encryption mode to use for uploads on the S3 bucket used for file transfer.
    choices: [ 'AES256', 'aws:kms' ]
    required: false
    version_added: 2.2.0
    vars:
    - name: ansible_aws_ssm_bucket_sse_mode
  bucket_sse_kms_key_id:
    description: KMS key id to use when encrypting objects using C(bucket_sse_mode=aws:kms). Ignored otherwise.
    version_added: 2.2.0
    vars:
    - name: ansible_aws_ssm_bucket_sse_kms_key_id
  ssm_document:
    description:
    - SSM Session document to use when connecting.
    - To configure the remote_user (when C(become=False), it is possible to use an SSM Session
      document and define the C(runAsEnabled) and C(runAsDefaultUser) parameters.  See also
      U(https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-schema.html)
    vars:
    - name: ansible_aws_ssm_document
    version_added: 5.2.0
  s3_addressing_style:
    description:
    - The addressing style to use when using S3 URLs.
    - When the S3 bucket isn't in the same region as the Instance
      explicitly setting the addressing style to 'virtual' may be necessary
      U(https://repost.aws/knowledge-center/s3-http-307-response) as this forces
      the use of a specific endpoint.
    choices: [ 'path', 'virtual', 'auto' ]
    default: 'auto'
    version_added: 5.2.0
    vars:
    - name: ansible_aws_ssm_s3_addressing_style
"""

EXAMPLES = r"""
---
# Wait for SSM Agent to be available on the Instance
- name: Wait for connection to be available
  vars:
    ansible_connection: aws_ssm
    ansible_aws_ssm_bucket_name: nameofthebucket
    ansible_aws_ssm_region: us-west-2
    # When the S3 bucket isn't in the same region as the Instance
    # Explicitly setting the addressing style to 'virtual' may be necessary
    # https://repost.aws/knowledge-center/s3-http-307-response
    ansible_aws_ssm_s3_addressing_style: virtual
  tasks:
    - name: Wait for connection
      wait_for_connection:

# Stop Spooler Process on Windows Instances
- name: Stop Spooler Service on Windows Instances
  vars:
    ansible_connection: aws_ssm
    ansible_shell_type: powershell
    ansible_aws_ssm_bucket_name: nameofthebucket
    ansible_aws_ssm_region: us-east-1
  tasks:
    - name: Stop spooler service
      win_service:
        name: spooler
        state: stopped

# Install a Nginx Package on Linux Instance
- name: Install a Nginx Package
  vars:
    ansible_connection: aws_ssm
    ansible_aws_ssm_bucket_name: nameofthebucket
    ansible_aws_ssm_region: us-west-2
  tasks:
    - name: Install a Nginx Package
      yum:
        name: nginx
        state: present

# Create a directory in Windows Instances
- name: Create a directory in Windows Instance
  vars:
    ansible_connection: aws_ssm
    ansible_shell_type: powershell
    ansible_aws_ssm_bucket_name: nameofthebucket
    ansible_aws_ssm_region: us-east-1
  tasks:
    - name: Create a Directory
      win_file:
        path: C:\Windows\temp
        state: directory

---

# Making use of Dynamic Inventory Plugin
# =======================================
# # aws_ec2.yml (Dynamic Inventory - Linux)
# plugin: aws_ec2
# regions:
#   - us-east-1
# hostnames:
#   - instance-id
# # This will return the Instances with the tag "SSMTag" set to "ssmlinux"
# filters:
#   tag:SSMTag: ssmlinux
# -----------------------
- name: install aws-cli
  hosts: all
  gather_facts: false
  vars:
    ansible_connection: aws_ssm
    ansible_aws_ssm_bucket_name: nameofthebucket
    ansible_aws_ssm_region: us-east-1
  tasks:
    - name: aws-cli
      raw: yum install -y awscli
      tags: aws-cli

---

# Execution: ansible-playbook linux.yaml -i aws_ec2.yml
# =====================================================
# # aws_ec2.yml (Dynamic Inventory - Windows)
# plugin: aws_ec2
# regions:
#   - us-east-1
# hostnames:
#   - instance-id
# # This will return the Instances with the tag "SSMTag" set to "ssmwindows"
# filters:
#   tag:SSMTag: ssmwindows
# -----------------------
- name: Create a dir.
  hosts: all
  gather_facts: false
  vars:
    ansible_connection: aws_ssm
    ansible_shell_type: powershell
    ansible_aws_ssm_bucket_name: nameofthebucket
    ansible_aws_ssm_region: us-east-1
  tasks:
    - name: Create the directory
      win_file:
        path: C:\Temp\SSM_Testing5
        state: directory

---

# Execution:  ansible-playbook win_file.yaml -i aws_ec2.yml
# The playbook tasks will get executed on the instance ids returned from the dynamic inventory plugin using ssm connection.

# Install a Nginx Package on Linux Instance; with specific SSE CMK used for the file transfer
- name: Install a Nginx Package
  vars:
    ansible_connection: aws_ssm
    ansible_aws_ssm_bucket_name: nameofthebucket
    ansible_aws_ssm_region: us-west-2
    ansible_aws_ssm_bucket_sse_mode: 'aws:kms'
    ansible_aws_ssm_bucket_sse_kms_key_id: alias/kms-key-alias
  tasks:
    - name: Install a Nginx Package
      yum:
        name: nginx
        state: present

# Install a Nginx Package on Linux Instance; using the specified SSM document
- name: Install a Nginx Package
  vars:
    ansible_connection: aws_ssm
    ansible_aws_ssm_bucket_name: nameofthebucket
    ansible_aws_ssm_region: us-west-2
    ansible_aws_ssm_document: nameofthecustomdocument
  tasks:
    - name: Install a Nginx Package
      yum:
        name: nginx
        state: present

---
# Execution: ansible-playbook play.yaml -i ssm_inventory.ini
# =====================================================
# ssm_inventory.ini
# [all]
# linux ansible_aws_ssm_instance_id=i-01234567829abcdef ansible_aws_ssm_region=us-east-1

# [all:vars]
# ansible_connection=community.aws.aws_ssm
# ansible_python_interpreter=/usr/bin/python3
# local_tmp=/tmp/ansible-local-ssm-0123456
# ansible_aws_ssm_bucket_name=my-test-bucket
# ansible_aws_ssm_s3_addressing_style=virtual
# -----------------------
# Transfer file and run script on remote host
- name: Transfer file and Run script into SSM manage node
  hosts: all
  gather_facts: false

  tasks:
    - name: Create shell script
      ansible.builtin.copy:
        mode: '0755'
        dest: '/tmp/date.sh'
        content: |
          #!/usr/bin/env bash
          date

    - name: Execute script from remote host
      ansible.builtin.shell:
        cmd: '/tmp/date.sh'
"""
import getpass
import json
import os
import pty
import random
import re
import select
import string
import subprocess
import time
from functools import wraps
from typing import Any
from typing import Dict
from typing import Iterator
from typing import List
from typing import NoReturn
from typing import Optional
from typing import Tuple
from typing import TypedDict

try:
    import boto3
    from botocore.client import Config
except ImportError:
    pass

from ansible.errors import AnsibleConnectionFailure
from ansible.errors import AnsibleError
from ansible.errors import AnsibleFileNotFound
from ansible.module_utils._text import to_bytes
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.common.process import get_bin_path
from ansible.plugins.connection import ConnectionBase
from ansible.plugins.shell.powershell import _common_args
from ansible.utils.display import Display

from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3

from ansible_collections.community.aws.plugins.plugin_utils.s3clientmanager import S3ClientManager

display = Display()


def _ssm_retry(func: Any) -> Any:
    """
    Decorator to retry in the case of a connection failure
    Will retry if:
    * an exception is caught
    Will not retry if
    * remaining_tries is <2
    * retries limit reached
    """

    @wraps(func)
    def wrapped(self, *args: Any, **kwargs: Any) -> Any:
        remaining_tries = int(self.get_option("reconnection_retries")) + 1
        cmd_summary = f"{args[0]}..."
        for attempt in range(remaining_tries):
            try:
                return_tuple = func(self, *args, **kwargs)
                self.verbosity_display(4, f"ssm_retry: (success) {to_text(return_tuple)}")
                break

            except (AnsibleConnectionFailure, Exception) as e:
                if attempt == remaining_tries - 1:
                    raise
                pause = 2**attempt - 1
                pause = min(pause, 30)

                if isinstance(e, AnsibleConnectionFailure):
                    msg = f"ssm_retry: attempt: {attempt}, cmd ({cmd_summary}), pausing for {pause} seconds"
                else:
                    msg = (
                        f"ssm_retry: attempt: {attempt}, caught exception({e})"
                        f"from cmd ({cmd_summary}),pausing for {pause} seconds"
                    )

                self.verbosity_display(2, msg)

                time.sleep(pause)

                # Do not attempt to reuse the existing session on retries
                # This will cause the SSM session to be completely restarted,
                # as well as reinitializing the boto3 clients
                self.close()

                continue

        return return_tuple

    return wrapped


def chunks(lst: List, n: int) -> Iterator[List[Any]]:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]  # fmt: skip


def filter_ansi(line: str, is_windows: bool) -> str:
    """Remove any ANSI terminal control codes.

    :param line: The input line.
    :param is_windows: Whether the output is coming from a Windows host.
    :returns: The result line.
    """
    line = to_text(line)

    if is_windows:
        osc_filter = re.compile(r"\x1b\][^\x07]*\x07")
        line = osc_filter.sub("", line)
        ansi_filter = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]")
        line = ansi_filter.sub("", line)

        # Replace or strip sequence (at terminal width)
        line = line.replace("\r\r\n", "\n")
        if len(line) == 201:
            line = line[:-1]

    return line


class CommandResult(TypedDict):
    """
    A dictionary that contains the executed command results.
    """

    returncode: int
    stdout_combined: str
    stderr_combined: str


class Connection(ConnectionBase):
    """AWS SSM based connections"""

    transport = "community.aws.aws_ssm"
    default_user = ""

    allow_executable = False
    allow_extras = True
    has_pipelining = False
    is_windows = False

    _client = None
    _s3_client = None
    _session = None
    _stdout = None
    _session_id = ""
    _timeout = False
    MARK_LENGTH = 26

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        if not HAS_BOTO3:
            raise AnsibleError(missing_required_lib("boto3"))

        self.host = self._play_context.remote_addr
        self._instance_id = None
        self._polling_obj = None
        self._has_timeout = False

        if getattr(self._shell, "SHELL_FAMILY", "") == "powershell":
            self.delegate = None
            self.has_native_async = True
            self.always_pipeline_modules = True
            self.module_implementation_preferences = (".ps1", ".exe", "")
            self.protocol = None
            self.shell_id = None
            self._shell_type = "powershell"
            self.is_windows = True

    def __del__(self) -> None:
        self.close()

    def _connect(self) -> Any:
        """connect to the host via ssm"""
        self._play_context.remote_user = getpass.getuser()

        if not self._session_id:
            self.start_session()
        return self

    def _init_clients(self) -> None:
        """
        Initializes required AWS clients (SSM and S3).
        Delegates client initialization to specialized methods.
        """

        self.verbosity_display(4, "INITIALIZE BOTO3 CLIENTS")
        profile_name = self.get_option("profile") or ""
        region_name = self.get_option("region")

        # Initialize S3ClientManager
        self.s3_manager = S3ClientManager(self)

        # Initialize S3 client
        s3_endpoint_url, s3_region_name = self.s3_manager.get_bucket_endpoint()
        self.verbosity_display(4, f"SETUP BOTO3 CLIENTS: S3 {s3_endpoint_url}")
        self.s3_manager.initialize_client(
            region_name=s3_region_name, endpoint_url=s3_endpoint_url, profile_name=profile_name
        )
        self._s3_client = self.s3_manager._s3_client

        # Initialize SSM client
        self._initialize_ssm_client(region_name, profile_name)

    def _initialize_ssm_client(self, region_name: Optional[str], profile_name: str) -> None:
        """
        Initializes the SSM client used to manage sessions.
        Args:
            region_name (Optional[str]): AWS region for the SSM client.
            profile_name (str): AWS profile name for authentication.

        Returns:
            None
        """

        self.verbosity_display(4, "SETUP BOTO3 CLIENTS: SSM")
        self._client = self._get_boto_client(
            "ssm",
            region_name=region_name,
            profile_name=profile_name,
        )

    def verbosity_display(self, level: int, message: str) -> None:
        """
        Displays the given message depending on the verbosity level.

        :param message: The message to display.
        :param display_level: The verbosity level (1-4).

        :return: None
        """
        if self.host:
            host_args = {"host": self.host}
        else:
            host_args = {}

        verbosity_level = {1: display.v, 2: display.vv, 3: display.vvv, 4: display.vvvv}

        if level not in verbosity_level.keys():
            raise AnsibleError(f"Invalid verbosity level: {level}")
        verbosity_level[level](to_text(message), **host_args)

    def reset(self) -> Any:
        """start a fresh ssm session"""
        self.verbosity_display(4, "reset called on ssm connection")
        self.close()
        return self.start_session()

    @property
    def instance_id(self) -> str:
        if not self._instance_id:
            self._instance_id = self.host if self.get_option("instance_id") is None else self.get_option("instance_id")
        return self._instance_id

    @instance_id.setter
    def instance_id(self, instance_id: str) -> None:
        self._instance_id = instance_id

    def get_executable(self) -> str:
        ssm_plugin_executable = self.get_option("plugin")
        if ssm_plugin_executable:
            # User has provided a path to the ssm plugin, ensure this is a valid path
            if not os.path.exists(to_bytes(ssm_plugin_executable, errors="surrogate_or_strict")):
                raise AnsibleError(f"failed to find the executable specified {ssm_plugin_executable}.")
        else:
            ssm_plugin_executable = "/usr/local/bin/session-manager-plugin"
            if not os.path.exists(to_bytes(ssm_plugin_executable, errors="surrogate_or_strict")):
                # find executable from path 'session-manager-plugin'
                try:
                    ssm_plugin_executable = get_bin_path("session-manager-plugin")
                except ValueError as e:
                    raise AnsibleError(str(e))
        return ssm_plugin_executable

    def start_session(self):
        """start ssm session"""

        self.verbosity_display(3, f"ESTABLISH SSM CONNECTION TO: {self.instance_id}")

        executable = self.get_executable()

        self._init_clients()

        self.verbosity_display(4, f"START SSM SESSION: {self.instance_id}")
        start_session_args = dict(Target=self.instance_id, Parameters={})
        document_name = self.get_option("ssm_document")
        if document_name is not None:
            start_session_args["DocumentName"] = document_name
        response = self._client.start_session(**start_session_args)
        self._session_id = response["SessionId"]

        region_name = self.get_option("region")
        profile_name = self.get_option("profile") or ""
        cmd = [
            executable,
            json.dumps(response),
            region_name,
            "StartSession",
            profile_name,
            json.dumps({"Target": self.instance_id}),
            self._client.meta.endpoint_url,
        ]

        self.verbosity_display(4, f"SSM COMMAND: {to_text(cmd)}")

        stdout_r, stdout_w = pty.openpty()
        self._session = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=stdout_w,
            stderr=subprocess.PIPE,
            close_fds=True,
            bufsize=0,
        )

        os.close(stdout_w)
        self._stdout = os.fdopen(stdout_r, "rb", 0)

        # For non-windows Hosts: Ensure the session has started, and disable command echo and prompt.
        self._prepare_terminal()

        self.verbosity_display(4, f"SSM CONNECTION ID: {self._session_id}")  # pylint: disable=unreachable

        return self._session

    def poll_stdout(self, timeout: int = 1000) -> bool:
        """Polls the stdout file descriptor.

        :param timeout: Specifies the length of time in milliseconds which the system will wait.
        :returns: A boolean to specify the polling result
        """
        if self._polling_obj is None:
            self._polling_obj = select.poll()
            self._polling_obj.register(self._stdout, select.POLLIN)
        return bool(self._polling_obj.poll(timeout))

    def poll(self, label: str, cmd: str) -> NoReturn:
        """Poll session to retrieve content from stdout.

        :param label: A label for the display (EXEC, PRE...)
        :param cmd: The command being executed
        """
        start = round(time.time())
        yield self.poll_stdout()
        timeout = self.get_option("ssm_timeout")
        while self._session.poll() is None:
            remaining = start + timeout - round(time.time())
            self.verbosity_display(4, f"{label} remaining: {remaining} second(s)")
            if remaining < 0:
                self._has_timeout = True
                raise AnsibleConnectionFailure(f"{label} command '{cmd}' timeout on host: {self.instance_id}")
            yield self.poll_stdout()

    def exec_communicate(self, cmd: str, mark_start: str, mark_begin: str, mark_end: str) -> Tuple[int, str, str]:
        """Interact with session.
        Read stdout between the markers until 'mark_end' is reached.

        :param cmd: The command being executed.
        :param mark_start: The marker which starts the output.
        :param mark_begin: The begin marker.
        :param mark_end: The end marker.
        :returns: A tuple with the return code, the stdout and the stderr content.
        """
        # Read stdout between the markers
        stdout = ""
        win_line = ""
        begin = False
        returncode = None
        for poll_result in self.poll("EXEC", cmd):
            if not poll_result:
                continue

            line = filter_ansi(self._stdout.readline(), self.is_windows)
            self.verbosity_display(4, f"EXEC stdout line: \n{line}")

            if not begin and self.is_windows:
                win_line = win_line + line
                line = win_line

            if mark_start in line:
                begin = True
                if not line.startswith(mark_start):
                    stdout = ""
                continue
            if begin:
                if mark_end in line:
                    self.verbosity_display(4, f"POST_PROCESS: \n{to_text(stdout)}")
                    returncode, stdout = self._post_process(stdout, mark_begin)
                    self.verbosity_display(4, f"POST_PROCESSED: \n{to_text(stdout)}")
                    break
                stdout = stdout + line

        # see https://github.com/pylint-dev/pylint/issues/8909)
        return (returncode, stdout, self._flush_stderr(self._session))  # pylint: disable=unreachable

    @staticmethod
    def generate_mark() -> str:
        """Generates a random string of characters to delimit SSM CLI commands"""
        mark = "".join([random.choice(string.ascii_letters) for i in range(Connection.MARK_LENGTH)])
        return mark

    @_ssm_retry
    def exec_command(self, cmd: str, in_data: bool = None, sudoable: bool = True) -> Tuple[int, str, str]:
        """When running a command on the SSM host, uses generate_mark to get delimiting strings"""

        super().exec_command(cmd, in_data=in_data, sudoable=sudoable)

        self.verbosity_display(3, f"EXEC: {to_text(cmd)}")

        mark_begin = self.generate_mark()
        if self.is_windows:
            mark_start = mark_begin + " $LASTEXITCODE"
        else:
            mark_start = mark_begin
        mark_end = self.generate_mark()

        # Wrap command in markers accordingly for the shell used
        cmd = self._wrap_command(cmd, mark_start, mark_end)

        self._flush_stderr(self._session)

        for chunk in chunks(cmd, 1024):
            self._session.stdin.write(to_bytes(chunk, errors="surrogate_or_strict"))

        return self.exec_communicate(cmd, mark_start, mark_begin, mark_end)

    def _ensure_ssm_session_has_started(self) -> None:
        """Ensure the SSM session has started on the host. We poll stdout
        until we match the following string 'Starting session with SessionId'
        """
        stdout = ""
        for poll_result in self.poll("START SSM SESSION", "start_session"):
            if poll_result:
                stdout += to_text(self._stdout.read(1024))
                self.verbosity_display(4, f"START SSM SESSION stdout line: \n{to_bytes(stdout)}")
                match = str(stdout).find("Starting session with SessionId")
                if match != -1:
                    self.verbosity_display(4, "START SSM SESSION startup output received")
                    break

    def _disable_prompt_command(self) -> None:
        """Disable prompt command from the host"""
        end_mark = "".join([random.choice(string.ascii_letters) for i in range(self.MARK_LENGTH)])
        disable_prompt_cmd = to_bytes(
            "PS1='' ; bind 'set enable-bracketed-paste off'; printf '\\n%s\\n' '" + end_mark + "'\n",
            errors="surrogate_or_strict",
        )
        disable_prompt_reply = re.compile(r"\r\r\n" + re.escape(end_mark) + r"\r\r\n", re.MULTILINE)

        # Send command
        self.verbosity_display(4, f"DISABLE PROMPT Disabling Prompt: \n{disable_prompt_cmd}")
        self._session.stdin.write(disable_prompt_cmd)

        stdout = ""
        for poll_result in self.poll("DISABLE PROMPT", disable_prompt_cmd):
            if poll_result:
                stdout += to_text(self._stdout.read(1024))
                self.verbosity_display(4, f"DISABLE PROMPT stdout line: \n{to_bytes(stdout)}")
                if disable_prompt_reply.search(stdout):
                    break

    def _disable_echo_command(self) -> None:
        """Disable echo command from the host"""
        disable_echo_cmd = to_bytes("stty -echo\n", errors="surrogate_or_strict")

        # Send command
        self.verbosity_display(4, f"DISABLE ECHO Disabling Prompt: \n{disable_echo_cmd}")
        self._session.stdin.write(disable_echo_cmd)

        stdout = ""
        for poll_result in self.poll("DISABLE ECHO", disable_echo_cmd):
            if poll_result:
                stdout += to_text(self._stdout.read(1024))
                self.verbosity_display(4, f"DISABLE ECHO stdout line: \n{to_bytes(stdout)}")
                match = str(stdout).find("stty -echo")
                if match != -1:
                    break

    def _prepare_terminal(self) -> None:
        """perform any one-time terminal settings"""
        # No Windows setup for now
        if self.is_windows:
            return

        # Ensure SSM Session has started
        self._ensure_ssm_session_has_started()

        # Disable echo command
        self._disable_echo_command()  # pylint: disable=unreachable

        # Disable prompt command
        self._disable_prompt_command()  # pylint: disable=unreachable

        self.verbosity_display(4, "PRE Terminal configured")  # pylint: disable=unreachable

    def _wrap_command(self, cmd: str, mark_start: str, mark_end: str) -> str:
        """Wrap command so stdout and status can be extracted"""

        if self.is_windows:
            if not cmd.startswith(" ".join(_common_args) + " -EncodedCommand"):
                cmd = self._shell._encode_script(cmd, preserve_rc=True)
            cmd = cmd + "; echo " + mark_start + "\necho " + mark_end + "\n"
        else:
            cmd = (
                f"printf '%s\\n' '{mark_start}';\n"
                f"echo | {cmd};\n"
                f"printf '\\n%s\\n%s\\n' \"$?\" '{mark_end}';\n"
            )  # fmt: skip

        self.verbosity_display(4, f"_wrap_command: \n'{to_text(cmd)}'")
        return cmd

    def _post_process(self, stdout: str, mark_begin: str) -> Tuple[str, str]:
        """extract command status and strip unwanted lines"""

        if not self.is_windows:
            # Get command return code
            returncode = int(stdout.splitlines()[-2])

            # Throw away final lines
            for _x in range(0, 3):
                stdout = stdout[:stdout.rfind('\n')]  # fmt: skip

            return (returncode, stdout)

        # Windows is a little more complex
        # Value of $LASTEXITCODE will be the line after the mark
        trailer = stdout[stdout.rfind(mark_begin):]  # fmt: skip
        last_exit_code = trailer.splitlines()[1]
        if last_exit_code.isdigit:
            returncode = int(last_exit_code)
        else:
            returncode = -1
        # output to keep will be before the mark
        stdout = stdout[:stdout.rfind(mark_begin)]  # fmt: skip

        # If the return code contains #CLIXML (like a progress bar) remove it
        clixml_filter = re.compile(r"#<\sCLIXML\s<Objs.*</Objs>")
        stdout = clixml_filter.sub("", stdout)

        # If it looks like JSON remove any newlines
        if stdout.startswith("{"):
            stdout = stdout.replace("\n", "")

        return (returncode, stdout)

    def _flush_stderr(self, session_process) -> str:
        """read and return stderr with minimal blocking"""

        poll_stderr = select.poll()
        poll_stderr.register(session_process.stderr, select.POLLIN)
        stderr = ""

        while session_process.poll() is None:
            if not poll_stderr.poll(1):
                break
            line = session_process.stderr.readline()
            self.verbosity_display(4, f"stderr line: {to_text(line)}")
            stderr = stderr + line

        return stderr

    def _get_boto_client(self, service, region_name=None, profile_name=None, endpoint_url=None):
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
        if profile_name:
            session_args["profile_name"] = profile_name
        session = boto3.session.Session(**session_args)

        client = session.client(
            service,
            endpoint_url=endpoint_url,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": self.get_option("s3_addressing_style")},
            ),
        )
        return client

    def _escape_path(self, path: str) -> str:
        return path.replace("\\", "/")

    def _generate_commands(
        self,
        bucket_name: str,
        s3_path: str,
        in_path: str,
        out_path: str,
    ) -> Tuple[List[Dict], dict]:
        """
        Generate commands for the specified bucket, S3 path, input path, and output path.

        :param bucket_name: The name of the S3 bucket used for file transfers.
        :param s3_path: The S3 path to the file to be sent.
        :param in_path: Input path
        :param out_path: Output path
        :param method: The request method to use for the command (can be "get" or "put").

        :returns: A tuple containing a list of command dictionaries along with any ``put_args`` dictionaries.
        """

        put_args, put_headers = self.s3_manager.generate_encryption_settings()
        commands = []

        put_url = self.s3_manager.get_url("put_object", bucket_name, s3_path, "PUT", extra_args=put_args)
        get_url = self.s3_manager.get_url("get_object", bucket_name, s3_path, "GET")

        if self.is_windows:
            put_command_headers = "; ".join([f"'{h}' = '{v}'" for h, v in put_headers.items()])
            commands.append({
                "command":
                (
                    "Invoke-WebRequest "
                    f"'{get_url}' "
                    f"-OutFile '{out_path}'"
                ),
                # The "method" key indicates to _file_transport_command which commands are get_commands
                "method": "get",
                "headers": {},
            })  # fmt: skip
            commands.append({
                "command":
                (
                    "Invoke-WebRequest -Method PUT "
                    # @{'key' = 'value'; 'key2' = 'value2'}
                    f"-Headers @{{{put_command_headers}}} "
                    f"-InFile '{in_path}' "
                    f"-Uri '{put_url}' "
                    f"-UseBasicParsing"
                ),
                # The "method" key indicates to _file_transport_command which commands are put_commands
                "method": "put",
                "headers": put_headers,
            })  # fmt: skip
        else:
            put_command_headers = " ".join([f"-H '{h}: {v}'" for h, v in put_headers.items()])
            commands.append({
                "command":
                (
                    "curl "
                    f"-o '{out_path}' "
                    f"'{get_url}'"
                ),
                # The "method" key indicates to _file_transport_command which commands are get_commands
                "method": "get",
                "headers": {},
            })  # fmt: skip
            # Due to https://github.com/curl/curl/issues/183 earlier
            # versions of curl did not create the output file, when the
            # response was empty. Although this issue was fixed in 2015,
            # some actively maintained operating systems still use older
            # versions of it (e.g. CentOS 7)
            commands.append({
                "command":
                (
                    "touch "
                    f"'{out_path}'"
                ),
                "method": "get",
                "headers": {},
            })  # fmt: skip
            commands.append({
                "command":
                (
                    "curl --request PUT "
                    f"{put_command_headers} "
                    f"--upload-file '{in_path}' "
                    f"'{put_url}'"
                ),
                # The "method" key indicates to _file_transport_command which commands are put_commands
                "method": "put",
                "headers": put_headers,
            })  # fmt: skip

        return commands, put_args

    def _exec_transport_commands(self, in_path: str, out_path: str, commands: List[dict]) -> CommandResult:
        """
        Execute the provided transport commands.

        :param in_path: The input path.
        :param out_path: The output path.
        :param commands: A list of command dictionaries containing the command string and metadata.

        :returns: A tuple containing the return code, stdout, and stderr.
        """

        stdout_combined, stderr_combined = "", ""
        for command in commands:
            (returncode, stdout, stderr) = self.exec_command(command["command"], in_data=None, sudoable=False)

            # Check the return code
            if returncode != 0:
                raise AnsibleError(f"failed to transfer file to {in_path} {out_path}:\n{stdout}\n{stderr}")

            stdout_combined += stdout
            stderr_combined += stderr

        return (returncode, stdout_combined, stderr_combined)

    @_ssm_retry
    def _file_transport_command(
        self,
        in_path: str,
        out_path: str,
        ssm_action: str,
    ) -> CommandResult:
        """
        Transfer file(s) to/from host using an intermediate S3 bucket and then delete the file(s).

        :param in_path: The input path.
        :param out_path: The output path.
        :param ssm_action: The SSM action to perform ("get" or "put").

        :returns: The command's return code, stdout, and stderr in a tuple.
        """

        bucket_name = self.get_option("bucket_name")
        s3_path = self._escape_path(f"{self.instance_id}/{out_path}")

        client = self._s3_client

        commands, put_args = self._generate_commands(
            bucket_name,
            s3_path,
            in_path,
            out_path,
        )

        try:
            if ssm_action == "get":
                put_commands = [cmd for cmd in commands if cmd.get("method") == "put"]
                result = self._exec_transport_commands(in_path, out_path, put_commands)
                with open(to_bytes(out_path, errors="surrogate_or_strict"), "wb") as data:
                    client.download_fileobj(bucket_name, s3_path, data)
            else:
                get_commands = [cmd for cmd in commands if cmd.get("method") == "get"]
                with open(to_bytes(in_path, errors="surrogate_or_strict"), "rb") as data:
                    client.upload_fileobj(data, bucket_name, s3_path, ExtraArgs=put_args)
                result = self._exec_transport_commands(in_path, out_path, get_commands)
            return result
        finally:
            # Remove the files from the bucket after they've been transferred
            client.delete_object(Bucket=bucket_name, Key=s3_path)

    def put_file(self, in_path: str, out_path: str) -> Tuple[int, str, str]:
        """transfer a file from local to remote"""

        super().put_file(in_path, out_path)

        self.verbosity_display(3, f"PUT {in_path} TO {out_path}")
        if not os.path.exists(to_bytes(in_path, errors="surrogate_or_strict")):
            raise AnsibleFileNotFound(f"file or module does not exist: {in_path}")

        return self._file_transport_command(in_path, out_path, "put")

    def fetch_file(self, in_path: str, out_path: str) -> Tuple[int, str, str]:
        """fetch a file from remote to local"""

        super().fetch_file(in_path, out_path)

        self.verbosity_display(3, f"FETCH {in_path} TO {out_path}")
        return self._file_transport_command(in_path, out_path, "get")

    def close(self) -> None:
        """terminate the connection"""
        if self._session_id:
            self.verbosity_display(3, f"CLOSING SSM CONNECTION TO: {self.instance_id}")
            if self._has_timeout:
                self._session.terminate()
            else:
                cmd = b"\nexit\n"
                self._session.communicate(cmd)

            self.verbosity_display(4, f"TERMINATE SSM SESSION: {self._session_id}")
            self._client.terminate_session(SessionId=self._session_id)
            self._session_id = ""
