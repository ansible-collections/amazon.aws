# Based on the ssh connection plugin by Michael DeHaan
#
# Copyright: (c) 2018, Pat Sharkey <psharkey@cleo.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
author:
- Pat Sharkey (@psharkey) <psharkey@cleo.com>
- HanumanthaRao MVL (@hanumantharaomvl) <hanumanth@flux7.com>
- Gaurav Ashtikar (@gau1991) <gaurav.ashtikar@flux7.com>
name: aws_ssm
short_description: execute via AWS Systems Manager
description:
- This connection plugin allows ansible to execute tasks on an EC2 instance via the aws ssm CLI.
requirements:
- The remote EC2 instance must be running the AWS Systems Manager Agent (SSM Agent).
- The control machine must have the aws session manager plugin installed.
- The remote EC2 linux instance must have the curl installed.
options:
  access_key_id:
    description: The STS access key to use when connecting via session-manager.
    vars:
    - name: ansible_aws_ssm_access_key_id
    version_added: 1.3.0
  secret_access_key:
    description: The STS secret key to use when connecting via session-manager.
    vars:
    - name: ansible_aws_ssm_secret_access_key
    version_added: 1.3.0
  session_token:
    description: The STS session token to use when connecting via session-manager.
    vars:
    - name: ansible_aws_ssm_session_token
    version_added: 1.3.0
  instance_id:
    description: The EC2 instance ID.
    vars:
    - name: ansible_aws_ssm_instance_id
  region:
    description: The region the EC2 instance is located.
    vars:
    - name: ansible_aws_ssm_region
    default: 'us-east-1'
  bucket_name:
    description: The name of the S3 bucket used for file transfers.
    vars:
    - name: ansible_aws_ssm_bucket_name
  plugin:
    description: This defines the location of the session-manager-plugin binary.
    vars:
    - name: ansible_aws_ssm_plugin
    default: '/usr/local/bin/session-manager-plugin'
  profile:
    description: Sets AWS profile to use.
    vars:
    - name: ansible_aws_ssm_profile
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
'''

EXAMPLES = r'''

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

# Making use of Dynamic Inventory Plugin
# =======================================
# aws_ec2.yml (Dynamic Inventory - Linux)
# This will return the Instance IDs matching the filter
#plugin: aws_ec2
#regions:
#    - us-east-1
#hostnames:
#    - instance-id
#filters:
#    tag:SSMTag: ssmlinux
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
# Execution: ansible-playbook linux.yaml -i aws_ec2.yml
# The playbook tasks will get executed on the instance ids returned from the dynamic inventory plugin using ssm connection.
# =====================================================
# aws_ec2.yml (Dynamic Inventory - Windows)
#plugin: aws_ec2
#regions:
#    - us-east-1
#hostnames:
#    - instance-id
#filters:
#    tag:SSMTag: ssmwindows
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
# Execution:  ansible-playbook win_file.yaml -i aws_ec2.yml
# The playbook tasks will get executed on the instance ids returned from the dynamic inventory plugin using ssm connection.

# Install a Nginx Package on Linux Instance; with specific SSE for file transfer
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
'''

import os
import getpass
import json
import pty
import random
import re
import select
import string
import subprocess
import time

try:
    import boto3
    from botocore.client import Config
except ImportError as e:
    pass

from functools import wraps
from ansible_collections.amazon.aws.plugins.module_utils.botocore import HAS_BOTO3
from ansible.errors import AnsibleConnectionFailure, AnsibleError, AnsibleFileNotFound
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.six.moves import xrange
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.plugins.connection import ConnectionBase
from ansible.plugins.shell.powershell import _common_args
from ansible.utils.display import Display

display = Display()


def _ssm_retry(func):
    """
    Decorator to retry in the case of a connection failure
    Will retry if:
    * an exception is caught
    Will not retry if
    * remaining_tries is <2
    * retries limit reached
    """
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        remaining_tries = int(self.get_option('reconnection_retries')) + 1
        cmd_summary = "%s..." % args[0]
        for attempt in range(remaining_tries):
            cmd = args[0]

            try:
                return_tuple = func(self, *args, **kwargs)
                display.vvv(return_tuple, host=self.host)
                break

            except (AnsibleConnectionFailure, Exception) as e:
                if attempt == remaining_tries - 1:
                    raise
                else:
                    pause = 2 ** attempt - 1
                    if pause > 30:
                        pause = 30

                    if isinstance(e, AnsibleConnectionFailure):
                        msg = "ssm_retry: attempt: %d, cmd (%s), pausing for %d seconds" % (attempt, cmd_summary, pause)
                    else:
                        msg = "ssm_retry: attempt: %d, caught exception(%s) from cmd (%s), pausing for %d seconds" % (attempt, e, cmd_summary, pause)

                    display.vv(msg, host=self.host)

                    time.sleep(pause)

                    # Do not attempt to reuse the existing session on retries
                    self.close()

                    continue

        return return_tuple
    return wrapped


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


class Connection(ConnectionBase):
    ''' AWS SSM based connections '''

    transport = 'community.aws.aws_ssm'
    allow_executable = False
    allow_extras = True
    has_pipelining = False
    is_windows = False
    _client = None
    _session = None
    _stdout = None
    _session_id = ''
    _timeout = False
    MARK_LENGTH = 26

    def __init__(self, *args, **kwargs):
        if not HAS_BOTO3:
            raise AnsibleError('{0}'.format(missing_required_lib("boto3")))

        super(Connection, self).__init__(*args, **kwargs)
        self.host = self._play_context.remote_addr

        if getattr(self._shell, "SHELL_FAMILY", '') == 'powershell':
            self.delegate = None
            self.has_native_async = True
            self.always_pipeline_modules = True
            self.module_implementation_preferences = ('.ps1', '.exe', '')
            self.protocol = None
            self.shell_id = None
            self._shell_type = 'powershell'
            self.is_windows = True

    def __del__(self):
        self.close()

    def _connect(self):
        ''' connect to the host via ssm '''

        self._play_context.remote_user = getpass.getuser()

        if not self._session_id:
            self.start_session()
        return self

    def reset(self):
        ''' start a fresh ssm session '''
        display.vvvv('reset called on ssm connection')
        return self.start_session()

    def start_session(self):
        ''' start ssm session '''

        if self.get_option('instance_id') is None:
            self.instance_id = self.host
        else:
            self.instance_id = self.get_option('instance_id')

        display.vvv(u"ESTABLISH SSM CONNECTION TO: {0}".format(self.instance_id), host=self.host)

        executable = self.get_option('plugin')
        if not os.path.exists(to_bytes(executable, errors='surrogate_or_strict')):
            raise AnsibleError("failed to find the executable specified %s."
                               " Please verify if the executable exists and re-try." % executable)

        profile_name = self.get_option('profile') or ''
        region_name = self.get_option('region')
        ssm_parameters = dict()
        client = self._get_boto_client('ssm', region_name=region_name, profile_name=profile_name)
        self._client = client
        response = client.start_session(Target=self.instance_id, Parameters=ssm_parameters)
        self._session_id = response['SessionId']

        cmd = [
            executable,
            json.dumps(response),
            region_name,
            "StartSession",
            profile_name,
            json.dumps({"Target": self.instance_id}),
            client.meta.endpoint_url
        ]

        display.vvvv(u"SSM COMMAND: {0}".format(to_text(cmd)), host=self.host)

        stdout_r, stdout_w = pty.openpty()
        session = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=stdout_w,
            stderr=subprocess.PIPE,
            close_fds=True,
            bufsize=0,
        )

        os.close(stdout_w)
        self._stdout = os.fdopen(stdout_r, 'rb', 0)
        self._session = session
        self._poll_stdout = select.poll()
        self._poll_stdout.register(self._stdout, select.POLLIN)

        # Disable command echo and prompt.
        self._prepare_terminal()

        display.vvv(u"SSM CONNECTION ID: {0}".format(self._session_id), host=self.host)

        return session

    @_ssm_retry
    def exec_command(self, cmd, in_data=None, sudoable=True):
        ''' run a command on the ssm host '''

        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        display.vvv(u"EXEC {0}".format(to_text(cmd)), host=self.host)

        session = self._session

        mark_begin = "".join([random.choice(string.ascii_letters) for i in xrange(self.MARK_LENGTH)])
        if self.is_windows:
            mark_start = mark_begin + " $LASTEXITCODE"
        else:
            mark_start = mark_begin
        mark_end = "".join([random.choice(string.ascii_letters) for i in xrange(self.MARK_LENGTH)])

        # Wrap command in markers accordingly for the shell used
        cmd = self._wrap_command(cmd, sudoable, mark_start, mark_end)

        self._flush_stderr(session)

        for chunk in chunks(cmd, 1024):
            session.stdin.write(to_bytes(chunk, errors='surrogate_or_strict'))

        # Read stdout between the markers
        stdout = ''
        win_line = ''
        begin = False
        stop_time = int(round(time.time())) + self.get_option('ssm_timeout')
        while session.poll() is None:
            remaining = stop_time - int(round(time.time()))
            if remaining < 1:
                self._timeout = True
                display.vvvv(u"EXEC timeout stdout: {0}".format(to_text(stdout)), host=self.host)
                raise AnsibleConnectionFailure("SSM exec_command timeout on host: %s"
                                               % self.instance_id)
            if self._poll_stdout.poll(1000):
                line = self._filter_ansi(self._stdout.readline())
                display.vvvv(u"EXEC stdout line: {0}".format(to_text(line)), host=self.host)
            else:
                display.vvvv(u"EXEC remaining: {0}".format(remaining), host=self.host)
                continue

            if not begin and self.is_windows:
                win_line = win_line + line
                line = win_line

            if mark_start in line:
                begin = True
                if not line.startswith(mark_start):
                    stdout = ''
                continue
            if begin:
                if mark_end in line:
                    display.vvvv(u"POST_PROCESS: {0}".format(to_text(stdout)), host=self.host)
                    returncode, stdout = self._post_process(stdout, mark_begin)
                    break
                else:
                    stdout = stdout + line

        stderr = self._flush_stderr(session)

        return (returncode, stdout, stderr)

    def _prepare_terminal(self):
        ''' perform any one-time terminal settings '''

        if not self.is_windows:
            cmd = "stty -echo\n" + "PS1=''\n"
            cmd = to_bytes(cmd, errors='surrogate_or_strict')
            self._session.stdin.write(cmd)

    def _wrap_command(self, cmd, sudoable, mark_start, mark_end):
        ''' wrap command so stdout and status can be extracted '''

        if self.is_windows:
            if not cmd.startswith(" ".join(_common_args) + " -EncodedCommand"):
                cmd = self._shell._encode_script(cmd, preserve_rc=True)
            cmd = cmd + "; echo " + mark_start + "\necho " + mark_end + "\n"
        else:
            if sudoable:
                cmd = "sudo " + cmd
            cmd = "echo " + mark_start + "\n" + cmd + "\necho $'\\n'$?\n" + "echo " + mark_end + "\n"

        display.vvvv(u"_wrap_command: '{0}'".format(to_text(cmd)), host=self.host)
        return cmd

    def _post_process(self, stdout, mark_begin):
        ''' extract command status and strip unwanted lines '''

        if self.is_windows:
            # Value of $LASTEXITCODE will be the line after the mark
            trailer = stdout[stdout.rfind(mark_begin):]
            last_exit_code = trailer.splitlines()[1]
            if last_exit_code.isdigit:
                returncode = int(last_exit_code)
            else:
                returncode = -1
            # output to keep will be before the mark
            stdout = stdout[:stdout.rfind(mark_begin)]

            # If it looks like JSON remove any newlines
            if stdout.startswith('{'):
                stdout = stdout.replace('\n', '')

            return (returncode, stdout)
        else:
            # Get command return code
            returncode = int(stdout.splitlines()[-2])

            # Throw away ending lines
            for x in range(0, 3):
                stdout = stdout[:stdout.rfind('\n')]

            return (returncode, stdout)

    def _filter_ansi(self, line):
        ''' remove any ANSI terminal control codes '''
        line = to_text(line)

        if self.is_windows:
            osc_filter = re.compile(r'\x1b\][^\x07]*\x07')
            line = osc_filter.sub('', line)
            ansi_filter = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')
            line = ansi_filter.sub('', line)

            # Replace or strip sequence (at terminal width)
            line = line.replace('\r\r\n', '\n')
            if len(line) == 201:
                line = line[:-1]

        return line

    def _flush_stderr(self, subprocess):
        ''' read and return stderr with minimal blocking '''

        poll_stderr = select.poll()
        poll_stderr.register(subprocess.stderr, select.POLLIN)
        stderr = ''

        while subprocess.poll() is None:
            if poll_stderr.poll(1):
                line = subprocess.stderr.readline()
                display.vvvv(u"stderr line: {0}".format(to_text(line)), host=self.host)
                stderr = stderr + line
            else:
                break

        return stderr

    def _get_url(self, client_method, bucket_name, out_path, http_method, profile_name, extra_args=None):
        ''' Generate URL for get_object / put_object '''

        bucket_location = boto3.client('s3').get_bucket_location(
            Bucket=(self.get_option('bucket_name')),
        )
        region_name = bucket_location['LocationConstraint']

        client = self._get_boto_client('s3', region_name=region_name, profile_name=profile_name)
        params = {'Bucket': bucket_name, 'Key': out_path}
        if extra_args is not None:
            params.update(extra_args)
        return client.generate_presigned_url(client_method, Params=params, ExpiresIn=3600, HttpMethod=http_method)

    def _get_boto_client(self, service, region_name=None, profile_name=None):
        ''' Gets a boto3 client based on the STS token '''

        aws_access_key_id = self.get_option('access_key_id')
        aws_secret_access_key = self.get_option('secret_access_key')
        aws_session_token = self.get_option('session_token')

        if aws_access_key_id is None:
            aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID", None)
        if aws_secret_access_key is None:
            aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY", None)
        if aws_session_token is None:
            aws_session_token = os.environ.get("AWS_SESSION_TOKEN", None)
        if not profile_name:
            profile_name = os.environ.get("AWS_PROFILE", None)

        session_args = dict(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            region_name=region_name,
        )
        if profile_name:
            session_args['profile_name'] = profile_name
        session = boto3.session.Session(**session_args)

        client = session.client(
            service,
            config=Config(signature_version="s3v4")
        )
        return client

    @_ssm_retry
    def _file_transport_command(self, in_path, out_path, ssm_action):
        ''' transfer a file from using an intermediate S3 bucket '''

        path_unescaped = u"{0}/{1}".format(self.instance_id, out_path)
        s3_path = path_unescaped.replace('\\', '/')
        bucket_url = 's3://%s/%s' % (self.get_option('bucket_name'), s3_path)

        profile_name = self.get_option('profile')

        put_args = dict()
        put_headers = dict()
        if self.get_option('bucket_sse_mode'):
            put_args['ServerSideEncryption'] = self.get_option('bucket_sse_mode')
            put_headers['x-amz-server-side-encryption'] = self.get_option('bucket_sse_mode')
            if self.get_option('bucket_sse_mode') == 'aws:kms' and self.get_option('bucket_sse_kms_key_id'):
                put_args['SSEKMSKeyId'] = self.get_option('bucket_sse_kms_key_id')
                put_headers['x-amz-server-side-encryption-aws-kms-key-id'] = self.get_option('bucket_sse_kms_key_id')

        if self.is_windows:
            put_command_headers = "; ".join(["'%s' = '%s'" % (h, v) for h, v in put_headers.items()])
            put_command = "Invoke-WebRequest -Method PUT -Headers @{%s} -InFile '%s' -Uri '%s' -UseBasicParsing" % (
                put_command_headers, in_path,
                self._get_url('put_object', self.get_option('bucket_name'), s3_path, 'PUT', profile_name,
                              extra_args=put_args))
            get_command = "Invoke-WebRequest '%s' -OutFile '%s'" % (
                self._get_url('get_object', self.get_option('bucket_name'), s3_path, 'GET', profile_name), out_path)
        else:
            put_command_headers = "".join(["-H '%s: %s' " % (h, v) for h, v in put_headers.items()])
            put_command = "curl --request PUT %s--upload-file '%s' '%s'" % (
                put_command_headers, in_path,
                self._get_url('put_object', self.get_option('bucket_name'), s3_path, 'PUT', profile_name,
                              extra_args=put_args))
            get_command = "curl '%s' -o '%s'" % (
                self._get_url('get_object', self.get_option('bucket_name'), s3_path, 'GET', profile_name), out_path)

        client = self._get_boto_client('s3', profile_name=profile_name)
        if ssm_action == 'get':
            (returncode, stdout, stderr) = self.exec_command(put_command, in_data=None, sudoable=False)
            with open(to_bytes(out_path, errors='surrogate_or_strict'), 'wb') as data:
                client.download_fileobj(self.get_option('bucket_name'), s3_path, data)
        else:
            with open(to_bytes(in_path, errors='surrogate_or_strict'), 'rb') as data:
                client.upload_fileobj(data, self.get_option('bucket_name'), s3_path, ExtraArgs=put_args)
            (returncode, stdout, stderr) = self.exec_command(get_command, in_data=None, sudoable=False)

        # Remove the files from the bucket after they've been transferred
        client.delete_object(Bucket=self.get_option('bucket_name'), Key=s3_path)

        # Check the return code
        if returncode == 0:
            return (returncode, stdout, stderr)
        else:
            raise AnsibleError("failed to transfer file to %s %s:\n%s\n%s" %
                               (to_native(in_path), to_native(out_path), to_native(stdout), to_native(stderr)))

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to remote '''

        super(Connection, self).put_file(in_path, out_path)

        display.vvv(u"PUT {0} TO {1}".format(in_path, out_path), host=self.host)
        if not os.path.exists(to_bytes(in_path, errors='surrogate_or_strict')):
            raise AnsibleFileNotFound("file or module does not exist: {0}".format(to_native(in_path)))

        return self._file_transport_command(in_path, out_path, 'put')

    def fetch_file(self, in_path, out_path):
        ''' fetch a file from remote to local '''

        super(Connection, self).fetch_file(in_path, out_path)

        display.vvv(u"FETCH {0} TO {1}".format(in_path, out_path), host=self.host)
        return self._file_transport_command(in_path, out_path, 'get')

    def close(self):
        ''' terminate the connection '''
        if self._session_id:

            display.vvv(u"CLOSING SSM CONNECTION TO: {0}".format(self.instance_id), host=self.host)
            if self._timeout:
                self._session.terminate()
            else:
                cmd = b"\nexit\n"
                self._session.communicate(cmd)

            display.vvvv(u"TERMINATE SSM SESSION: {0}".format(self._session_id), host=self.host)
            self._client.terminate_session(SessionId=self._session_id)
            self._session_id = ''
