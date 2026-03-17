# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Pat Sharkey <psharkey@cleo.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Based on the ssh connection plugin by Michael DeHaan


from __future__ import annotations

DOCUMENTATION = r"""
name: aws_ssm
author:
  - Pat Sharkey (@psharkey) <psharkey@cleo.com>
  - HanumanthaRao MVL (@hanumantharaomvl) <hanumanth@flux7.com>
  - Gaurav Ashtikar (@gau1991) <gaurav.ashtikar@flux7.com>

version_added: 1.0.0
version_added_collection: community.aws
short_description: connect to EC2 instances via AWS Systems Manager
description:
  - This connection plugin allows Ansible to execute tasks on an EC2 instance via an AWS SSM Session.
notes:
  - The C(amazon.aws.aws_ssm) connection plugin does not support using the ``remote_user`` and
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
  access_key:
    description: The STS access key to use when connecting via session-manager.
    aliases: ['access_key_id', 'aws_access_key_id']
    vars:
    - name: ansible_aws_ssm_access_key_id
    env:
    - name: AWS_ACCESS_KEY_ID
    - name: AWS_ACCESS_KEY
    version_added: 1.3.0
  secret_key:
    description: The STS secret key to use when connecting via session-manager.
    aliases: ['secret_access_key', 'aws_secret_access_key']
    vars:
    - name: ansible_aws_ssm_secret_access_key
    env:
    - name: AWS_SECRET_ACCESS_KEY
    - name: AWS_SECRET_KEY
    version_added: 1.3.0
  session_token:
    description: The STS session token to use when connecting via session-manager.
    aliases: ['aws_session_token']
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
  endpoint_url:
    description:
    - URL to connect to instead of the default AWS endpoints.
    - This is used for the SSM client connection.
    aliases: ['aws_endpoint_url']
    vars:
    - name: ansible_aws_ssm_endpoint_url
    env:
    - name: AWS_URL
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
    aliases: ['aws_profile']
    vars:
    - name: ansible_aws_ssm_profile
    env:
    - name: AWS_PROFILE
    - name: AWS_DEFAULT_PROFILE
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

# Alternatively, you can use a tag (eg. Name) as hostname instead of InstanceID.
# However,  "ansible_host" must still be set to the instance_id
# =======================================
# # aws_ec2.yml (Dynamic Inventory - Linux)
# plugin: aws_ec2
# regions:
#   - us-east-1
# hostnames:
#   - tag:Name # will return `tag:Name` for hostname
# compose:
#   ansible_host: instance_id # but connection will be done to InstanceID
---

# Execution: ansible-playbook windows.yaml -i aws_ec2.yml
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
# ansible_connection=amazon.aws.aws_ssm
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
import base64
import getpass
import os
import random
import re
import string
import time
import typing

if typing.TYPE_CHECKING:
    from typing import Any
    from typing import Dict
    from typing import Iterator
    from typing import List
    from typing import Optional
    from typing import Tuple

from ansible.errors import AnsibleError
from ansible.errors import AnsibleFileNotFound
from ansible.module_utils._text import to_bytes
from ansible.module_utils._text import to_text
from ansible.module_utils.common.process import get_bin_path
from ansible.utils.display import Display

from ansible_collections.amazon.aws.plugins.module_utils.s3 import get_bucket_region
from ansible_collections.amazon.aws.plugins.plugin_utils.connection import AWSConnectionBase
from ansible_collections.amazon.aws.plugins.plugin_utils.retries import AWSConnectionRetry
from ansible_collections.amazon.aws.plugins.plugin_utils.ssm.common import CommandResult
from ansible_collections.amazon.aws.plugins.plugin_utils.ssm.filetransfermanager import FileTransferManager
from ansible_collections.amazon.aws.plugins.plugin_utils.ssm.s3clientmanager import S3ClientManager
from ansible_collections.amazon.aws.plugins.plugin_utils.ssm.sessionmanager import SSMSessionManager
from ansible_collections.amazon.aws.plugins.plugin_utils.ssm.terminalmanager import TerminalManager
from ansible_collections.amazon.aws.plugins.plugin_utils.ssm.text import filter_ansi

display = Display()


def chunks(lst: list, n: int) -> Iterator[list[Any]]:
    """Yield successive n-sized chunks from lst.

    :param lst: The list to chunk.
    :param n: The size of each chunk.
    :returns: Iterator yielding list chunks of size n.
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]  # fmt: skip


def _chunked_payload(payload: bytes | string, buffer_size: int = 1024) -> Iterator[tuple[bytes, bool]]:
    """
    Yield successive buffer-sized chunks from payload with completion flag.

    :param payload: The data to chunk (bytes or string)
    :param buffer_size: Size of each chunk in bytes (default: 1024)
    :returns: Iterator yielding tuples of (chunk, is_last)
    """
    payload_bytes = to_bytes(payload)
    byte_count = len(payload_bytes)
    for i in range(0, byte_count, buffer_size):
        yield payload_bytes[i : i + buffer_size], i + buffer_size >= byte_count


def escape_path(path: str) -> str:
    """
    Converts a file path to a safe format by replacing backslashes with forward slashes.
    :param path: The file path to escape.
    :return: The escaped file path.
    """
    return path.replace("\\", "/")


class Connection(AWSConnectionBase):
    """AWS SSM based connections"""

    transport = "amazon.aws.aws_ssm"
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

    def _get_bucket_endpoint(
        self, bucket_name: str, bucket_endpoint_url: str | None, region_name: str | None
    ) -> tuple[str, str]:
        """
        Fetch the correct S3 endpoint and region for use with our bucket.

        If we don't explicitly set the endpoint then some commands will use the global
        endpoint and fail (new AWS regions and new buckets in a region other than the one we're running in).

        :param bucket_name: The name of the S3 bucket
        :param bucket_endpoint_url: Optional explicit endpoint URL
        :param region_name: The region name
        :returns: Tuple of (endpoint_url, region_name)
        """
        # Create a temporary S3 client in the specified region to determine bucket location
        tmp_s3_client = self.client("s3", region=region_name)

        # Get the bucket region using head_bucket (preferred over get_bucket_location)
        bucket_region = get_bucket_region(tmp_s3_client, bucket_name)

        if bucket_endpoint_url:
            return bucket_endpoint_url, bucket_region

        # Create another client for the region the bucket lives in, so we can get the endpoint URL
        if bucket_region != region_name:
            tmp_s3_client = self.client("s3", region=bucket_region)

        return tmp_s3_client.meta.endpoint_url, tmp_s3_client.meta.region_name

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
            s3_endpoint_url, s3_region_name = self._get_bucket_endpoint(
                bucket_name=self.get_option("bucket_name"),
                bucket_endpoint_url=bucket_endpoint_url,
                region_name=self.get_option("region"),
            )

            s3_client = self.client("s3", endpoint=s3_endpoint_url, region=s3_region_name, aws_config=config)

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
            # The S3 configuration here might be a copy and paste mistake.  For now we'll keep it.
            config = {"signature_version": "s3v4", "s3": {"addressing_style": self.get_option("s3_addressing_style")}}
            self._client = self.client("ssm", aws_config=config)
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
        try:
            self.close()
        except ReferenceError:
            # Object being garbage collected, references may already be cleaned up
            pass

    def _connect(self) -> Any:
        """connect to the host via ssm"""
        self._play_context.remote_user = getpass.getuser()
        if not self.session_manager:
            self.verbosity_display(3, "NO EXISTING SESSION, STARTING NEW ONE")
            self.start_session()
        else:
            self.verbosity_display(3, f"REUSING EXISTING SESSION: {self.session_manager._session_id}")

        self._connected = True
        return self

    def _init_clients(self) -> None:
        """
        Initializes required AWS clients (SSM and S3).
        Delegates client initialization to specialized methods.
        """

        self.verbosity_display(3, "INITIALIZE BOTO3 CLIENTS")

        # Initialize S3 client
        self.s3_manager  # pylint: disable=pointless-statement

        # Initialize SSM client
        self.ssm_client  # pylint: disable=pointless-statement

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

    def reset(self) -> None:
        """start a fresh ssm session"""
        self.verbosity_display(3, "reset called on ssm connection")
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

        self.verbosity_display(2, f"ESTABLISH SSM CONNECTION TO: {self.instance_id}")

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

            self.verbosity_display(3, f"STARTED SSM SESSION: {self.session_manager._session_id}")

            # For non-windows Hosts: Ensure the session has started, and disable command echo and prompt.
            self.terminal_manager.prepare_terminal()

    def exec_communicate(self, cmd: str, in_data: bytes | None, mark_begin: str, mark_end: str) -> tuple[int, str, str]:
        """Interact with session.
        Read stdout between the markers until 'mark_end' is reached.

        :param cmd: The command being executed.
        :param in_data: Data to send to stdin after the begin marker.
        :param mark_begin: The begin marker.
        :param mark_end: The end marker.
        :returns: A tuple with the return code, the stdout and the stderr content.
        """
        start_time = time.time()
        # Read stdout between the markers
        stdout = ""
        returncode = None
        start_search = re.compile(f"^{re.escape(mark_begin)}$", re.MULTILINE)
        end_search = re.compile(f"{re.escape(mark_end)}", re.MULTILINE)

        # Wait for our start marker to come in
        self.verbosity_display(4, f"EXEC_COMMUNICATE: Waiting for begin marker ({mark_begin})")
        marker_wait_start = time.time()

        self.session_manager.wait_for_match(
            label="EXEC_COMMUNICATE",
            cmd="<BEGIN_MARKER>",
            match=start_search.search,
            is_windows=self.is_windows,
        )

        marker_wait_duration = time.time() - marker_wait_start
        self.verbosity_display(3, f"EXEC_COMMUNICATE: Begin marker received after {marker_wait_duration:.2f}s")

        # The command's been sent, and the begin marker has happened, send the stdin data
        if in_data:
            stdin_size = len(in_data)
            self.verbosity_display(4, f"EXEC_COMMUNICATE: Sending {stdin_size} bytes of STDIN data")
            stdin_start = time.time()
            chunk_count = 0
            for chunk, is_last in _chunked_payload(in_data):
                chunk_count += 1
                self.verbosity_display(
                    5, f"EXEC_COMMUNICATE: Sending STDIN chunk {chunk_count} ({len(chunk)} bytes, last={is_last})"
                )
                self.session_manager.stdin_write(to_bytes(chunk, errors="surrogate_or_strict"))

            # Send EOF delimiter for PowerShell stdin wrapper (four null bytes + newline)
            # This signals to the PowerShell script that stdin is complete
            if self.is_windows:
                stdin_duration = time.time() - stdin_start
                self.verbosity_display(
                    4,
                    f"EXEC_COMMUNICATE: Sent {chunk_count} chunks ({stdin_size} bytes) in {stdin_duration:.2f}s, sending EOF delimiter",
                )
                self.session_manager.stdin_write(b"\0\0\0\0\n")
        else:
            self.verbosity_display(4, "EXEC_COMMUNICATE: No STDIN data to send")

        self.verbosity_display(4, "EXEC_COMMUNICATE: Polling for output")
        poll_start = time.time()
        line_count = 0
        for poll_result in self.session_manager.poll("EXEC", cmd):
            if not poll_result:
                continue

            line = filter_ansi(self.session_manager.stdout_readline(), self.is_windows)
            line_count += 1
            self.verbosity_display(4, f"EXEC_COMMUNICATE: stdout line {line_count}: {repr(line)}")

            # Check for end marker before adding line to output
            if end_search.search(line):
                self.verbosity_display(4, f"EXEC_COMMUNICATE: Found end marker ({mark_end}) in line {line_count}")
                break

            stdout = stdout + line

        poll_duration = time.time() - poll_start
        self.verbosity_display(4, f"EXEC_COMMUNICATE: Polling complete after {poll_duration:.2f}s ({line_count} lines)")

        self.verbosity_display(5, f"EXEC_COMMUNICATE_POST_PROCESS: \n{to_text(stdout)}")
        returncode, stdout = self._post_process(stdout, mark_begin)
        total_duration = time.time() - start_time
        self.verbosity_display(
            4, f"EXEC_COMMUNICATE: Complete - returncode={returncode}, total_duration={total_duration:.2f}s"
        )
        self.verbosity_display(5, f"EXEC_COMMUNICATE_POST_PROCESSED: \n{to_text(stdout)}")

        # see https://github.com/pylint-dev/pylint/issues/8909)
        return (returncode, stdout, self.session_manager.flush_stderr())

    @staticmethod
    def generate_mark() -> str:
        """Generates a random string of characters to delimit SSM CLI commands"""
        mark = "".join(
            [random.choice(string.ascii_letters) for i in range(Connection.MARK_LENGTH)]
        )  # nosec B311 - markers for output parsing, not security
        return mark

    def _exec_command_via_s3(
        self, cmd: str, in_data: bytes | None, mark_begin: str, mark_end: str
    ) -> tuple[int, str, str]:
        """Execute a Windows command by uploading to S3 and downloading via tiny command.

        This avoids PTY echo timeouts by keeping the session command tiny (~100 bytes)
        while the actual command (which may be kilobytes) is retrieved from S3.

        :param cmd: The PowerShell command to execute (may be encoded command line).
        :param in_data: Optional stdin data for the command.
        :param mark_begin: The begin marker for output parsing.
        :param mark_end: The end marker for output parsing.
        :returns: A tuple of (exit_code, stdout, stderr).
        """
        import uuid

        # Generate unique S3 key for this command
        command_id = str(uuid.uuid4())
        s3_key = f"{self.instance_id}/commands/{command_id}.ps1"
        stdin_key = None  # Initialize for cleanup scope

        self.verbosity_display(3, f"EXEC_VIA_S3: Uploading command to s3://{self.get_option('bucket_name')}/{s3_key}")
        self.verbosity_display(4, f"EXEC_VIA_S3: Command length: {len(cmd)} bytes")

        # DEBUG: Show command encoding details (level 6 for long-term debugging of encoding issues)
        cmd_str = to_text(cmd)
        self.verbosity_display(6, f"EXEC_VIA_S3: Command (str): {repr(cmd_str[:200])}")
        if isinstance(cmd, bytes):
            self.verbosity_display(6, f"EXEC_VIA_S3: Command (bytes): {cmd[:200]}")
        self.verbosity_display(6, f"EXEC_VIA_S3: Command content:\n{cmd_str}")

        # If the command is a PowerShell command line with -EncodedCommand, decode it to get the actual script
        # The wrapper expects PowerShell script code, not a command line
        script_to_upload = cmd
        encoded_match = re.search(r'-EncodedCommand\s+["\']?([A-Za-z0-9+/=]+)["\']?', cmd_str)
        if encoded_match:
            self.verbosity_display(4, "EXEC_VIA_S3: Detected -EncodedCommand, decoding to extract PowerShell script")
            try:
                # Extract and decode the base64-encoded UTF-16LE PowerShell script
                encoded_script = encoded_match.group(1)
                self.verbosity_display(5, f"EXEC_VIA_S3: Base64 length: {len(encoded_script)} chars")
                script_bytes = base64.b64decode(encoded_script)
                script_to_upload = script_bytes.decode("utf-16-le")
                self.verbosity_display(4, f"EXEC_VIA_S3: Decoded script length: {len(script_to_upload)} chars")
                self.verbosity_display(6, f"EXEC_VIA_S3: Decoded script:\n{script_to_upload}")
            except Exception as e:
                self.verbosity_display(
                    3, f"EXEC_VIA_S3: WARNING - Failed to decode -EncodedCommand, uploading as-is: {e}"
                )
                # Fall back to uploading the command line as-is
                script_to_upload = cmd

        try:
            # Upload script to S3 with text content type so PowerShell recognizes it as text
            script_bytes = to_bytes(script_to_upload, errors="surrogate_or_strict")
            self.verbosity_display(6, f"EXEC_VIA_S3: Script to upload (str): {repr(to_text(script_to_upload)[:200])}")
            self.verbosity_display(6, f"EXEC_VIA_S3: Script to upload (bytes): {script_bytes[:200]}")

            self.s3_client.put_object(
                Bucket=self.get_option("bucket_name"),
                Key=s3_key,
                Body=script_bytes,
                ContentType="text/plain; charset=utf-8",
            )
            self.verbosity_display(4, f"EXEC_VIA_S3: Uploaded {len(script_bytes)} bytes to S3")

            # Generate presigned URL (1 hour expiry)
            presigned_url = self.s3_manager.get_url("get_object", self.get_option("bucket_name"), s3_key, "GET")

            self.verbosity_display(4, f"EXEC_VIA_S3: Generated presigned URL (length: {len(presigned_url)})")
            self.verbosity_display(6, f"EXEC_VIA_S3: Presigned URL: {presigned_url}")

            # Create wrapper command that:
            # 1. Downloads script from S3
            # 2. Executes it with stdin if provided
            # 3. Captures output and return code
            if in_data:
                # If we have stdin, we need to handle it specially
                # Upload stdin data to S3 as well
                stdin_key = f"{self.instance_id}/commands/{command_id}-stdin.txt"
                self.verbosity_display(
                    3, f"EXEC_VIA_S3: Uploading stdin data to s3://{self.get_option('bucket_name')}/{stdin_key}"
                )
                self.verbosity_display(4, f"EXEC_VIA_S3: Stdin data length: {len(in_data)} bytes")
                self.verbosity_display(6, f"EXEC_VIA_S3: Stdin data (bytes): {in_data[:200]}")
                self.verbosity_display(6, f"EXEC_VIA_S3: Stdin data (decoded): {repr(to_text(in_data, errors='surrogate_or_strict')[:200])}")

                self.s3_client.put_object(
                    Bucket=self.get_option("bucket_name"),
                    Key=stdin_key,
                    Body=in_data,
                    ContentType="text/plain; charset=utf-8",
                )
                stdin_url = self.s3_manager.get_url("get_object", self.get_option("bucket_name"), stdin_key, "GET")
                self.verbosity_display(4, f"EXEC_VIA_S3: Generated stdin presigned URL (length: {len(stdin_url)})")
                self.verbosity_display(6, f"EXEC_VIA_S3: Stdin presigned URL: {stdin_url}")

                # PowerShell: download script and stdin using WebClient (more reliable than Invoke-WebRequest)
                # See https://github.com/ansible-collections/amazon.aws/pull/2820
                # Set WebClient encoding to UTF-8 to correctly decode S3 content
                # Save script to temp file and execute as separate process to handle exit codes correctly
                # Scriptblocks don't set $LASTEXITCODE properly when they contain exit statements
                wrapper = (
                    f"try {{ "
                    f"$wc=[System.Net.WebClient]::new() ; "
                    f"$wc.Encoding=[System.Text.Encoding]::UTF8 ; "
                    f"$s=$wc.DownloadString('{presigned_url}') ; "
                    f"$i=$wc.DownloadString('{stdin_url}') ; "
                    f"$wc.Dispose() ; "
                    f"$t=[System.IO.Path]::GetTempFileName() ; "
                    f"$t=[System.IO.Path]::ChangeExtension($t,'.ps1') ; "
                    f"[System.IO.File]::WriteAllText($t,$s,[System.Text.Encoding]::UTF8) ; "
                    f"echo '{mark_begin}' ; "
                    f'($i -split "`r?`n") | powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $t ; '
                    f"$e=$LASTEXITCODE ; "
                    f"Remove-Item -LiteralPath $t -Force -ErrorAction SilentlyContinue ; "
                    f"echo '' ; echo $e ; echo '{mark_end}' "
                    f"}} catch {{ "
                    f"echo '{mark_begin}' ; echo \"S3_DOWNLOAD_ERROR: $_\" ; echo '' ; echo 99 ; echo '{mark_end}' "
                    f"}}"
                )
            else:
                # No stdin: download script using WebClient and execute
                # See https://github.com/ansible-collections/amazon.aws/pull/2820
                # Set WebClient encoding to UTF-8 to correctly decode S3 content
                # Save script to temp file and execute as separate process to handle exit codes correctly
                # Scriptblocks don't set $LASTEXITCODE properly when they contain exit statements
                wrapper = (
                    f"try {{ "
                    f"$wc=[System.Net.WebClient]::new() ; "
                    f"$wc.Encoding=[System.Text.Encoding]::UTF8 ; "
                    f"$s=$wc.DownloadString('{presigned_url}') ; "
                    f"$wc.Dispose() ; "
                    f"$t=[System.IO.Path]::GetTempFileName() ; "
                    f"$t=[System.IO.Path]::ChangeExtension($t,'.ps1') ; "
                    f"[System.IO.File]::WriteAllText($t,$s,[System.Text.Encoding]::UTF8) ; "
                    f"echo '{mark_begin}' ; "
                    f"powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $t ; "
                    f"$e=$LASTEXITCODE ; "
                    f"Remove-Item -LiteralPath $t -Force -ErrorAction SilentlyContinue ; "
                    f"echo '' ; echo $e ; echo '{mark_end}' "
                    f"}} catch {{ "
                    f"echo '{mark_begin}' ; echo \"S3_DOWNLOAD_ERROR: $_\" ; echo '' ; echo 99 ; echo '{mark_end}' "
                    f"}}"
                )

            self.verbosity_display(3, f"EXEC_VIA_S3: Wrapper command length: {len(wrapper)} bytes")
            self.verbosity_display(5, f"EXEC_VIA_S3: Wrapper command:\n{wrapper}")

            # Send wrapper command via session (tiny, won't timeout from echo)
            wrapper_bytes = to_bytes(wrapper + "\n", errors="surrogate_or_strict")
            self.verbosity_display(3, f"EXEC_VIA_S3: Sending wrapper command to session ({len(wrapper_bytes)} bytes)")
            self.session_manager.stdin_write(wrapper_bytes)

            # Execute via normal communicate flow (no stdin data since wrapper handles it)
            result = self.exec_communicate(wrapper, None, mark_begin, mark_end)

            self.verbosity_display(3, f"EXEC_VIA_S3: Command execution complete, returncode={result[0]}")
            self.verbosity_display(6, f"EXEC_VIA_S3: Stdout (str): {repr(result[1][:200])}")
            self.verbosity_display(6, f"EXEC_VIA_S3: Stderr (str): {repr(result[2][:200])}")
            self.verbosity_display(6, f"EXEC_VIA_S3: Stdout type: {type(result[1])}, length: {len(result[1])}")
            self.verbosity_display(6, f"EXEC_VIA_S3: Stderr type: {type(result[2])}, length: {len(result[2])}")
            return result

        finally:
            # Clean up S3 objects
            try:
                self.verbosity_display(4, f"EXEC_VIA_S3: Cleaning up S3 object: {s3_key}")
                self.s3_client.delete_object(Bucket=self.get_option("bucket_name"), Key=s3_key)
                if stdin_key is not None:
                    self.verbosity_display(4, f"EXEC_VIA_S3: Cleaning up S3 stdin object: {stdin_key}")
                    self.s3_client.delete_object(Bucket=self.get_option("bucket_name"), Key=stdin_key)
            except Exception as e:
                self.verbosity_display(3, f"EXEC_VIA_S3: Failed to clean up S3 objects: {e}")

    # @AWSConnectionRetry.exponential_backoff()
    def exec_command(self, cmd: str, in_data: bytes | None = None, sudoable: bool = True) -> tuple[int, bytes, bytes]:
        """Execute a command on the SSM host with automatic retry on failure.

        For Windows, large commands are uploaded to S3 and executed via a tiny wrapper
        command to avoid PTY echo timeouts. For Linux, commands are sent inline.

        :param cmd: The command to execute.
        :param in_data: Optional data to send to stdin.
        :param sudoable: Whether the command can be run with sudo (unused for SSM).
        :returns: A tuple of (exit_code, stdout, stderr).
        """
        super().exec_command(cmd, in_data=in_data, sudoable=sudoable)

        self.verbosity_display(2, f"EXEC: {to_text(cmd)[:200]}...")
        self.verbosity_display(5, f"EXEC: Full command: {to_text(cmd)}")
        self.verbosity_display(5, f"EXEC: Command length: {len(cmd)} bytes")
        if in_data:
            self.verbosity_display(5, f"EXEC: Has stdin data: {len(in_data)} bytes")
            self.verbosity_display(6, f"EXEC: First 200 bytes of stdin: {in_data[:200]}")
        else:
            self.verbosity_display(5, "EXEC: No stdin data")

        mark_begin = self.generate_mark()
        mark_end = self.generate_mark()
        self.verbosity_display(5, f"EXEC: Generated begin marker: {mark_begin}")
        self.verbosity_display(5, f"EXEC: Generated end marker: {mark_end}")

        # For Windows, use S3-based execution to avoid PTY echo timeouts
        # The PTY echoes ALL stdin data to stdout before PowerShell can read it,
        # causing timeouts on large commands. S3 approach keeps session command tiny.
        if self.is_windows:
            self.verbosity_display(3, "EXEC: Using S3-based execution for Windows (avoids PTY echo)")
            returncode, stdout, stderr = self._exec_command_via_s3(cmd, in_data, mark_begin, mark_end)

            # DEBUG: Show what we're returning to Ansible (level 6 for long-term debugging of encoding issues)
            stdout_bytes = to_bytes(stdout, errors="surrogate_or_strict")
            stderr_bytes = to_bytes(stderr, errors="surrogate_or_strict")
            self.verbosity_display(6, f"EXEC: Returning stdout (str): {repr(stdout[:200])}")
            self.verbosity_display(6, f"EXEC: Returning stdout (bytes): {stdout_bytes[:200]}")
            self.verbosity_display(6, f"EXEC: Returning stderr (str): {repr(stderr[:200])}")
            self.verbosity_display(6, f"EXEC: Returning stderr (bytes): {stderr_bytes[:200]}")

            return (returncode, stdout_bytes, stderr_bytes)

        # For Linux, use inline command execution (works fine, no PTY echo issues)
        self.verbosity_display(3, "EXEC: Using inline execution for Linux")

        # Wrap command in markers
        self.verbosity_display(5, f"EXEC: Wrapping command with has_stdin={bool(in_data)}")
        trigger_cmd, stdin_cmd = self.terminal_manager.wrap_command(cmd, mark_begin, mark_end, has_stdin=bool(in_data))
        self.verbosity_display(5, f"EXEC: Trigger command length: {len(trigger_cmd)} bytes")
        self.verbosity_display(6, f"EXEC: Full trigger command: {to_text(trigger_cmd)}")

        self.session_manager.flush_stderr()

        # Send the trigger command
        chunk_count = 0
        for chunk, is_last in _chunked_payload(trigger_cmd):
            chunk_count += 1
            self.verbosity_display(5, f"STREAM_TRIGGER: Chunk {chunk_count} ({len(chunk)} bytes, last={is_last})")
            self.verbosity_display(6, f"STREAM_TRIGGER: Chunk {chunk_count} content: {to_text(chunk)}")
            self.session_manager.stdin_write(to_bytes(chunk, errors="surrogate_or_strict"))
        self.verbosity_display(5, f"EXEC: Sent {chunk_count} trigger chunks to session")

        returncode, stdout, stderr = self.exec_communicate(trigger_cmd, in_data, mark_begin, mark_end)
        return (
            returncode,
            to_bytes(stdout, errors="surrogate_or_strict"),
            to_bytes(stderr, errors="surrogate_or_strict"),
        )

    def _post_process(self, stdout: str, mark_begin: str) -> tuple[int, str]:
        """Extract command status and strip unwanted lines.

        :param stdout: The raw stdout content containing exit code and output.
        :param mark_begin: The begin marker (unused, kept for compatibility).
        :returns: A tuple of (exit_code, cleaned_stdout).
        """
        # Get command return code (second to last line)
        self.verbosity_display(
            5, f"POST_PROCESS: Raw stdout length: {len(stdout)} bytes, {len(stdout.splitlines())} lines"
        )
        self.verbosity_display(6, f"POST_PROCESS: Raw stdout:\n{stdout}")
        try:
            return_data = stdout.splitlines()[-1]
            self.verbosity_display(4, f'POST_PROCESS: Return code line: "{return_data}"')
            returncode = int(return_data)
            self.verbosity_display(5, f"POST_PROCESS: Parsed return code: {returncode}")
        except ValueError:
            self.verbosity_display(4, f'POST_PROCESS: Failed to parse return code from "{return_data}", using 32')
            returncode = 32

        # Throw away final lines (blank line, exit code, already removed mark_end)
        self.verbosity_display(5, "POST_PROCESS: Removing final 3 lines (blank, exit code, end marker)")
        for _x in range(0, 3):
            stdout = stdout[:stdout.rfind('\n')]  # fmt: skip
        self.verbosity_display(
            5, f"POST_PROCESS: After removing final lines: {len(stdout)} bytes, {len(stdout.splitlines())} lines"
        )

        if self.is_windows:
            # If the return code contains #CLIXML (like a progress bar) remove it
            clixml_filter = re.compile(r"#<\sCLIXML\s<Objs.*</Objs>")
            original_len = len(stdout)
            stdout = clixml_filter.sub("", stdout)
            if len(stdout) != original_len:
                self.verbosity_display(
                    5, f"POST_PROCESS: Removed CLIXML, reduced from {original_len} to {len(stdout)} bytes"
                )

            # If it looks like JSON remove any newlines
            if stdout.startswith("{"):
                self.verbosity_display(5, "POST_PROCESS: Detected JSON output, removing newlines")
                stdout = stdout.replace("\n", "")

        self.verbosity_display(5, f"POST_PROCESS: Final stdout length: {len(stdout)} bytes")
        self.verbosity_display(6, f"POST_PROCESS: Final stdout:\n{stdout}")
        return (returncode, stdout)

    def generate_commands(self, in_path: str, out_path: str, ssm_action: str) -> tuple[str, str, dict]:
        """
        Generate S3 path and associated transport commands for file transfer.
        :param in_path: The local file path to transfer from.
        :param out_path: The remote file path to transfer to (used to build the S3 key).
        :param ssm_action: The SSM action to perform ("get" or "put").
        :return: A tuple containing:
            - s3_path (str): The S3 key used for the transfer.
            - commands (str): Command to be executed for the transfer.
            - put_args (dict): Additional arguments needed for a 'put' operation.
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

        self.verbosity_display(2, f"PUT {in_path} TO {out_path}")
        if not os.path.exists(to_bytes(in_path, errors="surrogate_or_strict")):
            raise AnsibleFileNotFound(f"file or module does not exist: {in_path}")

        s3_path, command, put_args = self.generate_commands(in_path, out_path, "put")
        return self.file_transfer_manager._file_transport_command(in_path, out_path, "put", command, put_args, s3_path)

    def fetch_file(self, in_path: str, out_path: str) -> CommandResult:
        """fetch a file from remote to local"""

        super().fetch_file(in_path, out_path)

        self.verbosity_display(2, f"FETCH {in_path} TO {out_path}")

        s3_path, command, put_args = self.generate_commands(in_path, out_path, "get")
        return self.file_transfer_manager._file_transport_command(in_path, out_path, "get", command, put_args, s3_path)

    def close(self) -> None:
        """terminate the connection"""
        if self.session_manager is not None:
            self.verbosity_display(2, f"TERMINATE SSM SESSION: {self.session_manager._session_id}")

            self.session_manager.terminate()
            self.session_manager = None

        self._connected = False
