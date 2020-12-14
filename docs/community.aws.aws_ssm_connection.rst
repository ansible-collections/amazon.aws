.. _community.aws.aws_ssm_connection:


*********************
community.aws.aws_ssm
*********************

**execute via AWS Systems Manager**



.. contents::
   :local:
   :depth: 1


Synopsis
--------
- This connection plugin allows ansible to execute tasks on an EC2 instance via the aws ssm CLI.



Requirements
------------
The below requirements are needed on the local Ansible controller node that executes this connection.

- The remote EC2 instance must be running the AWS Systems Manager Agent (SSM Agent).
- The control machine must have the aws session manager plugin installed.
- The remote EC2 linux instance must have the curl installed.


Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="1">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
                <th>Configuration</th>
            <th width="100%">Comments</th>
        </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>access_key_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 1.3.0</div>
                </td>
                <td>
                </td>
                    <td>
                                <div>var: ansible_aws_ssm_access_key_id</div>
                    </td>
                <td>
                        <div>The STS access key to use when connecting via session-manager.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>bucket_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                                <div>var: ansible_aws_ssm_bucket_name</div>
                    </td>
                <td>
                        <div>The name of the S3 bucket used for file transfers.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>instance_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                    <td>
                                <div>var: ansible_aws_ssm_instance_id</div>
                    </td>
                <td>
                        <div>The EC2 instance ID.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>plugin</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"/usr/local/bin/session-manager-plugin"</div>
                </td>
                    <td>
                                <div>var: ansible_aws_ssm_plugin</div>
                    </td>
                <td>
                        <div>This defines the location of the session-manager-plugin binary.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>region</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"us-east-1"</div>
                </td>
                    <td>
                                <div>var: ansible_aws_ssm_region</div>
                    </td>
                <td>
                        <div>The region the EC2 instance is located.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>retries</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">3</div>
                </td>
                    <td>
                                <div>var: ansible_aws_ssm_retries</div>
                    </td>
                <td>
                        <div>Number of attempts to connect.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>secret_access_key</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 1.3.0</div>
                </td>
                <td>
                </td>
                    <td>
                                <div>var: ansible_aws_ssm_secret_access_key</div>
                    </td>
                <td>
                        <div>The STS secret key to use when connecting via session-manager.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>session_token</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                    <div style="font-style: italic; font-size: small; color: darkgreen">added in 1.3.0</div>
                </td>
                <td>
                </td>
                    <td>
                                <div>var: ansible_aws_ssm_session_token</div>
                    </td>
                <td>
                        <div>The STS session token to use when connecting via session-manager.</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ssm_timeout</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">60</div>
                </td>
                    <td>
                                <div>var: ansible_aws_ssm_timeout</div>
                    </td>
                <td>
                        <div>Connection timeout seconds.</div>
                </td>
            </tr>
    </table>
    <br/>




Examples
--------

.. code-block:: yaml

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




Status
------


Authors
~~~~~~~

- Pat Sharkey (@psharkey) <psharkey@cleo.com>
- HanumanthaRao MVL (@hanumantharaomvl) <hanumanth@flux7.com>
- Gaurav Ashtikar (@gau1991 )<gaurav.ashtikar@flux7.com>


.. hint::
    Configuration entries for each entry type have a low to high priority order. For example, a variable that is lower in the list will override a variable that is higher up.
