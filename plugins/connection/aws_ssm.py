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
import os
import random
import re
import string
from typing import Any, Dict
from typing import Iterator
from typing import List
from typing import Tuple

from ansible.errors import AnsibleError
from ansible.errors import AnsibleFileNotFound
from ansible.module_utils._text import to_bytes
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.common.process import get_bin_path
from ansible.plugins.connection import ConnectionBase
from ansible.utils.display import Display

from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3
from ansible_collections.community.aws.plugins.plugin_utils.ssm.base import AwsConnectionPluginBase
from ansible_collections.community.aws.plugins.plugin_utils.ssm.s3clientmanager import S3ClientManager
from ansible_collections.community.aws.plugins.plugin_utils.ssm.terminalmanager import TerminalManager
from ansible_collections.community.aws.plugins.plugin_utils.ssm.sessionmanager import (
    SSMSessionManager,
)

from ansible_collections.community.aws.plugins.plugin_utils.ssm.filetransfermanager import FileTransferManager
from ansible_collections.community.aws.plugins.plugin_utils.ssm.common import ssm_retry
from ansible_collections.community.aws.plugins.plugin_utils.ssm.common import CommandResult


display = Display()


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


def escape_path(path: str) -> str:
    """
    Converts a file path to a safe format by replacing backslashes with forward slashes.
    :param path: The file path to escape.
    :return: The escaped file path.
    """
    return path.replace("\\", "/")


class Connection(ConnectionBase, AwsConnectionPluginBase):
    """AWS SSM based connections"""

    transport = "community.aws.aws_ssm"
    default_user = ""

    allow_executable = False
    allow_extras = True
    has_pipelining = False
    is_windows = False

    _client = None
    _s3_manager = None
    _session_manager = None
    MARK_LENGTH = 26

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        if not HAS_BOTO3:
            raise AnsibleError(missing_required_lib("boto3"))

        self.host = self._play_context.remote_addr
        self._instance_id = None
        self.terminal_manager = TerminalManager(self)
        self.reconnection_retries = self.get_option("reconnection_retries")

        if getattr(self._shell, "SHELL_FAMILY", "") == "powershell":
            self.delegate = None
            self.has_native_async = True
            self.always_pipeline_modules = True
            self.module_implementation_preferences = (".ps1", ".exe", "")
            self.protocol = None
            self.shell_id = None
            self._shell_type = "powershell"
            self.is_windows = True

    @property
    def s3_client(self) -> None:
        if self._s3_manager is not None:
            return self._s3_manager.client
        return None

    @property
    def s3_manager(self) -> None:
        if self._s3_manager is None:
            config = {"signature_version": "s3v4", "s3": {"addressing_style": self.get_option("s3_addressing_style")}}

            bucket_endpoint_url = self.get_option("bucket_endpoint_url")
            s3_endpoint_url, s3_region_name = S3ClientManager.get_bucket_endpoint(
                bucket_name=self.get_option("bucket_name"),
                bucket_endpoint_url=bucket_endpoint_url,
                access_key_id=self.get_option("access_key_id"),
                secret_key_id=self.get_option("secret_access_key"),
                session_token=self.get_option("session_token"),
                region_name=self.get_option("region"),
                profile_name=self.get_option("profile"),
            )

            s3_client = self._get_boto_client(
                "s3", endpoint_url=s3_endpoint_url, region_name=s3_region_name, config=config
            )

            self._s3_manager = S3ClientManager(s3_client)

        return self._s3_manager

    @property
    def session_manager(self):
        return self._session_manager

    @session_manager.setter
    def session_manager(self, value):
        self._session_manager = value

    @property
    def ssm_client(self):
        if self._client is None:
            config = {"signature_version": "s3v4", "s3": {"addressing_style": self.get_option("s3_addressing_style")}}

            self._client = self._get_boto_client("ssm", region_name=self.get_option("region"), config=config)
        return self._client

    @property
    def instance_id(self) -> str:
        if not self._instance_id:
            self._instance_id = self.host if self.get_option("instance_id") is None else self.get_option("instance_id")
        return self._instance_id

    @instance_id.setter
    def instance_id(self, instance_id: str) -> None:
        self._instance_id = instance_id

    def __del__(self) -> None:
        self.close()

    def _connect(self) -> Any:
        """connect to the host via ssm"""
        self._play_context.remote_user = getpass.getuser()
        if not self.session_manager:
            self.start_session()

        return self

    def _init_clients(self) -> None:
        """
        Initializes required AWS clients (SSM and S3).
        Delegates client initialization to specialized methods.
        """

        self.verbosity_display(4, "INITIALIZE BOTO3 CLIENTS")

        # Initialize S3 client
        self.s3_manager

        # Initialize SSM client
        self.ssm_client

        # Initialize FileTransferManager
        self.file_transfer_manager = FileTransferManager(
            bucket_name=self.get_option("bucket_name"),
            instance_id=self.instance_id,
            s3_client=self.s3_client,
            reconnection_retries=self.reconnection_retries,
            verbosity_display=self.verbosity_display,
            close=self.close,
            exec_command=self.exec_command,
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

    def reset(self) -> None:
        """start a fresh ssm session"""
        self.verbosity_display(4, "reset called on ssm connection")
        self.close()
        self.start_session()

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

    def start_session(self) -> None:
        """start ssm session"""

        self.verbosity_display(3, f"ESTABLISH SSM CONNECTION TO: {self.instance_id}")

        executable = self.get_executable()

        self._init_clients()

        if self.session_manager is None:
            self.session_manager = SSMSessionManager(
                self.ssm_client,
                self.instance_id,
                verbosity_display=self.verbosity_display,
                ssm_timeout=self.get_option("ssm_timeout"),
            )

            self.session_manager.start_session(
                executable=executable,
                document_name=self.get_option("ssm_document"),
                region_name=self.get_option("region"),
                profile_name=self.get_option("profile") or "",
            )

            # For non-windows Hosts: Ensure the session has started, and disable command echo and prompt.
            self.terminal_manager.prepare_terminal()

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
        for poll_result in self.session_manager.poll("EXEC", cmd):
            if not poll_result:
                continue

            line = filter_ansi(self.session_manager.stdout_readline(), self.is_windows)
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
        return (returncode, stdout, self.session_manager.flush_stderr())

    @staticmethod
    def generate_mark() -> str:
        """Generates a random string of characters to delimit SSM CLI commands"""
        mark = "".join([random.choice(string.ascii_letters) for i in range(Connection.MARK_LENGTH)])
        return mark

    @ssm_retry
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
        cmd = self.terminal_manager.wrap_command(cmd, mark_start, mark_end)

        self.session_manager.flush_stderr()

        for chunk in chunks(cmd, 1024):
            self.session_manager.stdin_write(to_bytes(chunk, errors="surrogate_or_strict"))

        return self.exec_communicate(cmd, mark_start, mark_begin, mark_end)

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

    def generate_commands(self, in_path: str, out_path: str, ssm_action: str) -> Tuple[str, str, Dict]:
        """
        Generate S3 path and associated transport commands for file transfer.
        :param in_path: The local file path to transfer from.
        :param out_path: The remote file path to transfer to (used to build the S3 key).
        :param ssm_action: The SSM action to perform ("get" or "put").
        :return: A tuple containing:
            - s3_path (str): The S3 key used for the transfer.
            - commands (List[Dict]): A list of commands to be executed for the transfer.
            - put_args (Dict): Additional arguments needed for a 'put' operation.
        """
        s3_path = escape_path(f"{self.instance_id}/{out_path}")
        command = ""
        put_args = []
        command, put_args = self.s3_manager.generate_host_commands(
            self.get_option("bucket_name"),
            self.get_option("bucket_sse_mode"),
            self.get_option("bucket_sse_kms_key_id"),
            s3_path,
            in_path,
            out_path,
            self.is_windows,
            ssm_action,
        )
        return s3_path, command, put_args

    def _exec_transport_commands(self, in_path: str, out_path: str, command: dict) -> CommandResult:
        """
        Execute the provided transport command.

        :param in_path: The input path.
        :param out_path: The output path.
        :param command: A command to execute on the host.

        :returns: A tuple containing the return code, stdout, and stderr.
        """

        returncode, stdout, stderr = self.exec_command(command, in_data=None, sudoable=False)
        # Check the return code
        if returncode != 0:
            raise AnsibleError(f"failed to transfer file to {in_path} {out_path}:\n{stdout}\n{stderr}")

        return returncode, stdout, stderr

    def put_file(self, in_path: str, out_path: str) -> CommandResult:
        """transfer a file from local to remote"""

        super().put_file(in_path, out_path)

        self.verbosity_display(3, f"PUT {in_path} TO {out_path}")
        if not os.path.exists(to_bytes(in_path, errors="surrogate_or_strict")):
            raise AnsibleFileNotFound(f"file or module does not exist: {in_path}")

        s3_path, command, put_args = self.generate_commands(in_path, out_path, "put")
        return self.file_transfer_manager._file_transport_command(in_path, out_path, "put", command, put_args, s3_path)

    def fetch_file(self, in_path: str, out_path: str) -> CommandResult:
        """fetch a file from remote to local"""

        super().fetch_file(in_path, out_path)

        self.verbosity_display(3, f"FETCH {in_path} TO {out_path}")

        s3_path, command, put_args = self.generate_commands(in_path, out_path, "get")
        return self.file_transfer_manager._file_transport_command(in_path, out_path, "get", command, put_args, s3_path)

    def close(self) -> None:
        """terminate the connection"""
        if self.session_manager is not None:
            self.session_manager.terminate()
            self.session_manager = None
